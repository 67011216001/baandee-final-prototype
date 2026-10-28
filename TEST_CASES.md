# 🧪 Test Cases Specification & Execution Report (รายงานผลการทดสอบระบบ)
**โครงงาน:** ระบบช่วยตรวจสอบสินค้าที่มีความเสี่ยงขาดสต็อกและจัดการใบคำขอสั่งซื้อ (BaanDee Stockout Risk & Reorder System)  
**เป้าหมาย:** ยืนยันความถูกต้องของคุณภาพข้อมูล, เอนจินคำนวณความเสี่ยง (Risk Assessment Engine), สถาปัตยกรรมกักกันข้อมูล (Quarantine/Human-in-the-Loop) และระบบจัดการตั๋วสั่งซื้อ (Storage CRUD & Soft Delete)

---

## 🎯 1. ภาพรวมการทดสอบ (Testing Overview)

การทดสอบระบบถูกออกแบบให้ครอบคลุมทั้ง **Success Flow**, **Failure Handling Flow**, **Data Quality Quarantine**, **Persistence** และ **Soft Delete Logic** โดยอิงตามเกณฑ์การประเมินของโครงงาน Data Product

* **Framework ที่ใช้:** Python `pytest` / Custom Validation Script (`tests/test_pipeline.py`)
* **จำนวน Test Cases ทั้งหมด:** 5 กรณีทดสอบหลัก
* **สถานะการทดสอบ:** **PASS 100% (5/5 Cases)**

---

## 🧪 2. รายละเอียดกรณีทดสอบทั้ง 5 (5 Main Test Cases)

### 📌 **TC-01: การคำนวณความเสี่ยง SKU ปกติที่มีสต็อกเพียงพอ (Success Case)**
* **วัตถุประสงค์:** ทดสอบว่าระบบสามารถคำนวณ `Days of Cover` และให้ป้ายสถานะ `NORMAL` ถูกต้องเมื่อสต็อกครอบคลุมระยะเวลาจัดส่งของซัพพลายเออร์
* **ข้อมูลนำเข้า (Input):** 
  * SKU: `SKU-0001`
  * Available Qty: `5` ชิ้น
  * Daily Sales Rate: `0.1` ชิ้น/วัน
  * Lead Time: `14` วัน
* **การคำนวณ:** `Days of Cover` = 5 / 0.1 = **50 วัน** (มากกว่า Lead Time 14 วัน)
* **ผลลัพธ์ที่คาดหวัง (Expected Result):** `risk_status` = `'NORMAL'`
* **ผลลัพธ์จริง (Actual Result):** `risk_status` = `'NORMAL'`
* **สถานะ:** ✅ **PASS**

---

### 📌 **TC-02: การตรวจจับสินค้าสต็อกหมดหรือเสี่ยงวิกฤต (Critical Risk Case)**
* **วัตถุประสงค์:** ทดสอบว่าระบบแจ้งเตือน `CRITICAL_RISK` ทันทีเมื่อสต็อกคงเหลือเท่ากับ 0 หรือวันคงเหลือขายต่ำกว่าระยะเวลาจัดส่ง
* **ข้อมูลนำเข้า (Input):** 
  * SKU: `SKU-0002`
  * Available Qty: `0` ชิ้น หรือ `Days of Cover` < `Lead Time`
* **ผลลัพธ์ที่คาดหวัง (Expected Result):** `risk_status` = `'CRITICAL_RISK'`
* **ผลลัพธ์จริง (Actual Result):** `risk_status` = `'CRITICAL_RISK'`
* **สถานะ:** ✅ **PASS**

---

### 📌 **TC-03: การหยุดประเมินเมื่อข้อมูล Lead Time ขาดหาย (Quarantine / Human-in-the-Loop Case)**
* **วัตถุประสงค์:** ทดสอบว่าระบบไม่สุ่มเดาค่าตัวเลขเมื่อพบข้อมูลบกพร่อง (`NaN` หรือค่าติดลบ `<= 0`) และหยุดการประเมินอัตโนมัติเพื่อส่งต่อให้มนุษย์ตรวจ
* **ข้อมูลนำเข้า (Input):** 
  * SKU: `SKU-0015`
  * Lead Time: `NaN` (ฝังไว้ใน `supplier_lead_time.csv`)
* **ผลลัพธ์ที่คาดหวัง (Expected Result):** `risk_status` = `'HUMAN_REVIEW_NEEDED'` และคัดแยกไปที่ `review_needed.csv`
* **ผลลัพธ์จริง (Actual Result):** `risk_status` = `'HUMAN_REVIEW_NEEDED'`
* **สถานะ:** ✅ **PASS**

---

### 📌 **TC-04: การสร้างตั๋วสั่งซื้อและการบันทึกสถานะถาวร (Create Draft PO & Persistence Case)**
* **วัตถุประสงค์:** ทดสอบกระบวนการสร้างตั๋วคำขอสั่งซื้อ (Reorder Request) ผ่าน UI Dashboard และตรวจสอบว่าข้อมูลถูกบันทึกลงไฟล์ CSV ถาวร ไม่สูญหายเมื่อปิดโปรแกรม
* **ข้อมูลนำเข้า (Input):** 
  * SKU: `SKU-0001`
  * Reorder Qty: `10` ชิ้น
  * Action: กดปุ่ม "สร้างใบคำขอสั่งซื้อ"
* **ผลลัพธ์ที่คาดหวัง (Expected Result):** สร้างตั๋วรหัส `REQ-XXXX` สถานะ `'Draft'` และบันทึกลงไฟล์ `data/app_state/reorder_requests.csv`
* **ผลลัพธ์จริง (Actual Result):** สร้างตั๋วสำเร็จ ข้อมูลคงค้างในไฟล์ถาวร 100%
* **สถานะ:** ✅ **PASS**

---

### 📌 **TC-05: การลบตั๋วสั่งซื้อแบบ Soft Delete (Soft Delete Logic Case)**
* **วัตถุประสงค์:** ทดสอบว่าการลบใบสั่งซื้อผ่านหน้าจอ UI จะปรับสถานะซ่อนรายการ แต่ยังคงรักษาแถวข้อมูลเดิมไว้ในฐานข้อมูลเพื่อความปลอดภัย (Audit Trail)
* **ข้อมูลนำเข้า (Input):** 
  * Request ID: `REQ-0001`
  * Action: กดปุ่ม "ลบใบสั่งซื้อ"
* **ผลลัพธ์ที่คาดหวัง (Expected Result):** คอลัมน์ `is_deleted` ใน `reorder_requests.csv` เปลี่ยนเป็น `True` รายการซ่อนจาก UI แต่แถวข้อมูลไม่ถูกลบออกจาก CSV
* **ผลลัพธ์จริง (Actual Result):** `is_deleted` = `True` ข้อมูลยังคงอยู่ใน CSV ครบถ้วน
* **สถานะ:** ✅ **PASS**

---

## 📊 3. ตารางสรุปผลการทดสอบ (Test Execution Summary)

| Test ID | รายละเอียดกรณีทดสอบ | Input Data | Expected Result | Actual Result | Status |
| :---: | :--- | :--- | :--- | :--- | :---: |
| **TC-01** | คำนวณความเสี่ยง SKU ปกติสต็อกพอ | SKU-0001 (Stock=5, Sales/day=0.1, LeadTime=14) | `risk_status` = 'NORMAL' | `risk_status` = 'NORMAL' | **PASS** |
| **TC-02** | ตรวจจับสินค้าสต็อกหมด/เสี่ยงวิกฤต | SKU-0002 (Stock=0 หรือ DaysOfCover < LeadTime) | `risk_status` = 'CRITICAL_RISK' | `risk_status` = 'CRITICAL_RISK' | **PASS** |
| **TC-03** | หยุดประเมินเมื่อข้อมูล Lead Time ขาดหาย | SKU-0015 (Lead Time = `NaN`) | `risk_status` = 'HUMAN_REVIEW_NEEDED' | `risk_status` = 'HUMAN_REVIEW_NEEDED' | **PASS** |
| **TC-04** | สร้างตั๋วสั่งซื้อและบันทึกสถานะถาวร | Request SKU-0001, Reorder Qty = 10 | บันทึกตั๋วสถานะ 'Draft' ลงไฟล์ CSV ถาวร | สร้างตั๋วสำเร็จ ข้อมูลไม่สูญหาย | **PASS** |
| **TC-05** | ลบตั๋วสั่งซื้อแบบ Soft Delete | Delete REQ-0001 | `is_deleted` = `True` ซ่อนจาก UI ข้อมูลไม่สูญหาย | `is_deleted` = `True` ข้อมูลคงเดิมใน CSV | **PASS** |

---

## 💻 4. ตัวอย่างคำสั่งรันชุดทดสอบอัตโนมัติ (Automated Test Execution)

สามารถรันชุดทดสอบทั้งหมดผ่าน `pytest` ได้ด้วยคำสั่ง:

```bash
# รันชุดทดสอบทั้งหมดในโฟลเดอร์ tests/
pytest tests/test_pipeline.py -v
```
