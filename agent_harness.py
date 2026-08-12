import os
import json
import argparse
import google.generativeai as genai
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# โหลดค่า API Keys จากไฟล์ .env
load_dotenv()
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# ฟังก์ชันสำหรับเขียน Log ลงไฟล์และพิมพ์ออกหน้าจอ
def write_trace(log_text):
    with open("agent_trace.log", "a", encoding="utf-8") as f:
        f.write(log_text + "\n")
    print(log_text)

# --- จำลอง Tools ทั้ง 3 ตัวตามโจทย์ ---
def log_sale(menu, qty, price):
    th_tz = timezone(timedelta(hours=7))
    timestamp = datetime.now(th_tz).strftime('%Y-%m-%dT%H:%M:%S+07')
    return f"log_sale OK: row appended at {timestamp}"

def query_sales(date):
    return f"query_sales OK: found records for {date}"

def send_alert(message):
    return f"send_alert OK: message sent"

def main():
    # 1. รับคำสั่งจาก CLI ผ่าน --cmd
    parser = argparse.ArgumentParser(description="Agent Harness")
    parser.add_argument("--cmd", type=str, required=True, help="คำสั่งภาษาไทย")
    args = parser.parse_args()
    
    user_cmd = args.cmd
    
    # พิมพ์ Trace Log บรรทัดแรก: รับคำสั่งผู้ใช้
    write_trace(f"[USER] {user_cmd}")
    
    # 2. ส่งคำสั่งให้ Gemini วิเคราะห์ (บังคับตอบเป็น JSON)
    prompt = f"""
    คุณคือระบบ AI Agent สำหรับร้านค้า หน้าที่ของคุณคือวิเคราะห์คำสั่งภาษาไทยและเลือกใช้ Tool ที่เหมาะสม
    
    Tool Schema ที่มีให้เลือก:
    1. log_sale: บันทึกยอดขาย (รับ arguments: menu เป็น string, qty เป็น int, price เป็น float)
    2. query_sales: ดูยอดขาย (รับ arguments: date เป็น string รูปแบบ YYYY-MM-DD)
    3. send_alert: ส่งแจ้งเตือน (รับ arguments: message เป็น string)
    
    คำสั่งของผู้ใช้: "{user_cmd}"
    
    จงตอบกลับมาเป็น JSON เท่านั้น โดยใช้รูปแบบนี้ (ไม่ต้องมีเครื่องหมาย markdown ```json):
    {{
        "tool": "ชื่อ tool ที่เลือก",
        "args": {{
            "ชื่อพารามิเตอร์": "ค่าพารามิเตอร์"
        }},
        "reply": "ข้อความตอบกลับผู้ใช้แบบสั้นๆ (เช่น บันทึกแล้วยอด xx บาท)"
    }}
    """
    
    try:
        model = genai.GenerativeModel('gemini-3.5-flash-lite')
        response = model.generate_content(prompt)
        
        # 3. Parse response เป็น Tool call
        raw_text = response.text.replace("```json", "").replace("```", "").strip()
        llm_decision = json.loads(raw_text)
        
        tool_name = llm_decision.get("tool")
        tool_args = llm_decision.get("args", {})
        user_reply = llm_decision.get("reply", "ดำเนินการเรียบร้อย")
        
        # จัดรูปแบบ args ให้ตรงตามสเปก Trace Log
        args_str = ", ".join([f"{k}: {v}" for k, v in tool_args.items()])
        
        # พิมพ์ Trace Log บรรทัดที่สอง: AI คิด
        write_trace(f"[LLM]  tool={tool_name} args={{{args_str}}}")
        
        # 4. เรียกใช้ Tool จริง
        tool_result = ""
        if tool_name == "log_sale":
            tool_result = log_sale(tool_args.get("menu"), int(tool_args.get("qty", 1)), float(tool_args.get("price", 0)))
        elif tool_name == "query_sales":
            tool_result = query_sales(tool_args.get("date"))
        elif tool_name == "send_alert":
            tool_result = send_alert(tool_args.get("message"))
        else:
            tool_result = f"Error: Tool {tool_name} not found"
            
        # พิมพ์ Trace Log บรรทัดที่สาม: ผลลัพธ์จาก Tool
        write_trace(f"[TOOL] {tool_result}")
        
        # พิมพ์ Trace Log บรรทัดสุดท้าย: ตอบกลับผู้ใช้
        write_trace(f"[USER] ←  {user_reply}")
        write_trace("-" * 40) # ขีดเส้นคั่นแต่ละรอบให้ดูง่าย
        
    except Exception as e:
        write_trace(f"[ERROR] เกิดข้อผิดพลาด: {str(e)}")

if __name__ == "__main__":
    main()