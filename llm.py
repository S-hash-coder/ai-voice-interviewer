from google import genai
import time
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

#client = genai.Client(api_key="GEMINI_API_KEY")

def ask_llm(messages, retries=3):
    for _ in range(retries):
        try:
            prompt = ""

            for m in messages:
                role = m.get("role", "")
                content = m.get("content", "")
                prompt += f"{role}: {content}\n"

            prompt += "\nHR Interviewer:"

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            return response.text

        except Exception as e:
            if "503" in str(e):
                time.sleep(2)
                continue
            return f"LLM ERROR: {str(e)}"

    return "LLM busy. Please try again."