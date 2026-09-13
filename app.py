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

st.title("📧 Email Dashboard")


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
# Mailbox configuration
# =====================================

mailboxes = [

    {
        "name": "Yahoo Mailbox 1",
        "email": os.getenv("YAHOO_EMAIL"),
        "password": os.getenv("YAHOO_APP_PASSWORD"),
        "server": "imap.mail.yahoo.com"
    },

    {
        "name": "Yahoo Mailbox 2",
        "email": os.getenv("YAHOO_EMAIL_2"),
        "password": os.getenv("YAHOO_APP_PASSWORD_2"),
        "server": "imap.mail.yahoo.com"
    },

    {
        "name": "AOL Mailbox 1",
        "email": os.getenv("AOL_EMAIL"),
        "password": os.getenv("AOL_APP_PASSWORD"),
        "server": "imap.aol.com"
    }

]


# =====================================
# Dashboard
# =====================================

for mailbox in mailboxes:

    st.divider()

    col1, col2 = st.columns([3, 1])

    with col1:

        st.subheader(
            f"📬 {mailbox['name']}"
        )

        st.write(
            f"**Email:** {mailbox['email']}"
        )

    with col2:

        check_button = st.button(
            "🔄 Check",
            key=mailbox["name"]
        )

    if check_button:

        if (
            not mailbox["email"]
            or not mailbox["password"]
        ):

            st.error(
                "❌ Mailbox credentials are missing."
            )

        else:

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
                        "No unread emails."
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
