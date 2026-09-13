import os
import imaplib
import email
from email.header import decode_header
from datetime import datetime
import streamlit as st


# =====================================
# Page Settings
# =====================================

st.set_page_config(
    page_title="Yahoo Email Dashboard",
    page_icon="📧",
    layout="wide"
)

st.title("📧 Yahoo 100 Mailbox Dashboard")


# =====================================
# Session State
# =====================================

if "results" not in st.session_state:
    st.session_state.results = {}

if "last_checked" not in st.session_state:
    st.session_state.last_checked = {}


# =====================================
# Decode Email Header
# =====================================

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


# =====================================
# Check Yahoo Mailbox
# =====================================

def check_mailbox(
    email_address,
    password,
    server
):

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

        # Get latest 10 unread emails
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
# Create 100 Yahoo Mailboxes
# =====================================

mailboxes = []


for i in range(1, 101):

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


# =====================================
# Dashboard Controls
# =====================================

st.write("### 📊 Mailbox Monitoring")


# Search box

search = st.text_input(

    "🔍 Search Yahoo mailbox",

    placeholder="Search mailbox number or email address..."

)


# Check all button

check_all = st.button(

    "🔄 Check All 100 Yahoo Mailboxes",

    type="primary",

    use_container_width=True

)


# =====================================
# Check All 100 Mailboxes
# =====================================

if check_all:

    progress = st.progress(0)

    status_text = st.empty()

    for index, mailbox in enumerate(mailboxes):

        name = mailbox["name"]

        status_text.write(

            f"Checking {name} "
            f"({index + 1}/100)..."

        )


        # Missing credentials

        if (
            not mailbox["email"]
            or not mailbox["password"]
        ):

            st.session_state.results[name] = {

                "status": "not_configured",

                "error": "Credentials missing"

            }


        else:

            result, error = check_mailbox(

                mailbox["email"],

                mailbox["password"],

                mailbox["server"]

            )


            if error:

                st.session_state.results[name] = {

                    "status": "failed",

                    "error": error

                }


            else:

                st.session_state.results[name] = {

                    "status": "connected",

                    "unread_count":
                        result["unread_count"],

                    "messages":
                        result["messages"]

                }


            # Save last checked time

            st.session_state.last_checked[name] = (

                datetime.now().strftime(

                    "%Y-%m-%d %H:%M:%S"

                )

            )


        progress.progress(

            (index + 1) / 100

        )


    status_text.success(

        "✅ Finished checking all 100 Yahoo mailboxes."

    )


# =====================================
# Summary
# =====================================

connected = 0

failed = 0

not_configured = 0

total_unread = 0


for result in st.session_state.results.values():

    if result["status"] == "connected":

        connected += 1

        total_unread += result.get(
            "unread_count",
            0
        )


    elif result["status"] == "failed":

        failed += 1


    elif result["status"] == "not_configured":

        not_configured += 1


# =====================================
# Summary Display
# =====================================

st.divider()

st.write("### 📈 Summary")


col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "🟢 Connected",
        connected
    )


with col2:

    st.metric(
        "🔴 Failed",
        failed
    )


with col3:

    st.metric(
        "⚠️ Not Configured",
        not_configured
    )


with col4:

    st.metric(
        "📩 Total Unread",
        total_unread
    )


# =====================================
# Individual Mailboxes
# =====================================

st.divider()

st.write("### 📬 Yahoo Mailboxes")


for mailbox in mailboxes:

    name = mailbox["name"]


    # =================================
    # Search Filter
    # =================================

    if search:

        search_text = (

            name
            + " "
            + str(
                mailbox["email"] or ""
            )

        ).lower()


        if search.lower() not in search_text:

            continue


    # Get previous result

    result = st.session_state.results.get(
        name
    )


    # =================================
    # Mailbox Layout
    # =================================

    col1, col2, col3 = st.columns(
        [3, 3, 1]
    )


    # =================================
    # Mailbox Name
    # =================================

    with col1:

        st.write(
            f"**{name}**"
        )


        if mailbox["email"]:

            st.caption(
                mailbox["email"]
            )

        else:

            st.caption(
                "Not configured"
            )


    # =================================
    # Status
    # =================================

    with col2:

        if not result:

            st.write(
                "⚪ Not checked yet"
            )


        elif result["status"] == "connected":

            st.success(

                f"🟢 Connected | "
                f"Unread: "
                f"{result['unread_count']}"

            )


        elif result["status"] == "failed":

            st.error(
                "🔴 Connection failed"
            )


        else:

            st.warning(
                "⚠️ Not configured"
            )


    # =================================
    # Individual Check
    # =================================

    with col3:

        check_button = st.button(

            "🔄 Check",

            key=f"check_{name}"

        )


        if check_button:


            if (
                not mailbox["email"]
                or not mailbox["password"]
            ):

                st.warning(
                    "Credentials missing."
                )


            else:

                with st.spinner(

                    f"Checking {name}..."

                ):

                    result, error = check_mailbox(

                        mailbox["email"],

                        mailbox["password"],

                        mailbox["server"]

                    )


                if error:

                    st.session_state.results[name] = {

                        "status": "failed",

                        "error": error

                    }


                    st.session_state.last_checked[name] = (

                        datetime.now().strftime(

                            "%Y-%m-%d %H:%M:%S"

                        )

                    )


                    st.error(

                        f"🔴 {error}"

                    )


                else:

                    st.session_state.results[name] = {

                        "status": "connected",

                        "unread_count":
                            result["unread_count"],

                        "messages":
                            result["messages"]

                    }


                    st.session_state.last_checked[name] = (

                        datetime.now().strftime(

                            "%Y-%m-%d %H:%M:%S"

                        )

                    )


                    st.success(
                        "🟢 Connected"
                    )


    # =================================
    # Last Checked
    # =================================

    if name in st.session_state.last_checked:

        st.caption(

            "🕐 Last checked: "
            + st.session_state.last_checked[name]

        )


    # =================================
    # Show Unread Emails
    # =================================

    if (

        result
        and result["status"] == "connected"

    ):

        messages = result.get(
            "messages",
            []
        )


        if messages:

            with st.expander(
                "📩 Latest unread emails"
            ):


                for message in messages:

                    st.write(

                        f"**From:** "
                        f"{message['from']}"

                    )


                    st.write(

                        f"**Subject:** "
                        f"{message['subject']}"

                    )


                    st.write(

                        f"**Date:** "
                        f"{message['date']}"

                    )


                    st.divider()


    # =================================
    # Error Details
    # =================================

    elif (

        result
        and result["status"] == "failed"

    ):

        with st.expander(
            "⚠️ Error details"
        ):

            st.code(

                result.get(
                    "error",
                    "Unknown error"
                )

            )
