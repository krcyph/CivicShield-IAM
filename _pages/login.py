from datetime import datetime
import streamlit as st
from auth.auth import login, MAX_FAILED_ATTEMPTS
from ui.components import inject_css

_CURRENT_YEAR = datetime.now().year

# ── Login-page overrides ─────────────────────────────────────────────────
_LOGIN_CSS = """
<style>
/* Midnight Navy background on login page */
[data-testid="stAppViewContainer"] {
    background-color: #0B1728 !important;
}
[data-testid="stAppViewContainer"] > .main .block-container {
    padding-top: 2.5rem;
}
/* Hide sidebar on login */
[data-testid="stSidebar"] { display: none !important; }

/* Form card — Deep Slate surface */
[data-testid="stForm"] {
    background: #12243A;
    border-radius: 10px;
    padding: 12px 8px;
    border: 1px solid #1E3A56;
}
/* Input labels */
[data-testid="stForm"] label {
    color: #DCE8F2 !important;
    font-weight: 600;
    font-size: 0.88rem;
}
/* Input boxes */
[data-testid="stForm"] input {
    background: #0B1728 !important;
    border: 1px solid #1E3A56 !important;
    border-radius: 6px !important;
    color: #DCE8F2 !important;
}
[data-testid="stForm"] input:focus {
    border-color: #20C5B5 !important;
}
</style>
"""


def render_login_page() -> None:
    """Render the full login page and handle credential submission."""

    inject_css()
    st.markdown(_LOGIN_CSS, unsafe_allow_html=True)

    # Centred column layout
    _, col, _ = st.columns([1, 1.4, 1])

    with col:
        # ── Header ────────────────────────────────────────────────
        st.markdown(
            """
            <div style="text-align:center; margin-bottom:28px;">
                <div style="font-size:3.4rem;line-height:1;">🛡️</div>
                <div style="font-size:1.35rem; font-weight:700; color:#DCE8F2;
                            letter-spacing:0.04em; margin-top:10px;">
                    CivicShield
                </div>
                <div style="font-size:0.82rem; color:#20C5B5; margin-top:4px;
                            font-weight:500; letter-spacing:0.03em;">
                    Government Identity &amp; Access Management System
                </div>
                <div style="font-size:0.72rem; color:#5C7A96; margin-top:6px;">
                    Citizen Services Department — Secure Identity Platform
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── Login form ────────────────────────────────────────────
        with st.form("login_form", clear_on_submit=False):
            st.markdown(
                """
                <div style="text-align:center; margin-bottom:16px;">
                    <div style="font-size:0.95rem; font-weight:700; color:#DCE8F2;">
                        Sign in to your account
                    </div>
                    <div style="font-size:0.74rem; color:#5C7A96; margin-top:4px;
                                padding-bottom:12px; border-bottom:1px solid #1E3A56;">
                        Authorised personnel only. All access is logged and monitored.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            username = st.text_input(
                "Username",
                placeholder="Enter your username",
                autocomplete="username",
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                autocomplete="current-password",
            )

            submitted = st.form_submit_button(
                "Sign In",
                width="stretch",
                type="primary",
            )

        # ── Handle submission (outside form to allow reruns) ──────
        if submitted:
            if not username or not password:
                st.error("Please enter both username and password.")
            else:
                user = login(username.strip().lower(), password)
                if user:
                    st.session_state["authenticated"] = True
                    st.session_state["user"] = user
                    st.session_state["current_page"] = "Dashboard"
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
                    st.caption("This attempt has been recorded in the audit log.")

        # ── Demo credentials ──────────────────────────────────────
        st.markdown(
            f"""
            <div style="background:rgba(32,197,181,0.07);border:1px solid #1E3A56;
                        border-left:3px solid #20C5B5;
                        border-radius:6px; padding:12px 14px; font-size:0.78rem;
                        color:#DCE8F2; margin-top:14px;">
                <b style="color:#20C5B5;">Demo Credentials</b><br>
                <span style="color:#5C7A96;">Admin &nbsp;—</span>
                username: <b>admin</b> &nbsp;/ password: <b>Admin@1234</b><br>
                <span style="color:#5C7A96;">Auditor —</span>
                username: <b>auditor</b> / password: <b>Audit@5678</b>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── Footer ───────────────────────────────────────────────
        st.markdown(
            f"""
            <div style="text-align:center; font-size:0.68rem; color:#5C7A96;
                        margin-top:28px; line-height:1.8; border-top:1px solid #1E3A56;
                        padding-top:14px;">
                CivicShield v1.0.0 &nbsp;|&nbsp; &copy; {_CURRENT_YEAR} Citizen Services Department<br>
                <span style="color:rgba(92,122,150,0.7);">
                    Academic demonstration only — not an official government portal
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )
