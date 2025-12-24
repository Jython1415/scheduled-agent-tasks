# Scheduled Agent Tasks

Template for running scheduled AI-powered research tasks using Claude Agent SDK in GitHub Actions.

## Quick Start

1. **Set up authentication:** Run `claude setup-token` locally, then add to GitHub Secrets:
   ```bash
   gh secret set CLAUDE_CODE_OAUTH_TOKEN
   ```

2. **Add a research task:**
   - Copy `tasks/_template.py` → `tasks/my-task.py`
   - Edit `get_research_prompt()` with your research
   - Copy `.github/workflows/_template-workflow.yml` → `.github/workflows/my-task.yml`
   - Replace `TASK_NAME` with `my-task` throughout the workflow
   - Set schedule (cron expression)
   - Commit and push

3. **Check results:** Look in `results/latest/` for recent findings, or `results/YYYY-MM/` for history

## How It Works

Each research task runs on its own schedule, uses Claude Agent SDK to search and analyze information, and writes findings to markdown files in `results/`. Only significant findings (alerts) are saved.

See [setup_guide.md](setup_guide.md) for detailed documentation and examples.
