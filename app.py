```python
import streamlit as st
import imaplib
import email
import os
import threading
from email.header import decode_header
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


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

# Maximum number of mailboxes processed simultaneously
MAX_PARALLEL_MAILBOXES = 10

MAX_LATEST_MESSAGES = 20


# =========================================================
# SESSION STATE
# =========================================================

defaults = {
    "logged_in": False,
    "processing": False,
    "stop_requested": False,
    "results": {},
    "selected_mailbox": None,
    "run_id": 0,
}

for key, value in defaults.items():

    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# GLOBAL STOP EVENT
# =========================================================

# IMPORTANT:
# This is NOT stored inside worker logic.
# Workers receive this Event directly.

if "stop_event" not in st.session_state:
    st.session_state.stop_event = threading.Event()


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
        margin: 70px auto 25px auto;
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

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# HELPERS
# =========================================================

def now_string():

    return datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def decode_mime(value):

    if not value:
        return ""

    try:

        parts = decode_header(value)

        output = ""

        for part, encoding in parts:

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


# =========================================================
# LOAD YAHOO ACCOUNTS
# =========================================================

def load_accounts():

    accounts = []

    for i in range(1, 101):

        email_address = os.getenv(
            f"YAHOO_EMAIL_{i}"
        )

        app_password = os.getenv(
            f"YAHOO_APP_PASSWORD_{i}"
        )

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
# EMPTY RESULT
# =========================================================

def create_empty_result(email_address):

    return {
        "email": email_address,
        "unread_found": 0,
        "selected": 0,
        "fetched": 0,
        "seen": 0,
        "failed": 0,
        "error": "",
        "latest": [],
        "started": now_string(),
        "finished": "",
        "stopped": False,
    }


# =========================================================
# PROCESS ONE MAILBOX
# =========================================================

def check_mailbox(account, stop_event):

    email_address = account["email"]
    password = account["password"]

    result = create_empty_result(
        email_address
    )

    mail = None

    try:

        # =================================================
        # STOP BEFORE CONNECT
        # =================================================

        if stop_event.is_set():

            result["stopped"] = True
            result["finished"] = now_string()

            return result


        # =================================================
        # CONNECT
        # =================================================

        mail = imaplib.IMAP4_SSL(
            IMAP_SERVER,
            IMAP_PORT,
            timeout=30
        )


        # =================================================
        # STOP CHECK
        # =================================================

        if stop_event.is_set():

            result["stopped"] = True
            result["finished"] = now_string()

            return result


        # =================================================
        # LOGIN
        # =================================================

        mail.login(
            email_address,
            password
        )


        # =================================================
        # STOP CHECK
        # =================================================

        if stop_event.is_set():

            result["stopped"] = True
            result["finished"] = now_string()

            return result


        # =================================================
        # SELECT INBOX
        # =================================================

        status, _ = mail.select(
            "INBOX"
        )

        if status != "OK":

            raise Exception(
                "Unable to select INBOX"
            )


        # =================================================
        # SEARCH UNSEEN
        # =================================================

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

        result["unread_found"] = len(
            uid_list
        )


        # =================================================
        # LIMIT
        # =================================================

        selected_uids = uid_list[
            :MAX_MESSAGES_PER_MAILBOX
        ]

        result["selected"] = len(
            selected_uids
        )


        # =================================================
        # NO UNREAD
        # =================================================

        if not selected_uids:

            result["finished"] = now_string()

            return result


        # =================================================
        # PROCESS MESSAGES
        # =================================================

        for uid in selected_uids:

            # ---------------------------------------------
            # STOP CHECK
            # ---------------------------------------------

            if stop_event.is_set():

                result["stopped"] = True

                break


            try:

                # -----------------------------------------
                # FETCH MESSAGE
                # -----------------------------------------

                fetch_status, msg_data = mail.uid(
                    "fetch",
                    uid,
                    "(RFC822)"
                )

                if fetch_status != "OK":

                    result["failed"] += 1

                    continue


                # -----------------------------------------
                # EXTRACT RAW MESSAGE
                # -----------------------------------------

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
                    msg.get(
                        "Subject",
                        ""
                    )
                )


                sender = decode_mime(
                    msg.get(
                        "From",
                        ""
                    )
                )


                # -----------------------------------------
                # FETCH COUNT
                # -----------------------------------------

                result["fetched"] += 1


                # -----------------------------------------
                # MARK SEEN
                # -----------------------------------------

                if stop_event.is_set():

                    result["stopped"] = True

                    break


                seen_status, _ = mail.uid(
                    "store",
                    uid,
                    "+FLAGS",
                    "(\\Seen)"
                )


                if seen_status == "OK":

                    result["seen"] += 1


                # -----------------------------------------
                # SAVE LATEST
                # -----------------------------------------

                if len(
                    result["latest"]
                ) < MAX_LATEST_MESSAGES:

                    result["latest"].append(
                        {
                            "subject":
                                subject
                                if subject
                                else "(No Subject)",

                            "from":
                                sender
                                if sender
                                else "(Unknown Sender)"
                        }
                    )


            except Exception:

                result["failed"] += 1

                continue


        # =================================================
        # FINISH
        # =================================================

        result["finished"] = now_string()

        return result


    except Exception as exc:

        result["error"] = str(exc)

        result["finished"] = now_string()

        return result


    finally:

        # =================================================
        # CLOSE IMAP
        # =================================================

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

            <div class="login-icon">
                📬
            </div>

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
        "Username"
    )


    password = st.text_input(
        "Password",
        type="password"
    )


    if st.button(
        "🔐 LOGIN",
        use_container_width=True
    ):

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

st.title(
    "📬 Yahoo Mailbox Dashboard"
)

st.caption(
    "Manage your configured Yahoo mailboxes"
)


# =========================================================
# CONTROL BUTTONS
# =========================================================

c1, c2, c3 = st.columns(
    [2, 1, 1]
)


# =========================================================
# START BUTTON
# =========================================================

with c1:

    start_clicked = st.button(
        "▶ START PROCESSING",
        use_container_width=True,
        disabled=st.session_state.processing
    )


# =========================================================
# STOP BUTTON
# =========================================================

with c2:

    stop_clicked = st.button(
        "🛑 STOP",
        use_container_width=True,
        disabled=not st.session_state.processing
    )


# =========================================================
# LOGOUT BUTTON
# =========================================================

with c3:

    logout_clicked = st.button(
        "🚪 LOGOUT",
        use_container_width=True
    )


# =========================================================
# LOGOUT
# =========================================================

if logout_clicked:

    st.session_state.stop_event.set()

    st.session_state.processing = False

    st.session_state.stop_requested = True

    st.session_state.logged_in = False

    st.session_state.selected_mailbox = None

    st.rerun()


# =========================================================
# STOP
# =========================================================

if stop_clicked:

    st.session_state.stop_requested = True

    st.session_state.stop_event.set()

    st.warning(
        "🛑 Stop requested. Running mailbox tasks "
        "will stop at the next safe point."
    )


# =========================================================
# START PROCESSING
# =========================================================

if start_clicked:

    # =====================================================
    # SAFETY CHECK
    # =====================================================

    if st.session_state.processing:

        st.warning(
            "Processing is already running."
        )

    elif not accounts:

        st.error(
            "No Yahoo mailboxes configured."
        )

    else:

        # =================================================
        # NEW RUN
        # =================================================

        st.session_state.run_id += 1

        current_run_id = (
            st.session_state.run_id
        )

        # Clear previous stop signal
        st.session_state.stop_event.clear()

        st.session_state.stop_requested = False

        st.session_state.processing = True


        # =================================================
        # FIND PENDING ACCOUNTS
        # =================================================

        pending_accounts = []

        for account in accounts:

            email_address = account[
                "email"
            ]

            old_result = (
                st.session_state.results.get(
                    email_address
                )
            )


            # ---------------------------------------------
            # SKIP SUCCESSFULLY COMPLETED
            # ---------------------------------------------

            if (
                old_result
                and old_result.get("finished")
                and not old_result.get("stopped")
                and not old_result.get("error")
            ):

                continue


            pending_accounts.append(
                account
            )


        # =================================================
        # NOTHING TO PROCESS
        # =================================================

        if not pending_accounts:

            st.session_state.processing = False

            st.success(
                "✅ All configured mailboxes are already processed."
            )

        else:

            total_pending = len(
                pending_accounts
            )

            st.info(
                f"⚡ Processing {total_pending} mailboxes "
                f"using up to {MAX_PARALLEL_MAILBOXES} "
                f"parallel connections."
            )


            overall_progress = st.progress(
                0
            )


            status_text = st.empty()


            completed_count = 0


            # =================================================
            # THREAD POOL
            # =================================================

            with ThreadPoolExecutor(
                max_workers=MAX_PARALLEL_MAILBOXES
            ) as executor:


                future_map = {}


                # =================================================
                # SUBMIT TASKS
                # =================================================

                for account in pending_accounts:

                    # Do NOT submit more work after stop
                    if st.session_state.stop_event.is_set():

                        break


                    future = executor.submit(
                        check_mailbox,
                        account,
                        st.session_state.stop_event
                    )


                    future_map[
                        future
                    ] = account


                # =================================================
                # COLLECT COMPLETED TASKS
                # =================================================

                for future in as_completed(
                    future_map
                ):

                    account = future_map[
                        future
                    ]

                    email_address = account[
                        "email"
                    ]


                    try:

                        result = future.result()


                    except Exception as exc:

                        result = create_empty_result(
                            email_address
                        )

                        result["error"] = str(
                            exc
                        )

                        result["finished"] = (
                            now_string()
                        )


                    # =============================================
                    # SAVE RESULT
                    # =============================================

                    st.session_state.results[
                        email_address
                    ] = result


                    completed_count += 1


                    # =============================================
                    # PROGRESS
                    # =============================================

                    progress_value = (
                        completed_count
                        / total_pending
                    )


                    overall_progress.progress(
                        progress_value
                    )


                    status_text.info(
                        f"⚡ Completed "
                        f"{completed_count}/"
                        f"{total_pending} — "
                        f"{email_address}"
                    )


                    # =============================================
                    # STOP CHECK
                    # =============================================

                    if st.session_state.stop_event.is_set():

                        # Do not submit new tasks.
                        # Already-running tasks will notice
                        # stop_event and finish safely.

                        continue


            # =================================================
            # PROCESSING FINISHED
            # =================================================

            st.session_state.processing = False


            # =================================================
            # STOPPED
            # =================================================

            if (
                st.session_state.stop_event.is_set()
                or st.session_state.stop_requested
            ):

                st.session_state.stop_requested = True

                st.warning(
                    "🛑 Processing stopped. "
                    "Completed mailbox results are saved."
                )


            # =================================================
            # COMPLETED
            # =================================================

            else:

                st.session_state.stop_requested = False

                st.success(
                    "✅ Parallel processing completed."
                )


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

mailboxes_count = len(
    accounts
)


unread_total = sum(
    r.get(
        "unread_found",
        0
    )
    for r in st.session_state.results.values()
)


fetched_total = sum(
    r.get(
        "fetched",
        0
    )
    for r in st.session_state.results.values()
)


seen_total = sum(
    r.get(
        "seen",
        0
    )
    for r in st.session_state.results.values()
)


failed_total = sum(
    r.get(
        "failed",
        0
    )
    for r in st.session_state.results.values()
)


# =========================================================
# METRIC DISPLAY
# =========================================================

m1, m2, m3, m4, m5 = st.columns(
    5
)


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
# STATUS
# =========================================================

if st.session_state.processing:

    st.info(
        "⏳ Parallel processing is running..."
    )

elif st.session_state.stop_requested:

    st.warning(
        "🛑 Processing was stopped."
    )

elif st.session_state.results:

    st.success(
        "✅ Processing is not running."
    )


# =========================================================
# MAILBOX LIST
# =========================================================

st.divider()

st.subheader(
    "📮 Mailboxes"
)


if not accounts:

    st.warning(
        "No Yahoo mailboxes configured "
        "in Render environment variables."
    )

else:

    for account in accounts:

        email_address = account[
            "email"
        ]


        # =================================================
        # SEARCH FILTER
        # =================================================

        if (
            search_text
            and search_text.lower()
            not in email_address.lower()
        ):

            continue


        result = (
            st.session_state.results.get(
                email_address
            )
        )


        with st.container(
            border=True
        ):

            c1, c2 = st.columns(
                [4, 1]
            )


            # =================================================
            # MAILBOX INFO
            # =================================================

            with c1:

                st.markdown(
                    f"### 📧 {email_address}"
                )


                if result:

                    if result.get(
                        "stopped"
                    ):

                        st.warning(
                            "⏸ Processing stopped"
                        )


                    elif result.get(
                        "error"
                    ):

                        st.error(
                            "❌ Error: "
                            + result["error"]
                        )


                    else:

                        st.success(
                            "✅ Processed"
                        )


                    st.write(
                        f"Unread: "
                        f"**{result.get('unread_found', 0)}**  |  "
                        f"Fetched: "
                        f"**{result.get('fetched', 0)}**  |  "
                        f"Seen: "
                        f"**{result.get('seen', 0)}**  |  "
                        f"Failed: "
                        f"**{result.get('failed', 0)}**"
                    )


                    if result.get(
                        "finished"
                    ):

                        st.caption(
                            "Finished: "
                            + result["finished"]
                        )


                else:

                    st.info(
                        "Not processed yet."
                    )


            # =================================================
            # INDIVIDUAL PROCESS BUTTON
            # =================================================

            with c2:

                open_clicked = st.button(
                    "▶ Open / Process",
                    key=f"open_{account['index']}",
                    use_container_width=True,
                    disabled=st.session_state.processing
                )


                if open_clicked:

                    # -----------------------------------------
                    # RESET STOP EVENT
                    # -----------------------------------------

                    st.session_state.stop_event.clear()

                    st.session_state.stop_requested = False

                    st.session_state.selected_mailbox = (
                        email_address
                    )


                    # -----------------------------------------
                    # PROCESS
                    # -----------------------------------------

                    with st.spinner(
                        f"Processing {email_address}..."
                    ):

                        result = check_mailbox(
                            account,
                            st.session_state.stop_event
                        )


                    # -----------------------------------------
                    # SAVE
                    # -----------------------------------------

                    st.session_state.results[
                        email_address
                    ] = result


                    st.rerun()


# =========================================================
# SELECTED MAILBOX
# =========================================================

selected = (
    st.session_state.selected_mailbox
)


if selected:

    selected_result = (
        st.session_state.results.get(
            selected
        )
    )


    if selected_result:

        st.divider()

        st.subheader(
            f"📧 {selected}"
        )


        d1, d2, d3, d4 = st.columns(
            4
        )


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


        # =================================================
        # ERROR
        # =================================================

        if selected_result.get(
            "error"
        ):

            st.error(
                selected_result["error"]
            )


        # =================================================
        # STOPPED
        # =================================================

        if selected_result.get(
            "stopped"
        ):

            st.warning(
                "Processing was stopped."
            )


        # =================================================
        # LATEST MESSAGES
        # =================================================

        latest = selected_result.get(
            "latest",
            []
        )


        if latest:

            st.subheader(
                "📨 Latest Processed Messages"
            )


            for message in latest:

                with st.container(
                    border=True
                ):

                    st.write(
                        "**Subject:** "
                        + message.get(
                            "subject",
                            "(No Subject)"
                        )
                    )


                    st.write(
                        "**From:** "
                        + message.get(
                            "from",
                            "(Unknown Sender)"
                        )
                    )


        else:

            st.info(
                "No messages were processed."
            )
```
