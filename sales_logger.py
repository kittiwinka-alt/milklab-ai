import streamlit as st
import os
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date, timezone, timedelta
from dotenv import load_dotenv

# โหลดตัวแปรจาก .env
load_dotenv()
GOOGLE_SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID")

# --- ฟังก์ชันส่งแจ้งเตือน Telegram ---
def send_telegram_notification(message):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        st.warning("คำเตือน: ยังไม่ได้ตั้งค่า Telegram Token จะข้ามการส่งข้อความ")
        return
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except Exception as e:
        st.error(f"Error sending Telegram notification: {e}")

# --- หน้าเว็บ UI ---
st.title("📸 Camera Craft: Sales Logger")
st.write("ระบบบันทึกยอดขายสินค้าหลังบ้าน")

with st.form("sales_log_form"):
    st.subheader("บันทึกรายการขายใหม่")
    
    col1, col2 = st.columns(2)
    with col1:
        sale_date = st.date_input("วันที่ขาย", date.today())
        brand = st.selectbox("แบรนด์", ["Panasonic", "Sony", "Canon", "Nikon", "Fujifilm", "Olympus", "อื่นๆ"])
        model = st.text_input("รุ่นกล้อง/เลนส์", placeholder="เช่น Lumix GF8")
    
    with col2:
        condition = st.selectbox("สภาพสินค้า", ["99% (เหมือนใหม่)", "95% (มีรอยนิดหน่อย)", "90% (ใช้งานปกติ)", "85% (มีตำหนิ)"])
        shutter_count = st.number_input("จำนวนชัตเตอร์ (ถ้ามี)", min_value=0, step=1000)
        price = st.number_input("ราคาขาย (บาท)", min_value=0, step=100, value=4500)
    
    accessories = st.text_input("ของแถม/อุปกรณ์ที่ให้ไป", placeholder="เช่น แบต 1, แท่นชาร์จ, สายคล้องคอ, เมม 32GB")
    note = st.text_area("หมายเหตุเพิ่มเติม")
    
    submit = st.form_submit_button("💾 บันทึกยอดขาย")

# --- เมื่อกดปุ่มบันทึก ---
if submit:
    if not model.strip():
        st.error("กรุณากรอกชื่อรุ่นกล้อง/เลนส์ด้วยครับ!")
    else:
        with st.spinner("กำลังส่งข้อมูลเข้า Google Sheets และ Telegram..."):
            try:
                # 1. จัดการเวลาไทย
                th_tz = timezone(timedelta(hours=7)) 
                time_str = datetime.now(th_tz).strftime("%H:%M:%S")
                full_date_str = f"{sale_date.strftime('%Y-%m-%d')} {time_str}"
                
                # 2. เตรียมข้อมูล 8 คอลัมน์
                row_data = [full_date_str, brand, model, condition, shutter_count, price, accessories, note]
                
                # 3. ส่งเข้า Google Sheets ด้วย gspread
                scopes = ["https://www.googleapis.com/auth/spreadsheets"]
                creds = Credentials.from_service_account_file("service-account.json", scopes=scopes)
                client = gspread.authorize(creds)
                sheet = client.open_by_key(GOOGLE_SHEETS_ID).sheet1
                
                sheet.append_row(row_data)
                
                # 4. ส่งแจ้งเตือน Telegram
                notification_msg = f"📸 ยอดขาย Camera Craft ใหม่!\nแบรนด์: {brand}\nรุ่น: {model}\nสภาพ: {condition}\nราคา: {price} บาท\nของแถม: {accessories}"
                send_telegram_notification(notification_msg)
                
                # 5. แสดงผลลัพธ์บนหน้าเว็บ
                st.success(f"🎉 บันทึกยอดขาย {brand} {model} ลง Sheets และส่งเข้ามือถือสำเร็จแล้วครับ!")
                with st.expander("ดูข้อมูลที่ถูกบันทึก"):
                    st.write(row_data)
                    
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาดในการเชื่อมต่อ: {e}")
                st.info("💡 อย่าลืมเช็กว่าไฟล์ service-account.json ยังอยู่ในโปรเจกต์นะครับ")