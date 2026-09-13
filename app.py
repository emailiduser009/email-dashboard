import streamlit as st

st.set_page_config(
    page_title="Mailbox Dashboard",
    page_icon="📧",
    layout="wide"
)

st.title("📧 Mailbox Dashboard")
st.write("Mailbox monitoring dashboard")

st.divider()

# Test mailbox
accounts = [
    {
        "name": "Account 01",
        "provider": "Yahoo",
        "status": "Ready",
        "mail_count": 0
    }
]

st.subheader("Mailboxes")

for account in accounts:
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.write("**Account**")
        st.write(account["name"])

    with col2:
        st.write("**Provider**")
        st.write(account["provider"])

    with col3:
        st.write("**Status**")
        st.success(account["status"])

    with col4:
        st.write("**Mail count**")
        st.write(account["mail_count"])

st.divider()

if st.button("🔄 Check Mailboxes"):
    st.info("Mailbox checking module will be connected next.")
