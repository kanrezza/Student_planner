"""Info.plist dùng chung cho LichHocAgent.app và app spike.

Khai báo quyền Lịch/Lời nhắc (research R4).
"""

USAGE_TEXT_CALENDAR = "Lịch Học Cá Nhân cần ghi buổi học vào Lịch để nhắc bạn trên Mac và iPhone."
USAGE_TEXT_REMINDERS = (
    "Lịch Học Cá Nhân cần ghi hạn chót công việc vào Lời nhắc để nhắc bạn trên Mac và iPhone."
)

PLIST = {
    "CFBundleIdentifier": "vn.lichhoc.agent",
    "CFBundleName": "LichHocAgent",
    "CFBundleDisplayName": "Lịch Học Cá Nhân – Đồng bộ",
    "CFBundleShortVersionString": "0.1.0",
    "LSUIElement": True,  # chạy nền, không có icon trên Dock
    "NSCalendarsFullAccessUsageDescription": USAGE_TEXT_CALENDAR,
    "NSCalendarsUsageDescription": USAGE_TEXT_CALENDAR,
    "NSRemindersFullAccessUsageDescription": USAGE_TEXT_REMINDERS,
    "NSRemindersUsageDescription": USAGE_TEXT_REMINDERS,
}
