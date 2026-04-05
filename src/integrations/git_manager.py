"""
Git Manager - Auto commit, branch management, PR creation.
Tích hợp với DevTeam để auto-commit agent output.
"""

import os
import subprocess
import logging
from datetime import datetime
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


def _run_git(args: list[str], cwd: str, check: bool = False) -> subprocess.CompletedProcess:
    """Run git command safely."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if check and result.returncode != 0:
            logger.error(f"git {' '.join(args)} failed: {result.stderr.strip()}")
        return result
    except subprocess.TimeoutExpired:
        logger.error(f"git {' '.join(args)} timed out")
        raise
    except FileNotFoundError:
        logger.error("git is not installed")
        raise


class GitManager:
    """Quản lý git operations cho automated workflow."""

    def __init__(self, repo_path: str = "."):
        self.repo_path = str(Path(repo_path).resolve())
        self._verify_repo()

    def _verify_repo(self) -> None:
        """Verify this is a valid git repo."""
        result = _run_git(["rev-parse", "--git-dir"], self.repo_path)
        if result.returncode != 0:
            raise RuntimeError(f"Not a git repository: {self.repo_path}")

    def status(self) -> dict:
        """Get current git status."""
        result = _run_git(["status", "--porcelain"], self.repo_path)
        branch = _run_git(["branch", "--show-current"], self.repo_path)

        changes = []
        for line in result.stdout.strip().split("\n"):
            if line.strip():
                status_code = line[:2].strip()
                filepath = line[3:].strip()
                changes.append({"status": status_code, "file": filepath})

        return {
            "branch": branch.stdout.strip(),
            "clean": len(changes) == 0,
            "changes": changes,
            "change_count": len(changes),
        }

    def add(self, files: Optional[list[str]] = None) -> bool:
        """Stage files. If no files specified, stage all."""
        if files:
            for f in files:
                result = _run_git(["add", f], self.repo_path)
                if result.returncode != 0:
                    logger.warning(f"Failed to stage {f}: {result.stderr}")
                    return False
        else:
            result = _run_git(["add", "-A"], self.repo_path)
            return result.returncode == 0
        return True

    def commit(self, message: str, author: Optional[str] = None) -> Optional[str]:
        """Commit staged changes. Returns commit hash or None."""
        args = ["commit", "-m", message]
        if author:
            args.extend(["--author", author])

        result = _run_git(args, self.repo_path)
        if result.returncode != 0:
            if "nothing to commit" in result.stdout:
                logger.info("Nothing to commit")
                return None
            logger.error(f"Commit failed: {result.stderr}")
            return None

        # Extract commit hash
        hash_result = _run_git(["rev-parse", "HEAD"], self.repo_path)
        commit_hash = hash_result.stdout.strip()[:8]
        logger.info(f"Committed: {commit_hash} - {message}")
        return commit_hash

    def auto_commit(self, files: list[str], agent_name: str, task_description: str) -> Optional[str]:
        """Auto commit từ agent output."""
        self.add(files)

        message = (
            f"[{agent_name}] {task_description[:72]}\n\n"
            f"Auto-committed by ThiemAICamp agent at {datetime.now().isoformat()}"
        )
        return self.commit(message, author=f"ThiemAICamp <agent@thiemaicamp.dev>")

    def create_branch(self, branch_name: str, from_branch: str = "HEAD") -> bool:
        """Create and checkout new branch."""
        result = _run_git(["checkout", "-b", branch_name, from_branch], self.repo_path)
        if result.returncode != 0:
            # Branch might already exist
            result = _run_git(["checkout", branch_name], self.repo_path)
        return result.returncode == 0

    def switch_branch(self, branch_name: str) -> bool:
        result = _run_git(["checkout", branch_name], self.repo_path)
        return result.returncode == 0

    def merge(self, source_branch: str, message: Optional[str] = None) -> bool:
        """Merge branch into current branch."""
        args = ["merge", source_branch, "--no-ff"]
        if message:
            args.extend(["-m", message])
        result = _run_git(args, self.repo_path)
        if result.returncode != 0:
            logger.error(f"Merge failed: {result.stderr}")
            return False
        return True

    def push(self, branch: Optional[str] = None, remote: str = "origin") -> bool:
        """Push to remote."""
        args = ["push", remote]
        if branch:
            args.extend(["-u", remote, branch])
        result = _run_git(args, self.repo_path)
        if result.returncode != 0:
            logger.error(f"Push failed: {result.stderr}")
            return False
        logger.info(f"Pushed to {remote}")
        return True

    def get_diff(self, staged: bool = True) -> str:
        """Get diff of changes."""
        args = ["diff"]
        if staged:
            args.append("--cached")
        result = _run_git(args, self.repo_path)
        return result.stdout

    def get_log(self, n: int = 5) -> list[dict]:
        """Get recent commit log."""
        result = _run_git(
            ["log", f"-{n}", "--format=%H|%an|%ae|%s|%ai"],
            self.repo_path,
        )
        commits = []
        for line in result.stdout.strip().split("\n"):
            if "|" in line:
                parts = line.split("|", 4)
                commits.append({
                    "hash": parts[0][:8],
                    "author": parts[1],
                    "email": parts[2],
                    "message": parts[3],
                    "date": parts[4] if len(parts) > 4 else "",
                })
        return commits

    def stash(self) -> bool:
        result = _run_git(["stash"], self.repo_path)
        return result.returncode == 0

    def stash_pop(self) -> bool:
        result = _run_git(["stash", "pop"], self.repo_path)
        return result.returncode == 0
