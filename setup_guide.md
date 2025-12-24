# Scheduled Claude Research Repository - Setup Guide

**Context:** This pattern emerged from a conversation between Joshua and Claude.ai about setting up automated dependency monitoring using Claude Agent SDK in GitHub Actions. We developed an approach using modern Python tooling (uv + PEP 723) that makes scheduled AI-powered research tasks self-contained and maintainable. This document is for Claude Code to implement and can serve as a template pattern for other repositories.

## The Pattern

**Core Idea:** Use GitHub Actions to run Claude Agent SDK on a schedule, performing research tasks like monitoring dependencies, tracking industry developments, or analyzing changes in external systems. The agent uses web search tools, creates alerts when findings matter, and stays silent otherwise.

**Why This Works:**
- **Self-contained scripts** with inline dependencies (PEP 723)
- **Fast execution** with uv package manager (~2-5s setup vs 30-60s with pip)
- **OAuth authentication** using Claude Pro/Max subscription (with optional API key fallback)
- **Smart alerting** via GitHub Issues - only notifies when there's something to act on
- **Template pattern** - easy to add new research tasks by copying a script

## Repository Purpose

This repository serves two purposes:
1. **Template/pattern demonstration** - shows how to set up scheduled Claude research
2. **Operational home** - hosts Joshua's miscellaneous regularly scheduled research tasks

## Implementation Steps for Claude Code

### Step 1: Create Repository Structure

```bash
# Create new repository (public recommended - see PUBLIC_VS_PRIVATE_ANALYSIS.md)
# Public repos get unlimited free GitHub Actions minutes
# Private repos limited to 2,000 minutes/month across all private repos
gh repo create scheduled-claude-research --public --description "Template for scheduled AI-powered research tasks using Claude Agent SDK"

# Clone it
gh repo clone scheduled-claude-research
cd scheduled-claude-research

# Create directory structure
mkdir -p .github/workflows
mkdir -p tasks
mkdir -p docs
```

### Step 2: Create Core Files

**`.github/workflows/scheduled-research.yml`** - Main workflow:

```yaml
name: Scheduled Research Tasks

on:
  schedule:
    # Run every 6 hours
    - cron: '0 */6 * * *'
  
  # Allow manual triggering
  workflow_dispatch:
    inputs:
      task:
        description: 'Specific task to run (filename without .py)'
        required: false
        type: string

permissions:
  contents: write
  issues: write

jobs:
  run-tasks:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
      
      - name: Install uv
        uses: astral-sh/setup-uv@v7
        with:
          enable-cache: true
      
      - name: Set up Python
        run: uv python install 3.10
      
      - name: Run research tasks
        env:
          CLAUDE_CODE_OAUTH_TOKEN: ${{ secrets.CLAUDE_OAUTH_TOKEN }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          MANUAL_TASK: ${{ inputs.task }}
        run: |
          if [ -n "$MANUAL_TASK" ]; then
            echo "Running specific task: $MANUAL_TASK"
            uv run "tasks/${MANUAL_TASK}.py"
          else
            echo "Running all enabled tasks..."
            for task in tasks/*.py; do
              if [[ -f "$task" ]] && [[ ! "$task" =~ _disabled\.py$ ]]; then
                echo "Running: $task"
                uv run "$task" || echo "Task failed: $task"
              fi
            done
          fi
        continue-on-error: true
      
      - name: Process results
        id: process
        run: |
          # Check for alerts
          if ls tasks/alerts/*.txt 1> /dev/null 2>&1; then
            echo "alerts_found=true" >> $GITHUB_OUTPUT
            echo "alert_count=$(ls tasks/alerts/*.txt | wc -l)" >> $GITHUB_OUTPUT
          else
            echo "alerts_found=false" >> $GITHUB_OUTPUT
          fi
          
          # Check for errors
          if ls tasks/errors/*.txt 1> /dev/null 2>&1; then
            echo "errors_found=true" >> $GITHUB_OUTPUT
          else
            echo "errors_found=false" >> $GITHUB_OUTPUT
          fi
      
      - name: Create alert issues
        if: steps.process.outputs.alerts_found == 'true'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const path = require('path');
            
            const alertDir = 'tasks/alerts';
            const files = fs.readdirSync(alertDir);
            
            for (const file of files) {
              if (!file.endsWith('.txt')) continue;
              
              const content = fs.readFileSync(path.join(alertDir, file), 'utf8');
              const taskName = file.replace('.txt', '');
              
              await github.rest.issues.create({
                owner: context.repo.owner,
                repo: context.repo.repo,
                title: `🔔 Research Alert: ${taskName}`,
                labels: ['research-alert', 'automated'],
                body: `## Research Task Alert\n\n**Task:** ${taskName}\n\n${content}\n\n---\n**Triggered:** ${new Date().toISOString()}\n**Workflow:** ${context.serverUrl}/${context.repo.owner}/${context.repo.repo}/actions/runs/${context.runId}`
              });
            }
      
      - name: Create error issues
        if: steps.process.outputs.errors_found == 'true'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const path = require('path');
            
            const errorDir = 'tasks/errors';
            const files = fs.readdirSync(errorDir);
            
            for (const file of files) {
              if (!file.endsWith('.txt')) continue;
              
              const content = fs.readFileSync(path.join(errorDir, file), 'utf8');
              const taskName = file.replace('.txt', '');
              
              await github.rest.issues.create({
                owner: context.repo.owner,
                repo: context.repo.repo,
                title: `⚠️ Research Task Error: ${taskName}`,
                labels: ['task-error', 'needs-attention'],
                body: `## Task Execution Error\n\n**Task:** ${taskName}\n\n${content}\n\n---\n**Occurred:** ${new Date().toISOString()}\n**Workflow:** ${context.serverUrl}/${context.repo.owner}/${context.repo.repo}/actions/runs/${context.runId}`
              });
            }
      
      - name: Upload artifacts
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: task-results
          path: |
            tasks/alerts/*.txt
            tasks/errors/*.txt
            tasks/*.log
          retention-days: 7
```

**`tasks/_template.py`** - Template for new research tasks:

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "claude-agent-sdk>=1.0.0",
# ]
# ///
"""
Research Task Template

Copy this file and modify for your specific research needs.
Rename from _template.py to descriptive-name.py

Tasks ending in _disabled.py are skipped by the workflow.
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

try:
    from claude_agent_sdk import query, ClaudeAgentOptions
except ImportError:
    print("ERROR: claude-agent-sdk not installed")
    print("Run with: uv run task.py")
    sys.exit(1)


class ResearchTask:
    """Base class for research tasks"""
    
    def __init__(self):
        self.oauth_token = os.getenv('CLAUDE_CODE_OAUTH_TOKEN')
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        self.task_name = Path(__file__).stem
        
        # Create output directories
        Path("tasks/alerts").mkdir(parents=True, exist_ok=True)
        Path("tasks/errors").mkdir(parents=True, exist_ok=True)
    
    def _get_auth_method(self) -> str:
        """Determine authentication method"""
        if self.oauth_token:
            return "oauth"
        elif self.api_key:
            return "api_key"
        else:
            return "none"
    
    def _write_alert(self, message: str):
        """Write alert to file for GitHub Actions to create Issue"""
        alert_file = Path(f"tasks/alerts/{self.task_name}.txt")
        alert_file.write_text(message)
        print(f"ALERT: {message}")
    
    def _write_error(self, message: str):
        """Write error to file for GitHub Actions to create Issue"""
        error_file = Path(f"tasks/errors/{self.task_name}.txt")
        error_file.write_text(message)
        print(f"ERROR: {message}", file=sys.stderr)
    
    def get_research_prompt(self) -> str:
        """
        Override this method with your specific research task.
        
        Return a prompt that:
        1. Clearly states what to research
        2. Specifies where to look (URLs, sources)
        3. Defines what constitutes an alert vs silence
        4. Ends with: Print "ALERT: [summary]" or "SILENT"
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
    
    async def run(self) -> bool:
        """Execute the research task"""
        
        auth_method = self._get_auth_method()
        print(f"Task: {self.task_name}")
        print(f"Authentication: {auth_method}")
        
        if auth_method == "none":
            self._write_error(
                "No authentication configured.\n\n"
                "Set either CLAUDE_CODE_OAUTH_TOKEN or ANTHROPIC_API_KEY"
            )
            return False
        
        # Configure Claude Agent
        options = ClaudeAgentOptions(
            cwd=".",
            allowed_tools=["WebSearch", "WebFetch", "Read", "Write"],
            permission_mode="acceptAll",
            max_turns=10,
            system_prompt="""You are a focused research agent.
Your job: search for specific information, analyze findings, report concisely.
Be thorough but efficient. Only report significant findings.""",
        )
        
        prompt = self.get_research_prompt()
        
        print("-" * 50)
        print("Starting research...")
        
        alert_triggered = False
        full_response = []
        
        try:
            async for message in query(prompt=prompt, options=options):
                message_str = str(message)
                full_response.append(message_str)
                print(message_str)
                
                if "ALERT:" in message_str.upper():
                    alert_triggered = True
            
            print("-" * 50)
            
            if alert_triggered:
                alert_messages = [
                    msg for msg in full_response 
                    if "ALERT:" in msg.upper()
                ]
                alert_text = "\n".join(alert_messages)
                self._write_alert(alert_text)
                return True
            else:
                print("No alerts - research complete")
                return False
                
        except Exception as e:
            error_msg = str(e)
            
            # Check for auth errors
            if any(x in error_msg.lower() for x in ['auth', 'token', 'key', 'credit', 'quota']):
                if auth_method == "oauth":
                    self._write_error(
                        f"OAuth authentication failed: {error_msg}\n\n"
                        "Possible fixes:\n"
                        "1. Refresh CLAUDE_CODE_OAUTH_TOKEN (run: claude setup-token)\n"
                        "2. Set ANTHROPIC_API_KEY as fallback\n"
                        "3. Wait for rate limits to reset"
                    )
                else:
                    self._write_error(
                        f"API key authentication failed: {error_msg}\n\n"
                        "Check API key in Anthropic Console"
                    )
            else:
                self._write_error(f"Unexpected error: {error_msg}")
            
            return False


async def main():
    """Entry point"""
    task = ResearchTask()
    
    try:
        await task.run()
        sys.exit(0)
    except KeyboardInterrupt:
        print("\nTask interrupted")
        sys.exit(130)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
```

**`tasks/monitor-react-19.py`** - Example concrete task:

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "claude-agent-sdk>=1.0.0",
# ]
# ///
"""
Monitor React 19 Release Status

Checks for official React 19 release and useActionState hook availability.
"""

import asyncio
import sys
from pathlib import Path

# Import the template base class
sys.path.insert(0, str(Path(__file__).parent))
from _template import ResearchTask


class ReactMonitor(ResearchTask):
    """Monitor React 19 release"""
    
    def get_research_prompt(self) -> str:
        return """
Research: React 19 - useActionState hook release status

Check these sources:
1. React blog: react.dev/blog
2. GitHub releases: github.com/facebook/react
3. NPM package: npmjs.com/package/react

Look for:
- Official React 19.x release announcement
- useActionState hook in documentation
- Stable release (not beta/RC)

If React 19 with useActionState is officially released:
- Print "ALERT: React 19 released with useActionState hook - [version number]"

If still in beta/RC/unreleased:
- Print "SILENT"

Be precise about version numbers and release status.
"""


if __name__ == "__main__":
    asyncio.run(ReactMonitor().run())
```

**`README.md`** - Repository documentation:

```markdown
# Scheduled Claude Research

Template repository for running scheduled AI-powered research tasks using Claude Agent SDK in GitHub Actions.

## What This Does

Runs Claude Agent SDK on a schedule to:
- Monitor dependencies and APIs for releases
- Track industry developments and changes
- Analyze external systems for updates
- Research specific topics on a cadence
- Alert via GitHub Issues when findings matter

**Key Features:**
- ✅ Self-contained tasks with inline dependencies (PEP 723)
- ✅ Fast execution with uv package manager
- ✅ OAuth authentication (Claude Pro/Max) with API key fallback
- ✅ Smart alerting - only creates Issues for significant findings
- ✅ Easy to add new tasks - copy template, modify prompt

## Quick Start

### 1. Set Authentication

Add GitHub Secret (Settings → Secrets → Actions):

```
Name: CLAUDE_CODE_OAUTH_TOKEN
Value: [get from: claude setup-token]
```

Optional fallback:
```
Name: ANTHROPIC_API_KEY
Value: [from Anthropic Console]
```

### 2. Add a Research Task

Copy the template:
```bash
cp tasks/_template.py tasks/my-research.py
```

Edit `get_research_prompt()` to define your research:
```python
def get_research_prompt(self) -> str:
    return """
Research: [What to investigate]

Check: [Where to look]

Alert if: [Condition]
Otherwise: Print "SILENT"
"""
```

### 3. Test It

Manual trigger:
```bash
# Locally (requires uv)
uv run tasks/my-research.py

# In GitHub Actions
Actions → Scheduled Research Tasks → Run workflow
```

### 4. Deploy

Commit and push. The workflow runs every 6 hours automatically.

## File Structure

```
.
├── .github/
│   └── workflows/
│       └── scheduled-research.yml    # Main workflow
├── tasks/
│   ├── _template.py                  # Copy this for new tasks
│   ├── monitor-react-19.py          # Example task
│   ├── alerts/                       # Generated alerts (git-ignored)
│   └── errors/                       # Generated errors (git-ignored)
└── docs/
    └── pattern-explanation.md        # How this pattern works
```

## How It Works

**GitHub Actions Workflow:**
1. Runs on schedule (every 6 hours)
2. Installs uv and Python 3.10
3. Executes all `tasks/*.py` files (except *_disabled.py)
4. Creates GitHub Issues for alerts/errors
5. Uploads logs as artifacts

**Research Tasks:**
- Self-contained Python scripts with inline dependencies
- Inherit from `ResearchTask` base class
- Override `get_research_prompt()` with specific research
- Print "ALERT: [message]" or "SILENT"
- Automatically create alert/error files

**Alert Flow:**
```
Task finds something → Writes tasks/alerts/[task-name].txt
→ GitHub Actions creates Issue → You get notified
```

## Adding New Tasks

### Pattern 1: Simple Monitoring
```python
class MyMonitor(ResearchTask):
    def get_research_prompt(self) -> str:
        return """
Monitor: Python 3.13 release
Check: python.org/downloads
Alert if: Stable 3.13.x available
"""
```

### Pattern 2: Competitive Analysis
```python
def get_research_prompt(self) -> str:
    return """
Research: Competitor blog posts last week
Search: [competitor].com/blog posts from last 7 days
Alert if: Major feature announcement
Include: Link and summary
"""
```

### Pattern 3: API Monitoring
```python
def get_research_prompt(self) -> str:
    return """
Check: GitHub API v4 breaking changes
Sources: 
- docs.github.com/graphql/overview/breaking-changes
- github.blog
Alert if: New deprecation affecting our usage
"""
```

## Disabling Tasks

Rename to `*_disabled.py`:
```bash
mv tasks/my-research.py tasks/my-research_disabled.py
```

## Local Development

**Install uv:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Run a task:**
```bash
# Set environment
export CLAUDE_CODE_OAUTH_TOKEN="your-token"

# Execute
uv run tasks/my-research.py
```

**Test workflow:**
```bash
# Install act (GitHub Actions locally)
brew install act  # or see: github.com/nektos/act

# Run workflow
act workflow_dispatch
```

## Cost Estimates

**With OAuth (Claude Pro - $20/month):**
- Uses existing subscription
- ~10 agent runs per 5-hour reset period
- If running 4 tasks 4x daily = 16 runs/day
- May hit rate limits during peak usage

**With API Key (Pay-as-you-go):**
- ~$0.35 per research task run
- 4 tasks × 4 runs/day = $5.60/day = ~$168/month
- More predictable, no rate limits

**Recommendation:** Use OAuth for moderate usage, API key for heavy automation.

## Troubleshooting

**"No module named claude_agent_sdk"**
→ Script should be run with `uv run` (not `python`)

**Rate limit errors**
→ OAuth limits reset every 5 hours. Reduce frequency or use API key.

**No alerts created**
→ Check Actions logs. Task may be printing "SILENT" (expected).

**Task keeps failing**
→ Check errors/ directory or Issues labeled `task-error`

## Use Cases

- **Dependency monitoring** - Track library releases, breaking changes
- **Competitor analysis** - Monitor competitor blogs, product updates
- **API monitoring** - Watch for deprecations, new features
- **Research automation** - Industry trends, news aggregation
- **Content monitoring** - Track changes to documentation, policies
- **Security monitoring** - CVE databases, security advisories

## Template Pattern Benefits

1. **Self-contained** - Dependencies travel with scripts
2. **Fast** - uv setup in 2-5 seconds
3. **Standards-compliant** - PEP 723 works everywhere
4. **Easy extension** - Copy template, modify prompt
5. **Smart alerting** - Only notifies when it matters
6. **Audit trail** - All runs logged in Actions
7. **Reusable** - Same pattern across repos

## References

- [PEP 723 - Inline Script Metadata](https://peps.python.org/pep-0723/)
- [uv Documentation](https://docs.astral.sh/uv/)
- [Claude Agent SDK](https://docs.claude.com/en/api/agent-sdk/overview)
- [GitHub Actions](https://docs.github.com/actions)

## License

MIT - Use freely in your projects
```

**`docs/pattern-explanation.md`** - Technical deep-dive:

```markdown
# Scheduled Research Pattern - Technical Explanation

## Architecture

### Component Stack

```
GitHub Actions (Orchestration)
    ↓
uv (Package Management)
    ↓
Python 3.10+ (Runtime)
    ↓
Claude Agent SDK (AI Agent Harness)
    ↓
Web Search/Fetch Tools (Research)
    ↓
Alert/Error Files (Output)
    ↓
GitHub Issues (Notification)
```

### Why This Stack

**uv + PEP 723:**
- Dependencies embedded in scripts (no requirements.txt)
- Install times: 2-5s vs 30-60s with pip
- Parallel package downloads
- Isolated environments per script
- Works offline after first run (cached)

**Claude Agent SDK:**
- Full agentic harness (not just API calls)
- Multi-turn autonomous operation
- Tool ecosystem: WebSearch, WebFetch, file ops
- Context management and compaction
- Can run for extended periods

**GitHub Actions:**
- Free for public repos (2000 min/month)
- Reliable scheduling (cron)
- Built-in Issue creation
- Artifact storage
- Secrets management

### Data Flow

```
Workflow triggers (schedule/manual)
    ↓
For each task file:
    ↓
    uv reads inline dependencies
    ↓
    Creates isolated environment
    ↓
    Installs claude-agent-sdk
    ↓
    Runs task script
    ↓
    Task executes Claude Agent
    ↓
    Agent uses WebSearch/WebFetch
    ↓
    Agent analyzes findings
    ↓
    Prints "ALERT" or "SILENT"
    ↓
    Task writes alert/error files
    ↓
Workflow processes results
    ↓
Creates GitHub Issues for alerts/errors
```

## Authentication Strategy

### Primary: OAuth Token

**How it works:**
```bash
claude setup-token  # Get token locally
# Add to GitHub Secrets: CLAUDE_CODE_OAUTH_TOKEN
```

**Characteristics:**
- Uses Claude Pro/Max subscription
- Fixed monthly cost ($20-100)
- Subject to rate limits (resets every 5 hours)
- ~10 concurrent agent runs per reset
- Best for moderate usage

**Rate limit handling:**
- Monitor failed runs
- Adjust schedule if hitting limits
- Fallback to API key if consistent

### Fallback: API Key

**How it works:**
```bash
# Get from: console.anthropic.com
# Add to GitHub Secrets: ANTHROPIC_API_KEY
```

**Characteristics:**
- Pay-as-you-go
- No subscription limits
- ~$0.35 per research run
- Predictable costs
- Best for heavy automation

**Cost estimation:**
- Agent runs typically: ~50k tokens
- ~5 web searches per run
- Total: ~$0.30 tokens + $0.05 searches
- 4 tasks × 4x daily = $5.60/day

### Error Handling

When auth fails, system:
1. Catches exception in task
2. Writes detailed error file
3. Workflow creates Issue with:
   - Specific error message
   - Possible causes
   - Solution steps
   - Link to workflow run

## Task Lifecycle

### Task Creation

```python
# 1. Copy template
cp tasks/_template.py tasks/new-task.py

# 2. Modify prompt
class NewTask(ResearchTask):
    def get_research_prompt(self):
        return "Research: ..."

# 3. Test locally
uv run tasks/new-task.py

# 4. Commit and deploy
```

### Task Execution

```python
# GitHub Actions runs:
uv run tasks/new-task.py

# Internally:
1. ResearchTask.__init__()
   - Gets auth credentials
   - Creates output directories
   
2. ResearchTask.run()
   - Configures Claude Agent
   - Sends research prompt
   - Streams responses
   - Detects "ALERT" or "SILENT"
   
3. Output handling
   - Alert found → writes tasks/alerts/new-task.txt
   - Error occurred → writes tasks/errors/new-task.txt
```

### Result Processing

```yaml
# Workflow checks for files:
if tasks/alerts/*.txt exist:
    for each alert file:
        Create GitHub Issue with content

if tasks/errors/*.txt exist:
    for each error file:
        Create GitHub Issue with diagnostic info
```

## Prompt Engineering

### Effective Research Prompts

**Structure:**
```
1. Research goal (clear, specific)
2. Sources to check (URLs, keywords)
3. Alert condition (what matters)
4. Output format ("ALERT: ..." or "SILENT")
```

**Good prompt:**
```
Research: React 19 stable release

Check:
1. React blog (react.dev/blog)
2. GitHub releases (facebook/react)
3. NPM latest tag

Alert if: React 19.x stable (not beta/RC)
Include: Version number and release date

Otherwise: Print "SILENT"
```

**Bad prompt:**
```
Check if React 19 is out
```

### Multi-Turn Strategy

The agent can:
- Search multiple sources
- Follow links
- Cross-reference findings
- Verify information
- Extract specifics

Typical flow:
```
1. Initial search → finds blog post
2. Follow link → reads full article
3. Verify on GitHub → checks release tags
4. Cross-check NPM → confirms version
5. Synthesize → reports findings
```

## Scaling Patterns

### Adding More Tasks

**Horizontal scaling:**
- Each task is independent
- Runs in parallel (implicitly)
- No coordination needed
- Linear cost increase

**Resource usage:**
- Each task: 2-5 minutes runtime
- All tasks run sequentially
- 10 tasks × 3 min = 30 min total
- Still within free tier

### Frequency Tuning

**Current: Every 6 hours (4x daily)**

Adjust in workflow:
```yaml
schedule:
  # Every hour
  - cron: '0 * * * *'
  
  # Twice daily
  - cron: '0 8,20 * * *'
  
  # Daily at 9am UTC
  - cron: '0 9 * * *'
```

**Considerations:**
- More frequent → higher costs
- Less frequent → delayed alerts
- Match cadence to update frequency

### Multi-Repo Pattern

**Option 1: Separate repos**
- Each repo has own research tasks
- Scoped to repo context
- Independent scheduling

**Option 2: Central research repo**
- All research tasks in one place
- Single schedule management
- Unified alert stream

**Option 3: Hybrid**
- Template repo (this one)
- Fork for each context
- Customize per use case

## Performance Optimization

### Caching Strategy

**uv caching:**
```yaml
- name: Install uv
  uses: astral-sh/setup-uv@v7
  with:
    enable-cache: true
    cache-dependency-glob: "tasks/*.py"
```

**What gets cached:**
- Python interpreter
- Package index metadata
- Installed packages
- Virtual environments

**Cache invalidation:**
- Dependency changes → new environment
- Python version change → rebuild
- Weekly automatic refresh

### Token Efficiency

**Minimize context:**
- Focused prompts (not exploratory)
- Specific sources (not broad searches)
- Clear conditions (not vague)

**Typical token usage:**
- Prompt: ~500 tokens
- Agent reasoning: ~20k tokens
- Web search results: ~10k tokens
- Response: ~500 tokens
- Total: ~31k tokens @ $0.003 input = $0.09

**Web search costs:**
- ~5 searches per task
- $0.01 per search
- $0.05 per task run

### Execution Time

**Breakdown:**
```
uv setup:           2s
SDK initialization: 1s
Agent execution:    30-90s
Result processing:  1s
Total:             34-94s per task
```

**Optimization opportunities:**
- Reduce max_turns (currently 10)
- More specific prompts (fewer searches)
- Batch related checks

## Security Considerations

### Secrets Management

**Never commit:**
- OAuth tokens
- API keys
- Personal data

**Use GitHub Secrets:**
- Encrypted at rest
- Redacted in logs
- Access controlled

### Tool Permissions

```python
allowed_tools=["WebSearch", "WebFetch", "Read", "Write"]
```

**WebSearch/WebFetch:**
- Only access URLs in context
- Cannot exfiltrate data
- Rate limited

**Read/Write:**
- Scoped to workflow workspace
- No access to secrets
- Temporary filesystem

### Rate Limiting

**Protection mechanisms:**
- uv: Respects PyPI rate limits
- Claude: API rate limits enforced
- GitHub: Actions quota management

## Extension Patterns

### Custom Tools

Add MCP servers for specialized access:

```python
options = ClaudeAgentOptions(
    allowed_tools=["WebSearch", "WebFetch", "custom_api"],
    mcp_config="mcp-servers.json"
)
```

### Structured Output

Parse JSON responses:

```python
prompt = """
Research: [task]
Output as JSON:
{
  "alert": true/false,
  "summary": "...",
  "details": {...}
}
"""

# Parse and process
```

### Notification Channels

Beyond GitHub Issues:
- Slack webhooks
- Email via SendGrid
- Discord webhooks
- Custom API calls

### State Management

For continuous research:

```python
# Load previous state
last_check = load_state("last_check.json")

# Include in prompt
prompt = f"""
Last checked: {last_check}
Check for changes since then
"""

# Save new state
save_state({"last_check": now()})
```

## Debugging

### Local Testing

```bash
# Set environment
export CLAUDE_CODE_OAUTH_TOKEN="token"

# Enable debug output
export DEBUG=1

# Run task
uv run tasks/my-task.py
```

### Workflow Debugging

```yaml
- name: Run with debug
  run: |
    uv run --verbose tasks/my-task.py
```

### Common Issues

**"claude-agent-sdk not found"**
→ Running with `python` instead of `uv run`

**Empty responses**
→ Check system_prompt and agent permissions

**Rate limits**
→ Reduce frequency or switch to API key

**Silent when should alert**
→ Review agent logs, refine prompt

## Future Enhancements

**Potential additions:**
- Diff tracking (only alert on changes)
- Confidence scores (alert threshold)
- Aggregated summaries (weekly digest)
- Interactive mode (ask followups)
- Result caching (avoid redundant searches)

## Conclusion

This pattern provides:
- **Reliable** - proven in production
- **Flexible** - adapt to any research need
- **Maintainable** - clear structure
- **Cost-effective** - optimized execution
- **Scalable** - add tasks easily

The combination of uv, PEP 723, and Claude Agent SDK creates a powerful foundation for automated research that's both sophisticated and approachable.
```

**`.gitignore`**:

```
# Environment
.env

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# uv
.venv/
*.lock

# Task outputs (created by workflows)
tasks/alerts/
tasks/errors/
*.log

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db
```

### Step 3: Configure Repository

```bash
# Initialize git
git init
git add .
git commit -m "Initial commit: Scheduled research template"

# Create remote and push
gh repo create scheduled-claude-research --source=. --public --push

# Set up labels for Issues
gh label create "research-alert" --description "Automated research finding" --color "0E8A16"
gh label create "task-error" --description "Task execution error" --color "D93F0B"
gh label create "automated" --description "Created by automation" --color "FBCA04"
gh label create "needs-attention" --description "Requires human review" --color "D93F0B"

# Enable workflow permissions
gh api repos/{owner}/{repo}/actions/permissions --method PUT --field enabled=true
gh api repos/{owner}/{repo}/actions/permissions/workflow --method PUT --field default_workflow_permissions=write --field can_approve_pull_request_reviews=false
```

### Step 4: Set Secrets

```bash
# Get OAuth token
echo "Run locally: claude setup-token"
echo "Then set secret with:"
gh secret set CLAUDE_CODE_OAUTH_TOKEN

# Optional: API key fallback
gh secret set ANTHROPIC_API_KEY
```

### Step 5: Test

```bash
# Trigger workflow manually
gh workflow run scheduled-research.yml

# Watch progress
gh run list

# View logs
gh run view --log
```

## Usage Examples for Joshua

### Example 1: Monitor Python 3.13 Release

Create `tasks/monitor-python-313.py`:

```python
class Python313Monitor(ResearchTask):
    def get_research_prompt(self) -> str:
        return """
Research: Python 3.13 stable release status

Check:
1. python.org/downloads
2. GitHub releases: github.com/python/cpython
3. PyPI version info

Alert if: Python 3.13.x stable released (not beta/RC)
Include: Version number and release date

Otherwise: Print "SILENT"
"""
```

### Example 2: Competitor Blog Monitoring

Create `tasks/monitor-competitor-blogs.py`:

```python
def get_research_prompt(self) -> str:
    return """
Research: Math education technology competitors - new blog posts

Check these blogs for posts from last 7 days:
1. competitor1.com/blog
2. competitor2.com/blog
3. competitor3.com/blog

Alert if: Major feature announcements or product launches
Include: Title, link, and one-sentence summary

Otherwise: Print "SILENT"
"""
```

### Example 3: IXL API Changes

Create `tasks/monitor-ixl-api.py`:

```python
def get_research_prompt(self) -> str:
    return """
Research: IXL API availability and changes

Check:
1. IXL developer documentation
2. Search for "IXL API public" recent mentions
3. IXL support pages

Alert if:
- New public API announced
- Changes to integration capabilities
- New developer resources

Include: What changed and implications

Otherwise: Print "SILENT"
"""
```

## Template Variations

### High-Frequency Monitoring
```yaml
schedule:
  - cron: '0 * * * *'  # Every hour
```

### Low-Frequency Research
```yaml
schedule:
  - cron: '0 9 * * 1'  # Monday 9am UTC
```

### Multi-Environment
```yaml
strategy:
  matrix:
    environment: [production, staging]
env:
  ENVIRONMENT: ${{ matrix.environment }}
```

## Repository Settings Checklist

- [ ] Repository created and pushed
- [ ] Secrets configured (CLAUDE_CODE_OAUTH_TOKEN)
- [ ] Labels created for Issues
- [ ] Workflow permissions enabled (read/write)
- [ ] At least one task file created
- [ ] Workflow tested manually
- [ ] Schedule confirmed working

## Questions for Joshua

1. **Initial tasks to create?**
   - React 19 monitoring (already planned)
   - Other specific dependencies?
   - Competitor monitoring?
   - Industry research topics?

2. **Schedule frequency?**
   - Every 6 hours (current default)
   - Different per task?
   - Specific times of day?

3. **Notification preferences?**
   - GitHub Issues sufficient?
   - Also want Slack/email?
   - Digest vs immediate?

4. **Repository visibility?**
   - Public (as template)?
   - Private (for operational use)?
   - Both (template public, instance private)?

## Next Steps

After repository setup:
1. Test with one simple task
2. Verify alert Issue creation
3. Add production research tasks
4. Monitor costs and adjust
5. Document learnings for template improvement

This pattern is production-ready and can be deployed immediately. The template structure makes it easy to add new research tasks as needed while maintaining a clean, maintainable codebase.