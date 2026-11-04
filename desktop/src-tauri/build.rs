fn main() {
    // Khai báo lệnh của app để cấp quyền từng lệnh trong capabilities/splash.json.
    tauri_build::try_build(
        tauri_build::Attributes::new()
            .app_manifest(tauri_build::AppManifest::new().commands(&["open_orbstack", "retry_now"])),
    )
    .expect("không build được app Tauri");
}
