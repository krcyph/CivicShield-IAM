import csv
import io
import streamlit as st
from database.db_init import get_connection
from auth.auth import require_permission, has_permission
from ui.components import inject_css, top_nav_bar, page_title, section_header

SEVERITY_COLOURS = {
    "Critical": ("#E04B4B", "rgba(224,75,75,0.12)"),
    "Warning":  ("#F0B45A", "rgba(240,180,90,0.12)"),
    "Info":     ("#20C5B5", "rgba(32,197,181,0.12)"),
}

EVENT_TYPES = [
    "All", "LOGIN_SUCCESS", "LOGIN_FAILURE", "LOGOUT",
    "USER_CREATED", "USER_UPDATED", "ACCOUNT_ENABLED", "ACCOUNT_DISABLED",
    "ROLE_ASSIGNED", "ROLE_REVOKED",
    "PERMISSION_DENIED", "DATA_EXPORT",
    "POLICY_UPDATED", "PASSWORD_CHANGED", "SESSION_TIMEOUT",
]


# ── DB helpers ────────────────────────────────────────────────────────────

def _query_logs(
    actor_q:    str = "",
    event_type: str = "All",
    severity:   str = "All",
    date_from:  str = "",
    date_to:    str = "",
    limit:      int = 500,
) -> list[dict]:
    conditions: list[str] = []
    params:     list      = []

    if actor_q:
        conditions.append("(LOWER(actor) LIKE ? OR LOWER(target) LIKE ?)")
        params += [f"%{actor_q.lower()}%", f"%{actor_q.lower()}%"]
    if event_type != "All":
        conditions.append("event_type = ?")
        params.append(event_type)
    if severity != "All":
        conditions.append("severity = ?")
        params.append(severity)
    if date_from:
        conditions.append("created_at >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("created_at <= ?")
        params.append(date_to + " 23:59:59")

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    sql   = f"""
        SELECT id, event_type, actor, target, details, ip_address, severity, created_at
        FROM audit_logs
        {where}
        ORDER BY id DESC
        LIMIT ?
    """
    params.append(limit)

    conn = get_connection()
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _summary_counts() -> dict:
    conn = get_connection()
    c    = conn.cursor()
    c.execute("SELECT COUNT(*) FROM audit_logs")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM audit_logs WHERE severity='Critical'")
    critical = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM audit_logs WHERE severity='Warning'")
    warnings = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM audit_logs WHERE event_type='LOGIN_FAILURE'")
    failures = c.fetchone()[0]
    conn.close()
    return {"total": total, "critical": critical,
            "warnings": warnings, "failures": failures}


def _to_csv(rows: list[dict]) -> str:
    buf    = io.StringIO()
    fields = ["id", "event_type", "actor", "target",
              "details", "ip_address", "severity", "created_at"]
    writer = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def _build_table_html(logs: list[dict]) -> str:
    """Build a complete HTML table string for all audit log rows."""
    rows_html = ""
    for log in logs:
        sev             = log["severity"]
        sev_fg, sev_bg  = SEVERITY_COLOURS.get(sev, ("#5C7A96", "rgba(92,122,150,0.12)"))
        badge = (
            f'<span style="background:{sev_bg};color:{sev_fg};padding:2px 8px;'
            f'border-radius:10px;font-size:0.73rem;font-weight:700;">{sev}</span>'
        )
        rows_html += (
            f'<tr style="border-bottom:1px solid #1E3A56;">'
            f'<td style="padding:8px 10px;">{badge}</td>'
            f'<td style="padding:8px 10px;font-family:\'IBM Plex Mono\',monospace;font-size:0.76rem;'
            f'color:#20C5B5;">{log["event_type"]}</td>'
            f'<td style="padding:8px 10px;color:#DCE8F2;">{log["actor"]}</td>'
            f'<td style="padding:8px 10px;color:#5C7A96;">{log["target"] or "—"}</td>'
            f'<td style="padding:8px 10px;color:#5C7A96;font-size:0.78rem;max-width:260px;">'
            f'{(log["details"] or "—")[:90]}</td>'
            f'<td style="padding:8px 10px;font-family:\'IBM Plex Mono\',monospace;font-size:0.74rem;'
            f'color:#5C7A96;">{log["ip_address"] or "—"}</td>'
            f'<td style="padding:8px 10px;font-size:0.76rem;color:#5C7A96;">'
            f'{log["created_at"]}</td>'
            f'</tr>'
        )

    th = ('background:#173B56;color:#DCE8F2;padding:9px 10px;'
          'text-align:left;font-size:0.73rem;font-weight:600;')
    header = (
        f'<tr>'
        f'<th style="{th}">Severity</th>'
        f'<th style="{th}">Event Type</th>'
        f'<th style="{th}">Actor</th>'
        f'<th style="{th}">Target</th>'
        f'<th style="{th}">Details</th>'
        f'<th style="{th}">IP Address</th>'
        f'<th style="{th}">Timestamp</th>'
        f'</tr>'
    )
    return (
        '<div style="background:#12243A;border-radius:8px;border:1px solid #1E3A56;overflow-x:auto;">'
        '<table style="width:100%;border-collapse:collapse;font-size:0.81rem;">'
        f'<thead>{header}</thead>'
        f'<tbody>{rows_html}</tbody>'
        '</table></div>'
    )


# ── Page renderer ─────────────────────────────────────────────────────────

def render_audit_logs(session_state) -> None:
    inject_css()

    user  = session_state.get("user", {})
    top_nav_bar(user.get("full_name", ""), user.get("role", ""))

    page_title(
        "📜 Audit Logs",
        "Security event log — all access, authentication and administrative actions.",
    )

    if not require_permission(session_state, "view_audit_logs"):
        return

    can_export = has_permission(session_state, "export_audit_logs")

    # ── Summary cards ────────────────────────────────────────────────
    counts = _summary_counts()
    c1, c2, c3, c4 = st.columns(4)
    for col, label, val, colour in [
        (c1, "Total Events",    counts["total"],    "#20C5B5"),
        (c2, "Critical Events", counts["critical"], "#E04B4B"),
        (c3, "Warnings",        counts["warnings"], "#F0B45A"),
        (c4, "Login Failures",  counts["failures"], "#7C5CD8"),
    ]:
        col.markdown(
            f'<div style="background:#12243A;border-radius:8px;padding:16px 14px;'
            f'border:1px solid #1E3A56;border-left:3px solid {colour};margin-bottom:8px;">'
            f'<div style="font-size:0.70rem;font-weight:700;text-transform:uppercase;'
            f'letter-spacing:0.08em;color:#5C7A96;">{label}</div>'
            f'<div style="font-size:1.9rem;font-weight:700;color:#DCE8F2;">{val}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Filters ──────────────────────────────────────────────────────
    section_header("🔍 Filter Events")
    f1, f2, f3, f4, f5 = st.columns([1.6, 1.6, 1.0, 1.0, 1.0])
    with f1:
        actor_q    = st.text_input("Actor / Target",
                                   placeholder="e.g. admin, EMP-003",
                                   key="al_actor")
    with f2:
        evt_filter = st.selectbox("Event Type", EVENT_TYPES, key="al_event")
    with f3:
        sev_filter = st.selectbox("Severity",
                                  ["All", "Info", "Warning", "Critical"],
                                  key="al_sev")
    with f4:
        date_from  = st.text_input("From (YYYY-MM-DD)",
                                   placeholder="2026-01-01",
                                   key="al_date_from")
    with f5:
        date_to    = st.text_input("To (YYYY-MM-DD)",
                                   placeholder="2026-12-31",
                                   key="al_date_to")

    # ── Fetch logs ───────────────────────────────────────────────────
    logs = _query_logs(
        actor_q    = actor_q,
        event_type = evt_filter,
        severity   = sev_filter,
        date_from  = date_from,
        date_to    = date_to,
    )

    # ── Toolbar: result count + CSV export ───────────────────────────
    tb1, tb2 = st.columns([3, 1])
    limit_note = " — limit reached, refine filters" if len(logs) == 500 else ""
    tb1.markdown(
        f'<div style="font-size:0.81rem;color:#5C7A96;margin-top:6px;">'
        f'<b style="color:#DCE8F2;">{len(logs)}</b> event(s) found{limit_note}</div>',
        unsafe_allow_html=True,
    )
    if can_export and logs:
        tb2.download_button(
            label="Export CSV",
            data=_to_csv(logs),
            file_name="civicshield_audit_logs.csv",
            mime="text/csv",
            width="stretch",
        )

    # ── Log table (single HTML block — no per-row st.columns) ────────
    section_header("📋 Event Log")

    if not logs:
        st.info("No audit log entries match the selected filters.")
        return

    # Render entire table as a single markdown block
    st.markdown(_build_table_html(logs), unsafe_allow_html=True)
    st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)
