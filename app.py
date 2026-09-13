import streamlit as st

st.set_page_config(
    page_title="Mailbox Dashboard",
    page_icon="📧",
    layout="wide"
)

st.title("📧 Mailbox Dashboard")
st.write("Authorized mailbox monitoring")

st.divider()

st.subheader("Add Test Mailbox")

email = st.text_input(
    "Email address",
    placeholder="example@yahoo.com"
)

provider = st.selectbox(
    "Provider",
    ["Yahoo", "AOL"]
)

if st.button("Add Mailbox"):
    if email:
        st.success(f"{email} added successfully")
        st.info(f"Provider: {provider}")
    else:
        st.warning("Please enter an email address")

st.divider()

st.subheader("Mailbox Status")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Mailboxes", "0")

with col2:
    st.metric("Connected", "0")

with col3:
    st.metric("Errors", "0")
