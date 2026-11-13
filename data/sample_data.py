"""
data/sample_data.py
--------------------
Seeds the database with fictional government employee records for demonstration
purposes.  All names, IDs, emails and departments are entirely made up.

Call seed_employees() once during app startup — it checks whether data already
exists before inserting, so it is safe to call on every run.
"""

import sqlite3
from database.db_init import get_connection

# ---------------------------------------------------------------------------
# Fictional employee data
# ---------------------------------------------------------------------------

SAMPLE_EMPLOYEES = [
    # (employee_id, full_name, email, department, job_title, role, clearance_level, account_status, last_login)
    ("EMP-001", "Margaret L. Thornton",  "m.thornton@csd.gov",  "Human Resources",       "HR Director",                   "Department Head",   "Secret",        "Active",   "2025-06-10 09:14"),
    ("EMP-002", "James R. Whitfield",    "j.whitfield@csd.gov", "IT Infrastructure",     "Senior Systems Administrator",  "IT Administrator",  "Top Secret",    "Active",   "2025-06-11 08:02"),
    ("EMP-003", "Priya S. Anand",        "p.anand@csd.gov",     "Cybersecurity",          "Security Analyst",              "Auditor",           "Top Secret",    "Active",   "2025-06-11 10:45"),
    ("EMP-004", "Robert O. Flanagan",    "r.flanagan@csd.gov",  "Finance",               "Budget Controller",             "Department Head",   "Confidential",  "Active",   "2025-06-09 14:30"),
    ("EMP-005", "Sarah K. Beaumont",     "s.beaumont@csd.gov",  "Legal Affairs",         "Senior Counsel",                "Department Head",   "Secret",        "Active",   "2025-06-10 11:00"),
    ("EMP-006", "Daniel A. Voss",        "d.voss@csd.gov",      "IT Infrastructure",     "Network Engineer",              "IT Administrator",  "Confidential",  "Active",   "2025-06-11 07:55"),
    ("EMP-007", "Alicia M. Reyes",       "a.reyes@csd.gov",     "Citizen Services",      "Service Desk Lead",             "Officer",           "Public",        "Active",   "2025-06-10 16:22"),
    ("EMP-008", "Thomas P. Nguyen",      "t.nguyen@csd.gov",    "Cybersecurity",          "Penetration Tester",            "Auditor",           "Top Secret",    "Active",   "2025-06-11 09:30"),
    ("EMP-009", "Helen B. Kowalski",     "h.kowalski@csd.gov",  "Policy & Compliance",   "Compliance Officer",            "Auditor",           "Confidential",  "Active",   "2025-06-08 13:10"),
    ("EMP-010", "Marcus J. Steele",      "m.steele@csd.gov",    "Human Resources",       "Recruitment Specialist",        "Officer",           "Public",        "Inactive", "2025-05-20 10:00"),
    ("EMP-011", "Fatima O. Hassan",      "f.hassan@csd.gov",    "Finance",               "Accounts Payable Clerk",        "Officer",           "Public",        "Active",   "2025-06-11 08:50"),
    ("EMP-012", "Gregory C. Miles",      "g.miles@csd.gov",     "IT Infrastructure",     "Cloud Architect",               "IT Administrator",  "Secret",        "Active",   "2025-06-10 15:05"),
    ("EMP-013", "Laura T. Simmons",      "l.simmons@csd.gov",   "Citizen Services",      "Case Worker",                   "Officer",           "Public",        "Inactive", "2025-04-15 09:45"),
    ("EMP-014", "Anthony D. Ferreira",   "a.ferreira@csd.gov",  "Policy & Compliance",   "Policy Analyst",                "Officer",           "Confidential",  "Active",   "2025-06-09 12:00"),
    ("EMP-015", "Natalie R. Brooks",     "n.brooks@csd.gov",    "Legal Affairs",         "Paralegal",                     "Officer",           "Confidential",  "Active",   "2025-06-10 10:30"),
    ("EMP-016", "Kevin P. Okafor",       "k.okafor@csd.gov",    "Cybersecurity",          "SOC Analyst",                   "Auditor",           "Secret",        "Active",   "2025-06-11 06:30"),
    ("EMP-017", "Diana L. Huang",        "d.huang@csd.gov",     "IT Infrastructure",     "Database Administrator",        "IT Administrator",  "Secret",        "Active",   "2025-06-11 08:10"),
    ("EMP-018", "Stephen M. Grant",      "s.grant@csd.gov",     "Finance",               "Financial Analyst",             "Officer",           "Confidential",  "Inactive", "2025-03-28 14:00"),
    ("EMP-019", "Yasmine A. Tremblay",   "y.tremblay@csd.gov",  "Citizen Services",      "Digital Services Officer",      "Officer",           "Public",        "Active",   "2025-06-10 09:00"),
    ("EMP-020", "Patrick H. O'Brien",    "p.obrien@csd.gov",    "Human Resources",       "Learning & Development Mgr",    "Department Head",   "Public",        "Active",   "2025-06-09 11:20"),
]


# ---------------------------------------------------------------------------
# Audit log seed data
# ---------------------------------------------------------------------------

SAMPLE_AUDIT_LOGS = [
    # (event_type, actor, target, details, ip_address, severity)
    ("LOGIN_SUCCESS",    "admin",         "System",         "Admin login successful",               "10.0.1.5",   "Info"),
    ("LOGIN_FAILURE",    "unknown_user",  "System",         "Failed login attempt — unknown user",  "203.0.113.7","Warning"),
    ("USER_CREATED",     "admin",         "EMP-020",        "New employee account provisioned",     "10.0.1.5",   "Info"),
    ("ROLE_ASSIGNED",    "admin",         "EMP-003",        "Role 'Security Auditor' assigned",     "10.0.1.5",   "Info"),
    ("PERMISSION_DENIED","j.whitfield",   "AuditLog Module","Attempted access to restricted module","10.0.2.11",  "Warning"),
    ("PASSWORD_CHANGED", "p.anand",       "EMP-003",        "Password changed by user",             "10.0.3.44",  "Info"),
    ("ACCOUNT_DISABLED", "admin",         "EMP-013",        "Account disabled — extended leave",    "10.0.1.5",   "Info"),
    ("LOGIN_FAILURE",    "m.steele",      "System",         "Multiple failed login attempts",       "10.0.4.21",  "Critical"),
    ("POLICY_UPDATED",   "admin",         "IAM Policy v2",  "Password policy updated",              "10.0.1.5",   "Info"),
    ("ROLE_REVOKED",     "admin",         "EMP-018",        "Role 'Finance Manager' revoked",       "10.0.1.5",   "Warning"),
    ("LOGIN_SUCCESS",    "auditor",       "System",         "Auditor login successful",             "10.0.1.9",   "Info"),
    ("DATA_EXPORT",      "auditor",       "AuditLog",       "Audit log exported to CSV",            "10.0.1.9",   "Info"),
    ("LOGIN_FAILURE",    "a.reyes",       "System",         "Incorrect password entered",           "10.0.5.62",  "Warning"),
    ("SESSION_TIMEOUT",  "r.flanagan",    "System",         "Session expired after inactivity",     "10.0.2.88",  "Info"),
    ("USER_DELETED",     "admin",         "EMP-010",        "Inactive account removed from system", "10.0.1.5",   "Critical"),
]


# ---------------------------------------------------------------------------
# Seeding functions
# ---------------------------------------------------------------------------

# Mapping of employee_id -> intended role for migration of existing DBs
_ROLE_MAP = {row[0]: row[5] for row in SAMPLE_EMPLOYEES}


def seed_employees() -> None:
    """Insert sample employees if the employees table is empty.
    Also migrates existing rows that have role='Officer' (default) to
    the intended role defined in SAMPLE_EMPLOYEES.
    """
    conn    = get_connection()
    cursor  = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM employees")
    count = cursor.fetchone()[0]

    if count == 0:
        # Fresh insert — include role in the tuple
        cursor.executemany(
            """INSERT INTO employees
               (employee_id, full_name, email, department, job_title,
                role, clearance_level, account_status, last_login)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            SAMPLE_EMPLOYEES,
        )
        conn.commit()
    else:
        # Existing rows — update role where it's still the default 'Officer'
        # but only for employees that *should* have a different role.
        for emp_id, intended_role in _ROLE_MAP.items():
            if intended_role != "Officer":
                cursor.execute(
                    "UPDATE employees SET role=? WHERE employee_id=? AND role='Officer'",
                    (intended_role, emp_id),
                )
        conn.commit()

    conn.close()


def seed_audit_logs() -> None:
    """Insert sample audit log entries if the audit_logs table is empty."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM audit_logs")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    cursor.executemany(
        """INSERT INTO audit_logs
           (event_type, actor, target, details, ip_address, severity)
           VALUES (?,?,?,?,?,?)""",
        SAMPLE_AUDIT_LOGS,
    )
    conn.commit()
    conn.close()


def seed_all() -> None:
    """Seed all sample data. Safe to call on every startup."""
    seed_employees()
    seed_audit_logs()


# ---------------------------------------------------------------------------
# Query helpers used by the dashboard and other pages
# ---------------------------------------------------------------------------

def get_summary_stats() -> dict:
    """
    Return a dict of summary statistics for the dashboard cards.

    Keys
    ----
    total_employees, active_accounts, inactive_accounts,
    security_events, departments, top_secret_clearances
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM employees")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM employees WHERE account_status='Active'")
    active = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM employees WHERE account_status='Inactive'")
    inactive = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM audit_logs WHERE severity IN ('Warning','Critical')")
    security_events = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT department) FROM employees")
    departments = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM employees WHERE clearance_level='Top Secret'")
    ts_clearances = cursor.fetchone()[0]

    conn.close()

    return {
        "total_employees":      total,
        "active_accounts":      active,
        "inactive_accounts":    inactive,
        "security_events":      security_events,
        "departments":          departments,
        "top_secret_clearances": ts_clearances,
    }


def get_employees_df():
    """Return all employees as a list of dicts (for display in tables)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT employee_id, full_name, email, department,
               job_title, clearance_level, account_status, last_login
        FROM employees
        ORDER BY full_name
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_recent_audit_logs(limit: int = 10) -> list[dict]:
    """Return the most recent audit log entries."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT event_type, actor, target, details, ip_address, severity, created_at
        FROM audit_logs
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_department_counts() -> list[dict]:
    """Return employee counts grouped by department."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT department, COUNT(*) AS count
        FROM employees
        GROUP BY department
        ORDER BY count DESC
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_clearance_counts() -> list[dict]:
    """Return employee counts grouped by clearance level."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT clearance_level, COUNT(*) AS count
        FROM employees
        GROUP BY clearance_level
        ORDER BY count DESC
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows
