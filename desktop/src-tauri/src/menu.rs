//! Menu macOS tiếng Việt (desktop-shell §3).

use tauri::menu::{AboutMetadata, Menu, MenuItem, PredefinedMenuItem, Submenu};
use tauri::{AppHandle, Manager, Wry};

const ID_SETTINGS: &str = "settings";
const ID_SHORTCUTS: &str = "shortcuts";

pub fn build(app: &AppHandle) -> tauri::Result<Menu<Wry>> {
    let about = PredefinedMenuItem::about(
        app,
        Some("Giới thiệu Lịch Học Cá Nhân"),
        Some(AboutMetadata {
            name: Some("Lịch Học Cá Nhân".into()),
            version: Some(app.package_info().version.to_string()),
            ..Default::default()
        }),
    )?;
    let settings = MenuItem::with_id(app, ID_SETTINGS, "Cài đặt…", true, Some("CmdOrCtrl+,"))?;
    let app_menu = Submenu::with_items(
        app,
        "Lịch Học Cá Nhân",
        true,
        &[
            &about,
            &PredefinedMenuItem::separator(app)?,
            &settings,
            &PredefinedMenuItem::separator(app)?,
            &PredefinedMenuItem::hide(app, Some("Ẩn Lịch Học Cá Nhân"))?,
            &PredefinedMenuItem::hide_others(app, Some("Ẩn ứng dụng khác"))?,
            &PredefinedMenuItem::show_all(app, Some("Hiện tất cả"))?,
            &PredefinedMenuItem::separator(app)?,
            &PredefinedMenuItem::quit(app, Some("Thoát Lịch Học Cá Nhân"))?,
        ],
    )?;

    let edit_menu = Submenu::with_items(
        app,
        "Sửa",
        true,
        &[
            &PredefinedMenuItem::undo(app, Some("Hoàn tác"))?,
            &PredefinedMenuItem::redo(app, Some("Làm lại"))?,
            &PredefinedMenuItem::separator(app)?,
            &PredefinedMenuItem::cut(app, Some("Cắt"))?,
            &PredefinedMenuItem::copy(app, Some("Chép"))?,
            &PredefinedMenuItem::paste(app, Some("Dán"))?,
            &PredefinedMenuItem::select_all(app, Some("Chọn tất cả"))?,
        ],
    )?;

    let window_menu = Submenu::with_items(
        app,
        "Cửa sổ",
        true,
        &[
            &PredefinedMenuItem::minimize(app, Some("Thu nhỏ"))?,
            &PredefinedMenuItem::maximize(app, Some("Phóng to"))?,
            &PredefinedMenuItem::close_window(app, Some("Đóng cửa sổ"))?,
        ],
    )?;

    let shortcuts = MenuItem::with_id(app, ID_SHORTCUTS, "Phím tắt", true, Some("CmdOrCtrl+/"))?;
    let help_menu = Submenu::with_items(app, "Trợ giúp", true, &[&shortcuts])?;

    Menu::with_items(app, &[&app_menu, &edit_menu, &window_menu, &help_menu])
}

/// Mục menu điều khiển trang giao diện bằng hàm toàn cục `window.lichhoc` (desktop-shell §4).
pub fn handle_event(app: &AppHandle, id: &str) {
    let script = match id {
        ID_SETTINGS => "window.lichhoc?.navigate('/cai-dat')",
        ID_SHORTCUTS => "window.lichhoc?.showShortcuts()",
        _ => return,
    };
    if let Some(window) = app.get_webview_window("main") {
        let _ = window.eval(script);
    }
}
