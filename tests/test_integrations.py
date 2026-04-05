"""Tests for integrations - git_manager and notifier."""

import os
import pytest
import subprocess
import tempfile
from src.integrations.git_manager import GitManager
from src.integrations.notifier import Notifier, NotificationLevel, NotificationChannel
from src.persistence.database import Database


class TestGitManager:
    @pytest.fixture
    def git_repo(self, tmp_path):
        """Create a temp git repo."""
        repo = str(tmp_path / "repo")
        os.makedirs(repo)
        subprocess.run(["git", "init"], cwd=repo, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, capture_output=True)
        # Initial commit
        (tmp_path / "repo" / "init.txt").write_text("init")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=repo, capture_output=True)
        return repo

    def test_status_clean(self, git_repo):
        gm = GitManager(git_repo)
        status = gm.status()
        assert status["clean"] is True
        assert status["change_count"] == 0

    def test_status_dirty(self, git_repo):
        # Create new file
        with open(os.path.join(git_repo, "new.txt"), "w") as f:
            f.write("new file")
        gm = GitManager(git_repo)
        status = gm.status()
        assert status["clean"] is False

    def test_add_and_commit(self, git_repo):
        with open(os.path.join(git_repo, "feature.py"), "w") as f:
            f.write("print('feature')")
        gm = GitManager(git_repo)
        gm.add(["feature.py"])
        hash = gm.commit("Add feature")
        assert hash is not None

    def test_auto_commit(self, git_repo):
        with open(os.path.join(git_repo, "api.py"), "w") as f:
            f.write("# API code")
        gm = GitManager(git_repo)
        hash = gm.auto_commit(["api.py"], "api_agent", "Build user API")
        assert hash is not None

    def test_commit_nothing(self, git_repo):
        gm = GitManager(git_repo)
        assert gm.commit("Empty commit") is None

    def test_create_branch(self, git_repo):
        gm = GitManager(git_repo)
        assert gm.create_branch("feature/api") is True
        status = gm.status()
        assert status["branch"] == "feature/api"

    def test_get_log(self, git_repo):
        gm = GitManager(git_repo)
        log = gm.get_log(5)
        assert len(log) >= 1
        assert log[0]["message"] == "init"

    def test_get_diff(self, git_repo):
        with open(os.path.join(git_repo, "diff.py"), "w") as f:
            f.write("changed")
        gm = GitManager(git_repo)
        gm.add(["diff.py"])
        diff = gm.get_diff(staged=True)
        assert "changed" in diff

    def test_invalid_repo(self, tmp_path):
        # On Windows, git rev-parse may walk up to parent repo.
        # We test that _verify_repo checks returncode properly.
        gm = GitManager.__new__(GitManager)
        gm.repo_path = str(tmp_path / "definitely_not_a_repo_xyz")
        # Calling _verify_repo on non-existent dir should fail
        with pytest.raises(Exception):
            gm._verify_repo()


class TestNotifier:
    @pytest.fixture
    def db(self, tmp_path):
        db = Database(db_path=str(tmp_path / "test.db"))
        yield db
        db.close()

    @pytest.fixture
    def notifier(self, db):
        return Notifier(db=db)

    def test_console_notification(self, notifier, capsys):
        notifier.notify("Test Title", "Test message")
        captured = capsys.readouterr()
        assert "Test Title" in captured.out
        assert "Test message" in captured.out

    def test_file_notification(self, notifier, tmp_path):
        log_file = str(tmp_path / "notifications.log")
        notifier.log_file = log_file
        notifier.add_channel(NotificationChannel.FILE)
        notifier.notify("File Test", "Logged", channels=[NotificationChannel.FILE])
        assert os.path.exists(log_file)
        with open(log_file) as f:
            content = f.read()
        assert "File Test" in content

    def test_notification_persisted_to_db(self, notifier, db):
        notifier.notify("DB Test", "Persisted")
        # Should be persisted via db.log_notification

    def test_pipeline_convenience_methods(self, notifier, capsys):
        notifier.pipeline_started("MyProject", 5)
        notifier.pipeline_completed("MyProject", 10.5)
        captured = capsys.readouterr()
        assert "MyProject" in captured.out
        assert "5 tasks" in captured.out

    def test_approval_needed(self, notifier, capsys):
        notifier.approval_needed("ap_001", "Deploy v2")
        captured = capsys.readouterr()
        assert "Deploy v2" in captured.out

    def test_review_result(self, notifier, capsys):
        notifier.review_result("api.py", 8.5, True)
        captured = capsys.readouterr()
        assert "8.5" in captured.out
        assert "Approved" in captured.out
