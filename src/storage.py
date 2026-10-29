"""จัดเก็บร่างคำขอสั่งซื้อ (Reorder Request) ลง CSV แบบถาวร: Create / Read / Update / Soft Delete

หมายเหตุ: เป็น "ร่างภายใน" เพื่อให้หัวหน้าอนุมัติ ไม่ได้ส่งใบสั่งซื้อจริงไปหาซัพพลายเออร์
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]

COLUMNS = [
    "request_id", "product_id", "product_name", "requested_qty",
    "risk_status", "status", "created_at", "updated_at", "is_deleted",
]
VALID_STATUS = {"Draft", "Approved"}


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_storage_path(project_path=None) -> Path:
    root = Path(project_path) if project_path else PROJECT_ROOT
    p = root / "data" / "app_state"
    p.mkdir(parents=True, exist_ok=True)
    return p / "reorder_requests.csv"


def init_storage(project_path=None) -> Path:
    sf = get_storage_path(project_path)
    if not sf.exists():
        pd.DataFrame(columns=COLUMNS).to_csv(sf, index=False)
    return sf


def _read(sf: Path) -> pd.DataFrame:
    df = pd.read_csv(sf)
    for col in COLUMNS:  # กันไฟล์เก่าที่คอลัมน์ไม่ครบ
        if col not in df.columns:
            df[col] = None
    return df


def create_reorder_request(project_path, product_id, requested_qty, product_name="-", risk_status="UNKNOWN") -> dict:
    qty = int(requested_qty)
    if qty <= 0:
        raise ValueError("requested_qty ต้องมากกว่า 0")
    sf = init_storage(project_path)
    df = _read(sf)

    # นับรวมแถวที่ถูก soft delete ด้วย เพื่อไม่ให้รหัสซ้ำ
    request_id = f"REQ-{len(df) + 1:04d}"
    now = _now()
    row = {
        "request_id": request_id, "product_id": str(product_id), "product_name": str(product_name),
        "requested_qty": qty, "risk_status": str(risk_status), "status": "Draft",
        "created_at": now, "updated_at": now, "is_deleted": False,
    }
    pd.concat([df, pd.DataFrame([row])], ignore_index=True).to_csv(sf, index=False)
    return row


def get_reorder_requests(project_path=None, include_deleted=False) -> pd.DataFrame:
    df = _read(init_storage(project_path))
    if df.empty:
        return df
    df["is_deleted"] = df["is_deleted"].astype(str).str.lower() == "true"
    if not include_deleted:
        df = df[~df["is_deleted"]]
    return df


def _update(project_path, request_id, **fields) -> bool:
    sf = init_storage(project_path)
    df = _read(sf)
    if df.empty or request_id not in df["request_id"].values:
        return False
    mask = df["request_id"] == request_id
    for k, v in fields.items():
        df.loc[mask, k] = v
    df.loc[mask, "updated_at"] = _now()
    df.to_csv(sf, index=False)
    return True


def update_request_status(project_path, request_id, new_status="Approved") -> bool:
    if new_status not in VALID_STATUS:
        raise ValueError(f"status ต้องเป็นหนึ่งใน {sorted(VALID_STATUS)}")
    return _update(project_path, request_id, status=new_status)


def update_request_qty(project_path, request_id, new_qty) -> bool:
    qty = int(new_qty)
    if qty <= 0:
        raise ValueError("requested_qty ต้องมากกว่า 0")
    return _update(project_path, request_id, requested_qty=qty)


def soft_delete_request(project_path, request_id) -> bool:
    """ซ่อนรายการโดยไม่ลบแถวออกจากไฟล์ (Audit Trail)"""
    return _update(project_path, request_id, is_deleted=True)
