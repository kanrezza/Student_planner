"""Thông báo macOS khi quá 3 ngày chưa sao lưu (spec FR-008, research R10).

`stale_notice_due` là hàm thuần (có test). Phần gửi dùng UNUserNotificationCenter (PyObjC); bấm vào
thông báo thì mở `lichhoc://cai-dat/sao-luu` (app Tauri nhận qua deep link và mở Cài đặt → Sao lưu).
"""

from __future__ import annotations

import logging
import subprocess
from datetime import datetime, timedelta

log = logging.getLogger("lichhoc_agent")

STALE_AFTER = timedelta(days=3)
DEEP_LINK = "lichhoc://cai-dat/sao-luu"
TITLE = "Lịch Học Cá Nhân"
BODY = "Đã 3 ngày chưa sao lưu được dữ liệu. Mở Cài đặt → Sao lưu để kiểm tra."

_delegate = None  # giữ tham chiếu: UNUserNotificationCenter không giữ delegate


def stale_notice_due(
    now: datetime,
    last_success_at: datetime | None,
    enabled_since: datetime,
    notified_for: str | None,
    enabled: bool = True,
) -> bool:
    """Gửi đúng một lần cho mỗi mốc: chỉ gửi lại sau khi có bản sao lưu thành công mới (FR-008)."""
    if not enabled:
        return False
    anchor = last_success_at or enabled_since
    if now - anchor <= STALE_AFTER:
        return False
    return notified_for != anchor.isoformat()


def stale_anchor(last_success_at: datetime | None, enabled_since: datetime) -> datetime:
    return last_success_at or enabled_since


def install_delegate() -> bool:
    """Đặt delegate nhận click thông báo. Gọi một lần ở luồng chính khi agent khởi động."""
    global _delegate
    try:
        import UserNotifications as UN
        from Foundation import NSObject

        class Delegate(NSObject):
            def userNotificationCenter_willPresentNotification_withCompletionHandler_(
                self, center, notification, handler
            ):
                handler(
                    UN.UNNotificationPresentationOptionBanner
                    | UN.UNNotificationPresentationOptionList
                )

            def userNotificationCenter_didReceiveNotificationResponse_withCompletionHandler_(
                self, center, response, handler
            ):
                subprocess.run(["open", DEEP_LINK], check=False)
                handler()

        _delegate = Delegate.alloc().init()
        UN.UNUserNotificationCenter.currentNotificationCenter().setDelegate_(_delegate)
        return True
    except Exception as e:  # noqa: BLE001 — chạy ngoài .app (test, --once) hoặc thiếu PyObjC
        log.info("Không đặt được delegate thông báo (%s); bỏ qua thông báo macOS", e)
        return False


def send_stale_notice() -> bool:
    """Gửi thông báo; trả True nếu đã gửi yêu cầu. Chưa được cấp quyền thì ghi log, không lỗi."""
    try:
        import UserNotifications as UN

        center = UN.UNUserNotificationCenter.currentNotificationCenter()

        def send(granted, error):
            if not granted:
                log.warning("Chưa được cấp quyền thông báo (%s): chỉ cảnh báo trong app", error)
                return
            content = UN.UNMutableNotificationContent.alloc().init()
            content.setTitle_(TITLE)
            content.setBody_(BODY)
            request = UN.UNNotificationRequest.requestWithIdentifier_content_trigger_(
                "backup-stale", content, None
            )
            center.addNotificationRequest_withCompletionHandler_(
                request,
                lambda err: log.info("Đã gửi thông báo quá 3 ngày chưa sao lưu (lỗi: %s)", err),
            )

        center.requestAuthorizationWithOptions_completionHandler_(
            UN.UNAuthorizationOptionAlert | UN.UNAuthorizationOptionSound, send
        )
        return True
    except Exception as e:  # noqa: BLE001
        log.warning("Không gửi được thông báo macOS: %s", e)
        return False
