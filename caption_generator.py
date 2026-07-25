import os
import argparse
from dotenv import load_dotenv
from google import genai

# โหลดค่าตัวแปรจากไฟล์ .env (เช่น GOOGLE_API_KEY)
load_dotenv()

# ข้อ 3: ข้อมูลเมนูสำหรับดึงราคาและส่วนผสมไปใส่ใน Prompt
MENU_DATA = {
    "ชาไทย": {"price": 45, "ingredients": "ชาไทยแท้ + นมข้นหวาน"},
    "นมหมีฮอกไกโด": {"price": 50, "ingredients": "นมตราหมี + ไซรัปฮอกไกโด"},
    "อเมริกาโน่": {"price": 55, "ingredients": "เมล็ดกาแฟคั่วกลาง + น้ำเปล่า"},
    "ลาเต้น้ำผึ้ง": {"price": 60, "ingredients": "เอสเพรสโซ่ช็อต + นมสด + น้ำผึ้งแท้"}
}

def generate_caption(menu, client):
    """
    ฟังก์ชันสำหรับสร้างแคปชั่น 1 ข้อความ และตรวจสอบความยาว
    """
    # ดึงข้อมูลจาก MENU_DATA ถ้าหาไม่เจอให้ใช้ค่าเริ่มต้นเพื่อไม่ให้โปรแกรมพัง
    menu_info = MENU_DATA.get(menu, {"price": "ไม่ระบุ", "ingredients": "สูตรลับเฉพาะของร้าน"})
    price = menu_info["price"]
    ingredients = menu_info["ingredients"]

    # สร้าง Prompt แบบ R-T-F-C พร้อมแนบ Context (ราคา, ส่วนผสม)
    prompt = f"""
    คุณคือ social media manager ของร้าน MilkLab
    เขียนแคปชั่นโปรโมตเมนู "{menu}"
    ข้อมูลเมนู: ราคา {price} บาท, ส่วนผสมหลักคือ {ingredients}
    
    ข้อกำหนด:
    - เขียน 2 ถึง 3 ประโยค
    - ภาษาไทย โทนสนุกสนาน เป็นกันเอง
    - มี emoji ประกอบและมี Call to Action (CTA) สั้นๆ ตอนท้าย
    - ห้ามใช้ em dash (—)
    - ความยาวทั้งหมดห้ามเกิน 280 ตัวอักษร
    """

    # ข้อ 4: ระบบขอเจนใหม่ (Regenerate) สูงสุด 3 รอบ ถ้าข้อความยาวเกิน
    max_attempts = 3
    for attempt in range(max_attempts):
        response = client.models.generate_content(
            model='gemini-3.5-flash-lite',
            contents=prompt,
        )
        text = response.text.strip()
        
        if len(text) <= 280:
            return text
        else:
            print(f"[ระบบ] ข้อความยาวเกินไป ({len(text)} ตัวอักษร) กำลังสร้างใหม่รอบที่ {attempt + 2}...")
            
    # ถ้าครบ 3 รอบยังเกิน 280 ตัวอักษร ให้แจ้ง Error โยนกลับไป
    raise RuntimeError("Error: ระบบไม่สามารถสร้างแคปชั่นที่สั้นกว่า 280 ตัวอักษรได้ภายใน 3 ครั้ง")

def generate_n(menu, n):
    """
    ฟังก์ชันเรียกวนลูปสร้างแคปชั่นตามจำนวน n ที่ผู้ใช้ต้องการ
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("ไม่พบ GOOGLE_API_KEY ในระบบ กรุณาตรวจสอบไฟล์ .env")
    
    # สร้าง Client ของ Google GenAI (SDK ใหม่)
    client = genai.Client(api_key=api_key)
    
    print(f"\n✨ กำลังสร้างแคปชั่นสำหรับ: {menu} จำนวน {n} แบบ...\n")
    
    # ข้อ 2: วนลูปและใส่ตัวเลขกำกับ
    for i in range(n):
        try:
            caption = generate_caption(menu, client)
            print(f"[{i+1}]\n{caption}\n")
        except Exception as e:
            print(f"[{i+1}] ❌ {e}\n")

def main():
    # ข้อ 1 & 2: ใช้ argparse เพื่อรับ Flag --menu และ --n ผ่าน CLI
    parser = argparse.ArgumentParser(description="MilkLab AI Caption Generator")
    parser.add_argument("--menu", type=str, required=True, help="ชื่อเมนูที่ต้องการโปรโมต")
    parser.add_argument("--n", type=int, default=1, help="จำนวน Caption ที่ต้องการสร้าง (ค่าเริ่มต้น: 1)")
    
    args = parser.parse_args()
    
    # ส่งข้อมูลเข้าฟังก์ชันจัดการหลัก
    generate_n(args.menu, args.n)

if __name__ == "__main__":
    main()