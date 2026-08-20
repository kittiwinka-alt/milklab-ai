import streamlit as st
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import os
import json
import time
import uuid
from google import genai
from dotenv import load_dotenv

# โหลด API Key
load_dotenv()
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# --- ฟังก์ชันบันทึก Trace Log ลงไฟล์ traces.jsonl ---
def log_trace(trace_id, span_name, latency, details):
    trace_data = {
        "trace_id": trace_id,
        "span": span_name,
        "latency_ms": round(latency * 1000, 2),
        "details": details
    }
    with open("traces.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(trace_data, ensure_ascii=False) + "\n")
    return trace_data

# --- โหลดข้อมูล แตก Chunk สร้าง Embedding และ Faiss Index ---
@st.cache_resource
def init_rag_system():
    # 1. เปลี่ยนมาอ่านไฟล์ camera_kb.md แทนของเก่า
    with open("camera_kb.md", "r", encoding="utf-8") as f:
        text = f.read()
    chunks = [c.strip() for c in text.split('\n\n') if c.strip()]
    
    # 2. Encode ด้วย sentence-transformers
    model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
    embeddings = model.encode(chunks)
    
    # 3. สร้าง Faiss index สำหรับค้นหา
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings))
    
    return chunks, model, index

chunks, embed_model, faiss_index = init_rag_system()

# --- ฟังก์ชัน Retrieve Top-k ---
def retrieve_top_k(query, k=3, trace_id=None):
    start_time = time.time()
    
    query_vector = embed_model.encode([query])
    distances, indices = faiss_index.search(np.array(query_vector), k)
    retrieved_chunks = [chunks[i] for i in indices[0]]
    
    latency = time.time() - start_time
    trace_info = log_trace(trace_id, "retrieve_top_k", latency, {"query": query, "top_k": k, "found": retrieved_chunks})
    
    return retrieved_chunks, trace_info

# --- ฟังก์ชัน Generate Answer ---
def generate_answer(query, context_chunks, trace_id=None):
    start_time = time.time()
    
    context_text = "\n".join(context_chunks)
    
    # 🌟 ปรับ Prompt ใหม่ให้บอทพูดจาเพราะขึ้น เป็นกันเอง และดูเป็นมืออาชีพ
    prompt = f"""คุณคือแอดมินผู้เชี่ยวชาญของร้าน Camera Craft ร้านขายกล้องมือสอง
กรุณาตอบคำถามลูกค้าด้วยน้ำเสียงที่สุภาพ เป็นกันเอง กระตือรือร้นที่จะช่วยเหลือ และลงท้ายด้วย "ครับ" หรือ "ค่ะ" เสมอ

กฎสำคัญ: 
1. จงตอบคำถามโดยอิงจาก "ข้อมูลร้านค้า" ด้านล่างนี้เท่านั้น 
2. หากลูกค้าถามหาสินค้าหรือข้อมูลที่ไม่มีในนี้ ห้ามแต่งข้อมูลขึ้นมาเองเด็ดขาด ให้ตอบอย่างสุภาพทำนองว่า "ต้องขออภัยด้วยครับ ตอนนี้ทางร้านยังไม่มีสินค้าแบรนด์นี้/รุ่นนี้นะครับ" หรือ "ขออภัยครับ แอดมินยังไม่มีข้อมูลในส่วนนี้นะครับ"

ข้อมูลร้านค้า:
{context_text}

คำถามจากลูกค้า: {query}"""
    
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt
    )
    
    latency = time.time() - start_time
    trace_info = log_trace(trace_id, "generate_answer", latency, {"prompt": prompt, "answer": response.text})
    
    return response.text, trace_info

# --- สร้าง Chat UI ด้วย Streamlit ---
# เปลี่ยนชื่อ Title ให้เข้ากับแบรนด์ใหม่
st.title("📸 Camera Craft RAG Chatbot")

# เก็บประวัติการแชท
if "messages" not in st.session_state:
    st.session_state.messages = []

# แสดงแชทเก่า
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "trace" in msg:
            with st.expander("ดู Trace Log"):
                st.json(msg["trace"])

# ช่องรับข้อความจากผู้ใช้
if prompt := st.chat_input("สอบถามสเปกกล้องหรือเลนส์ได้เลยครับ..."):
    # 1. แสดงคำถาม
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    current_trace_id = str(uuid.uuid4())

    # 2. ให้ AI คิดและตอบ
    with st.chat_message("assistant"):
        with st.spinner("กำลังค้นหาข้อมูลสเปก..."):
            retrieved_chunks, retrieve_trace = retrieve_top_k(prompt, k=3, trace_id=current_trace_id)
            answer, gen_trace = generate_answer(prompt, retrieved_chunks, trace_id=current_trace_id)
            
            st.markdown(answer)
            
            combined_trace = [retrieve_trace, gen_trace]
            with st.expander("ดู Trace Log"):
                st.json(combined_trace)
            
    # 3. บันทึกคำตอบลง session
    st.session_state.messages.append({"role": "assistant", "content": answer, "trace": combined_trace})