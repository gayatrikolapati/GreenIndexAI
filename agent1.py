import os
import re
from groq import Groq
import json

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ✅ STATE ALIAS MAP (IMPORTANT)
STATE_ALIASES = {
    "andaman nicobar": "Andaman and Nicobar Islands",
    "andaman and nicobar": "Andaman and Nicobar Islands",
    "a&n": "Andaman and Nicobar Islands",
    "a&n islands": "Andaman and Nicobar Islands"
}

def query_llm(user_input, ndvi_json_data):

    # ---------- NORMALIZE USER INPUT ----------
    lower_input = user_input.lower()
    for alias, proper in STATE_ALIASES.items():
        if alias in lower_input:
            user_input = proper
            break

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
  {{"state":"Andaman and Nicobar Islands","month":"May","year":2025}}
]
No explanation. Only JSON.
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
    )

    message = response.choices[0].message.content

    match = re.search(r"\[\s*{.*?}\s*\]", message, re.DOTALL)
    if not match:
        raise Exception("No JSON found in model output.\nRaw:\n" + message)

    parsed = json.loads(match.group(0))

    # ---------- STRICT VALIDATION ----------
    for item in parsed:
        if item["state"] not in allowed_states:
            raise Exception(
                f"State '{item['state']}' not found in NDVI dataset"
            )

    return parsed
