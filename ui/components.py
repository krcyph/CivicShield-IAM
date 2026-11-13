from datetime import datetime
import streamlit as st
from collections.abc import MutableMapping
from typing import cast
from auth.auth import logout

# ── Brand constants ──────────────────────────────────────────────────────
_TEAL   = "#20C5B5"
_NAVY   = "#0B1728"
_SLATE  = "#12243A"
_STEEL  = "#173B56"
_ICE    = "#DCE8F2"
_AMBER  = "#F0B45A"
_MUTED  = "#5C7A96"
_BORDER = "#1E3A56"

_CURRENT_YEAR = datetime.now().year

# -----------------------------------------------------------------------
# Global CSS  — injected once per page render
# -----------------------------------------------------------------------

GLOBAL_CSS = f"""
<style>
/* ── Base ─────────────────────────────────────────────────────── */
html, body, [data-testid="stAppViewContainer"] {{
    font-family: 'IBM Plex Sans', 'Segoe UI', Arial, sans-serif;
    background-color: {_NAVY};
    color: {_ICE};
}}

/* ── Hide Streamlit chrome ────────────────────────────────────── */
#MainMenu {{ visibility: hidden; }}
footer    {{ visibility: hidden; }}
header    {{ visibility: hidden; }}

/* ── Remove default top padding ──────────────────────────────── */
[data-testid="stAppViewContainer"] > .main .block-container {{
    padding-top: 0.75rem;
    padding-bottom: 2rem;
}}

/* ── Sidebar ──────────────────────────────────────────────────── */
[data-testid="stSidebar"] {{
    background-color: {_NAVY};
    border-right: 1px solid {_BORDER};
}}
[data-testid="stSidebar"] > div > div {{
    color: {_ICE};
}}

/* Sidebar radio labels */
[data-testid="stSidebar"] .stRadio label span {{
    color: #8BABC8 !important;
    font-size: 0.88rem;
}}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:hover span {{
    color: {_ICE} !important;
}}
/* Selected nav item */
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label[data-checked="true"] span {{
    color: {_TEAL} !important;
    font-weight: 600;
}}

/* Sidebar logout button */
[data-testid="stSidebar"] .stButton > button {{
    background: transparent;
    border: 1px solid {_BORDER};
    color: #8BABC8;
    border-radius: 6px;
    font-size: 0.85rem;
    transition: border-color 0.15s, color 0.15s;
}}
[data-testid="stSidebar"] .stButton > button:hover {{
    border-color: {_TEAL};
    color: {_TEAL};
    background: rgba(32,197,181,0.08);
}}

/* ── Top nav bar ──────────────────────────────────────────────── */
.cs-top-nav {{
    background: {_SLATE};
    border: 1px solid {_BORDER};
    border-radius: 8px;
    padding: 10px 18px;
    margin-bottom: 18px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}}
.cs-top-nav-title {{
    font-size: 0.92rem;
    font-weight: 700;
    letter-spacing: 0.03em;
    color: {_ICE};
}}
.cs-top-nav-user {{
    font-size: 0.82rem;
    color: {_MUTED};
}}
.cs-top-nav-user b {{
    color: {_TEAL};
}}

/* ── Page title ───────────────────────────────────────────────── */
.cs-page-title {{
    font-size: 1.55rem;
    font-weight: 700;
    color: {_ICE};
    margin-bottom: 2px;
    letter-spacing: -0.01em;
}}
.cs-page-subtitle {{
    font-size: 0.85rem;
    color: {_MUTED};
    margin-bottom: 20px;
}}

/* ── Section header ───────────────────────────────────────────── */
.cs-section-header {{
    font-size: 0.88rem;
    font-weight: 700;
    color: {_TEAL};
    border-bottom: 1px solid {_BORDER};
    padding-bottom: 6px;
    margin-top: 22px;
    margin-bottom: 14px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}}

/* ── Metric cards ─────────────────────────────────────────────── */
.cs-card {{
    background: {_SLATE};
    border-radius: 8px;
    padding: 18px 16px;
    border: 1px solid {_BORDER};
    border-left: 3px solid {_TEAL};
    margin-bottom: 8px;
}}
.cs-card-title {{
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.09em;
    color: {_MUTED};
    margin-bottom: 6px;
}}
.cs-card-value {{
    font-size: 2.0rem;
    font-weight: 700;
    color: {_ICE};
    line-height: 1.1;
}}
.cs-card-delta {{
    font-size: 0.76rem;
    margin-top: 4px;
    color: {_MUTED};
}}

/* ── Status badges ────────────────────────────────────────────── */
.badge-active   {{ background:rgba(32,197,181,0.15); color:#20C5B5;
                   padding:2px 10px; border-radius:12px;
                   font-size:0.76rem; font-weight:600; }}
.badge-inactive {{ background:rgba(224,75,75,0.15);  color:#E04B4B;
                   padding:2px 10px; border-radius:12px;
                   font-size:0.76rem; font-weight:600; }}
.badge-pending  {{ background:rgba(240,180,90,0.15); color:{_AMBER};
                   padding:2px 10px; border-radius:12px;
                   font-size:0.76rem; font-weight:600; }}
.badge-critical {{ background:rgba(224,75,75,0.15);  color:#E04B4B;
                   padding:2px 10px; border-radius:12px;
                   font-size:0.76rem; font-weight:600; }}

/* ── Data table wrapper ───────────────────────────────────────── */
.cs-table-wrapper {{
    background: {_SLATE};
    border-radius: 8px;
    padding: 0;
    border: 1px solid {_BORDER};
    overflow-x: auto;
    margin-bottom: 16px;
}}

/* ── Ensure stDataframe doesn't overflow ─────────────────────── */
[data-testid="stDataFrame"] {{
    width: 100% !important;
}}
</style>
"""


def inject_css() -> None:
    """Inject the global stylesheet. Call once at the top of every page."""
    _ = st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


# -----------------------------------------------------------------------
# Metric card
# -----------------------------------------------------------------------

def metric_card(title: str, value: str | int, delta: str = "", accent: str = _TEAL) -> None:
    border_style = f"border-left: 3px solid {accent};"
    _ = st.markdown(
        f"""
        <div class="cs-card" style="{border_style}">
            <div class="cs-card-title">{title}</div>
            <div class="cs-card-value">{value}</div>
            <div class="cs-card-delta">{delta}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------
# Section header
# -----------------------------------------------------------------------

def section_header(text: str) -> None:
    _ = st.markdown(f'<div class="cs-section-header">{text}</div>', unsafe_allow_html=True)


# -----------------------------------------------------------------------
# Page title block
# -----------------------------------------------------------------------

def page_title(title: str, subtitle: str = "") -> None:
    _ = st.markdown(f'<div class="cs-page-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        _ = st.markdown(f'<div class="cs-page-subtitle">{subtitle}</div>', unsafe_allow_html=True)


# -----------------------------------------------------------------------
# Top navigation bar
# -----------------------------------------------------------------------

def top_nav_bar(username: str, role: str) -> None:
    role_display = role.replace("_", " ").title()
    _ = st.markdown(
        f"""
        <div class="cs-top-nav">
            <span class="cs-top-nav-title">🛡️ &nbsp;CivicShield — Identity &amp; Access Management</span>
            <span class="cs-top-nav-user">👤 <b>{username}</b> &nbsp;|&nbsp; {role_display}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------
# Status badge
# -----------------------------------------------------------------------

def status_badge(status: str) -> str:
    cls = {
        "Active":   "badge-active",
        "Inactive": "badge-inactive",
        "Pending":  "badge-pending",
        "Critical": "badge-critical",
    }.get(status, "badge-pending")
    return f'<span class="{cls}">{status}</span>'


# -----------------------------------------------------------------------
# Sidebar navigation
# -----------------------------------------------------------------------

NAV_ITEMS = [
    (":material/dashboard:",    "Dashboard"),
    (":material/group:",        "User Management"),
    (":material/lock:",         "Roles & Permissions"),
    (":material/policy:",       "IAM Policies"),
    (":material/history:",      "Audit Logs"),
]


def render_sidebar(session_state: MutableMapping[str, object]) -> str:
    """Render the sidebar navigation and return the selected page name."""
    with st.sidebar:
        # ── Logo / brand ─────────────────────────────────────────────
        _ = st.markdown(
            f"""
            <div style="padding:20px 12px 14px 12px;">
                <div style="display:flex;align-items:center;gap:10px;margin-bottom:4px;">
                    <span style="font-size:2.0rem;line-height:1;">🛡️</span>
                    <div>
                        <div style="font-size:1.05rem;font-weight:700;
                                    color:{_TEAL};letter-spacing:0.04em;">
                            CivicShield
                        </div>
                        <div style="font-size:0.65rem;color:{_MUTED};
                                    letter-spacing:0.06em;text-transform:uppercase;">
                            Identity &amp; Access Management
                        </div>
                    </div>
                </div>
                <div style="font-size:0.62rem;color:{_MUTED};margin-top:4px;
                            padding:4px 8px;background:rgba(32,197,181,0.08);
                            border-radius:4px;border-left:2px solid {_TEAL};">
                    Academic demo — not an official government portal
                </div>
            </div>
            <hr style="border:none;border-top:1px solid {_BORDER};margin:0 0 10px 0;">
            """,
            unsafe_allow_html=True,
        )

        # ── Navigation ────────────────────────────────────────────────
        _ = st.markdown(
            f'<div style="font-size:0.66rem;color:{_MUTED};text-transform:uppercase;letter-spacing:0.1em;margin:0 0 6px 4px;">Navigation</div>',
            unsafe_allow_html=True,
        )

        labels = [f"{icon}  {name}" for icon, name in NAV_ITEMS]
        current = session_state.get("current_page", "Dashboard")

        current_label = next(
            (f"{icon}  {name}" for icon, name in NAV_ITEMS if name == current),
            labels[0],
        )

        selected_label = st.radio(
            label="nav",
            options=labels,
            index=labels.index(current_label),
            label_visibility="collapsed",
        )

        selected_page = selected_label.split("  ", 1)[1]

        _ = st.markdown(
            f'<hr style="border:none;border-top:1px solid {_BORDER};margin:14px 0 10px 0;">',
            unsafe_allow_html=True,
        )

        # ── Logged-in user info ───────────────────────────────────────
        user = cast(dict[str, str], session_state.get("user", {}))
        role_display = user.get("role", "").replace("_", " ").title()
        _ = st.markdown(
            f"""
            <div style="padding:0 4px 12px 4px;">
                <div style="font-size:0.68rem;color:{_MUTED};margin-bottom:3px;
                            text-transform:uppercase;letter-spacing:0.06em;">
                    Logged in as
                </div>
                <div style="font-size:0.88rem;font-weight:600;color:{_ICE};">
                    {user.get('full_name', 'Unknown')}
                </div>
                <div style="font-size:0.72rem;color:{_TEAL};margin-top:1px;margin-bottom:12px;">
                    {role_display}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("Sign Out", width="stretch"):
            logout(session_state)
            st.rerun()

        _ = st.markdown(
            f"""
            <div style="margin-top:28px;padding:0 4px;text-align:center;
                        font-size:0.62rem;color:{_MUTED};line-height:1.7;
                        border-top:1px solid {_BORDER};padding-top:12px;">
                CivicShield v1.0.0<br>
                &copy; {_CURRENT_YEAR} Citizen Services Dept.<br>
                <span style="color:rgba(92,122,150,0.6);">Academic demonstration only</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    return selected_page
