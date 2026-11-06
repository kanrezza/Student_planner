"""SPIKE (feature 003, task T005, research R10): agent có chạy được vòng lặp Cocoa trên luồng chính
(để nhận click thông báo) trong khi luồng nền vẫn gọi EventKit không?

Chạy dưới dạng .app (py2app) bằng `open`. Các bước:
1. Luồng chính: đặt delegate cho UNUserNotificationCenter, xin quyền, gửi 1 thông báo, rồi chạy vòng
   lặp sự kiện Cocoa (PyObjCTools.AppHelper.runConsoleEventLoop).
2. Luồng nền: mỗi 3 giây gọi EKEventStore.sources() (cùng kiểu gọi mà agent thật dùng).
3. Bấm vào thông báo → delegate chạy `open lichhoc://cai-dat/sao-luu` và ghi `clicked: true`.
4. Kết quả ghi vào ~/Library/Application Support/LichHocAgent/spike-notify-result.json.

Tự thoát sau 90 giây (hoặc 15 giây nếu chạy với --auto-exit, dùng khi kiểm tự động không có người bấm).
"""

from __future__ import annotations

import json
import subprocess
import sys
import threading
import time
import traceback
from pathlib import Path

import EventKit
import objc
import UserNotifications as UN
from Foundation import NSObject
from PyObjCTools import AppHelper

RESULT_FILE = Path.home() / "Library/Application Support/LichHocAgent/spike-notify-result.json"
DEEP_LINK = "lichhoc://cai-dat/sao-luu"
result: dict = {
    "eventkit_thread_calls": 0,
    "eventkit_thread_errors": [],
    "authorized": None,
    "notification_sent": False,
    "clicked": False,
}


def save() -> None:
    RESULT_FILE.parent.mkdir(parents=True, exist_ok=True)
    RESULT_FILE.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


class Delegate(NSObject):
    def userNotificationCenter_willPresentNotification_withCompletionHandler_(
        self, center, notification, handler
    ):
        handler(UN.UNNotificationPresentationOptionBanner | UN.UNNotificationPresentationOptionList)

    def userNotificationCenter_didReceiveNotificationResponse_withCompletionHandler_(
        self, center, response, handler
    ):
        result["clicked"] = True
        result["deep_link_exit"] = subprocess.run(["open", DEEP_LINK], check=False).returncode
        save()
        handler()


def eventkit_loop() -> None:
    store = EventKit.EKEventStore.alloc().init()
    while True:
        try:
            result["eventkit_thread_calls"] += 1
            result["eventkit_sources"] = len(store.sources())
        except Exception:  # noqa: BLE001 — spike: ghi lại mọi lỗi
            result["eventkit_thread_errors"].append(traceback.format_exc(limit=2))
        save()
        time.sleep(3)


def send_notification(center) -> None:
    content = UN.UNMutableNotificationContent.alloc().init()
    content.setTitle_("Lịch Học Cá Nhân")
    content.setBody_("Spike: bấm vào thông báo này để thử mở Cài đặt → Sao lưu.")
    request = UN.UNNotificationRequest.requestWithIdentifier_content_trigger_(
        "spike-notify", content, None
    )

    def done(error):
        result["notification_sent"] = error is None
        result["notification_error"] = str(error) if error else None
        save()

    center.addNotificationRequest_withCompletionHandler_(request, done)


def main() -> None:
    center = UN.UNUserNotificationCenter.currentNotificationCenter()
    delegate = Delegate.alloc().init()
    center.setDelegate_(delegate)

    def on_auth(granted, error):
        result["authorized"] = bool(granted)
        result["auth_error"] = str(error) if error else None
        save()
        if granted:
            send_notification(center)

    center.requestAuthorizationWithOptions_completionHandler_(
        UN.UNAuthorizationOptionAlert | UN.UNAuthorizationOptionSound, on_auth
    )
    threading.Thread(target=eventkit_loop, daemon=True).start()
    seconds = 15 if "--auto-exit" in sys.argv else 90
    threading.Timer(seconds, AppHelper.stopEventLoop).start()
    AppHelper.runConsoleEventLoop(installInterrupt=True)
    result["finished_event_loop"] = True
    save()


if __name__ == "__main__":
    objc.setVerbose(False)
    main()
