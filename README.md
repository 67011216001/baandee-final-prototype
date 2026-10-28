# 📦 BaanDee Stockout Risk & Reorder System
**ระบบช่วยตรวจสอบสินค้าที่มีความเสี่ยงขาดสต็อกและจัดการใบคำขอสั่งซื้อ (Data Product Prototype)**  
*ต้นแบบสำหรับ Final Project · บริษัทสมมติ BaanDee Living · ข้อมูลทั้งหมดเป็นข้อมูลสังเคราะห์*

---

## 🎯 1. ปัญหา ผู้ใช้ และคุณค่าที่คาดหวัง (Problem, Users & Expected Value)

### 1.1 ผู้ใช้หลักและผู้ใช้รอง
* **ผู้ใช้หลัก:** เจ้าหน้าที่จัดซื้อ / วางแผนสต็อกของ BaanDee Living
* **ผู้ใช้รอง:** หัวหน้าฝ่ายจัดซื้อ (ผู้อนุมัติใบคำขอสั่งซื้อ)

### 1.2 งานที่ผู้ใช้กำลังพยายามทำ (Job-to-be-Done)
ตัดสินใจในแต่ละวันว่า **ควรขอสั่งซื้อสินค้ารายการใด จำนวนเท่าไร และเร่งด่วนแค่ไหน** ก่อนที่สินค้าจะหมดคลัง โดยต้องเปรียบเทียบปัจจัย 3 ประการพร้อมกัน:
1. จำนวนสต็อกคงเหลือปัจจุบัน ณ วัน Snapshot
2. ความเร็วในการขาย (ยอดขายเฉลี่ยต่อวันย้อนหลัง 30 วัน)
3. ระยะเวลาจัดส่งของซัพพลายเออร์ (Supplier Lead Time)

### 1.3 ปัญหาในกระบวนการปัจจุบัน
1. **ข้อมูลกระจายตัวอยู่คนละแห่ง:** ข้อมูลสินค้า สต็อก ยอดขาย และ Lead Time เก็บแยกกัน ทำให้เสียเวลาในการรวบรวม
2. **ไม่มีเกณฑ์กลางในการประเมินความเสี่ยง:** แต่ละคนใช้ดุลยพินิจไม่เหมือนกัน
3. **ดูสต็อกอย่างเดียวบอกความเร่งด่วนไม่ได้:** สต็อกเหลือ 10 ชิ้นอาจขายได้อีก 2 วันหรือ 2 เดือน ขึ้นอยู่กับอัตราการขาย
4. **ไม่มีการเตือนข้อมูลไม่สมบูรณ์:** ข้อมูลที่เก่าหรือขาดหายมักถูกละเลยหรือสุ่มเดา

### 1.4 ต้นแบบนี้ช่วยได้อย่างไร
* **รวมข้อมูลในหน้าจอเดียว:** ดึงข้อมูลด้วย `product_id` จากแหล่งข้อมูล 2 แหล่งมาแสดงผลใน Dashboard เดียว
* **ประเมินความเสี่ยงด้วยสูตรมาตรฐาน (Deterministic Rule):** คำนวณวันคงเหลือขาย (`Days of Cover = Available Qty / Daily Sales Rate`) เทียบกับ `Lead Time`
* **แยกแยะประเภทข้อมูลอย่างชัดเจน:** ติดป้าย **"ข้อเท็จจริงที่ยืนยันแล้ว"** (สต็อก ณ 31 ก.ค. 2026) ออกจาก **"ค่าประมาณ"** (อัตราขายเฉลี่ย 30 วัน)
* **หยุดส่งต่อคนเมื่อข้อมูลไม่พร้อม (Human-in-the-loop):** หากพบข้อมูลขาดหาย หรือ Lead Time ติดลบ ระบบจะไม่สุ่มเดาตัวเลขแทน แต่จะติดป้าย `HUMAN_REVIEW_NEEDED` และแยกเข้าคัดกรองทันที

### 1.5 สมมติฐานที่ยังต้องทดลองกับผู้ใช้จริง (Unproven Hypotheses)
* **H1:** เจ้าหน้าที่จัดซื้อใช้เวลาลดลงในการตรวจรายการเสี่ยงเมื่อมี Dashboard รวมข้อมูล
* **H2:** กฎการจัดระดับความเสี่ยงตรงกับการตัดสินใจของผู้เชี่ยวชาญจริง
* **H3:** ป้าย "ต้องให้คนตรวจ" ช่วยป้องกันความผิดพลาดจากการประเมินมั่วของระบบ

---

## 📊 2. ข้อมูล ความสัมพันธ์ และคุณภาพข้อมูล (Data Map & Quality)

### 2.1 แหล่งข้อมูล (Data Sources)
โครงงานนี้นำข้อมูลมาเชื่อมโยงกันจาก **2 กลุ่มแหล่งข้อมูล** (รวม 5 ตารางหลัก):
1. **ข้อมูลดิบต้นฉบับ BaanDee (`data/raw/`):**
   * `products.csv` : ข้อมูลรายละเอียดสินค้า (`product_id`, `product_name`, `category`, `unit_price_thb`)
   * `inventory_snapshot.csv` : จำนวนสต็อกคงคลัง ณ วัน snapshot 31 ก.ค. 2026 (`product_id`, `location_id`, `available_qty`, `as_of`)
   * `orders.csv` & `order_lines.csv` : ประวัติการสั่งซื้อสำหรับคำนวณยอดขายย้อนหลัง
2. **ข้อมูลแหล่งใหม่ที่สังเคราะห์ขึ้น (`data/generated/`):**
   * `supplier_lead_time.csv` : ระยะเวลาจัดส่งของซัพพลายเออร์ (`product_id`, `supplier_name`, `lead_time_days`, `source`, `generated_at`) พร้อมฝังข้อมูลบกพร่องเพื่อทดสอบ Failure Behavior
3. **ข้อมูลที่ทำความสะอาดแล้ว (`data/cleaned/`):**
   * `joined_products_supplier.csv` : ผลการ Left Join ข้อมูลสินค้าและซัพพลายเออร์
   * `stock_risk_summary.csv` : ผลการประเมินความเสี่ยงทั้ง 82 SKU
   * `review_needed.csv` : รายการข้อมูลกักกันที่ต้องส่งต่อให้มนุษย์ตรวจสอบ
4. **ข้อมูลสถานะแอปพลิเคชัน (`data/app_state/`):**
   * `reorder_requests.csv` : บันทึกตั๋วคำขอสั่งซื้อที่สร้างผ่านแอปพลิเคชัน (รองรับ Persistence และ Soft Delete)

### 2.2 สรุปหลักฐานปัญหาคุณภาพข้อมูลและการจัดการ (Data Quality Findings)

| ลำดับ | ปัญหาคุณภาพข้อมูลที่พบ | หลักฐานในข้อมูลดิบ (Before) | วิธีตรวจพบ (Detection Rule) | วิธีจัดการ / ผลลัพธ์ (After / Correction Rule) |
| :---: | :--- | :--- | :--- | :--- |
| **1** | **รหัส SKU ผิดฟอร์แมตมาตรฐาน** | `SKU-BD-220`, `SKU-KT-104` ใน `products.csv` | Regex `^SKU-\d{4}$` ตรวจจับรหัสที่ไม่ตรงรูปแบบ `SKU-XXXX` | **ก่อน:** รหัสผิดปกติปนในคลัง<br>**หลัง:** กักกันรายการกำกวมไปที่ `review_needed.csv` ไม่สุ่มเดาค่า |
| **2** | **ชื่อหมวดสินค้าสะกดไม่เป็นมาตรฐาน** | `kitchen`/`Kitchen`, `bedding`/`Bedding`, `Bed room` ใน `products.csv` | `value_counts()` ตรวจหาอักษรพิมพ์เล็ก-ใหญ่และช่องว่าง | **ก่อน:** มี 8 หมวดสะกดปนกัน<br>**หลัง:** ปรับ `trim()` และแปลงเป็น Title Case เหลือ 4 หมวดมาตรฐาน |
| **3** | **รูปแบบวันที่ปนกันและกำกวม** | `28/07/2026`, `07/08/2026` ใน `orders.order_date` | Regex `^\d{4}-\d{2}-\d{2}$` ตรวจจับวันที่ผิดฟอร์แมต | **ก่อน:** รูปแบบวันที่ปนกันระหว่าง `/` กับ `-`<br>**หลัง:** แปลงเป็น `YYYY-MM-DD` มาตรฐาน |

---

## 🏗 3. สถาปัตยกรรมระบบ และจุดเชื่อมต่อ API (Architecture & API Boundary)

### 3.1 เทคโนโลยีที่เลือกใช้ (Tech Stack)
* **Backend & Analytics Engine:** Python 3.11+, `pandas`, `numpy`
* **API Framework:** `FastAPI` / `Uvicorn`
* **Frontend Dashboard UI:** `Gradio`
* **Testing:** `pytest` / Custom Validation Script

### 3.2 จุดเชื่อมต่อข้ามระบบ (API System Boundary)
ระบบมีจุดเชื่อมต่อข้ามระบบผ่าน API Endpoint `/get_supplier_lead_time_api` เพื่อดึงข้อมูล Lead Time ของซัพพลายเออร์ โดยรองรับครบ **3 สถานการณ์**:
1. **200 Success (ได้รับข้อมูลสำเร็จ):** คืนค่า `product_id`, `supplier_name`, และ `lead_time_days`
2. **404 Not Found / Review Needed (ไม่พบข้อมูลหรือข้อมูลไม่สมบูรณ์):** คืนค่าเมื่อไม่พบ SKU, ค่า Lead Time เป็น `NaN`, หรือติดลบ `<= 0` พร้อมส่งต่อให้มนุษย์ตรวจ
3. **503 Service Unavailable (บริการไม่พร้อมใช้งาน):** คืนค่าเมื่อไฟล์ฐานข้อมูลขาดหาย หรือระบบ API ขัดข้อง

---

## 📂 4. โครงสร้าง Repository (Repository Structure)

```text
baandee-stockout-risk/
├── data/
│   ├── raw/                   # ข้อมูลดิบต้นฉบับ 7 ไฟล์จากอาจารย์ (ไม่แก้ไขทับ)
│   ├── generated/             # supplier_lead_time.csv (ข้อมูลสังเคราะห์แหล่งที่ 2)
│   ├── cleaned/               # cleaned_*.csv, joined_..., stock_risk_summary.csv, review_needed.csv
│   └── app_state/             # reorder_requests.csv (สถานะตั๋วที่บันทึกจาก UI)
├── src/
│   ├── risk.py                # เอนจินคำนวณ Days of Cover และจัดป้ายระดับความเสี่ยง
│   ├── storage.py             # เอนจินจัดการ CRUD ตั๋วสั่งซื้อ (Draft, Approve, Soft Delete)
│   └── app.py                 # หน้าจอ Gradio Dashboard & Reorder Form
├── api/
│   └── main.py                # FastAPI Endpoint สำหรับเชื่อมต่อข้อมูล Lead Time
├── tests/
│   └── test_pipeline.py       # ชุดทดสอบอัตโนมัติ 5 Test Cases
├── docs/
│   ├── problem_statement.md   # รายละเอียดปัญหาและขอบเขตโครงการ
│   └── data_quality_findings.csv # ตารางสรุปหลักฐานคุณภาพข้อมูล
├── .env.example               # ตัวอย่าง Environment Variables
├── .gitignore                 # กำหนดไฟล์ที่ไม่ต้อง push ขึ้น Git
├── requirements.txt           # รายชื่อ Python Packages
├── AI_USE.md                  # รายงานการใช้งาน AI อย่างโปร่งใส
└── README.md                  # เอกสารคู่มือโปรเจกต์ฉบับสมบูรณ์
```

---

## 🚀 5. วิธีติดตั้งและเริ่มระบบ (Installation & Setup)

### 5.1 การเตรียม Environment
```bash
# 1. Clone Repository
git clone https://github.com/67011216001/baandee-stockout-risk.git
cd baandee-stockout-risk

# 2. สร้าง Virtual Environment และลง Library
python -m venv .venv
source .venv/bin/activate  # บน Windows ใช้: .venv\Scripts\activate
pip install -r requirements.txt

# 3. เตรียมไฟล์ Environment
cp .env.example .env
```

### 5.2 คำสั่งรันระบบ
```bash
# รันหน้าจอ Gradio Dashboard
python src/app.py

# รัน API Server (FastAPI)
uvicorn api.main:app --reload

# รันชุดทดสอบ Test Cases
pytest tests/
```

---

## 🎬 6. กรณีสาธิตหลัก (Main Demo Scenarios)

1. **กรณีทำงานสำเร็จ (Success Flow):**
   * เลือก SKU-0001 ➔ ระบบแสดงสต็อกคงเหลือ, ยอดขาย 30 วัน, Lead Time, Days of Cover ➔ ระบุป้าย `NORMAL` ➔ สร้างตั๋ว Draft สั่งซื้อ ➔ กดอนุมัติ ➔ ปิดและเปิดโปรแกรมใหม่ ข้อมูลตั๋วยังคงอยู่ครบถ้วน (Persistence)
2. **กรณีหยุดส่งต่อให้มนุษย์ (Failure / Human Review Flow):**
   * เลือก SKU-0015 (ข้อมูล Lead Time เป็น `NaN`) ➔ ระบบตรวจเจอความผิดปกติ ➔ บล็อกการประเมินความเสี่ยงและขึ้นป้ายเตือน `HUMAN_REVIEW_NEEDED` ทันที
3. **กรณีทดสอบการลบตั๋ว (Soft Delete Flow):**
   * เลือกรายการตั๋วสั่งซื้อ ➔ กดปุ่ม Delete ➔ ระบบปรับสถานะ `is_deleted = True` โดยไม่ลบแถวข้อมูลออกจากไฟล์จริง

---

## 🧪 7. ตารางสรุปการทดสอบ (5 Test Cases)

| Test ID | รายละเอียดกรณีทดสอบ (Scenario) | Input | Expected Result | Actual Result | Pass/Fail |
| :---: | :--- | :--- | :--- | :--- | :---: |
| **TC-01** | คำนวณความเสี่ยง SKU ปกติที่มีสต็อกพอ | SKU-0001 (Stock=5, Sales/day=0.1, LeadTime=14) | `risk_status` = 'NORMAL' | `risk_status` = 'NORMAL' | **PASS** |
| **TC-02** | ตรวจจับสินค้าสต็อกหมดหรือเสี่ยงวิกฤต | SKU-0002 (Stock=0 หรือ DaysOfCover < LeadTime) | `risk_status` = 'CRITICAL_RISK' | `risk_status` = 'CRITICAL_RISK' | **PASS** |
| **TC-03** | หยุดประเมินเมื่อข้อมูล Lead Time ขาดหาย | SKU-0015 (Lead Time = `NaN`) | `risk_status` = 'HUMAN_REVIEW_NEEDED' | `risk_status` = 'HUMAN_REVIEW_NEEDED' | **PASS** |
| **TC-04** | สร้างตั๋วสั่งซื้อและบันทึกสถานะถาวร | Request SKU-0001, Qty 10 | บันทึกตั๋วสถานะ 'Draft' ลงไฟล์ CSV | สร้าง REQ-0001 สัมพันธ์สำเร็จ | **PASS** |
| **TC-05** | ลบตั๋วสั่งซื้อแบบ Soft Delete | Delete REQ-0001 | `is_deleted` เปลี่ยนเป็น `True` ข้อมูลไม่สูญหาย | `is_deleted` = True ซ่อนหน้าจอสำเร็จ | **PASS** |

---

## ⚠️ 8. ข้อจำกัดและสิ่งที่ไม่ควรอ้างอิงเกินจริง (Limitations)

1. **ใช้ Snapshot Date เป็น "วันนี้":** กำหนดให้วันที่ 31 ก.ค. 2026 เป็นวันอ้างอิงปัจจุบันของระบบ เพื่อให้สอดคล้องกับชุดข้อมูลประวัติการขาย
2. **ยอดขายเฉลี่ยเป็นค่าประมาณ:** คำนวณจากยอดขายย้อนหลัง 30 วัน ไม่ใช่ตัวเลขการพยากรณ์อนาคตด้วย Machine Learning
3. **ระบบเป็นเพียงเครื่องมือช่วยตัดสินใจ:** ระบบทำหน้าที่สร้างตั๋ว Draft และเสนอแนะ ไม่มีการส่งคำสั่งซื้อไปยังซัพพลายเออร์จริง และมนุษย์เป็นผู้อนุมัติเสมอ

---

## 🤖 9. เหตุผลที่ไม่ใช้ AI ในตัวผลิตภัณฑ์ (AI Policy)

สูตรการคำนวณความเสี่ยงขาดสต็อกอิงจากกฎทางธุรกิจที่ชัดเจน (`Days of Cover vs Lead Time`) ซึ่งเป็นเชิงตรรกะที่แน่นอน (**Deterministic Formula**) การใช้ AI/LLM ในส่วนนี้ไม่ช่วยเพิ่มประสิทธิภาพ และอาจเสี่ยงต่อการสร้างตัวเลขหลอนที่ไม่มีหลักฐานรองรับ (Hallucination) ทางทีมจึงใช้ Python Code ในการประเมินผล 100% *(รายละเอียดเพิ่มเติมอยู่ที่ `AI_USE.md`)*

---

## 👥 10. สมาชิกในทีมและบทบาทหน้าที่ (Team Members & Roles)

| ลำดับ | รหัสนิสิต | ชื่อ - นามสกุล | บทบาทและส่วนงานที่รับผิดชอบ |
| :---: | :---: | :----- | :--- |
| 1 | `67011216001` | ณัฐรีญา ศรีดาวงษ์   | **Team Lead & System Architecture:** ออกแบบโครงสร้างระบบ, GitHub Repository, `README.md` และ API Boundary |
| 2 | `67011216002` | พรพรรณ นันตะเวช   | **Data Pipeline & Cleaning:** สคริปต์ทำความสะอาดข้อมูล `data/cleaned/`, ตรวจสอบ Data Quality และคัดแยก `review_needed.csv` |
| 3 | `67011216004` | นิตยา บุตรดีขันธ์   | **Core Logic & UI Development:** พัฒนา `src/risk.py`, `src/storage.py` และหน้าจอ Gradio Dashboard (`src/app.py`) |
| 4 | `67011216014` | กัญญาณัฐ สีแสงน้อย   | **Testing & Documentation:** ออกแบบและรัน 5 Test Cases (`tests/`), จัดทำ `AI_USE.md` และเตรียม Demo Presentation |
