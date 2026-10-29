@echo off
REM ดับเบิลคลิกเพื่อรันบน Windows (สร้าง .venv และติดตั้งให้อัตโนมัติครั้งแรก)
cd /d "%~dp0"
if not exist .venv ( py -3 -m venv .venv )
call .venv\Scripts\activate
python -m pip install -q -r requirements.txt
start "" http://127.0.0.1:8000
python -m uvicorn api.main:app --port 8000
