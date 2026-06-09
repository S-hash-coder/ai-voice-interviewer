from resume import read_resume, chunk_text
from rag import build_index, search

from fastapi import FastAPI, UploadFile, File
import shutil
import os

from llm import ask_llm
from resume import read_resume
from prompt import HR_PROMPT

app = FastAPI()

chat_history = [{"role": "system", "content": HR_PROMPT}]
resume_text = ""

os.makedirs("uploads", exist_ok=True)


# 1. Upload resume
@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    global resume_text

    path = f"uploads/{file.filename}"

    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    resume_text = read_resume(path)

    chunks = chunk_text(resume_text)
    build_index(chunks)

    return {"message": "Resume uploaded and indexed successfully"}


# 2. Start interview
@app.get("/start")
def start():
    global chat_history

    relevant_context = search("start interview introduction resume")

    chat_history.append({
    "role": "user",
    "content": f"""
You are an expert HR interviewer.

Use the resume context below to ask intelligent interview questions.

RESUME CONTEXT:
----------------
{relevant_context}
----------------

Now respond naturally like a real interviewer.
"""
})

    response = ask_llm(chat_history)

    chat_history.append({"role": "assistant", "content": response})

    return {"question": response}


# 3. Continue chat (SAFE FIX ONLY)
from pydantic import BaseModel

class ChatRequest(BaseModel):
    answer: str


@app.post("/chat")
def chat(answer: str):

    relevant_context = search(answer)

    chat_history.append({
    "role": "user",
    "content": f"""
Candidate Answer:
{answer}

Resume Context:
----------------
{relevant_context}
----------------

Act as a professional HR interviewer.

Use both the candidate's answer and the resume context to ask the next interview question.
"""
})

    response = ask_llm(chat_history)

    chat_history.append({"role": "assistant", "content": response})

    MAX_HISTORY = 8

    if len(chat_history) > MAX_HISTORY:
        chat_history[:] = [chat_history[0]] + chat_history[-7:]

    return {"question": response}