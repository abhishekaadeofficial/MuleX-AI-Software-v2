import streamlit as st
import pandas as pd
import sqlite3

st.set_page_config(
    page_title="MuleX Admin Panel",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ MuleX AI — Admin Monitoring Panel")

# Connect database
conn = sqlite3.connect("mulex.db")
df = pd.read_sql("SELECT * FROM fraud_logs", conn)

# Metrics
st.markdown("## 📊 Live Fraud Statistics")

col1, col2, col3 = st.columns(3)

col1.metric("Total Cases", len(df))

high_risk = len(df[df["risk"].str.contains("HIGH", na=False)])

col2.metric("High Risk Cases", high_risk)

fraud_cases = len(df[df["prediction"].str.contains("FRAUD", na=False)])

col3.metric("Fraud Detected", fraud_cases)

st.markdown("---")

# Live table
st.subheader("🚨 Live Fraud Logs")

st.dataframe(
    df,
    use_container_width=True
)

st.markdown("---")

# Risk filter
risk_filter = st.selectbox(
    "Filter by Risk",
    ["ALL", "HIGH", "MEDIUM", "LOW"]
)

if risk_filter != "ALL":

    filtered_df = df[
        df["risk"].str.contains(risk_filter, na=False)
    ]

    st.subheader(f"Filtered Results — {risk_filter}")

    st.dataframe(
        filtered_df,
        use_container_width=True
    )

# Auto refresh
st.markdown("---")

st.info("🔄 Real-time monitoring active")
