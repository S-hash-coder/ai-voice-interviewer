import uuid
from threading import Lock

llm_lock = Lock()

from resume import read_resume, chunk_text
from rag import build_index, search

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import shutil
import os

from llm import ask_llm
from prompt import HR_PROMPT

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")

sessions = {}

os.makedirs("uploads", exist_ok=True)


# -------------------------
# UPLOAD RESUME
# -------------------------
@app.post("/upload")
async def upload(file: UploadFile = File(...), session_id: str = None):

    if not session_id:
        session_id = str(uuid.uuid4())

    path = f"uploads/{session_id}_{file.filename}"

    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    resume_text = read_resume(path)
    chunks = chunk_text(resume_text)
    build_index(chunks)

    sessions[session_id] = {
        "resume_text": resume_text,
        "chat_history": [
            {"role": "system", "content": HR_PROMPT}
        ]
    }

    return {
        "message": "Resume uploaded successfully",
        "session_id": session_id
    }


# -------------------------
# START INTERVIEW
# -------------------------
@app.get("/start")
def start(session_id: str):

    session = sessions.get(session_id)
    if not session:
        return {"error": "Invalid session"}

    relevant_context = search("introduce yourself resume summary")

    session["chat_history"].append({
        "role": "user",
        "content": f"""
Start interview.

Resume context:
{relevant_context}
"""
    })

    with llm_lock:
        response = ask_llm(session["chat_history"])

    session["chat_history"].append({
        "role": "assistant",
        "content": response
    })

    return {"question": response}


# -------------------------
# CHAT
# -------------------------
@app.get("/chat")
def chat(answer: str, session_id: str):

    session = sessions.get(session_id)
    if not session:
        return {"error": "Invalid session"}

    relevant_context = search(answer)

    session["chat_history"].append({
        "role": "user",
        "content": f"""
Candidate Answer:
{answer}

Resume Context:
{relevant_context}

Ask next question strictly based on resume only.
"""
    })

    with llm_lock:
        response = ask_llm(session["chat_history"])

    session["chat_history"].append({
        "role": "assistant",
        "content": response
    })

    return {"question": response}


# -------------------------
# FRONTEND
# -------------------------
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="static")