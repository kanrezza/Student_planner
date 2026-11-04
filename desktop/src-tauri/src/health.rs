//! Kiểm tra backend đã sẵn sàng chưa: `GET /api/health` tới 127.0.0.1:8080 bằng TcpStream thuần
//! (không thêm thư viện HTTP — constitution IV, YAGNI).

use std::io::{Read, Write};
use std::net::{SocketAddr, TcpStream};
use std::time::Duration;

pub const BACKEND_ADDR: &str = "127.0.0.1:8080";

#[derive(Debug, PartialEq, Eq)]
pub enum HealthResult {
    /// Backend trả 200.
    Ready,
    /// Có phản hồi nhưng chưa sẵn sàng (ví dụ 502 khi nginx chạy mà backend chưa lên).
    NotReady(u16),
    /// Không kết nối được hoặc phản hồi không hợp lệ.
    Unreachable,
}

/// Lấy mã trạng thái từ dòng đầu của phản hồi, ví dụ `HTTP/1.1 200 OK` → `Some(200)`.
pub fn parse_status_line(line: &str) -> Option<u16> {
    let mut parts = line.split_whitespace();
    let version = parts.next()?;
    if !version.starts_with("HTTP/") {
        return None;
    }
    parts.next()?.parse().ok()
}

pub fn is_ready(status: u16) -> bool {
    status == 200
}

pub fn check_health(addr: &str, timeout: Duration) -> HealthResult {
    let Ok(socket_addr) = addr.parse::<SocketAddr>() else {
        return HealthResult::Unreachable;
    };
    let Ok(mut stream) = TcpStream::connect_timeout(&socket_addr, timeout) else {
        return HealthResult::Unreachable;
    };
    let _ = stream.set_read_timeout(Some(timeout));
    let _ = stream.set_write_timeout(Some(timeout));

    let request = format!("GET /api/health HTTP/1.1\r\nHost: {addr}\r\nConnection: close\r\n\r\n");
    if stream.write_all(request.as_bytes()).is_err() {
        return HealthResult::Unreachable;
    }

    let mut buffer = [0u8; 256];
    let Ok(read) = stream.read(&mut buffer) else {
        return HealthResult::Unreachable;
    };
    let text = String::from_utf8_lossy(&buffer[..read]);
    match text.lines().next().and_then(parse_status_line) {
        Some(status) if is_ready(status) => HealthResult::Ready,
        Some(status) => HealthResult::NotReady(status),
        None => HealthResult::Unreachable,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::net::TcpListener;
    use std::thread;

    /// Dựng máy chủ giả trả đúng một phản hồi rồi đóng.
    fn serve_once(response: &'static str) -> String {
        let listener = TcpListener::bind("127.0.0.1:0").unwrap();
        let addr = listener.local_addr().unwrap().to_string();
        thread::spawn(move || {
            if let Ok((mut stream, _)) = listener.accept() {
                let mut buf = [0u8; 512];
                let _ = stream.read(&mut buf);
                let _ = stream.write_all(response.as_bytes());
            }
        });
        addr
    }

    #[test]
    fn parses_status_lines() {
        assert_eq!(parse_status_line("HTTP/1.1 200 OK"), Some(200));
        assert_eq!(parse_status_line("HTTP/1.1 502 Bad Gateway"), Some(502));
        assert_eq!(parse_status_line("rác không phải HTTP"), None);
        assert_eq!(parse_status_line("HTTP/1.1 abc"), None);
        assert_eq!(parse_status_line(""), None);
    }

    #[test]
    fn only_200_is_ready() {
        assert!(is_ready(200));
        assert!(!is_ready(502));
        assert!(!is_ready(404));
    }

    #[test]
    fn health_200_is_ready() {
        let addr = serve_once("HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n");
        assert_eq!(check_health(&addr, Duration::from_secs(1)), HealthResult::Ready);
    }

    #[test]
    fn health_502_is_not_ready() {
        let addr = serve_once("HTTP/1.1 502 Bad Gateway\r\n\r\n");
        assert_eq!(check_health(&addr, Duration::from_secs(1)), HealthResult::NotReady(502));
    }

    #[test]
    fn health_garbage_is_unreachable() {
        let addr = serve_once("xin chào, không phải HTTP\r\n\r\n");
        assert_eq!(check_health(&addr, Duration::from_secs(1)), HealthResult::Unreachable);
    }

    #[test]
    fn health_refused_is_unreachable() {
        // Cổng vừa giải phóng nên không còn ai nghe.
        let addr = TcpListener::bind("127.0.0.1:0").unwrap().local_addr().unwrap().to_string();
        assert_eq!(check_health(&addr, Duration::from_secs(1)), HealthResult::Unreachable);
    }
}
