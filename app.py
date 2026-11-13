"""
app.py
-------
CivicShield – Government Identity and Access Management System
Academic demonstration — not an official government portal.

Run with:
    streamlit run app.py

How it works
------------
1. On first run, initialize_database() creates the SQLite DB and seeds tables.
2. seed_all() adds fictional employee and audit-log data.
3. If the user is not authenticated, the login page is shown.
4. Once authenticated, the sidebar navigation controls which page is rendered.
"""

import streamlit as st

# ── Page config must be the very first Streamlit call ────────────────
st.set_page_config(
    page_title="CivicShield IAM",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── One-time startup: DB init + seed ─────────────────────────────────
from database.db_init import initialize_database
from data.sample_data import seed_all

initialize_database()
seed_all()

# ── Auth imports ──────────────────────────────────────────────────────
from auth.auth import is_authenticated

# ── Page imports ──────────────────────────────────────────────────────
from _pages.login import render_login_page
from _pages.dashboard import render_dashboard
from _pages.user_management import render_user_management
from _pages.roles_permissions import render_roles_permissions
from _pages.iam_policies import render_iam_policies
from _pages.audit_logs import render_audit_logs
from ui.components import render_sidebar


# ── Router ────────────────────────────────────────────────────────────

def main() -> None:
    """Main router: show login or the appropriate authenticated page."""

    # Show login page if not authenticated
    if not is_authenticated(st.session_state):
        render_login_page()
        return

    # Render sidebar and get the currently selected page
    selected_page = render_sidebar(st.session_state)

    # Persist the selected page in session state
    st.session_state["current_page"] = selected_page

    # Route to the correct page renderer
    if selected_page == "Dashboard":
        render_dashboard(st.session_state)

    elif selected_page == "User Management":
        render_user_management(st.session_state)

    elif selected_page == "Roles & Permissions":
        render_roles_permissions(st.session_state)

    elif selected_page == "IAM Policies":
        render_iam_policies(st.session_state)

    elif selected_page == "Audit Logs":
        render_audit_logs(st.session_state)

    else:
        st.error(f"Unknown page: {selected_page}")


if __name__ == "__main__":
    main()
else:
    # Streamlit re-runs the module on every interaction —
    # calling main() at module level handles that correctly.
    main()
