"""
ThiemAICamp CLI - Command line interface cho AI Software Office.
"""

import json
import asyncio
import typer
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.utils import setup_logging

app = typer.Typer(
    name="thiemaicamp",
    help="ThiemAICamp - AI Software Office CLI",
    add_completion=False,
)
console = Console()


def _get_db():
    from src.persistence.database import Database
    return Database()


# ── Status ─────────────────────────────────────────────────────

@app.command()
def status():
    """Xem trang thai toan bo he thong."""
    from src.persistence.database import Database
    from src.memory.chroma_store import MemoryStore

    db = _get_db()
    console.print(Panel("[bold]ThiemAICamp System Status[/bold]", style="blue"))

    # Memory stats
    try:
        memory = MemoryStore()
        stats = memory.get_stats()
        table = Table(title="Memory Store")
        table.add_column("Collection", style="cyan")
        table.add_column("Count", justify="right")
        for name, count in stats.items():
            table.add_row(name, str(count))
        console.print(table)
    except Exception as e:
        console.print(f"[yellow]Memory store unavailable: {e}[/yellow]")

    # Metrics
    summary = db.get_metrics_summary()
    if summary.get("total_runs"):
        table = Table(title="Agent Metrics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right")
        table.add_row("Total Runs", str(summary.get("total_runs", 0)))
        table.add_row("Completed", str(summary.get("completed", 0)))
        table.add_row("Errors", str(summary.get("errors", 0)))
        table.add_row("Total Tokens", str(summary.get("total_tokens", 0)))
        console.print(table)

    # Pending approvals
    pending = db.get_pending_approvals()
    if pending:
        console.print(f"\n[yellow]Pending Approvals: {len(pending)}[/yellow]")
        for p in pending:
            console.print(f"  - [{p['id']}] {p['title']}")

    # Projects
    projects = db.list_projects()
    if projects:
        console.print(f"\nProjects: {len(projects)}")

    db.close()


# ── Memory ─────────────────────────────────────────────────────

@app.command()
def memory_search(query: str, collection: str = "code_patterns", n: int = 5):
    """Tim kiem trong memory store."""
    from src.memory.chroma_store import MemoryStore
    memory = MemoryStore()

    if collection == "all":
        results = memory.search_all(query, n)
        for coll_name, items in results.items():
            if items:
                console.print(f"\n[bold cyan]{coll_name}[/bold cyan]")
                for item in items:
                    dist = item.get("distance", "?")
                    console.print(f"  [{item['id']}] (dist={dist:.3f})")
                    console.print(f"  {item['content'][:150]}...")
    else:
        results = memory.search(query, collection, n)
        for item in results:
            dist = item.get("distance", "?")
            console.print(f"\n[cyan]{item['id']}[/cyan] (distance={dist:.3f})")
            console.print(item["content"][:300])


@app.command()
def memory_stats():
    """Xem thong ke memory store."""
    from src.memory.chroma_store import MemoryStore
    memory = MemoryStore()
    stats = memory.get_stats()
    table = Table(title="Memory Statistics")
    table.add_column("Collection", style="cyan")
    table.add_column("Documents", justify="right")
    total = 0
    for name, count in stats.items():
        table.add_row(name, str(count))
        total += count
    table.add_row("[bold]Total[/bold]", f"[bold]{total}[/bold]")
    console.print(table)


# ── Task Engine ────────────────────────────────────────────────

@app.command()
def project_create(name: str, description: str = ""):
    """Tao project moi."""
    from src.engine.task_engine import TaskEngine
    engine = TaskEngine(db=_get_db())
    project = engine.create_project(name, description)
    console.print(f"[green]Created project:[/green] {project.name} ({project.id})")


@app.command()
def project_status(project_id: str):
    """Xem tien do project."""
    from src.engine.task_engine import TaskEngine
    engine = TaskEngine(db=_get_db())
    # Load from DB
    data = engine.db.load_task_state(project_id)
    if not data:
        console.print(f"[red]Project {project_id} not found[/red]")
        return

    console.print(Panel(f"[bold]{data['name']}[/bold]", style="blue"))
    for m in data.get("milestones", []):
        tasks = m.get("tasks", [])
        done = sum(1 for t in tasks if t.get("status") == "completed")
        console.print(f"  Milestone: {m['title']} ({done}/{len(tasks)} tasks)")
        for t in tasks:
            status_color = {
                "completed": "green",
                "in_progress": "yellow",
                "failed": "red",
                "pending": "dim",
            }.get(t.get("status", "pending"), "dim")
            console.print(f"    [{status_color}][{t['status']}][/{status_color}] {t['title']}")


# ── Approvals ──────────────────────────────────────────────────

@app.command()
def approvals():
    """Xem danh sach approvals dang cho."""
    db = _get_db()
    pending = db.get_pending_approvals()
    if not pending:
        console.print("[green]No pending approvals[/green]")
        return

    table = Table(title="Pending Approvals")
    table.add_column("ID", style="cyan")
    table.add_column("Type")
    table.add_column("Title")
    table.add_column("Reviewer")
    for p in pending:
        table.add_row(p["id"], p["checkpoint_type"], p["title"], p["reviewer"])
    console.print(table)
    db.close()


@app.command()
def approve(request_id: str, feedback: str = ""):
    """Approve mot request."""
    from src.checkpoints.human_approval import HumanApprovalSystem
    system = HumanApprovalSystem(db=_get_db())
    if system.approve(request_id, feedback):
        console.print(f"[green]Approved: {request_id}[/green]")
    else:
        console.print(f"[red]Request not found: {request_id}[/red]")


@app.command()
def reject(request_id: str, feedback: str = ""):
    """Reject mot request."""
    from src.checkpoints.human_approval import HumanApprovalSystem
    system = HumanApprovalSystem(db=_get_db())
    if system.reject(request_id, feedback):
        console.print(f"[yellow]Rejected: {request_id}[/yellow]")
    else:
        console.print(f"[red]Request not found: {request_id}[/red]")


# ── Execution ──────────────────────────────────────────────────

@app.command()
def run_code(code: str, language: str = "python", timeout: int = 30):
    """Chay code trong sandbox."""
    from src.execution.sandbox import Sandbox
    sandbox = Sandbox(timeout=timeout)

    if language == "python":
        result = sandbox.run_python(code)
    elif language in ("js", "javascript", "node"):
        result = sandbox.run_node(code)
    else:
        result = sandbox.run_shell(code)

    if result.success:
        console.print(f"[green]Success[/green] ({result.duration_ms:.0f}ms)")
        if result.stdout:
            console.print(result.stdout)
    else:
        console.print(f"[red]Failed[/red] (exit code {result.returncode})")
        if result.stderr:
            console.print(f"[red]{result.stderr}[/red]")


@app.command()
def run_tests(path: str = "tests/"):
    """Chay tests."""
    from src.execution.sandbox import Sandbox
    sandbox = Sandbox()
    result = sandbox.run_tests(path)
    console.print(result.stdout)
    if result.stderr:
        console.print(f"[red]{result.stderr}[/red]")


# ── Templates ──────────────────────────────────────────────────

@app.command()
def templates():
    """Xem danh sach templates."""
    from src.templates.template_manager import TemplateManager
    tm = TemplateManager()
    table = Table(title="Available Templates")
    table.add_column("Key", style="cyan")
    table.add_column("Name")
    table.add_column("Tech Stack")
    for t in tm.list_templates():
        table.add_row(t["key"], t["name"], ", ".join(t["tech_stack"]))
    console.print(table)


@app.command()
def scaffold(template: str, output_dir: str, name: str = ""):
    """Scaffold project tu template."""
    from src.templates.template_manager import TemplateManager
    tm = TemplateManager()
    try:
        result = tm.scaffold(template, output_dir, name)
        console.print(f"[green]Scaffolded {result['template']}[/green]")
        console.print(f"  Output: {result['output_dir']}")
        console.print(f"  Files: {result['files_created']}")
    except ValueError as e:
        console.print(f"[red]{e}[/red]")


# ── Metrics ────────────────────────────────────────────────────

@app.command()
def metrics():
    """Xem metrics tong hop."""
    db = _get_db()
    summary = db.get_metrics_summary()
    table = Table(title="System Metrics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")
    for key, value in summary.items():
        if value is not None:
            display = f"{value:.2f}" if isinstance(value, float) else str(value)
            table.add_row(key.replace("_", " ").title(), display)
    console.print(table)
    db.close()


# ── Pipeline ───────────────────────────────────────────────────

@app.command()
def pipeline(
    name: str = typer.Argument(..., help="Project name"),
    description: str = typer.Option("", help="Project description"),
    auto_approve: bool = typer.Option(False, help="Skip approval step"),
):
    """Chay full pipeline cho mot project (interactive)."""
    from src.orchestrator.pipeline import Pipeline

    console.print(Panel(f"[bold]Pipeline: {name}[/bold]", style="blue"))
    console.print(f"Description: {description}")
    console.print(f"Auto-approve: {auto_approve}")

    p = Pipeline(auto_approve=auto_approve)
    console.print("\n[yellow]Pipeline initialized. Use the Python API to define tasks and run.[/yellow]")
    console.print("Example:")
    console.print('  from src.orchestrator.pipeline import Pipeline')
    console.print('  p = Pipeline(auto_approve=True)')
    console.print('  asyncio.run(p.run_project("name", "desc", tasks=[...]))')


def main():
    setup_logging()
    app()


if __name__ == "__main__":
    main()
