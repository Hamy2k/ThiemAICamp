"""
ThiemAICamp Telegram Bot - Ket noi Telegram voi AI Software Office pipeline.
Nhan lenh tu Telegram, chay pipeline, tra ket qua.

Usage:
    export TELEGRAM_BOT_TOKEN=your_token
    python -m src.telegram_bot
"""

import os
import asyncio
import logging
from datetime import datetime

from telegram import Update, BotCommand
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters,
)

from src.persistence.database import Database
from src.orchestrator.pipeline import Pipeline, PipelineStage
from src.agents.dev_team import AgentRole
from src.memory.chroma_store import MemoryStore
from src.templates.template_manager import TemplateManager
from src.utils import setup_logging

logger = logging.getLogger(__name__)

# Lazy-init pipeline (expensive to create)
_pipeline = None
_template_manager = None


def get_pipeline() -> Pipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = Pipeline(auto_approve=False, workspace_dir="./workspace")
    return _pipeline


def get_template_manager() -> TemplateManager:
    global _template_manager
    if _template_manager is None:
        _template_manager = TemplateManager()
    return _template_manager


# ── /start ─────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🐉 *Drake Dragon - ThiemAICamp Bot*\n\n"
        "AI Software Office san sang!\n\n"
        "📋 *Commands:*\n"
        "`/build <name> <desc>` - Tao project moi\n"
        "`/run <task>` - Chay 1 task\n"
        "`/status` - Xem trang thai\n"
        "`/approve <id>` - Approve request\n"
        "`/reject <id> <reason>` - Reject request\n"
        "`/templates` - Xem templates\n"
        "`/scaffold <type> <name>` - Tao project tu template\n"
        "`/memory <query>` - Tim trong memory\n"
        "`/score` - Xem metrics\n\n"
        "Hoac gui text bat ky de AI thuc hien task!",
        parse_mode="Markdown",
    )


# ── /build ─────────────────────────────────────────────────────

async def cmd_build(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if not args or len(args) < 2:
        await update.message.reply_text("❌ Cu phap: `/build <name> <description>`", parse_mode="Markdown")
        return

    name = args[0]
    description = " ".join(args[1:])
    await update.message.reply_text(f"🚀 Bat dau pipeline: *{name}*\n_{description}_", parse_mode="Markdown")

    pipeline = get_pipeline()

    # Auto-detect tasks from description
    tasks = [
        {"title": f"Build {name}", "role": "api", "priority": "high", "description": description},
    ]

    # Add more tasks if keywords detected
    desc_lower = description.lower()
    if any(kw in desc_lower for kw in ["auth", "login", "jwt", "oauth"]):
        tasks.append({"title": "Auth system", "role": "auth", "priority": "high", "description": "Authentication"})
    if any(kw in desc_lower for kw in ["database", "schema", "model", "db"]):
        tasks.append({"title": "Database", "role": "db", "priority": "medium", "description": "Database setup"})
    if any(kw in desc_lower for kw in ["ui", "frontend", "page", "form"]):
        tasks.append({"title": "Frontend", "role": "ui", "priority": "medium", "description": "UI components"})

    try:
        run = await pipeline.run_project(name, description, tasks, require_approval=False)

        if run.stage == PipelineStage.COMPLETED:
            files = run.results.get("files_written", [])
            files_text = "\n".join(f"  - `{f}`" for f in files[:10]) if files else "  (no files)"
            if len(files) > 10:
                files_text += f"\n  ... +{len(files) - 10} more"

            dev_results = run.results.get("development", {})
            review_results = run.results.get("review", {})

            await update.message.reply_text(
                f"✅ *Pipeline COMPLETED:* {name}\n\n"
                f"📊 *Summary:*\n"
                f"  - Tasks: {len(tasks)}\n"
                f"  - Files written: {len(files)}\n\n"
                f"📁 *Files:*\n{files_text}\n\n"
                f"⏱ Duration: {run.completed_at}",
                parse_mode="Markdown",
            )
        else:
            errors = "\n".join(run.errors[:5]) if run.errors else "Unknown"
            await update.message.reply_text(
                f"❌ *Pipeline FAILED:* {name}\n\n"
                f"Error: {errors}\n\n"
                f"💡 Thu lai voi: `/build {name} {description}`",
                parse_mode="Markdown",
            )

    except Exception as e:
        logger.error(f"Build failed: {e}")
        await update.message.reply_text(f"❌ Error: `{str(e)[:500]}`", parse_mode="Markdown")


# ── /run ───────────────────────────────────────────────────────

async def cmd_run(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("❌ Cu phap: `/run <task description>`", parse_mode="Markdown")
        return

    task = " ".join(context.args)
    await update.message.reply_text(f"⚡ Dang chay: _{task}_", parse_mode="Markdown")

    pipeline = get_pipeline()

    # Auto-detect role
    task_lower = task.lower()
    role = AgentRole.API
    if any(kw in task_lower for kw in ["ui", "frontend", "page", "component", "css"]):
        role = AgentRole.UI
    elif any(kw in task_lower for kw in ["auth", "login", "jwt", "password"]):
        role = AgentRole.AUTH
    elif any(kw in task_lower for kw in ["database", "schema", "migration", "model", "sql"]):
        role = AgentRole.DB

    try:
        result = await pipeline.run_single_task(task, role=role, review=False)
        output = result.get("output", "")
        # Truncate for Telegram (max 4096 chars)
        if len(output) > 3500:
            output = output[:3500] + "\n\n... (truncated)"

        await update.message.reply_text(
            f"✅ *Task completed* ({role.value} agent)\n\n"
            f"```\n{output}\n```",
            parse_mode="Markdown",
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: `{str(e)[:500]}`", parse_mode="Markdown")


# ── /status ────────────────────────────────────────────────────

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pipeline = get_pipeline()
    status = pipeline.get_system_status()

    team = status.get("team_status", {})
    team_text = "\n".join(
        f"  {role}: {'🔴 busy' if info.get('busy') else '🟢 available'}"
        for role, info in team.items()
    )

    pending = len(status.get("pending_approvals", []))
    metrics = status.get("metrics_summary", {})
    memory = status.get("memory_stats", {})

    memory_text = ", ".join(f"{k}: {v}" for k, v in memory.items()) if memory else "empty"

    await update.message.reply_text(
        f"📊 *ThiemAICamp Status*\n\n"
        f"🤖 *Team:*\n{team_text}\n\n"
        f"📋 Pending Approvals: {pending}\n"
        f"📈 Total Runs: {metrics.get('total_runs', 0)}\n"
        f"🎯 Tokens Used: {metrics.get('total_tokens', 0)}\n"
        f"🧠 Memory: {memory_text}",
        parse_mode="Markdown",
    )


# ── /approve, /reject ─────────────────────────────────────────

async def cmd_approve(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("❌ Cu phap: `/approve <request_id>`", parse_mode="Markdown")
        return

    request_id = context.args[0]
    feedback = " ".join(context.args[1:]) if len(context.args) > 1 else ""

    pipeline = get_pipeline()
    if pipeline.approval_system.approve(request_id, feedback):
        await update.message.reply_text(f"✅ Approved: `{request_id}`", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"❌ Request `{request_id}` khong tim thay", parse_mode="Markdown")


async def cmd_reject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("❌ Cu phap: `/reject <request_id> <reason>`", parse_mode="Markdown")
        return

    request_id = context.args[0]
    reason = " ".join(context.args[1:]) if len(context.args) > 1 else "Rejected"

    pipeline = get_pipeline()
    if pipeline.approval_system.reject(request_id, reason):
        await update.message.reply_text(f"🚫 Rejected: `{request_id}` - {reason}", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"❌ Request `{request_id}` khong tim thay", parse_mode="Markdown")


# ── /templates, /scaffold ─────────────────────────────────────

async def cmd_templates(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tm = get_template_manager()
    templates = tm.list_templates()
    text = "\n".join(
        f"  `{t['key']}` - *{t['name']}*\n    {', '.join(t['tech_stack'])}"
        for t in templates
    )
    await update.message.reply_text(
        f"📦 *Templates:*\n\n{text}\n\n"
        f"Dung: `/scaffold <key> <project_name>`",
        parse_mode="Markdown",
    )


async def cmd_scaffold(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("❌ Cu phap: `/scaffold <template> <name>`", parse_mode="Markdown")
        return

    template_key = context.args[0]
    project_name = " ".join(context.args[1:])
    output_dir = f"./workspace/{project_name.lower().replace(' ', '-')}"

    tm = get_template_manager()
    try:
        result = tm.scaffold(template_key, output_dir, project_name)
        await update.message.reply_text(
            f"✅ *Scaffolded:* {result['template']}\n\n"
            f"📁 Output: `{result['output_dir']}`\n"
            f"📄 Files: {result['files_created']}",
            parse_mode="Markdown",
        )
    except ValueError as e:
        await update.message.reply_text(f"❌ {e}", parse_mode="Markdown")


# ── /memory ────────────────────────────────────────────────────

async def cmd_memory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("❌ Cu phap: `/memory <search query>`", parse_mode="Markdown")
        return

    query = " ".join(context.args)
    pipeline = get_pipeline()
    results = pipeline.memory.search_all(query, n_results=3)

    parts = []
    for collection, items in results.items():
        if items:
            parts.append(f"*{collection}:*")
            for item in items:
                dist = item.get("distance", 0)
                preview = item["content"][:150].replace("`", "'")
                parts.append(f"  [{dist:.2f}] {preview}...")

    if parts:
        await update.message.reply_text(
            f"🧠 *Memory results for:* _{query}_\n\n" + "\n".join(parts),
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(f"🧠 Khong tim thay ket qua cho: _{query}_", parse_mode="Markdown")


# ── /score ─────────────────────────────────────────────────────

async def cmd_score(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pipeline = get_pipeline()
    metrics = pipeline.logger.get_summary()

    await update.message.reply_text(
        f"📈 *ThiemAICamp Metrics*\n\n"
        f"🏃 Total Runs: {metrics.get('total_runs', 0)}\n"
        f"✅ Completed: {metrics.get('completed', 0)}\n"
        f"❌ Errors: {metrics.get('errors', 0)}\n"
        f"🪙 Total Tokens: {metrics.get('total_tokens', 0)}\n"
        f"⏱ Avg Duration: {metrics.get('avg_duration', 0)}s",
        parse_mode="Markdown",
    )


# ── Free text handler ──────────────────────────────────────────

async def handle_free_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle any text message as a task for the AI pipeline."""
    text = update.message.text.strip()
    if not text or text.startswith("/"):
        return

    await update.message.reply_text(f"🤖 Dang xu ly: _{text}_", parse_mode="Markdown")

    # Detect role from text
    text_lower = text.lower()
    role = AgentRole.API
    if any(kw in text_lower for kw in ["ui", "frontend", "page", "component"]):
        role = AgentRole.UI
    elif any(kw in text_lower for kw in ["auth", "login", "jwt"]):
        role = AgentRole.AUTH
    elif any(kw in text_lower for kw in ["database", "schema", "sql", "model"]):
        role = AgentRole.DB

    pipeline = get_pipeline()
    try:
        result = await pipeline.run_single_task(text, role=role, review=False)
        output = result.get("output", "No output")
        if len(output) > 3500:
            output = output[:3500] + "\n... (truncated)"

        await update.message.reply_text(
            f"✅ *Done* ({role.value} agent)\n\n```\n{output}\n```",
            parse_mode="Markdown",
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: `{str(e)[:500]}`", parse_mode="Markdown")


# ── Main ───────────────────────────────────────────────────────

def main() -> None:
    setup_logging("INFO")

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ Set TELEGRAM_BOT_TOKEN environment variable!")
        print("   export TELEGRAM_BOT_TOKEN=your_bot_token")
        return

    app = Application.builder().token(token).build()

    # Register commands
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_start))
    app.add_handler(CommandHandler("build", cmd_build))
    app.add_handler(CommandHandler("run", cmd_run))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("approve", cmd_approve))
    app.add_handler(CommandHandler("reject", cmd_reject))
    app.add_handler(CommandHandler("templates", cmd_templates))
    app.add_handler(CommandHandler("scaffold", cmd_scaffold))
    app.add_handler(CommandHandler("memory", cmd_memory))
    app.add_handler(CommandHandler("score", cmd_score))

    # Free text handler (last priority)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_free_text))

    logger.info("🐉 ThiemAICamp Telegram Bot starting...")
    print("🐉 ThiemAICamp Bot dang chay! Gui /start trong Telegram de bat dau.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
