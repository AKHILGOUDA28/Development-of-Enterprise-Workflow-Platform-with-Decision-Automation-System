"""
web_search_tool.py
------------------
Simulated Web Search / IT Knowledge Search Tool.

Returns curated IT article summaries, technical documentation snippets,
and community forum answers for a given IT-related query.
Simulates integration with an enterprise search gateway.
"""

from pydantic import BaseModel, Field
from tools.base_tool import BaseTool


# ---------------------------------------------------------------------------
# Pydantic Schema
# ---------------------------------------------------------------------------
class WebSearchSchema(BaseModel):
    query: str = Field(..., description="IT-related search query or topic")
    max_results: int = Field(default=3, ge=1, le=10, description="Maximum number of results to return")


# ---------------------------------------------------------------------------
# Simulated Knowledge Article Database
# ---------------------------------------------------------------------------
ARTICLES = [
    {
        "title": "How to Troubleshoot VPN Connectivity Issues After Windows Update",
        "source": "Microsoft Support Docs",
        "url": "https://support.microsoft.com/vpn-troubleshoot",
        "snippet": (
            "After a Windows Update, VPN clients may fail to connect due to changes in "
            "network adapter settings. Resolution: (1) Reinstall VPN client, "
            "(2) Reset WinSock stack with 'netsh winsock reset', (3) Check firewall rules. "
            "Most connectivity issues resolve after restarting the 'IKE and AuthIP IPsec Keying Modules' service."
        ),
        "tags": ["vpn", "windows", "update", "network", "connectivity"]
    },
    {
        "title": "Active Directory: Users Cannot Log In After Domain Controller Upgrade",
        "source": "TechNet Community",
        "url": "https://techcommunity.microsoft.com/ad-login-dc-upgrade",
        "snippet": (
            "Login failures after DC upgrade are commonly caused by Kerberos ticket caching issues. "
            "Steps: (1) Force Group Policy update with 'gpupdate /force', "
            "(2) Flush Kerberos tickets with 'klist purge', "
            "(3) Verify DNS is pointing to the new DC, (4) Check AD replication status."
        ),
        "tags": ["active directory", "domain", "login", "authentication", "kerberos"]
    },
    {
        "title": "Printer Offline: Common Causes and Fixes for Enterprise Printers",
        "source": "HP Enterprise Support",
        "url": "https://support.hp.com/printer-offline",
        "snippet": (
            "Enterprise printers show 'offline' status for several reasons: "
            "IP address changes, print spooler corruption, or network adapter failure. "
            "Fix: (1) Restart Print Spooler service, (2) Delete stuck jobs, "
            "(3) Reassign printer IP using static DHCP lease, (4) Reinstall printer drivers."
        ),
        "tags": ["printer", "offline", "print spooler", "driver", "network"]
    },
    {
        "title": "Wi-Fi Drops Intermittently — Enterprise WLAN Diagnosis Guide",
        "source": "Cisco Networking Academy",
        "url": "https://cisco.com/wlan-intermittent",
        "snippet": (
            "Intermittent Wi-Fi drops are often caused by channel congestion, DHCP exhaustion, "
            "or rogue access points. Diagnosis steps: (1) Run 'netsh wlan show all' to assess signal, "
            "(2) Check DHCP lease count on the controller, "
            "(3) Enable band steering to push devices to 5 GHz, "
            "(4) Review AP channel overlap using Wi-Fi analyzer."
        ),
        "tags": ["wifi", "wireless", "wlan", "drops", "network", "dhcp"]
    },
    {
        "title": "Blue Screen of Death (BSOD): DRIVER_IRQL_NOT_LESS_OR_EQUAL Fix",
        "source": "Windows Debugging Community",
        "url": "https://community.windows-debug.com/bsod-driver-irql",
        "snippet": (
            "This BSOD is caused by a driver accessing an invalid memory address. "
            "Resolution: (1) Boot to Safe Mode, (2) Run 'sfc /scannow' for corrupted files, "
            "(3) Run 'chkdsk /f /r' to repair disk errors, "
            "(4) Update or rollback the most recently installed driver, "
            "(5) Use WinDbg to analyze the memory dump file."
        ),
        "tags": ["bsod", "blue screen", "driver", "crash", "memory", "hardware"]
    },
    {
        "title": "Office 365 Outlook: Profile Corrupted — Cannot Open PST File",
        "source": "Microsoft 365 Admin Docs",
        "url": "https://docs.microsoft.com/outlook-pst-corrupt",
        "snippet": (
            "Corrupted Outlook profiles manifest as startup crashes or 'Cannot open your default email folders'. "
            "Fix: (1) Run 'scanpst.exe' (Inbox Repair Tool) against the PST file, "
            "(2) Create a new Outlook profile via Control Panel → Mail, "
            "(3) If using Exchange, reconnect mailbox via Admin Center."
        ),
        "tags": ["outlook", "office 365", "email", "pst", "profile", "corrupt"]
    },
    {
        "title": "Server Disk Full: Immediate Actions for Production Systems",
        "source": "SysAdmin Handbook",
        "url": "https://sysadmin.handbook.com/disk-full",
        "snippet": (
            "A full disk on a production server can cause service outages. Immediate steps: "
            "(1) Run 'du -sh /*' to identify large directories, "
            "(2) Clear log files in /var/log older than 30 days, "
            "(3) Remove old package caches with 'apt-get clean', "
            "(4) Move archived data to NAS or cold storage, "
            "(5) Set up logrotate for automatic log management."
        ),
        "tags": ["server", "disk", "storage", "full", "linux", "logs"]
    },
    {
        "title": "Two-Factor Authentication (2FA) Bypass Issues — Enterprise MFA Guide",
        "source": "Security Best Practices Hub",
        "url": "https://security-hub.com/mfa-issues",
        "snippet": (
            "MFA failures in enterprise environments are often caused by time sync issues or "
            "provisioning errors. Checklist: (1) Ensure device clock is synchronized with NTP, "
            "(2) Re-provision the MFA token in the admin portal, "
            "(3) Check if the user's account is locked in Active Directory, "
            "(4) Verify RADIUS server connectivity for hardware token users."
        ),
        "tags": ["mfa", "2fa", "authentication", "security", "radius", "token"]
    },
]


# ---------------------------------------------------------------------------
# Tool Implementation
# ---------------------------------------------------------------------------
class WebSearchTool(BaseTool):
    name = "web_search"
    description = (
        "Searches the enterprise IT knowledge gateway for technical articles, "
        "documentation, and community solutions related to IT issues."
    )
    args_schema = WebSearchSchema

    def _execute(self, query: str, max_results: int = 3) -> str:
        query_lower = query.lower()

        # Score each article by tag/title keyword overlap
        scored = []
        for article in ARTICLES:
            score = 0
            for tag in article["tags"]:
                if tag in query_lower:
                    score += 2
            # Title match bonus
            title_words = article["title"].lower().split()
            for word in query_lower.split():
                if word in title_words and len(word) > 3:
                    score += 1
            if score > 0:
                scored.append((score, article))

        # Sort by relevance
        scored.sort(key=lambda x: x[0], reverse=True)
        results = [art for _, art in scored[:max_results]]

        if not results:
            return (
                f"No relevant articles found for '{query}'. "
                "Try more specific IT keywords (e.g., 'VPN', 'BSOD', 'printer offline')."
            )

        lines = [f"Web Search Results for: '{query}' ({len(results)} found)\n"]
        for i, art in enumerate(results, 1):
            lines.append(
                f"[{i}] {art['title']}\n"
                f"    Source: {art['source']}\n"
                f"    URL: {art['url']}\n"
                f"    Summary: {art['snippet']}\n"
            )

        return "\n".join(lines)


# Singleton instance
web_search_tool = WebSearchTool()
