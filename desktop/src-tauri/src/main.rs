//! Vỏ app macOS của Lịch Học Cá Nhân: hiện trang chờ, kiểm tra backend ở 127.0.0.1:8080,
//! khi sẵn sàng thì nạp giao diện web (research R1–R3, contracts/desktop-shell.md).

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod backup_cmds;
mod deep_link;
mod health;
mod menu;

use std::process::Command;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::mpsc::{self, RecvTimeoutError, Sender};
use std::sync::Mutex;
use std::thread;
use std::time::Duration;

use serde::Serialize;
use tauri::{AppHandle, Emitter, Manager, RunEvent, State, WindowEvent};
use tauri_plugin_deep_link::DeepLinkExt;

use health::{check_health, HealthResult, BACKEND_ADDR};

const CHECK_INTERVAL: Duration = Duration::from_secs(2);
const CHECK_TIMEOUT: Duration = Duration::from_secs(1);

#[derive(Clone, Copy, Serialize)]
#[serde(rename_all = "snake_case")]
enum ConnectionState {
    Connecting,
    WaitingForBackend,
    OrbstackMissing,
}

#[derive(Clone, Serialize)]
struct ConnectionStatus {
    state: ConnectionState,
}

/// Trạng thái dùng chung giữa các lệnh và vòng kiểm tra nền.
struct Shared {
    /// Đánh thức vòng kiểm tra để thử ngay (nút "Thử lại").
    wake: Mutex<Sender<()>>,
    /// Lần mở OrbStack gần nhất thất bại → giữ thông báo cho tới khi backend lên.
    orbstack_missing: AtomicBool,
}

fn emit_state(app: &AppHandle, state: ConnectionState) {
    let _ = app.emit("connection-status", ConnectionStatus { state });
}

/// Mở app OrbStack; không tìm thấy thì báo `orbstack_missing`.
#[tauri::command]
fn open_orbstack(app: AppHandle, shared: State<Shared>) -> Result<(), String> {
    let opened = Command::new("open")
        .args(["-a", "OrbStack"])
        .status()
        .map(|status| status.success())
        .unwrap_or(false);
    if opened {
        shared.orbstack_missing.store(false, Ordering::SeqCst);
        emit_state(&app, ConnectionState::WaitingForBackend);
        Ok(())
    } else {
        shared.orbstack_missing.store(true, Ordering::SeqCst);
        emit_state(&app, ConnectionState::OrbstackMissing);
        Err("Không tìm thấy OrbStack".into())
    }
}

/// Kiểm tra ngay, không chờ hết chu kỳ.
#[tauri::command]
fn retry_now(shared: State<Shared>) {
    if let Ok(wake) = shared.wake.lock() {
        let _ = wake.send(());
    }
}

/// Vòng kiểm tra ở luồng nền: ngay lập tức rồi mỗi 2 giây; dừng khi backend sẵn sàng.
fn spawn_health_loop(app: AppHandle, wake: mpsc::Receiver<()>) {
    thread::spawn(move || {
        emit_state(&app, ConnectionState::Connecting);
        loop {
            if check_health(BACKEND_ADDR, CHECK_TIMEOUT) == HealthResult::Ready {
                load_web_ui(&app);
                return;
            }
            let missing = app
                .state::<Shared>()
                .orbstack_missing
                .load(Ordering::SeqCst);
            emit_state(
                &app,
                if missing {
                    ConnectionState::OrbstackMissing
                } else {
                    ConnectionState::WaitingForBackend
                },
            );
            match wake.recv_timeout(CHECK_INTERVAL) {
                Ok(()) | Err(RecvTimeoutError::Timeout) => {}
                Err(RecvTimeoutError::Disconnected) => return,
            }
        }
    });
}

fn load_web_ui(app: &AppHandle) {
    let url = format!("http://{BACKEND_ADDR}/");
    if let (Some(window), Ok(url)) = (app.get_webview_window("main"), url.parse()) {
        let _ = window.navigate(url);
    }
}

/// Liên kết `lichhoc://cai-dat/sao-luu`: hiện cửa sổ và chuyển tới trang đó nếu giao diện đã nạp.
fn open_deep_link(app: &AppHandle, link: &str) {
    let Some(target) = deep_link::target_url(link, BACKEND_ADDR) else {
        return;
    };
    show_main_window(app);
    if let (Some(window), Ok(url)) = (app.get_webview_window("main"), target.parse()) {
        // Giao diện chưa nạp (đang ở trang chờ) thì thôi: app sẽ mở ở màn hình Hôm nay.
        let loaded = window.url().is_ok_and(|current| current.host_str() == Some("127.0.0.1"));
        if loaded {
            let _ = window.navigate(url);
        }
    }
}

fn show_main_window(app: &AppHandle) {
    if let Some(window) = app.get_webview_window("main") {
        let _ = window.unminimize();
        let _ = window.show();
        let _ = window.set_focus();
    }
}

fn main() {
    let (wake_tx, wake_rx) = mpsc::channel::<()>();

    let app = tauri::Builder::default()
        // Mở app lần hai → đưa cửa sổ đang có lên trước.
        .plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| {
            show_main_window(app);
        }))
        .plugin(tauri_plugin_window_state::Builder::default().build())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_deep_link::init())
        .manage(Shared {
            wake: Mutex::new(wake_tx),
            orbstack_missing: AtomicBool::new(false),
        })
        .invoke_handler(tauri::generate_handler![
            open_orbstack,
            retry_now,
            backup_cmds::pick_backup_folder,
            backup_cmds::pick_backup_file,
            backup_cmds::reveal_in_finder
        ])
        .menu(|app| menu::build(app))
        .on_menu_event(|app, event| menu::handle_event(app, event.id().as_ref()))
        // Đóng cửa sổ (nút đỏ, ⌘W) chỉ ẩn đi; ⌘Q mới thoát.
        .on_window_event(|window, event| {
            if let WindowEvent::CloseRequested { api, .. } = event {
                api.prevent_close();
                let _ = window.hide();
            }
        })
        .setup(move |app| {
            let handle = app.handle().clone();
            app.deep_link().on_open_url(move |event| {
                for url in event.urls() {
                    open_deep_link(&handle, url.as_str());
                }
            });
            spawn_health_loop(app.handle().clone(), wake_rx);
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("không khởi tạo được app Tauri");

    app.run(|app, event| {
        // Bấm icon Dock khi cửa sổ đang ẩn → hiện lại.
        if let RunEvent::Reopen { .. } = event {
            show_main_window(app);
        }
    });
}
