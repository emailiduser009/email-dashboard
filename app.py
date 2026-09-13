import os
import imaplib
import email
from email.header import decode_header
import streamlit as st


st.set_page_config(
    page_title="Email Dashboard",
    page_icon="📧",
    layout="wide"
)

st.title("📧 50 Mailbox Dashboard")


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


def check_mailbox(email_address, password, server):

    try:
        mail = imaplib.IMAP4_SSL(
            server,
            993
        )

        mail.login(
            email_address,
            password
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

        unread_count = len(unread_ids)

        # Latest 10 unread emails
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

            messages.append({
                "from": decode_text(
                    msg.get("From")
                ),
                "subject": decode_text(
                    msg.get("Subject")
                ),
                "date": msg.get("Date")
            })

        mail.logout()

        return {
            "unread_count": unread_count,
            "messages": messages
        }, None

    except Exception as e:

        return None, str(e)


# =====================================
# Create 50 Mailboxes
# =====================================

mailboxes = []


# -------------------------------------
# Yahoo 1 - 25
# -------------------------------------

for i in range(1, 26):

    mailboxes.append({
        "name": f"Yahoo Mailbox {i}",
        "email": os.getenv(
            f"YAHOO_EMAIL_{i}"
        ),
        "password": os.getenv(
            f"YAHOO_APP_PASSWORD_{i}"
        ),
        "server": "imap.mail.yahoo.com"
    })


# -------------------------------------
# AOL 1 - 25
# -------------------------------------

for i in range(1, 26):

    mailboxes.append({
        "name": f"AOL Mailbox {i}",
        "email": os.getenv(
            f"AOL_EMAIL_{i}"
        ),
        "password": os.getenv(
            f"AOL_APP_PASSWORD_{i}"
        ),
        "server": "imap.aol.com"
    })


# =====================================
# Dashboard
# =====================================

for mailbox in mailboxes:

    st.divider()

    col1, col2 = st.columns([4, 1])

    with col1:

        st.subheader(
            f"📬 {mailbox['name']}"
        )

        if mailbox["email"]:
            st.write(
                f"**Email:** {mailbox['email']}"
            )
        else:
            st.write(
                "**Email:** Not configured"
            )

    with col2:

        check_button = st.button(
            "🔄 Check",
            key=f"check_{mailbox['name']}"
        )

    if check_button:

        if (
            not mailbox["email"]
            or not mailbox["password"]
        ):

            st.warning(
                "⚠️ This mailbox is not configured yet."
            )

        else:

            with st.spinner(
                "Checking mailbox..."
            ):

                result, error = check_mailbox(
                    mailbox["email"],
                    mailbox["password"],
                    mailbox["server"]
                )

            if error:

                st.error(
                    f"🔴 Connection failed: {error}"
                )

            else:

                st.success(
                    "🟢 Connected successfully!"
                )

                st.metric(
                    "Unread Messages",
                    result["unread_count"]
                )

                if not result["messages"]:

                    st.info(
                        "📭 No unread emails."
                    )

                else:

                    st.write(
                        "### 📩 Latest Unread Emails"
                    )

                    for message in result["messages"]:

                        with st.container(
                            border=True
                        ):

                            st.write(
                                f"**From:** {message['from']}"
                            )

                            st.write(
                                f"**Subject:** {message['subject']}"
                            )

                            st.write(
                                f"**Date:** {message['date']}"
                            )
