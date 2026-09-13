import os
import imaplib
import streamlit as st

st.set_page_config(
    page_title="Yahoo Mail Dashboard",
    page_icon="📧",
    layout="wide"
)

st.title("📧 Yahoo Mail Dashboard")

email = os.getenv("YAHOO_EMAIL")
app_password = os.getenv("YAHOO_APP_PASSWORD")

st.write("Yahoo mailbox connection test")

if st.button("🔄 Check Yahoo Mail"):

    if not email or not app_password:
        st.error("Yahoo credentials are not configured in Render.")
    else:
        try:
            mail = imaplib.IMAP4_SSL("imap.mail.yahoo.com", 993)

            mail.login(email, app_password)

            mail.select("INBOX")

            status, data = mail.search(None, "ALL")

            if status == "OK":
                message_ids = data[0].split()
                total = len(message_ids)

                st.success("✅ Yahoo mailbox connected successfully!")

                col1, col2 = st.columns(2)

                with col1:
                    st.metric("Mailbox", email)

                with col2:
                    st.metric("Total Inbox Messages", total)

            else:
                st.warning("Could not read the Inbox.")

            mail.logout()

        except Exception as e:
            st.error("❌ Yahoo connection failed.")
            st.write(str(e))
