import streamlit as st

st.set_page_config(
    page_title="Email Dashboard",
    page_icon="📧",
    layout="wide"
)

st.title("📧 Email Dashboard")
st.write("Yahoo / AOL Email Monitoring Dashboard")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Yahoo", "Ready")

with col2:
    st.metric("AOL", "Ready")

with col3:
    st.metric("Status", "Online")
