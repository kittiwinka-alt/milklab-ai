import os
import sys
from datetime import datetime
import gspread
import requests
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

# โหลดค่าคอนฟิกจากไฟล์ .env
load_dotenv()

def send_telegram_message(menu, quantity, total):
    # ดึงค่า Token และ Chat ID จาก .env
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("ข้ามการส่ง Telegram: ไม่พบการตั้งค่า Token หรือ Chat ID ใน .env")
        return

    # จัดข้อความสำหรับส่ง
    message = f"🔔 **MilkLab Morning Report** 🔔\n\n📌 มีออเดอร์ใหม่เข้าระบบ!\nเมนู: {menu}\nจำนวน: {quantity} แก้ว\nรวมทั้งสิ้น: {total} บาท\n\nบันทึกข้อมูลเรียบร้อยแล้วค่ะ 📝"
    
    # ยิง API ไปยัง Telegram
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("📲 ส่งรายงานเข้า Telegram สำเร็จ!")
        else:
            print(f"❌ ส่ง Telegram ล้มเหลว: {response.text}")
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการส่ง Telegram: {e}")

def append_sale(menu, quantity, price):
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file("service-account.json", scopes=scopes)
    client = gspread.authorize(creds)
    
    sheet_id = os.getenv("GOOGLE_SHEETS_ID")
    sheet = client.open_by_key(sheet_id).sheet1
    
    total = quantity * price
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    row = [date_str, menu, quantity, price, total]
    sheet.append_row(row)
    print(f"บันทึกยอดขายสำเร็จ: {row}")
    
    # เรียกฟังก์ชันส่งข้อความเข้า Telegram
    send_telegram_message(menu, quantity, total)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            raw_data = sys.argv[1]
            menu, qty, price = raw_data.split(":")
            append_sale(menu, int(qty), float(price))
        except ValueError:
            print("Error: กรุณากรอกข้อมูลให้ถูกฟอร์แมต (เมนู:จำนวน:ราคา) เช่น 'ชาไทย:3:55'")