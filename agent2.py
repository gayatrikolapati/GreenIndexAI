import os
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def answer_followup_question(user_query: str, context: str) -> str:

    if not context.strip():
        return "No data available. Please run a query first."

    prompt = f"""
You are an NDVI analysis assistant.
Use ONLY the following context:

{context}

User question: {user_query}

Write a clear, short analytical answer (3–5 sentences).
"""

    response = client.chat.completions.create(
        model="llama-3.1-70b-versatile",   # FIXED LINE
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
    )

    return response.choices[0].message["content"].strip()
