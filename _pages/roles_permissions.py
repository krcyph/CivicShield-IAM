import streamlit as st
from database.db_init import get_connection, log_event
from auth.auth import require_permission, has_permission, ROLE_PERMISSIONS
from ui.components import inject_css, top_nav_bar, page_title, section_header

# ── Role definitions ────────────────────────────────────────────────────

ROLE_DEFINITIONS = [
    {
        "name":        "Super Admin",
        "key":         "superadmin",
        "colour":      "#c0392b",
        "description": "Unrestricted access to all modules and data. Full user, role and policy management.",
        "permissions": [
            "view_dashboard", "view_users", "create_user", "edit_user",
            "delete_user", "activate_user", "deactivate_user",
            "view_roles", "assign_role", "revoke_role", "edit_role",
            "view_policies", "view_audit_logs", "export_audit_logs",
        ],
    },
    {
        "name":        "Department Head",
        "key":         "dept_head",
        "colour":      "#1e5fa8",
        "description": "Can view and edit employees in their department. Read-only access to audit logs and policies.",
        "permissions": [
            "view_dashboard", "view_users", "edit_user",
            "view_roles", "view_policies", "view_audit_logs",
        ],
    },
    {
        "name":        "IT Administrator",
        "key":         "it_admin",
        "colour":      "#8e44ad",
        "description": "Manages accounts and roles. Cannot delete users or export audit data.",
        "permissions": [
            "view_dashboard", "view_users", "create_user", "edit_user",
            "activate_user", "deactivate_user",
            "view_roles", "assign_role",
            "view_policies", "view_audit_logs",
        ],
    },
    {
        "name":        "Auditor",
        "key":         "auditor",
        "colour":      "#27ae60",
        "description": "Read-only access to all modules. Can view and export audit logs. Cannot modify any data.",
        "permissions": [
            "view_dashboard", "view_users",
            "view_roles", "view_policies",
            "view_audit_logs", "export_audit_logs",
        ],
    },
    {
        "name":        "Officer",
        "key":         "officer",
        "colour":      "#7f8c8d",
        "description": "Basic access. Can only view the dashboard. No administrative privileges.",
        "permissions": ["view_dashboard"],
    },
]

ALL_PERMISSIONS = [
    ("view_dashboard",    "View Dashboard"),
    ("view_users",        "View Users"),
    ("create_user",       "Create User"),
    ("edit_user",         "Edit User"),
    ("activate_user",     "Activate User"),
    ("deactivate_user",   "Deactivate User"),
    ("delete_user",       "Delete User"),
    ("view_roles",        "View Roles"),
    ("assign_role",       "Assign Role"),
    ("revoke_role",       "Revoke Role"),
    ("edit_role",         "Edit Role"),
    ("view_policies",     "View Policies"),
    ("view_audit_logs",   "View Audit Logs"),
    ("export_audit_logs", "Export Audit Logs"),
]


# ──────────────────────────────────────────────────────────────────────────
# DB helpers
# ──────────────────────────────────────────────────────────────────────────

def _get_employees_with_roles() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("""
        SELECT id, employee_id, full_name, department, role, account_status
        FROM employees
        ORDER BY full_name
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _assign_role(emp_id: int, new_role: str, actor: str) -> None:
    conn = get_connection()
    conn.execute("UPDATE employees SET role=? WHERE id=?", (new_role, emp_id))
    conn.commit()
    conn.close()
    log_event("ROLE_ASSIGNED", actor, str(emp_id),
              f"Role set to '{new_role}'", severity="Info")


# ──────────────────────────────────────────────────────────────────────────
# Page renderer
# ──────────────────────────────────────────────────────────────────────────

_TICK  = '<span style="color:#20C5B5;font-weight:700;">✓</span>'
_CROSS = '<span style="color:#2A4560;">–</span>'


def render_roles_permissions(session_state) -> None:
    inject_css()

    user  = session_state.get("user", {})
    actor = user.get("username", "unknown")
    top_nav_bar(user.get("full_name", ""), user.get("role", ""))

    page_title(
        "🔐 Roles & Permissions",
        "IAM role definitions, permission matrix and employee role assignment.",
    )

    if not require_permission(session_state, "view_roles"):
        return

    can_assign = has_permission(session_state, "assign_role")

    # ── Role cards ───────────────────────────────────────────────────
    section_header("📌 Role Definitions")
    for i in range(0, len(ROLE_DEFINITIONS), 3):
        chunk = ROLE_DEFINITIONS[i:i+3]
        cols  = st.columns(len(chunk))
        for col, rd in zip(cols, chunk):
            perm_list = "".join(
                f'<li style="color:#DCE8F2;font-size:0.76rem;">{p}</li>'
                for p in rd["permissions"]
            )
            col.markdown(
                f"""
                <div style="background:#12243A;border-radius:8px;padding:16px 14px;
                            border:1px solid #1E3A56;border-left:3px solid {rd['colour']};
                            height:100%;">
                    <div style="font-size:0.95rem;font-weight:700;color:{rd['colour']};
                                margin-bottom:4px;">{rd['name']}</div>
                    <div style="font-size:0.76rem;color:#5C7A96;
                                margin-bottom:10px;">{rd['description']}</div>
                    <ul style="margin:0;padding-left:16px;">{perm_list}</ul>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ── Permission matrix ────────────────────────────────────────────
    section_header("📊 Permission Matrix")

    # Build a table: rows = permissions, cols = roles
    role_names = [rd["name"] for rd in ROLE_DEFINITIONS]
    role_perm_sets = {rd["name"]: set(rd["permissions"]) for rd in ROLE_DEFINITIONS}

    # Table HTML
    th_style = "padding:8px 10px;background:#173B56;color:#DCE8F2;font-size:0.76rem;font-weight:600;text-align:center;"
    td_style = "padding:7px 10px;border-bottom:1px solid #1E3A56;text-align:center;"
    td_label = "padding:7px 10px;border-bottom:1px solid #1E3A56;font-size:0.79rem;color:#DCE8F2;"

    header_row = f'<tr><th style="{th_style}text-align:left;">Permission</th>'
    for rn in role_names:
        rd_obj = next(r for r in ROLE_DEFINITIONS if r["name"] == rn)
        header_row += f'<th style="{th_style}color:{rd_obj["colour"]};">{rn}</th>'
    header_row += "</tr>"

    body_rows = ""
    for perm_key, perm_label in ALL_PERMISSIONS:
        body_rows += f'<tr><td style="{td_label}">{perm_label}</td>'
        for rn in role_names:
            mark = _TICK if perm_key in role_perm_sets[rn] else _CROSS
            body_rows += f'<td style="{td_style}">{mark}</td>'
        body_rows += "</tr>"

    st.markdown(
        f"""
        <div style="background:#12243A;border-radius:8px;border:1px solid #1E3A56;overflow-x:auto;">
            <table style="width:100%;border-collapse:collapse;font-size:0.81rem;">
                <thead>{header_row}</thead>
                <tbody>{body_rows}</tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Role assignment ──────────────────────────────────────────────
    section_header("🔑 Assign Roles to Employees")

    if not can_assign:
        st.info("🔒 You have read-only access to role information. "
                "Super Admin or IT Administrator permissions are required to assign roles.")
        return

    employees    = _get_employees_with_roles()
    role_options = [rd["name"] for rd in ROLE_DEFINITIONS]

    search_ra = st.text_input("🔍 Search by name or employee ID",
                              placeholder="Filter…",
                              key="ra_search")
    q = search_ra.strip().lower()
    filtered = [e for e in employees if not q
                or q in e["full_name"].lower()
                or q in e["employee_id"].lower()]

    if not filtered:
        st.info("No employees match your search.")
        return

    st.markdown(
        '<div style="font-size:0.75rem;color:#5C7A96;margin-bottom:8px;">'
        f'Showing {len(filtered)} of {len(employees)} employees</div>',
        unsafe_allow_html=True,
    )

    # Use a form so the Save button triggers a full rerun
    for emp in filtered:
        emp_id      = emp["id"]
        current_role = emp["role"] if emp["role"] in role_options else role_options[-1]
        current_idx  = role_options.index(current_role)

        with st.container():
            rc = st.columns([0.7, 1.5, 1.1, 1.0, 1.6, 0.9])

            rc[0].markdown(
                f'<span style="font-family:\'IBM Plex Mono\',monospace;font-size:0.77rem;'
                f'color:#20C5B5;">{emp["employee_id"]}</span>',
                unsafe_allow_html=True,
            )
            rc[1].markdown(
                f'<span style="font-weight:600;color:#DCE8F2;">{emp["full_name"]}</span>',
                unsafe_allow_html=True,
            )
            rc[2].markdown(
                f'<span style="color:#5C7A96;font-size:0.81rem;">{emp["department"]}</span>',
                unsafe_allow_html=True,
            )
            # Show current saved role as a read-only badge
            rc[3].markdown(
                f'<span style="background:rgba(32,197,181,0.12);color:#20C5B5;padding:2px 8px;'
                f'border-radius:6px;font-size:0.76rem;font-weight:600;">'
                f'{current_role}</span>',
                unsafe_allow_html=True,
            )

            new_role = rc[4].selectbox(
                "Assign role",
                role_options,
                index=current_idx,
                label_visibility="collapsed",
                key=f"role_sel_{emp_id}",
            )

            if rc[5].button("💾 Save", key=f"role_save_{emp_id}",
                            width="stretch"):
                if new_role != current_role:
                    _assign_role(emp_id, new_role, actor)
                    st.success(
                        f"✅ **{emp['full_name']}** → role changed from "
                        f"**{current_role}** to **{new_role}**."
                    )
                else:
                    st.info(f"{emp['full_name']} already has the role **{new_role}**.")
                st.rerun()
