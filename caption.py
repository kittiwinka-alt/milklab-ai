import os
import google.generativeai as genai
from dotenv import load_dotenv

# 1. โหลดคีย์จากไฟล์ .env
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

# ตรวจสอบว่ามีคีย์ไหม
if not api_key:
    print("Error: ไม่พบ GOOGLE_API_KEY ในไฟล์ .env")
    exit(1)

# 2. ตั้งค่าการเชื่อมต่อกับ Gemini API
genai.configure(api_key=api_key)

# 3. กำหนดโจทย์ (Prompt) ด้วยหลัก PEFC
menu_name = "ลาเต้น้ำผึ้ง"
price = "65 บาท"

prompt = f"""
You are a marketing copywriter for cafés.
Generate 3 Instagram caption variants for a café named MilkLab based on this menu: {menu_name} price {price}.
The output must be strictly in Thai with a casual tone, and follow this exact format:

Cute: [ข้อความสไตล์อบอุ่น เอาใจ emoji เยอะ]
Minimal: [ข้อความสไตล์สั้น เรียบ หรู ห้ามใช้ emoji]
Gen-Z: [ข้อความสไตล์วัยรุ่น ใช้สแลงฮิตๆ]
"""

# 4. เรียกใช้โมเดล Gemini 2.5 Flash
model = genai.GenerativeModel('gemini-2.5-flash')
response = model.generate_content(prompt)

# 5. แสดงผลลัพธ์บน Terminal
print(response.text)
