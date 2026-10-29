
# =============================================================================
# AUTOMATED SYSTEM TEST SUITE (5 TEST CASES)
# File: tests/test_system.py
# Project: BaanDee Stockout Risk Management Prototype
# =============================================================================

from pathlib import Path
import os
import sys
import tempfile

import pandas as pd

# -----------------------------------------------------------------------------
# 1. Set project root and import backend modules
# -----------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from api.main import get_supplier_lead_time_api
from src.risk import calculate_stock_risk
from src.storage import (
    create_reorder_request,
    get_reorder_requests,
    soft_delete_request,
    update_request_status,
)


def record_result(results, test_id, test_name, test_input,
                  expected, actual, passed):
    """เก็บผลการทดสอบแต่ละกรณี"""
    results.append({
        "test_id": test_id,
        "test_name": test_name,
        "input": test_input,
        "expected": expected,
        "actual": str(actual),
        "status": "PASS" if passed else "FAIL",
    })


def run_system_tests():
    """รันทดสอบระบบ 5 กรณี และบันทึกผลลง test_results.csv"""

    results = []
    app_state_dir = BASE_DIR / "data" / "app_state"
    app_state_dir.mkdir(parents=True, exist_ok=True)

   
    # -------------------------------------------------------------------------
    # TC-01: Invalid Data Detection and Human Review
    # ตรวจว่าระบบระบุข้อมูลผิดปกติและให้เหตุผลสำหรับตรวจสอบได้
    # -------------------------------------------------------------------------
    try:
        df_risk = calculate_stock_risk(BASE_DIR, save=False)

        required_columns = {
            "product_id",
            "risk_status",
            "review_reason",
        }

        missing_columns = required_columns - set(df_risk.columns)

        if missing_columns:
            raise ValueError(
                f"ไม่พบคอลัมน์ที่จำเป็น: {sorted(missing_columns)}"
            )

        review_rows = df_risk[
            df_risk["risk_status"] == "HUMAN_REVIEW_NEEDED"
        ]

        review_count = len(review_rows)

        reasons_filled = (
            review_rows["review_reason"]
            .fillna("")
            .astype(str)
            .str.strip()
            .ne("")
        )

        reasons_count = int(reasons_filled.sum())

        passed = (
            review_count >= 2
            and reasons_count == review_count
        )

        actual = (
            f"ประมวลผล {len(df_risk)} SKUs; "
            f"ต้องตรวจสอบ {review_count} รายการ; "
            f"มีเหตุผลประกอบ {reasons_count} รายการ"
        )

    except Exception as exc:
        passed = False
        actual = f"{type(exc).__name__}: {exc}"

    record_result(
        results,
        "TC-01",
        "Invalid Data Detection and Human Review",
        "ข้อมูลสินค้า สต็อก และ Supplier Lead Time",
        "พบข้อมูลที่ต้องตรวจสอบอย่างน้อย 2 รายการ "
        "และทุกรายการมีเหตุผลประกอบ",
        actual,
        passed,
    )

    # -------------------------------------------------------------------------
    # TC-02: Supplier API Boundary (200, 404, 503)
    # ทดสอบผ่านฟังก์ชัน API จริง โดยใช้โฟลเดอร์ชั่วคราว
    # เพื่อไม่แก้ไขไฟล์ข้อมูลจริงของโปรเจกต์
    # -------------------------------------------------------------------------
    original_root = os.environ.get("BAANDEE_ROOT")

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            api_root = Path(temp_dir)
            generated_dir = api_root / "data" / "generated"
            generated_dir.mkdir(parents=True)

            supplier_file = generated_dir / "supplier_lead_time.csv"
            pd.DataFrame([{
                "product_id": "SKU-0001",
                "lead_time_days": 7,
                "supplier_name": "Test Supplier",
                "last_updated": "2026-10-30",
            }]).to_csv(supplier_file, index=False)

            os.environ["BAANDEE_ROOT"] = str(api_root)

            res_200 = get_supplier_lead_time_api("SKU-0001")
            res_404 = get_supplier_lead_time_api("SKU-9999")

            code_200 = (
                200 if isinstance(res_200, dict)
                else getattr(res_200, "status_code", None)
            )
            code_404 = getattr(res_404, "status_code", 200)

            # จำลองระบบต้นทางไม่พร้อมใช้งาน ด้วยโฟลเดอร์ที่ไม่มี CSV
            unavailable_root = api_root / "unavailable"
            unavailable_root.mkdir()
            os.environ["BAANDEE_ROOT"] = str(unavailable_root)

            res_503 = get_supplier_lead_time_api("SKU-0001")
            code_503 = getattr(res_503, "status_code", 200)

            passed = (
                code_200 == 200
                and code_404 == 404
                and code_503 == 503
            )
            actual = (
                f"HTTP status: 200={code_200}, "
                f"404={code_404}, 503={code_503}"
            )

    except Exception as exc:
        passed = False
        actual = f"{type(exc).__name__}: {exc}"

    finally:
        if original_root is None:
            os.environ.pop("BAANDEE_ROOT", None)
        else:
            os.environ["BAANDEE_ROOT"] = original_root

    record_result(
        results,
        "TC-02",
        "Supplier API Boundary Handling",
        "Valid SKU, missing SKU, unavailable supplier data",
        "API ให้ผลลัพธ์ 200, 404 และ 503 ตามเงื่อนไข",
        actual,
        passed,
    )

    # -------------------------------------------------------------------------
    # TC-03: Stock Risk Calculation
    # -------------------------------------------------------------------------
    try:
        df_risk = calculate_stock_risk(BASE_DIR, save=False)

        required_column = "risk_status"
        if required_column not in df_risk.columns:
            raise ValueError(
                f"ไม่พบคอลัมน์ {required_column}"
            )

        statuses = set(df_risk[required_column].dropna().astype(str))

        has_critical = "CRITICAL_RISK" in statuses
        has_human_review = "HUMAN_REVIEW_NEEDED" in statuses

        passed = has_critical and has_human_review
        actual = (
            f"ประมวลผล {len(df_risk)} SKUs; "
            f"CRITICAL_RISK={has_critical}; "
            f"HUMAN_REVIEW_NEEDED={has_human_review}"
        )

    except Exception as exc:
        passed = False
        actual = f"{type(exc).__name__}: {exc}"

    record_result(
        results,
        "TC-03",
        "Stock Risk Calculation Engine",
        "Cleaned and joined datasets",
        "คำนวณความเสี่ยงและพบ CRITICAL_RISK "
        "รวมถึง HUMAN_REVIEW_NEEDED",
        actual,
        passed,
    )

    # -------------------------------------------------------------------------
    # TC-04: Create Reorder Request and Update Status
    # ใช้พื้นที่ชั่วคราว เพื่อไม่ปนกับคำขอจริงของโปรเจกต์
    # -------------------------------------------------------------------------
    req_id = None
    test_storage_dir = None

    try:
        temp_storage = tempfile.TemporaryDirectory()
        test_storage_dir = Path(temp_storage.name)

        req = create_reorder_request(
            project_path=test_storage_dir,
            product_id="SKU-0001",
            product_name="Test Product",
            requested_qty=50,
            risk_status="CRITICAL_RISK",
        )

        req_id = req["request_id"]

        created_requests = get_reorder_requests(
            project_path=test_storage_dir,
            include_deleted=False,
        )

        created_row = created_requests[
            created_requests["request_id"] == req_id
        ]

        created_as_draft = (
            not created_row.empty
            and str(created_row.iloc[0]["status"]) == "Draft"
        )

        updated = update_request_status(
            project_path=test_storage_dir,
            request_id=req_id,
            new_status="Approved",
        )

        updated_requests = get_reorder_requests(
            project_path=test_storage_dir,
            include_deleted=False,
        )

        updated_row = updated_requests[
            updated_requests["request_id"] == req_id
        ]

        approved = (
            not updated_row.empty
            and str(updated_row.iloc[0]["status"]) == "Approved"
        )

        passed = created_as_draft and updated and approved
        actual = (
            f"request_id={req_id}; "
            f"created_as_Draft={created_as_draft}; "
            f"update_success={updated}; approved={approved}"
        )

    except Exception as exc:
        passed = False
        actual = f"{type(exc).__name__}: {exc}"

    record_result(
        results,
        "TC-04",
        "Reorder Request Create and Update",
        "SKU-0001, quantity=50",
        "สร้างคำขอเป็น Draft แล้วอัปเดตเป็น Approved ได้",
        actual,
        passed,
    )

    # -------------------------------------------------------------------------
    # TC-05: Soft Delete and Audit Trail
    # -------------------------------------------------------------------------
    try:
        if req_id is None or test_storage_dir is None:
            raise RuntimeError(
                "ไม่สามารถทดสอบ Soft Delete ได้ เพราะ TC-04 สร้างคำขอไม่สำเร็จ"
            )

        deleted = soft_delete_request(
            project_path=test_storage_dir,
            request_id=req_id,
        )

        active_requests = get_reorder_requests(
            project_path=test_storage_dir,
            include_deleted=False,
        )

        all_requests = get_reorder_requests(
            project_path=test_storage_dir,
            include_deleted=True,
        )

        hidden_from_active = (
            req_id not in active_requests["request_id"].values
        )

        retained_in_history = (
            req_id in all_requests["request_id"].values
        )

        deleted_row = all_requests[
            all_requests["request_id"] == req_id
        ]

        marked_deleted = (
            not deleted_row.empty
            and str(deleted_row.iloc[0]["is_deleted"]).lower() == "true"
        )

        passed = (
            deleted
            and hidden_from_active
            and retained_in_history
            and marked_deleted
        )

        actual = (
            f"delete_success={deleted}; "
            f"hidden_from_active={hidden_from_active}; "
            f"retained_in_history={retained_in_history}; "
            f"is_deleted={marked_deleted}"
        )

    except Exception as exc:
        passed = False
        actual = f"{type(exc).__name__}: {exc}"

    finally:
        if test_storage_dir is not None:
            temp_storage.cleanup()

    record_result(
        results,
        "TC-05",
        "Soft Delete and Audit Trail",
        f"Request ID: {req_id}",
        "ซ่อนคำขอจากรายการปกติ แต่เก็บประวัติและตั้ง is_deleted=True",
        actual,
        passed,
    )

    # -------------------------------------------------------------------------
    # 6. Save Test Results
    # -------------------------------------------------------------------------
    df_results = pd.DataFrame(results)

    output_file = app_state_dir / "test_results.csv"
    df_results.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig",
    )

    print("=" * 70)
    print("AUTOMATED SYSTEM TEST RESULTS")
    print("=" * 70)

    for _, row in df_results.iterrows():
        print(
            f"[{row['status']}] {row['test_id']}: "
            f"{row['test_name']}"
        )
        print(f"  Actual: {row['actual']}")

    passed_count = int((df_results["status"] == "PASS").sum())
    total_count = len(df_results)

    print("-" * 70)
    print(f"Summary: {passed_count}/{total_count} tests passed")
    print(f"Results saved to: {output_file}")

    return df_results


if __name__ == "__main__":
    df_test_results = run_system_tests()
    print(df_test_results.to_string(index=False))
