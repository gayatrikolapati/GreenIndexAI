import streamlit as st
import requests
from PIL import Image
from io import BytesIO
import json
from agent1 import query_llm  # ← NEW IMPORT
from agent2 import answer_followup_question
import streamlit as st
import time

st.set_page_config(page_title="GreenIndex AI", layout="wide")

# Initialize state
if "allow_app" not in st.session_state:
    st.session_state.allow_app = False
if "start_time" not in st.session_state:
    st.session_state.start_time = time.time()

# Splash Screen
if not st.session_state.allow_app:
    st.markdown(
        "<h1 style='text-align: center; color: green;'>🌿 GreenIndex AI</h1>",
        unsafe_allow_html=True
    )

    with st.container():
        st.error("""
        **Notice:**  
        This application uses geospatial NDVI data collected from sources like **MODIS**, **Sentinel**, and other public datasets.

        Due to limitations in regional boundaries:
        - States like **Telangana and Andhra Pradesh** may appear merged.
        - Some regions such as **POK** may be missing or distorted.
        - Mention month and year 
    
        **Data Range:** January 2025 – June 2025
        """, icon="⚠️")

    # Calculate time elapsed
    elapsed = time.time() - st.session_state.start_time

    if elapsed >= 5:
        if st.button("✅ Proceed", use_container_width=True):
            st.session_state.allow_app = True
            st.rerun()
    else:
        remaining = int(5 - elapsed)
        st.info(f"Please read the notice. 'Proceed' button will be enabled in {remaining} second(s).")
        time.sleep(1)
        st.rerun()

    # Block app below
    st.stop()


st.set_page_config(page_title="GreenIndex AI", layout="wide")
st.markdown(
        "<h1 style='text-align: center; color: green;'>🌿 GreenIndex AI</h1>",
        unsafe_allow_html=True
    )

# Load fixed NDVI data from JSON
with open("ndvi_data.json", "r") as f:
    ndvi_json_data = json.load(f)

# Initialize session state
if "history" not in st.session_state:
    st.session_state.history = []
if "query_history" not in st.session_state:
    st.session_state.query_history = []

# Layout
left, right = st.columns([3, 1])

# RIGHT PANEL — Natural Language Input
with right:
    st.header("NDVI Data Query (Natural Language)")
    user_input = st.text_input("Ask a query like 'Show NDVI for states starting with A in June 2023'", key="nl_query")

    if st.button("Submit Query"):
        if not user_input.strip():
            st.warning("Please enter a query.")
        else:
            with st.spinner("Processing your query using AI..."):
                try:
                    query_list = query_llm(user_input, ndvi_json_data)  # ← REPLACED
                    for i, query in enumerate(query_list):
                        state = query.get("state", "").strip().lower()
                        month = query.get("month", "").strip()
                        year = int(query.get("year", 0))

                        if not (state and month and year):
                            st.warning(f"⚠️ Skipping incomplete query #{i+1}")
                            continue

                        entry = next(
                            (row for row in ndvi_json_data if row["state"] == state and row["month"] == month and row["year"] == year),
                            None
                        )

                        if not entry:
                            st.warning(f"⚠️ No data for {state}, {month} {year}")
                            continue

                        # Try fetching image from local API
                        img = None
                        try:
                            payload = {
                                "state": state,
                                "month": month,
                                "year": year,
                            }
                            res = requests.post("https://greenindexai.onrender.com/query", json=payload)
                            if res.status_code == 200:
                                api_data = res.json()
                                if "ndvi_url" in api_data:
                                    img_res = requests.get(api_data["ndvi_url"])
                                    if img_res.status_code == 200:
                                        img = Image.open(BytesIO(img_res.content))
                        except:
                            pass

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

                        st.subheader(f"Result {i+1}")
                        summary = (
                            f"The NDVI data for **{state.title()}** in **{month} {year}** shows an NDVI value "
                            f"of **{entry['ndvi_value']}**, with a temperature of **{entry['temperature']}°C**, "
                            f"rainfall of **{entry['rainfall']}mm**, and soil moisture of **{entry['soilmoisture']}%**."
                        )
                        st.markdown(summary)
                        if img:
                            st.image(img, caption="NDVI Image", width=200)

                    st.rerun()

                except Exception as e:
                    st.error(f"❌ AI Agent Error: {e}")

# LEFT PANEL — Display Results and Q&A
with left:
    top_container = st.container()
    bottom_container = st.container()

    with top_container:
        with st.container(height=400, border=False):
            for i, item in enumerate(st.session_state.history):
                m = item["meta"]
                if m["state"].lower() == "ai response":
                    st.markdown(f"**Q: {item['question']}**")
                    st.markdown(f"**A: {item['answer']}**")
                else:
                    st.subheader(f"{m['state'].title()} — {m['month']} {m['year']}")
                    if item["image"]:
                        st.image(item["image"], width=500)
                    summary = (
                        f"In **{m['month']} {m['year']}**, the state of **{m['state'].title()}** experienced "
                        f"an NDVI value of **{m['ndvi_value']}**, a temperature of **{m['temperature']}°C**, "
                        f"rainfall measuring **{m['rainfall']}mm**, and soil moisture level of **{m['soilmoisture']}%**."
                    )
                    st.markdown(summary)
                    st.markdown("---")


    with bottom_container:
        st.divider()
        st.markdown("#### Ask a question based on the above data:")
        user_query = st.text_input("Enter query here", key="query_input")

        if st.button("Ask"):
            if user_query.strip() == "":
                st.warning("Please enter a question.")
            elif not st.session_state.history:
                st.warning("No data available. Please run a query first.")
            else:
                context = ""
                for i, h in enumerate(st.session_state.history):
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

                    st.error(f"❌ AI Agent2 Error: {e}")

