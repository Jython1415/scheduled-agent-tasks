#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "claude-agent-sdk",
#   "atproto",
# ]
# ///
"""
Bluesky Labeler Monitoring Task

Monitors subscribed Bluesky labelers for:
- Connectivity issues (offline/unreachable labelers)
- Recent controversies or trust issues
- Policy changes or operational updates
- Community concerns or complaints

Runs biweekly to check all subscribed labelers.
"""

import asyncio
import os
import sys
from datetime import datetime, timezone

try:
    from claude_agent_sdk import query, ClaudeAgentOptions
    from atproto import Client
except ImportError as e:
    print(f"ERROR: Required package not installed: {e}", file=sys.stderr)
    print("Run with: uv run research.py", file=sys.stderr)
    sys.exit(1)


def check_labeler_connectivity(client, labeler_did: str, user_did: str) -> str:
    """
    Check if a labeler is reachable by the AppView.

    Makes a getProfile request with the labeler in the accept header.
    If the response includes atproto-content-labelers header with this labeler,
    it means the AppView successfully connected to it.

    Returns: 'connected', 'not_connected', or 'error'
    """
    try:
        # Make request with this specific labeler in the header
        url = client._build_url('app.bsky.actor.getProfile')
        params = {'actor': user_did}

        # Add the labeler to the accept header
        headers = {
            'atproto-accept-labelers': labeler_did
        }

        response = client.request.get(url, params=params, headers=headers)

        # Check if the response headers include this labeler in content-labelers
        response_headers = response.headers
        content_labelers = response_headers.get('atproto-content-labelers', '')

        # The AppView includes labelers it successfully connected to
        if labeler_did in content_labelers:
            return 'connected'
        else:
            return 'not_connected'

    except Exception as e:
        print(f"Error checking connectivity for {labeler_did}: {e}", file=sys.stderr)
        return 'error'


def time_ago(dt) -> str:
    """Convert datetime to human-readable time ago string."""
    now = datetime.now(timezone.utc)
    diff = now - dt

    seconds = diff.total_seconds()

    if seconds < 60:
        return f"{int(seconds)} seconds ago"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    elif seconds < 2592000:  # 30 days
        weeks = int(seconds / 604800)
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
    elif seconds < 31536000:  # 365 days
        months = int(seconds / 2592000)
        return f"{months} month{'s' if months != 1 else ''} ago"
    else:
        years = int(seconds / 31536000)
        return f"{years} year{'s' if years != 1 else ''} ago"


def parse_iso_datetime(dt_str: str) -> datetime:
    """Parse ISO datetime string to datetime object."""
    if '.' in dt_str:
        return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    else:
        return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))


def get_research_prompt() -> str:
    """
    Build research prompt for Claude Agent to check labeler health.

    This orchestrates:
    1. Connectivity check for all subscribed labelers
    2. Research on labelers for recent issues/concerns
    3. Output structured alert or SILENT
    """
    return """You are monitoring Bluesky labeler subscriptions for potential issues.

Your task:
1. First, I will provide you with a connectivity report showing which labelers are online/offline
2. For each labeler, research recent mentions:
   - Controversies or trust issues (past 2-4 weeks)
   - Policy changes or operational updates
   - Community concerns or complaints
   - Reports of inappropriate behavior or misuse

**Known Issues to Ignore** (do not alert on these):

- **Laelaps (@laelaps.fyi)**: The "interacts" label is a known controversial feature that
  labels users who interact with flagged accounts. This is by design and not a new issue.

- **Anti "Anti-AI" Labeler (@antiantiai.bsky.social)**: Was created in Nov 2024 during the
  Hugging Face dataset controversy. The initial controversy is known and not concerning.

Only report NEW or WORSENING issues, not the known controversies listed above.

Sources to check:
- Bluesky posts mentioning the labeler name or handle
- GitHub issues/discussions (if the labeler has a public repo)
- Community forums, blog posts, or announcements
- Any official labeler communications
- Online articles discussing the labeler

Guidelines:
- Prioritize recent information (past 2-4 weeks)
- Be thorough but efficient with searches
- Distinguish between legitimate concerns and unfounded complaints
- **Filter out the known issues listed above**

Output format:
- If you find connectivity issues OR new/significant concerns:
  Print "ALERT: Issues found with Bluesky labelers" followed by details

- If all labelers are healthy and no NEW significant concerns found:
  Print "SILENT" followed by details from your research

Be objective and fact-based in your assessment. The goal is to identify real NEW issues
that warrant review of labeler subscriptions.
"""


async def main():
    """Execute the labeler monitoring task"""

    # Check Bluesky authentication
    bluesky_handle = os.getenv('BLUESKY_HANDLE')
    bluesky_password = os.getenv('BLUESKY_APP_PASSWORD')

    if not bluesky_handle or not bluesky_password:
        print("ERROR: Bluesky credentials not configured", file=sys.stderr)
        print("Set BLUESKY_HANDLE and BLUESKY_APP_PASSWORD environment variables", file=sys.stderr)
        sys.exit(1)

    # Check Claude authentication
    oauth_token = os.getenv('CLAUDE_CODE_OAUTH_TOKEN')
    api_key = os.getenv('ANTHROPIC_API_KEY')

    if not oauth_token and not api_key:
        print("ERROR: No Claude authentication configured", file=sys.stderr)
        print("Set either CLAUDE_CODE_OAUTH_TOKEN or ANTHROPIC_API_KEY", file=sys.stderr)
        sys.exit(1)

    auth_method = "OAuth" if oauth_token else "API Key"
    print(f"Authentication: Bluesky ({bluesky_handle}) + Claude ({auth_method})")
    print("-" * 70)

    try:
        # Login to Bluesky
        print("Connecting to Bluesky...")
        client = Client()
        client.login(bluesky_handle, bluesky_password)
        user_did = client.me.did
        print(f"Logged in as: {bluesky_handle} ({user_did})")
        print()

        # Fetch labeler subscriptions
        print("Fetching labeler subscriptions...")
        url = client._build_url('app.bsky.actor.getPreferences')
        raw_response = client.request.get(url)
        prefs_data = raw_response.content.get('preferences', [])

        # Find labelersPref
        labelers_data = None
        for pref in prefs_data:
            if pref.get('$type') == 'app.bsky.actor.defs#labelersPref':
                labelers_data = pref
                break

        if not labelers_data or not labelers_data.get('labelers'):
            print("No labeler subscriptions found.")
            print("SILENT")
            return

        labelers_list = labelers_data.get('labelers', [])
        labeler_dids = [labeler['did'] for labeler in labelers_list]

        print(f"Found {len(labeler_dids)} subscribed labeler(s)")
        print()

        # Fetch labeler details
        print("Fetching labeler details...")
        labelers_response = client.app.bsky.labeler.get_services(params={'dids': labeler_dids})

        # Check connectivity for each labeler
        print("Checking AppView connectivity...")
        print("-" * 70)

        labeler_info = []
        connectivity_issues = []

        for view in labelers_response.views:
            name = view.creator.display_name or view.creator.handle
            handle = view.creator.handle
            did = view.creator.did

            # Check connectivity
            connectivity = check_labeler_connectivity(client, did, user_did)

            # Get indexed_at for reference
            if hasattr(view, 'indexed_at') and view.indexed_at:
                indexed_dt = parse_iso_datetime(view.indexed_at)
                ago = time_ago(indexed_dt)
            else:
                indexed_dt = None
                ago = "Unknown"

            status_symbol = "✓" if connectivity == "connected" else "✗"
            print(f"{status_symbol} {name} (@{handle})")
            print(f"  Service updated: {ago}")
            print(f"  Status: {connectivity}")
            print()

            labeler_info.append({
                'name': name,
                'handle': handle,
                'did': did,
                'connectivity': connectivity,
                'service_updated': ago,
            })

            if connectivity != 'connected':
                connectivity_issues.append({
                    'name': name,
                    'handle': handle,
                    'did': did,
                    'service_updated': ago,
                })

        print("-" * 70)
        print(f"Connectivity check complete: {len([l for l in labeler_info if l['connectivity'] == 'connected'])}/{len(labeler_info)} connected")
        print()

        # Build context for Claude Agent research
        context_report = "# Bluesky Labeler Connectivity Report\n\n"
        context_report += f"**Total labelers checked:** {len(labeler_info)}\n"
        context_report += f"**Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n\n"

        if connectivity_issues:
            context_report += "## ⚠️ Connectivity Issues\n\n"
            for labeler in connectivity_issues:
                context_report += f"- **{labeler['name']}** (@{labeler['handle']})\n"
                context_report += f"  - DID: `{labeler['did']}`\n"
                context_report += f"  - Service updated: {labeler['service_updated']}\n"
                context_report += f"  - Status: Offline/unreachable\n\n"
        else:
            context_report += "## ✓ All Labelers Connected\n\n"
            context_report += "All subscribed labelers are currently reachable by the AppView.\n\n"

        context_report += "## Subscribed Labelers\n\n"
        for labeler in labeler_info:
            context_report += f"- **{labeler['name']}** (@{labeler['handle']})\n"

        # Prepare full research prompt
        full_prompt = get_research_prompt() + "\n\n" + context_report
        full_prompt += "\n\nNow research these labelers for recent issues, controversies, or concerns. "
        full_prompt += "Focus especially on labelers that are offline or have connectivity issues."

        # Configure Claude Agent
        print("Starting research with Claude Agent...")
        print("-" * 70)

        options = ClaudeAgentOptions(
            cwd=".",
            allowed_tools=["WebSearch", "WebFetch"],
            permission_mode="bypassPermissions",
            max_turns=15,  # Allow more turns for thorough research
            system_prompt="""You are a focused research agent monitoring Bluesky labeler health.
Your job: analyze connectivity status, search for recent issues/controversies, report significant findings.
Be thorough but efficient. Only report issues that warrant attention or review.""",
        )

        # Run research
        async for message in query(prompt=full_prompt, options=options):
            print(message)

        print("-" * 70)

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        sys.exit(130)
