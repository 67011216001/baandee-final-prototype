###=============================================================================
### AUTOMATED SYSTEM TEST SUITE (5 TEST CASES)
### ไฟล์: tests/test_system.py
### วัตถุประสงค์: สคริปต์ทดสอบระบบอัตโนมัติแบบครอบคลุมทั้ง Pipeline (End-to-End)
### เพื่อพิสูจน์การทำงานของ Backend Modules ในโฟลเดอร์ src/
###=============================================================================

from pathlib import Path
import sys
import pandas as pd
from google.colab import drive

# ------------------------------------------------------------------------------
# 1. เชื่อมต่อ Google Drive และตั้งค่า Path โปรเจกต์
# ------------------------------------------------------------------------------
drive.mount('/content/drive')

BASE_DIR = Path(
    '/content/drive/MyDrive/ปี 3 1/1208304/Project'
)

if not BASE_DIR.exists():
    raise FileNotFoundError(
        f'ไม่พบโฟลเดอร์โปรเจกต์: {BASE_DIR}\n'
        'กรุณาตรวจสอบชื่อโฟลเดอร์และตำแหน่งใน Google Drive'
    )

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Import ฟังก์ชันหลักจากระบบหลังบ้าน
from api.main import get_supplier_lead_time_api
from src.risk import calculate_stock_risk
from src.storage import (
    create_reorder_request,
    get_reorder_requests,
    soft_delete_reorder_request,
    update_reorder_status,
)


def run_system_tests():
    """สคริปต์ทดสอบระบบอัตโนมัติ 5 Test Cases (TC-01 ถึง TC-05)"""
    test_results = []
    req_id = None

    app_state_dir = BASE_DIR / 'data' / 'app_state'
    app_state_dir.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------------------------------
    # TC-01: Data Cleaning & Quarantine Check
    # --------------------------------------------------------------------------
    try:
        review_file = (
            BASE_DIR / 'data' / 'cleaned' / 'review_needed.csv'
        )

        if review_file.exists():
            df_review = pd.read_csv(review_file)
            invalid_count = len(df_review)
            status = 'PASS' if invalid_count >= 2 else 'FAIL'
            msg = (
                'พบข้อมูลบกพร่องที่ถูกกักกันใน review_needed.csv '
                f'จำนวน {invalid_count} รายการ'
            )
        else:
            status = 'FAIL'
            msg = 'ไม่พบไฟล์ review_needed.csv'

    except Exception as e:
        status = 'FAIL'
        msg = f'Error: {str(e)}'

    test_results.append({
        'test_id': 'TC-01',
        'test_name': 'Data Ingestion & Quarantine Isolation',
        'input': 'Raw products.csv (82 SKUs)',
        'expected': (
            'กักกัน SKU ผิดฟอร์แมตลง review_needed.csv '
            'อย่างน้อย 2 รายการ'
        ),
        'actual': msg,
        'status': status,
    })

    # --------------------------------------------------------------------------
    # TC-02: API Boundary Response Handling (200, 404, 503)
    # --------------------------------------------------------------------------
    try:
        supp_file = (
            BASE_DIR / 'data' / 'generated' /
            'supplier_lead_time.csv'
        )

        res_200 = get_supplier_lead_time_api(
            product_id=1,
            gen_data_path=supp_file,
            simulate_503=False
        )

        res_404 = get_supplier_lead_time_api(
            product_id=9999,
            gen_data_path=supp_file,
            simulate_503=False
        )

        res_503 = get_supplier_lead_time_api(
            product_id=1,
            gen_data_path=supp_file,
            simulate_503=True
        )

        code_200 = res_200.get('status_code') == 200
        code_404 = res_404.get('status_code') == 404
        code_503 = res_503.get('status_code') == 503

        if code_200 and code_404 and code_503:
            status = 'PASS'
            msg = (
                'API ตอบรับสถานะ 200, 404 และ 503 '
                'ถูกต้องตามเงื่อนไข'
            )
        else:
            status = 'FAIL'
            msg = (
                f'API Response Mismatch '
                f'(200:{code_200}, 404:{code_404}, 503:{code_503})'
            )

    except Exception as e:
        status = 'FAIL'
        msg = f'Error: {str(e)}'

    test_results.append({
        'test_id': 'TC-02',
        'test_name': 'Supplier API Boundary Handling',
        'input': 'Product IDs (1, 9999) + Simulate 503 Flag',
        'expected': (
            'ตอบรับครบ 200 OK, 404 Not Found, '
            '503 Service Unavailable'
        ),
        'actual': msg,
        'status': status,
    })

    # --------------------------------------------------------------------------
    # TC-03: Risk Assessment Engine Calculation
    # --------------------------------------------------------------------------
    try:
        df_risk = calculate_stock_risk(BASE_DIR)

        has_critical = (
            df_risk['risk_status'] == 'CRITICAL_RISK'
        ).any()

        has_human = (
            df_risk['risk_status'] == 'HUMAN_REVIEW_NEEDED'
        ).any()

        if has_critical and has_human:
            status = 'PASS'
            msg = (
                'คำนวณและจำแนกความเสี่ยงสำเร็จรวม '
                f'{len(df_risk)} SKUs'
            )
        else:
            status = 'FAIL'
            msg = (
                'การจัดกลุ่มความเสี่ยงไม่ครอบคลุม '
                'สถานะวิกฤตหรือกักกัน'
            )

    except Exception as e:
        status = 'FAIL'
        msg = f'Error: {str(e)}'

    test_results.append({
        'test_id': 'TC-03',
        'test_name': 'Stock Risk Calculation Engine',
        'input': 'Joined Cleaned Data + Lead Times',
        'expected': (
            'คำนวณ Days of Cover และจำแนกสถานะความเสี่ยงถูกต้อง'
        ),
        'actual': msg,
        'status': status,
    })

    # --------------------------------------------------------------------------
    # TC-04: Storage Engine - Ticket Creation & Status Update
    # --------------------------------------------------------------------------
    try:
        req = create_reorder_request(
            product_id='SKU-0001',
            product_name='เก้าอี้มินิมอล',
            requested_qty=50,
            risk_status='CRITICAL_RISK',
            project_path=BASE_DIR,
        )

        req_id = req.get('request_id') if req else None

        if req_id is None:
            raise ValueError(
                'ไม่สามารถสร้างคำขอสั่งซื้อหรือไม่พบ request_id'
            )

        updated = update_reorder_status(
            request_id=req_id,
            new_status='Approved',
            project_path=BASE_DIR
        )

        if req and updated:
            status = 'PASS'
            msg = (
                f'สร้างตั๋ว {req_id} (Draft) '
                'และอัปเดตสถานะเป็น Approved สำเร็จ'
            )
        else:
            status = 'FAIL'
            msg = 'ไม่สามารถสร้างหรืออัปเดตสถานะตั๋วได้'

    except Exception as e:
        status = 'FAIL'
        msg = f'Error: {str(e)}'

    test_results.append({
        'test_id': 'TC-04',
        'test_name': 'Storage Engine CRUD (Create & Update)',
        'input': 'SKU-0001, Qty: 50, Status: Approved',
        'expected': 'ออกรหัส REQ-XXXX และปรับสถานะเป็น Approved สำเร็จ',
        'actual': msg,
        'status': status,
    })

    # --------------------------------------------------------------------------
    # TC-05: Storage Engine - Soft Delete Audit Trail
    # --------------------------------------------------------------------------
    try:
        if req_id is None:
            raise ValueError(
                'ไม่สามารถทดสอบ Soft Delete ได้ '
                'เพราะ TC-04 ไม่มี request_id'
            )

        deleted = soft_delete_reorder_request(
            request_id=req_id,
            project_path=BASE_DIR
        )

        df_active = get_reorder_requests(
            include_deleted=False,
            project_path=BASE_DIR
        )

        df_all = get_reorder_requests(
            include_deleted=True,
            project_path=BASE_DIR
        )

        is_hidden_from_active = (
            req_id not in df_active['request_id'].values
        )

        exists_in_all = (
            req_id in df_all['request_id'].values
        )

        if deleted and is_hidden_from_active and exists_in_all:
            status = 'PASS'
            msg = (
                f'Soft Delete ตั๋ว {req_id} สำเร็จ '
                '(ซ่อนจาก UI แต่เก็บประวัติไว้ใน CSV)'
            )
        else:
            status = 'FAIL'
            msg = 'Soft Delete ไม่เป็นไปตามเกณฑ์ Audit Trail'

    except Exception as e:
        status = 'FAIL'
        msg = f'Error: {str(e)}'

    test_results.append({
        'test_id': 'TC-05',
        'test_name': 'Storage Engine Soft Delete',
        'input': f'Soft Delete Request ID: {req_id}',
        'expected': (
            'ซ่อนรายการออกจาก UI โดยไม่ลบแถวออกจากไฟล์ CSV'
        ),
        'actual': msg,
        'status': status,
    })

    # --------------------------------------------------------------------------
    # สรุปและบันทึกผลลัพธ์ลงไฟล์ test_results.csv
    # --------------------------------------------------------------------------
    df_res = pd.DataFrame(test_results)

    out_path = (
        BASE_DIR / 'data' / 'app_state' / 'test_results.csv'
    )

    df_res.to_csv(out_path, index=False, encoding='utf-8-sig')

    print('=' * 65)
    print('🧪 ผลการทดสอบระบบสคริปต์อัตโนมัติ (REPEATABLE TEST RESULTS)')
    print('=' * 65)

    for _, row in df_res.iterrows():
        print(f"[{row['status']}] {row['test_id']}: {row['test_name']}")
        print(f" รายละเอียด: {row['actual']}\n")

    print('=' * 65)
    print(f'✅ บันทึกหลักฐานผลการทดสอบลงไฟล์: {out_path}')

    return df_res


# เรียกใช้งานโดยตรงใน Google Colab
df_test_results = run_system_tests()

display(df_test_results)
