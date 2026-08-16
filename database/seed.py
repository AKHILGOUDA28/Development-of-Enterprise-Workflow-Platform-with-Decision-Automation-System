"""
seed.py
-------
Production-scale database seeder.

Generates realistic synthetic IT incident data:
  - 10 departments
  - 100 employees
  - 100 knowledge articles (across 6 categories)
  - 500 historical incidents (varied statuses, severities, categories)
  - 500+ agent events
  - 100+ tickets
  - 200+ audit log entries
  - 50+ notifications
  - 30+ long-term memory entries

Usage:
    python database/seed.py
    python database/seed.py --reset   # drops all data first
"""

import sys
import os
import uuid
import json
import random
import argparse
from datetime import datetime, timedelta, timezone

# Allow running from project root or from database/ directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import db_manager
from database.init_db import init_databases

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_minus(days: float = 0, hours: float = 0, minutes: float = 0) -> str:
    dt = datetime.now(timezone.utc) - timedelta(days=days, hours=hours, minutes=minutes)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

def _rand_dt(days_back_min: int = 1, days_back_max: int = 90) -> str:
    days_back = random.uniform(days_back_min, days_back_max)
    return _now_minus(days=days_back)

def _upsert(table: str, pk_col: str, pk_val, cols: list, vals: tuple, conflict_action: str = "DO NOTHING"):
    placeholders = ",".join(["?"] * len(vals))
    col_str = ",".join(cols)
    db_manager.execute(
        f"INSERT INTO {table} ({col_str}) VALUES ({placeholders}) "
        f"ON CONFLICT({pk_col}) {conflict_action}",
        vals
    )

# ---------------------------------------------------------------------------
# 1. DEPARTMENTS (10)
# ---------------------------------------------------------------------------
DEPARTMENTS = [
    "Engineering", "IT", "Human Resources", "Finance",
    "Operations", "Sales", "Marketing", "Legal",
    "Customer Success", "Executive"
]

def seed_departments():
    print("[*] Seeding departments...")
    now = _now_minus(days=365)
    for dept in DEPARTMENTS:
        try:
            db_manager.execute(
                "INSERT INTO departments (name, manager_id, created_at) "
                "VALUES (?,?,?) ON CONFLICT(name) DO NOTHING",
                (dept, None, now)
            )
        except Exception:
            pass
    print(f"    [OK] {len(DEPARTMENTS)} departments ready.")

# ---------------------------------------------------------------------------
# 2. EMPLOYEES (100)
# ---------------------------------------------------------------------------
FIRST_NAMES = [
    "Akhil","Sarah","David","Elena","James","Maria","Robert","Lisa","Michael","Priya",
    "Alex","Jessica","Daniel","Amanda","Christopher","Stephanie","Andrew","Nicole","Joshua","Samantha",
    "Kevin","Rachel","Brian","Megan","Edward","Lauren","Ryan","Amy","Jason","Melissa",
    "Tyler","Emily","Nathan","Christine","Justin","Heather","Brandon","Amber","Samuel","Rebecca",
    "Gregory","Vanessa","Eric","Diana","Patrick","Dawn","Timothy","Brittany","Adam","Karen",
    "Rajesh","Ananya","Vikram","Meera","Arjun","Deepa","Suresh","Kavya","Ravi","Pooja",
    "Liam","Olivia","Noah","Emma","William","Ava","Lucas","Isabella","Mason","Sophia",
    "Ethan","Charlotte","Oliver","Amelia","Elijah","Mia","Aiden","Harper","Carter","Evelyn",
    "Wei","Mei","Jian","Lin","Hui","Yan","Feng","Xiao","Hong","Ying",
    "Mohammed","Fatima","Ahmed","Aisha","Omar","Zainab","Hassan","Nour","Ali","Sara"
]
LAST_NAMES = [
    "Kumar","Johnson","Chen","Rodriguez","Williams","Davis","Brown","Miller","Wilson","Moore",
    "Anderson","Taylor","Thomas","Jackson","White","Harris","Martin","Thompson","Garcia","Martinez",
    "Robinson","Clark","Lewis","Lee","Walker","Hall","Allen","Young","Hernandez","King",
    "Wright","Lopez","Hill","Scott","Green","Adams","Baker","Gonzalez","Nelson","Carter",
    "Mitchell","Perez","Roberts","Turner","Phillips","Campbell","Parker","Evans","Edwards","Collins",
    "Sharma","Patel","Gupta","Singh","Verma","Nair","Pillai","Reddy","Rao","Iyer",
    "O'Brien","Murphy","Walsh","Kelly","O'Connor","O'Neill","Byrne","Ryan","Doyle","Hughes",
    "Schmidt","Mueller","Becker","Wagner","Fischer","Weber","Meyer","Wolf","Schumann","Koch",
    "Nakamura","Tanaka","Yamamoto","Watanabe","Suzuki","Ito","Kobayashi","Sato","Kato","Abe",
    "Al-Hassan","Al-Rashid","Al-Farsi","Al-Jabri","Al-Khatib","Al-Masri","Al-Sayed","Khalil","Nasser","Qureshi"
]

TITLES = {
    "Engineering": ["Software Engineer","Senior Engineer","Principal Engineer","Tech Lead","DevOps Engineer","SRE","QA Engineer"],
    "IT": ["IT Analyst","IT Specialist","System Admin","Network Engineer","Help Desk Technician","IT Manager","Security Analyst"],
    "Human Resources": ["HR Coordinator","HR Manager","Recruiter","Benefits Specialist","HR Business Partner"],
    "Finance": ["Financial Analyst","Accountant","Senior Accountant","Finance Manager","Controller","CFO"],
    "Operations": ["Operations Analyst","Project Manager","Program Manager","Operations Manager","VP Operations"],
    "Sales": ["Sales Rep","Account Executive","Sales Manager","Regional Director","VP Sales"],
    "Marketing": ["Marketing Analyst","Content Strategist","Digital Marketer","Marketing Manager","CMO"],
    "Legal": ["Legal Counsel","Associate","Contract Specialist","Compliance Manager","General Counsel"],
    "Customer Success": ["CSM","Senior CSM","Customer Success Director","Support Specialist","Onboarding Manager"],
    "Executive": ["CEO","CTO","CISO","COO","VP Engineering","Director of IT"],
}
LOCATIONS = ["New York", "San Francisco", "Austin", "Chicago", "Seattle", "London", "Singapore", "Bangalore", "Toronto", "Sydney"]

def seed_employees():
    print("[*] Seeding 100 employees...")
    now = _now_minus(days=180)
    employees = []

    for i in range(100):
        emp_id = f"EMP{1000 + i:04d}"
        first = FIRST_NAMES[i % len(FIRST_NAMES)]
        last  = LAST_NAMES[i % len(LAST_NAMES)]
        name  = f"{first} {last}"
        dept  = DEPARTMENTS[i % len(DEPARTMENTS)]
        title = random.choice(TITLES.get(dept, ["Analyst"]))
        email = f"{first.lower()}.{last.lower().replace(' ', '').replace('-', '')}@enterprise.com"
        phone = f"+1-{random.randint(200,999)}-{random.randint(100,999)}-{random.randint(1000,9999)}"
        location = random.choice(LOCATIONS)
        hire_date = _rand_dt(days_back_min=365, days_back_max=3650)
        is_vip = 1 if i < 10 else 0

        employees.append((emp_id, name, email, dept, title, None, phone, location, hire_date, is_vip, now))

        try:
            db_manager.execute(
                "INSERT INTO employees (employee_id,name,email,department,title,manager,phone,location,hire_date,is_vip,created_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(employee_id) DO NOTHING",
                employees[-1]
            )
        except Exception as e:
            pass

        # Also add to users table (so they can log in as employee)
        username = f"emp{1000 + i}"
        try:
            db_manager.execute(
                "INSERT INTO users (username,name,role,employee_id,email,password) "
                "VALUES (?,?,?,?,?,?) ON CONFLICT(username) DO NOTHING",
                (username, name, "Employee", emp_id, email, "password123")
            )
        except Exception:
            pass

    # Ensure core admin users exist
    for uname, uname_full, role, emp_id, email, pwd in [
        ("emp1024", "Akhil Gouda", "Employee", "EMP1024", "akhil@company.com", "password123"),
        ("itsupport","Alex Morgan (IT Lead)","IT Support","EMP8080","support@enterprise.com","support123"),
        ("admin","System Administrator","Admin","EMP0001","admin@enterprise.com","admin123"),
    ]:
        try:
            db_manager.execute(
                "INSERT INTO users (username,name,role,employee_id,email,password) "
                "VALUES (?,?,?,?,?,?) ON CONFLICT(username) DO NOTHING",
                (uname, uname_full, role, emp_id, email, pwd)
            )
        except Exception:
            pass

    print(f"    [OK] 100 employees seeded.")
    return employees

# ---------------------------------------------------------------------------
# 3. KNOWLEDGE ARTICLES (100)
# ---------------------------------------------------------------------------
KB_TEMPLATES = [
    # Network / VPN (15)
    ("Network","VPN","VPN Connection Failure After Windows Update",
     "VPN client loses connectivity after Windows updates modify network stack settings.",
     "1. Run as Admin: netsh int ip reset && netsh winsock reset\n2. Reinstall VPN profile from IT portal\n3. Reboot","Medium"),
    ("Network","VPN","VPN Authentication Failure",
     "VPN shows authentication error even with correct credentials.",
     "1. Verify MFA token is current\n2. Clear VPN client credential cache\n3. Delete and re-import VPN profile\n4. Contact IT if MFA is not working","High"),
    ("Network","VPN","Split Tunneling VPN Performance Issue",
     "Users experience slow VPN speeds when split tunneling is enabled.",
     "1. Disable split tunneling in VPN client settings\n2. Set DNS servers to 10.0.0.1 and 8.8.8.8\n3. Reconnect VPN","Low"),
    ("Network","VPN","VPN Client Crashes on Launch",
     "VPN client application crashes immediately on startup.",
     "1. Uninstall VPN client completely\n2. Delete residual folders in AppData\n3. Download latest client from IT portal\n4. Install as Administrator","Medium"),
    ("Network","WiFi","WiFi Drops in Conference Rooms",
     "WiFi connectivity is intermittent in conference room areas.",
     "1. Forget and re-join corporate WiFi network\n2. Set network to Private in Windows settings\n3. Update WiFi adapter drivers\n4. If persistent, submit AV request for AP inspection","Low"),
    ("Network","WiFi","Cannot Connect to Corporate WiFi",
     "Device cannot associate with the corporate SSID.",
     "1. Verify device is enrolled in MDM\n2. Check certificate validity: certmgr.msc\n3. Delete stored WiFi profile and reconnect\n4. If fails, re-enroll device","Medium"),
    ("Network","DNS","DNS Resolution Failure",
     "Internal hostnames cannot be resolved on corporate network.",
     "1. Run: ipconfig /flushdns\n2. Set DNS to 10.0.0.1 (primary) and 10.0.0.2 (secondary)\n3. Run: nslookup intranet.enterprise.local\n4. If fails, escalate to Network team","Medium"),
    ("Network","DNS","Slow DNS Response Times",
     "Applications load slowly due to DNS lookup delays.",
     "1. Check DNS cache: ipconfig /displaydns\n2. Flush DNS: ipconfig /flushdns\n3. Test DNS with: Resolve-DnsName enterprise.local\n4. Contact Network team if RTT > 100ms","Low"),
    ("Network","Proxy","Proxy Configuration Issue",
     "Browser and applications cannot reach the internet through corporate proxy.",
     "1. Check proxy settings: inetcpl.cpl > Connections > LAN Settings\n2. Set proxy: proxy.enterprise.local:8080\n3. Export proxy settings via GPO\n4. Whitelist application in proxy exceptions","Medium"),
    ("Network","Firewall","Firewall Blocking Application",
     "Application fails to connect due to firewall rules.",
     "1. Test connectivity: Test-NetConnection <host> -Port <port>\n2. Submit firewall exception request to security team\n3. Include business justification and target IP/port\n4. Allow 1 business day for approval","Medium"),
    ("Network","Network","Slow Network Performance",
     "General network slowness affecting productivity.",
     "1. Run speed test at: speedtest.enterprise.local\n2. Check for Windows updates downloading in background\n3. Disable OneDrive sync temporarily\n4. If <10 Mbps, submit network performance ticket","Low"),
    ("Network","VPN","VPN License Capacity Reached",
     "Users cannot connect to VPN due to license limit being reached.",
     "1. Check VPN dashboard for active sessions\n2. Disconnect idle VPN sessions\n3. Contact IT Admin to review license count\n4. Temporary: Use web-based VPN portal","High"),
    ("Network","Network","Network Adapter Not Detected",
     "Windows Device Manager shows network adapter with error.",
     "1. Run: devmgmt.msc\n2. Right-click adapter > Update Driver\n3. Disable/Enable adapter\n4. Run: netsh int ip reset\n5. If fails, replace NIC or run hardware diagnostics","High"),
    ("Network","WiFi","2.4GHz vs 5GHz WiFi Band Issues",
     "Device connects to slower 2.4GHz band instead of 5GHz.",
     "1. In WiFi adapter properties, prefer 5GHz band\n2. Go to Device Manager > WiFi Adapter > Advanced\n3. Set 'Preferred Band' to '5GHz'\n4. Reconnect to WiFi","Low"),
    ("Network","Network","IP Address Conflict",
     "Two devices have the same IP address causing connectivity issues.",
     "1. Release and renew IP: ipconfig /release && ipconfig /renew\n2. If static IP assigned, change to DHCP\n3. Contact Network team to identify conflicting device\n4. Check DHCP lease table","Medium"),

    # Email / Outlook (15)
    ("Email","Exchange","Outlook Cannot Connect to Exchange",
     "Outlook shows Disconnected status and cannot reach Exchange server.",
     "1. Check credential cache: Windows Credential Manager\n2. Re-enter Exchange password\n3. Run: outlook.exe /cleanprofile\n4. Delete and recreate Outlook profile\n5. If server-side, escalate to Exchange team","Medium"),
    ("Email","SMTP","Email Delivery Failure 550",
     "Outbound emails bounce with 550 permanent failure error.",
     "1. Check recipient address spelling\n2. Verify sender domain is not blacklisted\n3. Check MX records: nslookup -type=MX enterprise.com\n4. Submit SMTP relay review request if bulk sending","Medium"),
    ("Email","SMTP","Email Bounce 5.7.1 Relay Access Denied",
     "Emails fail with 5.7.1 relay access denied error.",
     "1. Verify sender is using authenticated SMTP\n2. Check if sender IP is whitelisted in email gateway\n3. Use SMTP port 587 with TLS instead of port 25\n4. Contact email admin for relay permission","Medium"),
    ("Email","Outlook","Outlook Search Not Working",
     "Outlook search returns no results or incomplete results.",
     "1. Run: outlook.exe /resetfolders\n2. Rebuild search index: Control Panel > Indexing Options > Rebuild\n3. Delete OST file and let Outlook recreate\n4. Check mailbox size (>50GB may cause issues)","Low"),
    ("Email","Outlook","Outlook Calendar Sync Issue",
     "Calendar appointments not syncing between devices or showing wrong times.",
     "1. Set timezone correctly in Outlook and Windows\n2. Check for delegate calendar permissions\n3. Clear Outlook temporary files\n4. Run: outlook.exe /CleanReminders\n5. Force sync: Send/Receive All Folders","Low"),
    ("Email","Outlook","Outlook Freezes When Opening Attachments",
     "Outlook becomes unresponsive when trying to open email attachments.",
     "1. Disable Outlook add-ins: File > Options > Add-ins\n2. Run in Safe Mode: outlook.exe /safe\n3. Clear Outlook temp folder: %localappdata%\\Microsoft\\Windows\\INetCache\\Content.Outlook\n4. Update Microsoft Office","Low"),
    ("Email","Exchange","Mailbox Full Error",
     "User cannot send or receive emails due to mailbox quota exceeded.",
     "1. Empty Deleted Items and Junk Email folders\n2. Archive old emails using Outlook Archive feature\n3. Check mailbox size: File > Account Settings > Account Settings\n4. Request quota increase from IT Admin if legitimate","Low"),
    ("Email","Outlook","Outlook Autocomplete Not Working",
     "Outlook not suggesting email addresses when composing.",
     "1. Enable autocomplete: File > Options > Mail > Use Auto-Complete List\n2. Clear and rebuild autocomplete: NK2Edit tool or delete NK2 file\n3. Start Outlook in Safe Mode to test\n4. Check Exchange Offline Address Book sync","Low"),
    ("Email","Security","Phishing Email Reported",
     "User has received and/or clicked a suspicious phishing email.",
     "1. DO NOT click any links or open attachments\n2. Forward email to: phishing@enterprise.com\n3. Delete email immediately\n4. If clicked: immediately change password and enable MFA\n5. Security team will investigate within 2 hours","Critical"),
    ("Email","Exchange","Email Signature Not Applying",
     "Corporate email signature is missing from outbound emails.",
     "1. Check Outlook signature settings: File > Options > Mail > Signatures\n2. Verify signature is set for New Messages and Replies\n3. If signature managed by IT policy, run: gpupdate /force\n4. Contact IT if signature template has changed","Low"),
    ("Email","Distribution","Distribution List Not Receiving Emails",
     "Emails sent to a distribution group are not reaching all members.",
     "1. Verify sender is allowed to email the distribution list\n2. Check if list is moderated and requires approval\n3. Verify member email addresses are valid\n4. Contact Exchange admin to check distribution list settings","Medium"),
    ("Email","Outlook","Outlook Profile Corruption",
     "Outlook crashes repeatedly or shows errors about profile corruption.",
     "1. Create new Outlook profile: Control Panel > Mail > Profiles > Add\n2. Set new profile as default\n3. Re-add Exchange account\n4. Import PST backup if available\n5. Delete corrupted profile after confirming new profile works","Medium"),
    ("Email","Security","Email Account Compromised",
     "Unauthorized access to employee email account detected.",
     "1. IMMEDIATELY reset email password\n2. Enable MFA if not already active\n3. Check email rules for forwarding to external addresses\n4. Review sign-in logs for suspicious activity\n5. Report to security team within 15 minutes","Critical"),
    ("Email","Outlook","Outlook Slow to Load",
     "Outlook takes 5+ minutes to open or load inbox.",
     "1. Disable unnecessary add-ins\n2. Compact PST/OST file via Account Settings\n3. Limit sync to recent emails: Account Settings > More Settings > Offline\n4. Move large attachments to SharePoint\n5. Consider mailbox cleanup if >25GB","Low"),
    ("Email","Exchange","Meeting Room Booking Not Working",
     "Unable to book meeting rooms through Outlook calendar.",
     "1. Verify room resource mailbox is available\n2. Check room booking policy (max attendees, advance notice)\n3. Use Room Finder in Outlook: Home > New Meeting > Room Finder\n4. Contact Exchange admin if room shows unavailable when calendar is clear","Low"),

    # Security (15)
    ("Security","Account Access","Password Reset Request",
     "Employee forgot password and needs account reset.",
     "1. Use SSPR portal: https://sspr.enterprise.local\n2. Verify identity via MFA\n3. If SSPR fails, IT Admin can reset via AD\n4. New password must meet: 12+ chars, upper+lower+number+symbol","Low"),
    ("Security","Account Access","Account Locked Out",
     "Employee account is locked due to multiple failed login attempts.",
     "1. Wait 30 minutes for auto-unlock (policy)\n2. Or use SSPR portal for immediate unlock\n3. If recurring, check for stale credentials in mapped drives or services\n4. Review login attempts in AD for suspicious activity","Medium"),
    ("Security","MFA","MFA Token Not Working",
     "Multi-factor authentication code is being rejected.",
     "1. Sync authenticator app time: Settings > Time Correction for Codes\n2. Try backup codes from IT portal\n3. Verify you're using the correct MFA method (TOTP vs SMS)\n4. Contact IT to reset MFA enrollment if app is lost","Medium"),
    ("Security","Account Access","Employee Offboarding - Account Disable",
     "Former employee account needs to be disabled immediately.",
     "1. REQUIRES IT ADMIN APPROVAL\n2. Disable AD account\n3. Remove from all distribution groups\n4. Revoke all active sessions\n5. Transfer mailbox access to manager\n6. Archive data per retention policy\n7. Document in audit log","High"),
    ("Security","Certificates","SSL Certificate Expired",
     "Web application shows SSL certificate error in browsers.",
     "1. Identify certificate: click lock icon in browser > Certificate\n2. Check expiry date\n3. Raise emergency ticket to PKI team\n4. Temporary: add exception in browser (NOT recommended for production)\n5. PKI team will renew within 4 hours for critical systems","Critical"),
    ("Security","Access Control","Unauthorized Software Detected",
     "Endpoint security detected unauthorized or unlicensed software installation.",
     "1. Security alert auto-quarantines suspicious software\n2. Review application details in endpoint security console\n3. If false positive, submit whitelist request with business justification\n4. If confirmed threat, initiate incident response procedure","High"),
    ("Security","Data","Data Breach Suspected",
     "Possible unauthorized access to sensitive data detected.",
     "1. IMMEDIATELY notify CISO and IT Security team\n2. Isolate affected system from network\n3. Preserve all logs and do not power off machine\n4. Begin forensic investigation\n5. Notify Legal and HR within 1 hour\n6. Assess notification requirements under GDPR/local law","Critical"),
    ("Security","Access Control","Privilege Escalation Request",
     "Employee needs elevated permissions for a system or application.",
     "1. Submit access request with business justification via IT portal\n2. Manager approval required\n3. IT Security reviews and approves/denies\n4. Temporary elevation expires after 24 hours unless extended\n5. All privileged actions are audited","High"),
    ("Security","Endpoint","Antivirus Alert - Malware Detected",
     "Endpoint security detected malware on employee workstation.",
     "1. Endpoint is automatically quarantined\n2. DO NOT continue using the machine\n3. Security team will remotely remediate\n4. If remediation fails, machine will be reimaged\n5. Employee receives loaner device within 2 hours","Critical"),
    ("Security","MFA","Lost MFA Device",
     "Employee lost phone or hardware token used for MFA.",
     "1. Temporarily use backup MFA codes\n2. Contact IT immediately to disable old MFA device\n3. Re-enroll new device via IT portal with manager approval\n4. Generate and securely store new backup codes","High"),
    ("Security","Access Control","VPN Access Request for New Employee",
     "New employee needs VPN access configured.",
     "1. Manager submits access request in IT portal\n2. IT verifies employee is in HR system\n3. VPN profile created and emailed to employee\n4. Employee downloads and installs VPN client\n5. IT confirms first successful connection","Low"),
    ("Security","Certificates","Certificate Authority Trust Error",
     "Applications show certificate trust errors for internal CA certificates.",
     "1. Check if corporate root CA is installed: certmgr.msc > Trusted Root CAs\n2. Run: gpupdate /force to re-apply certificate GPO\n3. Manually import CA cert if GPO fails\n4. Contact PKI team if CA cert is expired","Medium"),
    ("Security","Account Access","Service Account Password Expiry",
     "Service account password expired causing application failures.",
     "1. REQUIRES IT ADMIN + APPLICATION OWNER APPROVAL\n2. Generate new password meeting complexity requirements\n3. Update password in: Windows Services, IIS App Pools, Scheduled Tasks, Application configs\n4. Test application functionality after update\n5. Set reminders 30 days before next expiry","High"),
    ("Security","Compliance","Security Audit Log Request",
     "Compliance team requires security audit logs for review.",
     "1. Logs are available in IT Security SIEM console\n2. Provide date range and specific events needed\n3. IT Security exports logs in PDF and CSV format\n4. Logs are retained for 12 months per compliance policy","Low"),
    ("Security","Phishing","Ransomware Attack Response",
     "Ransomware detected and encrypting files on endpoint or file server.",
     "1. IMMEDIATELY disconnect machine from network (unplug Ethernet, disable WiFi)\n2. Alert IT Security, CISO, and management\n3. Do NOT pay ransom\n4. Restore from last clean backup\n5. Preserve machine for forensics\n6. Engage incident response team\n7. Notify regulatory bodies if required","Critical"),

    # Hardware (15)
    ("Hardware","Laptop","Laptop Battery Not Charging",
     "Laptop shows plugged in but not charging.",
     "1. Try different power outlet and cable\n2. Check power adapter light is on\n3. Calibrate battery: fully discharge, then charge to 100%\n4. Run: powercfg /batteryreport\n5. If battery health < 40%, submit hardware replacement request","Low"),
    ("Hardware","Laptop","Laptop Screen Flickering",
     "Display flickers or shows artifacts.",
     "1. Update display driver via Device Manager\n2. Change screen refresh rate: Display Settings > Advanced Display\n3. Test with external monitor to isolate GPU vs screen\n4. If GPU issue, reimage machine\n5. If screen issue, submit hardware replacement request","Medium"),
    ("Hardware","Printer","Printer Offline or Not Printing",
     "Print jobs stuck in queue or printer shows offline.",
     "1. Restart Print Spooler: services.msc > Print Spooler > Restart\n2. Clear print queue: %SYSTEMROOT%\\System32\\spool\\PRINTERS\n3. Delete and reinstall printer driver\n4. Check network connectivity to printer IP\n5. Power cycle printer","Low"),
    ("Hardware","Printer","Printer Driver Installation",
     "New printer needs to be set up on employee workstation.",
     "1. Open \\\\printserver.enterprise.local in File Explorer\n2. Double-click printer to auto-install driver\n3. Set as default printer if needed\n4. Print test page to verify\n5. If printer not listed, contact IT with printer model and location","Low"),
    ("Hardware","Monitor","External Monitor Not Detected",
     "Laptop does not detect externally connected monitor.",
     "1. Press Win + P to toggle display modes\n2. Try different display cable (HDMI, DisplayPort, USB-C)\n3. Update display adapter drivers\n4. Check monitor power is on and input source selected\n5. Test with different monitor to isolate issue","Low"),
    ("Hardware","Laptop","Laptop Running Hot",
     "Laptop overheating and shutting down or throttling performance.",
     "1. Clean laptop vents with compressed air\n2. Use on hard, flat surface for airflow\n3. Run: powercfg /energy to check power issues\n4. Set power plan to Balanced instead of High Performance\n5. If > 90°C under load, submit hardware ticket","Medium"),
    ("Hardware","Keyboard","Keyboard Keys Not Working",
     "Some or all keyboard keys are unresponsive.",
     "1. Test with external USB keyboard\n2. Check keyboard driver in Device Manager\n3. Clean keyboard with compressed air\n4. Uninstall and reinstall keyboard driver\n5. If laptop keyboard hardware failure, request replacement","Medium"),
    ("Hardware","Storage","Hard Drive Failure Warning",
     "SMART monitoring or OS shows hard drive failure warning.",
     "1. IMMEDIATELY backup all data\n2. Run: wmic diskdrive get status\n3. Run CrystalDiskInfo for detailed SMART data\n4. Submit hardware replacement request URGENT\n5. IT will replace drive within 4 hours for SMART failure","Critical"),
    ("Hardware","RAM","Computer Freezing Randomly",
     "Computer freezes or crashes with blue screen errors.",
     "1. Check Windows Event Viewer for critical errors\n2. Run Windows Memory Diagnostic: mdsched.exe\n3. Run System File Checker: sfc /scannow\n4. Check for driver updates\n5. If memory errors found, request RAM replacement","Medium"),
    ("Hardware","Laptop","Laptop Touchpad Not Working",
     "Touchpad is unresponsive or behaving erratically.",
     "1. Check touchpad enable/disable key (usually Fn + F5 or F9)\n2. Update touchpad driver via Device Manager\n3. Disable palm rejection if causing false clicks\n4. Test with mouse to confirm input works\n5. If hardware issue, submit replacement request","Low"),
    ("Hardware","Headset","Headset Not Recognized",
     "Headset audio device not showing in Windows sound settings.",
     "1. Unplug and replug headset\n2. Try different USB port or 3.5mm jack\n3. Set as default device: Right-click speaker icon > Sound Settings\n4. Update audio drivers\n5. Test headset on another machine to isolate issue","Low"),
    ("Hardware","Webcam","Webcam Not Working in Video Calls",
     "Webcam not detected or showing black screen in Teams/Zoom.",
     "1. Check camera privacy setting: Settings > Privacy > Camera > Allow apps to access\n2. Check if another app is using camera (Task Manager)\n3. Test in Camera app (Win + Camera)\n4. Update webcam drivers\n5. Unplug and replug USB webcam","Low"),
    ("Hardware","Laptop","Laptop Not Starting",
     "Laptop does not power on at all.",
     "1. Connect power adapter and wait 10 minutes\n2. Hold power button 30 seconds for forced reset\n3. Remove battery (if removable) and try on AC power only\n4. Try external monitor to check if screen failed\n5. Submit hardware emergency ticket if no response","High"),
    ("Hardware","Storage","External Drive Not Recognized",
     "External USB drive not showing in Windows File Explorer.",
     "1. Check Disk Management (diskmgmt.msc) for unallocated drive\n2. Try different USB ports and cable\n3. Initialize disk if showing as not initialized\n4. Update USB controller drivers\n5. Test drive on another computer to verify it's not physically failed","Low"),
    ("Hardware","Docking Station","Docking Station Not Working",
     "Laptop connected to docking station but peripherals not responding.",
     "1. Unplug and replug docking station power adapter\n2. Disconnect and reconnect laptop to dock\n3. Check dock firmware update via manufacturer utility\n4. Try direct connection of peripherals to laptop\n5. Replace docking station cable if damaged","Medium"),

    # Software (20)
    ("Software","OS","Windows Update Failing",
     "Windows Update shows error codes and fails to install updates.",
     "1. Run Windows Update Troubleshooter\n2. Run: net stop wuauserv && net start wuauserv\n3. Clear update cache: %SystemRoot%\\SoftwareDistribution\\Download\n4. Run: DISM /Online /Cleanup-Image /RestoreHealth\n5. Run: sfc /scannow\n6. Manual update download from catalog.update.microsoft.com","Medium"),
    ("Software","OS","Blue Screen of Death (BSOD)",
     "Windows shows stop error (BSOD) with error code.",
     "1. Note error code and module name from BSOD\n2. Check Event Viewer > Windows Logs > System for critical errors\n3. Run memory diagnostic: mdsched.exe\n4. Check for driver updates for flagged module\n5. Run startup repair if boot issues\n6. Escalate to Level 2 with BSOD dump file","High"),
    ("Software","Application","Application Not Launching",
     "Business application crashes on startup or shows error.",
     "1. Run as Administrator\n2. Check Event Viewer > Application for errors\n3. Verify .NET/Visual C++ runtimes are installed\n4. Reinstall application\n5. Check application logs in %APPDATA%\n6. Escalate to application owner if persists","Medium"),
    ("Software","License","Software License Expired",
     "Application shows license expired and will not open.",
     "1. Check License Management portal for renewal status\n2. IT Admin can push license key via GPO\n3. For Adobe/Microsoft, sign in with enterprise account to activate\n4. Submit license renewal request if expired\n5. Use web alternative if available (O365 Web Apps)","Medium"),
    ("Software","Microsoft 365","Teams Calls Dropping",
     "Microsoft Teams calls disconnecting or poor audio/video quality.",
     "1. Check network quality: Test-NetConnection teams.microsoft.com -Port 443\n2. Enable QoS in Teams settings for calls\n3. Use wired connection instead of WiFi\n4. Update Teams: Help > Check for Updates\n5. Clear Teams cache: %appdata%\\Microsoft\\Teams\\Cache","Medium"),
    ("Software","Microsoft 365","OneDrive Sync Issues",
     "OneDrive files not syncing or showing sync errors.",
     "1. Right-click OneDrive tray icon > Pause sync > Resume\n2. Sign out and back in to OneDrive\n3. Reset OneDrive: %localappdata%\\Microsoft\\OneDrive\\onedrive.exe /reset\n4. Check file path length limit (260 chars max)\n5. Check for unsupported characters in file names","Low"),
    ("Software","Microsoft 365","SharePoint Cannot Open Files",
     "Files on SharePoint won't open in desktop applications.",
     "1. Clear Office credential cache via Windows Credential Manager\n2. Enable 'Open with Explorer' for SharePoint library\n3. Map SharePoint as network drive\n4. Check if Office is activated and signed in to correct account\n5. Sync library with OneDrive instead","Low"),
    ("Software","Application","Application Performance Slow",
     "Business application running significantly slower than expected.",
     "1. Check system resources: Task Manager > Performance\n2. Verify application is connecting to correct server\n3. Clear application cache\n4. Check network latency to application server\n5. Review application event log\n6. Coordinate with application team for performance review","Medium"),
    ("Software","OS","User Profile Corruption",
     "Windows user profile is corrupted, login fails or desktop is blank.",
     "1. Log in with temporary admin account\n2. Copy user data from C:\\Users\\<username> to safe location\n3. Delete user profile from System Properties > Advanced > User Profiles\n4. Create new profile by logging back as user\n5. Restore user data\n6. Re-apply user settings","High"),
    ("Software","OS","Slow Computer Performance",
     "Computer is generally slow affecting all applications.",
     "1. Check startup programs: Task Manager > Startup\n2. Run Disk Cleanup: cleanmgr.exe\n3. Check disk health: chkdsk C: /f\n4. Verify antivirus is not running full scan\n5. Check for malware with Malwarebytes\n6. If > 3 years old machine, consider upgrade","Low"),
    ("Software","Microsoft 365","Office Activation Required",
     "Microsoft Office apps show deactivated and require activation.",
     "1. Open any Office app > File > Account > Sign In\n2. Use enterprise email and password\n3. Run: cscript ospp.vbs /dstatus (to check license)\n4. Run: cscript ospp.vbs /act (to force activation)\n5. Contact IT if license not assigned","Medium"),
    ("Software","Application","VDI/Remote Desktop Connection Issue",
     "Cannot connect to virtual desktop or Remote Desktop services.",
     "1. Verify VPN is connected\n2. Check RDP port: Test-NetConnection <vdi-server> -Port 3389\n3. Clear RDP credential cache\n4. Check if RDP sessions limit is reached\n5. Try different RDC client version\n6. Contact IT to verify server is up","Medium"),
    ("Software","OS","Windows Activation Error",
     "Windows shows 'Windows is not activated' error.",
     "1. Connect to corporate network or VPN\n2. Run: slmgr /ato\n3. Check KMS server connectivity: nslookup _vlmcs._tcp.enterprise.local\n4. If fails: slmgr /skms kms.enterprise.local && slmgr /ato\n5. Contact IT Admin if KMS unreachable","Medium"),
    ("Software","Drivers","Driver Installation Failure",
     "Device driver fails to install or causes system instability.",
     "1. Download correct driver from manufacturer site for your OS version\n2. Run as Administrator\n3. If fails, uninstall old driver first via Device Manager\n4. Run in compatibility mode if needed\n5. Use DDU (Display Driver Uninstaller) for GPU drivers","Medium"),
    ("Software","Application","Application Update Required",
     "Business application needs to be updated to continue functioning.",
     "1. Check for updates within application\n2. Corporate apps update via Software Center\n3. Run Windows Update for Microsoft applications\n4. If auto-update fails, download from IT Software Portal\n5. Do not run unofficial update packages","Low"),
    ("Software","Microsoft 365","Teams Status Always Away",
     "Teams status automatically changes to Away even when actively using computer.",
     "1. In Teams > Settings > Privacy, set status to Available manually\n2. Disable automatic status updates in Teams settings\n3. Check if screen saver or lock screen is triggering Away status\n4. Set screen saver timeout to 15+ minutes\n5. Install Teams Activity Reminder app","Low"),
    ("Software","Application","Application Crashes with Memory Error",
     "Application crashes with 'Out of Memory' or memory access violation error.",
     "1. Increase virtual memory: System Properties > Performance > Virtual Memory\n2. Close unnecessary applications before running\n3. Check RAM usage: Task Manager > Performance > Memory\n4. Run application repair or reinstall\n5. If 32-bit app, consider 64-bit version if available","Medium"),
    ("Software","OS","Disk Space Running Low",
     "System drive (C:) is running low on disk space.",
     "1. Run Disk Cleanup: cleanmgr /sageset:50 && cleanmgr /sagerun:50\n2. Move large files to OneDrive or network drive\n3. Uninstall unused applications\n4. Clear Windows update cache: dism /online /cleanup-image /startcomponentcleanup\n5. Request storage expansion if legitimately needed","Low"),
    ("Software","Development","Development Environment Setup",
     "Developer needs to set up local development environment.",
     "1. Install from Software Portal: Git, VS Code, Docker Desktop, Node.js/Python\n2. Clone company repo: git clone https://git.enterprise.local/org/repo.git\n3. Copy .env.example to .env and fill company credentials\n4. Run: npm install / pip install -r requirements.txt\n5. Contact Dev team lead for access to company repositories","Low"),
    ("Software","Microsoft 365","Power BI Cannot Connect to Data Source",
     "Power BI Desktop or Service shows data refresh errors.",
     "1. Verify credentials for data source are current\n2. For on-premises data: ensure Personal Gateway is running\n3. Check network connectivity to SQL Server/SharePoint\n4. Review firewall rules for Power BI service IPs\n5. Contact Data team for connection string updates","Medium"),

    # Access / IAM (10)
    ("Access","Active Directory","New Employee Account Creation",
     "IT needs to create accounts for a new employee joining the company.",
     "1. HR submits new hire form in onboarding portal\n2. IT creates AD account with naming convention: firstname.lastname\n3. Add to appropriate security groups per department\n4. Create M365 mailbox and license assignment\n5. Send welcome email with credentials and IT portal link","Low"),
    ("Access","Active Directory","User Account Deprovisioning",
     "Employee leaving company, all access needs to be revoked.",
     "1. REQUIRES HR AND MANAGER CONFIRMATION\n2. Disable AD account (not delete)\n3. Remove all security group memberships\n4. Revoke MFA and VPN\n5. Transfer email to manager with read access\n6. Archive data per 90-day retention policy\n7. Document everything in audit log","High"),
    ("Access","Permissions","Shared Folder Access Request",
     "Employee needs access to a shared network folder.",
     "1. Employee submits request via IT portal with business justification\n2. Manager approves request\n3. IT adds employee to corresponding AD security group\n4. Access granted within 30 minutes\n5. Access is reviewed quarterly","Low"),
    ("Access","Permissions","Application Access Request",
     "Employee needs access to a business application.",
     "1. Submit request in IT portal specifying application and access level\n2. Application owner approves\n3. IT provisions access in application\n4. Notify employee when access is ready\n5. All elevated access logged and reviewed monthly","Low"),
    ("Access","Active Directory","Group Policy Not Applying",
     "Windows Group Policy settings not being applied to workstation.",
     "1. Run: gpupdate /force\n2. Run: gpresult /r to check applied policies\n3. Ensure machine is domain-joined: System Properties > Computer Name\n4. Check event log for GP errors: Event Viewer > System\n5. Contact IT Admin if machine is in wrong OU","Medium"),
    ("Access","Remote Access","Remote Access Setup for WFH",
     "Employee needs to set up secure remote access from home.",
     "1. Install VPN client from IT portal\n2. Register device in MDM: https://mdm.enterprise.local/enroll\n3. Enable BitLocker encryption on device\n4. Install and configure MFA authenticator app\n5. Test VPN connection and email access from home","Low"),
    ("Access","Permissions","Admin Rights Request",
     "Employee needs temporary local administrator rights.",
     "1. Submit justification via IT security portal\n2. Manager and Security team approval required\n3. Temporary admin rights granted for 24-hour window\n4. All actions logged during elevated privilege period\n5. Rights automatically revoked after 24 hours","High"),
    ("Access","Active Directory","Account Name Change Request",
     "Employee name changed (marriage/legal) requiring AD account update.",
     "1. HR submits name change confirmation to IT\n2. Create new AD account with new name\n3. Migrate all mailbox data\n4. Update all application accounts\n5. Old account kept active for 30 days for redirect\n6. Notify relevant team members of email change","Medium"),
    ("Access","SSO","Single Sign-On Not Working",
     "SSO is not working for corporate applications.",
     "1. Clear browser cookies and cache\n2. Try SSO in InPrivate/Incognito mode\n3. Verify you're using corporate email for SSO\n4. Check if identity provider (Okta/Azure AD) is available\n5. Contact IT if SSO service shows any alerts","Medium"),
    ("Access","Permissions","Contractor Access Provisioning",
     "External contractor needs limited access to company systems.",
     "1. Contractor manager submits formal access request\n2. Legal/Compliance approves based on contract terms\n3. IT creates contractor account with contractor.lastname@enterprise.com\n4. Access limited to specific approved systems only\n5. Access automatically expires on contract end date","High"),

    # IT Operations (10)
    ("IT Operations","Asset Management","New Hardware Request",
     "Employee needs new or replacement hardware.",
     "1. Submit hardware request in IT Asset Portal\n2. Manager approval required for requests > $500\n3. IT checks refurbished stock first\n4. If purchase needed, procurement process takes 5-7 business days\n5. New hardware delivered and configured within 2 days of receipt","Low"),
    ("IT Operations","Software Deployment","Mass Software Deployment Request",
     "IT team needs to deploy software update to all endpoints.",
     "1. Test deployment on 10 pilot machines first\n2. Create deployment package in SCCM/Intune\n3. Schedule during maintenance window (Sat 10PM-6AM)\n4. Monitor deployment success rate via console\n5. Communicate to users via IT newsletter","Medium"),
    ("IT Operations","Server","Server Performance Degradation",
     "Production server showing high CPU/memory utilization.",
     "1. Check server dashboard in monitoring tool (Datadog/Zabbix)\n2. Identify top consuming processes\n3. Review recent deployments or config changes\n4. Scale resources if cloud-hosted\n5. Engage application owner for tuning\n6. Escalate to infrastructure team","High"),
    ("IT Operations","Backup","Backup Job Failure",
     "Scheduled backup job failed to complete successfully.",
     "1. Check backup log in Veeam/NetBackup console\n2. Verify backup target has sufficient space\n3. Check network connectivity to backup target\n4. Retry failed backup manually\n5. If consistent failures, review backup schedule and retention policy","High"),
    ("IT Operations","Monitoring","Server Monitoring Alert",
     "Automated monitoring has triggered an alert.",
     "1. Acknowledge alert in monitoring console\n2. SSH to server and check top, df -h, netstat -tlnp\n3. Review application logs in /var/log/\n4. Implement short-term fix to clear alert\n5. Create problem ticket for root cause investigation","High"),
    ("IT Operations","Network","WAN Link Saturation",
     "WAN link to branch office is saturated causing slowness.",
     "1. Check traffic in network monitoring tool\n2. Identify top bandwidth consumers: NetFlow data\n3. Apply QoS rules to prioritize business traffic\n4. Throttle or schedule large transfers to off-peak hours\n5. Evaluate WAN upgrade if consistently > 80% utilization","High"),
    ("IT Operations","Compliance","Patch Compliance Report Request",
     "Security team needs patch compliance report for audit.",
     "1. Run patch compliance report from SCCM/Intune console\n2. Export to Excel format\n3. Include: patch name, CVE, severity, compliance %\n4. Identify non-compliant machines and owners\n5. Provide remediation plan for critical patches","Medium"),
    ("IT Operations","Asset Management","Device Inventory Audit",
     "Annual device inventory audit needs to be conducted.",
     "1. Export current asset list from CMDB\n2. Run automated discovery scan on network\n3. Compare discovered vs registered assets\n4. Identify unregistered or missing devices\n5. Update CMDB with confirmed asset data\n6. Report lost/stolen devices to IT Security","Medium"),
    ("IT Operations","Disaster Recovery","DR Test Execution",
     "Annual disaster recovery test needs to be performed.",
     "1. Notify all stakeholders 2 weeks in advance\n2. Create DR runbook from last year's test\n3. Execute failover during approved maintenance window\n4. Test all critical systems and record RTO/RPO\n5. Document findings and create improvement plan\n6. Present results to management","High"),
    ("IT Operations","Cloud","Cloud Cost Optimization",
     "Cloud spending exceeded budget threshold.",
     "1. Pull cloud cost report from AWS/Azure console\n2. Identify top cost drivers\n3. Check for idle/untagged resources\n4. Rightsize oversized instances\n5. Implement auto-scaling for variable workloads\n6. Set budget alerts and review monthly","Medium"),
]

def seed_knowledge_articles():
    print("[*] Seeding 100 knowledge articles...")
    now = _now_minus(days=60)
    count = 0
    for i, template in enumerate(KB_TEMPLATES):
        article_num = f"KB-{i+1:04d}"
        category, subcategory, title, content, resolution, severity = template
        try:
            db_manager.execute(
                "INSERT INTO knowledge_articles "
                "(article_number,title,category,subcategory,content,resolution,severity,approved,views,created_at,updated_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(article_number) DO NOTHING",
                (article_num, title, category, subcategory, content, resolution, severity, 1,
                 random.randint(10, 500), now, now)
            )
            count += 1
        except Exception as e:
            pass
    print(f"    [OK] {count} knowledge articles seeded.")

# ---------------------------------------------------------------------------
# 4. INCIDENTS (500)
# ---------------------------------------------------------------------------
INCIDENT_TEMPLATES = [
    # (category, subcategory, issue_template, possible_statuses, priority_weights, resolution_templates)
    ("Network","VPN",
     ["VPN not connecting after Windows update","VPN authentication failing","VPN connection drops every hour",
      "Cannot access VPN from home network","VPN client crashes on startup","VPN split tunneling not working",
      "VPN connection extremely slow","VPN license error - cannot connect","VPN disconnects during video calls"],
     ["AUTO-RESOLUTION","RESOLVED","ESCALATION","INVESTIGATING"],
     [40, 30, 20, 10],
     ["Reset VPN adapter and reinstall profile","Cleared VPN credential cache and re-enrolled MFA",
      "Updated VPN client to latest version","Reconfigured DNS settings for VPN subnet"]),
    ("Network","WiFi",
     ["WiFi drops in conference room B","Cannot connect to corporate WiFi after OS upgrade",
      "WiFi performance very slow in engineering floor","WiFi authentication fails on new laptop",
      "Lost WiFi connection after Windows update","Intermittent WiFi in remote office"],
     ["AUTO-RESOLUTION","RESOLVED","ESCALATION","INVESTIGATING"],
     [50, 30, 15, 5],
     ["Forgot and rejoined WiFi network","Updated WiFi adapter drivers","Moved to 5GHz band",
      "Reset TCP/IP stack"]),
    ("Email","Outlook",
     ["Outlook not connecting to Exchange server","Outlook search not working","Outlook extremely slow",
      "Cannot open attachments in Outlook","Outlook calendar not syncing","Outlook freezing when composing emails",
      "Outlook profile corruption error","Cannot send emails - SMTP error"],
     ["AUTO-RESOLUTION","RESOLVED","ESCALATION","INVESTIGATING"],
     [35, 35, 20, 10],
     ["Rebuilt Outlook profile","Cleared Outlook cache","Re-ran email configuration wizard",
      "Reset Exchange connection settings"]),
    ("Security","Account Access",
     ["Password expired and cannot reset","Account locked after too many failed attempts",
      "MFA token not working","Cannot access VPN after password change",
      "Forgot backup MFA codes","New phone - need to re-enroll MFA"],
     ["AUTO-RESOLUTION","RESOLVED","PENDING_APPROVAL","ESCALATION"],
     [40, 30, 20, 10],
     ["Reset password via SSPR portal","Unlocked account in Active Directory",
      "Re-enrolled MFA device","Synced time on authenticator app"]),
    ("Hardware","Laptop",
     ["Laptop battery draining too fast","Laptop screen flickering","Laptop running very slow",
      "Laptop not recognizing external monitor","Laptop keyboard some keys not working",
      "Laptop overheating and shutting down","Laptop touchpad not working","Laptop won't turn on"],
     ["AUTO-RESOLUTION","RESOLVED","ESCALATION","PENDING_APPROVAL"],
     [30, 40, 20, 10],
     ["Replaced battery","Updated display drivers","Cleaned up startup programs and disk",
      "Replaced laptop keyboard","Cleared thermal paste and reseated cooling fan"]),
    ("Hardware","Printer",
     ["Printer showing offline","Print jobs stuck in queue","Cannot install printer driver",
      "Printer not printing in color","Printer paper jam","Network printer not visible on workstation"],
     ["AUTO-RESOLUTION","RESOLVED","ESCALATION"],
     [50, 35, 15],
     ["Restarted Print Spooler service","Reinstalled printer drivers","Cleared print queue",
      "Added printer via print server path"]),
    ("Software","Microsoft 365",
     ["Teams calls dropping frequently","OneDrive sync error","SharePoint permissions issue",
      "Office activation showing expired","Excel crashing when opening large files",
      "Teams status stuck on Away","Microsoft Forms not loading","Power BI refresh failing"],
     ["AUTO-RESOLUTION","RESOLVED","ESCALATION","INVESTIGATING"],
     [40, 30, 20, 10],
     ["Cleared Teams cache","Reset OneDrive sync","Reactivated Office with enterprise license",
      "Updated Microsoft 365 apps to latest version"]),
    ("Software","OS",
     ["Windows update failing with error 0x80070005","Blue screen with DRIVER_IRQL error",
      "Computer extremely slow after update","Windows not activating on corporate network",
      "Disk space critically low on C: drive","User profile corrupted after Windows update"],
     ["AUTO-RESOLUTION","RESOLVED","ESCALATION","PENDING_APPROVAL"],
     [30, 35, 25, 10],
     ["Ran DISM repair and Windows Update troubleshooter","Rolled back problematic driver",
      "Performed disk cleanup and moved files to OneDrive","Rebuilt user profile"]),
    ("Access","Permissions",
     ["Need access to Finance shared drive","Cannot access HR portal","Project folder access request",
      "Application license not assigned","Need admin rights for software installation",
      "Contractor access setup","VPN access for new joiner"],
     ["AUTO-RESOLUTION","RESOLVED","PENDING_APPROVAL","ESCALATION"],
     [35, 35, 25, 5],
     ["Granted access via AD security group","Provisioned application license",
      "Approved temporary admin rights for 24 hours","Created contractor account with limited access"]),
    ("IT Operations","Server",
     ["Production server high CPU alert","Database server memory usage at 95%",
      "Web server returning 502 errors","Backup job failing on file server",
      "Server disk space critically low","Application server response time degraded"],
     ["ESCALATION","INVESTIGATING","PENDING_APPROVAL","RESOLVED"],
     [40, 30, 20, 10],
     ["Restarted application service","Increased server memory allocation",
      "Cleared disk space and archived old logs","Identified and killed runaway process"]),
]

SEVERITY_MAP = {
    "RESOLVED": ["Low","Low","Medium"],
    "AUTO-RESOLUTION": ["Low","Low","Medium","Medium"],
    "ESCALATION": ["High","High","Medium","Critical"],
    "PENDING_APPROVAL": ["High","Critical","Medium"],
    "INVESTIGATING": ["Medium","High","Low"],
}

ASSIGNED_TEAMS = {
    "Network": "Network Team",
    "Email": "Email Team",
    "Security": "Security Team",
    "Hardware": "Hardware Team",
    "Software": "Software Team",
    "Access": "IAM Team",
    "IT Operations": "Infrastructure Team",
}

def seed_incidents(employees: list):
    print("[*] Seeding 500 historical incidents...")
    emp_ids = [e[0] for e in employees]
    emp_names = {e[0]: e[1] for e in employees}
    count = 0
    incident_ids = []

    for i in range(500):
        template = INCIDENT_TEMPLATES[i % len(INCIDENT_TEMPLATES)]
        category, subcategory, issues, statuses, weights, resolutions = template

        # Pick a status
        status = random.choices(statuses, weights=weights[:len(statuses)], k=1)[0]

        emp_id = random.choice(emp_ids)
        emp_name = emp_names[emp_id]
        issue = random.choice(issues)
        severity = random.choice(SEVERITY_MAP.get(status, ["Medium"]))
        priority = {"Critical": "Critical", "High": "High", "Medium": "Medium", "Low": "Low"}.get(severity, "Medium")
        confidence = {
            "AUTO-RESOLUTION": round(random.uniform(85, 99), 1),
            "RESOLVED": round(random.uniform(80, 99), 1),
            "ESCALATION": round(random.uniform(40, 65), 1),
            "PENDING_APPROVAL": round(random.uniform(60, 84), 1),
            "INVESTIGATING": round(random.uniform(55, 80), 1),
        }.get(status, 85.0)

        inc_num = f"INC-{10000 + i + 100}"
        inc_id = inc_num
        created_at = _rand_dt(days_back_min=1, days_back_max=90)
        updated_at = created_at
        resolved_at = None

        resolution = None
        assigned_to = "IT Auto-Bot" if status in ["AUTO-RESOLUTION", "RESOLVED"] else "IT Support"
        assigned_team = ASSIGNED_TEAMS.get(category, "IT Team")

        if status in ["AUTO-RESOLUTION", "RESOLVED"]:
            resolution = random.choice(resolutions)
            resolved_at = created_at
        elif status in ["ESCALATION", "INVESTIGATING"]:
            assigned_to = "Tier-2 IT"

        requires_approval = 1 if status == "PENDING_APPROVAL" else 0
        approval_status = "PENDING" if status == "PENDING_APPROVAL" else "N/A"
        ticket_number = f"TKT-{5000 + i}" if status in ["ESCALATION", "PENDING_APPROVAL"] else None

        try:
            db_manager.execute(
                "INSERT INTO incidents "
                "(incident_id,incident_number,employee_id,employee_name,issue,category,subcategory,"
                "priority,severity,confidence,status,assigned_to,assigned_team,resolution,"
                "resolution_strategy,ticket_number,requires_approval,approval_action,"
                "approval_reason,approval_status,created_at,updated_at,resolved_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) "
                "ON CONFLICT(incident_id) DO NOTHING",
                (inc_id, inc_num, emp_id, emp_name, issue, category, subcategory,
                 priority, severity, confidence, status, assigned_to, assigned_team,
                 resolution, "Auto-Fix" if status in ["AUTO-RESOLUTION","RESOLVED"] else "Escalate",
                 ticket_number, requires_approval,
                 f"Approve resolution for {issue[:50]}" if requires_approval else None,
                 "High-risk action requires human verification" if requires_approval else None,
                 approval_status, created_at, updated_at, resolved_at)
            )
            incident_ids.append(inc_id)
            count += 1
        except Exception as e:
            pass

    print(f"    [OK] {count} incidents seeded.")
    return incident_ids

# ---------------------------------------------------------------------------
# 5. TICKETS (100+)
# ---------------------------------------------------------------------------
def seed_tickets(incident_ids: list):
    print("[*] Seeding 100+ tickets...")
    count = 0
    for i in range(100):
        tkt_id = f"TKT-{5000 + i}"
        tkt_num = tkt_id
        inc_id = incident_ids[i] if i < len(incident_ids) else None
        priority = random.choice(["Low","Medium","High","Critical"])
        status = random.choice(["Open","In Progress","Resolved","Closed"])
        team = random.choice(["Network Team","Email Team","Security Team","Hardware Team","Infrastructure Team","IAM Team"])
        created_at = _rand_dt()
        updated_at = created_at
        try:
            db_manager.execute(
                "INSERT INTO tickets (ticket_id,ticket_number,incident_id,\"user\",issue,priority,status,assigned_team,created_at,updated_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?) ON CONFLICT(ticket_id) DO NOTHING",
                (tkt_id, tkt_num, inc_id, f"EMP{random.randint(1000,1099):04d}",
                 f"Escalated incident {inc_id or 'Unknown'}", priority, status, team, created_at, updated_at)
            )
            count += 1
        except Exception as e:
            pass
    print(f"    [OK] {count} tickets seeded.")

# ---------------------------------------------------------------------------
# 6. AUDIT LOGS (200+)
# ---------------------------------------------------------------------------
EVENT_TYPES = [
    ("planner_agent","plan_started","Planner agent received incident and began investigation planning"),
    ("planner_agent","plan_ready","Investigation plan generated successfully"),
    ("researcher_agent","research_started","Researcher agent began evidence collection"),
    ("researcher_agent","knowledge_base_queried","Knowledge base searched for matching articles"),
    ("researcher_agent","incident_database_queried","Historical incident database queried"),
    ("researcher_agent","hr_system_queried","HR system queried for employee context"),
    ("researcher_agent","research_complete","Evidence collection phase completed"),
    ("analysis_agent","analysis_started","Analysis agent began root cause analysis"),
    ("analysis_agent","analysis_complete","Root cause analysis and severity assessment completed"),
    ("decision_agent","decision_started","Decision agent evaluating lifecycle routing"),
    ("decision_agent","tool_called","Decision agent invoked tool"),
    ("decision_agent","decision_complete","Incident lifecycle decision made"),
    ("auto_fix_node","auto_fix_execution","Remediation email sent to employee. Incident auto-resolved."),
    ("escalate_node","ticket_creation","Escalation ticket generated and Tier-2 IT notified."),
    ("pending_approval_node","approval_paused","Workflow paused. Awaiting IT Admin HITL approval."),
    ("executor_agent","resolution_finalized","Executor agent completed final incident resolution record."),
    ("hitl_system","action_approved","Human-in-the-loop action approved by IT Admin."),
    ("hitl_system","action_rejected","Human-in-the-loop action rejected by IT Admin."),
    ("email_tool","email_sent","Resolution email delivered to employee successfully."),
    ("ticket_tool","ticket_created","IT support ticket created in ticketing system."),
]

def seed_audit_logs(incident_ids: list):
    print("[*] Seeding 200+ audit logs...")
    count = 0
    for i, inc_id in enumerate(incident_ids[:200]):
        # 1-3 events per incident
        n_events = random.randint(1, 3)
        events = random.sample(EVENT_TYPES, min(n_events, len(EVENT_TYPES)))
        base_time_offset = random.uniform(1, 90)
        for j, (agent, event_type, description) in enumerate(events):
            ts = _now_minus(days=base_time_offset, minutes=j*2)
            try:
                db_manager.execute(
                    "INSERT INTO audit_logs (incident_id,timestamp,agent_or_system,event_type,description,payload) "
                    "VALUES (?,?,?,?,?,?)",
                    (inc_id, ts, agent, event_type, description, json.dumps({"incident_id": inc_id, "step": j+1}))
                )
                count += 1
            except Exception:
                pass
    print(f"    [OK] {count} audit log entries seeded.")

# ---------------------------------------------------------------------------
# 7. AGENT EVENTS (500+)
# ---------------------------------------------------------------------------
def seed_agent_events(incident_ids: list):
    print("[*] Seeding 500+ agent events...")
    count = 0
    publishers = ["planner_agent","researcher_agent","analysis_agent","decision_agent","executor_agent","workflow","hitl_system"]
    event_types = ["plan_started","plan_ready","research_started","research_complete","analysis_started",
                   "analysis_complete","decision_started","decision_complete","tool_called","workflow_started",
                   "workflow_finished","action_approved","action_rejected"]
    for i in range(500):
        publisher = random.choice(publishers)
        event_type = random.choice(event_types)
        inc_id = random.choice(incident_ids) if incident_ids else f"INC-{10000+i}"
        session_id = f"SES-{str(uuid.uuid4())[:8].upper()}"
        ts = _rand_dt()
        try:
            db_manager.execute(
                "INSERT INTO agent_events (session_id,publisher,event_type,payload,timestamp) "
                "VALUES (?,?,?,?,?)",
                (session_id, publisher, event_type, json.dumps({"incident_id": inc_id, "iteration": i}), ts)
            )
            count += 1
        except Exception:
            pass
    print(f"    [OK] {count} agent events seeded.")

# ---------------------------------------------------------------------------
# 8. NOTIFICATIONS (50+)
# ---------------------------------------------------------------------------
NOTIFICATION_MESSAGES = [
    "Your incident has been automatically resolved. Please check your email for resolution steps.",
    "Your IT support ticket has been created. A specialist will contact you within 4 hours.",
    "Your incident is pending IT Admin approval. You will be notified once reviewed.",
    "Your VPN issue has been resolved. Please try connecting again.",
    "Your password has been successfully reset. Please update your MFA settings.",
    "Your access request has been approved. You can now access the requested resource.",
    "Your laptop hardware issue requires hands-on attention. Please visit IT desk (Room 201).",
    "Your incident has been escalated to our Tier-2 support team.",
    "Scheduled maintenance: Network maintenance tonight 10PM-2AM. VPN may be intermittent.",
    "Security Alert: Please change your password immediately and review your account activity.",
]

def seed_notifications(incident_ids: list):
    print("[*] Seeding 50+ notifications...")
    count = 0
    channels = ["email","dashboard","sms"]
    statuses = ["sent","delivered","read"]
    for i in range(80):
        inc_id = random.choice(incident_ids) if incident_ids else None
        recipient = f"emp{random.randint(1000,1099)}@enterprise.com"
        channel = random.choice(channels)
        status = random.choices(statuses, weights=[30,40,30], k=1)[0]
        message = random.choice(NOTIFICATION_MESSAGES)
        sent_at = _rand_dt()
        try:
            db_manager.execute(
                "INSERT INTO notifications (incident_id,recipient,channel,status,message,sent_at) "
                "VALUES (?,?,?,?,?,?)",
                (inc_id, recipient, channel, status, message, sent_at)
            )
            count += 1
        except Exception:
            pass
    print(f"    [OK] {count} notifications seeded.")

# ---------------------------------------------------------------------------
# 9. LONG-TERM MEMORY (30+)
# ---------------------------------------------------------------------------
MEMORY_ENTRIES = [
    ("vpn_resolution_pattern", {
        "pattern": "VPN connection failure after Windows update",
        "root_cause": "Windows update modifies network adapter settings, breaking VPN tunnel",
        "resolution": "Reset VPN adapter: netsh int ip reset. Reinstall VPN profile.",
        "confidence": 95, "verified": True, "occurrences": 47
    }),
    ("outlook_profile_corruption", {
        "pattern": "Outlook profile corruption after Windows upgrade",
        "root_cause": "Windows upgrade invalidates Outlook profile cache",
        "resolution": "Create new Outlook profile via Control Panel > Mail",
        "confidence": 88, "verified": True, "occurrences": 23
    }),
    ("wifi_driver_update_pattern", {
        "pattern": "WiFi drops after Windows Update KB patches",
        "root_cause": "Driver conflicts introduced by Windows Update",
        "resolution": "Roll back WiFi driver or update to manufacturer latest",
        "confidence": 82, "verified": True, "occurrences": 18
    }),
    ("account_lockout_pattern", {
        "pattern": "Account lockout from stale cached credentials",
        "root_cause": "Old password cached in mapped drives or services",
        "resolution": "Clear Windows Credential Manager and update all stored passwords",
        "confidence": 91, "verified": True, "occurrences": 35
    }),
    ("printer_spooler_fix", {
        "pattern": "Printer showing offline",
        "root_cause": "Print Spooler service crashed or stuck",
        "resolution": "Restart Print Spooler service and clear spool folder",
        "confidence": 97, "verified": True, "occurrences": 62
    }),
    ("teams_cache_fix", {
        "pattern": "Teams freezing or crashing",
        "root_cause": "Corrupted Teams local cache",
        "resolution": "Delete %appdata%\\Microsoft\\Teams\\Cache and restart Teams",
        "confidence": 89, "verified": True, "occurrences": 29
    }),
    ("mfa_time_sync", {
        "pattern": "MFA token rejected even with correct code",
        "root_cause": "Phone clock is not synchronized causing TOTP drift",
        "resolution": "Sync authenticator app time: Settings > Time Correction for Codes",
        "confidence": 93, "verified": True, "occurrences": 15
    }),
    ("onedrive_sync_fix", {
        "pattern": "OneDrive not syncing or stuck",
        "root_cause": "OneDrive client state machine stuck in error state",
        "resolution": "Reset OneDrive: %localappdata%\\Microsoft\\OneDrive\\onedrive.exe /reset",
        "confidence": 86, "verified": True, "occurrences": 31
    }),
    ("disk_space_critical", {
        "pattern": "C: drive full causing performance issues",
        "root_cause": "Windows Update cache and user temp files consuming excess space",
        "resolution": "Run DISM cleanup: dism /online /cleanup-image /startcomponentcleanup",
        "confidence": 94, "verified": True, "occurrences": 19
    }),
    ("ssl_cert_expiry", {
        "pattern": "SSL certificate expired on internal services",
        "root_cause": "Certificate auto-renewal misconfigured",
        "resolution": "Emergency renewal via PKI team. Escalate immediately.",
        "confidence": 99, "verified": True, "occurrences": 7
    }),
]

def seed_memory():
    print("[*] Seeding 30+ long-term memory entries...")
    count = 0
    now = _now_minus(days=30)
    for key, value_dict in MEMORY_ENTRIES:
        try:
            db_manager.execute(
                "INSERT INTO long_term_memory (key,value,updated_at) "
                "VALUES (?,?,?) ON CONFLICT(key) DO NOTHING",
                (key, json.dumps(value_dict), now)
            )
            count += 1
        except Exception:
            pass

    # Add employee history entries for first 20 employees
    for i in range(20):
        emp_id = f"EMP{1000 + i:04d}"
        try:
            db_manager.execute(
                "INSERT INTO long_term_memory (key,value,updated_at) "
                "VALUES (?,?,?) ON CONFLICT(key) DO NOTHING",
                (f"{emp_id}_history", json.dumps({
                    "employee_id": emp_id,
                    "previous_incidents_count": random.randint(1, 15),
                    "most_common_issue": random.choice(["VPN","Outlook","WiFi","Password","Teams"]),
                    "successful_resolutions": random.randint(1, 12),
                    "vip_status": i < 5
                }), now)
            )
            count += 1
        except Exception:
            pass

    print(f"    [OK] {count} memory entries seeded.")

# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def reset_tables():
    """Drop all seed data from tables (not tables themselves)."""
    print("[!] Resetting all data tables...")
    tables = [
        "notifications","audit_logs","agent_events","tool_executions",
        "workflow_results","incidents","tickets","knowledge_articles",
        "long_term_memory","employees","departments","users"
    ]
    for t in tables:
        try:
            db_manager.execute(f"DELETE FROM {t}")
            print(f"    [OK] Cleared {t}")
        except Exception as e:
            print(f"    [!] Could not clear {t}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Production seed script for AI IT Incident Platform")
    parser.add_argument("--reset", action="store_true", help="Reset all data before seeding")
    args = parser.parse_args()

    print("\n" + "="*60)
    print("  AI IT Incident Platform — Production Seed Script")
    print("="*60)

    # Initialize schema first
    init_databases()

    if args.reset:
        reset_tables()

    seed_departments()
    employees = seed_employees()
    seed_knowledge_articles()
    incident_ids = seed_incidents(employees)
    seed_tickets(incident_ids)
    seed_audit_logs(incident_ids)
    seed_agent_events(incident_ids)
    seed_notifications(incident_ids)
    seed_memory()

    print("\n" + "="*60)
    print("  Seed Complete! Summary:")
    tables_to_count = [
        "departments","employees","users","knowledge_articles",
        "incidents","tickets","audit_logs","agent_events","notifications","long_term_memory"
    ]
    for t in tables_to_count:
        try:
            row = db_manager.fetchone(f"SELECT COUNT(*) AS c FROM {t}")
            print(f"  {t:<25} {row['c']:>5} rows")
        except Exception as e:
            print(f"  {t:<25} ERROR: {e}")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
