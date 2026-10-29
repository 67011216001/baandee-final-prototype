# รัน BaanDee Stockout Radar บน VS Code (ทำตามทีละขั้น)

## ครั้งแรก
1. ติดตั้ง **Python 3.11+** (บน Windows ติ๊ก *Add Python to PATH*) และ **VS Code** + extension **Python**
2. เปิดโฟลเดอร์โปรเจกต์: `File > Open Folder` (ต้องเปิดที่โฟลเดอร์ที่มี `data/`, `src/`, `api/` อยู่ข้างใน)
3. เปิด Terminal ใน VS Code แล้วพิมพ์ทีละบรรทัด

   Windows (PowerShell):
   ```
   py -3 -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   python -m uvicorn api.main:app --reload
   ```
   macOS/Linux:
   ```
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   python -m uvicorn api.main:app --reload
   ```
4. เปิดเบราว์เซอร์ที่ http://127.0.0.1:8000

ทางลัด: Windows ดับเบิลคลิก `run.bat` / macOS-Linux รัน `./run.sh` (ทำขั้นตอนข้างบนให้ทั้งหมด)

## ครั้งถัดไป
Activate `.venv` แล้วรัน `python -m uvicorn api.main:app --reload` หรือกด **F5** เลือก "BaanDee: รันเว็บ (FastAPI)"

## ปัญหาที่เจอบ่อย
| อาการ | วิธีแก้ |
|---|---|
| PowerShell: "running scripts is disabled" ตอน Activate | รัน `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` แล้วลองใหม่ หรือใช้ `run.bat` |
| `ModuleNotFoundError: fastapi` | ยังไม่ activate `.venv` หรือยังไม่ `pip install -r requirements.txt` (ดูว่ามี `(.venv)` หน้าบรรทัด) |
| `FileNotFoundError ... data/cleaned/...` | เปิดโฟลเดอร์ผิดชั้น หรือไฟล์ CSV ถูกลบ/ย้าย |
| พอร์ต 8000 ถูกใช้อยู่ | เพิ่ม `--port 8001` แล้วเปิด http://127.0.0.1:8001 |
| CSV ภาษาไทยเพี้ยนใน Excel | เปิดด้วย VS Code หรือบันทึกเป็น UTF-8 |
| หน้าเว็บว่าง | กด F12 > Console ดู error และดู terminal ที่รันเซิร์ฟเวอร์ |

## รันเทสต์
```
python -m pytest tests -q
```
เทสต์ใช้สำเนาข้อมูลชั่วคราว รันซ้ำกี่ครั้งก็ผลเท่าเดิม และไม่แตะ `data/app_state/reorder_requests.csv` จริง

## หมายเหตุ
- ไฟล์ `README .md` และ `AI_USE .md` มี **เว้นวรรคก่อน .md** ควร rename เป็น `README.md` / `AI_USE.md` เพื่อให้ GitHub แสดงหน้าแรกของ repo
- ข้อมูลทั้งหมดเป็นข้อมูลสังเคราะห์ ไม่มี secret
