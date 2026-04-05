# ThiemAICamp - AI Software Office

Hệ thống AI agents tự động phát triển phần mềm, phiên bản **8.5/10**.

## Kiến trúc

```
ThiemAICamp/
├── src/
│   ├── memory/          # Upgrade 1 - ChromaDB Memory System
│   ├── engine/          # Upgrade 2 - Task Engine (Project > Milestone > Task > Subtask)
│   ├── agents/          # Upgrade 3 & 4 - Dev Team + Reviewer Agent
│   ├── monitoring/      # Upgrade 5 - LangSmith Observability
│   ├── checkpoints/     # Upgrade 6 - Human Approval Checkpoints
│   └── templates/       # Upgrade 7 - Project Templates (SaaS, CRUD, AI Tool)
├── requirements.txt
└── CLAUDE.md
```

## Cài đặt

```bash
pip install -r requirements.txt
```

Cần thiết lập API keys:
```bash
export ANTHROPIC_API_KEY=your_key
export LANGSMITH_API_KEY=your_key     # optional, cho observability
```

## Hướng dẫn sử dụng

### 1. Memory System (`src/memory/chroma_store.py`)

Lưu trữ và tìm kiếm code patterns, bugs đã fix, architecture decisions.

```python
from src.memory.chroma_store import MemoryStore

store = MemoryStore()

# Lưu code pattern
store.store_code_pattern("Singleton", "Thread-safe singleton", "class Singleton: ...")

# Lưu bug fix
store.store_bug_fix("NPE on login", "NullPointerError", "Missing null check", "Added guard clause")

# Lưu architecture decision
store.store_architecture_decision("Use PostgreSQL", "Need ACID", "PostgreSQL for main DB", "Better for relational data")

# Tìm kiếm
results = store.search("database connection pooling")
all_results = store.search_all("authentication pattern")
```

### 2. Task Engine (`src/engine/task_engine.py`)

Quản lý hierarchy: Project > Milestones > Tasks > Subtasks. Mỗi agent chỉ nhận 1 task.

```python
from src.engine.task_engine import TaskEngine, Priority

engine = TaskEngine()

# Tạo project
project = engine.create_project("E-commerce App")

# Thêm milestone
m1 = project.add_milestone("MVP", deadline="2025-03-01")

# Thêm tasks
t1 = m1.add_task("Setup database schema", priority=Priority.HIGH)
t2 = m1.add_task("Build auth API", priority=Priority.HIGH)
t2.dependencies = [t1.id]  # t2 phụ thuộc t1

# Agent lấy task
task = engine.get_next_task("api_agent")  # Trả về t1 (priority cao, không có dependency)

# Hoàn thành task
engine.complete_task(task.id)

# Xem tiến độ
summary = engine.get_project_summary(project.id)
```

### 3. Multi-Dev Parallel (`src/agents/dev_team.py`)

4 specialized agents chạy song song: API, UI, Auth, DB.

```python
import asyncio
from src.agents.dev_team import DevTeam, AgentRole

team = DevTeam()

# Giao task cho từng agent
result = asyncio.run(team.assign_task(AgentRole.API, "Build REST API for users"))

# Giao nhiều tasks song song
results = asyncio.run(team.assign_parallel({
    AgentRole.API: "Build user endpoints",
    AgentRole.DB: "Create user schema",
    AgentRole.AUTH: "Setup JWT authentication",
    AgentRole.UI: "Build login page",
}))

# Git worktree cho mỗi agent
worktrees = team.setup_worktrees()

# Xem trạng thái team
status = team.team_status()
```

### 4. Review Agent (`src/agents/reviewer.py`)

Pipeline: Dev > Reviewer > QA.

```python
import asyncio
from src.agents.reviewer import ReviewPipeline

pipeline = ReviewPipeline()

code = '''
def get_user(id):
    return db.query(f"SELECT * FROM users WHERE id = {id}")
'''

# Chạy full review pipeline
result = asyncio.run(pipeline.run(code, filename="user_service.py"))
# Reviewer sẽ phát hiện SQL injection vulnerability
```

### 5. Observability (`src/monitoring/langsmith_logger.py`)

LangSmith logging cho agent runtime, token usage, errors.

```python
from src.monitoring.langsmith_logger import LangSmithLogger

logger = LangSmithLogger(project_name="MyProject", api_key="ls_...")

# Track agent execution
metrics = logger.start_tracking("api_agent", "task_001")
# ... agent làm việc ...
logger.end_tracking(metrics, input_tokens=500, output_tokens=200)

# Decorator
@logger.track_agent("api_agent")
async def do_work():
    pass

# Xem thống kê
summary = logger.get_summary()
agent_stats = logger.get_agent_stats("api_agent")
```

### 6. Human Checkpoint (`src/checkpoints/human_approval.py`)

Flow: PM xong > Hỏi Thiêm > Dev bắt đầu.

```python
import asyncio
from src.checkpoints.human_approval import HumanApprovalSystem, CheckpointType

approval = HumanApprovalSystem()

# Tạo checkpoint
request = approval.create_checkpoint(
    CheckpointType.TASK_APPROVAL,
    title="Deploy v2.0 lên production",
    description="Bao gồm: new auth system, dashboard redesign",
    details={"estimated_downtime": "0", "rollback_plan": "revert to v1.9"},
)

# Thiêm approve
approval.approve(request.id, feedback="LGTM, deploy đi!")

# Hoặc reject
approval.reject(request.id, feedback="Chưa test đủ, thêm integration tests")
```

### 7. Template System (`src/templates/template_manager.py`)

3 templates sẵn có: SaaS, CRUD App, AI Tool.

```python
from src.templates.template_manager import TemplateManager

tm = TemplateManager()

# Xem templates
templates = tm.list_templates()

# Scaffold project mới
result = tm.scaffold("saas", output_dir="./my-saas-app", project_name="My SaaS")
result = tm.scaffold("crud", output_dir="./my-crud-app")
result = tm.scaffold("ai_tool", output_dir="./my-ai-tool")
```

## Tech Stack

- **Memory**: ChromaDB + LangChain
- **LLM**: Anthropic Claude (via langchain-anthropic)
- **Observability**: LangSmith
- **Language**: Python 3.11+

## License

MIT
