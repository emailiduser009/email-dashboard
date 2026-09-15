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

    /* =========================
       GLOBAL
       ========================= */

    .stApp {
        background:
            radial-gradient(
                circle at 10% 10%,
                rgba(109, 93, 252, 0.10),
                transparent 28%
            ),
            radial-gradient(
                circle at 90% 15%,
                rgba(76, 139, 245, 0.09),
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


    /* =========================
       LOGIN
       ========================= */

    .login-space {
        height: 6vh;
    }

    .login-marker {
        display: none;
    }

    [data-testid="stVerticalBlockBorderWrapper"]:has(.login-marker) {
        max-width: 470px;
        margin-left: auto;
        margin-right: auto;

        padding: 32px 34px 30px 34px;

        border-radius: 24px;

        border: 1px solid rgba(120, 130, 160, 0.20);

        background: rgba(255, 255, 255, 0.96);

        box-shadow:
            0 25px 70px rgba(25, 35, 65, 0.12),
            0 5px 20px rgba(25, 35, 65, 0.05);

        backdrop-filter: blur(12px);
    }

    .login-logo {
        width: 68px;
        height: 68px;

        margin: 0 auto 17px auto;

        border-radius: 19px;

        display: flex;
        align-items: center;
        justify-content: center;

        font-size: 32px;

        background:
            linear-gradient(
                135deg,
                #6d5dfc,
                #4c8bf5
            );

        box-shadow:
            0 12px 30px rgba(88, 82, 220, 0.25);
    }

    .login-title {
        text-align: center;

        font-size: 27px;
        font-weight: 750;

        color: #20243a;

        letter-spacing: -0.5px;

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
        font-size: 13px !important;
        font-weight: 650 !important;
    }

    [data-testid="stVerticalBlockBorderWrapper"]:has(.login-marker) input {
        min-height: 45px !important;

        border-radius: 11px !important;

        border: 1px solid #dce0ea !important;

        background: #fafbfe !important;

        padding-left: 13px !important;
    }

    [data-testid="stVerticalBlockBorderWrapper"]:has(.login-marker)
    input:focus {
        border-color: #6d5dfc !important;

        box-shadow:
            0 0 0 2px rgba(109, 93, 252, 0.10) !important;
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

    [data-testid="stFormSubmitButton"] button:hover {
        transform: translateY(-1px);

        box-shadow:
            0 11px 28px rgba(88, 82, 220, 0.30) !important;
    }

    .login-note {
        text-align: center;

        color: #9a9fb0;

        font-size: 11px;

        margin-top: 15px;
    }


    /* =========================
       DASHBOARD HEADER
       ========================= */

    .dashboard-header {
        display: flex;

        align-items: center;

        gap: 15px;

        padding: 22px 25px;

        border-radius: 20px;

        background: rgba(255, 255, 255, 0.95);

        border: 1px solid rgba(120, 130, 160, 0.17);

        box-shadow:
            0 10px 30px rgba(25, 35, 65, 0.06);

        margin-bottom: 22px;
    }

    .dashboard-icon {
        width: 55px;
        height: 55px;

        flex-shrink: 0;

        border-radius: 16px;

        display: flex;
        align-items: center;
        justify-content: center;

        font-size: 28px;

        background:
            linear-gradient(
                135deg,
                #6d5dfc,
                #4c8bf5
            );

        box-shadow:
            0 10px 25px rgba(88, 82, 220, 0.20);
    }

    .dashboard-title {
        font-size: 26px;

        font-weight: 750;

        color: #20243a;

        line-height: 1.2;

        letter-spacing: -0.5px;
    }

    .dashboard-subtitle {
        font-size: 13px;

        color: #7b8193;

        margin-top: 4px;
    }


    /* =========================
       SECTION
       ========================= */

    .section-title {
        font-size: 19px;

        font-weight: 720;

        color: #292d40;

        margin-top: 10px;

        margin-bottom: 3px;
    }

    .section-subtitle {
        font-size: 12px;

        color: #858b9d;

        margin-bottom: 13px;
    }


    /* =========================
       METRIC CARDS
       ========================= */

    .metric-card {
        min-height: 105px;

        padding: 18px 20px;

        border-radius: 17px;

        background: rgba(255, 255, 255, 0.94);

        border: 1px solid rgba(120, 130, 160, 0.16);

        box-shadow:
            0 7px 22px rgba(25, 35, 65, 0.05);
    }

    .metric-label {
        color: #858b9d;

        font-size: 11px;

        font-weight: 650;

        letter-spacing: 0.3px;

        margin-bottom: 8px;
    }

    .metric-value {
        color: #25293c;

        font-size: 27px;

        font-weight: 750;

        line-height: 1;
    }


    /* =========================
       MAILBOX CARDS
       ========================= */

    [data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 17px;

        border-color: rgba(120, 130, 160, 0.17);

        background: rgba(255, 255, 255, 0.92);

        box-shadow:
            0 6px 20px rgba(25, 35, 65, 0.045);
    }

    .mailbox-title {
        color: #2d3144;

        font-size: 15px;

        font-weight: 700;

        margin-bottom: 3px;
    }

    .mailbox-email {
        color: #808699;

        font-size: 12px;

        word-break: break-all;
    }

    .mailbox-status {
        display: inline-block;

        margin-top: 8px;

        padding: 4px 9px;

        border-radius: 20px;

        background: #f0f2f8;

        color: #626a7f;

        font-size: 10px;

        font-weight: 650;
    }


    /* =========================
       BUTTONS
       ========================= */

    .stButton > button {
        min-height: 40px !important;

        border-radius: 10px !important;

        border: 1px solid #dce0ea !important;

        background: #ffffff !important;

        color: #34394c !important;

        font-weight: 650 !important;

        transition: all 0.18s ease !important;
    }

    .stButton > button:hover {
        border-color: #6d5dfc !important;

        color: #5b4ce0 !important;

        box-shadow:
            0 5px 16px rgba(80, 70, 200, 0.10) !important;
    }


    /* =========================
       INPUT
       ========================= */

    .stTextInput input {
        min-height: 42px !important;

        border-radius: 10px !important;

        border: 1px solid #dce0ea !important;

        background: rgba(255, 255, 255, 0.95) !important;
    }


    /* =========================
       ALERTS
       ========================= */

    .stAlert {
        border-radius: 12px !important;
    }


    /* =========================
       MOBILE
       ========================= */

    @media (max-width: 700px) {

        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }

        .dashboard-title {
            font-size: 22px;
        }

        .dashboard-header {
            padding: 19px;
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

    st.markdown(
        '<div class="login-space"></div>',
        unsafe_allow_html=True
    )

    left, center, right = st.columns(
        [1, 1.15, 1]
    )

    with center:

        with st.container(border=True):

            st.markdown(
                '<div class="login-marker"></div>',
                unsafe_allow_html=True
            )

            st.markdown(
                """
                <div class="login-logo">
                    📬
                </div>

                <div class="login-title">
                    Mailbox Dashboard
                </div>

                <div class="login-subtitle">
                    Sign in to manage your Yahoo mailboxes
                </div>
                """,
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
                """
                <div class="login-note">
                    Secure dashboard access
                </div>
                """,
                unsafe_allow_html=True
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
# PROCESS MAILBOX
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

        "finished": ""
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
        # MAX 2000
        # ----------------------------------------------------

        selected_uids = all_uids[
            :MAX_MESSAGES_PER_MAILBOX
        ]

        result["selected"] = len(
            selected_uids
        )


        # ----------------------------------------------------
        # FETCH
        # ----------------------------------------------------

        for position, uid in enumerate(
            selected_uids,
            start=1
        ):

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
                # MARK SEEN
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
                # LATEST 20
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
                        position
                        / max(
                            len(selected_uids),
                            1
                        )
                    )


                if status_placeholder:

                    status_placeholder.info(
                        f"Processing {email_address} "
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
# LOAD MAILBOXES
# ============================================================

accounts = load_accounts()


# ============================================================
# DASHBOARD HEADER
# ============================================================

st.markdown(
    """
    <div class="dashboard-header">

        <div class="dashboard-icon">
            📬
        </div>

        <div>

            <div class="dashboard-title">
                Yahoo Mailbox Dashboard
            </div>

            <div class="dashboard-subtitle">
                Manage your configured Yahoo mailboxes
            </div>

        </div>

    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# TOP BAR
# ============================================================

top_left, top_middle, top_right = st.columns(
    [3, 4, 1]
)


with top_left:

    st.markdown(
        """
        <div class="section-title">
            📊 Mailbox Overview
        </div>

        <div class="section-subtitle">
            Monitor your configured mailboxes
        </div>
        """,
        unsafe_allow_html=True
    )


with top_right:

    if st.button(
        "🚪 Logout",
        use_container_width=True
    ):

        st.session_state.logged_in = False

        st.session_state.stop_requested = False

        st.session_state.processing = False

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
# METRIC CARDS
# ============================================================

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
        unsafe_allow_html=True
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
        unsafe_allow_html=True
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
        unsafe_allow_html=True
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
        unsafe_allow_html=True
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
        unsafe_allow_html=True
    )


st.write("")


# ============================================================
# SEARCH
# ============================================================

search_col, blank_col = st.columns(
    [2, 5]
)

with search_col:

    search_text = st.text_input(
        "Search",
        placeholder="🔎  Search mailbox...",
        label_visibility="collapsed"
    )


# ============================================================
# START / STOP
# ============================================================

start_col, stop_col, status_col = st.columns(
    [1.3, 1, 4]
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
            f"Processing {len(accounts)} mailbox(es). "
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

                status_placeholder=mailbox_status
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
# RESULTS
# ============================================================

if st.session_state.results:

    st.markdown(
        """
        <div class="section-title">
            📈 Processing Results
        </div>

        <div class="section-subtitle">
            Current processing summary
        </div>
        """,
        unsafe_allow_html=True
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

st.markdown(
    """
    <div class="section-title">
        📬 Mailboxes
    </div>

    <div class="section-subtitle">
        Select a mailbox to view its latest processed messages.
    </div>
    """,
    unsafe_allow_html=True
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
                    f"""
                    <div class="mailbox-title">
                        📧 Mailbox {account["index"]}
                    </div>

                    <div class="mailbox-email">
                        {email_address}
                    </div>
                    """,
                    unsafe_allow_html=True
                )


                if result:

                    if result.get("error"):

                        st.markdown(
                            """
                            <div class="mailbox-status">
                                ⚠️ Error
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    else:

                        st.markdown(
                            """
                            <div class="mailbox-status">
                                ✓ Processed
                            </div>
                            """,
                            unsafe_allow_html=True
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

                    st.markdown(
                        """
                        <div class="mailbox-status">
                            ○ Not processed
                        </div>
                        """,
                        unsafe_allow_html=True
                    )


                if st.button(
                    "▶ Open",
                    key=f"open_{account['index']}",
                    use_container_width=True
                ):

                    st.session_state.selected_mailbox = (
                        email_address
                    )


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


    st.markdown(
        f"""
        <div class="section-title">
            📩 {selected_mailbox}
        </div>

        <div class="section-subtitle">
            Latest processed messages
        </div>
        """,
        unsafe_allow_html=True
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

st.markdown(
    """
    <div style="
        text-align:center;
        color:#9a9fb0;
        font-size:11px;
        padding-top:25px;
    ">
        Yahoo Mailbox Dashboard
    </div>
    """,
    unsafe_allow_html=True
)
