"""
File Operations - Agents đọc/ghi files thật trên filesystem.
Cung cấp safe file I/O với validation và backup.
"""

import os
import shutil
import logging
import difflib
from datetime import datetime
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class FileOperations:
    """Safe file operations cho agents."""

    # Files/dirs that agents should never touch
    BLOCKED_PATTERNS = {
        ".git", ".env", "node_modules", "__pycache__",
        ".ssh", ".aws", "credentials", "secrets",
    }

    def __init__(self, workspace_dir: str, backup_dir: Optional[str] = None):
        self.workspace = Path(workspace_dir).resolve()
        self.backup_dir = Path(backup_dir or os.path.join(workspace_dir, ".backups")).resolve()
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self._changes: list[dict] = []

    def _validate_path(self, filepath: str) -> Path:
        """Validate path is within workspace and not blocked."""
        path = (self.workspace / filepath).resolve()

        # Prevent path traversal
        if not str(path).startswith(str(self.workspace)):
            raise PermissionError(f"Path traversal detected: {filepath}")

        # Check blocked patterns
        parts = path.parts
        for blocked in self.BLOCKED_PATTERNS:
            if blocked in parts or any(blocked in p for p in parts):
                raise PermissionError(f"Access to '{blocked}' is blocked: {filepath}")

        return path

    def read_file(self, filepath: str) -> str:
        """Đọc nội dung file."""
        path = self._validate_path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        content = path.read_text(encoding="utf-8")
        logger.debug(f"Read file: {filepath} ({len(content)} chars)")
        return content

    def write_file(self, filepath: str, content: str) -> dict:
        """Ghi file mới hoặc ghi đè file hiện tại (với backup)."""
        path = self._validate_path(filepath)

        # Create backup if file exists
        old_content = None
        if path.exists():
            old_content = path.read_text(encoding="utf-8")
            self._create_backup(filepath, old_content)

        # Create parent dirs
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        path.write_text(content, encoding="utf-8")

        change = {
            "action": "write",
            "file": filepath,
            "is_new": old_content is None,
            "size": len(content),
            "timestamp": datetime.now().isoformat(),
        }
        self._changes.append(change)
        logger.info(f"{'Created' if old_content is None else 'Updated'} file: {filepath}")
        return change

    def edit_file(self, filepath: str, old_text: str, new_text: str) -> dict:
        """Edit file bằng cách thay thế text cụ thể."""
        path = self._validate_path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        content = path.read_text(encoding="utf-8")

        if old_text not in content:
            raise ValueError(f"Text to replace not found in {filepath}")

        self._create_backup(filepath, content)
        new_content = content.replace(old_text, new_text, 1)
        path.write_text(new_content, encoding="utf-8")

        change = {
            "action": "edit",
            "file": filepath,
            "replaced_chars": len(old_text),
            "new_chars": len(new_text),
            "timestamp": datetime.now().isoformat(),
        }
        self._changes.append(change)
        logger.info(f"Edited file: {filepath}")
        return change

    def delete_file(self, filepath: str) -> dict:
        """Xóa file (với backup)."""
        path = self._validate_path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        content = path.read_text(encoding="utf-8")
        self._create_backup(filepath, content)
        path.unlink()

        change = {"action": "delete", "file": filepath, "timestamp": datetime.now().isoformat()}
        self._changes.append(change)
        logger.info(f"Deleted file: {filepath}")
        return change

    def list_files(self, directory: str = ".", pattern: str = "**/*") -> list[str]:
        """Liệt kê files trong directory."""
        dir_path = self._validate_path(directory)
        if not dir_path.is_dir():
            raise NotADirectoryError(f"Not a directory: {directory}")

        files = []
        for p in dir_path.glob(pattern):
            if p.is_file():
                rel = str(p.relative_to(self.workspace))
                # Skip blocked paths
                skip = False
                for blocked in self.BLOCKED_PATTERNS:
                    if blocked in rel:
                        skip = True
                        break
                if not skip:
                    files.append(rel.replace("\\", "/"))
        return sorted(files)

    def get_diff(self, filepath: str, new_content: str) -> str:
        """Tạo unified diff giữa file hiện tại và nội dung mới."""
        path = self._validate_path(filepath)
        if path.exists():
            old_content = path.read_text(encoding="utf-8")
        else:
            old_content = ""

        diff = difflib.unified_diff(
            old_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile=f"a/{filepath}",
            tofile=f"b/{filepath}",
        )
        return "".join(diff)

    def _create_backup(self, filepath: str, content: str) -> None:
        """Tạo backup trước khi modify."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{filepath.replace('/', '_').replace(os.sep, '_')}_{timestamp}"
        backup_path = self.backup_dir / backup_name
        backup_path.write_text(content, encoding="utf-8")

    def get_changes(self) -> list[dict]:
        """Trả về danh sách changes đã thực hiện."""
        return list(self._changes)

    def get_changed_files(self) -> list[str]:
        """Trả về danh sách files đã thay đổi."""
        return list({c["file"] for c in self._changes})

    def restore_backup(self, filepath: str) -> bool:
        """Khôi phục file từ backup gần nhất."""
        prefix = filepath.replace("/", "_").replace(os.sep, "_")
        backups = sorted(
            [f for f in self.backup_dir.iterdir() if f.name.startswith(prefix)],
            reverse=True,
        )
        if not backups:
            return False

        latest = backups[0]
        content = latest.read_text(encoding="utf-8")
        path = self._validate_path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        logger.info(f"Restored {filepath} from backup")
        return True
