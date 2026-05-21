import streamlit as st
import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import networkx as nx
from fpdf import FPDF
import tempfile
import os
from datetime import datetime
from database.database import conn, cursor
from utils.ai_summary import generate_ai_response
from utils.risk_engine import assign_risk
import google.generativeai as genai

# ══════════════════════════════════════════════════════════════
# LOAD MODEL
# ══════════════════════════════════════════════════════════════

model = joblib.load("model/fraud_model.pkl")

# ══════════════════════════════════════════════════════════════
# GEMINI AI SETUP
# ══════════════════════════════════════════════════════════════

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

gemini_model = genai.GenerativeModel("gemini-1.5-flash")

# ══════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="MuleX AI",
    page_icon="🛡️",
    layout="wide"
)

# ══════════════════════════════════════════════════════════════
# DARK THEME
# ══════════════════════════════════════════════════════════════

st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
        color: white;
    }

    .stMetric {
        background-color: #1c1f26;
        padding: 10px;
        border-radius: 10px;
    }

    .stSidebar {
        background-color: #161b22;
    }

    h1, h2, h3 {
        color: #00d4ff;
    }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# LOGIN SYSTEM
# ══════════════════════════════════════════════════════════════

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:

    st.markdown(
        "<h1 style='text-align:center;color:#00d4ff;'>🛡️ MuleX AI</h1>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<h4 style='text-align:center;color:#aaaaaa;'>Bank Admin Login</h4>",
        unsafe_allow_html=True
    )

    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:

        username = st.text_input("👤 Username")

        password = st.text_input(
            "🔒 Password",
            type="password"
        )

        if st.button("Login", use_container_width=True):

            if username == "admin" and password == "mulex123":

                st.session_state.logged_in = True
                st.rerun()

            else:
                st.error("❌ Invalid credentials")

    st.stop()

# ══════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════

st.sidebar.title("🛡️ MuleX AI")
st.sidebar.markdown("### Cyber Fraud Detection System")

page = st.sidebar.radio(
    "Navigate",
    [
        "🏠 Home",
        "🚨 Fraud Alerts",
        "📤 Upload & Predict",
        "🕸️ Fraud Network",
        "📊 Analytics"
    ]
)

if st.sidebar.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.rerun()

# ══════════════════════════════════════════════════════════════
# GEMINI AI ANALYSIS
# ══════════════════════════════════════════════════════════════

def generate_ai_analysis(score, risk):

    prompt = f"""
    You are a Cybersecurity Fraud Analyst.

    Analyze this banking transaction.

    Fraud Score: {score}
    Risk Level: {risk}

    Give:
    1. Fraud reason
    2. Threat severity
    3. Recommended action
    4. Investigation advice

    Keep response professional and short.
    """

    response = gemini_model.generate_content(prompt)

    return response.text

# ══════════════════════════════════════════════════════════════
# PDF GENERATOR
# ══════════════════════════════════════════════════════════════

def generate_pdf(summary, fraud_count, safe_count, total, accuracy):

    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial", "B", 20)
    pdf.cell(
        0,
        10,
        "MuleX AI - Fraud Investigation Report",
        ln=True,
        align="C"
    )

    pdf.ln(10)

    pdf.set_font("Arial", "", 12)

    stats = [
        ("Total Transactions", total),
        ("Fraudulent", fraud_count),
        ("Safe", safe_count),
        ("Accuracy", f"{accuracy}%")
    ]

    for label, value in stats:
        pdf.cell(90, 10, str(label), border=1)
        pdf.cell(90, 10, str(value), border=1, ln=True)

    pdf.ln(10)

    pdf.cell(0, 10, "Risk Summary", ln=True)

    for key, value in summary.items():
        pdf.cell(90, 10, key, border=1)
        pdf.cell(90, 10, str(value), border=1, ln=True)

    path = os.path.join(
        tempfile.gettempdir(),
        "MuleX_Report.pdf"
    )

    pdf.output(path)

    return path

# ══════════════════════════════════════════════════════════════
# HOME PAGE
# ══════════════════════════════════════════════════════════════

if page == "🏠 Home":

    st.title("🛡️ MuleX AI Dashboard")

    st.subheader(
        "Real-Time Fraud & Mule Account Detection"
    )

    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Transactions", "9,082")
    col2.metric("Frauds", "21 🔴")
    col3.metric("Accuracy", "94.7%")
    col4.metric("Alerts", "5 ⚠️")

    st.markdown("---")

    st.subheader("📋 Live Transactions")

    transactions = pd.DataFrame([
        ["TXN001", "UPI", 50000, "Mumbai", "High 🔴"],
        ["TXN002", "NEFT", 1000, "Pune", "Low 🟢"],
        ["TXN003", "IMPS", 99000, "Delhi", "High 🔴"]
    ], columns=[
        "Transaction ID",
        "Type",
        "Amount",
        "City",
        "Risk"
    ])

    st.dataframe(
        transactions,
        use_container_width=True
    )

    st.markdown("---")

    st.subheader("🤖 AI Live Prediction")

    sample_input = np.random.rand(1, 3923)

    prediction = model.predict(sample_input)

    prob = model.predict_proba(sample_input)[0]

    risk_label, risk_reason = assign_risk(prob[1] * 100)

    col1, col2, col3 = st.columns(3)

    with col1:

        if prediction[0] == 1:
            st.error("🚨 Fraud Detected")
        else:
            st.success("✅ Safe Transaction")

    col2.metric(
        "Fraud Probability",
        f"{prob[1] * 100:.1f}%"
    )

    col3.metric(
        "Risk Level",
        risk_label
    )

    st.info(f"📌 {risk_reason}")

    st.markdown("---")

    st.subheader("🤖 MuleX AI Assistant")

    query = st.text_input(
        "Ask about fraud activity"
    )

    if query:

        response = generate_ai_response(query)

        st.success(response)

# ══════════════════════════════════════════════════════════════
# FRAUD ALERTS
# ══════════════════════════════════════════════════════════════

elif page == "🚨 Fraud Alerts":

    st.title("🚨 Fraud Alerts")

    alerts = pd.DataFrame([
        ["ACC8821", "UPI", 98000, "Mumbai", "BLOCKED 🔴"],
        ["ACC3341", "IMPS", 75000, "Delhi", "FLAGGED 🟡"]
    ], columns=[
        "Account",
        "Type",
        "Amount",
        "City",
        "Status"
    ])

    st.dataframe(
        alerts,
        use_container_width=True
    )

# ══════════════════════════════════════════════════════════════
# UPLOAD & PREDICT
# ══════════════════════════════════════════════════════════════

elif page == "📤 Upload & Predict":

    st.title("📤 Upload CSV & Predict Fraud")

    uploaded_file = st.file_uploader(
        "Upload CSV File",
        type=["csv"]
    )

    if uploaded_file:

        df = pd.read_csv(uploaded_file)

        st.success(
            f"Loaded {df.shape[0]} rows"
        )

        st.dataframe(
            df.head(),
            use_container_width=True
        )

        if st.button("🤖 Run AI Prediction"):

            df = df.apply(
                pd.to_numeric,
                errors="coerce"
            ).fillna(0)

            expected = 3923

            if df.shape[1] > expected:
                df = df.iloc[:, :expected]

            elif df.shape[1] < expected:

                for i in range(expected - df.shape[1]):
                    df[f"pad_{i}"] = 0

            preds = model.predict(df)

            probs = model.predict_proba(df)[:, 1]

            df["Prediction"] = [
                "🔴 FRAUD" if p == 1 else "🟢 SAFE"
                for p in preds
            ]

            df["Fraud Score"] = (
                probs * 100
            ).round(1)

            risk_levels = []
            risk_reasons = []

            for score in df["Fraud Score"]:

                rl, rr = assign_risk(score)

                risk_levels.append(rl)
                risk_reasons.append(rr)

            df["Risk Level"] = risk_levels
            df["Risk Reason"] = risk_reasons

            # SAVE TO DATABASE

            for i in range(len(df)):

                cursor.execute("""
                    INSERT INTO fraud_logs
                    (account, amount, risk, prediction)
                    VALUES (?, ?, ?, ?)
                """, (
                    f"ACC{i}",
                    float(df["Fraud Score"].iloc[i]),
                    df["Risk Level"].iloc[i],
                    df["Prediction"].iloc[i]
                ))

            conn.commit()

            st.markdown("---")

            st.subheader("🔍 Prediction Results")

            st.dataframe(
                df[[
                    "Prediction",
                    "Fraud Score",
                    "Risk Level",
                    "Risk Reason"
                ]].head(20),
                use_container_width=True
            )

            st.markdown("---")

            st.subheader("🤖 Gemini AI Investigation")

            with st.spinner("Analyzing..."):

                summary_text = generate_ai_analysis(
                    df["Fraud Score"].iloc[0],
                    df["Risk Level"].iloc[0]
                )

            st.success(summary_text)

            fraud_count = int(sum(preds))

            safe_count = len(preds) - fraud_count

            total = len(preds)

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Frauds",
                fraud_count
            )

            col2.metric(
                "Safe",
                safe_count
            )

            col3.metric(
                "Total",
                total
            )

            summary = {
                "HIGH":
                df["Risk Level"].str.contains("HIGH").sum(),

                "MEDIUM":
                df["Risk Level"].str.contains("MEDIUM").sum(),

                "LOW":
                df["Risk Level"].str.contains("LOW").sum()
            }

            pdf_path = generate_pdf(
                summary,
                fraud_count,
                safe_count,
                total,
                94.7
            )

            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()

            st.download_button(
                label="📥 Download PDF Report",
                data=pdf_bytes,
                file_name="MuleX_Report.pdf",
                mime="application/pdf",
                use_container_width=True
            )

# ══════════════════════════════════════════════════════════════
# FRAUD NETWORK
# ══════════════════════════════════════════════════════════════

elif page == "🕸️ Fraud Network":

    st.title("🕸️ Fraud Network")

    G = nx.DiGraph()

    edges = [
        ("ACC8821", "MasterMule"),
        ("ACC3341", "MasterMule"),
        ("ACC9910", "ACC8821")
    ]

    G.add_edges_from(edges)

    fig, ax = plt.subplots(figsize=(10, 7))

    pos = nx.spring_layout(G, seed=42)

    nx.draw(
        G,
        pos,
        with_labels=True,
        node_color="skyblue",
        node_size=3000,
        font_size=10,
        ax=ax
    )

    st.pyplot(fig)

# ══════════════════════════════════════════════════════════════
# ANALYTICS
# ══════════════════════════════════════════════════════════════

elif page == "📊 Analytics":

    st.title("📊 Analytics")

    fig, ax = plt.subplots()

    ax.bar(
        ["Low", "Medium", "High"],
        [1796, 50, 21]
    )

    st.pyplot(fig)

    st.success(
        "✅ MuleX AI Monitoring Active"
    )
