import streamlit as st
from ui.components import inject_css, top_nav_bar, page_title

# Icon mapping for each placeholder page
PAGE_ICONS = {
    "User Management":    "👥",
    "Roles & Permissions": "🔐",
    "IAM Policies":       "📋",
    "Audit Logs":         "📜",
}


def render_placeholder(session_state, page_name: str) -> None:
    """Render a 'coming soon' page with the given page name."""

    inject_css()

    user = session_state.get("user", {})
    top_nav_bar(user.get("full_name", "Unknown"), user.get("role", ""))

    icon = PAGE_ICONS.get(page_name, "🔧")
    page_title(page_name, "This module is under development.")

    st.markdown(
        f"""
        <div style="
            background: #ffffff;
            border-radius: 12px;
            padding: 48px 40px;
            text-align: center;
            border: 2px dashed #c5d8f5;
            max-width: 560px;
            margin: 40px auto;
            box-shadow: 0 2px 8px rgba(30,95,168,0.07);
        ">
            <div style="font-size:3.5rem;margin-bottom:16px;">{icon}</div>
            <div style="font-size:1.25rem;font-weight:700;color:#0a1628;margin-bottom:8px;">
                {page_name}
            </div>
            <div style="font-size:0.9rem;color:#5a7499;margin-bottom:20px;">
                This module is not yet implemented in the current version.
                It will be available in a future release of CivicShield IAM.
            </div>
            <div style="
                display:inline-block;
                background:#eaf1fb;
                color:#1e5fa8;
                border-radius:20px;
                padding:6px 20px;
                font-size:0.82rem;
                font-weight:600;
                border:1px solid #b8d0f5;
            ">
                🚧 &nbsp; Coming Soon
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
