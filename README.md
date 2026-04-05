# ThiemAICamp - AI Software Office v8.5

He thong AI agents tu dong phat trien phan mem. **Score: 8.5/10**

## Architecture

```
ThiemAICamp/
├── src/
│   ├── memory/          # ChromaDB semantic memory (patterns, bugs, ADRs)
│   ├── engine/          # Task Engine: Project > Milestone > Task > Subtask
│   ├── agents/          # Dev Team (4 agents) + Review Agent + QA Agent
│   ├── orchestrator/    # Main Pipeline: Plan > Approve > Dev > Review > QA
│   ├── execution/       # File I/O + Code Sandbox (Python/Node/Shell)
│   ├── integrations/    # Git Manager + Webhook Notifications
│   ├── monitoring/      # LangSmith Observability + SQLite metrics
│   ├── checkpoints/     # Human Approval System (async, persisted)
│   ├── persistence/     # SQLite database layer (thread-safe)
│   ├── templates/       # Project Templates: SaaS, CRUD, AI Tool
│   ├── cli.py           # Typer CLI interface
│   └── utils.py         # Retry decorators, error classes, logging
├── tests/               # 81 unit tests (pytest)
├── requirements.txt
└── CLAUDE.md
```

## Quick Start

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key

# CLI
python -m src.cli status
python -m src.cli templates
python -m src.cli memory-stats
python -m src.cli run-tests
```

## Modules

### 1. Memory System
ChromaDB-backed semantic search across 3 collections with dedup detection.

```python
from src.memory.chroma_store import MemoryStore
store = MemoryStore()
store.store_code_pattern("Retry", "Exponential backoff", "def retry(): ...")
store.store_bug_fix("NPE", "NullPointerError", "Missing check", "Added guard")
results = store.search_all("database connection")
```

### 2. Task Engine
Thread-safe hierarchy with priority-based assignment and cross-milestone dependencies.

```python
from src.engine.task_engine import TaskEngine, Priority
engine = TaskEngine()
project = engine.create_project("E-commerce")
m = project.add_milestone("MVP", deadline="2025-06-01")
t1 = m.add_task("Setup DB", priority=Priority.HIGH)
t2 = m.add_task("Build API", priority=Priority.CRITICAL)
t2.dependencies = [t1.id]
task = engine.get_next_task("api_agent")  # Gets t1 (t2 blocked)
```

### 3. Dev Team (4 Parallel Agents)
API, UI, Auth, DB agents with git worktree isolation.

```python
import asyncio
from src.agents.dev_team import DevTeam, AgentRole
team = DevTeam()
results = asyncio.run(team.assign_parallel({
    AgentRole.API: "Build user endpoints",
    AgentRole.DB: "Create user schema",
    AgentRole.AUTH: "Setup JWT",
    AgentRole.UI: "Build login page",
}))
```

### 4. Review Pipeline (Dev > Reviewer > QA)
Structured JSON output with severity levels and categories.

```python
from src.agents.reviewer import ReviewPipeline
pipeline = ReviewPipeline()
result = asyncio.run(pipeline.run(code, filename="api.py"))
# Returns: {"review": {..., "score": 8.5}, "qa": {"passed": true, "test_cases": [...]}}
```

### 5. Orchestrator (Full Pipeline)
Connects ALL modules: Memory > Plan > Approve > Dev > Review > QA.

```python
from src.orchestrator.pipeline import Pipeline
p = Pipeline(auto_approve=True)
run = asyncio.run(p.run_project("My App", "E-commerce platform", tasks=[
    {"title": "User API", "role": "api", "priority": "high"},
    {"title": "Auth system", "role": "auth", "priority": "critical"},
]))
print(run.results)
```

### 6. Code Execution Sandbox
Safe subprocess execution with timeout and blocked command detection.

```python
from src.execution.sandbox import Sandbox
sandbox = Sandbox(timeout=30)
result = sandbox.run_python("print(sum(range(100)))")
assert result.success and "4950" in result.stdout
```

### 7. File Operations
Safe file I/O with path validation, backup/restore, and diff generation.

```python
from src.execution.file_ops import FileOperations
fops = FileOperations("./workspace")
fops.write_file("api/users.py", code)
fops.edit_file("api/users.py", "old_func", "new_func")
fops.restore_backup("api/users.py")  # Undo
```

### 8. Git Manager
Auto-commit from agent output with branch management.

```python
from src.integrations.git_manager import GitManager
git = GitManager(".")
git.auto_commit(["api.py"], "api_agent", "Build user endpoints")
git.create_branch("feature/auth")
git.push()
```

### 9. Notifications
Multi-channel: console, webhook (Slack/Discord), file log.

```python
from src.integrations.notifier import Notifier
n = Notifier(webhook_url="https://hooks.slack.com/...")
n.pipeline_started("MyProject", 5)
n.approval_needed("ap_001", "Deploy v2")
n.review_result("api.py", 8.5, True)
```

### 10. Human Approval
Async approval with timeout, persisted to SQLite.

```python
from src.checkpoints.human_approval import HumanApprovalSystem, CheckpointType
approval = HumanApprovalSystem()
req = approval.create_checkpoint(CheckpointType.DEPLOY_APPROVAL, "Deploy v2", "Details...")
approval.approve(req.id, "LGTM!")
```

### 11. Observability
LangSmith integration + SQLite persistence for metrics.

```python
from src.monitoring.langsmith_logger import LangSmithLogger
logger = LangSmithLogger(api_key="ls_...")
metrics = logger.start_tracking("api_agent", "task_001")
logger.end_tracking(metrics, input_tokens=500, output_tokens=200)
print(logger.get_summary())
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `status` | System overview |
| `memory-search <query>` | Search memory store |
| `memory-stats` | Memory statistics |
| `project-create <name>` | Create new project |
| `project-status <id>` | Project progress |
| `approvals` | List pending approvals |
| `approve <id>` | Approve a request |
| `reject <id>` | Reject a request |
| `run-code <code>` | Run code in sandbox |
| `run-tests` | Run pytest |
| `templates` | List templates |
| `scaffold <template> <dir>` | Create project from template |
| `metrics` | System metrics |

## Tests

```bash
python -m pytest tests/ -v
# 81 tests covering: persistence, task_engine, memory, approval, execution, integrations
```

## What's New in v8.5

| Feature | Before (v1) | After (v8.5) |
|---------|------------|--------------|
| Persistence | In-memory only | SQLite (thread-safe) |
| Error Handling | None | Retry decorators, graceful degradation |
| Orchestrator | Modules standalone | Full pipeline connecting all 7 modules |
| Code Execution | Agents return text only | Real file I/O + subprocess sandbox |
| Git Integration | Worktree concept only | Auto-commit, branch, merge, push |
| Notifications | print() only | Console + Webhook + File log |
| Tests | None | 81 unit tests |
| CLI | None | 14 Typer commands |
| Thread Safety | None | RLock on task engine, thread-local DB |
| LangSmith | Env vars only | Real trace sending |

## Tech Stack

- **Memory**: ChromaDB
- **LLM**: Anthropic Claude (langchain-anthropic)
- **Observability**: LangSmith
- **Persistence**: SQLite
- **CLI**: Typer + Rich
- **Testing**: pytest
- **Language**: Python 3.10+
