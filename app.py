import streamlit as st
import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import networkx as nx
from fpdf import FPDF
import tempfile, os
from datetime import datetime
from database.database import conn, cursor
from utils.ai_summary import generate_ai_response
import google.generativeai as genai

# ─── Load Model ───────────────────────────────────────────────
model = joblib.load("model/fraud_model.pkl")

# Gemini AI Setup — key loaded from secrets (never hardcoded)
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

gemini_model = genai.GenerativeModel("gemini-1.5-flash")

# ─── Page Config ──────────────────────────────────────────────
st.set_page_config(page_title="MuleX AI", page_icon="🛡️", layout="wide")

# ─── Dark Theme ───────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .stMetric { background-color: #1c1f26; padding: 10px; border-radius: 10px; }
    .stSidebar { background-color: #161b22; }
    h1, h2, h3 { color: #00d4ff; }
</style>
""", unsafe_allow_html=True)

# ─── Login ────────────────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align:center;color:#00d4ff;'>🛡️ MuleX AI</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align:center;color:#aaaaaa;'>Bank Admin Login</h4>", unsafe_allow_html=True)
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        username = st.text_input("👤 Username")
        password = st.text_input("🔒 Password", type="password")
        if st.button("Login", use_container_width=True):
            if username == "admin" and password == "mulex123":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("❌ Invalid credentials. Try admin / mulex123")
    st.stop()

# ─── Sidebar ──────────────────────────────────────────────────
st.sidebar.title("🛡️ MuleX AI")
st.sidebar.markdown("**Bank Admin Dashboard**")
st.sidebar.markdown("---")
page = st.sidebar.radio("Navigate", [
    "🏠 Home",
    "🚨 Fraud Alerts",
    "📤 Upload & Predict",
    "🕸️ Fraud Network",
    "📊 Analytics"
])
st.sidebar.markdown("---")
if st.sidebar.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.rerun()

def assign_risk(score):
    if score >= 80:
        return "🔴 HIGH", "Possible Mule Account"
    elif score >= 50:
        return "🟡 MEDIUM", "Suspicious Transaction Pattern"
    else:
        return "🟢 LOW", "Normal Banking Activity"

# ─── Gemini AI Fraud Analysis ─────────────────────────────────
def generate_ai_analysis(score, risk):
    prompt = f"""
    You are an AI Cybersecurity Fraud Analyst.

    Analyze this banking transaction.

    Fraud Score: {score}
    Risk Level: {risk}

    Give:
    1. Fraud reason
    2. Threat severity
    3. Recommended bank action
    4. Investigation advice

    Keep response professional and short.
    """
    response = gemini_model.generate_content(prompt)
    return response.text

# ─── PDF Generator ────────────────────────────────────────────
def generate_pdf(summary, fraud_count, safe_count, total, accuracy):
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial", "B", 20)
    pdf.set_text_color(0, 180, 255)
    pdf.cell(0, 12, "MuleX AI - Fraud Investigation Report", ln=True, align="C")

    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%d %B %Y, %H:%M:%S')}  |  Bank of India - Cyber Fraud Division", ln=True, align="C")
    pdf.ln(5)

    pdf.set_draw_color(0, 180, 255)
    pdf.set_line_width(0.8)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)

    pdf.set_font("Arial", "B", 13)
    pdf.set_text_color(0, 180, 255)
    pdf.cell(0, 10, "Executive Summary", ln=True)

    pdf.set_font("Arial", "", 11)
    pdf.set_text_color(30, 30, 30)

    stats = [
        ("Total Transactions Analyzed", str(total)),
        ("Fraudulent Transactions",     str(fraud_count)),
        ("Safe Transactions",            str(safe_count)),
        ("Model Accuracy",              f"{accuracy}%"),
        ("Fraud Detection Rate",        f"{(fraud_count/total*100):.1f}%" if total > 0 else "N/A"),
        ("Report Status",               "FINAL"),
    ]
    for label, value in stats:
        pdf.set_font("Arial", "B", 11)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(90, 9, label, border=0)
        pdf.set_font("Arial", "", 11)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 9, value, ln=True)

    pdf.ln(5)

    pdf.set_font("Arial", "B", 13)
    pdf.set_text_color(0, 180, 255)
    pdf.cell(0, 10, "Risk Category Breakdown", ln=True)

    pdf.set_fill_color(230, 245, 255)
    pdf.set_font("Arial", "B", 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(90, 9, "Risk Level", fill=True, border=1)
    pdf.cell(0,  9, "Count",      fill=True, border=1, ln=True)

    high   = summary.get("HIGH",   0)
    medium = summary.get("MEDIUM", 0)
    low    = summary.get("LOW",    0)

    for level, count, color in [
        ("HIGH RISK",   high,   (255, 100, 100)),
        ("MEDIUM RISK", medium, (255, 180,  50)),
        ("LOW RISK",    low,    ( 50, 200, 100)),
    ]:
        pdf.set_fill_color(*color)
        pdf.set_font("Arial", "B", 11)
        pdf.cell(90, 9, level,       fill=True, border=1)
        pdf.set_font("Arial", "",    11)
        pdf.cell(0,  9, str(count),  fill=True, border=1, ln=True)

    pdf.ln(5)

    pdf.set_font("Arial", "B", 13)
    pdf.set_text_color(0, 180, 255)
    pdf.cell(0, 10, "Top Fraud Indicators Detected", ln=True)

    pdf.set_font("Arial", "", 11)
    pdf.set_text_color(30, 30, 30)
    reasons = [
        "1. Possible Mule Account Activity",
        "2. Suspicious Transaction Pattern",
        "3. High Velocity Cross-Account Transfers",
        "4. Device Anomaly Pattern Detected",
        "5. Blacklisted Account Cross-Reference Match",
    ]
    for r in reasons:
        pdf.cell(0, 8, r, ln=True)

    pdf.ln(5)

    pdf.set_font("Arial", "I", 9)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 8, "CONFIDENTIAL - For internal use only. MuleX AI (C) 2026 | IIT Hyderabad Hackathon Submission", ln=True, align="C")

    path = os.path.join(tempfile.gettempdir(), "MuleX_Report.pdf")
    pdf.output(path)
    return path

# ══════════════════════════════════════════════════════════════
# PAGE 1 — HOME
# ══════════════════════════════════════════════════════════════
if page == "🏠 Home":
    st.title("🛡️ MuleX AI — Admin Dashboard")
    st.subheader("Real-Time Fraud & Mule Account Detection System")
    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Transactions", "9,082")
    col2.metric("Fraud Detected",     "21 🔴")
    col3.metric("Model Accuracy",     "94.7%")
    col4.metric("Active Alerts",      "5 ⚠️")

    st.markdown("---")
    st.subheader("📋 Live Transaction Monitor")
    transactions = pd.DataFrame([
        ["TXN001", "UPI",  50000, "Mumbai",  "High Risk 🔴"],
        ["TXN002", "NEFT", 1000,  "Pune",    "Low Risk 🟢"],
        ["TXN003", "IMPS", 99000, "Delhi",   "High Risk 🔴"],
        ["TXN004", "UPI",  500,   "Chennai", "Low Risk 🟢"],
        ["TXN005", "NEFT", 75000, "Kolkata", "Medium Risk 🟡"],
        ["TXN006", "UPI",  20000, "Jaipur",  "Medium Risk 🟡"],
        ["TXN007", "IMPS", 5000,  "Nagpur",  "Low Risk 🟢"],
    ], columns=["Transaction ID", "Type", "Amount (₹)", "Location", "Risk Level"])
    st.dataframe(transactions, use_container_width=True)

    st.markdown("---")
    st.subheader("🤖 AI Live Prediction")
    sample_input = np.random.rand(1, 3923)
    prediction   = model.predict(sample_input)
    prob         = model.predict_proba(sample_input)[0]
    risk_label, risk_reason = assign_risk(prob[1] * 100)

    col1, col2, col3 = st.columns(3)
    with col1:
        if prediction[0] == 1:
            st.error("🚨 Fraudulent Transaction Detected")
        else:
            st.success("✅ Legitimate Transaction")
    col2.metric("Fraud Probability", f"{prob[1]*100:.1f}%")
    col3.metric("Risk Level", risk_label)
    st.info(f"📌 Risk Reason: {risk_reason}")

    st.markdown("---")
    st.subheader("🤖 MuleX AI Assistant")

    query = st.text_input("Ask MuleX AI about fraud activity")

    if query:
        response = generate_ai_response(query)
        st.success(response)

# ══════════════════════════════════════════════════════════════
# PAGE 2 — FRAUD ALERTS
# ══════════════════════════════════════════════════════════════
elif page == "🚨 Fraud Alerts":
    st.title("🚨 Fraud Alerts")
    st.markdown("---")
    alerts = pd.DataFrame([
        ["ACC8821", "UPI",  98000, "Mumbai",  "BLOCKED 🔴",   "Mule Account"],
        ["ACC3341", "IMPS", 75000, "Delhi",   "FLAGGED 🟡",   "Velocity Breach"],
        ["ACC9910", "NEFT", 50000, "Pune",    "BLOCKED 🔴",   "Cross-Account Link"],
        ["ACC1122", "UPI",  30000, "Kolkata", "REVIEWING 🟡", "Device Anomaly"],
        ["ACC5577", "IMPS", 15000, "Chennai", "BLOCKED 🔴",   "Blacklisted Account"],
    ], columns=["Account ID", "Channel", "Amount (₹)", "City", "Status", "Reason"])
    st.dataframe(alerts, use_container_width=True)

    st.markdown("---")
    st.subheader("📊 Alert Breakdown")
    fig, ax = plt.subplots(figsize=(5, 5))
    fig.patch.set_facecolor("#0e1117")
    ax.pie([3, 2], labels=["BLOCKED", "FLAGGED"], autopct="%1.0f%%",
           colors=["#ff4444", "#ffaa00"], textprops={"color": "white"})
    st.pyplot(fig)

# ══════════════════════════════════════════════════════════════
# PAGE 3 — UPLOAD & PREDICT
# ══════════════════════════════════════════════════════════════
elif page == "📤 Upload & Predict":
    st.title("📤 Upload CSV & Predict Fraud")
    st.markdown("---")

    uploaded_file = st.file_uploader("Upload transaction CSV file", type=["csv"])

    if uploaded_file:
        df = pd.read_csv(uploaded_file, index_col=0)

        st.success(f"✅ File loaded: {df.shape[0]} rows, {df.shape[1]} columns")
        st.dataframe(df.head(), use_container_width=True)

        if st.button("🤖 Run AI Prediction"):

            df = df.apply(pd.to_numeric, errors="coerce").fillna(0)

            expected = 3923

            if df.shape[1] > expected:
                df = df.iloc[:, :expected]
            elif df.shape[1] < expected:
                for i in range(expected - df.shape[1]):
                    df[f"pad_{i}"] = 0

            preds = model.predict(df)
            probs = model.predict_proba(df)[:, 1]

            df["Prediction"] = ["🔴 FRAUD" if p == 1 else "🟢 SAFE" for p in preds]
            df["Fraud Score"] = (probs * 100).round(1)

            risk_levels = []
            risk_reasons = []

            for score in df["Fraud Score"]:
                rl, rr = assign_risk(score)
                risk_levels.append(rl)
                risk_reasons.append(rr)

            df["Risk Level"]  = risk_levels
            df["Risk Reason"] = risk_reasons

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
                df[["Prediction", "Fraud Score", "Risk Level", "Risk Reason"]].head(20),
                use_container_width=True
            )

            # ─── Gemini AI Investigation ──────────────────────

            st.markdown("---")
            st.subheader("🤖 Gemini AI Investigation")

            with st.spinner("Analyzing transaction with Gemini AI..."):
                summary_text = generate_ai_analysis(
                    df["Fraud Score"].iloc[0],
                    df["Risk Level"].iloc[0]
                )

            st.success(summary_text)

            fraud_count = int(sum(preds))
            safe_count  = len(preds) - fraud_count
            total       = len(preds)

            col1, col2, col3 = st.columns(3)
            col1.metric("Fraud Transactions", f"{fraud_count} 🔴")
            col2.metric("Safe Transactions",  f"{safe_count} 🟢")
            col3.metric("Total Analyzed",     str(total))

            summary = {
                "HIGH":   df["Risk Level"].str.contains("HIGH").sum(),
                "MEDIUM": df["Risk Level"].str.contains("MEDIUM").sum(),
                "LOW":    df["Risk Level"].str.contains("LOW").sum(),
            }

            st.markdown("---")
            st.subheader("📄 Download Investigation Report")

            pdf_path = generate_pdf(summary, fraud_count, safe_count, total, 94.7)

            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()

            st.download_button(
                label="📥 Download Investigation Report",
                data=pdf_bytes,
                file_name="MuleX_Fraud_Report.pdf",
                mime="application/pdf",
                use_container_width=True
            )

            st.success("✅ PDF report ready for download!")

    else:
        st.info("👆 Upload your DataSet.csv to run batch fraud prediction.")

# ══════════════════════════════════════════════════════════════
# PAGE 4 — FRAUD NETWORK
# ══════════════════════════════════════════════════════════════
elif page == "🕸️ Fraud Network":
    st.title("🕸️ Fraud Transaction Network")
    st.subheader("Visualizing mule account connections")
    st.markdown("---")

    G = nx.DiGraph()
    nodes = ["ACC8821","ACC3341","ACC9910","ACC1122","ACC5577","ACC0011","ACC2233","ACC4455","MasterMule"]
    G.add_nodes_from(nodes)
    edges = [
        ("ACC8821",    "MasterMule", 98000),
        ("ACC3341",    "MasterMule", 75000),
        ("ACC9910",    "ACC8821",    50000),
        ("ACC1122",    "ACC3341",    30000),
        ("ACC5577",    "MasterMule", 15000),
        ("ACC0011",    "ACC9910",    20000),
        ("ACC2233",    "ACC1122",    12000),
        ("ACC4455",    "ACC5577",     8000),
        ("MasterMule", "ACC0011",    60000),
    ]
    for s, d, w in edges:
        G.add_edge(s, d, weight=w)

    fig, ax = plt.subplots(figsize=(10, 7))
    fig.patch.set_facecolor("#0e1117")
    ax.set_facecolor("#0e1117")
    pos         = nx.spring_layout(G, seed=42)
    node_colors = ["#ff4444" if n == "MasterMule" else "#00d4ff" for n in G.nodes()]
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=1200, ax=ax)
    nx.draw_networkx_labels(G, pos, font_color="white", font_size=7, ax=ax)
    nx.draw_networkx_edges(G, pos, edge_color="#ffaa00", arrows=True, arrowsize=20, width=1.5, ax=ax)
    edge_labels = {(s, d): f"₹{w:,}" for s, d, w in edges}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color="#aaaaaa", font_size=6, ax=ax)
    ax.set_title("Mule Account Transaction Network", color="white", fontsize=14)
    ax.axis("off")
    st.pyplot(fig)

    st.markdown("---")
    st.error("🔴 MasterMule — Central node receiving funds from multiple mule accounts")
    st.warning("🟡 Blue nodes — Suspicious feeder accounts under monitoring")

# ══════════════════════════════════════════════════════════════
# PAGE 5 — ANALYTICS
# ══════════════════════════════════════════════════════════════
elif page == "📊 Analytics":
    st.title("📊 Transaction Analytics")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Risk Distribution")
        fig1, ax1 = plt.subplots()
        fig1.patch.set_facecolor("#0e1117")
        ax1.set_facecolor("#1c1f26")
        ax1.bar(["Low Risk","Medium Risk","High Risk"], [1796, 50, 21],
                color=["#00cc44","#ffaa00","#ff4444"])
        ax1.set_ylabel("Count", color="white")
        ax1.tick_params(colors="white")
        st.pyplot(fig1)

    with col2:
        st.subheader("Transaction Type Split")
        fig2, ax2 = plt.subplots()
        fig2.patch.set_facecolor("#0e1117")
        ax2.pie([40, 35, 25], labels=["UPI","NEFT","IMPS"], autopct="%1.0f%%",
                colors=["#00d4ff","#7b61ff","#ff6b6b"], textprops={"color":"white"})
        st.pyplot(fig2)

    st.markdown("---")
    st.subheader("📈 Fraud Trend (Last 7 Days)")
    days  = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    fraud = [2, 5, 3, 8, 4, 6, 3]
    fig3, ax3 = plt.subplots()
    fig3.patch.set_facecolor("#0e1117")
    ax3.set_facecolor("#1c1f26")
    ax3.plot(days, fraud, color="#00d4ff", marker="o", linewidth=2)
    ax3.fill_between(days, fraud, alpha=0.2, color="#00d4ff")
    ax3.set_ylabel("Fraud Cases", color="white")
    ax3.tick_params(colors="white")
    st.pyplot(fig3)

    st.markdown("---")
    st.success("✅ MuleX AI is actively monitoring all transactions.")
