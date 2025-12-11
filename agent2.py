import os
from dotenv import load_dotenv
import requests
import re

load_dotenv()

def answer_followup_question(user_query: str, context: str) -> str:
    if not context.strip():
        return "No data available. Please run a query first so I can use the results to answer your question."

    headers = {
    "Authorization": f"Bearer {os.getenv('PERPLEXITY_API_KEY')}",
    "Content-Type": "application/json",
}


    prompt = f"""
You are a skilled data analyst responding to questions using only the NDVI dataset provided.

Instructions:
- You may reason internally if you need to, but place the final answer **after 'Answer:'**
- The final answer should be a fluent, 3–5 sentence paragraph drawing comparisons and conclusions
- Do not make up values or use external knowledge

NDVI Data:
{context}

User's Question:
{user_query}

Answer:
"""

    try:
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers=headers,
            json={
                "model": "sonar-reasoning",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.5,
            },
        )

        if response.status_code != 200:
            raise Exception(f"LLM request failed: {response.status_code}\n{response.text}")

        full_response = response.json()["choices"][0]["message"]["content"].strip()

        # Extract only the final paragraph after 'Answer:'
        if "Answer:" in full_response:
            answer = full_response.split("Answer:")[-1].strip()
        else:
            # fallback to last paragraph
            paragraphs = re.split(r"\n{2,}", full_response.strip())
            answer = paragraphs[-1].strip()

        return answer

    except Exception as e:
        raise Exception(f"Error during LLM follow-up response: {e}")
