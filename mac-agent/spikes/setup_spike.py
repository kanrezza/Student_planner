"""Đóng gói spike EventKit thành LichHocSpike.app (cùng Info.plist quyền như app thật, khác bundle id).

Build (trong mac-agent/):
  cd spikes && ../.venv/bin/python setup_spike.py py2app --dist-dir dist --bdist-base build
  codesign --force --deep -s - dist/LichHocSpike.app
Chạy (trong spikes/):  open dist/LichHocSpike.app
"""

import sys
from pathlib import Path

from setuptools import setup

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app_plist import PLIST  # noqa: E402  (dùng chung khai báo quyền với app thật)

setup(
    name="LichHocSpike",
    app=[str(Path(__file__).with_name("eventkit_spike.py"))],
    options={
        "py2app": {
            "plist": {
                **PLIST,
                "CFBundleIdentifier": "vn.lichhoc.spike",
                "CFBundleName": "LichHocSpike",
            },
            "includes": ["EventKit", "Foundation"],
        }
    },
)
