import os
import sys
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

# โหลดค่าคอนฟิกจากไฟล์ .env
load_dotenv()

def append_sale(menu, quantity, price):
    # เชื่อมต่อกับ Google Sheets โดยใช้ Identity ของ Service Account
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file("service-account.json", scopes=scopes)
    client = gspread.authorize(creds)
    
    # เปิดสเปรดชีตตาม ID ที่กำหนดไว้ใน .env
    sheet_id = os.getenv("GOOGLE_SHEETS_ID")
    sheet = client.open_by_key(sheet_id).sheet1
    
    # คำนวณราคารวม
    total = quantity * price
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # จัดเรียงข้อมูลลงคอลัมน์: วันที่ | เมนู | จำนวน | ราคา | ยอดรวม
    row = [date_str, menu, quantity, price, total]
    sheet.append_row(row)
    print(f"บันทึกยอดขายสำเร็จ: {row}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            raw_data = sys.argv[1]
            menu, qty, price = raw_data.split(":")
            append_sale(menu, int(qty), float(price))
        except ValueError:
            print("Error: กรุณากรอกข้อมูลให้ถูกฟอร์แมต (เมนู:จำนวน:ราคา) เช่น 'ชาไทย:3:55'")