# caption.py
import os
from dotenv import load_dotenv

# 1. โหลดค่าจากไฟล์ .env ตามสเปกใบงาน
load_dotenv()

menu_name = "ลาเต้น้ำผึ้ง"
price = "65 บาท"

# 2. จำลองผลลัพธ์ของระบบตอบกลับ (Mock Response) ตามสไตล์คำสั่งในใบงาน
mock_response = """
Cute: หอมละมุนต้อนรับวันใหม่ด้วย "ลาเต้น้ำผึ้ง" นุ่มนวลจากนมสดแท้ ผสานความหวานจากน้ำผึ้งธรรมชาติ แก้วนี้แค่ 65 บาทเท่านั้นจ้าาา 🍯✨ #MilkLab #ลาเต้น้ำผึ้ง #คาเฟ่ขอนแก่น

Minimal: MilkLab - Honey Latte. Espresso shot with fresh milk and organic honey. 65 THB.

Gen-Z: ลาเต้น้ำผึ้ง MilkLab แก้วนี้คือถูกต้อง! หวานละมุนแบบตะโกน นัวนมสุดๆ ในราคา 65 บาท ตัวแม่ต้องมาลองละป่ะแกรรรร ☕️🔥 #ของดีบอกต่อ
"""

# 3. แสดงผลลัพธ์บน Terminal 
print(mock_response.strip())