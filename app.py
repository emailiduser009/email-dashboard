import os
import imaplib
import email
from email.header import decode_header
from datetime import datetime

import streamlit as st


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Yahoo Mailbox Dashboard",
    page_icon="📬",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background:
            radial-gradient(
                circle at 10% 10%,
                rgba(109, 93, 252, 0.10),
                transparent 28%
            ),
            radial-gradient(
                circle at 90% 10%,
                rgba(76, 139, 245, 0.08),
                transparent 28%
            ),
            linear-gradient(
                135deg,
                #f7f8fc 0%,
                #eef1f8 100%
            );
    }

    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    header {
        background: transparent !important;
    }

    .login-marker {
        display: none;
    }

    [data-testid="stVerticalBlockBorderWrapper"]:has(.login-marker) {
        max-width: 470px;
        margin-left: auto;
        margin-right: auto;
        padding: 30px 34px;
        border-radius: 24px;
        border: 1px solid rgba(120, 130, 160, 0.20);
        background: rgba(255, 255, 255, 0.96);
        box-shadow:
            0 25px 70px rgba(25, 35, 65, 0.12),
            0 5px 20px rgba(25, 35, 65, 0.05);
    }

    .login-logo {
        text-align: center;
        font-size: 48px;
        margin-bottom: 5px;
    }

    .login-title {
        text-align: center;
        font-size: 27px;
        font-weight: 750;
        color: #20243a;
        margin-bottom: 5px;
    }

    .login-subtitle {
        text-align: center;
        color: #7b8193;
        font-size: 13px;
        margin-bottom: 22px;
    }

    [data-testid="stVerticalBlockBorderWrapper"]:has(.login-marker) label {
        color: #42485c !important;
        font-weight: 650 !important;
        font-size: 13px !important;
    }

    [data-testid="stVerticalBlockBorderWrapper"]:has(.login-marker) input {
        min-height: 45px !important;
        border-radius: 11px !important;
        border: 1px solid #dce0ea !important;
        background: #fafbfe !important;
    }

    [data-testid="stFormSubmitButton"] button {
        min-height: 46px !important;
        border: none !important;
        border-radius: 11px !important;
        background:
            linear-gradient(
                135deg,
                #6d5dfc,
                #4c8bf5
            ) !important;
        color: white !important;
        font-weight: 700 !important;
        box-shadow:
            0 8px 22px rgba(88, 82, 220, 0.22) !important;
    }

    .login-note {
        text-align: center;
        color: #9a9fb0;
        font-size: 11px;
        margin-top: 15px;
    }

    [data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 16px;
        border-color: rgba(120, 130, 160, 0.17);
        background: rgba(255, 255, 255, 0.92);
        box-shadow:
            0 6px 20px rgba(25, 35, 65, 0.045);
    }

    .stButton > button {
        min-height: 40px !important;
        border-radius: 10px !important;
        border: 1px solid #dce0ea !important;
        background: white !important;
        color: #34394c !important;
        font-weight: 650 !important;
    }

    .stButton > button:hover {
        border-color: #6d5dfc !important;
        color: #5b4ce0 !important;
        box-shadow:
            0 5px 16px rgba(80, 70, 200, 0.10) !important;
    }

    .stTextInput input {
        min-height: 42px !important;
        border-radius: 10px !important;
        border: 1px solid #dce0ea !important;
        background: rgba(255,255,255,0.95) !important;
    }

    @media (max-width: 700px) {

        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }

        [data-testid="stVerticalBlockBorderWrapper"]:has(.login-marker) {
            padding: 25px 20px;
        }

    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "stop_requested" not in st.session_state:
    st.session_state.stop_requested = False

if "processing" not in st.session_state:
    st.session_state.processing = False

if "results" not in st.session_state:
    st.session_state.results = {}

if "selected_mailbox" not in st.session_state:
    st.session_state.selected_mailbox = None


# ============================================================
# DASHBOARD LOGIN
# ============================================================

DASHBOARD_USERNAME = os.getenv(
    "DASHBOARD_USERNAME",
    ""
).strip()

DASHBOARD_PASSWORD = os.getenv(
    "DASHBOARD_PASSWORD",
    ""
).strip()


if not st.session_state.logged_in:

    st.write("")
    st.write("")
    st.write("")

    left, center, right = st.columns(
        [1, 1.15, 1]
    )

    with center:

        with st.container(border=True):

            st.markdown(
                '<span class="login-marker"></span>',
                unsafe_allow_html=True
            )

            st.markdown(
                '<div class="login-logo">📬</div>',
                unsafe_allow_html=True
            )

            st.markdown(
                '<div class="login-title">Mailbox Dashboard</div>',
                unsafe_allow_html=True
            )

            st.markdown(
                '<div class="login-subtitle">'
                'Sign in to manage your Yahoo mailboxes'
                '</div>',
                unsafe_allow_html=True
            )

            with st.form("dashboard_login_form"):

                username = st.text_input(
                    "Username",
                    placeholder="Enter username"
                )

                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter password"
                )

                login_clicked = st.form_submit_button(
                    "🔐  Sign in",
                    use_container_width=True
                )

                if login_clicked:

                    if (
                        not DASHBOARD_USERNAME
                        or not DASHBOARD_PASSWORD
                    ):

                        st.error(
                            "Dashboard credentials are not configured."
                        )

                    elif (
                        username == DASHBOARD_USERNAME
                        and password == DASHBOARD_PASSWORD
                    ):

                        st.session_state.logged_in = True
                        st.session_state.stop_requested = False

                        st.rerun()

                    else:

                        st.error(
                            "Invalid username or password."
                        )

            st.markdown(
                '<div class="login-note">'
                'Secure dashboard access'
                '</div>',
                unsafe_allow_html=True
            )

    st.stop()


# ============================================================
# IMAP CONFIG
# ============================================================

IMAP_SERVER = "imap.mail.yahoo.com"
IMAP_PORT = 993

MAX_MESSAGES_PER_MAILBOX = 2000


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_env_value(prefix, index):

    return os.getenv(
        f"{prefix}_{index}",
        ""
    ).strip()


def load_accounts():

    accounts = []

    for i in range(1, 101):

        yahoo_email = get_env_value(
            "YAHOO_EMAIL",
            i
        )

        yahoo_password = get_env_value(
            "YAHOO_APP_PASSWORD",
            i
        )

        if yahoo_email and yahoo_password:

            accounts.append(
                {
                    "index": i,
                    "email": yahoo_email,
                    "password": yahoo_password
                }
            )

    return accounts


def decode_mime_header(value):

    if not value:
        return ""

    try:

        parts = decode_header(value)

        decoded = ""

        for part, encoding in parts:

            if isinstance(part, bytes):

                try:

                    decoded += part.decode(
                        encoding or "utf-8",
                        errors="replace"
                    )

                except Exception:

                    decoded += part.decode(
                        "utf-8",
                        errors="replace"
                    )

            else:

                decoded += str(part)

        return decoded

    except Exception:

        return str(value)


def get_subject(message):

    try:

        return decode_mime_header(
            message.get(
                "Subject",
                ""
            )
        )

    except Exception:

        return ""


def get_from(message):

    try:

        return decode_mime_header(
            message.get(
                "From",
                ""
            )
        )

    except Exception:

        return ""


# ============================================================
# PROCESS ONE MAILBOX
# ============================================================

def check_mailbox(
    account,
    progress_placeholder=None,
    status_placeholder=None
):

    email_address = account["email"]
    app_password = account["password"]

    result = {

        "email": email_address,

        "unread_found": 0,

        "selected": 0,

        "fetched": 0,

        "seen": 0,

        "failed": 0,

        "error": "",

        "latest": [],

        "started": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),

        "finished": "",

        "stopped": False
    }

    mail = None

    try:

        # ----------------------------------------------------
        # CONNECT
        # ----------------------------------------------------

        if status_placeholder:

            status_placeholder.info(
                f"Connecting to {email_address}..."
            )

        mail = imaplib.IMAP4_SSL(
            IMAP_SERVER,
            IMAP_PORT
        )

        # ----------------------------------------------------
        # LOGIN
        # ----------------------------------------------------

        if status_placeholder:

            status_placeholder.info(
                f"Logging in to {email_address}..."
            )

        mail.login(
            email_address,
            app_password
        )

        # ----------------------------------------------------
        # SELECT INBOX
        # ----------------------------------------------------

        if status_placeholder:

            status_placeholder.info(
                f"Opening INBOX: {email_address}"
            )

        select_status, select_data = mail.select(
            "INBOX",
            readonly=False
        )

        if select_status != "OK":

            result["error"] = (
                "Unable to open INBOX."
            )

            return result

        # ----------------------------------------------------
        # SEARCH UNREAD
        # ----------------------------------------------------

        if status_placeholder:

            status_placeholder.info(
                f"Searching unread messages: {email_address}"
            )

        search_status, search_data = mail.uid(
            "search",
            None,
            "UNSEEN"
        )

        if search_status != "OK":

            result["error"] = (
                "Unable to search unread messages."
            )

            return result

        uid_bytes = (
            search_data[0]
            if search_data and search_data[0]
            else b""
        )

        all_uids = uid_bytes.split()

        result["unread_found"] = len(
            all_uids
        )

        # ----------------------------------------------------
        # SELECT MAX 2000
        # ----------------------------------------------------

        selected_uids = all_uids[
            :MAX_MESSAGES_PER_MAILBOX
        ]

        result["selected"] = len(
            selected_uids
        )

        # ----------------------------------------------------
        # NO UNREAD
        # ----------------------------------------------------

        if not selected_uids:

            if status_placeholder:

                status_placeholder.success(
                    f"{email_address}: No unread messages."
                )

            return result

        # ----------------------------------------------------
        # FETCH
        # ----------------------------------------------------

        total_to_process = len(
            selected_uids
        )

        for position, uid in enumerate(
            selected_uids,
            start=1
        ):

            # ------------------------------------------------
            # STOP CHECK
            # ------------------------------------------------

            if st.session_state.stop_requested:

                result["stopped"] = True

                break

            # ------------------------------------------------
            # STATUS
            # ------------------------------------------------

            if status_placeholder:

                status_placeholder.info(
                    f"Processing {email_address} "
                    f"({position}/{total_to_process})"
                )

            # ------------------------------------------------
            # FETCH MESSAGE
            # ------------------------------------------------

            try:

                fetch_status, message_data = mail.uid(
                    "fetch",
                    uid,
                    "(RFC822)"
                )

                if fetch_status != "OK":

                    result["failed"] += 1

                    continue

                raw_message = None

                for item in message_data:

                    if (
                        isinstance(item, tuple)
                        and len(item) >= 2
                    ):

                        if isinstance(item[1], bytes):

                            raw_message = item[1]

                            break

                if raw_message is None:

                    result["failed"] += 1

                    continue

                # ------------------------------------------------
                # PARSE MESSAGE
                # ------------------------------------------------

                message = email.message_from_bytes(
                    raw_message
                )

                subject = get_subject(
                    message
                )

                sender = get_from(
                    message
                )

                result["fetched"] += 1

                # ------------------------------------------------
                # MARK AS SEEN
                # ------------------------------------------------

                seen_status, _ = mail.uid(
                    "store",
                    uid,
                    "+FLAGS",
                    "(\\Seen)"
                )

                if seen_status == "OK":

                    result["seen"] += 1

                else:

                    result["failed"] += 1

                # ------------------------------------------------
                # SAVE LATEST 20
                # ------------------------------------------------

                if len(result["latest"]) < 20:

                    result["latest"].append(
                        {
                            "uid": uid.decode(
                                errors="replace"
                            ),

                            "from": sender,

                            "subject": subject
                        }
                    )

                # ------------------------------------------------
                # PROGRESS
                # ------------------------------------------------

                if progress_placeholder:

                    progress_placeholder.progress(
                        position / max(
                            total_to_process,
                            1
                        )
                    )

            except Exception as message_error:

                result["failed"] += 1

        return result

    except Exception as exc:

        result["error"] = str(exc)

        return result

    finally:

        result["finished"] = (
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )

        # --------------------------------------------------------
        # CLOSE IMAP
        # --------------------------------------------------------

        if mail:

            try:

                mail.close()

            except Exception:

                pass

            try:

                mail.logout()

            except Exception:

                pass


# ============================================================
# LOAD ACCOUNTS
# ============================================================

accounts = load_accounts()


# ============================================================
# DASHBOARD HEADER
# ============================================================

st.title(
    "📬 Yahoo Mailbox Dashboard"
)

st.caption(
    "Manage your configured Yahoo mailboxes"
)


# ============================================================
# TOP ROW
# ============================================================

left_top, right_top = st.columns(
    [5, 1]
)

with left_top:

    st.subheader(
        "📊 Mailbox Overview"
    )

    st.caption(
        f"{len(accounts)} configured mailbox(s)"
    )

with right_top:

    if st.button(
        "🚪 Logout",
        use_container_width=True
    ):

        st.session_state.logged_in = False
        st.session_state.stop_requested = False
        st.session_state.processing = False
        st.session_state.results = {}
        st.session_state.selected_mailbox = None

        st.rerun()


# ============================================================
# CALCULATE METRICS
# ============================================================

total_mailboxes = len(accounts)

total_unread = sum(
    result.get(
        "unread_found",
        0
    )
    for result in st.session_state.results.values()
)

total_fetched = sum(
    result.get(
        "fetched",
        0
    )
    for result in st.session_state.results.values()
)

total_seen = sum(
    result.get(
        "seen",
        0
    )
    for result in st.session_state.results.values()
)

total_failed = sum(
    result.get(
        "failed",
        0
    )
    for result in st.session_state.results.values()
)


# ============================================================
# METRICS
# ============================================================

m1, m2, m3, m4, m5 = st.columns(5)

with m1:

    st.metric(
        "📬 Mailboxes",
        total_mailboxes
    )

with m2:

    st.metric(
        "📩 Unread Found",
        f"{total_unread:,}"
    )

with m3:

    st.metric(
        "📥 Fetched",
        f"{total_fetched:,}"
    )

with m4:

    st.metric(
        "✓ Marked Seen",
        f"{total_seen:,}"
    )

with m5:

    st.metric(
        "⚠️ Failed",
        f"{total_failed:,}"
    )


st.write("")


# ============================================================
# SEARCH
# ============================================================

search_text = st.text_input(
    "🔎 Search mailbox",
    placeholder="Search by Yahoo email address..."
)


# ============================================================
# START / STOP
# ============================================================

start_col, stop_col, empty_col = st.columns(
    [1.5, 1, 5]
)

with start_col:

    start_clicked = st.button(
        "▶ START PROCESSING",
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
        "Stop requested. Current mailbox operation will finish first."
    )


# ============================================================
# START ALL MAILBOXES
# ============================================================

if start_clicked:

    if not accounts:

        st.error(
            "No Yahoo mailboxes are configured."
        )

    else:

        st.session_state.processing = True
        st.session_state.stop_requested = False
        st.session_state.results = {}
        st.session_state.selected_mailbox = None

        st.info(
            f"Processing {len(accounts)} mailbox(es). "
            f"Maximum {MAX_MESSAGES_PER_MAILBOX:,} "
            f"unread messages per mailbox."
        )

        overall_progress = st.progress(0)

        overall_status = st.empty()

        for account_number, account in enumerate(
            accounts,
            start=1
        ):

            if st.session_state.stop_requested:

                break

            overall_status.info(
                f"Mailbox {account_number}/{len(accounts)}: "
                f"{account['email']}"
            )

            mailbox_progress = st.empty()

            mailbox_status = st.empty()

            result = check_mailbox(
                account,
                progress_placeholder=mailbox_progress,
                status_placeholder=mailbox_status
            )

            # IMPORTANT
            # Save result immediately
            st.session_state.results[
                account["email"]
            ] = result

            overall_progress.progress(
                account_number / len(accounts)
            )

            mailbox_progress.empty()
            mailbox_status.empty()

        st.session_state.processing = False

        if st.session_state.stop_requested:

            st.warning(
                "Processing stopped."
            )

        else:

            st.success(
                "All mailboxes processed successfully."
            )

        st.rerun()


# ============================================================
# PROCESSING STATUS
# ============================================================

if st.session_state.processing:

    st.info(
        "⏳ Processing is running..."
    )


# ============================================================
# RESULTS SUMMARY
# ============================================================

if st.session_state.results:

    st.subheader(
        "📈 Processing Results"
    )

    r1, r2, r3 = st.columns(3)

    with r1:

        st.metric(
            "Unread Found",
            f"{total_unread:,}"
        )

    with r2:

        st.metric(
            "Fetched",
            f"{total_fetched:,}"
        )

    with r3:

        st.metric(
            "Marked Seen",
            f"{total_seen:,}"
        )


# ============================================================
# MAILBOX SECTION
# ============================================================

st.subheader(
    "📬 Mailboxes"
)

st.caption(
    "Open / Process a mailbox to check its unread messages."
)


# ============================================================
# FILTER
# ============================================================

filtered_accounts = accounts

if search_text:

    search_lower = search_text.lower()

    filtered_accounts = [

        account

        for account in accounts

        if search_lower
        in account["email"].lower()

    ]


# ============================================================
# MAILBOX GRID
# ============================================================

for row_start in range(
    0,
    len(filtered_accounts),
    3
):

    row_accounts = filtered_accounts[
        row_start:row_start + 3
    ]

    cols = st.columns(3)

    for col, account in zip(
        cols,
        row_accounts
    ):

        with col:

            email_address = account["email"]

            result = st.session_state.results.get(
                email_address
            )

            with st.container(border=True):

                st.markdown(
                    f"### 📧 Mailbox {account['index']}"
                )

                st.caption(
                    email_address
                )

                # ------------------------------------------------
                # RESULT
                # ------------------------------------------------

                if result:

                    if result.get("error"):

                        st.error(
                            "⚠️ Processing failed"
                        )

                        st.caption(
                            result.get(
                                "error",
                                "Unknown error"
                            )
                        )

                    elif result.get("stopped"):

                        st.warning(
                            "⏸ Processing stopped"
                        )

                    else:

                        st.success(
                            "✓ Processed"
                        )

                    c1, c2 = st.columns(2)

                    with c1:

                        st.caption(
                            f"Unread: "
                            f"{result.get('unread_found', 0):,}"
                        )

                    with c2:

                        st.caption(
                            f"Seen: "
                            f"{result.get('seen', 0):,}"
                        )

                else:

                    st.info(
                        "Not processed yet"
                    )

                # ------------------------------------------------
                # OPEN / PROCESS BUTTON
                # ------------------------------------------------

                if st.button(
                    "▶ Open / Process",
                    key=f"open_{account['index']}",
                    use_container_width=True
                ):

                    st.session_state.selected_mailbox = (
                        email_address
                    )

                    with st.spinner(
                        f"Processing {email_address}..."
                    ):

                        mailbox_progress = st.progress(0)

                        mailbox_status = st.empty()

                        result = check_mailbox(
                            account,
                            progress_placeholder=mailbox_progress,
                            status_placeholder=mailbox_status
                        )

                        # IMPORTANT:
                        # Save result before rerun
                        st.session_state.results[
                            email_address
                        ] = result

                        mailbox_progress.empty()
                        mailbox_status.empty()

                    st.rerun()


# ============================================================
# SELECTED MAILBOX
# ============================================================

selected_mailbox = (
    st.session_state.selected_mailbox
)


if selected_mailbox:

    selected_result = (
        st.session_state.results.get(
            selected_mailbox
        )
    )

    st.divider()

    st.subheader(
        f"📩 {selected_mailbox}"
    )

    st.caption(
        "Latest processed messages"
    )

    if not selected_result:

        st.info(
            "This mailbox has not been processed yet."
        )

    elif selected_result.get("error"):

        st.error(
            f"⚠️ Processing failed: "
            f"{selected_result['error']}"
        )

    else:

        a1, a2, a3, a4, a5 = st.columns(5)

        with a1:

            st.metric(
                "Unread",
                f"{selected_result.get('unread_found', 0):,}"
            )

        with a2:

            st.metric(
                "Selected",
                f"{selected_result.get('selected', 0):,}"
            )

        with a3:

            st.metric(
                "Fetched",
                f"{selected_result.get('fetched', 0):,}"
            )

        with a4:

            st.metric(
                "Seen",
                f"{selected_result.get('seen', 0):,}"
            )

        with a5:

            st.metric(
                "Failed",
                f"{selected_result.get('failed', 0):,}"
            )

        st.write("")

        latest_messages = (
            selected_result.get(
                "latest",
                []
            )
        )

        if latest_messages:

            for message in latest_messages:

                with st.container(border=True):

                    st.write(
                        f"**From:** "
                        f"{message.get('from', '')}"
                    )

                    st.write(
                        f"**Subject:** "
                        f"{message.get('subject', '')}"
                    )

                    st.caption(
                        f"UID: "
                        f"{message.get('uid', '')}"
                    )

        else:

            st.info(
                "No processed messages to display."
            )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Yahoo Mailbox Dashboard"
)
