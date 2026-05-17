"""
Terminal Tool — sandboxed command execution.
Windows/Unix compatible with automatic command translation.
"""

import asyncio
import logging
import os
import platform
import shlex
from pathlib import Path
from typing import Optional

from backend.core.config import settings

logger = logging.getLogger(__name__)

IS_WINDOWS = platform.system() == "Windows"


class TerminalTool:
    """Secure terminal execution with Windows/Unix compatibility."""

    BLOCKED_PATTERNS = [
        "rm -rf /", "rm -rf ~", ":(){ :|:& };:",
        "dd if=", "mkfs", "fdisk",
        "> /dev/", "chmod -R 777 /",
        "curl | sh", "wget | sh", "curl | bash",
        "format c:", "del /f /s /q c:\\",
    ]

    ALLOWED_COMMANDS_WIN = {
        "python", "pip", "npm", "node", "git", "dir", "type", "echo",
        "mkdir", "copy", "move", "del", "where", "powershell", "pwsh",
        "docker", "uvicorn", "pytest", "code", "robocopy", "xcopy",
    }

    ALLOWED_COMMANDS_UNIX = {
        "python", "python3", "pip", "pip3", "npm", "node", "git",
        "ls", "cat", "echo", "mkdir", "touch", "cp", "mv", "find",
        "grep", "curl", "docker", "uvicorn", "pytest", "head", "tail",
        "wc", "sort", "which", "code",
    }

    # Unix команды → Windows PowerShell эквиваленты
    UNIX_TO_PS = {
        "ls":             "Get-ChildItem",
        "ls -la":         "Get-ChildItem -Force | Format-Table",
        "ls -l":          "Get-ChildItem | Format-Table",
        "cat":            "Get-Content",
        "grep":           "Select-String",
        "head":           "Select-Object -First",
        "tail":           "Select-Object -Last",
        "touch":          "New-Item -ItemType File",
        "which":          "Get-Command",
        "rm":             "Remove-Item",
        "cp":             "Copy-Item",
        "mv":             "Move-Item",
        "mkdir":          "New-Item -ItemType Directory",
        "clear":          "Clear-Host",
        "find":           None,   # обрабатывается отдельно
        "wc -l":          "(Get-Content {0}).Count",
    }

    def __init__(self, workspace_dir: Optional[str] = None):
        self.workspace_dir = Path(workspace_dir or settings.WORKSPACE_DIR).resolve()
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.allowed = self.ALLOWED_COMMANDS_WIN if IS_WINDOWS else self.ALLOWED_COMMANDS_UNIX

    def _translate_for_windows(self, command: str) -> tuple[str, bool]:
        """
        Translate Unix command to Windows equivalent.
        Returns (translated_command, use_powershell).
        """
        stripped = command.strip()

        # find ... -name "*.py" → Get-ChildItem -Recurse -Filter
        if stripped.startswith("find "):
            parts = stripped.split()
            path = parts[1] if len(parts) > 1 else "."
            name_filter = ""
            for i, p in enumerate(parts):
                if p == "-name" and i + 1 < len(parts):
                    name_filter = parts[i + 1].strip('"\'')
            if name_filter:
                ps_cmd = f'Get-ChildItem -Path "{path}" -Recurse -Filter "{name_filter}" -ErrorAction SilentlyContinue | Select-Object -First 20 | ForEach-Object {{ $_.FullName }}'
            else:
                ps_cmd = f'Get-ChildItem -Path "{path}" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 20 | ForEach-Object {{ $_.FullName }}'
            return ps_cmd, True

        # head -N → Select-Object -First N
        if stripped.startswith("head"):
            parts = stripped.split()
            n = "10"
            pipeline_input = ""
            for i, p in enumerate(parts):
                if p.startswith("-") and p[1:].isdigit():
                    n = p[1:]
                elif not p.startswith("-") and p != "head":
                    pipeline_input = p
            if pipeline_input:
                return f"Get-Content '{pipeline_input}' | Select-Object -First {n}", True
            return f"$input | Select-Object -First {n}", True

        # tail -N → Select-Object -Last N
        if stripped.startswith("tail"):
            parts = stripped.split()
            n = "10"
            for p in parts:
                if p.startswith("-") and p[1:].isdigit():
                    n = p[1:]
            return f"$input | Select-Object -Last {n}", True

        # grep "pattern" file → Select-String
        if stripped.startswith("grep "):
            rest = stripped[5:]
            return f"Select-String {rest}", True

        # ls → dir /b
        if stripped in ("ls", "ls -a"):
            return "dir /b", False
        if stripped.startswith("ls "):
            path = stripped[3:]
            return f"dir /b {path}", False

        # cat file → type file
        if stripped.startswith("cat "):
            return "type " + stripped[4:], False

        # which → where
        if stripped.startswith("which "):
            return "where " + stripped[6:], False

        # touch file → type nul > file (создать пустой файл)
        if stripped.startswith("touch "):
            fname = stripped[6:]
            return f"type nul > {fname}", False

        return command, False

    def _validate_command(self, command: str) -> tuple[bool, str]:
        """Validate against blocklist and allowlist."""
        if not settings.ENABLE_SANDBOX:
            return True, ""

        cmd_lower = command.lower().strip()

        for pattern in self.BLOCKED_PATTERNS:
            if pattern in cmd_lower:
                return False, f"Blocked: {pattern!r}"

        # Извлекаем базовую команду
        try:
            # На Windows shlex может не работать корректно с путями
            first_token = command.strip().split()[0] if command.strip() else ""
            base_cmd = Path(first_token).name.lower()
            # Убираем .exe если есть
            if base_cmd.endswith(".exe"):
                base_cmd = base_cmd[:-4]
        except Exception:
            return False, "Cannot parse command"

        if not base_cmd:
            return False, "Empty command"

        # PowerShell командлеты начинаются с глагола — всегда разрешаем если используем PS
        if "-" in first_token or base_cmd in ("get-childitem", "select-string",
                                               "select-object", "get-content",
                                               "new-item", "remove-item",
                                               "copy-item", "move-item"):
            return True, ""

        if base_cmd not in self.allowed:
            return False, f"Command '{base_cmd}' not allowed. Allowed: {', '.join(sorted(self.allowed))}"

        return True, ""

    def _resolve_working_dir(self, working_dir: Optional[str]) -> Path:
        if working_dir:
            p = Path(working_dir).resolve()
            if not p.exists():
                p.mkdir(parents=True, exist_ok=True)
            return p
        return self.workspace_dir

    async def execute(
        self,
        command: str,
        working_dir: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> str:
        """Execute command with Windows/Unix translation."""
        timeout = timeout or settings.COMMAND_TIMEOUT
        use_powershell = False

        # Транслируем команду под Windows
        if IS_WINDOWS:
            command, use_powershell = self._translate_for_windows(command)

        valid, reason = self._validate_command(command)
        if not valid:
            logger.warning(f"Command blocked: {reason}")
            return f"[BLOCKED] {reason}"

        cwd = self._resolve_working_dir(working_dir)
        logger.info(f"Executing: {command!r} in {cwd}")

        try:
            if IS_WINDOWS and use_powershell:
                # Запуск через PowerShell для Unix-like команд
                actual_cmd = ["powershell", "-NoProfile", "-NonInteractive", "-Command", command]
                process = await asyncio.create_subprocess_exec(
                    *actual_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=str(cwd),
                )
            else:
                process = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=str(cwd),
                    env={**os.environ},
                )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )

            out = stdout.decode("utf-8", errors="replace").strip()
            err = stderr.decode("utf-8", errors="replace").strip()

            parts = []
            if out:
                parts.append(out)
            if err:
                parts.append(f"[stderr]\n{err}")

            output = "\n".join(parts)
            result = f"Exit code: {process.returncode}\n{output}" if output else f"Exit code: {process.returncode} (no output)"
            logger.info(f"Done. Exit={process.returncode}, len={len(output)}")
            return result

        except asyncio.TimeoutError:
            logger.error(f"Timeout after {timeout}s")
            return f"[TIMEOUT] Command exceeded {timeout}s"
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            return f"[ERROR] {e}"

    async def execute_script(self, script: str, language: str = "python") -> str:
        """Write script to temp file and execute it."""
        import tempfile
        ext_map = {"python": ".py", "bash": ".sh", "node": ".js"}
        cmd_map = {"python": "python", "bash": ("bash" if not IS_WINDOWS else "powershell"), "node": "node"}

        ext = ext_map.get(language, ".py")
        cmd = cmd_map.get(language, "python")

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=ext, dir=self.workspace_dir, delete=False, encoding="utf-8"
        ) as f:
            f.write(script)
            tmp_path = f.name

        return await self.execute(f"{cmd} \"{tmp_path}\"")
