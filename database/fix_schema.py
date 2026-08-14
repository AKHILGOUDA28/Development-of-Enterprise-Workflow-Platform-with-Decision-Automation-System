"""Quick script to check and fix ALL missing columns, then run seed."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import db_manager

# 1. Get existing columns
rows = db_manager.fetchall(
    "SELECT column_name FROM information_schema.columns "
    "WHERE table_name = 'incidents' ORDER BY ordinal_position"
)
existing = {r["column_name"] for r in rows}
print("[*] incidents columns:", sorted(existing))

# 2. Add ALL missing columns
NEEDED = {
    "incident_number": "TEXT",
    "subcategory": "TEXT",
    "priority": "TEXT DEFAULT 'Medium'",
    "assigned_team": "TEXT",
    "resolution": "TEXT",
    "resolution_strategy": "TEXT",
    "resolution_time_hours": "REAL",
    "ticket_number": "TEXT",
    "resolved_at": "TEXT",
}

for col, typedef in NEEDED.items():
    if col not in existing:
        try:
            db_manager.execute(f"ALTER TABLE incidents ADD COLUMN {col} {typedef}")
            print(f"  [+] Added: {col}")
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                print(f"  [=] {col} already exists")
            else:
                print(f"  [!] {col}: {e}")
    else:
        print(f"  [=] {col} OK")

# 3. Check other tables
for table, ddl in [
    ("notifications", """
        CREATE TABLE IF NOT EXISTS notifications (
            id SERIAL PRIMARY KEY,
            incident_id TEXT,
            recipient TEXT,
            channel TEXT DEFAULT 'dashboard',
            subject TEXT,
            message TEXT,
            status TEXT DEFAULT 'sent',
            created_at TEXT
        )
    """),
    ("agent_events", """
        CREATE TABLE IF NOT EXISTS agent_events (
            id SERIAL PRIMARY KEY,
            session_id TEXT,
            agent_name TEXT,
            event_type TEXT,
            data TEXT,
            timestamp TEXT
        )
    """),
]:
    try:
        db_manager.fetchone(f"SELECT COUNT(*) AS c FROM {table}")
        print(f"[*] {table} exists")
    except:
        try:
            db_manager.execute(ddl)
            print(f"[+] Created {table}")
        except Exception as e:
            print(f"[!] {table}: {e}")

print("\n[OK] Schema ready for seeding.")
