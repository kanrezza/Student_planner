//! Liên kết `lichhoc://…` (feature 003, research R10): bấm vào thông báo "quá 3 ngày chưa sao lưu"
//! thì agent mở `lichhoc://cai-dat/sao-luu` và app đưa cửa sổ tới Cài đặt → Sao lưu.
//! Chỉ nhận đúng một đường dẫn trong danh sách cho phép; mọi liên kết khác bị bỏ qua.

const SCHEME_PREFIX: &str = "lichhoc://";
const ALLOWED_PAGES: [&str; 1] = ["cai-dat/sao-luu"];

/// `lichhoc://cai-dat/sao-luu` → `http://127.0.0.1:8080/cai-dat/sao-luu`; liên kết khác → `None`.
pub fn target_url(link: &str, backend_addr: &str) -> Option<String> {
    let page = link.strip_prefix(SCHEME_PREFIX)?.trim_end_matches('/');
    ALLOWED_PAGES
        .contains(&page)
        .then(|| format!("http://{backend_addr}/{page}"))
}

#[cfg(test)]
mod tests {
    use super::*;

    const ADDR: &str = "127.0.0.1:8080";

    #[test]
    fn mo_trang_sao_luu() {
        assert_eq!(
            target_url("lichhoc://cai-dat/sao-luu", ADDR).as_deref(),
            Some("http://127.0.0.1:8080/cai-dat/sao-luu")
        );
        assert!(target_url("lichhoc://cai-dat/sao-luu/", ADDR).is_some());
    }

    #[test]
    fn bo_qua_lien_ket_khac() {
        for link in [
            "lichhoc://session/12",
            "lichhoc://cai-dat",
            "lichhoc://cai-dat/sao-luu/../nhan",
            "lichhoc://cai-dat/sao-luu?x=1",
            "https://cai-dat/sao-luu",
            "lichhoc://",
        ] {
            assert_eq!(target_url(link, ADDR), None, "{link}");
        }
    }
}
