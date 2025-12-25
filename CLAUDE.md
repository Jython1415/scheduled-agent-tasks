# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Scheduled Agent Tasks: A template system for running scheduled AI-powered research tasks using Claude Agent SDK in GitHub Actions. Each task is self-contained with its own research logic and results storage.

## Project Structure

- **`tasks/`**: Self-contained research task folders
  - **`_template/`**: Template for creating new tasks
  - **`bluesky-labelers/`**: Example task monitoring Bluesky labeler health
  - Each task has:
    - `research.py`: PEP 723 inline-dependency script that uses Claude Agent SDK
    - `results/`: Timestamped outputs organized by month, plus `latest.md`
- **`.github/workflows/`**: GitHub Actions workflows
  - **`_template.yml`**: Template for scheduling new tasks
  - Individual workflows per task (e.g., `bluesky-labelers.yml`)
  - **`claude.yml`**: Claude PR Assistant workflow

## Common Commands

### Running Tasks Locally

All research scripts use PEP 723 inline dependencies and must be run with `uv`:

```bash
# Run a specific task
uv run tasks/bluesky-labelers/research.py

# Run template to test structure
uv run tasks/_template/research.py
```

**Authentication**: Tasks require either `CLAUDE_CODE_OAUTH_TOKEN` or `ANTHROPIC_API_KEY` environment variable. Some tasks (like bluesky-labelers) require additional credentials (e.g., `BLUESKY_HANDLE`, `BLUESKY_APP_PASSWORD`).

### Creating a New Task

```bash
# 1. Copy template folder
cp -r tasks/_template tasks/my-task

# 2. Edit the research prompt
# Modify get_research_prompt() in tasks/my-task/research.py

# 3. Copy workflow template
cp .github/workflows/_template.yml .github/workflows/my-task.yml

# 4. Update workflow file
# Replace all instances of TASK_NAME with my-task
# Set desired cron schedule
```

### Working with Git

Standard git workflows apply. GitHub Actions automatically commits results when alerts are found.

## Architecture

### Research Task Pattern

Each task follows this structure:

1. **PEP 723 Script Header**: Declares Python version and dependencies inline
2. **`get_research_prompt()`**: Returns the research instructions for Claude Agent
3. **`main()`**: Orchestrates:
   - Authentication checks (Claude + optional external services)
   - Data gathering (e.g., API calls to Bluesky)
   - Context building for Claude
   - Claude Agent SDK query with `ClaudeAgentOptions`
4. **Output Format**: Either `ALERT: [summary]` or `SILENT`

### Claude Agent SDK Configuration

Tasks use `ClaudeAgentOptions` with:
- `allowed_tools`: Restricted to `["WebSearch", "WebFetch"]` for safety
- `permission_mode`: `"bypassPermissions"` for automation
- `max_turns`: 10-15 depending on complexity
- `system_prompt`: Task-specific research instructions

### GitHub Actions Workflow Pattern

1. **Trigger**: Scheduled (cron) + manual (`workflow_dispatch`)
2. **Setup**: Checkout, install uv, install Python 3.10
3. **Execute**: Run research script, capture output
4. **Detect**: Check for `ALERT:` in output
5. **Save**: Write results to `tasks/TASK_NAME/results/YYYY-MM/YYYY-MM-DD.md`
6. **Commit**: Commit results if alert found
7. **Notify**: Fail workflow on alert (triggers email notifications)

### Results Organization

- Results stored in `tasks/TASK_NAME/results/`
- Organized by month: `YYYY-MM/YYYY-MM-DD.md`
- `latest.md`: Symlink or copy of most recent result
- Only alerts trigger commits (unless customized per workflow)

## Task Development Notes

### Writing Research Prompts

The `get_research_prompt()` function should:
- Clearly state what to research
- Specify sources to check (URLs, APIs, etc.)
- Define alert conditions
- Always end with: Print `ALERT: [summary]` or `SILENT`

### Authentication Patterns

Tasks check for authentication early in `main()`:
```python
oauth_token = os.getenv('CLAUDE_CODE_OAUTH_TOKEN')
api_key = os.getenv('ANTHROPIC_API_KEY')
if not oauth_token and not api_key:
    # Error and exit
```

External services (like Bluesky) follow similar pattern with their own environment variables.

### Error Handling

- Scripts exit with status 1 on errors
- `KeyboardInterrupt` exits with status 130
- Workflows use `continue-on-error: false` to fail fast

### Known Patterns in bluesky-labelers Task

- Fetches labeler subscriptions via AT Protocol
- Checks connectivity by inspecting `atproto-content-labelers` response headers
- Builds markdown context report for Claude
- Filters out known issues to avoid repeated alerts
- Combines connectivity checks with web research for comprehensive monitoring
