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
    page_title="Yahoo Mail Dashboard",
    page_icon="📬",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    /* ======================================================
       GLOBAL
       ====================================================== */

    .stApp {
        background:
            radial-gradient(
                circle at 15% 10%,
                rgba(124, 92, 255, 0.13),
                transparent 30%
            ),
            radial-gradient(
                circle at 85% 20%,
                rgba(0, 180, 216, 0.10),
                transparent 30%
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

    /* Hide Streamlit decoration */
    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    header {
        background: transparent !important;
    }


    /* ======================================================
       LOGIN PAGE
       ====================================================== */

    .login-page-space {
        height: 5vh;
    }

    .login-marker {
        height: 1px;
        width: 1px;
        overflow: hidden;
    }

    [data-testid="stVerticalBlockBorderWrapper"]:has(.login-marker) {
        max-width: 470px;
        margin-left: auto;
        margin-right: auto;
        padding: 32px 34px 30px 34px;
        border-radius: 24px;
        border: 1px solid rgba(120, 130, 160, 0.20);
        background: rgba(255, 255, 255, 0.94);
        box-shadow:
            0 20px 60px rgba(25, 35, 65, 0.12),
            0 4px 18px rgba(25, 35, 65, 0.05);
        backdrop-filter: blur(12px);
    }

    .login-logo {
        width: 70px;
        height: 70px;
        margin: 0 auto 16px auto;
        border-radius: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 34px;
        background:
            linear-gradient(
                135deg,
                #6d5dfc,
                #4c8bf5
            );
        box-shadow:
            0 12px 28px rgba(88, 82, 220, 0.25);
    }

    .login-title {
        text-align: center;
        font-size: 28px;
        font-weight: 750;
        color: #20243a;
        margin-bottom: 5px;
        letter-spacing: -0.5px;
    }

    .login-subtitle {
        text-align: center;
        color: #72788c;
        font-size: 14px;
        margin-bottom: 22px;
    }

    [data-testid="stVerticalBlockBorderWrapper"]:has(.login-marker)
    label {
        color: #42485c !important;
        font-weight: 600 !important;
        font-size: 13px !important;
    }

    [data-testid="stVerticalBlockBorderWrapper"]:has(.login-marker)
    input {
        border-radius: 11px !important;
        border: 1px solid #dce0ea !important;
        background: #fafbfe !important;
        min-height: 45px !important;
        padding-left: 13px !important;
    }

    [data-testid="stVerticalBlockBorderWrapper"]:has(.login-marker)
    input:focus {
        border-color: #6d5dfc !important;
        box-shadow: 0 0 0 2px rgba(109, 93, 252, 0.10) !important;
    }

    .login-note {
        text-align: center;
        color: #969bad;
        font-size: 12px;
        margin-top: 15px;
    }


    /* ======================================================
       DASHBOARD HEADER
       ====================================================== */

    .dashboard-hero {
        padding: 25px 28px;
        border-radius: 22px;
        background:
            linear-gradient(
                135deg,
                rgba(255,255,255,0.96),
                rgba(247,248,253,0.96)
            );
        border: 1px solid rgba(120,130,160,0.17);
        box-shadow:
            0 12px 35px rgba(25,35,65,0.07);
        margin-bottom: 22px;
    }

    .hero-row {
        display: flex;
        align-items: center;
        gap: 16px;
    }

    .hero-icon {
        width: 58px;
        height: 58px;
        border-radius: 17px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 29px;
        background:
            linear-gradient(
                135deg,
                #6d5dfc,
                #4c8bf5
            );
        box-shadow:
            0 10px 25px rgba(88,82,220,0.20);
    }

    .hero-title {
        font-size: 28px;
        font-weight: 750;
        color: #20243a;
        margin: 0;
        letter-spacing: -0.5px;
    }

    .hero-subtitle {
        color: #7b8193;
        font-size: 13px;
        margin-top: 4px;
    }


    /* ======================================================
       METRIC CARDS
       ====================================================== */

    .metric-card {
        padding: 18px 20px;
        min-height: 110px;
        border-radius: 18px;
        background: rgba(255,255,255,0.94);
        border: 1px solid rgba(120,130,160,0.16);
        box-shadow: 0 8px 25px rgba(25,35,65,0.055);
    }

    .metric-label {
        color: #858b9d;
        font-size: 12px;
        font-weight: 600;
        margin-bottom: 7px;
    }

    .metric-value {
        color: #25293c;
        font-size: 28px;
        font-weight: 750;
        line-height: 1;
    }


    /* ======================================================
       SECTION TITLES
       ====================================================== */

    .section-title {
        color: #292d40;
        font-size: 19px;
        font-weight: 720;
        margin-top: 12px;
        margin-bottom: 4px;
    }

    .section-subtitle {
        color: #858b9d;
        font-size: 12px;
        margin-bottom: 12px;
    }


    /* ======================================================
       MAILBOX CARDS
       ====================================================== */

    [data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 17px;
        border-color: rgba(120,130,160,0.17);
        background: rgba(255,255,255,0.90);
        box-shadow: 0 6px 20px rgba(25,35,65,0.045);
    }

    .mailbox-title {
        font-size: 15px;
        font-weight: 700;
        color: #2d3144;
        margin-bottom: 2px;
    }

    .mailbox-email {
        font-size: 12px;
        color: #808699;
    }

    .mailbox-status {
        display: inline-block;
        padding: 4px 9px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 650;
        margin-top: 7px;
        background: #eef1f8;
        color: #626a7f;
    }


    /* ======================================================
       BUTTONS
       ====================================================== */

    .stButton > button {
        border-radius: 10px !important;
        min-height: 40px !important;
        font-weight: 650 !important;
        border: 1px solid #dce0ea !important;
        background: #ffffff !important;
        color: #34394c !important;
        transition: all 0.18s ease !important;
    }

    .stButton > button:hover {
        border-color: #6d5dfc !important;
        color: #5b4ce0 !important;
        box-shadow: 0 5px 16px rgba(80,70,200,0.10) !important;
    }


    /* Login button */

    [data-testid="stFormSubmitButton"] button {
        border: none !important;
        border-radius: 11px !important;
        min-height: 46px !important;
        background:
            linear-gradient(
                135deg,
                #6d5dfc,
                #4c8bf5
            ) !important;
        color: white !important;
        font-weight: 700 !important;
        box-shadow:
            0 8px 20px rgba(88,82,220,0.20) !important;
    }

    [data-testid="stFormSubmitButton"] button:hover {
        box-shadow:
            0 10px 25px rgba(88,82,220,0.30) !important;
        transform: translateY(-1px);
    }


    /* ======================================================
       SEARCH
       ====================================================== */

    .stTextInput input {
        border-radius: 11px !important;
        border: 1px solid #dce0ea !important;
        background: rgba(255,255,255,0.95) !important;
    }


    /* ======================================================
       ALERTS
       ====================================================== */

    .stAlert {
        border-radius: 12px !important;
    }


    /* ======================================================
       MOBILE
       ====================================================== */

    @media (max-width: 700px) {

        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }

        [data-testid="stVerticalBlockBorderWrapper"]:has(.login-marker) {
            padding: 25px 20px;
        }

        .hero-title {
            font-size: 23px;
        }

        .dashboard-hero {
            padding: 20px;
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

DASHBOARD_USERNAME = os.getenv("DASHBOARD_USERNAME", "")
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "")


if not st.session_state.logged_in:

    st.markdown('<div class="login-page-space"></div>', unsafe_allow_html=True)

    left, center, right = st.columns([1, 1.15, 1])

    with center:

        with st.container(border=True):

            st.markdown(
                '<div class="login-marker"></div>',
                unsafe_allow_html=True
            )

            st.markdown(
                """
                <div class="login-logo">📬</div>

                <div class="login-title">
                    Mailbox Dashboard
                </div>

                <div class="login-subtitle">
                    Sign in to manage your Yahoo mailboxes
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.form("dashboard_login_form"):

                username = st.text_input(
                    "Username",
                    placeholder="Enter dashboard username",
                )

                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter dashboard password",
                )

                login_clicked = st.form_submit_button(
                    "🔐  Sign in",
                    use_container_width=True,
                )

                if login_clicked:

                    if not DASHBOARD_USERNAME or not DASHBOARD_PASSWORD:
                        st.error(
                            "Dashboard login credentials are not configured."
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
                """
                <div class="login-note">
                    Secure dashboard access
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.stop()


# ============================================================
# IMAP SETTINGS
# ============================================================

IMAP_SERVER = "imap.mail.yahoo.com"
IMAP_PORT = 993

MAX_MESSAGES_PER_MAILBOX = 2000


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_env_value(prefix, index):
    return os.getenv(f"{prefix}_{index}", "").strip()


def load_accounts():
    accounts = []

    for i in range(1, 101):

        email_address = get_env_value(
            "YAHOO_EMAIL",
            i
        )

        app_password = get_env_value(
            "YAHOO_APP_PASSWORD",
            i
        )

        if email_address and app_password:

            accounts.append(
                {
                    "index": i,
                    "email": email_address,
                    "password": app_password,
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
            message.get("Subject", "")
        )

    except Exception:
        return ""


def get_from(message):

    try:
        return decode_mime_header(
            message.get("From", "")
        )

    except Exception:
        return ""


# ============================================================
# PROCESS ONE MAILBOX
# ============================================================

def check_mailbox(
    account,
    progress_placeholder=None,
    status_placeholder=None,
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
    }

    mail = None

    try:

        if status_placeholder:
            status_placeholder.info(
                f"Connecting to {email_address}..."
            )

        # ----------------------------------------------------
        # CONNECT
        # ----------------------------------------------------

        mail = imaplib.IMAP4_SSL(
            IMAP_SERVER,
            IMAP_PORT
        )

        mail.login(
            email_address,
            app_password
        )

        mail.select(
            "INBOX",
            readonly=False
        )

        # ----------------------------------------------------
        # SEARCH UNREAD
        # ----------------------------------------------------

        status, data = mail.uid(
            "search",
            None,
            "UNSEEN"
        )

        if status != "OK":

            result["error"] = (
                "Unable to search unread messages."
            )

            return result

        uid_bytes = data[0] if data else b""

        all_uids = uid_bytes.split()

        result["unread_found"] = len(all_uids)

        # ----------------------------------------------------
        # LIMIT TO 2000
        # ----------------------------------------------------

        selected_uids = all_uids[
            :MAX_MESSAGES_PER_MAILBOX
        ]

        result["selected"] = len(selected_uids)

        # ----------------------------------------------------
        # FETCH MESSAGES
        # ----------------------------------------------------

        for position, uid in enumerate(
            selected_uids,
            start=1
        ):

            # STOP CHECK
            if st.session_state.stop_requested:
                break

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
                        raw_message = item[1]
                        break

                if raw_message is None:
                    result["failed"] += 1
                    continue

                # Parse message
                message = email.message_from_bytes(
                    raw_message
                )

                subject = get_subject(message)
                sender = get_from(message)

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
                # STORE ONLY LATEST 20 FOR UI
                # ------------------------------------------------

                if len(result["latest"]) < 20:

                    result["latest"].append(
                        {
                            "uid": uid.decode(
                                errors="replace"
                            ),
                            "from": sender,
                            "subject": subject,
                        }
                    )

                # ------------------------------------------------
                # PROGRESS
                # ------------------------------------------------

                if progress_placeholder:

                    progress_placeholder.progress(
                        position
                        / max(
                            len(selected_uids),
                            1
                        )
                    )

                if status_placeholder:

                    status_placeholder.info(
                        f"Processing {email_address}  "
                        f"({position}/{len(selected_uids)})"
                    )

            except Exception:

                result["failed"] += 1

        return result

    except Exception as exc:

        result["error"] = str(exc)

        return result

    finally:

        try:

            if mail:

                try:
                    mail.close()
                except Exception:
                    pass

                try:
                    mail.logout()
                except Exception:
                    pass

        except Exception:
            pass

        result["finished"] = (
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )


# ============================================================
# LOAD ACCOUNTS
# ============================================================

accounts = load_accounts()


# ============================================================
# DASHBOARD HEADER
# ============================================================

st.markdown(
    """
    <div class="dashboard-hero">

        <div class="hero-row">

            <div class="hero-icon">
                📬
            </div>

            <div>

                <div class="hero-title">
                    Yahoo Mailbox Dashboard
                </div>

                <div class="hero-subtitle">
                    Manage unread messages across your configured mailboxes
                </div>

            </div>

        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# TOP BAR
# ============================================================

top_left, top_middle, top_right = st.columns(
    [2, 5, 1]
)

with top_left:

    st.markdown(
        f"""
        <div class="section-title">
            📊 Mailbox Overview
        </div>
        <div class="section-subtitle">
            {len(accounts)} configured mailbox(s)
        </div>
        """,
        unsafe_allow_html=True,
    )


with top_right:

    if st.button(
        "🚪 Logout",
        use_container_width=True
    ):

        st.session_state.logged_in = False
        st.session_state.stop_requested = False
        st.session_state.processing = False
        st.rerun()


# ============================================================
# METRICS
# ============================================================

total_mailboxes = len(accounts)

total_unread = sum(
    item.get("unread_found", 0)
    for item in st.session_state.results.values()
)

total_fetched = sum(
    item.get("fetched", 0)
    for item in st.session_state.results.values()
)

total_seen = sum(
    item.get("seen", 0)
    for item in st.session_state.results.values()
)

total_failed = sum(
    item.get("failed", 0)
    for item in st.session_state.results.values()
)


m1, m2, m3, m4, m5 = st.columns(5)

with m1:

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">
                MAILBOXES
            </div>
            <div class="metric-value">
                {total_mailboxes}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with m2:

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">
                UNREAD FOUND
            </div>
            <div class="metric-value">
                {total_unread:,}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with m3:

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">
                FETCHED
            </div>
            <div class="metric-value">
                {total_fetched:,}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with m4:

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">
                MARKED SEEN
            </div>
            <div class="metric-value">
                {total_seen:,}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with m5:

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">
                FAILED
            </div>
            <div class="metric-value">
                {total_failed:,}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.write("")


# ============================================================
# SEARCH
# ============================================================

search_col, empty_col = st.columns(
    [2, 4]
)

with search_col:

    search_text = st.text_input(
        "Search mailbox",
        placeholder="🔎  Search email address...",
        label_visibility="collapsed",
    )


# ============================================================
# START / STOP
# ============================================================

start_col, stop_col, info_col = st.columns(
    [1, 1, 4]
)

with start_col:

    start_clicked = st.button(
        "▶ START PROCESSING",
        use_container_width=True,
        disabled=st.session_state.processing,
    )


with stop_col:

    stop_clicked = st.button(
        "🛑 STOP",
        use_container_width=True,
        disabled=not st.session_state.processing,
    )


if stop_clicked:

    st.session_state.stop_requested = True
    st.warning(
        "Stop requested. Current mailbox operation will finish first."
    )


# ============================================================
# START PROCESSING
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

        st.info(
            f"Starting processing for {len(accounts)} mailbox(es). "
            f"Maximum {MAX_MESSAGES_PER_MAILBOX:,} unread messages per mailbox."
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
                status_placeholder=mailbox_status,
            )

            st.session_state.results[
                account["email"]
            ] = result

            overall_progress.progress(
                account_number
                / len(accounts)
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
                "All mailboxes processed."
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

    st.markdown(
        """
        <div class="section-title">
            📈 Processing Results
        </div>

        <div class="section-subtitle">
            Latest processing information
        </div>
        """,
        unsafe_allow_html=True,
    )

    result_columns = st.columns(3)

    with result_columns[0]:

        st.metric(
            "Unread Found",
            f"{total_unread:,}"
        )

    with result_columns[1]:

        st.metric(
            "Fetched",
            f"{total_fetched:,}"
        )

    with result_columns[2]:

        st.metric(
            "Marked Seen",
            f"{total_seen:,}"
        )


# ============================================================
# MAILBOX LIST
# ============================================================

st.markdown(
    """
    <div class="section-title">
        📬 Mailboxes
    </div>

    <div class="section-subtitle">
        Select a mailbox to view its latest processed messages.
    </div>
    """,
    unsafe_allow_html=True,
)


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
                    f"""
                    <div class="mailbox-title">
                        📧 Mailbox {account["index"]}
                    </div>

                    <div class="mailbox-email">
                        {email_address}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if result:

                    if result.get("error"):

                        st.markdown(
                            """
                            <div class="mailbox-status">
                                ⚠️ Error
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                    else:

                        st.markdown(
                            f"""
                            <div class="mailbox-status">
                                ✓ Processed
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                    c1, c2 = st.columns(2)

                    with c1:

                        st.caption(
                            f"Unread: {result.get('unread_found', 0):,}"
                        )

                    with c2:

                        st.caption(
                            f"Seen: {result.get('seen', 0):,}"
                        )

                else:

                    st.markdown(
                        """
                        <div class="mailbox-status">
                            ○ Not processed
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                if st.button(
                    "▶ Open",
                    key=f"open_{account['index']}",
                    use_container_width=True,
                ):

                    st.session_state.selected_mailbox = (
                        email_address
                    )


# ============================================================
# SELECTED MAILBOX DETAILS
# ============================================================

selected = st.session_state.selected_mailbox

if selected:

    selected_result = st.session_state.results.get(
        selected
    )

    st.divider()

    st.markdown(
        f"""
        <div class="section-title">
            📩 {selected}
        </div>

        <div class="section-subtitle">
            Latest processed messages
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not selected_result:

        st.info(
            "This mailbox has not been processed yet."
        )

    elif selected_result.get("error"):

        st.error(
            selected_result["error"]
        )

    else:

        st.write(
            f"**Unread found:** "
            f"{selected_result.get('unread_found', 0):,}"
        )

        st.write(
            f"**Selected:** "
            f"{selected_result.get('selected', 0):,}"
        )

        st.write(
            f"**Fetched:** "
            f"{selected_result.get('fetched', 0):,}"
        )

        st.write(
            f"**Marked Seen:** "
            f"{selected_result.get('seen', 0):,}"
        )

        st.write(
            f"**Failed:** "
            f"{selected_result.get('failed', 0):,}"
        )

        latest = selected_result.get(
            "latest",
            []
        )

        if latest:

            for message in latest:

                with st.container(border=True):

                    st.markdown(
                        f"""
                        **From:** {message.get("from", "")}

                        **Subject:** {message.get("subject", "")}

                        **UID:** `{message.get("uid", "")}`
                        """
                    )

        else:

            st.info(
                "No processed messages to display."
            )


# ============================================================
# FOOTER
# ============================================================

st.write("")

st.markdown(
    """
    <div style="
        text-align:center;
        color:#9a9fb0;
        font-size:11px;
        padding-top:20px;
    ">
        Yahoo Mailbox Dashboard
    </div>
    """,
    unsafe_allow_html=True,
)
