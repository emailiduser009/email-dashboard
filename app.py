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


def check_mailbox(email_address, app_password):

    try:
        mail = imaplib.IMAP4_SSL(
            "imap.mail.yahoo.com",
            993
        )

        mail.login(
            email_address,
            app_password
        )

        mail.select("INBOX")

        status, data = mail.search(
            None,
            "UNSEEN"
        )

        if status != "OK":
            mail.logout()
            return None, "Could not read Inbox."

        unread_ids = data[0].split()

        unread_ids = unread_ids[-10:]
        unread_ids.reverse()

        messages = []

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

            messages.append({
                "from": sender,
                "subject": subject,
                "date": date
            })

        mail.logout()

        return messages, None

    except Exception as e:
        return None, str(e)


# -------------------------------
# Mailbox 1
# -------------------------------

email_1 = os.getenv("YAHOO_EMAIL")
password_1 = os.getenv("YAHOO_APP_PASSWORD")


# -------------------------------
# Mailbox 2
# -------------------------------

email_2 = os.getenv("YAHOO_EMAIL_2")
password_2 = os.getenv("YAHOO_APP_PASSWORD_2")


if st.button("🔄 Check All Mailboxes"):

    mailboxes = [
        ("Mailbox 1", email_1, password_1),
        ("Mailbox 2", email_2, password_2)
    ]

    for mailbox_name, email_address, password in mailboxes:

        st.divider()

        st.header(f"📬 {mailbox_name}")

        if not email_address or not password:

            st.warning(
                f"{mailbox_name} credentials are not configured."
            )

            continue

        st.write(
            f"**Email:** {email_address}"
        )

        messages, error = check_mailbox(
            email_address,
            password
        )

        if error:

            st.error(
                f"❌ Connection failed: {error}"
            )

        else:

            st.success(
                "✅ Mailbox connected successfully!"
            )

            st.metric(
                "Unread Messages",
                len(messages)
            )

            if not messages:

                st.info(
                    "No unread emails."
                )

            else:

                for message in messages:

                    with st.container(border=True):

                        st.write(
                            "**From:**",
                            message["from"]
                        )

                        st.write(
                            "**Subject:**",
                            message["subject"]
                        )

                        st.write(
                            "**Date:**",
                            message["date"]
                        )
