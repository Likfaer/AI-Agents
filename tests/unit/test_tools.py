"""
Unit tests for tools and core components.
"""

import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Allow running from project root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# ─── File Tool Tests ──────────────────────────────────────────────────────────

class TestFileTool:
    @pytest.fixture
    def tool(self, tmp_path):
        from backend.tools.file_tool import FileTool
        return FileTool(workspace_dir=str(tmp_path))

    @pytest.mark.asyncio
    async def test_write_and_read(self, tool):
        result = await tool.write_file("test.txt", "Hello, World!")
        assert "Written" in result

        content = await tool.read_file("test.txt")
        assert content == "Hello, World!"

    @pytest.mark.asyncio
    async def test_read_nonexistent(self, tool):
        result = await tool.read_file("does_not_exist.txt")
        assert "not found" in result.lower()

    @pytest.mark.asyncio
    async def test_list_directory(self, tool, tmp_path):
        await tool.write_file("file1.txt", "a")
        await tool.write_file("file2.py", "b")
        result = await tool.list_directory(".")
        assert "file1.txt" in result
        assert "file2.py" in result

    @pytest.mark.asyncio
    async def test_create_directory(self, tool):
        result = await tool.create_directory("sub/nested/dir")
        assert "Created" in result

    @pytest.mark.asyncio
    async def test_delete_file(self, tool):
        await tool.write_file("to_delete.txt", "temp")
        result = await tool.delete_file("to_delete.txt")
        assert "Deleted" in result

        content = await tool.read_file("to_delete.txt")
        assert "not found" in content.lower()

    @pytest.mark.asyncio
    async def test_search_files(self, tool):
        await tool.write_file("src/main.py", "# main")
        await tool.write_file("src/utils.py", "# utils")
        await tool.write_file("README.md", "# readme")

        result = await tool.search_files(".", "*.py")
        assert "main.py" in result
        assert "utils.py" in result
        assert "README.md" not in result

    @pytest.mark.asyncio
    async def test_write_creates_parent_dirs(self, tool):
        result = await tool.write_file("deep/nested/file.txt", "content")
        assert "Written" in result
        content = await tool.read_file("deep/nested/file.txt")
        assert content == "content"


# ─── Terminal Tool Tests ──────────────────────────────────────────────────────

class TestTerminalTool:
    @pytest.fixture
    def tool(self, tmp_path):
        from backend.tools.terminal_tool import TerminalTool
        return TerminalTool(workspace_dir=str(tmp_path))

    @pytest.mark.asyncio
    async def test_basic_python_command(self, tool):
        result = await tool.execute("python --version")
        assert "Python" in result or "Exit code: 0" in result

    @pytest.mark.asyncio
    async def test_echo_command(self, tool):
        result = await tool.execute("echo hello")
        assert "hello" in result

    @pytest.mark.asyncio
    async def test_blocked_dangerous_command(self, tool):
        result = await tool.execute("rm -rf /")
        assert "BLOCKED" in result

    @pytest.mark.asyncio
    async def test_disallowed_command(self, tool):
        result = await tool.execute("nc -l 4444")
        assert "BLOCKED" in result or "not in allowed" in result

    @pytest.mark.asyncio
    async def test_timeout(self, tool):
        result = await tool.execute("python -c \"import time; time.sleep(60)\"", timeout=1)
        assert "TIMEOUT" in result


# ─── Web Search Tool Tests ────────────────────────────────────────────────────

class TestWebSearchTool:
    @pytest.fixture
    def tool(self):
        from backend.tools.web_search_tool import WebSearchTool
        return WebSearchTool()

    @pytest.mark.asyncio
    async def test_search_returns_results(self, tool):
        """Test that search returns formatted results (mocked)."""
        mock_html = """
        <html><body>
        <div class="result">
            <a class="result__title">Python FastAPI</a>
            <span class="result__url">fastapi.tiangolo.com</span>
            <a class="result__snippet">Modern web framework for Python</a>
        </div>
        </body></html>
        """
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.text = mock_html
            mock_response.raise_for_status = MagicMock()
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client.return_value)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.return_value.post = AsyncMock(return_value=mock_response)

            result = await tool.search("FastAPI tutorial")
            assert isinstance(result, str)


# ─── Code Analysis Tool Tests ─────────────────────────────────────────────────

class TestCodeAnalysisTool:
    @pytest.fixture
    def tool(self):
        from backend.tools.code_analysis_tool import CodeAnalysisTool
        return CodeAnalysisTool()

    @pytest.mark.asyncio
    async def test_valid_python(self, tool):
        code = "def hello():\n    return 'world'\n"
        result = await tool.analyze(code, "python")
        assert "Valid Python" in result

    @pytest.mark.asyncio
    async def test_syntax_error(self, tool):
        code = "def broken(\n    return None"
        result = await tool.analyze(code, "python")
        assert "Syntax Error" in result

    @pytest.mark.asyncio
    async def test_missing_docstring_warning(self, tool):
        code = "def no_doc():\n    pass\n"
        result = await tool.analyze(code, "python")
        assert "docstring" in result.lower()

    @pytest.mark.asyncio
    async def test_language_detection(self, tool):
        python_code = "import os\ndef main():\n    pass"
        result = await tool.analyze(python_code)
        assert "python" in result.lower()


# ─── Memory Manager Tests ─────────────────────────────────────────────────────

class TestMemoryManager:
    @pytest.fixture
    def manager(self, tmp_path):
        from backend.memory.memory_manager import MemoryManager
        return MemoryManager(memory_dir=str(tmp_path / "memory"))

    @pytest.mark.asyncio
    async def test_store_and_recall(self, manager):
        await manager.remember("Python is a great language for AI", "long_term")
        result = await manager.recall("Python AI", "long_term")
        assert "Python" in result

    @pytest.mark.asyncio
    async def test_clear_collection(self, manager):
        await manager.remember("test entry", "long_term")
        result = await manager.clear_collection("long_term")
        assert "Cleared" in result

    @pytest.mark.asyncio
    async def test_list_collections(self, manager):
        result = await manager.list_collections()
        assert "long_term" in result
        assert "short_term" in result


# ─── Project Generator Tests ──────────────────────────────────────────────────

class TestProjectGenerator:
    @pytest.fixture
    def tool(self):
        from backend.tools.project_generator_tool import ProjectGeneratorTool
        return ProjectGeneratorTool()

    @pytest.mark.asyncio
    async def test_fastapi_generation(self, tool, tmp_path):
        result = await tool.generate_project("my-api", "fastapi", str(tmp_path))
        assert "Created" in result or "Generated" in result
        assert (tmp_path / "my-api" / "app" / "main.py").exists()

    @pytest.mark.asyncio
    async def test_react_generation(self, tool, tmp_path):
        result = await tool.generate_project("my-app", "react", str(tmp_path))
        assert (tmp_path / "my-app" / "src" / "App.jsx").exists()

    @pytest.mark.asyncio
    async def test_unknown_template(self, tool, tmp_path):
        result = await tool.generate_project("x", "unknown-type", str(tmp_path))
        assert "Unknown" in result


# ─── Agent Registry Tests ─────────────────────────────────────────────────────

class TestAgentRegistry:
    @pytest.fixture
    def registry(self):
        from backend.orchestrator.agent_registry import AgentRegistry
        return AgentRegistry()

    def test_register_and_get(self, registry):
        mock_agent = MagicMock()
        mock_agent.name = "Test Agent"
        mock_agent.__class__.__name__ = "TestAgent"

        key = registry.register(mock_agent, "test")
        assert key == "test"
        assert registry.get("test") is mock_agent

    def test_get_nonexistent(self, registry):
        assert registry.get("nonexistent") is None

    @pytest.mark.asyncio
    async def test_submit_task_creates_task(self, registry):
        mock_agent = MagicMock()
        mock_agent.name = "Mock"
        mock_agent.__class__.__name__ = "MockAgent"
        mock_agent.run = AsyncMock(return_value=MagicMock(content="done", tools_used=[], execution_time=0.1, error=None))
        mock_agent.to_dict = MagicMock(return_value={})

        registry.register(mock_agent, "mock")
        task_id = await registry.submit_task("do something", "mock")
        assert task_id is not None

        await asyncio.sleep(0.5)
        task = registry.get_task(task_id)
        assert task is not None
