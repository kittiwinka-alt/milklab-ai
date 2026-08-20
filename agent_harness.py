import streamlit as st
import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

# โหลด API Key
load_dotenv()
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

st.title("🤖 Camera Craft: AI Agent Harness")
st.write("ทดสอบระบบ Agent วิเคราะห์คำสั่งซื้อร้านกล้อง")

# 1. เปลี่ยน Tool Schema ให้เข้ากับธุรกิจ Camera Craft
camera_tool = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="log_camera_sale",
            description="ใช้บันทึกรายการขายเมื่อลูกค้าตกลงซื้อกล้องหรือเลนส์ และทราบข้อมูลครบถ้วนแล้ว",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "brand": types.Schema(type=types.Type.STRING, description="แบรนด์กล้อง เช่น Panasonic, Sony, เลนส์ Sony"),
                    "model": types.Schema(type=types.Type.STRING, description="รุ่นกล้อง หรือ เลนส์ เช่น Lumix GF8, 50mm f/1.8"),
                    "price": types.Schema(type=types.Type.NUMBER, description="ราคาขายเป็นตัวเลข")
                },
                required=["brand", "model", "price"]
            )
        )
    ]
)

# 2. ปรับ Prompt ให้เข้ากับบริบทใหม่
SYSTEM_INSTRUCTION = """คุณคือ AI Agent รับออเดอร์ของร้าน Camera Craft ร้านขายกล้องมือสอง
หน้าที่ของคุณคือคุยกับลูกค้าและรับออเดอร์ หากลูกค้าตกลงซื้อสินค้า ให้คุณดึงข้อมูล แบรนด์ รุ่น และราคา แล้วเรียกใช้เครื่องมือ log_camera_sale ทันที
หากข้อมูลไม่ชัดเจน ให้สอบถามลูกค้าเพิ่มเติมก่อนทำการบันทึก"""

if "messages" not in st.session_state:
    st.session_state.messages = []

# แสดงประวัติแชท
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# รับข้อความจากผู้ใช้
if prompt := st.chat_input("ลองพิมพ์สั่งซื้อ เช่น 'รับ GF8 ราคา 4500 ครับ'"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Agent กำลังวิเคราะห์..."):
            # ส่งให้ Gemini ประมวลผลพร้อมแนบ Tool ไปด้วย
            response = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    tools=[camera_tool],
                    temperature=0.2
                )
            )
            
            # ตรวจสอบว่า AI ตัดสินใจเรียกใช้ Tool (Function Calling) หรือไม่
            if response.function_calls:
                for fc in response.function_calls:
                    if fc.name == "log_camera_sale":
                        args = fc.args
                        st.success(f"🛠️ Agent ตัดสินใจเรียกใช้ Tool: {fc.name}")
                        st.json({
                            "Action": "ส่งข้อมูลไปหลังบ้าน (Sales Logger)",
                            "Extracted_Data": {
                                "Brand": args.get("brand"),
                                "Model": args.get("model"),
                                "Price": args.get("price")
                            }
                        })
                        reply_text = f"ระบบได้รับออเดอร์ {args.get('brand')} {args.get('model')} ในราคา {args.get('price')} บาท เรียบร้อยแล้วครับ ขอบคุณที่อุดหนุน Camera Craft ครับ! 📸"
                        st.markdown(reply_text)
                        st.session_state.messages.append({"role": "assistant", "content": reply_text})
            else:
                # ถ้าไม่ใช้ Tool ก็ตอบกลับธรรมดา
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})