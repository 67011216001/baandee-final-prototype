"""FastAPI: ให้บริการ Dashboard + API ของ BaanDee Stockout Risk

รัน:  uvicorn api.main:app --reload     แล้วเปิด http://127.0.0.1:8000
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import risk  # noqa: E402
import storage  # noqa: E402

app = FastAPI(title="BaanDee Stockout Risk API", version="1.0")
WEB_DIR = ROOT / "web"


def project_root() -> Path:
    """ปรับรากโปรเจกต์ได้ผ่าน env BAANDEE_ROOT (ใช้ตอนเทสต์ให้ไม่ไปเขียนทับข้อมูลจริง)"""
    return Path(os.environ.get("BAANDEE_ROOT", ROOT))


def _records(df: pd.DataFrame) -> list[dict]:
    return json.loads(df.to_json(orient="records", force_ascii=False))  # NaN -> null


def _risk_df() -> pd.DataFrame:
    try:
        return risk.calculate_stock_risk(project_root(), save=False)
    except FileNotFoundError as e:
        raise HTTPException(503, f"ไม่พบไฟล์ข้อมูล: {Path(e.filename).name if e.filename else e}")


# ---------------------------------------------------------------- Risk
@app.get("/api/summary")
def summary():
    df = _risk_df()
    counts = df["risk_status"].value_counts().to_dict()
    return {
        "total": len(df),
        "counts": {k: int(counts.get(k, 0)) for k in risk.RISK_LABELS_TH},
        "labels": risk.RISK_LABELS_TH,
        "snapshot_date": str(risk.SNAPSHOT_DATE.date()),
        "categories": sorted(df["category"].dropna().unique().tolist()),
    }


@app.get("/api/risk")
def list_risk(status: str | None = None, category: str | None = None, q: str | None = Query(None)):
    df = _risk_df()
    if status:
        df = df[df["risk_status"] == status]
    if category:
        df = df[df["category"] == category]
    if q:
        key = q.strip().lower()
        df = df[df["product_id"].str.lower().str.contains(key, na=False)
                | df["product_name"].str.lower().str.contains(key, na=False)]
    return _records(df)


@app.get("/api/risk/{product_id}")
def get_risk(product_id: str):
    df = _risk_df()
    row = df[df["product_id"].str.upper() == product_id.upper()]
    if row.empty:
        raise HTTPException(404, "ไม่พบ SKU นี้")
    return _records(row)[0]


# ------------------------------------------------- Cross-system boundary
@app.get("/get_supplier_lead_time_api")
def get_supplier_lead_time_api(product_id: str):
    """200 พบข้อมูล / 404 ไม่พบหรือข้อมูลไม่สมบูรณ์ (ส่งให้คนตรวจ) / 503 ระบบต้นทางใช้ไม่ได้"""
    f = project_root() / "data" / "generated" / "supplier_lead_time.csv"
    try:
        df = pd.read_csv(f)
    except (FileNotFoundError, pd.errors.EmptyDataError, pd.errors.ParserError):
        return JSONResponse(status_code=503, content={
            "status": "SERVICE_UNAVAILABLE", "message": "ระบบข้อมูลซัพพลายเออร์ไม่พร้อมใช้งาน"})

    pid = risk._fmt_pid(product_id.replace("SKU-", "")) if product_id.upper().startswith("SKU-") and product_id[4:].isdigit() else product_id
    df["_pid"] = df["product_id"].map(risk._fmt_pid)
    row = df[df["_pid"] == pid]
    if row.empty:
        return JSONResponse(status_code=404, content={
            "status": "HUMAN_REVIEW_NEEDED", "message": f"ไม่พบ {product_id} ในข้อมูลซัพพลายเออร์"})
    r = row.iloc[0]
    lt = r["lead_time_days"]
    if pd.isna(lt) or lt <= 0:
        return JSONResponse(status_code=404, content={
            "status": "HUMAN_REVIEW_NEEDED", "product_id": pid,
            "message": "Lead Time ขาดหายหรือผิดปกติ ต้องให้คนตรวจสอบ"})
    return {"status": "OK", "product_id": pid, "supplier_name": r["supplier_name"],
            "lead_time_days": float(lt), "last_updated": r.get("last_updated")}


# ---------------------------------------------------- Reorder requests
class NewRequest(BaseModel):
    product_id: str
    requested_qty: int = Field(gt=0)


class PatchRequest(BaseModel):
    requested_qty: int | None = Field(default=None, gt=0)
    status: str | None = None


@app.get("/api/requests")
def list_requests(include_deleted: bool = False):
    df = storage.get_reorder_requests(project_root(), include_deleted=include_deleted)
    return _records(df.iloc[::-1]) if not df.empty else []


@app.post("/api/requests", status_code=201)
def create_request(body: NewRequest):
    df = _risk_df()
    row = df[df["product_id"].str.upper() == body.product_id.upper()]
    if row.empty:
        raise HTTPException(404, "ไม่พบ SKU นี้")
    r = row.iloc[0]
    if r["risk_status"] == "HUMAN_REVIEW_NEEDED":
        raise HTTPException(409, "SKU นี้ข้อมูลไม่สมบูรณ์ ต้องให้คนตรวจก่อน จึงยังสร้างร่างไม่ได้")
    return storage.create_reorder_request(
        project_root(), r["product_id"], body.requested_qty, r["product_name"], r["risk_status"])


@app.patch("/api/requests/{request_id}")
def patch_request(request_id: str, body: PatchRequest):
    root = project_root()
    if body.requested_qty is None and body.status is None:
        raise HTTPException(422, "ไม่มีข้อมูลที่จะแก้ไข")
    try:
        ok = True
        if body.requested_qty is not None:
            ok = storage.update_request_qty(root, request_id, body.requested_qty) and ok
        if body.status is not None:
            ok = storage.update_request_status(root, request_id, body.status) and ok
    except ValueError as e:
        raise HTTPException(422, str(e))
    if not ok:
        raise HTTPException(404, "ไม่พบร่างคำขอนี้")
    return {"ok": True}


@app.delete("/api/requests/{request_id}")
def delete_request(request_id: str):
    if not storage.soft_delete_request(project_root(), request_id):
        raise HTTPException(404, "ไม่พบร่างคำขอนี้")
    return {"ok": True, "soft_deleted": True}


# ------------------------------------------------------------ Frontend
@app.get("/", include_in_schema=False)
def index():
    return FileResponse(WEB_DIR / "index.html")


app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")
