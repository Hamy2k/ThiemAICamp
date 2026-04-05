"""
UPGRADE 3 - MULTI-DEV PARALLEL
4 specialized agents: API, UI, Auth, DB chạy song song với git worktree.
"""

import os
import subprocess
import asyncio
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage


class AgentRole(str, Enum):
    API = "api"
    UI = "ui"
    AUTH = "auth"
    DB = "db"


AGENT_SYSTEM_PROMPTS = {
    AgentRole.API: (
        "Bạn là API Developer Agent. Chuyên xây dựng REST/GraphQL APIs, "
        "xử lý routing, middleware, validation, và error handling. "
        "Viết code clean, có tests, và documentation đầy đủ."
    ),
    AgentRole.UI: (
        "Bạn là UI Developer Agent. Chuyên xây dựng giao diện người dùng "
        "với React/Next.js, responsive design, accessibility, và UX tốt. "
        "Sử dụng component-based architecture."
    ),
    AgentRole.AUTH: (
        "Bạn là Auth Developer Agent. Chuyên xây dựng hệ thống authentication "
        "và authorization: JWT, OAuth2, RBAC, session management. "
        "Bảo mật là ưu tiên hàng đầu."
    ),
    AgentRole.DB: (
        "Bạn là Database Developer Agent. Chuyên thiết kế schema, "
        "viết migrations, tối ưu queries, indexing, và data modeling. "
        "Đảm bảo data integrity và performance."
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
    model: str = "claude-sonnet-4-5-20250514"
    worktree: Optional[WorktreeInfo] = None
    is_busy: bool = False
    current_task_id: Optional[str] = None

    def get_llm(self) -> ChatAnthropic:
        return ChatAnthropic(model=self.model, temperature=0)

    async def execute_task(self, task_description: str) -> str:
        """Thực thi một task và trả về kết quả."""
        self.is_busy = True
        try:
            llm = self.get_llm()
            messages = [
                SystemMessage(content=AGENT_SYSTEM_PROMPTS[self.role]),
                HumanMessage(content=f"Task: {task_description}\n\nHãy thực hiện task này. Trả về code và giải thích."),
            ]
            response = await llm.ainvoke(messages)
            return response.content
        finally:
            self.is_busy = False


class WorktreeManager:
    """Quản lý git worktrees cho các agents chạy song song."""

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.worktrees: dict[str, WorktreeInfo] = {}

    def create_worktree(self, agent_role: AgentRole, branch_name: str) -> WorktreeInfo:
        """Tạo git worktree mới cho agent."""
        worktree_path = os.path.join(self.repo_path, f".worktrees/{agent_role.value}")
        os.makedirs(os.path.dirname(worktree_path), exist_ok=True)

        # Tạo branch mới nếu chưa có
        subprocess.run(
            ["git", "branch", branch_name],
            cwd=self.repo_path,
            capture_output=True,
        )
        # Tạo worktree
        subprocess.run(
            ["git", "worktree", "add", worktree_path, branch_name],
            cwd=self.repo_path,
            capture_output=True,
        )

        info = WorktreeInfo(path=worktree_path, branch=branch_name, agent_role=agent_role)
        self.worktrees[agent_role.value] = info
        return info

    def remove_worktree(self, agent_role: AgentRole) -> None:
        """Xóa worktree của agent."""
        key = agent_role.value
        if key in self.worktrees:
            subprocess.run(
                ["git", "worktree", "remove", self.worktrees[key].path, "--force"],
                cwd=self.repo_path,
                capture_output=True,
            )
            del self.worktrees[key]

    def merge_worktree(self, agent_role: AgentRole, target_branch: str = "main") -> bool:
        """Merge branch của agent vào target branch."""
        key = agent_role.value
        if key not in self.worktrees:
            return False

        info = self.worktrees[key]
        result = subprocess.run(
            ["git", "merge", info.branch, "--no-ff", "-m", f"Merge {agent_role.value} agent work"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0


class DevTeam:
    """Đội ngũ 4 specialized agents chạy song song."""

    def __init__(self, repo_path: str = "."):
        self.repo_path = os.path.abspath(repo_path)
        self.worktree_manager = WorktreeManager(self.repo_path)
        self.agents: dict[AgentRole, DevAgent] = {
            role: DevAgent(role=role)
            for role in AgentRole
        }

    def get_agent(self, role: AgentRole) -> DevAgent:
        return self.agents[role]

    def get_available_agents(self) -> list[DevAgent]:
        return [a for a in self.agents.values() if not a.is_busy]

    async def assign_task(self, role: AgentRole, task_description: str, task_id: str) -> str:
        """Giao task cho một agent cụ thể."""
        agent = self.agents[role]
        if agent.is_busy:
            raise RuntimeError(f"Agent {role.value} đang bận")

        agent.current_task_id = task_id
        result = await agent.execute_task(task_description)
        agent.current_task_id = None
        return result

    async def assign_parallel(self, assignments: dict[AgentRole, str]) -> dict[AgentRole, str]:
        """Giao nhiều tasks cho nhiều agents chạy song song."""
        tasks = []
        for role, description in assignments.items():
            tasks.append(self._run_agent(role, description))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        output = {}
        for role, result in zip(assignments.keys(), results):
            if isinstance(result, Exception):
                output[role] = f"ERROR: {result}"
            else:
                output[role] = result
        return output

    async def _run_agent(self, role: AgentRole, description: str) -> str:
        agent = self.agents[role]
        return await agent.execute_task(description)

    def setup_worktrees(self, base_branch: str = "dev") -> dict[AgentRole, WorktreeInfo]:
        """Tạo worktrees cho tất cả agents."""
        result = {}
        for role in AgentRole:
            branch = f"{base_branch}/{role.value}"
            info = self.worktree_manager.create_worktree(role, branch)
            self.agents[role].worktree = info
            result[role] = info
        return result

    def merge_all(self, target_branch: str = "main") -> dict[AgentRole, bool]:
        """Merge tất cả worktrees vào target branch."""
        return {
            role: self.worktree_manager.merge_worktree(role, target_branch)
            for role in AgentRole
        }

    def cleanup(self) -> None:
        """Xóa tất cả worktrees."""
        for role in AgentRole:
            self.worktree_manager.remove_worktree(role)

    def team_status(self) -> dict:
        """Trạng thái của toàn bộ team."""
        return {
            role.value: {
                "busy": agent.is_busy,
                "current_task": agent.current_task_id,
                "has_worktree": agent.worktree is not None,
            }
            for role, agent in self.agents.items()
        }
