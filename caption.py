import os
from google import genai
from dotenv import load_dotenv

# 1. โหลดค่าจากไฟล์ .env
load_dotenv()

# 2. ดึงคีย์จาก environment variable
api_key = os.getenv("GEMINI_API_KEY")

# 3. ตั้งค่า Client ด้วยคีย์ที่ดึงมา
client = genai.Client(api_key=api_key)

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

# 4. เรียกใช้โมเดล gemini-3.5-flash
response = client.models.generate_content(
    model='gemini-3.5-flash-lite',
    contents=prompt,
)

print(response.text)