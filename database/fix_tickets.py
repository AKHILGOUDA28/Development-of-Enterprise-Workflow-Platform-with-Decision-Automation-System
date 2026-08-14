import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import db_manager
import random
from datetime import datetime, timedelta, timezone

# 1. Get existing tickets columns
try:
    rows = db_manager.fetchall(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'tickets' ORDER BY ordinal_position"
    )
    existing = {r["column_name"] for r in rows}
    print("[*] tickets columns:", sorted(existing))
except Exception as e:
    print("[!] tickets error:", e)
    existing = set()

# 2. Add missing columns to tickets if needed
NEEDED = {
    "ticket_number": "TEXT",
    "incident_id": "TEXT",
    "user": "TEXT",
    "issue": "TEXT",
    "priority": "TEXT DEFAULT 'Medium'",
    "status": "TEXT DEFAULT 'Open'",
    "assigned_team": "TEXT",
    "created_at": "TEXT",
    "updated_at": "TEXT"
}

for col, typedef in NEEDED.items():
    if col not in existing and existing:
        try:
            db_manager.execute(f"ALTER TABLE tickets ADD COLUMN {col} {typedef}")
            print(f"  [+] Added: {col}")
        except Exception as e:
            print(f"  [!] {col}: {e}")

# 3. Seed 100 tickets
incidents = db_manager.fetchall("SELECT incident_id FROM incidents LIMIT 100")
inc_ids = [r["incident_id"] for r in incidents]

count = 0
for i in range(100):
    tkt_id = f"TKT-{5000 + i}"
    tkt_num = tkt_id
    inc_id = inc_ids[i] if i < len(inc_ids) else None
    priority = random.choice(["Low","Medium","High","Critical"])
    status = random.choice(["Open","In Progress","Resolved","Closed"])
    team = random.choice(["Network Team","Email Team","Security Team","Hardware Team","Infrastructure Team","IAM Team"])
    now = (datetime.now(timezone.utc) - timedelta(days=random.uniform(1, 60))).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    try:
        db_manager.execute(
            "INSERT INTO tickets (ticket_id, ticket_number, incident_id, \"user\", issue, priority, status, assigned_team, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(ticket_id) DO NOTHING",
            (tkt_id, tkt_num, inc_id, f"EMP{random.randint(1000,1099)}",
             f"Escalated incident {inc_id or 'Unknown'}", priority, status, team, now, now)
        )
        count += 1
    except Exception as e:
        print(f"Failed ticket {tkt_id}: {e}")
        break

print(f"[OK] Seeded {count} tickets.")
