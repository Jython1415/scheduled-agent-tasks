#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "claude-agent-sdk",
# ]
# ///
"""
TASK_NAME Research Task

Template for scheduled research tasks using Claude Agent SDK.
Copy the entire _template folder and modify get_research_prompt() for your specific needs.

Usage:
  1. Copy the template folder: cp -r tasks/_template tasks/my-task
  2. Modify get_research_prompt() in tasks/my-task/research.py
  3. Copy the workflow: cp .github/workflows/_template.yml .github/workflows/my-task.yml
  4. Replace TASK_NAME with my-task in the workflow file
  5. Set your desired schedule in the workflow
"""

import asyncio
import os
import sys

try:
    from claude_agent_sdk import query, ClaudeAgentOptions
except ImportError:
    print("ERROR: claude-agent-sdk not installed", file=sys.stderr)
    print("Run with: uv run research.py", file=sys.stderr)
    sys.exit(1)


def get_research_prompt() -> str:
    """
    Customize this function with your research task.

    The prompt should:
    1. Clearly state what to research
    2. Specify where to look (URLs, sources)
    3. Define what constitutes an alert
    4. End with: Print "ALERT: [summary]" or "SILENT"

    Example:
        Research: React 19 stable release status

        Check:
        1. React blog (react.dev/blog)
        2. GitHub releases (github.com/facebook/react)
        3. NPM package (npmjs.com/package/react)

        Alert if: React 19.x stable (not beta/RC) is released
        Include: Version number and release date

        Otherwise: Print "SILENT"
    """
    return """
Research Task: [DESCRIBE YOUR TASK]

Search for:
1. [Specific thing to monitor]
2. [Another thing to check]

Sources to check:
- [Official website/blog]
- [GitHub releases]
- [Documentation]

If [condition that matters]:
  - Print "ALERT: [Brief summary of what was found]"

If nothing significant found:
  - Print "SILENT"

Be thorough but efficient with searches.
"""


async def main():
    """Execute the research task"""

    # Check authentication
    oauth_token = os.getenv('CLAUDE_CODE_OAUTH_TOKEN')
    api_key = os.getenv('ANTHROPIC_API_KEY')

    if not oauth_token and not api_key:
        print("ERROR: No authentication configured", file=sys.stderr)
        print("Set either CLAUDE_CODE_OAUTH_TOKEN or ANTHROPIC_API_KEY", file=sys.stderr)
        sys.exit(1)

    auth_method = "OAuth" if oauth_token else "API Key"
    print(f"Authentication: {auth_method}")
    print("-" * 50)

    # Configure Claude Agent
    options = ClaudeAgentOptions(
        cwd=".",
        allowed_tools=["WebSearch", "WebFetch"],
        permission_mode="bypassPermissions",
        max_turns=10,
        system_prompt="""You are a focused research agent.
Your job: search for specific information, analyze findings, report concisely.
Be thorough but efficient. Only report significant findings.""",
    )

    prompt = get_research_prompt()

    try:
        # Run research
        async for message in query(prompt=prompt, options=options):
            print(message)

        print("-" * 50)

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        sys.exit(130)
