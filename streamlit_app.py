import streamlit as st
import asyncio
import httpx
from PIL import Image
from io import BytesIO
import json
import time

from agent1 import query_llm
from agent2 import answer_followup_question


st.set_page_config(page_title="GreenIndex AI", layout="wide")

API_URL = "https://greenindexai-nv6x.onrender.com/query"

# ----------------------------
# INIT SESSION STATE
# ----------------------------
if "allow_app" not in st.session_state:
    st.session_state.allow_app = False
if "start_time" not in st.session_state:
    st.session_state.start_time = time.time()
if "history" not in st.session_state:
    st.session_state.history = []

# ----------------------------
# SPLASH SCREEN
# ----------------------------
if not st.session_state.allow_app:
    st.markdown("<h1 style='text-align: center; color: green;'>🌿 GreenIndex AI</h1>", unsafe_allow_html=True)

    st.error("""
    **Notice:** NDVI dataset may contain merged state boundaries or missing regions.
    Provide **month & year** for accurate results.
    Data Range: **Jan 2025 – Jun 2025**
    """, icon="⚠️")

    elapsed = time.time() - st.session_state.start_time

    if elapsed >= 5:
        if st.button("✅ Proceed", use_container_width=True):
            st.session_state.allow_app = True
            st.rerun()
    else:
        st.info(f"Please wait {int(5 - elapsed)} seconds…")
        time.sleep(1)
        st.rerun()

    st.stop()


# ----------------------------
# MAIN HEADER
# ----------------------------
st.markdown("<h1 style='text-align: center; color: green;'>🌿 GreenIndex AI</h1>", unsafe_allow_html=True)

# Load NDVI JSON
with open("ndvi_data.json", "r") as f:
    ndvi_json_data = json.load(f)


# ----------------------------
# ASYNC HELPERS
# ----------------------------

async def async_post(url, payload):
    """Async API call to Flask backend."""
    async with httpx.AsyncClient(timeout=15) as client:
        return await client.post(url, json=payload)


async def async_fetch_image(url):
    """Async fetch NDVI image from URL."""
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(url)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content))
    return None


async def run_query_llm_async(query, data):
    """Run agent1 in thread (if not async)."""
    return await asyncio.to_thread(query_llm, query, data)


async def run_followup_async(question, context):
    """Run agent2 in thread (if not async)."""
    return await asyncio.to_thread(answer_followup_question, question, context)


# ----------------------------
# LAYOUT
# ----------------------------
left, right = st.columns([3, 1])


# ----------------------------------------------------
# RIGHT PANEL — Natural Language Query
# ----------------------------------------------------
with right:
    st.header("NDVI Query (Natural Language)")

    user_input = st.text_input("Ask: e.g., 'NDVI for AP in May 2025'")

    if st.button("Submit Query"):

        async def process_query():
            if not user_input.strip():
                st.warning("Enter a valid query.")
                return

            with st.spinner("Processing using AI..."):

                try:
                    query_list = await run_query_llm_async(user_input, ndvi_json_data)

                    for query in query_list:
                        state = query.get("state", "").lower()
                        month = query.get("month", "").lower()
                        year = int(query.get("year", 0))

                        # Search local JSON
                        entry = next(
                            (row for row in ndvi_json_data if row["state"] == state and row["month"] == month and row["year"] == year),
                            None
                        )

                        if not entry:
                            st.warning(f"No data for {state}, {month} {year}")
                            continue

                        # Async backend API call
                        payload = {"state": state, "month": month, "year": year}
                        res = await async_post(API_URL, payload)

                        img = None
                        if res.status_code == 200:
                            api_data = res.json()
                            if "ndvi_url" in api_data:
                                img = await async_fetch_image(api_data["ndvi_url"])

                        # Store result
                        st.session_state.history.append({"meta": entry, "image": img})

                    st.rerun()

                except Exception as e:
                    st.error(f"❌ AI Error: {e}")

        asyncio.run(process_query())


# ----------------------------------------------------
# LEFT PANEL — Display Results + Follow-up
# ----------------------------------------------------
with left:

    st.subheader("Results")

    for item in st.session_state.history:
        m = item["meta"]

        if m["state"].lower() == "ai response":
            st.markdown(f"**Q:** {item['question']}")
            st.markdown(f"**A:** {item['answer']}")
            st.markdown("---")
            continue

        st.markdown(f"### {m['state'].title()} — {m['month']} {m['year']}")
        if item["image"]:
            st.image(item["image"], width=500)

        st.markdown(
            f"NDVI: **{m['ndvi_value']}**, Temp: **{m['temperature']}°C**,"
            f" Rainfall: **{m['rainfall']}mm**, Soil Moisture: **{m['soilmoisture']}%**"
        )
        st.markdown("---")

    st.divider()
    st.markdown("### Ask a follow-up question")

    user_query = st.text_input("Your question:")

    if st.button("Ask"):

        async def process_followup():
            if not user_query.strip():
                st.warning("Enter a question.")
                return

            # Build context
            context = ""
            for h in st.session_state.history:
                m = h["meta"]
                if m["state"].lower() == "ai response":
                    continue
                context += (f"{m['state']} {m['month']} {m['year']} "
                            f"NDVI={m['ndvi_value']} Temp={m['temperature']} "
                            f"Rain={m['rainfall']} Soil={m['soilmoisture']}\n")

            with st.spinner("AI analyzing context..."):
                answer = await run_followup_async(user_query, context)

                st.session_state.history.append({
                    "meta": {"state": "AI Response"},
                    "image": None,
                    "question": user_query,
                    "answer": answer
                })

                st.rerun()

        asyncio.run(process_followup())
