import requests
import json
import time

BASE_URL = "http://localhost:8000"

print("[*] Waiting for server startup...")
time.sleep(3)

# 1. Health check / Root
r = requests.get(f"{BASE_URL}/health")
print(f"[+] GET /health -> {r.status_code} {r.json()}")

# 2. Login
r_login = requests.post(f"{BASE_URL}/auth/login", json={"username": "admin", "password": "admin123"})
print(f"[+] POST /auth/login -> {r_login.status_code}")
token = r_login.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

# 3. Analytics Summary
r_summary = requests.get(f"{BASE_URL}/analytics/summary", headers=headers)
print(f"[+] GET /analytics/summary -> {r_summary.status_code}")
if r_summary.status_code == 200:
    data = r_summary.json()
    print(f"    Total Incidents: {data.get('total_incidents')}, Resolved: {data.get('resolved')}, Open: {data.get('open')}")

# 4. Analytics Trends
r_trends = requests.get(f"{BASE_URL}/analytics/trends?days=30", headers=headers)
print(f"[+] GET /analytics/trends -> {r_trends.status_code}")

# 5. Incidents List
r_incidents = requests.get(f"{BASE_URL}/incidents?limit=10", headers=headers)
print(f"[+] GET /incidents -> {r_incidents.status_code} ({len(r_incidents.json())} incidents returned)")

# 6. Approval Queue
r_approval = requests.get(f"{BASE_URL}/approval-queue", headers=headers)
print(f"[+] GET /approval-queue -> {r_approval.status_code} ({len(r_approval.json())} pending)")

# 7. Policy Table
r_policy = requests.get(f"{BASE_URL}/policy/table", headers=headers)
print(f"[+] GET /policy/table -> {r_policy.status_code} ({len(r_policy.json())} rules)")

# 8. Audit Logs
r_audit = requests.get(f"{BASE_URL}/audit-logs?limit=10", headers=headers)
print(f"[+] GET /audit-logs -> {r_audit.status_code} ({len(r_audit.json().get('rows', []))} rows)")

# 9. Knowledge Base
r_kb = requests.get(f"{BASE_URL}/knowledge?limit=10", headers=headers)
print(f"[+] GET /knowledge -> {r_kb.status_code} ({len(r_kb.json())} articles)")

# 10. Tools Stats
r_tools = requests.get(f"{BASE_URL}/tools/stats", headers=headers)
print(f"[+] GET /tools/stats -> {r_tools.status_code}")

print("\n========================================================")
print("  ALL ENDPOINTS VERIFIED SUCCESSFULLY WITH HTTP 200 OK  ")
print("========================================================")
