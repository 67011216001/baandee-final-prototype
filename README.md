# 📦 BaanDee Stockout Radar

**ระบบช่วยตรวจสอบสินค้าที่มีความเสี่ยงขาดสต็อก และสร้างร่างคำขอสั่งซื้อ (Data Product Prototype)**
*ต้นแบบสำหรับ Final Project · บริษัทสมมติ BaanDee Living · รายวิชา Data Product Development*

> **ระบบหลัก:** ตรวจว่าสินค้าใดเสี่ยงขาดสต็อก พร้อมบอกว่า "ควรสั่งภายในกี่วัน"
> **ระบบรอง:** ปุ่มสร้าง **ร่างคำขอสั่งซื้อภายใน** ให้หัวหน้าอนุมัติ (ไม่ใช่ใบสั่งซื้อจริง)

---

## 🎯 1. ปัญหา ผู้ใช้ และคุณค่าที่คาดหวัง

### 1.1 ผู้ใช้
- **ผู้ใช้หลัก:** เจ้าหน้าที่จัดซื้อ / วางแผนสต็อกของ BaanDee Living
- **ผู้ใช้รอง:** หัวหน้าฝ่ายจัดซื้อ (ผู้อนุมัติร่างคำขอสั่งซื้อ)

### 1.2 งานที่ผู้ใช้ต้องทำ (Job-to-be-Done)
ตัดสินใจทุกวันว่า **ควรขอสั่งสินค้ารายการใด จำนวนเท่าไร และเร่งด่วนแค่ไหน** ก่อนสินค้าหมดคลัง โดยเทียบ 3 ปัจจัยพร้อมกัน:
1. สต็อกคงเหลือ ณ วัน Snapshot
2. ยอดขายเฉลี่ยต่อวัน (ย้อนหลัง 30 วัน)
3. ระยะเวลาจัดส่งของซัพพลายเออร์ (Lead Time)

### 1.3 ปัญหาในกระบวนการปัจจุบัน
1. **ข้อมูลกระจายคนละแห่ง** (สินค้า สต็อก ยอดขาย Lead Time) ทำให้เสียเวลารวบรวม
2. **ไม่มีเกณฑ์กลางประเมินความเสี่ยง** แต่ละคนใช้ดุลยพินิจต่างกัน
3. **ดูสต็อกอย่างเดียวบอกความเร่งด่วนไม่ได้** สต็อก 10 ชิ้นอาจขายได้อีก 2 วันหรือ 2 เดือน
4. **ไม่มีการเตือนเมื่อข้อมูลไม่สมบูรณ์** ข้อมูลขาดหายมักถูกละเลยหรือเดา

### 1.4 ต้นแบบนี้ช่วยอย่างไร
- **รวมข้อมูลในหน้าจอเดียว:** เชื่อมข้อมูลด้วย `product_id` จากหลายแหล่งมาแสดงใน Dashboard เดียว
- **ประเมินความเสี่ยงด้วยกฎที่ตายตัว (Deterministic Rule)** ตามหัวข้อ 3.1
- **บอกเวลาที่ควรสั่ง:** คอลัมน์ "ควรสั่งภายใน" = Days of Cover − Lead Time (ติดลบ = เลยกำหนดแล้ว)
- **แยก "ข้อเท็จจริง" ออกจาก "ค่าประมาณ":** สต็อก/Lead Time/MOQ เป็นข้อเท็จจริงจากฐานข้อมูล ส่วนยอดขายเฉลี่ยและจำนวนแนะนำเป็นค่าประมาณ (แสดงป้ายต่างกันในหน้ารายละเอียดสินค้า)
- **หยุดแล้วส่งให้คนตรวจเมื่อข้อมูลไม่พร้อม:** ข้อมูลขาด/ผิดปกติจะติดป้าย `HUMAN_REVIEW_NEEDED` พร้อมเหตุผล และ**ไม่ให้สร้างร่างคำขอ** (ระบบไม่เดาค่า)

### 1.5 สมมติฐานที่ยังต้องทดลองกับผู้ใช้จริง
- **H1:** เจ้าหน้าที่ใช้เวลาตรวจรายการเสี่ยงน้อยลงเมื่อมี Dashboard รวมข้อมูล
- **H2:** กฎจัดระดับความเสี่ยงตรงกับการตัดสินใจของผู้เชี่ยวชาญจริง
- **H3:** ป้าย "ต้องให้คนตรวจ" ช่วยลดความผิดพลาดจากการประเมินมั่ว

---

## 📊 2. ข้อมูล ความสัมพันธ์ และคุณภาพข้อมูล

### 2.1 แหล่งข้อมูล
| โฟลเดอร์ | ไฟล์ | หมายเหตุ |
|---|---|---|
| `data/raw/` | `products`, `inventory_snapshot`, `orders`, `order_lines`, `customers`, `support_tickets`, `delay_policy.json` | ข้อมูลดิบ 7 ไฟล์ (ไม่แก้ทับ) · สต็อก ณ **31 ก.ค. 2026** |
| `data/generated/` | `supplier_lead_time.csv` | ข้อมูลแหล่งที่ 2 ที่สังเคราะห์ขึ้น ฝังข้อมูลบกพร่องไว้ทดสอบ Failure Behavior |
| `data/cleaned/` | `cleaned_products`, `cleaned_inventory_snapshot`, `cleaned_orders`, `cleaned_order_lines`, `joined_products_supplier` | ผลการทำความสะอาดและ Left Join สินค้า + ซัพพลายเออร์ |
| `data/app_state/` | `reorder_requests.csv` | สถานะร่างคำขอที่สร้างจากหน้าเว็บ (สร้างอัตโนมัติเมื่อใช้งานครั้งแรก) |

> ผลประเมินความเสี่ยง **ไม่ได้บันทึกเป็นไฟล์** แต่คำนวณสดทุกครั้งที่เปิดหน้าเว็บ (`src/risk.py`) เพื่อให้ตรงกับข้อมูลล่าสุดเสมอ

### 2.2 ลำดับการไหลของข้อมูล

```
 raw/ (products, inventory, orders, order_lines)      generated/ (supplier_lead_time)
              │                                                    │
              └──────────── Clean + Join ด้วย product_id ───────────┘
                          (รูปแบบ SKU-XXXX, trim, Title Case)
                                         │
                                         v
                          cleaned/joined_products_supplier.csv
                                         │
                                         v
              ┌────────────────────────────────────────────────┐
              │ Risk Engine (src/risk.py) คำนวณสดทุกครั้ง       │
              │ ยอดขาย 30 วัน → Days of Cover → เทียบ Lead Time │
              └───────────────┬────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              v                               v
   CRITICAL / WARNING / NORMAL        HUMAN_REVIEW_NEEDED
   (แสดง + สร้างร่างคำขอได้)           (ข้อมูลไม่พอ: แสดงเหตุผล, ห้ามสร้างร่าง)
              │
              v
   FastAPI (api/main.py)  →  Dashboard (web/index.html)  →  data/app_state/reorder_requests.csv
```

- **Join Rule:** ใช้ `product_id` ในรูปแบบมาตรฐาน `SKU-XXXX` เป็นกุญแจเชื่อมตาราง
- **Quarantine Rule:** รายการที่ Lead Time เป็น `NaN`/ติดลบ, รหัส SKU ผิดรูปแบบ หรือไม่พบสต็อก จะได้สถานะ `HUMAN_REVIEW_NEEDED` พร้อม `review_reason` และระบบไม่เดาค่าแทน

### 2.3 ปัญหาคุณภาพข้อมูลที่พบและวิธีจัดการ
| # | ปัญหา | หลักฐาน (Before) | วิธีตรวจพบ | วิธีจัดการ (After) |
|:-:|---|---|---|---|
| 1 | รหัส SKU ผิดฟอร์แมต | `SKU-BD-220`, `SKU-KT-104` ใน `products.csv` | Regex `^SKU-\d{4}$` | ไม่เดา → ติดป้าย `HUMAN_REVIEW_NEEDED` |
| 2 | ชื่อหมวดสะกดไม่เป็นมาตรฐาน | `kitchen`/`Kitchen`, `bedding`/`Bedding`, `Bed room` | `value_counts()` | `trim` + Title Case → เหลือ 4 หมวดมาตรฐาน |
| 3 | รูปแบบวันที่ปนกัน | `28/07/2026`, `07/08/2026` ใน `orders.order_date` | Regex `^\d{4}-\d{2}-\d{2}$` | แปลงเป็น `YYYY-MM-DD` |

---

## 🧮 3. กฎความเสี่ยง สถาปัตยกรรม และ API

### 3.1 กฎประเมินความเสี่ยง (ไม่ใช้ AI)

`Days of Cover = สต็อกคงเหลือ ÷ ยอดขายเฉลี่ยต่อวัน (ย้อนหลัง 30 วันจาก Snapshot)`

| ระดับ | เงื่อนไข | ความหมาย |
|---|---|---|
| `CRITICAL_RISK` เสี่ยงสูง | Days of Cover **<** Lead Time (หรือสต็อก = 0) | ของจะหมดก่อนของใหม่มาถึง |
| `WARNING_RISK` เสี่ยงปานกลาง | Lead Time ≤ Days of Cover ≤ Lead Time + 7 | เหลือเวลาสั่งไม่นาน |
| `NORMAL` ยังไม่เสี่ยง | Days of Cover > Lead Time + 7 (หรือไม่มียอดขาย) | สต็อกเพียงพอ |
| `HUMAN_REVIEW_NEEDED` ต้องให้คนตรวจ | Lead Time ขาด/≤ 0, สต็อกขาด/ติดลบ, SKU ผิดรูปแบบ | ข้อมูลไม่พอ ระบบไม่เดา |

- **ควรสั่งภายใน (วัน)** = Days of Cover − Lead Time
- **จำนวนแนะนำ (ค่าประมาณ)** = ยอดขาย/วัน × (Lead Time + 14 วันสำรอง) − สต็อก ปัดขึ้นเป็นเท่าของ MOQ

### 3.2 Tech Stack
- **Backend/Analytics:** Python 3.11+, `pandas`, `numpy`
- **API:** `FastAPI` + `Uvicorn`
- **Frontend:** หน้าเว็บ HTML/CSS/JavaScript (`web/index.html`) ให้บริการโดย FastAPI ไม่ต้องใช้ Colab หรือ Gradio
- **Storage:** CSV (`data/app_state/reorder_requests.csv`)
- **Testing:** `pytest`

### 3.3 API Endpoints
| Method | Path | หน้าที่ |
|---|---|---|
| GET | `/api/summary` | จำนวนสินค้าแต่ละระดับ, วัน Snapshot, รายการหมวด |
| GET | `/api/risk` · `/api/risk/{product_id}` | รายการ/รายละเอียดความเสี่ยง (กรองด้วย `status`, `category`, `q`) |
| GET | `/get_supplier_lead_time_api?product_id=` | **จุดเชื่อมต่อข้ามระบบ** ดึง Lead Time ซัพพลายเออร์ |
| GET / POST | `/api/requests` | ดู / สร้างร่างคำขอ (Create, Read) |
| PATCH | `/api/requests/{id}` | แก้จำนวน / อนุมัติ (Update) |
| DELETE | `/api/requests/{id}` | ซ่อนรายการ (Soft Delete) |

**API ข้ามระบบรองรับ 3 สถานการณ์:**
1. **200** พบข้อมูล → คืน `product_id`, `supplier_name`, `lead_time_days`
2. **404** ไม่พบ SKU หรือ Lead Time ขาด/ผิดปกติ → คืน `HUMAN_REVIEW_NEEDED`
3. **503** ไฟล์ข้อมูลซัพพลายเออร์ขาดหายหรือเสีย → บริการไม่พร้อมใช้งาน

### 3.4 ร่างคำขอสั่งซื้อ (ฟังก์ชันรอง)
ฟิลด์ที่บันทึก: `request_id`, `product_id`, `product_name`, `requested_qty`, `risk_status` (ณ วันสร้าง), `status` (`Draft` → `Approved`), `created_at`, `updated_at`, `is_deleted`
- เป็น **ร่างภายใน** เพื่อให้หัวหน้าอนุมัติ **ไม่ส่งคำสั่งซื้อจริงไปยังซัพพลายเออร์** (Human-in-the-loop)
- สินค้าที่เป็น `HUMAN_REVIEW_NEEDED` สร้างร่างไม่ได้ (API ตอบ 409)
- Soft Delete ตั้ง `is_deleted = True` โดยไม่ลบแถวออกจากไฟล์ (Audit Trail)

---

## 📂 4. โครงสร้าง Repository

```
baandee-final-prototype/
├── api/
│   └── main.py              # FastAPI: Risk API, Lead Time API, CRUD ร่างคำขอ, เสิร์ฟหน้าเว็บ
├── src/
│   ├── risk.py              # เอนจินคำนวณ Days of Cover และจัดระดับความเสี่ยง
│   └── storage.py           # CRUD ร่างคำขอ (Draft / Approve / Soft Delete) ลง CSV
├── web/
│   └── index.html           # หน้า Dashboard (ตรวจความเสี่ยง + ร่างคำขอสั่งซื้อ)
├── data/
│   ├── raw/  generated/  cleaned/  app_state/
├── tests/
│   ├── conftest.py
│   └── test_pipeline.py     # ชุดทดสอบอัตโนมัติ (ใช้สำเนาข้อมูลชั่วคราว)
├── docs/
│   └── VSCODE_SETUP.md      # วิธีรันบน VS Code และแก้ปัญหาที่พบบ่อย
├── .vscode/                 # launch.json (กด F5 รันเว็บ), settings.json
├── run.bat / run.sh         # ทางลัดติดตั้งและรัน
├── TEST_CASES.md            # รายงานผลทดสอบฉบับเต็ม
├── AI_USE.md                # รายงานการใช้งาน AI
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 🚀 5. วิธีติดตั้งและเริ่มระบบ (VS Code)

```bash
# 1. Clone
git clone https://github.com/67011216001/baandee-final-prototype.git
cd baandee-final-prototype

# 2. สร้าง Virtual Environment แล้วติดตั้งไลบรารี
python -m venv .venv
source .venv/bin/activate        # Windows (PowerShell): .venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 3. รันระบบ
python -m uvicorn api.main:app --reload
```

เปิดเบราว์เซอร์ที่ **http://127.0.0.1:8000** (หรือใน VS Code กด **F5** เลือก "BaanDee: รันเว็บ (FastAPI)")
Windows ดับเบิลคลิก `run.bat` / macOS-Linux รัน `./run.sh` ได้เช่นกัน

```bash
# รันชุดทดสอบ
python -m pytest tests -q
```

> ต้องเปิดผ่านเซิร์ฟเวอร์ข้างบนเท่านั้น (ห้ามดับเบิลคลิก `index.html` ตรงๆ เพราะหน้าเว็บต้องเรียก `/api/...`) · ปัญหาที่พบบ่อยดู `docs/VSCODE_SETUP.md`

---

## 🎬 6. กรณีสาธิตหลัก

1. **ทำงานสำเร็จ (Success Flow):** หน้า "ตรวจความเสี่ยง" → คลิกการ์ด **เสี่ยงสูง** เพื่อกรอง → คลิกสินค้า ดูสต็อก ยอดขาย Lead Time Days of Cover และ "ควรสั่งภายใน" → **สร้างร่างคำขอ** → แท็บ "ร่างคำขอสั่งซื้อ" แก้จำนวนและกด **อนุมัติ** → ปิดแล้วเปิดโปรแกรมใหม่ รายการยังอยู่ครบ (Persistence)
2. **หยุดส่งต่อให้คนตรวจ (Failure Flow):** คลิกการ์ด **ต้องให้คนตรวจ** → เลือก SKU-0015 (Lead Time เป็น `NaN`) → ระบบแสดงเหตุผลและ**ไม่ให้สร้างร่างคำขอ**
3. **ลบแบบซ่อน (Soft Delete):** ที่แท็บร่างคำขอ กด **ลบ** → รายการหายจากหน้าจอ แต่แถวยังอยู่ในไฟล์ CSV โดย `is_deleted = True`

---

## 🧪 7. สรุปผลการทดสอบ

รายละเอียดเต็ม (Input, Expected, Actual, Pass/Fail) ดู [**TEST_CASES.md**](./TEST_CASES.md) · รันซ้ำได้ด้วย `python -m pytest tests -q`

| Test ID | กรณีทดสอบ | Expected Result |
|:-:|---|---|
| TC-01 | SKU ปกติที่สต็อกพอ | `risk_status` = `NORMAL` |
| TC-02 | สินค้าสต็อกหมดหรือเสี่ยงวิกฤต | `risk_status` = `CRITICAL_RISK` |
| TC-03 | Lead Time ขาดหาย | `risk_status` = `HUMAN_REVIEW_NEEDED` |
| TC-04 | สร้างร่างคำขอและบันทึกถาวร | บันทึกสถานะ `Draft` ลง CSV |
| TC-05 | ลบร่างคำขอแบบ Soft Delete | `is_deleted` = `True` ข้อมูลยังอยู่ |

---

## ⚠️ 8. ข้อจำกัด

1. **Snapshot Date เป็น "วันนี้":** ใช้วันที่ 31 ก.ค. 2026 เป็นวันอ้างอิงของระบบให้สอดคล้องกับข้อมูลยอดขาย
2. **ยอดขายเฉลี่ยเป็นค่าประมาณ:** คำนวณจากยอดขายย้อนหลัง 30 วัน ไม่ใช่การพยากรณ์ด้วย Machine Learning
3. **เป็นเครื่องมือช่วยตัดสินใจเท่านั้น:** สร้างร่างภายในและเสนอจำนวนแนะนำ ไม่ส่งคำสั่งซื้อจริง และมนุษย์เป็นผู้อนุมัติเสมอ
4. **ข้อมูลเป็นข้อมูลสังเคราะห์:** ไม่ได้ผ่านการทดลองกับผู้ใช้จริง สมมติฐาน H1–H3 จึงยังไม่ได้พิสูจน์

---

## 🤖 9. เหตุผลที่ไม่ใช้ AI ในตัวผลิตภัณฑ์

สูตรความเสี่ยงอิงกฎธุรกิจที่ชัดเจน (`Days of Cover` เทียบ `Lead Time`) ซึ่งเป็นตรรกะที่แน่นอน การใช้ AI/LLM ไม่ช่วยเพิ่มประสิทธิภาพและเสี่ยงสร้างตัวเลขที่ไม่มีหลักฐานรองรับ จึงใช้โค้ด Python ประเมินผล 100% (รายละเอียดดู [**AI_USE.md**](./AI_USE.md))

---

## 👥 10. สมาชิกในทีมและบทบาทหน้าที่

| # | รหัสนิสิต | ชื่อ - นามสกุล | บทบาท |
|:-:|:-:|---|---|
| 1 | `67011216002` | พรพรรณ นันตะเวช | **Data Cleaning & Inspection:** สำรวจคุณภาพข้อมูลดิบ 7 ไฟล์ ทำความสะอาด และคัดแยกข้อมูลกำกวม |
| 2 | `67011216004` | นิตยา บุตรดีขันธ์ | **Synthetic Data & Risk Calculation:** สร้าง `supplier_lead_time.csv` พร้อมเคสทดสอบ, Data Join และเอนจินคำนวณความเสี่ยง |
| 3 | `67011216001` | ณัฐรีญา ศรีดาวงษ์ | **GitHub & UI Prototype:** จัดการ Repository, ระบบบันทึกร่างคำขอ (Storage) และหน้า Dashboard |
| 4 | `67011216014` | กัญญาณัฐ สีแสงน้อย | **Testing & Documentation:** ออกแบบและรันทดสอบ, จัดทำ README / AI_USE / TEST_CASES และสไลด์นำเสนอ |

---

## 🏷️ 11. Final Checklist ก่อนส่งงาน

- [ ] ไฟล์ชื่อ `README.md` และ `AI_USE.md` (ไม่มีเว้นวรรคก่อน `.md`)
- [ ] `python -m pytest tests -q` ผ่านทั้งหมดบนเครื่องที่ clone ใหม่
- [ ] README คำสั่งรันตรงกับโค้ดจริง (FastAPI + `web/index.html`)
- [ ] Push `api/`, `web/`, `tests/`, `.vscode/`, `requirements.txt`, `run.bat`, `run.sh` ขึ้น GitHub ครบ
- [ ] ไม่มี API Key, `.env`, `.venv/` ติดขึ้น Repository
- [ ] สร้าง Git Tag / Release `v1.0-final`
