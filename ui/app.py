import os
import sys
import json
import requests
import streamlit as st

# Ensure project root is on sys.path so we can import the 'ui' package
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from ui.examples import EXAMPLES

API_URL = "http://localhost:8000/analyze"

st.set_page_config(page_title="AML Alert Triage Copilot", layout="wide")
st.title("AML Alert Triage Copilot")

st.write(
    "This prototype simulates an AI-assisted investigator copilot that triages AML transaction alerts. "
    "It produces a structured risk summary and explanation for a human investigator to review. "
    "The AI supports analysts, but final decisions always remain with humans."
)

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Alert JSON")

    example_name = st.selectbox(
        "Load example alert",
        options=list(EXAMPLES.keys()),
        index=0
    )
    default_alert = EXAMPLES[example_name]

    alert_text = st.text_area(
        "Edit the alert or paste another example",
        value=json.dumps(default_alert, indent=2),
        height=400,
    )
    analyze_button = st.button("Analyze alert")

with col_right:
    st.subheader("AI Risk Summary & Human Decision")
    if analyze_button:
        try:
            alert = json.loads(alert_text)
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON: {e}")
        else:
            with st.spinner("Analyzing alert..."):
                try:
                    resp = requests.post(API_URL, json=alert)
                except Exception as ex:
                    st.error(f"Failed to call backend API: {ex}")
                else:
                    if resp.status_code != 200:
                        st.error(f"API error: {resp.status_code} {resp.text}")
                    else:
                        analysis = resp.json()
                        st.write("### AI-generated risk summary (for human review, not a final decision)")
                        st.json(analysis)

                        st.write("### Human-in-the-loop decision")
                        final_decision = st.selectbox(
                            "Final investigator decision (chosen by human, not AI):",
                            options=[
                                "Close as false positive",
                                "Investigate further",
                                "Escalate to senior investigator"
                            ],
                            index=1
                        )

                        investigator_note = st.text_area(
                            "Investigator note (edit the AI explanation or add your own)",
                            value=analysis.get("explanation", ""),
                            height=150
                        )

                        if st.button("Save (simulated) decision"):
                            st.success(
                                "Decision saved (simulated). In production, this would be stored in an investigations system."
                            )
                            st.write("**Stored decision (preview):**")
                            record = {
                                "alert_id": analysis.get("alert_id"),
                                "ai_risk_bucket": analysis.get("risk_bucket"),
                                "ai_recommended_action": analysis.get("recommended_next_action"),
                                "human_final_decision": final_decision,
                                "investigator_note": investigator_note,
                            }
                            st.json(record)
    else:
        st.info("Click 'Analyze alert' to see the AI-generated triage and explanation.")

st.markdown("""
---
**Note:** This prototype uses synthetic data and is designed for human-in-the-loop AML investigations only.  
It is not intended to make automated production decisions or replace regulatory model validation.
""")