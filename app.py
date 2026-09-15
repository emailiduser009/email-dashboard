import os
import imaplib
import email
from email.header import decode_header
from datetime import datetime
import streamlit as st


# ============================================================
# SETTINGS
# ============================================================

IMAP_SERVER = "imap.mail.yahoo.com"
IMAP_PORT = 993

MAX_MESSAGES_PER_ACCOUNT = 2000


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Yahoo Mailbox Dashboard",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ============================================================
# CUSTOM STYLE
# ============================================================

st.markdown(
    """
    <style>

    /* ========================================================
       GLOBAL
       ======================================================== */

    .stApp {
        background: #f5f7fb;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1450px;
    }


    /* ========================================================
       LOGIN
       ======================================================== */

    .login-wrapper {
        max-width: 430px;
        margin: 7vh auto 0 auto;
        padding: 32px 36px 28px 36px;
        background: white;
        border-radius: 18px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 10px 35px rgba(0, 0, 0, 0.08);
        text-align: center;
    }

    .login-icon {
        font-size: 42px;
        margin-bottom: 8px;
    }

    .login-title {
        font-size: 27px;
        font-weight: 700;
        color: #111827;
        line-height: 1.2;
    }

    .login-subtitle {
        margin-top: 8px;
        color: #6b7280;
        font-size: 14px;
    }


    /* ========================================================
       INPUTS
       ======================================================== */

    .stTextInput > div > div > input {
        border-radius: 10px;
        min-height: 44px;
    }


    /* ========================================================
       BUTTONS
       ======================================================== */

    .stButton > button {
        border-radius: 10px;
        min-height: 42px;
        font-weight: 600;
        border: 1px solid #e5e7eb;
    }


    /* ========================================================
       HEADINGS
       ======================================================== */

    h1 {
        font-weight: 750;
        letter-spacing: -0.5px;
    }

    h2 {
        font-weight: 700;
    }

    h3 {
        font-weight: 650;
    }


    /* ========================================================
       METRICS
       ======================================================== */

    [data-testid="stMetric"] {
        background: white;
        padding: 17px 18px;
        border-radius: 14px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 3px 12px rgba(0, 0, 0, 0.04);
    }

    [data-testid="stMetricLabel"] {
        font-size: 13px;
    }

    [data-testid="stMetricValue"] {
        font-weight: 700;
    }


    /* ========================================================
       MAILBOX CARDS
       ======================================================== */

    [data-testid="stVerticalBlockBorderWrapper"] {
        background: white;
        border-radius: 15px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 3px 12px rgba(0, 0, 0, 0.035);
    }


    /* ========================================================
       EXPANDERS
       ======================================================== */

    .streamlit-expanderHeader {
        font-weight: 600;
    }


    /* ========================================================
       CAPTION
       ======================================================== */

    .small-muted {
        color: #6b7280;
        font-size: 13px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# LOGIN PAGE
# ============================================================

def login_page():

    # Top spacing
    st.markdown(
        "<div style='height:4vh'></div>",
        unsafe_allow_html=True
    )

    # Login card
    st.markdown(
        """
        <div class="login-wrapper">

            <div class="login-icon">📧</div>

            <div class="login-title">
                Yahoo Mailbox Dashboard
            </div>

            <div class="login-subtitle">
                Sign in to continue
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    # Center form
    left, center, right = st.columns([1.2, 1.6, 1.2])

    with center:

        st.markdown(
            "<div style='height:18px'></div>",
            unsafe_allow_html=True
        )

        username = st.text_input(
            "Username",
            placeholder="Enter username",
            key="login_username"
        )

        password = st.text_input(
            "Password",
            placeholder="Enter password",
            type="password",
            key="login_password"
        )

        st.markdown(
            "<div style='height:5px'></div>",
            unsafe_allow_html=True
        )

        if st.button(
            "🔐 LOGIN",
            type="primary",
            use_container_width=True
        ):

            correct_username = os.getenv(
                "DASHBOARD_USERNAME",
                ""
            )

            correct_password = os.getenv(
                "DASHBOARD_PASSWORD",
                ""
            )

            if (
                username == correct_username
                and password == correct_password
                and correct_username
                and correct_password
            ):

                st.session_state.logged_in = True
                st.rerun()

            else:

                st.error(
                    "❌ Invalid username or password"
                )


# ============================================================
# LOGIN STATE
# ============================================================

if "logged_in" not in st.session_state:

    st.session_state.logged_in = False


# ============================================================
# SHOW LOGIN
# ============================================================

if not st.session_state.logged_in:

    login_page()

    st.stop()


# ============================================================
# SESSION STATE
# ============================================================

if "results" not in st.session_state:

    st.session_state.results = {}


if "processing" not in st.session_state:

    st.session_state.processing = False


if "stop_requested" not in st.session_state:

    st.session_state.stop_requested = False


if "last_checked" not in st.session_state:

    st.session_state.last_checked = None


# ============================================================
# LOGOUT
# ============================================================

logout_left, logout_right = st.columns([8, 1])

with logout_right:

    if st.button(
        "🚪 Logout",
        use_container_width=True
    ):

        st.session_state.logged_in = False

        st.session_state.processing = False

        st.session_state.stop_requested = True

        st.session_state.results = {}

        st.session_state.last_checked = None

        st.rerun()


# ============================================================
# DECODE TEXT
# ============================================================

def decode_text(value):

    if not value:
        return ""

    try:

        decoded = decode_header(value)

        output = ""

        for part, encoding in decoded:

            if isinstance(part, bytes):

                try:

                    output += part.decode(
                        encoding or "utf-8",
                        errors="replace"
                    )

                except Exception:

                    output += part.decode(
                        "utf-8",
                        errors="replace"
                    )

            else:

                output += str(part)

        return output

    except Exception:

        return str(value)


# ============================================================
# CHECK ONE MAILBOX
# ============================================================

def check_mailbox(
    email_address,
    password
):

    result = {

        "email": email_address,

        "status": "Starting",

        "total_unread": 0,

        "selected": 0,

        "processed": 0,

        "seen": 0,

        "failed": 0,

        "messages": [],

        "errors": [],

        "started": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),

        "finished": "",

        "stopped": False
    }

    mail = None

    try:

        # ====================================================
        # CONNECT
        # ====================================================

        result["status"] = "Connecting..."

        mail = imaplib.IMAP4_SSL(
            IMAP_SERVER,
            IMAP_PORT
        )


        # ====================================================
        # LOGIN
        # ====================================================

        result["status"] = "Logging in..."

        mail.login(
            email_address,
            password
        )


        # ====================================================
        # OPEN INBOX
        # ====================================================

        result["status"] = "Opening INBOX..."

        status, data = mail.select(
            "INBOX",
            readonly=False
        )

        if status != "OK":

            raise Exception(
                "Could not open INBOX"
            )


        # ====================================================
        # FIND UNREAD
        # ====================================================

        result["status"] = "Finding unread mails..."

        status, data = mail.uid(
            "search",
            None,
            "UNSEEN"
        )

        if status != "OK":

            raise Exception(
                "Unread mail search failed"
            )

        unread_ids = data[0].split()

        result["total_unread"] = len(
            unread_ids
        )


        # ====================================================
        # MAX 2000
        # ====================================================

        selected_ids = unread_ids[
            :MAX_MESSAGES_PER_ACCOUNT
        ]

        result["selected"] = len(
            selected_ids
        )


        # ====================================================
        # NO UNREAD
        # ====================================================

        if not selected_ids:

            result["status"] = "No unread mails"

            result["finished"] = (
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )

            try:

                mail.logout()

            except Exception:

                pass

            return result


        # ====================================================
        # PROCESS EACH MAIL
        # ====================================================

        for index, uid in enumerate(
            selected_ids,
            start=1
        ):

            # ------------------------------------------------
            # STOP CHECK
            # ------------------------------------------------

            if st.session_state.stop_requested:

                result["status"] = (
                    "Stopped by user"
                )

                result["stopped"] = True

                break


            try:

                # --------------------------------------------
                # FETCH FULL MESSAGE
                # --------------------------------------------

                result["status"] = (
                    f"Fetching {index}/"
                    f"{result['selected']}"
                )

                fetch_status, msg_data = mail.uid(
                    "fetch",
                    uid,
                    "(RFC822)"
                )

                if fetch_status != "OK":

                    result["failed"] += 1

                    result["errors"].append(
                        f"UID "
                        f"{uid.decode(errors='replace')}: "
                        f"Fetch failed"
                    )

                    continue


                raw_email = None

                for response in msg_data:

                    if isinstance(
                        response,
                        tuple
                    ):

                        raw_email = response[1]

                        break


                if not raw_email:

                    result["failed"] += 1

                    result["errors"].append(
                        f"UID "
                        f"{uid.decode(errors='replace')}: "
                        f"Empty message"
                    )

                    continue


                # --------------------------------------------
                # PARSE EMAIL
                # --------------------------------------------

                msg = email.message_from_bytes(
                    raw_email
                )


                from_address = decode_text(
                    msg.get("From", "")
                )


                subject = decode_text(
                    msg.get("Subject", "")
                )


                date_value = decode_text(
                    msg.get("Date", "")
                )


                message_id = decode_text(
                    msg.get("Message-ID", "")
                )


                # --------------------------------------------
                # SAVE MESSAGE INFORMATION
                # --------------------------------------------

                result["messages"].append(
                    {
                        "number": index,

                        "uid": uid.decode(
                            errors="replace"
                        ),

                        "from": from_address,

                        "subject": subject,

                        "date": date_value,

                        "message_id": message_id
                    }
                )


                result["processed"] += 1


                # --------------------------------------------
                # MARK AS SEEN
                # --------------------------------------------

                result["status"] = (
                    f"Marking Seen {index}/"
                    f"{result['selected']}"
                )


                seen_status, _ = mail.uid(
                    "store",
                    uid,
                    "+FLAGS",
                    "(\\Seen)"
                )


                if seen_status == "OK":

                    result["seen"] += 1

                else:

                    result["errors"].append(
                        f"UID "
                        f"{uid.decode(errors='replace')}: "
                        f"Could not mark Seen"
                    )


            except Exception as message_error:

                result["failed"] += 1

                result["errors"].append(
                    f"UID "
                    f"{uid.decode(errors='replace')}: "
                    f"{str(message_error)}"
                )


        # ====================================================
        # FINAL STATUS
        # ====================================================

        if result["stopped"]:

            result["status"] = (
                "Stopped by user"
            )

        else:

            result["status"] = (
                "Completed"
            )


        result["finished"] = (
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )


        # ====================================================
        # CLOSE
        # ====================================================

        try:

            mail.close()

        except Exception:

            pass


        try:

            mail.logout()

        except Exception:

            pass


        return result


    except Exception as account_error:

        result["status"] = "Failed"

        result["errors"].append(
            str(account_error)
        )

        result["finished"] = (
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )


        try:

            if mail:

                mail.logout()

        except Exception:

            pass


        return result


# ============================================================
# LOAD YAHOO ACCOUNTS
# ============================================================

mailboxes = []


for i in range(1, 101):

    email_address = os.getenv(
        f"YAHOO_EMAIL_{i}"
    )

    password = os.getenv(
        f"YAHOO_APP_PASSWORD_{i}"
    )


    if email_address and password:

        mailboxes.append(
            {
                "number": i,

                "email": email_address,

                "password": password
            }
        )


# ============================================================
# HEADER
# ============================================================

st.title(
    "📧 Yahoo Mailbox Dashboard"
)

st.caption(
    "Process up to 2,000 unread messages per mailbox"
)


# ============================================================
# TOP METRICS
# ============================================================

c1, c2, c3 = st.columns(3)


with c1:

    st.metric(
        "Configured Accounts",
        len(mailboxes)
    )


with c2:

    st.metric(
        "Max / Account",
        f"{MAX_MESSAGES_PER_ACCOUNT:,}"
    )


with c3:

    st.metric(
        "Maximum Total",
        f"{len(mailboxes) * MAX_MESSAGES_PER_ACCOUNT:,}"
    )


# ============================================================
# SEARCH
# ============================================================

search = st.text_input(
    "🔎 Search mailbox",
    placeholder="Type Yahoo email address..."
)


# ============================================================
# START / STOP
# ============================================================

start_col, stop_col = st.columns(2)


with start_col:

    start_clicked = st.button(
        "▶ START PROCESSING",
        type="primary",
        use_container_width=True,
        disabled=st.session_state.processing
    )


with stop_col:

    stop_clicked = st.button(
        "🛑 STOP",
        use_container_width=True,
        disabled=not st.session_state.processing
    )


# ============================================================
# STOP
# ============================================================

if stop_clicked:

    st.session_state.stop_requested = True

    st.warning(
        "🛑 Stop requested. "
        "Current IMAP operation will finish first."
    )


# ============================================================
# START
# ============================================================

if start_clicked:

    if not mailboxes:

        st.error(
            "No Yahoo mailbox environment variables found."
        )

    else:

        st.session_state.processing = True

        st.session_state.stop_requested = False

        st.session_state.results = {}

        st.session_state.last_checked = (
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )


        overall_progress = st.progress(0)

        overall_status = st.empty()

        total_accounts = len(mailboxes)


        # ====================================================
        # PROCESS ACCOUNTS
        # ====================================================

        for account_index, account in enumerate(
            mailboxes,
            start=1
        ):

            # ------------------------------------------------
            # STOP BEFORE NEXT ACCOUNT
            # ------------------------------------------------

            if st.session_state.stop_requested:

                overall_status.warning(
                    "🛑 Processing stopped."
                )

                break


            email_address = account["email"]


            overall_status.info(
                f"Account {account_index}/"
                f"{total_accounts} → "
                f"{email_address}"
            )


            # ------------------------------------------------
            # PROCESS
            # ------------------------------------------------

            result = check_mailbox(
                email_address,
                account["password"]
            )


            st.session_state.results[
                email_address
            ] = result


            # ------------------------------------------------
            # ACCOUNT PROGRESS
            # ------------------------------------------------

            overall_progress.progress(
                account_index / total_accounts
            )


            # ------------------------------------------------
            # STOP
            # ------------------------------------------------

            if st.session_state.stop_requested:

                overall_status.warning(
                    "🛑 Processing stopped by user."
                )

                break


        # ====================================================
        # PROCESSING FINISHED
        # ====================================================

        st.session_state.processing = False


        if st.session_state.stop_requested:

            overall_status.warning(
                "🛑 Processing stopped by user."
            )

        else:

            overall_status.success(
                "✅ All configured accounts processed."
            )


        st.rerun()


# ============================================================
# PROCESSING STATUS
# ============================================================

if st.session_state.processing:

    st.info(
        "🟢 Processing is running. "
        "Use STOP to stop after the current operation."
    )


# ============================================================
# LAST CHECKED
# ============================================================

if st.session_state.last_checked:

    st.caption(
        f"Last run: {st.session_state.last_checked}"
    )


# ============================================================
# OVERALL SUMMARY
# ============================================================

if st.session_state.results:

    results = list(
        st.session_state.results.values()
    )


    total_unread = sum(
        r["total_unread"]
        for r in results
    )


    total_selected = sum(
        r["selected"]
        for r in results
    )


    total_processed = sum(
        r["processed"]
        for r in results
    )


    total_seen = sum(
        r["seen"]
        for r in results
    )


    total_failed = sum(
        r["failed"]
        for r in results
    )


    st.subheader(
        "📊 Overall Summary"
    )


    a, b, c, d, e = st.columns(5)


    with a:

        st.metric(
            "Unread Found",
            f"{total_unread:,}"
        )


    with b:

        st.metric(
            "Selected",
            f"{total_selected:,}"
        )


    with c:

        st.metric(
            "Fetched",
            f"{total_processed:,}"
        )


    with d:

        st.metric(
            "Marked Seen",
            f"{total_seen:,}"
        )


    with e:

        st.metric(
            "Failed",
            f"{total_failed:,}"
        )


# ============================================================
# MAILBOX RESULTS
# ============================================================

st.subheader(
    "📬 Mailboxes"
)


for account in mailboxes:

    account_number = account["number"]

    email_address = account["email"]


    # ========================================================
    # SEARCH FILTER
    # ========================================================

    if search:

        if search.lower() not in email_address.lower():

            continue


    result = st.session_state.results.get(
        email_address
    )


    # ========================================================
    # MAILBOX CARD
    # ========================================================

    with st.container(border=True):

        # ----------------------------------------------------
        # ACCOUNT HEADER
        # ----------------------------------------------------

        left, right = st.columns([5, 1])


        with left:

            st.markdown(
                f"### {account_number}. "
                f"{email_address}"
            )


        with right:

            check_clicked = st.button(
                "▶ Open",
                key=f"open_{account_number}",
                use_container_width=True,
                disabled=st.session_state.processing
            )


        # ----------------------------------------------------
        # INDIVIDUAL OPEN
        # ----------------------------------------------------

        if check_clicked:

            st.session_state.stop_requested = False


            with st.spinner(
                f"Processing {email_address}..."
            ):

                result = check_mailbox(
                    email_address,
                    account["password"]
                )


                st.session_state.results[
                    email_address
                ] = result


                st.session_state.last_checked = (
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                )


            st.rerun()


        # ----------------------------------------------------
        # RESULT
        # ----------------------------------------------------

        if result:

            if result["status"] == "Completed":

                st.success(
                    "✅ Completed"
                )


            elif result["status"] == "Stopped by user":

                st.warning(
                    "🛑 Stopped"
                )


            elif result["status"] == "No unread mails":

                st.info(
                    "📭 No unread mails"
                )


            elif result["status"] == "Failed":

                st.error(
                    "❌ Failed"
                )


            else:

                st.warning(
                    result["status"]
                )


            # =================================================
            # MAILBOX METRICS
            # =================================================

            a, b, c, d, e = st.columns(5)


            with a:

                st.metric(
                    "Unread",
                    f"{result['total_unread']:,}"
                )


            with b:

                st.metric(
                    "Selected",
                    f"{result['selected']:,}"
                )


            with c:

                st.metric(
                    "Fetched",
                    f"{result['processed']:,}"
                )


            with d:

                st.metric(
                    "Seen",
                    f"{result['seen']:,}"
                )


            with e:

                st.metric(
                    "Failed",
                    f"{result['failed']:,}"
                )


            # =================================================
            # LIMIT
            # =================================================

            if (
                result["total_unread"]
                > MAX_MESSAGES_PER_ACCOUNT
            ):

                st.warning(
                    f"This mailbox has "
                    f"{result['total_unread']:,} unread "
                    f"messages. "
                    f"Maximum per run is "
                    f"{MAX_MESSAGES_PER_ACCOUNT:,}."
                )


            # =================================================
            # PROCESSED MAILS
            # =================================================

            if result["messages"]:

                with st.expander(
                    f"📨 Processed messages "
                    f"({len(result['messages']):,})"
                ):

                    # Dashboard display only.
                    # All selected messages are fetched.

                    display_messages = (
                        result["messages"][-20:]
                    )


                    for message in reversed(
                        display_messages
                    ):

                        st.markdown(
                            f"**#{message['number']}** "
                            f"UID: `{message['uid']}`"
                        )


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


                        if message["message_id"]:

                            st.caption(
                                f"Message-ID: "
                                f"{message['message_id']}"
                            )


                        st.divider()


            # =================================================
            # ERRORS
            # =================================================

            if result["errors"]:

                with st.expander(
                    f"⚠️ Errors "
                    f"({len(result['errors']):,})"
                ):

                    for error in result["errors"][:100]:

                        st.error(error)


                    if len(result["errors"]) > 100:

                        st.caption(
                            "Only first 100 errors "
                            "are displayed."
                        )


            # =================================================
            # TIME
            # =================================================

            st.caption(
                f"Started: {result['started']} | "
                f"Finished: {result['finished']}"
            )


        else:

            st.caption(
                "Not checked yet."
            )
