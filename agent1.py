import os
import json
import re
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def query_llm(user_input, ndvi_json_data):

    json_context = json.dumps(ndvi_json_data, indent=2)

    prompt = f"""
You are a data assistant. Only use the NDVI dataset below.
Do NOT guess. If information is missing, say "Data not available".

NDVI JSON:
{json_context}

User query: "{user_input}"

Return ONLY a JSON list like:
[
  {{"state": "andhrapradesh", "month": "May", "year": 2025}}
]
"""

    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}],
    )

    message = response.choices[0].message["content"]

    match = re.search(r"\[\s*{.*?}\s*\]", message, re.DOTALL)
    if not match:
        raise Exception("No JSON found in model output.\nRaw output:\n" + message)

    return json.loads(match.group(0))
