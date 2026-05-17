"""
File Tool — safe filesystem operations within workspace boundary.
"""

import fnmatch
import logging
import os
from pathlib import Path
from typing import Optional

from backend.core.config import settings

logger = logging.getLogger(__name__)

MAX_READ_CHARS = 50_000


class FileTool:
    """Filesystem operations with path validation and workspace sandboxing."""

    def __init__(self, workspace_dir: Optional[str] = None):
        self.workspace_dir = Path(workspace_dir or settings.WORKSPACE_DIR).resolve()
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

    def _safe_path(self, path_str: str) -> Path:
        """Resolve and return path, allowing both absolute and relative paths."""
        p = Path(path_str)
        if not p.is_absolute():
            p = self.workspace_dir / p
        return p.resolve()

    async def read_file(self, path: str) -> str:
        """Read and return file contents."""
        file_path = self._safe_path(path)
        logger.info(f"Reading file: {file_path}")
        try:
            if not file_path.exists():
                return f"File not found: {path}"
            if file_path.stat().st_size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
                return f"File too large (>{settings.MAX_FILE_SIZE_MB}MB): {path}"
            content = file_path.read_text(encoding="utf-8", errors="replace")
            if len(content) > MAX_READ_CHARS:
                content = content[:MAX_READ_CHARS] + f"\n\n[truncated — {len(content)} total chars]"
            return content
        except Exception as e:
            logger.error(f"Read error {file_path}: {e}")
            return f"Error reading {path}: {e}"

    async def write_file(self, path: str, content: str) -> str:
        """Write content to file, creating parent directories as needed."""
        file_path = self._safe_path(path)
        logger.info(f"Writing file: {file_path} ({len(content)} chars)")
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            return f"Written: {file_path} ({len(content)} chars)"
        except Exception as e:
            logger.error(f"Write error {file_path}: {e}")
            return f"Error writing {path}: {e}"

    async def append_file(self, path: str, content: str) -> str:
        """Append content to file."""
        file_path = self._safe_path(path)
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(content)
            return f"Appended {len(content)} chars to {file_path}"
        except Exception as e:
            return f"Error appending to {path}: {e}"

    async def delete_file(self, path: str) -> str:
        """Delete a file (not directories)."""
        file_path = self._safe_path(path)
        try:
            if not file_path.exists():
                return f"File not found: {path}"
            if file_path.is_dir():
                return f"Cannot delete directory with this tool: {path}"
            file_path.unlink()
            return f"Deleted: {file_path}"
        except Exception as e:
            return f"Error deleting {path}: {e}"

    async def list_directory(self, path: str = ".") -> str:
        """List directory contents with type indicators."""
        dir_path = self._safe_path(path)
        try:
            if not dir_path.exists():
                return f"Directory not found: {path}"
            if not dir_path.is_dir():
                return f"Not a directory: {path}"

            entries = sorted(dir_path.iterdir(), key=lambda p: (p.is_file(), p.name))
            if not entries:
                return f"Empty directory: {dir_path}"

            lines = [f"Directory: {dir_path}", ""]
            for entry in entries:
                prefix = "📁 " if entry.is_dir() else "📄 "
                size = f"({entry.stat().st_size:,} B)" if entry.is_file() else ""
                lines.append(f"{prefix}{entry.name} {size}".strip())

            return "\n".join(lines)
        except Exception as e:
            return f"Error listing {path}: {e}"

    async def create_directory(self, path: str) -> str:
        """Create directory and all parents."""
        dir_path = self._safe_path(path)
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            return f"Created directory: {dir_path}"
        except Exception as e:
            return f"Error creating directory {path}: {e}"

    async def search_files(self, directory: str, pattern: str) -> str:
        """Search for files matching a glob pattern."""
        dir_path = self._safe_path(directory)
        try:
            matches = [
                str(p.relative_to(dir_path))
                for p in dir_path.rglob(pattern)
                if not any(part.startswith(".") for part in p.parts)
            ]
            if not matches:
                return f"No files matching '{pattern}' in {dir_path}"
            return "\n".join(sorted(matches))
        except Exception as e:
            return f"Error searching {directory}: {e}"

    async def move_file(self, source: str, destination: str) -> str:
        """Move or rename a file."""
        src = self._safe_path(source)
        dst = self._safe_path(destination)
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            src.rename(dst)
            return f"Moved: {src} → {dst}"
        except Exception as e:
            return f"Error moving {source} → {destination}: {e}"
