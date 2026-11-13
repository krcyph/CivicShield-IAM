from datetime import datetime
import pandas as pd
import streamlit as st
from ui.components import (
    inject_css,
    top_nav_bar,
    metric_card,
    section_header,
    page_title,
    status_badge,
)
from data.sample_data import (
    get_summary_stats,
    get_employees_df,
    get_recent_audit_logs,
    get_department_counts,
    get_clearance_counts,
)

_CURRENT_YEAR = datetime.now().year

# ── CivicShield palette ──────────────────────────────────────────────────
_TEAL   = "#20C5B5"
_NAVY   = "#0B1728"
_SLATE  = "#12243A"
_STEEL  = "#173B56"
_ICE    = "#DCE8F2"
_AMBER  = "#F0B45A"
_MUTED  = "#5C7A96"
_BORDER = "#1E3A56"

SEVERITY_COLOURS = {
    "Critical": "#E04B4B",
    "Warning":  _AMBER,
    "Info":     _TEAL,
}


def render_dashboard(session_state) -> None:
    inject_css()

    user = session_state.get("user", {})
    top_nav_bar(user.get("full_name", "Unknown"), user.get("role", ""))

    page_title(
        "Dashboard",
        "Real-time overview of identity and access management activity.",
    )

    stats = get_summary_stats()

    # ── Row 1: Four primary metric cards ─────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Total Employees",   stats["total_employees"],
                    "Registered in the system", accent=_TEAL)
    with c2:
        metric_card("Active Accounts",   stats["active_accounts"],
                    "Currently active", accent="#20C5B5")
    with c3:
        metric_card("Inactive Accounts", stats["inactive_accounts"],
                    "Disabled or expired", accent=_AMBER)
    with c4:
        metric_card("Security Events",   stats["security_events"],
                    "Warnings & critical alerts", accent="#E04B4B")

    # ── Row 2: Two secondary metric cards ─────────────────────────────
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    c5, c6, _ = st.columns([1, 1, 2])
    with c5:
        metric_card("Departments",           stats["departments"],
                    "Across the organisation", accent="#7C5CD8")
    with c6:
        metric_card("Top Secret Clearances", stats["top_secret_clearances"],
                    "Highest clearance level", accent="#3B82D4")

    # ── Charts row ─────────────────────────────────────────────────────
    section_header("Organisation Overview")
    chart_left, chart_right = st.columns([3, 2])

    # Left: bar chart — employees by department
    with chart_left:
        st.markdown(
            f'<div style="background:{_SLATE};border-radius:8px;padding:16px 18px;'
            f'border:1px solid {_BORDER};">'
            f'<div style="font-size:0.82rem;font-weight:600;color:{_ICE};margin-bottom:12px;">'
            f'Employees by Department</div>',
            unsafe_allow_html=True,
        )
        dept_data = get_department_counts()
        if dept_data:
            df_dept = pd.DataFrame(dept_data).set_index("department")
            st.bar_chart(df_dept["count"], color=_TEAL, height=250)
        st.markdown("</div>", unsafe_allow_html=True)

    # Right: clearance breakdown — horizontal bar chart in HTML
    with chart_right:
        clearance_data = get_clearance_counts()
        clearance_colours = {
            "Top Secret":   "#E04B4B",
            "Secret":       _AMBER,
            "Confidential": "#3B82D4",
            "Public":       _TEAL,
        }
        rows_html = ""
        for row in clearance_data:
            colour    = clearance_colours.get(row["clearance_level"], _MUTED)
            bar_width = int(row["count"] / max(stats["total_employees"], 1) * 100)
            rows_html += f"""
            <div style="margin-bottom:14px;">
                <div style="display:flex;justify-content:space-between;
                            font-size:0.80rem;color:{_ICE};margin-bottom:4px;">
                    <span>{row['clearance_level']}</span>
                    <span style="font-weight:700;color:{colour};">{row['count']}</span>
                </div>
                <div style="background:{_NAVY};border-radius:4px;height:8px;">
                    <div style="width:{bar_width}%;background:{colour};
                                border-radius:4px;height:8px;"></div>
                </div>
            </div>"""
        st.markdown(
            f'<div style="background:{_SLATE};border-radius:8px;padding:16px 18px;'
            f'border:1px solid {_BORDER};height:100%;">'
            f'<div style="font-size:0.82rem;font-weight:600;color:{_ICE};margin-bottom:16px;">'
            f'Clearance Level Distribution</div>'
            f'{rows_html}</div>',
            unsafe_allow_html=True,
        )

    # ── Recent Security Events ─────────────────────────────────────────
    section_header("Recent Security Events")
    audit_logs = get_recent_audit_logs(limit=8)

    if audit_logs:
        rows_html = ""
        for log in audit_logs:
            sev        = log["severity"]
            sev_colour = SEVERITY_COLOURS.get(sev, _MUTED)
            sev_bg     = sev_colour + "22"
            badge = (
                f'<span style="background:{sev_bg};color:{sev_colour};'
                f'padding:2px 8px;border-radius:10px;font-size:0.72rem;'
                f'font-weight:700;">{sev}</span>'
            )
            rows_html += (
                f'<tr style="border-bottom:1px solid {_BORDER};">'
                f'<td style="padding:8px 10px;">{badge}</td>'
                f'<td style="padding:8px 10px;font-family:\'IBM Plex Mono\',monospace;'
                f'font-size:0.77rem;color:{_TEAL};">{log["event_type"]}</td>'
                f'<td style="padding:8px 10px;color:{_ICE};">{log["actor"]}</td>'
                f'<td style="padding:8px 10px;color:{_MUTED};font-size:0.79rem;">'
                f'{(log["details"] or "—")[:60]}</td>'
                f'<td style="padding:8px 10px;font-family:\'IBM Plex Mono\',monospace;'
                f'font-size:0.74rem;color:{_MUTED};">{log["ip_address"] or "—"}</td>'
                f'<td style="padding:8px 10px;font-size:0.76rem;color:{_MUTED};">'
                f'{log["created_at"]}</td>'
                f'</tr>'
            )

        th = (f'background:{_STEEL};color:{_ICE};padding:9px 10px;'
              f'text-align:left;font-size:0.73rem;font-weight:600;')
        st.markdown(
            f'<div style="background:{_SLATE};border-radius:8px;border:1px solid {_BORDER};'
            f'overflow-x:auto;">'
            f'<table style="width:100%;border-collapse:collapse;font-size:0.81rem;">'
            f'<thead><tr>'
            f'<th style="{th}">Severity</th>'
            f'<th style="{th}">Event Type</th>'
            f'<th style="{th}">Actor</th>'
            f'<th style="{th}">Details</th>'
            f'<th style="{th}">IP Address</th>'
            f'<th style="{th}">Timestamp</th>'
            f'</tr></thead>'
            f'<tbody>{rows_html}</tbody></table></div>',
            unsafe_allow_html=True,
        )

    # ── Employee directory preview ──────────────────────────────────────
    section_header("Employee Directory (Preview)")
    employees = get_employees_df()[:10]

    if employees:
        emp_rows = ""
        for emp in employees:
            badge = status_badge(emp["account_status"])
            emp_rows += (
                f'<tr style="border-bottom:1px solid {_BORDER};">'
                f'<td style="padding:8px 10px;font-family:\'IBM Plex Mono\',monospace;'
                f'font-size:0.77rem;color:{_TEAL};">{emp["employee_id"]}</td>'
                f'<td style="padding:8px 10px;font-weight:600;color:{_ICE};">'
                f'{emp["full_name"]}</td>'
                f'<td style="padding:8px 10px;color:{_MUTED};">{emp["department"]}</td>'
                f'<td style="padding:8px 10px;color:{_ICE};">{emp["job_title"]}</td>'
                f'<td style="padding:8px 10px;color:{_ICE};">{emp["clearance_level"]}</td>'
                f'<td style="padding:8px 10px;">{badge}</td>'
                f'<td style="padding:8px 10px;font-size:0.77rem;color:{_MUTED};">'
                f'{emp["last_login"] or "—"}</td>'
                f'</tr>'
            )

        th = (f'background:{_STEEL};color:{_ICE};padding:9px 10px;'
              f'text-align:left;font-size:0.73rem;font-weight:600;')
        st.markdown(
            f'<div style="background:{_SLATE};border-radius:8px;border:1px solid {_BORDER};'
            f'overflow-x:auto;">'
            f'<table style="width:100%;border-collapse:collapse;font-size:0.81rem;">'
            f'<thead><tr>'
            f'<th style="{th}">ID</th>'
            f'<th style="{th}">Full Name</th>'
            f'<th style="{th}">Department</th>'
            f'<th style="{th}">Job Title</th>'
            f'<th style="{th}">Clearance</th>'
            f'<th style="{th}">Status</th>'
            f'<th style="{th}">Last Login</th>'
            f'</tr></thead>'
            f'<tbody>{emp_rows}</tbody></table>'
            f'<div style="font-size:0.74rem;color:{_MUTED};padding:10px 12px;">'
            f'Showing 10 of {len(get_employees_df())} employees. '
            f'Full list available in User Management.</div></div>',
            unsafe_allow_html=True,
        )

    # ── Footer ─────────────────────────────────────────────────────────
    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
    st.markdown(
        f'<div style="text-align:center;font-size:0.70rem;color:{_MUTED};'
        f'border-top:1px solid {_BORDER};padding-top:12px;margin-top:8px;">'
        f'CivicShield v1.0.0 &nbsp;|&nbsp; &copy; {_CURRENT_YEAR} Citizen Services Department'
        f' &nbsp;|&nbsp; <span style="color:{_AMBER};">Academic demonstration — fictional data only</span>'
        f'</div>',
        unsafe_allow_html=True,
    )
