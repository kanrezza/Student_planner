fn main() {
    // Khai báo lệnh của app để cấp quyền từng lệnh trong capabilities/splash.json.
    tauri_build::try_build(
        tauri_build::Attributes::new()
            .app_manifest(tauri_build::AppManifest::new().commands(&[
                "open_orbstack",
                "retry_now",
                "pick_backup_folder",
                "pick_backup_file",
                "reveal_in_finder",
                "open_attachment",
                "save_attachment",
                "clipboard_file_paths",
                "upload_paths",
            ])),
    )
    .expect("không build được app Tauri");
}
