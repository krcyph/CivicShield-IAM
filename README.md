# 🛡️ CivicShield IAM
**Government Identity and Access Management System**

> **CivicShield – Government Identity and Access Management System**  
> Citizen Services Department — Secure Identity Platform  
>
> ⚠️ **Academic demonstration only — not an official government portal.**  
> All employee, citizen and department data is entirely fictional and for demonstration purposes only.

---

## Project Overview

CivicShield IAM is a web-based dashboard that simulates an Identity and Access Management platform for a government department. It demonstrates:

- Secure login with PBKDF2-HMAC-SHA256 password hashing (with legacy SHA-256 migration)
- Premium dark enterprise-cybersecurity UI (Midnight Navy / Cyber Teal theme)
- Employee directory with clearance levels and account statuses
- Security event / audit log viewer with filtering and CSV export
- Role-Based Access Control (RBAC) with a full five-role permission matrix
- IAM policy framework documentation
- SQLite-backed persistent storage (no external database required)

---

## Project Structure

```
Mini Project/
├── app.py                    # Main entry point — run this file
├── requirements.txt          # Python dependencies
├── civicshield.db            # SQLite database (auto-created on first run)
│
├── .streamlit/
│   └── config.toml           # CivicShield dark theme configuration
│
├── auth/
│   ├── __init__.py
│   └── auth.py               # Login, logout, PBKDF2 password hashing helpers
│
├── database/
│   ├── __init__.py
│   └── db_init.py            # Schema creation and database connection
│
├── data/
│   ├── __init__.py
│   └── sample_data.py        # Fictional employee/audit data + query helpers
│
├── _pages/
│   ├── __init__.py
│   ├── login.py              # Login page
│   ├── dashboard.py          # Main dashboard with stats and charts
│   ├── user_management.py    # Full CRUD employee management
│   ├── roles_permissions.py  # Role definitions, permission matrix, role assignment
│   ├── iam_policies.py       # Security policy framework documentation
│   └── audit_logs.py         # Audit log viewer with filters and CSV export
│
└── ui/
    ├── __init__.py
    └── components.py         # Reusable Streamlit UI components + global CSS
```

---

## Requirements

- **Python 3.10 or higher** (uses the `X | Y` union type hint syntax)
- **Streamlit 1.57+** (only third-party dependency)
- All other libraries used (`sqlite3`, `hashlib`, `os`, `datetime`) are Python built-ins

---

## Installation

### 1. Clone / open the project folder

```bash
cd ""
```

### 2. (Recommended) Create a virtual environment

```bash
# Windows PowerShell
python -m venv .venv
.venv\Scripts\Activate.ps1

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Running the Application

```bash
streamlit run app.py
```

Streamlit will open the app automatically in your default browser at:  
**http://localhost:8501**

---

## Default Login Credentials

| Role    | Username  | Password     |
|---------|-----------|--------------|
| Admin   | `admin`   | `Admin@1234` |
| Auditor | `auditor` | `Audit@5678` |

> These are seeded automatically the first time the app runs.

---

## Features Implemented (v1.0.0)

| Feature                          | Status  |
|----------------------------------|---------|
| Login page (dark theme)          | ✅ Done |
| PBKDF2 password hashing          | ✅ Done |
| Session management               | ✅ Done |
| Dark sidebar navigation          | ✅ Done |
| Dashboard (stats + charts)       | ✅ Done |
| Employee directory preview       | ✅ Done |
| Security events table            | ✅ Done |
| SQLite schema + seeding          | ✅ Done |
| User Management module           | ✅ Done |
| Roles & Permissions module       | ✅ Done |
| IAM Policies module              | ✅ Done |
| Audit Logs module (CSV export)   | ✅ Done |

---

## Visual Design

CivicShield uses a premium enterprise cybersecurity dark theme:

| Token         | Hex       | Usage                          |
|---------------|-----------|--------------------------------|
| Midnight Navy | `#0B1728` | Page background                |
| Deep Slate    | `#12243A` | Card / panel background        |
| Steel Blue    | `#173B56` | Table headers, sidebar accents |
| Cyber Teal    | `#20C5B5` | Primary actions, links, badges |
| Ice White     | `#DCE8F2` | Primary text                   |
| Amber         | `#F0B45A` | Warnings, highlights           |

---

## Technology Stack

| Layer      | Technology                            |
|------------|---------------------------------------|
| Language   | Python 3.10+                          |
| Web UI     | Streamlit 1.67+                       |
| Database   | SQLite (via `sqlite3` built-in)       |
| Security   | `hashlib` PBKDF2-HMAC-SHA256 (built-in) |
| Data       | `pandas` (bundled with Streamlit)     |

---

## Security Notes

- Passwords are stored as **PBKDF2-HMAC-SHA256** hashes with a unique random salt — never in plain text.
- Legacy SHA-256 hashes are transparently migrated to PBKDF2 on next successful login.
- All access events are logged to the `audit_logs` table.
- Account lockout after 5 failed login attempts (15-minute lockout period).
- This system does **not** connect to any real government infrastructure.
- Intended for **educational / academic demonstration** use only.

---

## Disclaimer

This project is created for **academic demonstration purposes**.  
It is **not** affiliated with, endorsed by, or representative of any actual government department.  
All data, names, and records are entirely fictional.

© 2026 — Fictional Citizen Services Department.  
CivicShield v1.0.0
