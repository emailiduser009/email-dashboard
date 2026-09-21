import streamlit as st
import imaplib
import email
import os
from email.header import decode_header
from datetime import datetime


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Yahoo Mailbox Dashboard",
    page_icon="📬",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# =========================================================
# SETTINGS
# =========================================================

IMAP_SERVER = "imap.mail.yahoo.com"
IMAP_PORT = 993

MAX_MESSAGES_PER_MAILBOX = 2000
MAX_LATEST_MESSAGES = 20


# =========================================================
# SESSION STATE
# =========================================================

defaults = {
    "logged_in": False,
    "stop_requested": False,
    "processing": False,
    "results": {},
    "selected_mailbox": None,
    "processing_index": 0,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
    <style>

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    header {
        visibility: hidden;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    .login-box {
        max-width: 430px;
        margin: 70px auto 0 auto;
        padding: 32px;
        border-radius: 18px;
        border: 1px solid rgba(128,128,128,0.25);
        box-shadow: 0 8px 30px rgba(0,0,0,0.08);
    }

    .login-icon {
        font-size: 42px;
        text-align: center;
    }

    .login-title {
        text-align: center;
        font-size: 27px;
        font-weight: 700;
        margin-top: 8px;
    }

    .login-subtitle {
        text-align: center;
        opacity: 0.7;
        margin-bottom: 25px;
    }

    .mailbox-card {
        padding: 18px;
        border: 1px solid rgba(128,128,128,0.22);
        border-radius: 14px;
        margin-bottom: 12px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def decode_mime(value):
    if not value:
        return ""

    try:
        parts = decode_header(value)
        output = ""

        for part, encoding in parts:
            if isinstance(part, bytes):
                output += part.decode(
                    encoding or "utf-8",
                    errors="replace"
                )
            else:
                output += str(part)

        return output

    except Exception:
        return str(value)


def load_accounts():

    accounts = []

    for i in range(1, 101):

        email_address = os.getenv(f"YAHOO_EMAIL_{i}")
        app_password = os.getenv(f"YAHOO_APP_PASSWORD_{i}")

        if email_address and app_password:

            accounts.append(
                {
                    "index": i,
                    "email": email_address.strip(),
                    "password": app_password.strip()
                }
            )

    return accounts


# =========================================================
# MAILBOX PROCESSING
# =========================================================

def check_mailbox(
    account,
    progress_placeholder=None,
    status_placeholder=None
):

    email_address = account["email"]
    password = account["password"]

    result = {
        "email": email_address,
        "unread_found": 0,
        "selected": 0,
        "fetched": 0,
        "seen": 0,
        "failed": 0,
        "error": "",
        "latest": [],
        "started": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "finished": "",
        "stopped": False,
    }

    mail = None

    try:

        # -------------------------------------------------
        # CONNECT
        # -------------------------------------------------

        if status_placeholder:
            status_placeholder.info(
                f"Connecting to {email_address}..."
            )

        mail = imaplib.IMAP4_SSL(
            IMAP_SERVER,
            IMAP_PORT
        )

        # -------------------------------------------------
        # LOGIN
        # -------------------------------------------------

        if status_placeholder:
            status_placeholder.info(
                f"Logging in: {email_address}"
            )

        mail.login(
            email_address,
            password
        )

        # -------------------------------------------------
        # SELECT INBOX
        # -------------------------------------------------

        mail.select("INBOX")

        # -------------------------------------------------
        # SEARCH UNREAD
        # -------------------------------------------------

        if status_placeholder:
            status_placeholder.info(
                f"Checking unread messages: {email_address}"
            )

        status, data = mail.uid(
            "search",
            None,
            "UNSEEN"
        )

        if status != "OK":
            raise Exception(
                "Unable to search UNSEEN messages"
            )

        uid_list = data[0].split()

        result["unread_found"] = len(uid_list)

        # -------------------------------------------------
        # LIMIT TO 2000
        # -------------------------------------------------

        selected_uids = uid_list[
            :MAX_MESSAGES_PER_MAILBOX
        ]

        result["selected"] = len(selected_uids)

        if len(selected_uids) == 0:

            if status_placeholder:
                status_placeholder.success(
                    f"No unread messages: {email_address}"
                )

            result["finished"] = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            return result

        # -------------------------------------------------
        # PROCESS MESSAGES
        # -------------------------------------------------

        total = len(selected_uids)

        for position, uid in enumerate(
            selected_uids,
            start=1
        ):

            # ---------------------------------------------
            # STOP CHECK
            # ---------------------------------------------

            if st.session_state.stop_requested:

                result["stopped"] = True

                if status_placeholder:
                    status_placeholder.warning(
                        f"Stopped: {email_address}"
                    )

                break

            # ---------------------------------------------
            # PROGRESS
            # ---------------------------------------------

            percent = position / total

            if progress_placeholder:
                progress_placeholder.progress(
                    percent
                )

            if status_placeholder:
                status_placeholder.info(
                    f"Processing {position}/{total} "
                    f"— {email_address}"
                )

            # ---------------------------------------------
            # FETCH MESSAGE
            # ---------------------------------------------

            try:

                fetch_status, msg_data = mail.uid(
                    "fetch",
                    uid,
                    "(RFC822)"
                )

                if fetch_status != "OK":
                    result["failed"] += 1
                    continue

                raw_message = None

                for item in msg_data:

                    if isinstance(item, tuple):

                        raw_message = item[1]

                        break

                if not raw_message:

                    result["failed"] += 1

                    continue

                # -----------------------------------------
                # PARSE MESSAGE
                # -----------------------------------------

                msg = email.message_from_bytes(
                    raw_message
                )

                subject = decode_mime(
                    msg.get("Subject", "")
                )

                sender = decode_mime(
                    msg.get("From", "")
                )

                # -----------------------------------------
                # FETCH COUNT
                # -----------------------------------------

                result["fetched"] += 1

                # -----------------------------------------
                # MARK SEEN
                # -----------------------------------------

                seen_status, _ = mail.uid(
                    "store",
                    uid,
                    "+FLAGS",
                    "(\\Seen)"
                )

                if seen_status == "OK":

                    result["seen"] += 1

                # -----------------------------------------
                # SAVE LATEST 20
                # -----------------------------------------

                if len(result["latest"]) < MAX_LATEST_MESSAGES:

                    result["latest"].append(
                        {
                            "subject": subject
                            if subject
                            else "(No Subject)",

                            "from": sender
                            if sender
                            else "(Unknown Sender)"
                        }
                    )

            except Exception:

                result["failed"] += 1

                continue

        # -------------------------------------------------
        # COMPLETE
        # -------------------------------------------------

        result["finished"] = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        if not result["stopped"]:

            if progress_placeholder:
                progress_placeholder.progress(1.0)

            if status_placeholder:
                status_placeholder.success(
                    f"Completed: {email_address}"
                )

        return result

    except Exception as exc:

        result["error"] = str(exc)

        result["finished"] = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        if status_placeholder:
            status_placeholder.error(
                f"Error: {email_address} — {exc}"
            )

        return result

    finally:

        if mail:

            try:
                mail.close()
            except Exception:
                pass

            try:
                mail.logout()
            except Exception:
                pass


# =========================================================
# LOGIN PAGE
# =========================================================

if not st.session_state.logged_in:

    st.markdown(
        """
        <div class="login-box">

            <div class="login-icon">📬</div>

            <div class="login-title">
                Mailbox Dashboard
            </div>

            <div class="login-subtitle">
                Sign in to manage your Yahoo mailboxes
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    username = st.text_input(
        "Username",
        key="login_username"
    )

    password = st.text_input(
        "Password",
        type="password",
        key="login_password"
    )

    login_clicked = st.button(
        "🔐 LOGIN",
        use_container_width=True
    )

    if login_clicked:

        dashboard_username = os.getenv(
            "DASHBOARD_USERNAME"
        )

        dashboard_password = os.getenv(
            "DASHBOARD_PASSWORD"
        )

        if (
            dashboard_username
            and dashboard_password
            and username == dashboard_username
            and password == dashboard_password
        ):

            st.session_state.logged_in = True

            st.rerun()

        else:

            st.error(
                "Invalid username or password."
            )

    st.stop()


# =========================================================
# LOAD ACCOUNTS
# =========================================================

accounts = load_accounts()


# =========================================================
# HEADER
# =========================================================

st.title("📬 Yahoo Mailbox Dashboard")

st.caption(
    "Manage your configured Yahoo mailboxes"
)


# =========================================================
# TOP CONTROLS
# =========================================================

col1, col2, col3 = st.columns(
    [2, 1, 1]
)


# =========================================================
# START PROCESSING
# =========================================================

with col1:

    start_clicked = st.button(
        "▶ START PROCESSING",
        use_container_width=True,
        disabled=st.session_state.processing
    )


# =========================================================
# STOP
# =========================================================

with col2:

    stop_clicked = st.button(
        "🛑 STOP",
        use_container_width=True,
        disabled=not st.session_state.processing
    )


# =========================================================
# LOGOUT
# =========================================================

with col3:

    logout_clicked = st.button(
        "🚪 LOGOUT",
        use_container_width=True
    )


if logout_clicked:

    st.session_state.logged_in = False
    st.session_state.processing = False
    st.session_state.stop_requested = False

    st.rerun()


# =========================================================
# STOP REQUEST
# =========================================================

if stop_clicked:

    st.session_state.stop_requested = True

    st.warning(
        "🛑 Stop requested. Current message will finish, "
        "then processing will stop."
    )


# =========================================================
# START GLOBAL PROCESSING
# =========================================================

if start_clicked:

    if not accounts:

        st.error(
            "No Yahoo mailbox configured."
        )

    else:

        # IMPORTANT:
        # Do NOT clear results here.
        #
        # Old code had:
        # st.session_state.results = {}
        #
        # That caused already processed mailbox
        # information to disappear.

        st.session_state.processing = True
        st.session_state.stop_requested = False

        # -------------------------------------------------
        # FIND NEXT MAILBOX
        # -------------------------------------------------

        total_accounts = len(accounts)

        for index, account in enumerate(accounts):

            email_address = account["email"]

            # ---------------------------------------------
            # STOP
            # ---------------------------------------------

            if st.session_state.stop_requested:

                st.session_state.processing_index = index

                break

            # ---------------------------------------------
            # ALREADY COMPLETED?
            # ---------------------------------------------

            existing = st.session_state.results.get(
                email_address
            )

            if existing:

                # If mailbox was previously completed
                # and not stopped, skip it.

                if (
                    existing.get("finished")
                    and not existing.get("stopped")
                    and not existing.get("error")
                ):

                    continue

            # ---------------------------------------------
            # CURRENT MAILBOX
            # ---------------------------------------------

            st.session_state.processing_index = index

            st.subheader(
                f"📬 Processing mailbox "
                f"{index + 1}/{total_accounts}"
            )

            mailbox_progress = st.progress(0)

            mailbox_status = st.empty()

            result = check_mailbox(
                account,
                progress_placeholder=mailbox_progress,
                status_placeholder=mailbox_status
            )

            # ---------------------------------------------
            # SAVE RESULT IMMEDIATELY
            # ---------------------------------------------

            st.session_state.results[
                email_address
            ] = result

            mailbox_progress.empty()
            mailbox_status.empty()

            # ---------------------------------------------
            # STOP AFTER CURRENT MAILBOX
            # ---------------------------------------------

            if result.get("stopped"):

                break

        # -------------------------------------------------
        # PROCESSING FINISHED / STOPPED
        # -------------------------------------------------

        st.session_state.processing = False

        if st.session_state.stop_requested:

            st.warning(
                "🛑 Processing stopped. "
                "Completed mailbox results are saved."
            )

        else:

            st.success(
                "✅ All available mailboxes processed."
            )

        st.rerun()


# =========================================================
# SEARCH
# =========================================================

search_text = st.text_input(
    "🔎 Search mailbox",
    placeholder="Search mailbox..."
)


# =========================================================
# METRICS
# =========================================================

mailboxes_count = len(accounts)

unread_total = sum(
    r.get("unread_found", 0)
    for r in st.session_state.results.values()
)

fetched_total = sum(
    r.get("fetched", 0)
    for r in st.session_state.results.values()
)

seen_total = sum(
    r.get("seen", 0)
    for r in st.session_state.results.values()
)

failed_total = sum(
    r.get("failed", 0)
    for r in st.session_state.results.values()
)


m1, m2, m3, m4, m5 = st.columns(5)

m1.metric(
    "Mailboxes",
    mailboxes_count
)

m2.metric(
    "Unread Found",
    unread_total
)

m3.metric(
    "Fetched",
    fetched_total
)

m4.metric(
    "Marked Seen",
    seen_total
)

m5.metric(
    "Failed",
    failed_total
)


# =========================================================
# PROCESSING STATUS
# =========================================================

if st.session_state.processing:

    st.info(
        "⏳ Processing is running..."
    )

elif st.session_state.results:

    st.success(
        "✅ Processing is not running."
    )


# =========================================================
# MAILBOX LIST
# =========================================================

st.divider()

st.subheader("📮 Mailboxes")


if not accounts:

    st.warning(
        "No Yahoo mailboxes configured in Render environment variables."
    )

else:

    for account in accounts:

        email_address = account["email"]

        if (
            search_text
            and search_text.lower()
            not in email_address.lower()
        ):
            continue

        result = st.session_state.results.get(
            email_address
        )

        with st.container(border=True):

            c1, c2 = st.columns(
                [4, 1]
            )

            with c1:

                st.markdown(
                    f"### 📧 {email_address}"
                )

                if result:

                    if result.get("stopped"):

                        st.warning(
                            "⏸ Processing stopped"
                        )

                    elif result.get("error"):

                        st.error(
                            f"❌ Error: "
                            f"{result['error']}"
                        )

                    else:

                        st.success(
                            "✅ Processed"
                        )

                    st.write(
                        f"Unread: **{result.get('unread_found', 0)}**  |  "
                        f"Fetched: **{result.get('fetched', 0)}**  |  "
                        f"Seen: **{result.get('seen', 0)}**  |  "
                        f"Failed: **{result.get('failed', 0)}**"
                    )

                else:

                    st.info(
                        "This mailbox has not been processed yet."
                    )

            with c2:

                open_clicked = st.button(
                    "▶ Open / Process",
                    key=f"open_{account['index']}",
                    use_container_width=True
                )

                if open_clicked:

                    st.session_state.selected_mailbox = (
                        email_address
                    )

                    with st.spinner(
                        f"Processing {email_address}..."
                    ):

                        mailbox_progress = st.progress(
                            0
                        )

                        mailbox_status = st.empty()

                        result = check_mailbox(
                            account,
                            progress_placeholder=mailbox_progress,
                            status_placeholder=mailbox_status
                        )

                        # SAVE RESULT
                        st.session_state.results[
                            email_address
                        ] = result

                        mailbox_progress.empty()
                        mailbox_status.empty()

                    st.rerun()


# =========================================================
# SELECTED MAILBOX DETAILS
# =========================================================

selected = st.session_state.selected_mailbox


if selected:

    selected_result = st.session_state.results.get(
        selected
    )

    if selected_result:

        st.divider()

        st.subheader(
            f"📧 {selected}"
        )

        d1, d2, d3, d4 = st.columns(4)

        d1.metric(
            "Unread",
            selected_result.get(
                "unread_found",
                0
            )
        )

        d2.metric(
            "Fetched",
            selected_result.get(
                "fetched",
                0
            )
        )

        d3.metric(
            "Seen",
            selected_result.get(
                "seen",
                0
            )
        )

        d4.metric(
            "Failed",
            selected_result.get(
                "failed",
                0
            )
        )

        if selected_result.get("error"):

            st.error(
                selected_result["error"]
            )

        if selected_result.get("stopped"):

            st.warning(
                "Processing was stopped."
            )

        # -------------------------------------------------
        # LATEST MESSAGES
        # -------------------------------------------------

        latest = selected_result.get(
            "latest",
            []
        )

        if latest:

            st.subheader(
                "📨 Latest Processed Messages"
            )

            for message in latest:

                with st.container(border=True):

                    st.write(
                        f"**Subject:** "
                        f"{message.get('subject', '(No Subject)')}"
                    )

                    st.write(
                        f"**From:** "
                        f"{message.get('from', '(Unknown Sender)')}"
                    )

        else:

            st.info(
                "No messages were processed."
            )
