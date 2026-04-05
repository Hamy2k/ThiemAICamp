"""Tests for dev_team - agent execution, parsing, team management."""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from src.agents.dev_team import (
    DevAgent, DevTeam, AgentRole, WorktreeManager,
    AGENT_SYSTEM_PROMPTS,
)


class TestDevAgent:
    def test_agent_roles(self):
        for role in AgentRole:
            assert role in AGENT_SYSTEM_PROMPTS
            agent = DevAgent(role=role)
            assert agent.model  # Should have default from config
            assert not agent.is_busy

    def test_parse_file_blocks_single(self):
        text = 'FILE: src/app.py\n```python\nprint("hello")\n```'
        files = DevAgent._parse_file_blocks(text)
        assert "src/app.py" in files
        assert 'print("hello")' in files["src/app.py"]

    def test_parse_file_blocks_multiple(self):
        text = (
            'Here is the code:\n\n'
            'FILE: api/users.py\n```python\ndef get_users():\n    return []\n```\n\n'
            'FILE: api/auth.py\n```python\ndef login():\n    pass\n```'
        )
        files = DevAgent._parse_file_blocks(text)
        assert len(files) == 2
        assert "api/users.py" in files
        assert "api/auth.py" in files
        assert "get_users" in files["api/users.py"]

    def test_parse_file_blocks_no_files(self):
        text = "Here is some general explanation without any code blocks"
        files = DevAgent._parse_file_blocks(text)
        assert len(files) == 0

    def test_parse_file_blocks_with_lang_tag(self):
        text = 'FILE: index.js\n```javascript\nconsole.log("hi")\n```'
        files = DevAgent._parse_file_blocks(text)
        assert "index.js" in files

    @patch("src.agents.dev_team.ChatAnthropic")
    def test_execute_task(self, mock_llm_class):
        mock_response = MagicMock()
        mock_response.content = "Generated code"
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_llm_class.return_value = mock_llm

        agent = DevAgent(role=AgentRole.API)
        result = asyncio.get_event_loop().run_until_complete(
            agent.execute_task("Build user API")
        )
        assert result == "Generated code"
        assert not agent.is_busy

    @patch("src.agents.dev_team.ChatAnthropic")
    def test_execute_task_sets_busy(self, mock_llm_class):
        busy_during_exec = [False]

        async def fake_invoke(messages):
            busy_during_exec[0] = agent.is_busy
            mock_resp = MagicMock()
            mock_resp.content = "code"
            return mock_resp

        mock_llm = MagicMock()
        mock_llm.ainvoke = fake_invoke
        mock_llm_class.return_value = mock_llm

        agent = DevAgent(role=AgentRole.DB)
        asyncio.get_event_loop().run_until_complete(
            agent.execute_task("Create schema")
        )
        assert busy_during_exec[0] is True
        assert agent.is_busy is False

    @patch("src.agents.dev_team.ChatAnthropic")
    def test_execute_task_with_files(self, mock_llm_class):
        mock_response = MagicMock()
        mock_response.content = (
            'FILE: src/api.py\n```python\ndef hello():\n    return "hi"\n```'
        )
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_llm_class.return_value = mock_llm

        from src.execution.file_ops import FileOperations
        from src.execution.sandbox import Sandbox
        import tempfile, os

        with tempfile.TemporaryDirectory() as tmpdir:
            fops = FileOperations(tmpdir)
            sandbox = Sandbox(tmpdir)
            agent = DevAgent(role=AgentRole.API)

            result = asyncio.get_event_loop().run_until_complete(
                agent.execute_task_with_files(
                    "Build API", fops, sandbox
                )
            )
            assert "src/api.py" in result["files_written"]
            assert result["files_parsed"] == 1
            # File should actually exist
            assert os.path.exists(os.path.join(tmpdir, "src", "api.py"))


class TestDevTeam:
    def test_team_init(self):
        team = DevTeam()
        assert len(team.agents) == 4
        for role in AgentRole:
            assert role in team.agents

    def test_get_available_agents(self):
        team = DevTeam()
        available = team.get_available_agents()
        assert len(available) == 4

        team.agents[AgentRole.API].is_busy = True
        available = team.get_available_agents()
        assert len(available) == 3

    def test_team_status(self):
        team = DevTeam()
        status = team.team_status()
        assert "api" in status
        assert "ui" in status
        assert "auth" in status
        assert "db" in status
        assert status["api"]["busy"] is False

    @patch("src.agents.dev_team.ChatAnthropic")
    def test_assign_parallel(self, mock_llm_class):
        mock_response = MagicMock()
        mock_response.content = "code output"
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_llm_class.return_value = mock_llm

        team = DevTeam()
        results = asyncio.get_event_loop().run_until_complete(
            team.assign_parallel({
                AgentRole.API: "Build API",
                AgentRole.DB: "Create schema",
            })
        )
        assert AgentRole.API in results
        assert AgentRole.DB in results
        assert results[AgentRole.API] == "code output"
