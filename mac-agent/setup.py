"""Đóng gói mac-agent thành LichHocAgent.app bằng py2app.

Phải là .app có Info.plist: từ macOS 14, quyền Lịch/Lời nhắc chỉ được cấp cho tiến trình khai báo
NSCalendarsFullAccessUsageDescription và NSRemindersFullAccessUsageDescription (research R4).

Build: python setup.py py2app
"""

from setuptools import setup

from app_plist import PLIST

setup(
    name="LichHocAgent",
    app=["lichhoc_agent/main.py"],
    options={
        "py2app": {
            "plist": PLIST,
            "packages": ["lichhoc_agent"],
            "includes": ["EventKit", "Foundation"],
        }
    },
    setup_requires=["py2app"],
)
