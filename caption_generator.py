import streamlit as st
import os
from google import genai
from dotenv import load_dotenv

# โหลด API Key
load_dotenv()
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

st.title("📸 Camera Craft: AI Caption Generator")
st.write("เครื่องมือช่วยแต่งแคปชั่นขายกล้องและเลนส์มือสองแบบมือโปร")

# ฟอร์มรับข้อมูลสินค้า
with st.form("camera_form"):
    brand_model = st.text_input("แบรนด์และรุ่นกล้อง/เลนส์", placeholder="เช่น Panasonic Lumix GF8")
    condition = st.selectbox("สภาพสินค้า (%)", ["99% (สภาพนางฟ้า เหมือนใหม่)", "95% (มีรอยขนแมวนิดหน่อย)", "90% (ใช้งานปกติ มีรอยตามการใช้งาน)", "85% (มีตำหนิ แต่ใช้งานเต็มระบบ)"])
    price = st.number_input("ราคา (บาท)", min_value=0, step=100, value=4500)
    accessories = st.text_input("อุปกรณ์ที่แถม", placeholder="เช่น เลนส์คิต, แบต 1 ก้อน, ที่ชาร์จแท้, สายคล้องคอ")
    highlights = st.text_area("จุดเด่น/สเปกที่อยากเน้น", placeholder="เช่น หน้าจอพับเซลฟี่ได้ 180 องศา, มี WiFi ส่งรูปเข้ามือถือได้เลย")
    
    submit = st.form_submit_button("✨ สร้างแคปชั่นขายของ")

# เมื่อกดปุ่ม
if submit and brand_model:
    prompt = f"""คุณคือแม่ค้าออนไลน์มือโปร ร้าน Camera Craft ขายกล้องและเลนส์มือสอง
ช่วยแต่งแคปชั่น Facebook สำหรับขายสินค้าตามข้อมูลนี้ให้น่าสนใจ กระตุ้นให้อยากซื้อ และดูน่าเชื่อถือ

ข้อมูลสินค้า:
- รุ่น: {brand_model}
- สภาพ: {condition}
- ราคา: {price} บาท
- อุปกรณ์ที่ได้: {accessories}
- จุดเด่น: {highlights}

ข้อกำหนด:
- ใช้ภาษาเป็นกันเอง อ่านง่าย มีอีโมจิประกอบพอประมาณ
- เน้นความคุ้มค่าและสภาพสินค้า
- มี Call to Action ตอนท้าย (เช่น ทักแชทสอบถาม, นัดรับขอนแก่นได้)
- ขอ 2 แบบ: แบบที่ 1 สั้นกระชับ (อ่านปรู๊ดเดียวจบ) และ แบบที่ 2 เล่าเรื่อง (ป้ายยาช่างภาพมือใหม่)"""

    with st.spinner("กำลังปั่นแคปชั่น..."):
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt
        )
        st.success("เสร็จเรียบร้อย! 🎉")
        st.markdown(response.text)