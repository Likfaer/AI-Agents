"""
VS Code Tool — opens projects, creates files, manages workspace.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

from backend.core.config import settings
from backend.tools.file_tool import FileTool

logger = logging.getLogger(__name__)


class VSCodeTool:
    """Integration with Visual Studio Code via CLI."""

    def __init__(self):
        self.file_tool = FileTool()

    async def open_project(self, path: str) -> str:
        """Open a directory or file in VS Code."""
        resolved = Path(path).resolve()
        logger.info(f"Opening in VS Code: {resolved}")
        try:
            process = await asyncio.create_subprocess_shell(
                f"{settings.VSCODE_EXECUTABLE} {resolved}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await asyncio.wait_for(process.wait(), timeout=10)
            return f"Opened in VS Code: {resolved}"
        except asyncio.TimeoutError:
            return f"VS Code launched for: {resolved}"
        except Exception as e:
            return f"Failed to open VS Code: {e}"

    async def create_and_open(self, path: str, content: str = "") -> str:
        """Create a file and open it in VS Code."""
        write_result = await self.file_tool.write_file(path, content)
        open_result = await self.open_project(path)
        return f"{write_result}\n{open_result}"

    async def create_workspace_structure(
        self, base_path: str, structure: dict
    ) -> str:
        """
        Create a nested file/directory structure and open in VS Code.

        structure format:
        {
            "src/": {
                "main.py": "# main content",
                "utils/": {}
            },
            "README.md": "# My Project"
        }
        """
        base = Path(base_path).resolve()
        results = []

        async def _create_recursive(current_path: Path, nodes: dict):
            for name, value in nodes.items():
                target = current_path / name
                if isinstance(value, dict):
                    target.mkdir(parents=True, exist_ok=True)
                    results.append(f"📁 Created dir: {target}")
                    await _create_recursive(target, value)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(str(value), encoding="utf-8")
                    results.append(f"📄 Created file: {target}")

        await _create_recursive(base, structure)
        await self.open_project(str(base))
        results.append(f"✅ Opened {base} in VS Code")
        return "\n".join(results)

    async def install_extension(self, extension_id: str) -> str:
        """Install a VS Code extension."""
        try:
            process = await asyncio.create_subprocess_shell(
                f"{settings.VSCODE_EXECUTABLE} --install-extension {extension_id}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=60)
            out = stdout.decode() + stderr.decode()
            return f"Extension install result:\n{out}"
        except Exception as e:
            return f"Failed to install extension {extension_id}: {e}"

    async def list_workspace_files(self, path: str) -> str:
        """List all files in VS Code workspace."""
        return await self.file_tool.list_directory(path)
