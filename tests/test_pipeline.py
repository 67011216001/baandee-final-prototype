"""5 Test Cases ตาม TEST_CASES.md (รันซ้ำได้ผลเดิมเสมอ เพราะใช้ข้อมูลสำเนาชั่วคราว)"""
import pandas as pd
from fastapi.testclient import TestClient

import risk
import storage


def client():
    from api.main import app
    return TestClient(app)


# TC-01 สต็อกพอ -> NORMAL  (50 วัน > Lead Time 14 + 7)
def test_tc01_normal():
    assert risk.classify_risk(stock=5, daily_rate=0.1, lead_time=14) == "NORMAL"


# TC-02 สต็อกหมด หรือ Days of Cover < Lead Time -> CRITICAL_RISK
def test_tc02_critical():
    assert risk.classify_risk(0, 0.5, 14) == "CRITICAL_RISK"
    assert risk.classify_risk(5, 0.6, 14) == "CRITICAL_RISK"   # 8.3 วัน < 14 วัน
    assert risk.classify_risk(10, 0.6, 14) == "WARNING_RISK"   # 16.7 วัน อยู่ระหว่าง 14..21
    assert risk.classify_risk(25, 0.6, 14) == "NORMAL"         # 41.7 วัน


# TC-03 Lead Time ขาด/ติดลบ -> HUMAN_REVIEW_NEEDED ไม่เดาค่า
def test_tc03_human_review(sandbox):
    assert risk.classify_risk(24, 0.67, float("nan")) == "HUMAN_REVIEW_NEEDED"
    assert risk.classify_risk(24, 0.67, -5) == "HUMAN_REVIEW_NEEDED"
    df = risk.calculate_stock_risk(sandbox, save=False).set_index("product_id")
    assert df.loc["SKU-0015", "risk_status"] == "HUMAN_REVIEW_NEEDED"   # NaN
    assert df.loc["SKU-0060", "risk_status"] == "HUMAN_REVIEW_NEEDED"   # ติดลบ
    assert df.loc["SKU-0015", "review_reason"] != ""
    # API ฝั่งซัพพลายเออร์ต้องตอบ 404 ไม่ใช่ค่าเดา
    c = client()
    assert c.get("/get_supplier_lead_time_api", params={"product_id": "SKU-0015"}).status_code == 404
    # และห้ามสร้างร่างคำขอให้ SKU ที่ข้อมูลไม่พร้อม
    r = c.post("/api/requests", json={"product_id": "SKU-0015", "requested_qty": 10})
    assert r.status_code == 409


# TC-04 สร้างร่างคำขอ แล้วข้อมูลคงอยู่ถาวร (อ่านจากไฟล์ใหม่ได้)
def test_tc04_create_and_persist(sandbox):
    c = client()
    r = c.post("/api/requests", json={"product_id": "SKU-0001", "requested_qty": 50})
    assert r.status_code == 201 and r.json()["status"] == "Draft"
    # จำลอง "ปิดแล้วเปิดโปรแกรมใหม่": อ่านไฟล์ตรง ๆ
    saved = pd.read_csv(storage.get_storage_path(sandbox))
    assert saved.loc[0, "product_id"] == "SKU-0001" and saved.loc[0, "requested_qty"] == 50
    assert c.patch(f"/api/requests/{r.json()['request_id']}", json={"status": "Approved"}).status_code == 200
    assert client().get("/api/requests").json()[0]["status"] == "Approved"


# TC-05 Soft Delete: ซ่อนจากหน้าจอ แต่แถวยังอยู่ในไฟล์
def test_tc05_soft_delete(sandbox):
    c = client()
    rid = c.post("/api/requests", json={"product_id": "SKU-0002", "requested_qty": 20}).json()["request_id"]
    assert c.delete(f"/api/requests/{rid}").status_code == 200
    assert c.get("/api/requests").json() == []
    raw = pd.read_csv(storage.get_storage_path(sandbox))
    assert len(raw) == 1 and str(raw.loc[0, "is_deleted"]).lower() == "true"


# ---- เทสต์เสริม: ขอบเขต API ครบ 3 สถานการณ์ + การตรวจสอบข้อมูลเข้า ----
def test_api_200_404_503(sandbox):
    c = client()
    ok = c.get("/get_supplier_lead_time_api", params={"product_id": "SKU-0001"})
    assert ok.status_code == 200 and ok.json()["lead_time_days"] == 14.0
    assert c.get("/get_supplier_lead_time_api", params={"product_id": "SKU-9999"}).status_code == 404
    (sandbox / "data" / "generated" / "supplier_lead_time.csv").unlink()
    assert c.get("/get_supplier_lead_time_api", params={"product_id": "SKU-0001"}).status_code == 503


def test_validation_and_counts(sandbox):
    c = client()
    assert c.post("/api/requests", json={"product_id": "SKU-0001", "requested_qty": 0}).status_code == 422
    assert c.post("/api/requests", json={"product_id": "SKU-NOPE", "requested_qty": 5}).status_code == 404
    counts = c.get("/api/summary").json()["counts"]
    assert sum(counts.values()) == 82
    cats = c.get("/api/summary").json()["categories"]
    assert all(x == x.title() for x in cats)   # หมวดสินค้าสะกดเป็นมาตรฐานแล้ว
