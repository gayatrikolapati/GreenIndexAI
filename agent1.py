import os
from dotenv import load_dotenv
import json
import requests
import re


load_dotenv()
def query_llm(user_input, ndvi_json_data):
    headers = {
    "Authorization": f"Bearer {os.getenv('PERPLEXITY_API_KEY')}",
    "Content-Type": "application/json",
}

    json_context = json.dumps(ndvi_json_data, indent=2)

    prompt = f"""
You are a data assistant. Only use the following NDVI dataset to answer the question. 
Do not guess. Do not use outside knowledge. If information is not in this JSON, say "Data not available".

JSON Data:
{json_context}

Answer this user query: "{user_input}"

Return a list of JSON objects with:
- "state": lowercase state name from JSON
- "month": e.g. "January"
- "year": e.g. 2025

Format:
[
  {{"state": "andhrapradesh", "month": "January", "year": 2025}},
  ...
]
Only output this JSON. No explanation.
"""

    response = requests.post(
        "https://api.perplexity.ai/chat/completions",
        headers=headers,
        json={
            "model": "sonar",
            "messages": [{"role": "user", "content": prompt}],
        },
    )

    if response.status_code != 200:
        raise Exception(f"LLM API call failed. Status code: {response.status_code}, Message: {response.text}")

    content = response.json()
    message = content["choices"][0]["message"]["content"]

    try:
        # Extract only JSON list using regex
        match = re.search(r"\[\s*{.*?}\s*\]", message, re.DOTALL)
        if not match:
            raise ValueError("No valid JSON array found in response.")

        json_string = match.group(0)
        query_list = json.loads(json_string)

        if not isinstance(query_list, list):
            raise ValueError("Extracted JSON is not a list.")

        return query_list

    except Exception as ex:
        raise Exception(f"Error parsing LLM response: {ex}\nRaw output:\n{message}")
