"""เอนจินคำนวณความเสี่ยงขาดสต็อก (Deterministic Rule-Based, ไม่ใช้ AI)

กฎหลัก:
    Days of Cover = สต็อกคงเหลือ / ยอดขายเฉลี่ยต่อวัน (ย้อนหลัง 30 วัน)
    - Days of Cover <  Lead Time          -> CRITICAL_RISK  (เสี่ยงสูง)
    - Lead Time <= Days of Cover <= LT+7  -> WARNING_RISK   (เสี่ยงปานกลาง)
    - Days of Cover >  Lead Time + 7      -> NORMAL         (ยังไม่เสี่ยง)
    - ข้อมูลขาด/ผิดปกติ                   -> HUMAN_REVIEW_NEEDED (ไม่เดา ส่งให้คนตรวจ)
"""
from __future__ import annotations

import math
import re
from pathlib import Path

import numpy as np
import pandas as pd

# รากของโปรเจกต์ = โฟลเดอร์ที่มี data/ อยู่ (ไม่ผูกกับ Google Drive / Colab)
PROJECT_ROOT = Path(__file__).resolve().parents[1]

SNAPSHOT_DATE = pd.Timestamp("2026-07-31")  # วัน Snapshot = "วันนี้" ของระบบ
WARNING_BUFFER_DAYS = 7                      # ส่วนเผื่อของระดับเสี่ยงปานกลาง
SAFETY_DAYS = 14                             # วันสำรองที่ใช้แนะนำจำนวนสั่งซื้อ

RISK_LABELS_TH = {
    "CRITICAL_RISK": "เสี่ยงสูง",
    "WARNING_RISK": "เสี่ยงปานกลาง",
    "NORMAL": "ยังไม่เสี่ยง",
    "HUMAN_REVIEW_NEEDED": "ต้องให้คนตรวจ",
}


def classify_risk(stock, daily_rate, lead_time) -> str:
    """คืนค่าสถานะความเสี่ยงของ 1 SKU (ฟังก์ชันบริสุทธิ์ ทดสอบง่าย)"""
    if pd.isna(lead_time) or lead_time <= 0 or pd.isna(stock) or stock < 0:
        return "HUMAN_REVIEW_NEEDED"
    if stock == 0:
        return "CRITICAL_RISK"
    if pd.isna(daily_rate) or daily_rate <= 0:
        return "NORMAL"  # ไม่มียอดขายเลย -> ไม่มีโอกาสขาดสต็อกจากการขาย
    days_of_cover = stock / daily_rate
    if days_of_cover < lead_time:
        return "CRITICAL_RISK"
    if days_of_cover <= lead_time + WARNING_BUFFER_DAYS:
        return "WARNING_RISK"
    return "NORMAL"


def suggest_order_qty(stock, daily_rate, lead_time, moq) -> int:
    """จำนวนที่แนะนำให้ขอสั่ง (ค่าประมาณ): ให้พอขายตลอด Lead Time + วันสำรอง
    ปัดขึ้นเป็นจำนวนเท่าของ MOQ ถ้าไม่ทราบ MOQ ใช้ 1"""
    if pd.isna(lead_time) or lead_time <= 0 or pd.isna(stock) or pd.isna(daily_rate):
        return 0
    need = daily_rate * (lead_time + SAFETY_DAYS) - stock
    if need <= 0:
        return 0
    step = int(moq) if pd.notna(moq) and moq > 0 else 1
    return int(math.ceil(need / step) * step)


def _clean_category(value):
    """ตัดช่องว่าง + ทำเป็น Title Case เท่านั้น (ไม่เดารวมหมวดที่ความหมายกำกวม)"""
    if pd.isna(value):
        return value
    return " ".join(str(value).split()).title()


def _fmt_pid(val) -> str:
    try:
        return f"SKU-{int(float(val)):04d}"
    except (TypeError, ValueError):
        return str(val)


def _pick(cleaned: Path, raw: Path, name: str) -> Path:
    return cleaned / name if (cleaned / name).exists() else raw / name


def calculate_stock_risk(project_path=None, save=True) -> pd.DataFrame:
    root = Path(project_path) if project_path else PROJECT_ROOT
    cleaned, raw = root / "data" / "cleaned", root / "data" / "raw"

    df_joined = pd.read_csv(cleaned / "joined_products_supplier.csv")
    df_orders = pd.read_csv(_pick(cleaned, raw, "cleaned_orders.csv" if (cleaned / "cleaned_orders.csv").exists() else "orders.csv"))
    df_lines = pd.read_csv(_pick(cleaned, raw, "cleaned_order_lines.csv" if (cleaned / "cleaned_order_lines.csv").exists() else "order_lines.csv"))
    df_inv = pd.read_csv(_pick(cleaned, raw, "cleaned_inventory_snapshot.csv" if (cleaned / "cleaned_inventory_snapshot.csv").exists() else "inventory_snapshot.csv"))

    # --- ยอดขาย 30 วันย้อนหลังจากวัน Snapshot ---
    start_30d = SNAPSHOT_DATE - pd.Timedelta(days=30)
    df_orders["order_date_dt"] = pd.to_datetime(df_orders["order_date"], errors="coerce")
    recent = df_orders[(df_orders["order_date_dt"] >= start_30d) & (df_orders["order_date_dt"] <= SNAPSHOT_DATE)]
    recent_lines = df_lines[df_lines["order_id"].isin(recent["order_id"])]
    sales = recent_lines.groupby("product_id")["quantity"].sum().rename("sales_30d_qty").reset_index()
    sales["product_id"] = sales["product_id"].map(_fmt_pid)

    df_inv = df_inv.copy()
    df_inv["product_id"] = df_inv["product_id"].map(_fmt_pid)

    df = df_joined.merge(df_inv[["product_id", "available_qty", "as_of"]], on="product_id", how="left")
    df = df.merge(sales, on="product_id", how="left")
    df["sales_30d_qty"] = df["sales_30d_qty"].fillna(0)
    df["daily_sales_rate"] = (df["sales_30d_qty"] / 30.0).round(4)
    if "category" in df.columns:
        df["category"] = df["category"].map(_clean_category)

    df["risk_status"] = [
        classify_risk(s, r, lt) for s, r, lt in zip(df["available_qty"], df["daily_sales_rate"], df["lead_time_days"])
    ]

    ok = df["risk_status"] != "HUMAN_REVIEW_NEEDED"
    rate_pos = df["daily_sales_rate"] > 0
    df["days_of_cover"] = np.where(rate_pos & ok, (df["available_qty"] / df["daily_sales_rate"]).round(1), np.nan)
    # เหลือกี่วันก่อน "ถึงเวลาต้องสั่ง" (ค่าติดลบ = เลยกำหนดสั่งแล้ว)
    df["days_until_order"] = np.where(rate_pos & ok, (df["days_of_cover"] - df["lead_time_days"]).round(1), np.nan)
    df["suggested_qty"] = [
        suggest_order_qty(s, r, lt, m) if st != "HUMAN_REVIEW_NEEDED" else 0
        for s, r, lt, m, st in zip(df["available_qty"], df["daily_sales_rate"], df["lead_time_days"],
                                   df["minimum_order_qty"], df["risk_status"])
    ]

    # ปัญหาที่ทำให้ต้องให้คนตรวจ (เก็บเหตุผลไว้แสดงบน UI)
    def reason(row):
        if row["risk_status"] != "HUMAN_REVIEW_NEEDED":
            return ""
        if not re.fullmatch(r"SKU-\d{4}", str(row["product_id"])):
            return "รหัส SKU ไม่ตรงรูปแบบมาตรฐาน (SKU-XXXX) และไม่มี Lead Time ที่เชื่อถือได้"
        if pd.isna(row["lead_time_days"]):
            return "ไม่มีข้อมูล Lead Time ของซัพพลายเออร์"
        if row["lead_time_days"] <= 0:
            return f"Lead Time ผิดปกติ ({row['lead_time_days']:g} วัน)"
        if pd.isna(row["available_qty"]):
            return "ไม่พบข้อมูลสต็อกใน Snapshot"
        return "ข้อมูลสต็อกผิดปกติ"

    df["review_reason"] = df.apply(reason, axis=1)

    # เรียงจากเร่งด่วนที่สุดก่อน
    order = {"CRITICAL_RISK": 0, "WARNING_RISK": 1, "HUMAN_REVIEW_NEEDED": 2, "NORMAL": 3}
    df["_o"] = df["risk_status"].map(order)
    df = df.sort_values(["_o", "days_until_order", "product_id"], na_position="last").drop(columns="_o").reset_index(drop=True)

    if save:
        df.to_csv(cleaned / "stock_risk_summary.csv", index=False)
    return df
