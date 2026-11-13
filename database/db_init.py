"""
database/db_init.py
--------------------
Handles SQLite database creation and schema initialization for CivicShield IAM.
All tables are created here with IF NOT EXISTS guards so this module is safe
to call on every application startup.
"""

import sqlite3
import os
import hashlib

# Path to the SQLite database file (stored at project root)
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "govsecure.db")


def get_connection() -> sqlite3.Connection:
    """Return a connection to the SQLite database with row_factory set."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # rows behave like dicts
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _pbkdf2_hash(password: str) -> str:
    """Hash a password with PBKDF2-HMAC-SHA256 + a per-password random salt.

    Format stored:  pbkdf2$<iterations>$<hex-salt>$<hex-digest>
    """
    import os as _os
    salt = _os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 260_000)
    return f"pbkdf2$260000${salt.hex()}${dk.hex()}"


def initialize_database() -> None:
    """
    Create all required tables and seed initial data if the database is new.
    Safe to call multiple times — uses IF NOT EXISTS on every table.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # ------------------------------------------------------------------
    # 1. admin_users  — system administrators who log into this dashboard
    # ------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin_users (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            username        TEXT    NOT NULL UNIQUE,
            password_hash   TEXT    NOT NULL,
            full_name       TEXT    NOT NULL,
            role            TEXT    NOT NULL DEFAULT 'admin',
            failed_attempts INTEGER NOT NULL DEFAULT 0,
            locked_until    TEXT,
            created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # ------------------------------------------------------------------
    # 2. employees  — fictional government department employees
    # ------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id     TEXT    NOT NULL UNIQUE,
            full_name       TEXT    NOT NULL,
            email           TEXT    NOT NULL UNIQUE,
            department      TEXT    NOT NULL,
            job_title       TEXT    NOT NULL,
            role            TEXT    NOT NULL DEFAULT 'Officer',
            clearance_level TEXT    NOT NULL DEFAULT 'Public',
            account_status  TEXT    NOT NULL DEFAULT 'Active',
            created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
            last_login      TEXT
        )
    """)

    # Add role column to employees if it was missing in older DB
    try:
        cursor.execute("ALTER TABLE employees ADD COLUMN role TEXT NOT NULL DEFAULT 'Officer'")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # column already exists

    # Add lockout columns to admin_users if missing in older DB
    for col_def in [
        "ALTER TABLE admin_users ADD COLUMN failed_attempts INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE admin_users ADD COLUMN locked_until TEXT",
    ]:
        try:
            cursor.execute(col_def)
            conn.commit()
        except sqlite3.OperationalError:
            pass

    # ------------------------------------------------------------------
    # 3. roles  — IAM roles that can be assigned to employees
    # ------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS roles (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            role_name   TEXT    NOT NULL UNIQUE,
            description TEXT,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # ------------------------------------------------------------------
    # 4. employee_roles  — many-to-many mapping of employees to roles
    # ------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employee_roles (
            employee_id INTEGER NOT NULL REFERENCES employees(id),
            role_id     INTEGER NOT NULL REFERENCES roles(id),
            assigned_at TEXT    NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (employee_id, role_id)
        )
    """)

    # ------------------------------------------------------------------
    # 5. audit_logs  — security and access event log
    # ------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type  TEXT    NOT NULL,
            actor       TEXT    NOT NULL,
            target      TEXT,
            details     TEXT,
            ip_address  TEXT,
            severity    TEXT    NOT NULL DEFAULT 'Info',
            created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    conn.commit()

    # Seed data only if tables are empty
    _seed_admin_users(cursor, conn)
    _seed_roles(cursor, conn)

    conn.close()


# -----------------------------------------------------------------------
# Private seed helpers
# -----------------------------------------------------------------------

def _seed_admin_users(cursor: sqlite3.Cursor, conn: sqlite3.Connection) -> None:
    """Insert default admin accounts if none exist."""
    cursor.execute("SELECT COUNT(*) FROM admin_users")
    if cursor.fetchone()[0] > 0:
        return  # already seeded

    admins = [
        ("admin",   _pbkdf2_hash("Admin@1234"),  "System Administrator",    "superadmin"),
        ("auditor", _pbkdf2_hash("Audit@5678"),  "Jane Blackwell",           "auditor"),
    ]
    cursor.executemany(
        "INSERT INTO admin_users (username, password_hash, full_name, role) VALUES (?,?,?,?)",
        admins,
    )
    conn.commit()


def _seed_roles(cursor: sqlite3.Cursor, conn: sqlite3.Connection) -> None:
    """Insert standard IAM roles if the roles table is empty."""
    cursor.execute("SELECT COUNT(*) FROM roles")
    if cursor.fetchone()[0] > 0:
        return

    roles = [
        ("Super Admin",       "Full system access — unrestricted"),
        ("Department Head",   "Manage department employees and view reports"),
        ("IT Administrator",  "Manage accounts, roles and system settings"),
        ("Auditor",           "Read-only access to audit logs and reports"),
        ("Officer",           "Basic citizen-services access only"),
    ]
    cursor.executemany(
        "INSERT INTO roles (role_name, description) VALUES (?,?)",
        roles,
    )
    conn.commit()


# -----------------------------------------------------------------------
# Audit log helper — call from anywhere to record an event
# -----------------------------------------------------------------------

def log_event(
    event_type: str,
    actor: str,
    target: str = "",
    details: str = "",
    ip_address: str = "",
    severity: str = "Info",
) -> None:
    """Insert a single audit log entry."""
    conn = get_connection()
    conn.execute(
        """INSERT INTO audit_logs (event_type, actor, target, details, ip_address, severity)
           VALUES (?,?,?,?,?,?)""",
        (event_type, actor, target or "", details or "", ip_address or "", severity),
    )
    conn.commit()
    conn.close()
