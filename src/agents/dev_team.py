"""
UPGRADE 3 - MULTI-DEV PARALLEL (v2 - with error handling, real file I/O)
4 specialized agents: API, UI, Auth, DB chạy song song với git worktree.
"""

import os
import subprocess
import asyncio
import logging
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from src.utils import async_retry, AgentError
from src import config

logger = logging.getLogger(__name__)


class AgentRole(str, Enum):
    API = "api"
    UI = "ui"
    AUTH = "auth"
    DB = "db"


AGENT_SYSTEM_PROMPTS = {
    AgentRole.API: (
        "Ban la API Developer Agent. Chuyen xay dung REST/GraphQL APIs, "
        "xu ly routing, middleware, validation, va error handling. "
        "Viet code clean, co tests, va documentation day du."
    ),
    AgentRole.UI: (
        "Ban la UI Developer Agent. Chuyen xay dung giao dien nguoi dung "
        "voi React/Next.js, responsive design, accessibility, va UX tot. "
        "Su dung component-based architecture."
    ),
    AgentRole.AUTH: (
        "Ban la Auth Developer Agent. Chuyen xay dung he thong authentication "
        "va authorization: JWT, OAuth2, RBAC, session management. "
        "Bao mat la uu tien hang dau."
    ),
    AgentRole.DB: (
        "Ban la Database Developer Agent. Chuyen thiet ke schema, "
        "viet migrations, toi uu queries, indexing, va data modeling. "
        "Dam bao data integrity va performance."
    ),
}


@dataclass
class WorktreeInfo:
    path: str
    branch: str
    agent_role: AgentRole


@dataclass
class DevAgent:
    role: AgentRole
    model: str = ""
    worktree: Optional[WorktreeInfo] = None
    is_busy: bool = False
    current_task_id: Optional[str] = None

    def __post_init__(self):
        if not self.model:
            self.model = config.LLM_MODEL

    def get_llm(self) -> ChatAnthropic:
        return ChatAnthropic(model=self.model, temperature=config.LLM_TEMPERATURE)

    @async_retry(max_attempts=2, delay=1.0)
    async def execute_task(self, task_description: str) -> str:
        """Thực thi một task và trả về kết quả (text only)."""
        self.is_busy = True
        try:
            llm = self.get_llm()
            messages = [
                SystemMessage(content=AGENT_SYSTEM_PROMPTS[self.role]),
                HumanMessage(
                    content=f"Task: {task_description}\n\n"
                    f"Hay thuc hien task nay. Tra ve code va giai thich."
                ),
            ]
            response = await llm.ainvoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"Agent {self.role.value} failed: {e}")
            raise AgentError(self.role.value, str(e), e)
        finally:
            self.is_busy = False

    async def execute_task_with_files(
        self,
        task_description: str,
        file_ops: "FileOperations",
        sandbox: "Sandbox",
        existing_files: Optional[list[str]] = None,
    ) -> dict:
        """Execute task: LLM generates code -> write files -> validate via sandbox.

        Returns dict with: output, files_written, validation result.
        """
        from src.execution.file_ops import FileOperations
        from src.execution.sandbox import Sandbox

        self.is_busy = True
        try:
            # Step 1: Read existing files for context
            context_parts = []
            if existing_files:
                for fp in existing_files:
                    try:
                        content = file_ops.read_file(fp)
                        context_parts.append(f"--- {fp} ---\n{content}")
                    except FileNotFoundError:
                        pass

            context = "\n\n".join(context_parts) if context_parts else "No existing files."

            # Step 2: Ask LLM to generate code with file structure
            llm = self.get_llm()
            system_prompt = (
                f"{AGENT_SYSTEM_PROMPTS[self.role]}\n\n"
                "IMPORTANT: Return code in this format:\n"
                "For EACH file, use:\n"
                "FILE: path/to/file.py\n"
                "```\ncode here\n```\n\n"
                "You can return multiple files."
            )
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(
                    content=f"Task: {task_description}\n\n"
                    f"Existing code:\n{context}"
                ),
            ]
            response = await llm.ainvoke(messages)
            raw_output = response.content

            # Step 3: Parse file blocks from LLM output
            files_written = []
            parsed_files = self._parse_file_blocks(raw_output)

            for filepath, code in parsed_files.items():
                try:
                    file_ops.write_file(filepath, code)
                    files_written.append(filepath)
                    logger.info(f"Agent {self.role.value} wrote: {filepath}")
                except (PermissionError, OSError) as e:
                    logger.warning(f"Failed to write {filepath}: {e}")

            # Step 4: Validate Python files via sandbox
            validation = {"passed": True, "errors": []}
            for fp in files_written:
                if fp.endswith(".py"):
                    result = sandbox.run_lint(
                        str(file_ops._validate_path(fp))
                    )
                    if not result.success:
                        validation["passed"] = False
                        validation["errors"].append({
                            "file": fp,
                            "error": result.stderr[:500],
                        })

            return {
                "output": raw_output,
                "files_written": files_written,
                "files_parsed": len(parsed_files),
                "validation": validation,
            }

        except Exception as e:
            logger.error(f"Agent {self.role.value} execute_with_files failed: {e}")
            raise AgentError(self.role.value, str(e), e)
        finally:
            self.is_busy = False

    @staticmethod
    def _parse_file_blocks(text: str) -> dict[str, str]:
        """Parse FILE: path + code blocks from LLM output."""
        import re
        files = {}
        # Match: FILE: some/path.py\n```[lang]\ncode\n```
        pattern = r'FILE:\s*(.+?)\s*\n```[^\n]*\n(.*?)```'
        for match in re.finditer(pattern, text, re.DOTALL):
            filepath = match.group(1).strip()
            code = match.group(2)
            if filepath and code:
                files[filepath] = code
        return files


def _run_git(args: list[str], cwd: str) -> subprocess.CompletedProcess:
    """Run a git command safely."""
    result = subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        logger.warning(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result


class WorktreeManager:
    """Quản lý git worktrees cho các agents chạy song song."""

    def __init__(self, repo_path: str):
        self.repo_path = os.path.abspath(repo_path)
        self.worktrees: dict[str, WorktreeInfo] = {}

    def create_worktree(self, agent_role: AgentRole, branch_name: str) -> WorktreeInfo:
        """Tạo git worktree mới cho agent."""
        worktree_path = os.path.join(self.repo_path, f".worktrees/{agent_role.value}")
        os.makedirs(os.path.dirname(worktree_path), exist_ok=True)

        _run_git(["branch", branch_name], self.repo_path)

        result = _run_git(["worktree", "add", worktree_path, branch_name], self.repo_path)
        if result.returncode != 0 and "already exists" not in result.stderr:
            raise AgentError(agent_role.value, f"Failed to create worktree: {result.stderr}")

        info = WorktreeInfo(path=worktree_path, branch=branch_name, agent_role=agent_role)
        self.worktrees[agent_role.value] = info
        logger.info(f"Created worktree for {agent_role.value} at {worktree_path}")
        return info

    def remove_worktree(self, agent_role: AgentRole) -> None:
        key = agent_role.value
        if key in self.worktrees:
            _run_git(["worktree", "remove", self.worktrees[key].path, "--force"], self.repo_path)
            del self.worktrees[key]
            logger.info(f"Removed worktree for {key}")

    def merge_worktree(self, agent_role: AgentRole, target_branch: str = "main") -> bool:
        key = agent_role.value
        if key not in self.worktrees:
            return False

        info = self.worktrees[key]

        # Check for uncommitted changes
        status = _run_git(["status", "--porcelain"], info.path)
        if status.stdout.strip():
            logger.warning(f"Worktree {key} has uncommitted changes, auto-committing")
            _run_git(["add", "-A"], info.path)
            _run_git(["commit", "-m", f"Auto-commit from {key} agent"], info.path)

        result = _run_git(
            ["merge", info.branch, "--no-ff", "-m", f"Merge {key} agent work"],
            self.repo_path,
        )
        if result.returncode != 0:
            logger.error(f"Merge failed for {key}: {result.stderr}")
            return False
        return True


class DevTeam:
    """Đội ngũ 4 specialized agents chạy song song."""

    def __init__(self, repo_path: str = ".", model: str = ""):
        self.repo_path = os.path.abspath(repo_path)
        self.worktree_manager = WorktreeManager(self.repo_path)
        effective_model = model or config.LLM_MODEL
        self.agents: dict[AgentRole, DevAgent] = {
            role: DevAgent(role=role, model=effective_model)
            for role in AgentRole
        }

    def get_agent(self, role: AgentRole) -> DevAgent:
        return self.agents[role]

    def get_available_agents(self) -> list[DevAgent]:
        return [a for a in self.agents.values() if not a.is_busy]

    async def assign_task(self, role: AgentRole, task_description: str, task_id: str = "") -> str:
        """Giao task cho một agent cụ thể."""
        agent = self.agents[role]
        if agent.is_busy:
            raise AgentError(role.value, f"Agent {role.value} dang ban")

        agent.current_task_id = task_id
        try:
            result = await agent.execute_task(task_description)
            return result
        finally:
            agent.current_task_id = None

    async def assign_parallel(self, assignments: dict[AgentRole, str]) -> dict[AgentRole, str]:
        """Giao nhiều tasks cho nhiều agents chạy song song."""
        tasks = {
            role: self._run_agent(role, desc)
            for role, desc in assignments.items()
        }

        results = await asyncio.gather(*tasks.values(), return_exceptions=True)

        output = {}
        for role, result in zip(tasks.keys(), results):
            if isinstance(result, Exception):
                logger.error(f"Agent {role.value} failed: {result}")
                output[role] = f"ERROR: {result}"
            else:
                output[role] = result
        return output

    async def _run_agent(self, role: AgentRole, description: str) -> str:
        return await self.agents[role].execute_task(description)

    def setup_worktrees(self, base_branch: str = "dev") -> dict[AgentRole, WorktreeInfo]:
        result = {}
        for role in AgentRole:
            try:
                branch = f"{base_branch}/{role.value}"
                info = self.worktree_manager.create_worktree(role, branch)
                self.agents[role].worktree = info
                result[role] = info
            except Exception as e:
                logger.error(f"Failed to create worktree for {role.value}: {e}")
        return result

    def merge_all(self, target_branch: str = "main") -> dict[AgentRole, bool]:
        return {
            role: self.worktree_manager.merge_worktree(role, target_branch)
            for role in AgentRole
        }

    def cleanup(self) -> None:
        for role in AgentRole:
            try:
                self.worktree_manager.remove_worktree(role)
            except Exception as e:
                logger.error(f"Cleanup failed for {role.value}: {e}")

    def team_status(self) -> dict:
        return {
            role.value: {
                "busy": agent.is_busy,
                "current_task": agent.current_task_id,
                "has_worktree": agent.worktree is not None,
            }
            for role, agent in self.agents.items()
        }
