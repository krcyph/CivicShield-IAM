import streamlit as st
from auth.auth import require_permission
from ui.components import inject_css, top_nav_bar, page_title, section_header

# ── Policy data ──────────────────────────────────────────────────────────

POLICIES = [
    {
        "icon":     "🔑",
        "title":    "Password Policy",
        "colour":   "#1e5fa8",
        "items": [
            ("Minimum Length",            "12 characters"),
            ("Complexity",                "Must contain uppercase, lowercase, digit and special character"),
            ("Maximum Age",               "90 days — users must change password after this period"),
            ("Password History",          "Cannot reuse the last 10 passwords"),
            ("Dictionary Check",          "Common and easily-guessed passwords are rejected"),
        ],
    },
    {
        "icon":     "🚫",
        "title":    "Account Lockout Policy",
        "colour":   "#c0392b",
        "items": [
            ("Maximum Failed Attempts",   "5 consecutive failed login attempts"),
            ("Lockout Duration",          "15 minutes — account auto-unlocks after this period"),
            ("Lockout Scope",             "Applies to all admin and employee accounts"),
            ("Audit on Lockout",          "Every lockout event is recorded in the audit log"),
        ],
    },
    {
        "icon":     "⏱️",
        "title":    "Session & Timeout Policy",
        "colour":   "#e67e22",
        "items": [
            ("Idle Session Timeout",      "30 minutes of inactivity automatically logs the user out"),
            ("Absolute Session Limit",    "Maximum 8-hour session regardless of activity"),
            ("Concurrent Sessions",       "Single active session per account enforced"),
            ("Re-authentication",         "Required after password change or role update"),
        ],
    },
    {
        "icon":     "🛡️",
        "title":    "Least-Privilege Access",
        "colour":   "#8e44ad",
        "items": [
            ("Default Access",            "New accounts receive Officer role (dashboard view only)"),
            ("Role Escalation",           "Elevated roles require Super Admin or IT Admin approval"),
            ("Access Reviews",            "Quarterly review of all role assignments mandatory"),
            ("Just-in-Time Access",       "Temporary elevated access expires automatically"),
            ("Department Segregation",    "Department Heads can only manage their own department's staff"),
        ],
    },
    {
        "icon":     "✅",
        "title":    "Access Approval Workflow",
        "colour":   "#27ae60",
        "items": [
            ("New Account Provisioning",  "Requires line-manager approval and HR sign-off"),
            ("Role Assignment",           "Super Admin or IT Administrator authorisation required"),
            ("Sensitive Module Access",   "Top Secret clearance requests require Security Officer approval"),
            ("Contractor Accounts",       "Temporary accounts created with mandatory expiry date"),
            ("Emergency Access",          "Break-glass procedures logged with post-incident review"),
        ],
    },
    {
        "icon":     "📋",
        "title":    "Audit & Monitoring Policy",
        "colour":   "#0a1628",
        "items": [
            ("Log Retention",             "All audit logs retained for minimum 7 years"),
            ("Real-time Alerting",        "Critical security events trigger immediate notifications"),
            ("Log Integrity",             "Audit logs are append-only; modifications are prohibited"),
            ("Access to Logs",            "Only Auditor and Super Admin roles can view audit logs"),
            ("Data Export",               "CSV export of audit data requires Auditor or Super Admin role"),
        ],
    },
    {
        "icon":     "🔒",
        "title":    "Data Protection & Encryption",
        "colour":   "#2c3e50",
        "items": [
            ("Password Storage",          "PBKDF2-HMAC-SHA256 with 260,000 iterations and unique salt per password"),
            ("Data at Rest",              "SQLite database encrypted at filesystem level on production systems"),
            ("Data in Transit",           "TLS 1.3 enforced for all web traffic; plain HTTP rejected"),
            ("PII Handling",              "Employee personal data processed under Data Protection Act 2025"),
            ("Key Management",            "Encryption keys stored separately in Hardware Security Modules (HSM)"),
        ],
    },
]


def render_iam_policies(session_state) -> None:
    inject_css()

    user = session_state.get("user", {})
    top_nav_bar(user.get("full_name", ""), user.get("role", ""))

    page_title(
        "📋 IAM Policies",
        "Security policies governing identity and access management across the organisation.",
    )

    if not require_permission(session_state, "view_policies"):
        return

    # ── Policy summary banner ────────────────────────────────────────
    st.markdown(
        """
        <div style="background:#12243A;border:1px solid #1E3A56;border-left:3px solid #20C5B5;
                    border-radius:8px;padding:16px 20px;margin-bottom:24px;">
            <div style="font-size:0.92rem;font-weight:700;margin-bottom:6px;color:#DCE8F2;">
                🛡️ CivicShield IAM — Security Policy Framework v2.1
            </div>
            <div style="font-size:0.80rem;color:#5C7A96;line-height:1.6;">
                These policies comply with the <b style="color:#DCE8F2;">Government Cybersecurity Act</b> and
                <b style="color:#DCE8F2;">ISO/IEC 27001:2022</b>. All access to systems is subject
                to these controls. Policies are reviewed annually by the Security Committee.
                Last reviewed: <b style="color:#DCE8F2;">January 2026</b>.
                <span style="color:#F0B45A;font-size:0.74rem;display:block;margin-top:6px;">
                    Academic demonstration only — not an official government document.
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Render policies in a 2-column layout
    for i in range(0, len(POLICIES), 2):
        pair = POLICIES[i:i+2]
        cols = st.columns(len(pair))
        for col, policy in zip(cols, pair):
            rows_html = ""
            for label, value in policy["items"]:
                rows_html += f"""
                <tr style="border-bottom:1px solid #1E3A56;">
                    <td style="padding:7px 10px;font-size:0.78rem;font-weight:600;
                               color:#5C7A96;white-space:nowrap;width:38%;">{label}</td>
                    <td style="padding:7px 10px;font-size:0.78rem;color:#DCE8F2;">{value}</td>
                </tr>
                """
            col.markdown(
                f"""
                <div style="background:#12243A;border-radius:8px;padding:16px;
                            border:1px solid #1E3A56;border-top:3px solid {policy['colour']};
                            margin-bottom:20px;height:calc(100% - 20px);">
                    <div style="font-size:0.92rem;font-weight:700;
                                color:{policy['colour']};margin-bottom:12px;">
                        {policy['icon']} &nbsp;{policy['title']}
                    </div>
                    <table style="width:100%;border-collapse:collapse;">
                        <tbody>{rows_html}</tbody>
                    </table>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ── Policy acceptance notice ─────────────────────────────────────
    st.markdown(
        """
        <div style="background:rgba(240,180,90,0.08);border:1px solid #1E3A56;
                    border-left:3px solid #F0B45A;border-radius:8px;
                    padding:14px 16px;margin-top:8px;font-size:0.80rem;color:#DCE8F2;">
            <b style="color:#F0B45A;">Policy Acknowledgement:</b> By accessing this system,
            all users acknowledge that they have read, understood and agree to abide by the
            CivicShield IAM Security Policies. Non-compliance may result in disciplinary
            action under applicable regulations.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
