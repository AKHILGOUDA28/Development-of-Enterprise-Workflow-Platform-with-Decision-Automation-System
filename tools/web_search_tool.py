"""
web_search_tool.py
------------------
Simulated Web Search / IT Knowledge Search Tool.
Returns curated IT article summaries, technical documentation snippets,
and community forum answers for a given IT-related query.
"""

from typing import Union
from pydantic import BaseModel, Field
from tools.base_tool import BaseTool


# ---------------------------------------------------------------------------
# Pydantic Schema (Coerces both int and str for max_results)
# ---------------------------------------------------------------------------
class WebSearchSchema(BaseModel):
    query: str = Field(..., description="IT-related search query or topic")
    max_results: Union[int, str] = Field(default=3, description="Maximum number of results to return (integer 1-10)")


# ---------------------------------------------------------------------------
# Simulated Knowledge Article Database
# ---------------------------------------------------------------------------
ARTICLES = [
    {
        "title": "How to Troubleshoot Application Installation Errors & UAC Rights",
        "source": "Windows Enterprise Support",
        "url": "https://support.microsoft.com/app-install-fix",
        "snippet": (
            "Application installation failures are frequently caused by insufficient administrator rights, "
            "corrupted %TEMP% files, or missing Visual C++ redistributable packages. "
            "Fix: (1) Run installer as Administrator (elevated prompt), (2) Clear temp directory, "
            "(3) Temporarily disable antivirus real-time shield during install."
        ),
        "tags": ["software", "application", "install", "installation", "uac", "windows"]
    },
    {
        "title": "How to Troubleshoot VPN Connectivity Issues After Windows Update",
        "source": "Microsoft Support Docs",
        "url": "https://support.microsoft.com/vpn-troubleshoot",
        "snippet": (
            "After a Windows Update, VPN clients may fail to connect due to changes in "
            "network adapter settings. Resolution: (1) Reinstall VPN client, "
            "(2) Reset WinSock stack with 'netsh winsock reset', (3) Check firewall rules."
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
            "(2) Flush Kerberos tickets with 'klist purge', (3) Verify DNS."
        ),
        "tags": ["active directory", "domain", "login", "authentication", "kerberos"]
    },
    {
        "title": "Printer Offline: Common Causes and Fixes for Enterprise Printers",
        "source": "HP Enterprise Support",
        "url": "https://support.hp.com/printer-offline",
        "snippet": (
            "Enterprise printers show 'offline' status due to IP changes or print spooler corruption. "
            "Fix: (1) Restart Print Spooler service, (2) Clear spooler cache, (3) Re-add printer."
        ),
        "tags": ["printer", "offline", "print spooler", "driver", "network"]
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

    def _execute(self, query: str, max_results: Union[int, str] = 3) -> str:
        query_lower = query.lower()

        try:
            limit = int(max_results)
        except Exception:
            limit = 3

        scored = []
        for article in ARTICLES:
            score = 0
            for tag in article["tags"]:
                if tag in query_lower:
                    score += 2
            title_words = article["title"].lower().split()
            for word in query_lower.split():
                if word in title_words and len(word) > 3:
                    score += 1
            if score > 0:
                scored.append((score, article))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = [art for _, art in scored[:limit]]

        if not results:
            return (
                f"No relevant articles found for '{query}'. "
                "Try keywords like 'install', 'VPN', 'BSOD', 'printer offline'."
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


web_search_tool = WebSearchTool()
