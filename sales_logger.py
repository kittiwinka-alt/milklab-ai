import os
import sys
import argparse
import requests
from datetime import datetime, timezone, timedelta
import gspread
import json
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

# ฟังก์ชันบันทึกประวัติลูปการทำงานของ Agent ลงไฟล์ Log
def log_agent_trace(event_type, detail):
    th_tz = timezone(timedelta(hours=7)) # สร้างโซนเวลา UTC+7
    timestamp = datetime.now(th_tz).strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"{timestamp} | {event_type} | {detail}\n"
    with open("agent_trace.log", "a", encoding="utf-8") as f:
        f.write(log_line)

# ฟังก์ชันส่งแจ้งเตือนเข้า Telegram
def send_telegram_notification(message):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("คำเตือน: ยังไม่ได้ตั้งค่า TELEGRAM_BOT_TOKEN หรือ TELEGRAM_CHAT_ID จะข้ามการส่งข้อความ")
        return
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("ส่งแจ้งเตือน Telegram สำเร็จ")
    except Exception as e:
        print(f"Error sending Telegram notification: {e}")

def append_sale(menu, quantity, price):
    # 1. Validation Logic
    if not menu.strip():
        log_agent_trace("tool_error", "ValueError: menu name cannot be empty")
        raise ValueError("menu name cannot be empty")
    if quantity <= 0:
        log_agent_trace("tool_error", f"ValueError: quantity must be positive (got {quantity})")
        raise ValueError("quantity must be positive")
    if price <= 0:
        log_agent_trace("tool_error", f"ValueError: price must be positive (got {price})")
        raise ValueError("price must be positive")

    # 2. เชื่อมต่อ Google Sheets (ดัก Error กรณี Sheets พังหรือเข้าถึงไม่ได้)
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_file("service-account.json", scopes=scopes)
        client = gspread.authorize(creds)
        
        sheet_id = os.getenv("GOOGLE_SHEETS_ID")
        sheet = client.open_by_key(sheet_id).sheet1
        
        total = quantity * price
        
        # --- จัดการเวลาไทย (UTC+7) ตรงนี้จุดเดียว ---
        th_tz = timezone(timedelta(hours=7)) 
        date_str = datetime.now(th_tz).strftime("%Y-%m-%d %H:%M:%S")
        
        row = [date_str, menu, quantity, price, total]
        sheet.append_row(row)
        
    except Exception as e:
        error_msg = f"Error: ไม่สามารถเข้าถึง Google Sheets ได้ - {str(e)}"
        print(error_msg)
        log_agent_trace("tool_error", error_msg)
        sys.exit(1) # บังคับจบโปรแกรมและแจ้งสถานะ Error กลับไประบบ

    # 3. ส่งข้อความแจ้งเตือนเข้าบอทและบันทึกล็อกความสำเร็จ
    notification_msg = f"💸 บันทึกยอดขายใหม่!\nเมนู: {menu}\nจำนวน: {quantity} แก้ว\nราคา: {price} บาท\nยอดรวม: {total} บาท"
    send_telegram_notification(notification_msg)
    
    log_agent_trace("tool_result", "row appended successfully")
    print(f"บันทึกยอดขายลง Sheets สำเร็จ: {row}")

if __name__ == "__main__":
    # ใช้ argparse แทน sys.argv ธรรมดาเพื่อให้รับ Flag ตามโจทย์
    parser = argparse.ArgumentParser(description="Sales Logger with Bot Notification")
    parser.add_argument("--menu", type=str, required=True, help="ชื่อเมนู")
    parser.add_argument("--qty", type=int, required=True, help="จำนวน")
    parser.add_argument("--price", type=float, required=True, help="ราคาต่อหน่วย")
    
    args = parser.parse_args()
    
    raw_input = f"--menu {args.menu} --qty {args.qty} --price {args.price}"
    log_agent_trace("user_input", raw_input)
    
    try:
        # จำลองการสร้าง JSON ของ LLM ให้สอดคล้องกับ Input ที่ปรับใหม่
        llm_decision = {"tool": "append_sale", "args": {"item": args.menu, "qty": args.qty, "price": args.price}}
        log_agent_trace("llm_response", json.dumps(llm_decision, ensure_ascii=False))
        
        # รัน Tool จริง
        append_sale(args.menu, args.qty, args.price)
        
    except Exception as e:
        print(f"Error: {e}")
        