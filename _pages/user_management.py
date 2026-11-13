import streamlit as st
from database.db_init import get_connection, log_event
from auth.auth import require_permission, has_permission
from ui.components import inject_css, top_nav_bar, page_title, section_header, status_badge

DEPARTMENTS = [
    "Cybersecurity", "Finance", "Human Resources",
    "IT Infrastructure", "Citizen Services",
    "Legal Affairs", "Policy & Compliance",
]
CLEARANCE_LEVELS = ["Public", "Confidential", "Secret", "Top Secret"]
STATUSES = ["Active", "Inactive"]
ROLES = ["Officer", "Auditor", "IT Administrator", "Department Head", "Super Admin"]


# ──────────────────────────────────────────────────────────────────────────
# DB helpers
# ──────────────────────────────────────────────────────────────────────────

def _get_all_employees() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("""
        SELECT id, employee_id, full_name, email, department, job_title,
               role, clearance_level, account_status, last_login, created_at
        FROM employees
        ORDER BY full_name
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _get_employee(emp_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM employees WHERE id = ?", (emp_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def _next_employee_id() -> str:
    conn = get_connection()
    row = conn.execute("SELECT MAX(CAST(SUBSTR(employee_id,5) AS INTEGER)) FROM employees").fetchone()
    conn.close()
    next_num = (row[0] or 0) + 1
    return f"EMP-{next_num:03d}"


def _create_employee(data: dict, actor: str) -> str | None:
    """Insert a new employee. Returns error string or None on success."""
    # Input validation
    for field in ("full_name", "email", "department", "job_title"):
        if not data.get(field, "").strip():
            return f"Field '{field}' is required."
    if "@" not in data["email"] or "." not in data["email"].split("@")[-1]:
        return "Invalid email address."

    conn = get_connection()
    try:
        emp_id = _next_employee_id()
        conn.execute("""
            INSERT INTO employees
                (employee_id, full_name, email, department, job_title,
                 role, clearance_level, account_status)
            VALUES (?,?,?,?,?,?,?,?)
        """, (
            emp_id,
            data["full_name"].strip(),
            data["email"].strip().lower(),
            data["department"],
            data["job_title"].strip(),
            data["role"],
            data["clearance_level"],
            data["account_status"],
        ))
        conn.commit()
        log_event("USER_CREATED", actor, emp_id,
                  f"New employee '{data['full_name']}' created", severity="Info")
        return None
    except Exception as exc:
        return str(exc)
    finally:
        conn.close()


def _update_employee(emp_id: int, data: dict, actor: str) -> str | None:
    """Update an existing employee. Returns error string or None on success."""
    for field in ("full_name", "email", "department", "job_title"):
        if not data.get(field, "").strip():
            return f"Field '{field}' is required."
    if "@" not in data["email"] or "." not in data["email"].split("@")[-1]:
        return "Invalid email address."

    conn = get_connection()
    try:
        conn.execute("""
            UPDATE employees
            SET full_name=?, email=?, department=?, job_title=?,
                role=?, clearance_level=?, account_status=?
            WHERE id=?
        """, (
            data["full_name"].strip(),
            data["email"].strip().lower(),
            data["department"],
            data["job_title"].strip(),
            data["role"],
            data["clearance_level"],
            data["account_status"],
            emp_id,
        ))
        conn.commit()
        log_event("USER_UPDATED", actor, str(emp_id),
                  f"Employee record updated", severity="Info")
        return None
    except Exception as exc:
        return str(exc)
    finally:
        conn.close()


def _toggle_status(emp_id: int, new_status: str, actor: str) -> None:
    event = "ACCOUNT_ENABLED" if new_status == "Active" else "ACCOUNT_DISABLED"
    conn = get_connection()
    conn.execute(
        "UPDATE employees SET account_status=? WHERE id=?",
        (new_status, emp_id),
    )
    conn.commit()
    conn.close()
    log_event(event, actor, str(emp_id),
              f"Account set to {new_status}", severity="Info")


# ──────────────────────────────────────────────────────────────────────────
# Page renderer
# ──────────────────────────────────────────────────────────────────────────

def render_user_management(session_state) -> None:
    inject_css()

    user = session_state.get("user", {})
    actor = user.get("username", "unknown")
    top_nav_bar(user.get("full_name", ""), user.get("role", ""))

    page_title(
        "👥 User Management",
        "Search, create, edit and manage employee accounts.",
    )

    # ── Permission check ────────────────────────────────────────────
    if not require_permission(session_state, "view_users"):
        return

    can_create   = has_permission(session_state, "create_user")
    can_edit     = has_permission(session_state, "edit_user")
    can_toggle   = has_permission(session_state, "activate_user") or has_permission(session_state, "deactivate_user")

    # ── Session state keys for this page ────────────────────────────
    if "um_search"     not in st.session_state: st.session_state["um_search"]     = ""
    if "um_dept"       not in st.session_state: st.session_state["um_dept"]       = "All"
    if "um_status"     not in st.session_state: st.session_state["um_status"]     = "All"
    if "um_editing_id" not in st.session_state: st.session_state["um_editing_id"] = None
    if "um_show_add"   not in st.session_state: st.session_state["um_show_add"]   = False

    # ── Toolbar ─────────────────────────────────────────────────────
    tcol1, tcol2, tcol3, tcol4 = st.columns([2.5, 1.5, 1.2, 1.2])
    with tcol1:
        search = st.text_input("🔍 Search name / email / ID",
                               value=st.session_state["um_search"],
                               placeholder="Type to filter…",
                               label_visibility="collapsed")
        st.session_state["um_search"] = search
    with tcol2:
        dept_opts = ["All"] + DEPARTMENTS
        dept_filter = st.selectbox("Department", dept_opts, label_visibility="collapsed",
                                   index=dept_opts.index(st.session_state["um_dept"]))
        st.session_state["um_dept"] = dept_filter
    with tcol3:
        stat_opts = ["All", "Active", "Inactive"]
        stat_filter = st.selectbox("Status", stat_opts, label_visibility="collapsed",
                                   index=stat_opts.index(st.session_state["um_status"]))
        st.session_state["um_status"] = stat_filter
    with tcol4:
        if can_create:
            if st.button("➕ Add Employee", width="stretch", type="primary"):
                st.session_state["um_show_add"]   = True
                st.session_state["um_editing_id"] = None

    # ── Add employee form ────────────────────────────────────────────
    if st.session_state["um_show_add"] and can_create:
        section_header("➕ New Employee")
        with st.form("add_employee_form"):
            a1, a2 = st.columns(2)
            with a1:
                fn   = st.text_input("Full Name *")
                em   = st.text_input("Email *")
                jt   = st.text_input("Job Title *")
            with a2:
                dp   = st.selectbox("Department *", DEPARTMENTS)
                rl   = st.selectbox("Role", ROLES)
                cl   = st.selectbox("Clearance Level", CLEARANCE_LEVELS)
                st_  = st.selectbox("Account Status", STATUSES)

            c_sub, c_can = st.columns(2)
            with c_sub:
                add_ok = st.form_submit_button("💾 Save Employee", width="stretch", type="primary")
            with c_can:
                add_cancel = st.form_submit_button("✕ Cancel", width="stretch")

        if add_ok:
            err = _create_employee(
                {"full_name": fn, "email": em, "job_title": jt,
                 "department": dp, "role": rl, "clearance_level": cl,
                 "account_status": st_},
                actor,
            )
            if err:
                st.error(err)
            else:
                st.success("✅ Employee created successfully.")
                st.session_state["um_show_add"] = False
                st.rerun()
        elif add_cancel:
            st.session_state["um_show_add"] = False
            st.rerun()

    # ── Edit employee form ───────────────────────────────────────────
    edit_id = st.session_state["um_editing_id"]
    if edit_id and can_edit:
        emp = _get_employee(edit_id)
        if emp:
            section_header(f"✏️ Edit Employee — {emp['full_name']}")
            with st.form("edit_employee_form"):
                e1, e2 = st.columns(2)
                with e1:
                    fn2  = st.text_input("Full Name *",  value=emp["full_name"])
                    em2  = st.text_input("Email *",      value=emp["email"])
                    jt2  = st.text_input("Job Title *",  value=emp["job_title"])
                with e2:
                    dp2  = st.selectbox("Department *", DEPARTMENTS,
                                        index=DEPARTMENTS.index(emp["department"]) if emp["department"] in DEPARTMENTS else 0)
                    rl2  = st.selectbox("Role", ROLES,
                                        index=ROLES.index(emp["role"]) if emp["role"] in ROLES else 0)
                    cl2  = st.selectbox("Clearance Level", CLEARANCE_LEVELS,
                                        index=CLEARANCE_LEVELS.index(emp["clearance_level"]) if emp["clearance_level"] in CLEARANCE_LEVELS else 0)
                    st2_ = st.selectbox("Account Status", STATUSES,
                                        index=STATUSES.index(emp["account_status"]) if emp["account_status"] in STATUSES else 0)

                u1, u2 = st.columns(2)
                with u1:
                    upd_ok = st.form_submit_button("💾 Update Employee", width="stretch", type="primary")
                with u2:
                    upd_cancel = st.form_submit_button("✕ Cancel", width="stretch")

            if upd_ok:
                err = _update_employee(
                    edit_id,
                    {"full_name": fn2, "email": em2, "job_title": jt2,
                     "department": dp2, "role": rl2, "clearance_level": cl2,
                     "account_status": st2_},
                    actor,
                )
                if err:
                    st.error(err)
                else:
                    st.success("✅ Employee updated.")
                    st.session_state["um_editing_id"] = None
                    st.rerun()
            elif upd_cancel:
                st.session_state["um_editing_id"] = None
                st.rerun()

    # ── Employee table ───────────────────────────────────────────────
    section_header("📋 Employee Directory")

    employees = _get_all_employees()

    # Apply filters
    q = search.lower()
    filtered = [
        e for e in employees
        if (not q or q in e["full_name"].lower()
                   or q in e["email"].lower()
                   or q in e["employee_id"].lower())
        and (dept_filter == "All" or e["department"] == dept_filter)
        and (stat_filter == "All" or e["account_status"] == stat_filter)
    ]

    st.markdown(
        f'<div style="font-size:0.8rem;color:#5C7A96;margin-bottom:8px;">'
        f'Showing <b>{len(filtered)}</b> of <b>{len(employees)}</b> employees</div>',
        unsafe_allow_html=True,
    )

    if not filtered:
        st.info("No employees match your filters.")
        return

    # Table header
    header_cols = ["ID", "Full Name", "Department", "Job Title", "Role",
                   "Clearance", "Status", "Last Login"]
    if can_edit or can_toggle:
        header_cols.append("Actions")

    col_widths = [0.7, 1.4, 1.2, 1.4, 1.1, 1.0, 0.7, 1.0]
    if can_edit or can_toggle:
        col_widths.append(1.1)

    # Header row
    hcols = st.columns(col_widths)
    header_style = "font-size:0.73rem;font-weight:700;color:#5C7A96;text-transform:uppercase;border-bottom:1px solid #1E3A56;padding-bottom:4px;"
    for hc, label in zip(hcols, header_cols):
        hc.markdown(f'<div style="{header_style}">{label}</div>', unsafe_allow_html=True)

    # Data rows
    for emp in filtered:
        row_cols = st.columns(col_widths)
        badge_html = status_badge(emp["account_status"])

        row_cols[0].markdown(
            f'<span style="font-family:\'IBM Plex Mono\',monospace;font-size:0.77rem;color:#20C5B5;">'
            f'{emp["employee_id"]}</span>', unsafe_allow_html=True)
        row_cols[1].markdown(
            f'<span style="font-weight:600;color:#DCE8F2;">{emp["full_name"]}</span>',
            unsafe_allow_html=True)
        row_cols[2].markdown(f'<span style="color:#5C7A96;">{emp["department"]}</span>', unsafe_allow_html=True)
        row_cols[3].markdown(f'<span style="color:#DCE8F2;">{emp["job_title"]}</span>', unsafe_allow_html=True)
        row_cols[4].markdown(f'<span style="color:#DCE8F2;">{emp["role"]}</span>', unsafe_allow_html=True)
        row_cols[5].markdown(f'<span style="color:#DCE8F2;">{emp["clearance_level"]}</span>', unsafe_allow_html=True)
        row_cols[6].markdown(badge_html, unsafe_allow_html=True)
        row_cols[7].markdown(
            f'<span style="font-size:0.77rem;color:#5C7A96;">'
            f'{emp["last_login"] or "—"}</span>', unsafe_allow_html=True)

        if (can_edit or can_toggle) and len(row_cols) > 8:
            action_col = row_cols[8]
            btn_key_edit   = f"edit_{emp['id']}"
            btn_key_toggle = f"toggle_{emp['id']}"

            if can_edit:
                if action_col.button("✏️", key=btn_key_edit, help="Edit employee"):
                    st.session_state["um_editing_id"] = emp["id"]
                    st.session_state["um_show_add"]   = False
                    st.rerun()

            if can_toggle:
                if emp["account_status"] == "Active":
                    if action_col.button("🚫", key=btn_key_toggle, help="Deactivate"):
                        _toggle_status(emp["id"], "Inactive", actor)
                        st.rerun()
                else:
                    if action_col.button("✅", key=btn_key_toggle, help="Activate"):
                        _toggle_status(emp["id"], "Active", actor)
                        st.rerun()
