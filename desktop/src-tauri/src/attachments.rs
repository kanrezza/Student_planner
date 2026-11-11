//! Lệnh cho file đính kèm (feature 005, contracts/desktop-commands.md): mở bằng ứng dụng mặc định
//! của macOS, lưu vào Tải về, đọc file đang chép trong Finder và gắn file theo đường dẫn.
//! Chỉ gọi `http://127.0.0.1:8080` (constitution IV) bằng `/usr/bin/curl` có sẵn của macOS — không
//! thêm thư viện HTTP. Capability `attachments` chỉ cấp cho trang tải từ địa chỉ đó.

use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;

use serde::Serialize;
use serde_json::Value;

use crate::health::BACKEND_ADDR;

const CURL: &str = "/usr/bin/curl";
const OPEN: &str = "/usr/bin/open";
const OSASCRIPT: &str = "/usr/bin/osascript";
const CACHE_MAX_AGE_SECS: u64 = 7 * 24 * 3600;

/// Địa chỉ API của backend; mọi lệnh chỉ dựng URL qua hàm này nên không thể gọi host khác.
pub fn api_url(path: &str) -> Result<String, String> {
    if !path.starts_with('/') || path.contains("..") || path.contains('@') || path.contains('\\') {
        return Err("Đường dẫn API không hợp lệ".into());
    }
    Ok(format!("http://{BACKEND_ADDR}/api{path}"))
}

/// Chỉ chấp nhận URL tới đúng `http://127.0.0.1:8080/`.
pub fn is_local_url(url: &str) -> bool {
    url.strip_prefix(&format!("http://{BACKEND_ADDR}/"))
        .is_some_and(|rest| !rest.contains('@') && !rest.starts_with('/'))
}

/// Tên file an toàn để đặt trên đĩa: bỏ thư mục, thay `/` và `:`, bỏ dấu chấm đầu.
pub fn sanitize_file_name(name: &str) -> String {
    let last = name.rsplit(['/', '\\']).next().unwrap_or("");
    let cleaned: String = last
        .chars()
        .map(|c| if c == ':' || c.is_control() { '_' } else { c })
        .collect();
    let trimmed = cleaned.trim().trim_start_matches('.').to_string();
    if trimmed.is_empty() {
        "file".into()
    } else {
        trimmed
    }
}

/// Đường dẫn trong thư mục cache: `<cache>/attachments/<id>/<tên>`; tên đã làm sạch nên không thể
/// thoát khỏi thư mục cache.
pub fn cache_path(cache_dir: &Path, id: i64, name: &str) -> PathBuf {
    cache_dir
        .join("attachments")
        .join(id.to_string())
        .join(sanitize_file_name(name))
}

/// Thêm " (2)", " (3)"… trước phần mở rộng khi `dir/name` đã có.
pub fn unique_download_path(dir: &Path, name: &str) -> PathBuf {
    let name = sanitize_file_name(name);
    let candidate = dir.join(&name);
    if !candidate.exists() {
        return candidate;
    }
    let path = Path::new(&name);
    let stem = path
        .file_stem()
        .map(|s| s.to_string_lossy().into_owned())
        .unwrap_or_default();
    let extension = path
        .extension()
        .map(|e| format!(".{}", e.to_string_lossy()))
        .unwrap_or_default();
    (2..)
        .map(|n| dir.join(format!("{stem} ({n}){extension}")))
        .find(|p| !p.exists())
        .expect("luôn tìm được tên chưa dùng")
}

/// Từ chối mở file có thể chạy chương trình (FR-022).
pub fn refuse_executable(metadata: &Value) -> Result<(), String> {
    if metadata
        .get("is_executable")
        .and_then(Value::as_bool)
        .unwrap_or(false)
    {
        Err(
            "Không mở trực tiếp file có thể chạy chương trình. Hãy tải về nếu bạn tin nguồn."
                .into(),
        )
    } else {
        Ok(())
    }
}

/// Đầu ra của script đọc clipboard (mỗi dòng một đường dẫn tuyệt đối) → danh sách đường dẫn.
pub fn parse_clipboard_paths(output: &str) -> Vec<String> {
    output
        .lines()
        .map(str::trim)
        .filter(|line| line.starts_with('/'))
        .map(String::from)
        .collect()
}

/// Giá trị cho `curl -F`: bọc nháy kép, escape `"` và `\`.
pub fn quote_form_value(value: &str) -> String {
    format!("\"{}\"", value.replace('\\', "\\\\").replace('"', "\\\""))
}

fn curl_json(args: &[&str], url: &str) -> Result<Value, String> {
    if !is_local_url(url) {
        return Err("Chỉ được kết nối tới ứng dụng trên máy này".into());
    }
    let output = Command::new(CURL)
        .args(["-sS", "-m", "30"])
        .args(args)
        .arg(url)
        .output()
        .map_err(|e| format!("Không chạy được curl: {e}"))?;
    serde_json::from_slice(&output.stdout)
        .map_err(|_| "Phản hồi từ ứng dụng không hợp lệ".to_string())
}

fn metadata(id: i64) -> Result<Value, String> {
    let body = curl_json(&[], &api_url(&format!("/attachments/{id}"))?)?;
    if let Some(error) = body.get("error") {
        let message = error
            .get("message")
            .and_then(Value::as_str)
            .unwrap_or("Không tìm thấy file");
        return Err(message.to_string());
    }
    Ok(body)
}

fn download_to(id: i64, path: &Path) -> Result<(), String> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|e| format!("Không tạo được thư mục: {e}"))?;
    }
    let url = api_url(&format!("/attachments/{id}/download"))?;
    if !is_local_url(&url) {
        return Err("Chỉ được kết nối tới ứng dụng trên máy này".into());
    }
    let partial = path.with_extension("part");
    let status = Command::new(CURL)
        .args(["-sS", "--fail", "-m", "600", "-o"])
        .arg(&partial)
        .arg(&url)
        .status()
        .map_err(|e| format!("Không chạy được curl: {e}"))?;
    if !status.success() {
        let _ = fs::remove_file(&partial);
        return Err("Không tải được file từ ứng dụng".into());
    }
    fs::rename(&partial, path).map_err(|e| format!("Không lưu được file: {e}"))
}

fn cache_dir() -> PathBuf {
    let home = std::env::var_os("HOME")
        .map(PathBuf::from)
        .unwrap_or_else(std::env::temp_dir);
    home.join("Library/Caches/vn.lichhoc.desktop")
}

/// Dọn mục cache cũ hơn 7 ngày; gọi khi app khởi động.
pub fn clean_cache() {
    let root = cache_dir().join("attachments");
    let Ok(entries) = fs::read_dir(&root) else {
        return;
    };
    for entry in entries.flatten() {
        let old = entry
            .metadata()
            .and_then(|m| m.modified())
            .ok()
            .and_then(|m| m.elapsed().ok())
            .is_some_and(|age| age.as_secs() > CACHE_MAX_AGE_SECS);
        if old {
            let _ = fs::remove_dir_all(entry.path());
        }
    }
}

fn open_impl(id: i64) -> Result<(), String> {
    let info = metadata(id)?;
    refuse_executable(&info)?;
    let name = info
        .get("display_name")
        .and_then(Value::as_str)
        .unwrap_or("file");
    let expected = info.get("size").and_then(Value::as_u64);
    let path = cache_path(&cache_dir(), id, name);
    let cached = fs::metadata(&path).ok().map(|m| m.len());
    if cached.is_none() || cached != expected {
        download_to(id, &path)?;
    }
    let status = Command::new(OPEN)
        .arg(&path)
        .status()
        .map_err(|e| format!("Không mở được file: {e}"))?;
    if status.success() {
        Ok(())
    } else {
        Err("macOS không mở được file này".into())
    }
}

fn save_impl(id: i64) -> Result<String, String> {
    let info = metadata(id)?;
    let name = info
        .get("display_name")
        .and_then(Value::as_str)
        .unwrap_or("file");
    let downloads = std::env::var_os("HOME")
        .map(|home| PathBuf::from(home).join("Downloads"))
        .ok_or("Không tìm thấy thư mục Tải về")?;
    fs::create_dir_all(&downloads).map_err(|e| format!("Không tạo được thư mục Tải về: {e}"))?;
    let target = unique_download_path(&downloads, name);
    download_to(id, &target)?;
    Ok(target.to_string_lossy().into_owned())
}

const CLIPBOARD_SCRIPT: &str = r#"
ObjC.import('AppKit');
var items = $.NSPasteboard.generalPasteboard.pasteboardItems;
var out = [];
for (var i = 0; items && i < items.count; i++) {
  var url = items.objectAtIndex(i).stringForType('public.file-url');
  if (!url.isNil()) { out.push(ObjC.unwrap($.NSURL.URLWithString(url).path)); }
}
out.join('\n');
"#;

fn clipboard_impl() -> Vec<String> {
    Command::new(OSASCRIPT)
        .args(["-l", "JavaScript", "-e", CLIPBOARD_SCRIPT])
        .output()
        .map(|o| parse_clipboard_paths(&String::from_utf8_lossy(&o.stdout)))
        .unwrap_or_default()
}

#[derive(Serialize, Default)]
pub struct UploadError {
    name: String,
    message: String,
}

#[derive(Serialize, Default)]
pub struct UploadResult {
    uploaded: u32,
    errors: Vec<UploadError>,
}

fn upload_one(owner_type: &str, owner_id: i64, path: &Path) -> Result<(), String> {
    if path.is_dir() {
        return Err("Chỉ gắn được file, không gắn thư mục".into());
    }
    if !path.is_file() {
        return Err("Không đọc được file này".into());
    }
    let name = path
        .file_name()
        .map(|n| n.to_string_lossy().into_owned())
        .unwrap_or_default();
    let file_field = format!(
        "file=@{};filename={}",
        quote_form_value(&path.to_string_lossy()),
        quote_form_value(&name)
    );
    let owner_field = format!("owner_type={owner_type}");
    let id_field = format!("owner_id={owner_id}");
    let body = curl_json(
        &[
            "-X",
            "POST",
            "-F",
            &owner_field,
            "-F",
            &id_field,
            "-F",
            &file_field,
            "-m",
            "600",
        ],
        &api_url("/attachments")?,
    )?;
    if let Some(first) = body
        .get("errors")
        .and_then(Value::as_array)
        .and_then(|e| e.first())
    {
        let message = first
            .get("message")
            .and_then(Value::as_str)
            .unwrap_or("Không gắn được file");
        return Err(message.to_string());
    }
    if let Some(error) = body.get("error") {
        let message = error
            .get("message")
            .and_then(Value::as_str)
            .unwrap_or("Không gắn được file");
        return Err(message.to_string());
    }
    Ok(())
}

fn upload_impl(owner_type: &str, owner_id: i64, paths: &[String]) -> UploadResult {
    let mut result = UploadResult::default();
    for raw in paths {
        let path = Path::new(raw);
        match upload_one(owner_type, owner_id, path) {
            Ok(()) => result.uploaded += 1,
            Err(message) => result.errors.push(UploadError {
                name: path
                    .file_name()
                    .map(|n| n.to_string_lossy().into_owned())
                    .unwrap_or_default(),
                message,
            }),
        }
    }
    result
}

async fn blocking<T: Send + 'static>(
    work: impl FnOnce() -> T + Send + 'static,
) -> Result<T, String> {
    tauri::async_runtime::spawn_blocking(work)
        .await
        .map_err(|e| e.to_string())
}

/// Mở file đính kèm bằng ứng dụng mặc định của macOS.
#[tauri::command]
pub async fn open_attachment(id: i64) -> Result<(), String> {
    blocking(move || open_impl(id)).await?
}

/// Lưu file đính kèm vào Tải về; trả đường dẫn đã lưu.
#[tauri::command]
pub async fn save_attachment(id: i64) -> Result<String, String> {
    blocking(move || save_impl(id)).await?
}

/// Đường dẫn các file đang chép trong Finder.
#[tauri::command]
pub async fn clipboard_file_paths() -> Result<Vec<String>, String> {
    blocking(clipboard_impl).await
}

/// Gắn các file theo đường dẫn vào một nơi.
#[tauri::command]
pub async fn upload_paths(
    owner_type: String,
    owner_id: i64,
    paths: Vec<String>,
) -> Result<UploadResult, String> {
    if !["task", "subject", "session", "exam"].contains(&owner_type.as_str()) {
        return Err("Loại nơi đính kèm không hợp lệ".into());
    }
    blocking(move || upload_impl(&owner_type, owner_id, &paths)).await
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    fn temp_dir(name: &str) -> PathBuf {
        let dir = std::env::temp_dir().join(format!("lichhoc-att-{name}-{}", std::process::id()));
        let _ = fs::remove_dir_all(&dir);
        fs::create_dir_all(&dir).unwrap();
        dir
    }

    #[test]
    fn chi_dung_url_127_0_0_1_8080() {
        assert!(is_local_url("http://127.0.0.1:8080/api/attachments/1"));
        for url in [
            "http://evil.example/api/attachments/1",
            "http://127.0.0.1:8081/api/x",
            "https://127.0.0.1:8080/api/x",
            "http://127.0.0.1:8080@evil.example/x",
            "http://127.0.0.1:8080//evil.example/x",
            "http://localhost:8080/api/x",
        ] {
            assert!(!is_local_url(url), "{url}");
        }
        assert_eq!(
            api_url("/attachments/5").unwrap(),
            "http://127.0.0.1:8080/api/attachments/5"
        );
        assert!(api_url("attachments").is_err());
        assert!(api_url("/../etc").is_err());
        assert!(api_url("/a@evil.example").is_err());
    }

    #[test]
    fn ten_file_khong_thoat_khoi_cache() {
        assert_eq!(sanitize_file_name("../../etc/passwd"), "passwd");
        assert_eq!(sanitize_file_name("a/b\\c.pdf"), "c.pdf");
        assert_eq!(sanitize_file_name(".bashrc"), "bashrc");
        assert_eq!(sanitize_file_name("Đề cương: NLP.pdf"), "Đề cương_ NLP.pdf");
        assert_eq!(sanitize_file_name("   "), "file");
        let cache = Path::new("/tmp/cache");
        let path = cache_path(cache, 7, "../../x.pdf");
        assert!(path.starts_with("/tmp/cache/attachments/7"));
        assert_eq!(path.file_name().unwrap(), "x.pdf");
    }

    #[test]
    fn tai_ve_trung_ten_them_hau_to() {
        let dir = temp_dir("dl");
        assert_eq!(unique_download_path(&dir, "a.pdf"), dir.join("a.pdf"));
        fs::write(dir.join("a.pdf"), b"1").unwrap();
        assert_eq!(unique_download_path(&dir, "a.pdf"), dir.join("a (2).pdf"));
        fs::write(dir.join("a (2).pdf"), b"2").unwrap();
        assert_eq!(unique_download_path(&dir, "a.pdf"), dir.join("a (3).pdf"));
        fs::write(dir.join("ghi chu"), b"").unwrap();
        assert_eq!(
            unique_download_path(&dir, "ghi chu"),
            dir.join("ghi chu (2)")
        );
    }

    #[test]
    fn tu_choi_file_thuc_thi() {
        assert!(refuse_executable(&json!({"is_executable": true})).is_err());
        assert!(refuse_executable(&json!({"is_executable": false})).is_ok());
        assert!(refuse_executable(&json!({})).is_ok());
    }

    #[test]
    fn doc_duong_dan_tu_clipboard() {
        let output = "/Users/a/De cuong.pdf\n/Users/a/Đề thi 2025.pdf\n\n";
        assert_eq!(
            parse_clipboard_paths(output),
            vec![
                "/Users/a/De cuong.pdf".to_string(),
                "/Users/a/Đề thi 2025.pdf".to_string()
            ]
        );
        assert!(parse_clipboard_paths("").is_empty());
        assert!(parse_clipboard_paths("lỗi: không có\nfile:///x").is_empty());
    }

    #[test]
    fn gia_tri_form_duoc_escape() {
        assert_eq!(quote_form_value("a;b,c.pdf"), "\"a;b,c.pdf\"");
        assert_eq!(quote_form_value("a\"b\\c"), "\"a\\\"b\\\\c\"");
    }

    #[test]
    fn thu_muc_va_file_khong_co_bi_tu_choi_khi_gan() {
        let dir = temp_dir("up");
        assert_eq!(
            upload_one("task", 1, &dir).unwrap_err(),
            "Chỉ gắn được file, không gắn thư mục"
        );
        assert!(upload_one("task", 1, &dir.join("khong-co")).is_err());
    }
}
