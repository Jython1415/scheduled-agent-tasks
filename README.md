# Scheduled Agent Tasks

Template for running scheduled AI-powered research tasks using Claude Agent SDK in GitHub Actions.

## Quick Start

1. **Set up authentication:** Run `claude setup-token` locally, then add to GitHub Secrets:
   ```bash
   gh secret set CLAUDE_CODE_OAUTH_TOKEN
   ```

2. **Add a research task:**
   - Copy the template folder: `cp -r tasks/_template tasks/my-task`
   - Edit `get_research_prompt()` in `tasks/my-task/research.py`
   - Copy the workflow: `cp .github/workflows/_template.yml .github/workflows/my-task.yml`
   - Replace `TASK_NAME` with `my-task` in the workflow file
   - Set schedule (cron expression)
   - Commit and push

3. **Check results:** Look in `tasks/my-task/results/latest.md` for recent findings, or `tasks/my-task/results/YYYY-MM/` for history

## Structure

Each task is self-contained in its own folder with results stored alongside the code.

See [setup_guide.md](setup_guide.md) for detailed documentation and examples.
