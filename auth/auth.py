import hashlib
import os
import sqlite3
from collections.abc import MutableMapping
from datetime import datetime, timedelta
from database.db_init import get_connection, log_event

# ── Policy constants ────────────────────────────────────────────────────
MAX_FAILED_ATTEMPTS = 5          # lock after this many consecutive failures
LOCKOUT_MINUTES     = 15         # how long the account stays locked


# -----------------------------------------------------------------------
# Permission matrix
# role → frozenset of allowed permission strings
# -----------------------------------------------------------------------

ROLE_PERMISSIONS: dict[str, frozenset] = {
    "superadmin": frozenset({
        "view_dashboard",
        "view_users", "create_user", "edit_user", "delete_user",
        "activate_user", "deactivate_user",
        "view_roles", "assign_role", "revoke_role", "edit_role",
        "view_policies",
        "view_audit_logs", "export_audit_logs",
    }),
    "auditor": frozenset({
        "view_dashboard",
        "view_users",
        "view_roles",
        "view_policies",
        "view_audit_logs", "export_audit_logs",
    }),
    "it_admin": frozenset({
        "view_dashboard",
        "view_users", "create_user", "edit_user",
        "activate_user", "deactivate_user",
        "view_roles", "assign_role",
        "view_policies",
        "view_audit_logs",
    }),
    "dept_head": frozenset({
        "view_dashboard",
        "view_users", "edit_user",
        "view_roles",
        "view_policies",
        "view_audit_logs",
    }),
    "officer": frozenset({
        "view_dashboard",
    }),
}


def get_permissions(role: str) -> frozenset:
    """Return the permission set for a role string (case-insensitive, normalised)."""
    normalised = role.lower().replace(" ", "_").replace("-", "_")
    return ROLE_PERMISSIONS.get(normalised, frozenset())


def has_permission(session_state: MutableMapping[str, object], permission: str) -> bool:
    """Return True if the logged-in user has the given permission."""
    user = session_state.get("user", {})
    role = user.get("role", "")  # type: ignore[union-attr]
    return permission in get_permissions(role)  # type: ignore[arg-type]


def require_permission(session_state: MutableMapping[str, object], permission: str) -> bool:
    """
    Check permission and log a denied-access event if missing.
    Returns True if allowed, False otherwise.
    Callers should stop rendering and show an error if False is returned.
    """
    import streamlit as st  # imported here to avoid circular imports at module level
    if has_permission(session_state, permission):
        return True

    user = session_state.get("user", {})
    actor = user.get("username", "unknown")
    log_event(
        "PERMISSION_DENIED",
        actor,
        permission,
        f"Access denied to '{permission}'",
        severity="Warning",
    )
    st.error("🚫 You do not have permission to access this feature.")
    return False


# -----------------------------------------------------------------------
# Password helpers
# -----------------------------------------------------------------------

def _pbkdf2_hash(password: str) -> str:
    """Hash with PBKDF2-HMAC-SHA256. Format: pbkdf2$iterations$hex-salt$hex-digest."""
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 260_000)
    return f"pbkdf2$260000${salt.hex()}${dk.hex()}"


def _verify_pbkdf2(plain: str, stored: str) -> bool:
    """Verify a PBKDF2 hash."""
    try:
        _, iters, salt_hex, digest_hex = stored.split("$")
        salt = bytes.fromhex(salt_hex)
        dk = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt, int(iters))
        return dk.hex() == digest_hex
    except Exception:
        return False


def _verify_legacy_sha256(plain: str, stored: str) -> bool:
    """Verify an old plain SHA-256 hash (migration path)."""
    return hashlib.sha256(plain.encode()).hexdigest() == stored


def verify_password(plain: str, stored: str) -> bool:
    """Verify a password against either PBKDF2 or legacy SHA-256 hash."""
    if stored.startswith("pbkdf2$"):
        return _verify_pbkdf2(plain, stored)
    return _verify_legacy_sha256(plain, stored)


def hash_password(password: str) -> str:
    """Return a PBKDF2 hash of the password (public API for other modules)."""
    return _pbkdf2_hash(password)


def _migrate_to_pbkdf2(user_id: int, plain_password: str) -> None:
    """Silently upgrade a legacy SHA-256 hash to PBKDF2 after a successful login."""
    new_hash = _pbkdf2_hash(plain_password)
    conn = get_connection()
    conn.execute(
        "UPDATE admin_users SET password_hash = ? WHERE id = ?",
        (new_hash, user_id),
    )
    conn.commit()
    conn.close()


# -----------------------------------------------------------------------
# Login / logout
# -----------------------------------------------------------------------

def login(username: str, password: str) -> dict | None:
    """
    Validate credentials against the admin_users table.

    - Checks for account lockout first.
    - Increments failed_attempts on failure; resets on success.
    - Migrates legacy SHA-256 hashes to PBKDF2 transparently.
    - Returns the user row as a dict on success, or None on failure.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM admin_users WHERE username = ?",
        (username.strip().lower(),),
    )
    row = cursor.fetchone()
    conn.close()

    if row is None:
        log_event("LOGIN_FAILURE", username, "System",
                  "Unknown username", severity="Warning")
        return None

    row = dict(row)

    # ── Lockout check ────────────────────────────────────────────────
    locked_until = row.get("locked_until")
    if locked_until:
        lock_dt = datetime.fromisoformat(locked_until)
        if datetime.utcnow() < lock_dt:
            mins_left = int((lock_dt - datetime.utcnow()).total_seconds() / 60) + 1
            log_event("LOGIN_FAILURE", username, "System",
                      f"Login attempted on locked account ({mins_left}m remaining)",
                      severity="Warning")
            return None
        else:
            # Lock expired — reset
            _reset_lockout(row["id"])

    # ── Password verification ─────────────────────────────────────────
    if not verify_password(password, row["password_hash"]):
        _increment_failed(row["id"], row.get("failed_attempts", 0))
        log_event("LOGIN_FAILURE", username, "System",
                  "Incorrect password", severity="Warning")
        return None

    # ── Success ───────────────────────────────────────────────────────
    # Migrate legacy hash if needed
    if not row["password_hash"].startswith("pbkdf2$"):
        _migrate_to_pbkdf2(row["id"], password)

    _reset_lockout(row["id"])
    log_event("LOGIN_SUCCESS", username, "System",
              "Successful login", severity="Info")
    return row


def logout(session_state: MutableMapping[str, object]) -> None:
    """Clear all authentication keys from Streamlit session state."""
    user = session_state.get("user", {})
    actor = user.get("username", "unknown")
    log_event("LOGOUT", actor, "System", "User logged out", severity="Info")
    for key in ("authenticated", "user", "current_page"):
        session_state.pop(key, None)


# -----------------------------------------------------------------------
# Lockout helpers
# -----------------------------------------------------------------------

def _increment_failed(user_id: int, current_count: int) -> None:
    new_count = current_count + 1
    locked_until = None
    if new_count >= MAX_FAILED_ATTEMPTS:
        locked_until = (datetime.utcnow() + timedelta(minutes=LOCKOUT_MINUTES)).isoformat()
    conn = get_connection()
    conn.execute(
        "UPDATE admin_users SET failed_attempts = ?, locked_until = ? WHERE id = ?",
        (new_count, locked_until, user_id),
    )
    conn.commit()
    conn.close()


def _reset_lockout(user_id: int) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE admin_users SET failed_attempts = 0, locked_until = NULL WHERE id = ?",
        (user_id,),
    )
    conn.commit()
    conn.close()


# -----------------------------------------------------------------------
# Session helpers (used across every page)
# -----------------------------------------------------------------------

def is_authenticated(session_state: MutableMapping[str, object]) -> bool:
    """Return True if the current session has a valid login."""
    return bool(session_state.get("authenticated", False))


def get_current_user(session_state: MutableMapping[str, object]) -> dict | None:
    """Return the logged-in user dict, or None if not logged in."""
    return session_state.get("user", None)  # type: ignore[return-value]
