//! Lệnh cho trang Cài đặt → Sao lưu (feature 003, research R11): chọn thư mục / file sao lưu bằng
//! hộp chọn của macOS và hiện trong Finder. Chỉ ba lệnh này được cấp cho trang tải từ backend
//! (capabilities/backup.json); trang không có quyền plugin nào khác.

use std::path::{Component, Path};
use std::process::Command;

use tauri::AppHandle;
use tauri_plugin_dialog::DialogExt;

/// Chỉ cho mở trong Finder một thư mục có thật hoặc một file `.lhbackup` có thật, đường dẫn tuyệt đối.
pub fn validate_reveal_path(path: &str) -> Result<(), String> {
    let path = Path::new(path);
    if !path.is_absolute() {
        return Err("Đường dẫn phải là đường dẫn đầy đủ".into());
    }
    if path.components().any(|part| matches!(part, Component::ParentDir)) {
        return Err("Đường dẫn không hợp lệ".into());
    }
    let is_backup_file = path.is_file() && path.extension().is_some_and(|ext| ext == "lhbackup");
    if path.is_dir() || is_backup_file {
        Ok(())
    } else {
        Err("Chỉ mở được thư mục hoặc file .lhbackup".into())
    }
}

/// Hộp chọn thư mục; `None` nếu người dùng huỷ.
#[tauri::command]
pub async fn pick_backup_folder(app: AppHandle) -> Option<String> {
    let chosen = app
        .dialog()
        .file()
        .set_title("Chọn thư mục sao lưu")
        .blocking_pick_folder()?;
    chosen.into_path().ok().map(|p| p.to_string_lossy().into_owned())
}

/// Hộp chọn một file `.lhbackup` để khôi phục; `None` nếu người dùng huỷ.
#[tauri::command]
pub async fn pick_backup_file(app: AppHandle) -> Option<String> {
    let chosen = app
        .dialog()
        .file()
        .set_title("Chọn bản sao lưu để khôi phục")
        .add_filter("Bản sao lưu Lịch Học Cá Nhân", &["lhbackup"])
        .blocking_pick_file()?;
    chosen.into_path().ok().map(|p| p.to_string_lossy().into_owned())
}

/// Hiện thư mục hoặc file sao lưu trong Finder.
#[tauri::command]
pub fn reveal_in_finder(path: String) -> Result<(), String> {
    validate_reveal_path(&path)?;
    let mut command = Command::new("open");
    if Path::new(&path).is_file() {
        command.arg("-R");
    }
    command
        .arg(&path)
        .status()
        .map_err(|e| e.to_string())
        .and_then(|status| if status.success() { Ok(()) } else { Err("Không mở được Finder".into()) })
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;

    fn temp_dir(name: &str) -> std::path::PathBuf {
        let dir = std::env::temp_dir().join(format!("lichhoc-test-{name}-{}", std::process::id()));
        let _ = fs::remove_dir_all(&dir);
        fs::create_dir_all(&dir).unwrap();
        dir
    }

    #[test]
    fn nhan_thu_muc_co_that() {
        let dir = temp_dir("dir");
        assert!(validate_reveal_path(dir.to_str().unwrap()).is_ok());
    }

    #[test]
    fn nhan_file_lhbackup_co_that() {
        let dir = temp_dir("file");
        let file = dir.join("LichHoc-2026-11-05-2100-tu-dong.lhbackup");
        fs::write(&file, b"x").unwrap();
        assert!(validate_reveal_path(file.to_str().unwrap()).is_ok());
    }

    #[test]
    fn tu_choi_file_khac_duoi() {
        let dir = temp_dir("other");
        let file = dir.join("ghi-chu.txt");
        fs::write(&file, b"x").unwrap();
        assert!(validate_reveal_path(file.to_str().unwrap()).is_err());
    }

    #[test]
    fn tu_choi_duong_dan_tuong_doi_va_len_thu_muc_cha() {
        assert!(validate_reveal_path("Sao lưu").is_err());
        let dir = temp_dir("parent");
        let sneaky = format!("{}/../", dir.to_str().unwrap());
        assert!(validate_reveal_path(&sneaky).is_err());
    }

    #[test]
    fn tu_choi_duong_dan_khong_ton_tai() {
        assert!(validate_reveal_path("/khong/co/thu/muc/nay").is_err());
    }
}
