import os
import re
from groq import Groq
import json

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def query_llm(user_input, ndvi_json_data):

    allowed_states = list({row["state"] for row in ndvi_json_data})
    allowed_months = list({row["month"] for row in ndvi_json_data})
    allowed_years = list({row["year"] for row in ndvi_json_data})

    prompt = f"""
Extract NDVI query details from this text.

User query: "{user_input}"

Allowed states: {allowed_states}
Allowed months: {allowed_months}
Allowed years: {allowed_years}

Return ONLY a JSON list like:
[
  {{"state":"andhrapradesh","month":"May","year":2025}}
]
No explanation. Only JSON.
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
    )

    message = response.choices[0].message.content  # ← FIXED LINE

    match = re.search(r"\[\s*{.*?}\s*\]", message, re.DOTALL)
    if not match:
        raise Exception("No JSON found in model output.\nRaw:\n" + message)

    return json.loads(match.group(0))
