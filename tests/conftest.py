import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))


@pytest.fixture()
def sandbox(tmp_path, monkeypatch):
    """คัดลอกโฟลเดอร์ data ไปที่ชั่วคราว เพื่อให้เทสต์ไม่แตะข้อมูลจริง และรันซ้ำได้ผลเดิมทุกครั้ง"""
    shutil.copytree(ROOT / "data", tmp_path / "data")
    (tmp_path / "data" / "app_state" / "reorder_requests.csv").unlink(missing_ok=True)
    monkeypatch.setenv("BAANDEE_ROOT", str(tmp_path))
    return tmp_path
