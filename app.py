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
    # บันทึกลงไฟล์ (Append)
    with open("traces.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(trace_data, ensure_ascii=False) + "\n")
    return trace_data

# --- ข้อ 1-3: โหลดข้อมูล แตก Chunk สร้าง Embedding และ Faiss Index ---
@st.cache_resource
def init_rag_system():
    # 1. โหลด menu_kb.md และ Split เป็น chunk (หั่นตามย่อหน้า)
    with open("menu_kb.md", "r", encoding="utf-8") as f:
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

# --- ข้อ 5: ฟังก์ชัน Retrieve Top-k ---
def retrieve_top_k(query, k=3, trace_id=None):
    start_time = time.time()
    
    query_vector = embed_model.encode([query])
    distances, indices = faiss_index.search(np.array(query_vector), k)
    retrieved_chunks = [chunks[i] for i in indices[0]]
    
    latency = time.time() - start_time
    # เก็บ Log ของ Span: retrieve_top_k
    trace_info = log_trace(trace_id, "retrieve_top_k", latency, {"query": query, "top_k": k, "found": retrieved_chunks})
    
    return retrieved_chunks, trace_info

# --- ข้อ 6: ฟังก์ชัน Generate Answer พร้อม Span ---
def generate_answer(query, context_chunks, trace_id=None):
    start_time = time.time()
    
    context_text = "\n".join(context_chunks)
    prompt = f"คุณคือแชทบอทร้าน MilkLab จงตอบคำถามโดยอิงจากข้อมูลต่อไปนี้เท่านั้น:\n\n{context_text}\n\nคำถาม: {query}"
    
    # ใช้ gemini-3.5-flash-lite ตัวพิมพ์เล็กทั้งหมด และต้องไม่มีเว้นวรรค
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt
    )
    
    latency = time.time() - start_time
    trace_info = log_trace(trace_id, "generate_answer", latency, {"prompt": prompt, "answer": response.text})
    
    return response.text, trace_info

# --- ข้อ 4: สร้าง Chat UI ด้วย Streamlit ---
st.title("🥤 MilkLab RAG Chatbot")

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
if prompt := st.chat_input("พิมพ์คำถามของคุณที่นี่..."):
    # 1. แสดงคำถาม
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # สร้าง trace_id เดียวกันสำหรับลูปนี้
    current_trace_id = str(uuid.uuid4())

    # 2. ให้ AI คิดและตอบ
    with st.chat_message("assistant"):
        with st.spinner("กำลังค้นหาข้อมูล..."):
            # ดึงข้อมูล Top-k
            retrieved_chunks, retrieve_trace = retrieve_top_k(prompt, k=3, trace_id=current_trace_id)
            
            # สร้างคำตอบ
            answer, gen_trace = generate_answer(prompt, retrieved_chunks, trace_id=current_trace_id)
            
            st.markdown(answer)
            
            # นำ Trace มาแสดงใน Expander ใต้คำตอบ
            combined_trace = [retrieve_trace, gen_trace]
            with st.expander("ดู Trace Log"):
                st.json(combined_trace)
            
    # 3. บันทึกคำตอบลง session
    st.session_state.messages.append({"role": "assistant", "content": answer, "trace": combined_trace})