import os
import sys
from datetime import datetime
import gspread
import json
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

# ฟังก์ชันบันทึกประวัติลูปการทำงานของ Agent ลงไฟล์ Log
def log_agent_trace(event_type, detail):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"{timestamp} | {event_type} | {detail}\n"
    with open("agent_trace.log", "a", encoding="utf-8") as f:
        f.write(log_line)

def append_sale(menu, quantity, price):
    # 1. Validation Logic (Guardrail สกัดกั้นข้อมูลเพี้ยน)
    if not menu.strip():
        log_agent_trace("tool_error", "ValueError: menu name cannot be empty")
        raise ValueError("menu name cannot be empty")
    if quantity <= 0:
        log_agent_trace("tool_error", f"ValueError: quantity must be positive (got {quantity})")
        raise ValueError("quantity must be positive")
    if price <= 0:
        log_agent_trace("tool_error", f"ValueError: price must be positive (got {price})")
        raise ValueError("price must be positive")

    # 2. เชื่อมต่อ Google Sheets
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file("service-account.json", scopes=scopes)
    client = gspread.authorize(creds)
    
    sheet_id = os.getenv("GOOGLE_SHEETS_ID")
    sheet = client.open_by_key(sheet_id).sheet1
    
    total = quantity * price
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    row = [date_str, menu, quantity, price, total]
    sheet.append_row(row)
    
    # 3. บันทึกผลลัพธ์สำเร็จ
    log_agent_trace("tool_result", "row appended successfully")
    print(f"บันทึกยอดขายสำเร็จ: {row}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        raw_input = sys.argv[1]
        
        # บันทึกเหตุการณ์แรก: ได้รับข้อความสั่งการจาก User
        log_agent_trace("user_input", raw_input)
        
        try:
            # จำลองพฤติกรรมคิดวิเคราะห์พารามิเตอร์ของ LLM ออกมาเป็น JSON
            menu, qty, price_str = raw_input.split(":")
            llm_decision = {"tool": "append_sale", "args": {"item": menu, "qty": int(qty), "price": float(price_str)}}
            
            # บันทึกเหตุการณ์ที่สอง: LLM ตัดสินใจเลือกใช้ Tool
            log_agent_trace("llm_response", json.dumps(llm_decision, ensure_ascii=False))
            
            # รัน Tool จริง
            append_sale(menu, int(qty), float(price_str))
            
        except Exception as e:
            print(f"Error: {e}")