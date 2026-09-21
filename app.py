import streamlit as st
import imaplib
import email
import os
import re
import json
import copy
import time
import hmac
import secrets
import threading
from email.header import decode_header
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor


# =========================================================
# PAGE CONFIG  (must be the first Streamlit call)
# =========================================================

st.set_page_config(
    page_title="Yahoo Mailbox Dashboard",
    page_icon="📬",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =========================================================
# SETTINGS
# =========================================================

IMAP_SERVER = "imap.mail.yahoo.com"
IMAP_PORT = 993

MAX_MESSAGES_PER_MAILBOX = 2000

# How many Yahoo mailboxes run at the same time.
# If Yahoo starts rejecting logins, lower this (e.g. 5).
MAX_PARALLEL_MAILBOXES = int(os.getenv("MAX_PARALLEL_MAILBOXES", "10"))

MAX_LATEST_MESSAGES = 20

# Messages fetched / marked seen per IMAP command
CHUNK_SIZE = 50

# Seconds before a hung IMAP socket raises an error
SOCKET_TIMEOUT = 60

# Auto-reconnect attempts per mailbox if the connection drops
MAX_RECONNECTS = 3

# False = download only From/Subject headers (very fast) and then mark as Seen
# True  = download the full message (slow, heavy)
FETCH_FULL_MESSAGE = False

# Dashboard auto-refresh interval (seconds)
REFRESH_SECONDS = 2

# Results are saved here so they survive page refresh / app restart
RESULTS_FILE = os.getenv("RESULTS_FILE", "mailbox_results.json")

# Login stays valid after a browser refresh for this many hours
SESSION_HOURS = 12

FETCH_SPEC = (
    "(UID RFC822)"
    if FETCH_FULL_MESSAGE
    else "(UID BODY.PEEK[HEADER.FIELDS (FROM SUBJECT)])"
)

UID_RE = re.compile(rb"UID (\d+)")


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    .login-icon {
        font-size: 46px;
        text-align: center;
        margin-top: 60px;
        line-height: 1.2;
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
        margin-bottom: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# HELPERS
# =========================================================

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def decode_mime(value):
    if not value:
        return ""

    try:
        output = ""

        for part, encoding in decode_header(value):
            if isinstance(part, bytes):
                try:
                    output += part.decode(encoding or "utf-8", errors="replace")
                except LookupError:
                    output += part.decode("utf-8", errors="replace")
            else:
                output += str(part)

        return output

    except Exception:
        return str(value)


def new_result(email_address, state="queued"):
    return {
        "email": email_address,
        "state": state,  # queued | running | done | stopped | error
        "unread_found": 0,
        "selected": 0,
        "fetched": 0,
        "seen": 0,
        "failed": 0,
        "error": "",
        "latest": [],
        "started": "",
        "finished": "",
        "stopped": False,
    }


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
                    "password": app_password.strip(),
                }
            )

    return accounts


# =========================================================
# IMAP WORK  (runs in background threads, no Streamlit calls)
# =========================================================

def imap_connect(email_address, password):
    mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT, timeout=SOCKET_TIMEOUT)

    try:
        mail.login(email_address, password)

        status, _ = mail.select("INBOX")

        if status != "OK":
            raise RuntimeError("Unable to select INBOX")

    except Exception:
        try:
            mail.logout()
        except Exception:
            pass
        raise

    return mail


def safe_logout(mail):
    if not mail:
        return

    try:
        mail.close()
    except Exception:
        pass

    try:
        mail.logout()
    except Exception:
        pass


def find_uid(*candidates):
    for c in candidates:
        if isinstance(c, (bytes, bytearray)):
            m = UID_RE.search(c)
            if m:
                return m.group(1)
    return None


def process_chunk(mail, chunk):
    """
    Fetch one batch of UIDs and mark them Seen.
    Returns (fetched, seen, failed, latest_items).
    Connection errors are raised so the caller can reconnect and retry.
    """

    uid_set = b",".join(chunk).decode()

    fetch_status, msg_data = mail.uid("fetch", uid_set, FETCH_SPEC)

    if fetch_status != "OK" or not msg_data:
        return 0, 0, len(chunk), []

    fetched_uids = []
    latest = []

    for i, item in enumerate(msg_data):

        if not isinstance(item, tuple):
            continue

        # UID is normally in the first part, but some servers
        # put it in the trailing element after the body.
        next_item = msg_data[i + 1] if i + 1 < len(msg_data) else None
        uid = find_uid(item[0], next_item)

        raw_message = item[1]

        if not uid or not raw_message:
            continue

        try:
            msg = email.message_from_bytes(raw_message)
            subject = decode_mime(msg.get("Subject", ""))
            sender = decode_mime(msg.get("From", ""))
        except Exception:
            subject = ""
            sender = ""

        fetched_uids.append(uid)

        latest.append(
            {
                "subject": subject if subject else "(No Subject)",
                "from": sender if sender else "(Unknown Sender)",
            }
        )

    seen = 0

    if fetched_uids:
        seen_status, _ = mail.uid(
            "store",
            b",".join(fetched_uids).decode(),
            "+FLAGS",
            "(\\Seen)",
        )

        if seen_status == "OK":
            seen = len(fetched_uids)

    failed = len(chunk) - len(fetched_uids)

    return len(fetched_uids), seen, failed, latest


def check_mailbox(account, stop_event, result, publish):
    """
    Process one mailbox. Mutates `result` and calls publish(result)
    after each batch so the dashboard can show live progress.
    """

    email_address = account["email"]
    password = account["password"]

    result["state"] = "running"
    result["started"] = now()
    result["stopped"] = False
    result["error"] = ""
    publish(result)

    mail = None

    try:
        mail = imap_connect(email_address, password)

        status, data = mail.uid("search", None, "UNSEEN")

        if status != "OK":
            raise RuntimeError("Unable to search UNSEEN messages")

        uid_list = data[0].split() if data and data[0] else []

        result["unread_found"] = len(uid_list)

        selected_uids = uid_list[:MAX_MESSAGES_PER_MAILBOX]

        result["selected"] = len(selected_uids)
        publish(result)

        reconnects = 0
        index = 0

        while index < len(selected_uids):

            if stop_event.is_set():
                result["stopped"] = True
                break

            chunk = selected_uids[index:index + CHUNK_SIZE]

            try:
                fetched, seen, failed, latest = process_chunk(mail, chunk)

            except (imaplib.IMAP4.abort, OSError) as exc:
                # Connection dropped / timed out -> reconnect and retry chunk
                reconnects += 1

                if reconnects > MAX_RECONNECTS:
                    raise RuntimeError(
                        f"Connection lost repeatedly: {exc}"
                    )

                safe_logout(mail)
                mail = None

                time.sleep(2 * reconnects)

                mail = imap_connect(email_address, password)

                continue

            result["fetched"] += fetched
            result["seen"] += seen
            result["failed"] += failed

            for item in latest:
                if len(result["latest"]) < MAX_LATEST_MESSAGES:
                    result["latest"].append(item)

            index += len(chunk)

            publish(result)

        result["state"] = "stopped" if result["stopped"] else "done"

    except Exception as exc:
        result["state"] = "error"
        result["error"] = str(exc)

    finally:
        result["finished"] = now()
        safe_logout(mail)
        publish(result)


# =========================================================
# BACKGROUND JOB MANAGER
#
# Lives at process level (st.cache_resource), NOT inside a
# browser session. So refreshing the page, clicking buttons,
# or logging out never interrupts running mailbox jobs.
# =========================================================

class JobManager:

    def __init__(self):
        self.lock = threading.RLock()
        self.stop_event = threading.Event()
        self.executor = ThreadPoolExecutor(
            max_workers=MAX_PARALLEL_MAILBOXES,
            thread_name_prefix="mailbox",
        )
        self.results = {}
        self.active = set()
        self.tokens = {}
        self._load()

    # ---------- persistence ----------

    def _load(self):
        try:
            if os.path.exists(RESULTS_FILE):
                with open(RESULTS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    self.results = data
        except Exception:
            self.results = {}

    def _save(self):
        try:
            with self.lock:
                data = {
                    k: v
                    for k, v in self.results.items()
                    if v.get("state") in ("done", "stopped", "error")
                }
                tmp = RESULTS_FILE + ".tmp"
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump(data, f)
                os.replace(tmp, RESULTS_FILE)
        except Exception:
            pass

    # ---------- state ----------

    def _publish(self, result):
        with self.lock:
            self.results[result["email"]] = copy.deepcopy(result)

    def snapshot(self):
        with self.lock:
            return copy.deepcopy(self.results), set(self.active)

    def request_stop(self):
        self.stop_event.set()

    def clear_results(self):
        with self.lock:
            if self.active:
                return False
            self.results = {}
        self._save()
        return True

    # ---------- jobs ----------

    def start(self, accounts, only_pending=True):
        queued = 0

        with self.lock:

            # Safe to reset the stop signal only when nothing is running
            if not self.active:
                self.stop_event.clear()

            for account in accounts:
                email_address = account["email"]

                if email_address in self.active:
                    continue

                old = self.results.get(email_address)

                if only_pending and old and old.get("state") == "done":
                    continue

                self.results[email_address] = new_result(email_address, "queued")
                self.active.add(email_address)
                self.executor.submit(self._run, account)
                queued += 1

        return queued

    def _run(self, account):
        email_address = account["email"]
        result = new_result(email_address, "queued")

        try:
            if self.stop_event.is_set():
                result["state"] = "stopped"
                result["stopped"] = True
                result["finished"] = now()
                self._publish(result)
            else:
                check_mailbox(
                    account,
                    self.stop_event,
                    result,
                    self._publish,
                )

        except Exception as exc:
            result["state"] = "error"
            result["error"] = str(exc)
            result["finished"] = now()
            self._publish(result)

        finally:
            with self.lock:
                self.active.discard(email_address)
            self._save()

    # ---------- login tokens (survive browser refresh) ----------

    def create_token(self):
        token = secrets.token_urlsafe(24)
        with self.lock:
            t = time.time()
            self.tokens = {k: v for k, v in self.tokens.items() if v > t}
            self.tokens[token] = t + SESSION_HOURS * 3600
        return token

    def validate_token(self, token):
        with self.lock:
            expiry = self.tokens.get(token)
            return bool(expiry and expiry > time.time())

    def revoke_token(self, token):
        with self.lock:
            self.tokens.pop(token, None)


@st.cache_resource
def get_manager():
    return JobManager()


mgr = get_manager()


# =========================================================
# SESSION STATE
# =========================================================

for key, value in {
    "logged_in": False,
    "selected_mailbox": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# AUTH
# =========================================================

def is_authenticated():
    if st.session_state.logged_in:
        return True

    token = st.query_params.get("auth")

    if token and mgr.validate_token(token):
        st.session_state.logged_in = True
        return True

    return False


def render_login():
    _, middle, _ = st.columns([1, 1.2, 1])

    with middle:

        st.markdown(
            """
            <div class="login-icon">📬</div>
            <div class="login-title">Mailbox Dashboard</div>
            <div class="login-subtitle">
                Sign in to manage your Yahoo mailboxes
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("login_form"):

            username = st.text_input("Username")
            password = st.text_input("Password", type="password")

            submitted = st.form_submit_button(
                "🔐 LOGIN",
                use_container_width=True,
            )

        if submitted:

            dashboard_username = os.getenv("DASHBOARD_USERNAME")
            dashboard_password = os.getenv("DASHBOARD_PASSWORD")

            if not dashboard_username or not dashboard_password:
                st.error(
                    "DASHBOARD_USERNAME / DASHBOARD_PASSWORD "
                    "environment variables are not set."
                )

            elif (
                hmac.compare_digest(username.encode(), dashboard_username.encode())
                and hmac.compare_digest(password.encode(), dashboard_password.encode())
            ):
                st.session_state.logged_in = True
                st.query_params["auth"] = mgr.create_token()
                st.rerun()

            else:
                st.error("Invalid username or password.")


if not is_authenticated():
    render_login()
    st.stop()


# =========================================================
# LOAD ACCOUNTS
# =========================================================

accounts = load_accounts()


# =========================================================
# UI PIECES
# =========================================================

def render_status(result):
    if not result:
        st.info("Not processed yet.")
        return

    state = result.get("state", "done")

    if state == "queued":
        st.info("🕒 Queued")

    elif state == "running":
        st.info(
            f"⏳ Processing... "
            f"{result.get('fetched', 0)} / {result.get('selected', 0)}"
        )

    elif state == "stopped":
        st.warning("⏸ Processing stopped")

    elif state == "error":
        st.error("❌ Error: " + result.get("error", ""))

    else:
        st.success("✅ Processed")

    st.write(
        f"Unread: **{result.get('unread_found', 0)}**  |  "
        f"Fetched: **{result.get('fetched', 0)}**  |  "
        f"Seen: **{result.get('seen', 0)}**  |  "
        f"Failed: **{result.get('failed', 0)}**"
    )


def render_selected(results):
    selected = st.session_state.selected_mailbox

    if not selected:
        return

    selected_result = results.get(selected)

    if not selected_result:
        return

    st.divider()

    st.subheader(f"📧 {selected}")

    d1, d2, d3, d4 = st.columns(4)

    d1.metric("Unread", selected_result.get("unread_found", 0))
    d2.metric("Fetched", selected_result.get("fetched", 0))
    d3.metric("Seen", selected_result.get("seen", 0))
    d4.metric("Failed", selected_result.get("failed", 0))

    if selected_result.get("error"):
        st.error(selected_result["error"])

    if selected_result.get("state") == "stopped":
        st.warning("Processing was stopped.")

    latest = selected_result.get("latest", [])

    if latest:

        st.subheader("📨 Latest Processed Messages")

        for message in latest:
            with st.container(border=True):
                st.write("**Subject:** " + message.get("subject", "(No Subject)"))
                st.write("**From:** " + message.get("from", "(Unknown Sender)"))

    elif selected_result.get("state") in ("done", "stopped", "error"):
        st.info("No messages were processed.")


# =========================================================
# LIVE DASHBOARD  (auto-refreshes; only this fragment reruns)
# =========================================================

@st.fragment(run_every=REFRESH_SECONDS)
def dashboard():

    results, active = mgr.snapshot()

    busy = len(active) > 0
    stopping = busy and mgr.stop_event.is_set()

    # ------------------- CONTROLS -------------------

    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])

    with c1:
        start_clicked = st.button(
            "▶ START PROCESSING",
            use_container_width=True,
            disabled=busy,
            key="btn_start",
        )

    with c2:
        stop_clicked = st.button(
            "🛑 STOP",
            use_container_width=True,
            disabled=(not busy) or stopping,
            key="btn_stop",
        )

    with c3:
        reset_clicked = st.button(
            "🧹 RESET",
            use_container_width=True,
            disabled=busy,
            key="btn_reset",
        )

    with c4:
        logout_clicked = st.button(
            "🚪 LOGOUT",
            use_container_width=True,
            key="btn_logout",
        )

    if logout_clicked:
        token = st.query_params.get("auth")

        if token:
            mgr.revoke_token(token)

        st.query_params.clear()
        st.session_state.logged_in = False
        st.rerun(scope="app")

    if stop_clicked:
        mgr.request_stop()
        st.rerun(scope="fragment")

    if reset_clicked:
        mgr.clear_results()
        st.session_state.selected_mailbox = None
        st.rerun(scope="fragment")

    if start_clicked:

        if not accounts:
            st.error("No Yahoo mailboxes configured.")

        else:
            queued = mgr.start(accounts, only_pending=True)

            if queued == 0:
                st.success("✅ All configured mailboxes are already processed.")
            else:
                st.rerun(scope="fragment")

    # ------------------- STATUS BAR -------------------

    if busy:

        finished = sum(
            1
            for a in accounts
            if results.get(a["email"], {}).get("state")
            in ("done", "stopped", "error")
        )

        total = max(len(accounts), 1)

        if stopping:
            st.warning(
                "🛑 Stop requested. Running mailboxes will stop "
                "after the current batch."
            )
        else:
            st.info(
                f"⚡ Running — {len(active)} mailbox(es) active "
                f"(up to {MAX_PARALLEL_MAILBOXES} in parallel). "
                f"You can refresh or close this page; processing continues."
            )

        st.progress(
            min(finished / total, 1.0),
            text=f"{finished}/{len(accounts)} mailboxes finished",
        )

    # ------------------- METRICS -------------------

    values = list(results.values())

    m1, m2, m3, m4, m5 = st.columns(5)

    m1.metric("Mailboxes", len(accounts))
    m2.metric("Unread Found", sum(r.get("unread_found", 0) for r in values))
    m3.metric("Fetched", sum(r.get("fetched", 0) for r in values))
    m4.metric("Marked Seen", sum(r.get("seen", 0) for r in values))
    m5.metric("Failed", sum(r.get("failed", 0) for r in values))

    # ------------------- MAILBOX LIST -------------------

    st.divider()

    st.subheader("📮 Mailboxes")

    if not accounts:
        st.warning(
            "No Yahoo mailboxes configured in Render environment variables."
        )
        return

    search_text = (st.session_state.get("search_text") or "").strip().lower()

    for account in accounts:

        email_address = account["email"]

        if search_text and search_text not in email_address.lower():
            continue

        result = results.get(email_address)

        with st.container(border=True):

            left, right = st.columns([4, 1])

            with left:
                st.markdown(f"### 📧 {email_address}")
                render_status(result)

            with right:

                process_clicked = st.button(
                    "▶ Process",
                    key=f"process_{account['index']}",
                    use_container_width=True,
                    disabled=(email_address in active) or stopping,
                )

                view_clicked = st.button(
                    "👁 View",
                    key=f"view_{account['index']}",
                    use_container_width=True,
                    disabled=result is None,
                )

                if process_clicked:
                    st.session_state.selected_mailbox = email_address
                    mgr.start([account], only_pending=False)
                    st.rerun(scope="fragment")

                if view_clicked:
                    st.session_state.selected_mailbox = email_address
                    st.rerun(scope="fragment")

    # ------------------- SELECTED MAILBOX -------------------

    render_selected(results)


# =========================================================
# PAGE
# =========================================================

st.title("📬 Yahoo Mailbox Dashboard")

st.caption("Manage your configured Yahoo mailboxes")

st.text_input(
    "🔎 Search mailbox",
    placeholder="Search mailbox...",
    key="search_text",
)

dashboard()
