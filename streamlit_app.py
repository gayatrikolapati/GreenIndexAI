import streamlit as st
import requests
from PIL import Image
from io import BytesIO
import json
import time

from agent1 import query_llm
from agent2 import answer_followup_question

# ------------------------------------
# CONFIG
# ------------------------------------
st.set_page_config(page_title="GreenIndex AI", layout="wide")

API_URL = "https://greenindexai-nv6x.onrender.com/query"

# Initialize session state
if "allow_app" not in st.session_state:
    st.session_state.allow_app = False
if "start_time" not in st.session_state:
    st.session_state.start_time = time.time()
if "history" not in st.session_state:
    st.session_state.history = []
if "query_history" not in st.session_state:
    st.session_state.query_history = []

# ------------------------------------
# SPLASH SCREEN
# ------------------------------------
if not st.session_state.allow_app:
    st.markdown(
        "<h1 style='text-align: center; color: green;'>🌿 GreenIndex AI</h1>",
        unsafe_allow_html=True
    )

    st.error("""
    **Notice:**  
    This application uses geospatial NDVI data collected from MODIS, Sentinel,
    and other public datasets.

    ⚠️ The map may show merged Telangana–Andhra boundaries  
    ⚠️ Some regions like POK may be missing  
    ⚠️ Provide **month & year** for accurate results  

    **Data Range:** January 2025 – June 2025
    """, icon="⚠️")

    elapsed = time.time() - st.session_state.start_time

    if elapsed >= 5:
        if st.button("✅ Proceed", use_container_width=True):
            st.session_state.allow_app = True
            st.rerun()
    else:
        st.info(f"Please read the notice. Proceed button enabled in {int(5 - elapsed)} seconds...")
        time.sleep(1)
        st.rerun()

    st.stop()

# ------------------------------------
# MAIN UI
# ------------------------------------
st.markdown(
    "<h1 style='text-align: center; color: green;'>🌿 GreenIndex AI</h1>",
    unsafe_allow_html=True
)

# Load static NDVI JSON
with open("ndvi_data.json", "r") as f:
    ndvi_json_data = json.load(f)

# Layout: LEFT = results, RIGHT = query
left, right = st.columns([3, 1])

# ----------------------------------------------------------
# RIGHT PANEL → Natural Language Query
# ----------------------------------------------------------
with right:
    st.header("NDVI Data Query (Natural Language)")

    user_input = st.text_input(
        "Ask a query (e.g., 'Show NDVI for states starting with A in June 2023')",
        key="nl_query"
    )

    if st.button("Submit Query"):
        if not user_input.strip():
            st.warning("Please enter a query.")
        else:
            with st.spinner("Processing your query using AI..."):
                try:
                    query_list = query_llm(user_input, ndvi_json_data)

                    for i, query in enumerate(query_list):
                        state = query.get("state", "").strip().lower()
                        month = query.get("month", "").strip()
                        year = int(query.get("year", 0))

                        if not (state and month and year):
                            st.warning(f"⚠️ Skipping incomplete query #{i+1}")
                            continue

                        # Lookup in local JSON
                        entry = next(
                            (row for row in ndvi_json_data
                             if row["state"] == state and row["month"] == month and row["year"] == year),
                            None
                        )

                        if not entry:
                            st.warning(f"⚠️ No data for {state}, {month} {year}")
                            continue

                        # Fetch image via API
                        img = None
                        try:
                            payload = {"state": state, "month": month, "year": year}
                            res = requests.post(API_URL, json=payload)

                            if res.status_code == 200:
                                api_data = res.json()
                                if "ndvi_url" in api_data:
                                    img_res = requests.get(api_data["ndvi_url"])
                                    if img_res.status_code == 200:
                                        img = Image.open(BytesIO(img_res.content))
                        except:
                            pass

                        # Add to history
                        record = {
                            "state": state,
                            "month": month,
                            "year": year,
                            "ndvi_value": entry["ndvi_value"],
                            "temperature": entry["temperature"],
                            "rainfall": entry["rainfall"],
                            "soilmoisture": entry["soilmoisture"],
                        }

                        st.session_state.history.append({"meta": record, "image": img})

                        # Display summary
                        st.subheader(f"Result {i+1}")
                        st.markdown(
                            f"The NDVI data for **{state.title()}** in **{month} {year}** shows an NDVI value "
                            f"of **{entry['ndvi_value']}**, temperature **{entry['temperature']}°C**, "
                            f"rainfall **{entry['rainfall']}mm**, and soil moisture **{entry['soilmoisture']}%**."
                        )
                        if img:
                            st.image(img, caption="NDVI Image", width=200)

                    st.rerun()

                except Exception as e:
                    st.error(f"❌ AI Agent Error: {e}")

# ----------------------------------------------------------
# LEFT PANEL → Results + Follow-up Q&A
# ----------------------------------------------------------
with left:

    # Show history of results
    with st.container(height=400, border=False):
        for i, item in enumerate(st.session_state.history):
            m = item["meta"]

            if m["state"].lower() == "ai response":
                st.markdown(f"**Q:** {item['question']}")
                st.markdown(f"**A:** {item['answer']}")
                st.markdown("---")
                continue

            st.subheader(f"{m['state'].title()} — {m['month']} {m['year']}")
            if item["image"]:
                st.image(item["image"], width=500)

            st.markdown(
                f"In **{m['month']} {m['year']}**, the state of **{m['state'].title()}** recorded NDVI **{m['ndvi_value']}**, "
                f"temperature **{m['temperature']}°C**, rainfall **{m['rainfall']}mm**, soil moisture **{m['soilmoisture']}%**."
            )
            st.markdown("---")

    # Follow-up question section
    st.divider()
    st.markdown("#### Ask a question based on the above data:")

    user_query = st.text_input("Enter your question", key="query_input")

    if st.button("Ask"):
        if user_query.strip() == "":
            st.warning("Please enter a question.")
        elif not st.session_state.history:
            st.warning("No data available. Submit a query first.")
        else:
            # Build context
            context = ""
            for h in st.session_state.history:
                m = h["meta"]
                if m["state"].lower() == "ai response":
                    continue
                context += (
                    f"State={m['state']}, Month={m['month']}, Year={m['year']}, "
                    f"NDVI={m['ndvi_value']}, Temperature={m['temperature']}°C, "
                    f"Rainfall={m['rainfall']}mm, Soil Moisture={m['soilmoisture']}%\n"
                )

            try:
                with st.spinner("Generating analytical insight..."):
                    answer = answer_followup_question(user_query, context)

                    st.session_state.history.append({
                        "meta": {
                            "state": "AI Response",
                            "month": "",
                            "year": "",
                            "ndvi_value": "",
                            "temperature": "",
                            "rainfall": "",
                            "soilmoisture": ""
                        },
                        "image": None,
                        "question": user_query,
                        "answer": answer
                    })

                    st.rerun()

            except Exception as e:
                st.error(f"❌ AI Agent Error: {e}")
