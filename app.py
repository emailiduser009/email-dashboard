import os
import imaplib
import email
from email.header import decode_header
import streamlit as st

st.set_page_config(
    page_title="Yahoo Mail Dashboard",
    page_icon="📧",
    layout="wide"
)

st.title("📧 Yahoo Mail Dashboard")

yahoo_email = os.getenv("YAHOO_EMAIL")
app_password = os.getenv("YAHOO_APP_PASSWORD")


def decode_text(value):
    if not value:
        return ""

    result = ""

    for text, encoding in decode_header(value):
        if isinstance(text, bytes):
            result += text.decode(
                encoding or "utf-8",
                errors="replace"
            )
        else:
            result += text

    return result


if st.button("🔄 Check Unread Mail"):

    if not yahoo_email or not app_password:
        st.error("Yahoo credentials are not configured.")
        st.stop()

    try:
        mail = imaplib.IMAP4_SSL(
            "imap.mail.yahoo.com",
            993
        )

        mail.login(
            yahoo_email,
            app_password
        )

        mail.select("INBOX")

        # Find unread messages
        status, data = mail.search(
            None,
            "UNSEEN"
        )

        if status != "OK":
            st.error("Could not check unread messages.")
            mail.logout()
            st.stop()

        unread_ids = data[0].split()

        st.success("✅ Yahoo mailbox connected!")

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "Unread Messages",
                len(unread_ids)
            )

        with col2:
            st.metric(
                "Mailbox",
                yahoo_email
            )

        st.subheader("📩 Unread Emails")

        if not unread_ids:
            st.info("No unread emails found.")

        else:
            # Show newest first
            unread_ids = unread_ids[-10:]
            unread_ids.reverse()

            for msg_id in unread_ids:

                status, msg_data = mail.fetch(
                    msg_id,
                    "(RFC822)"
                )

                if status != "OK":
                    continue

                raw_email = msg_data[0][1]

                msg = email.message_from_bytes(
                    raw_email
                )

                sender = decode_text(
                    msg.get("From")
                )

                subject = decode_text(
                    msg.get("Subject")
                )

                date = msg.get("Date")

                with st.container(border=True):

                    st.write(
                        "**From:**",
                        sender
                    )

                    st.write(
                        "**Subject:**",
                        subject
                    )

                    st.write(
                        "**Date:**",
                        date
                    )

        mail.logout()

    except Exception as e:

        st.error(
            "❌ Yahoo mailbox check failed."
        )

        st.write(str(e))
