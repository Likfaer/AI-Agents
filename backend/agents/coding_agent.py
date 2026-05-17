"""
Coding Agent — generates, refactors, and debugs code.
Integrates with file tools and terminal execution.
"""

from backend.agents.base_agent import BaseAgent
from backend.tools.file_tool import FileTool
from backend.tools.terminal_tool import TerminalTool
from backend.tools.code_analysis_tool import CodeAnalysisTool


CODING_SYSTEM_PROMPT = """You are an expert software engineer AI assistant.
You write clean, production-ready, well-documented code in any programming language.

Capabilities:
- Generate complete, working implementations (no stubs, no placeholders)
- Debug and fix errors with clear explanations
- Refactor code for clarity, performance, and maintainability
- Create full project structures with all necessary files
- Write tests, documentation, and configuration files

Guidelines:
- Always write complete code — never truncate with "..." or "add rest here"
- Use modern best practices for the target language/framework
- Include error handling, logging, and type hints where appropriate
- When creating files, use the file tools to actually write them
- When testing code, use the terminal tool to run it
- Explain your decisions concisely after implementing"""


class CodingAgent(BaseAgent):
    """Specialized agent for code generation, debugging, and refactoring."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._setup_tools()

    def _setup_tools(self):
        file_tool = FileTool()
        terminal_tool = TerminalTool()
        code_tool = CodeAnalysisTool()

        self.register_tool(file_tool.read_file, {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read contents of a file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path to read"},
                    },
                    "required": ["path"],
                },
            },
        })

        self.register_tool(file_tool.write_file, {
            "type": "function",
            "function": {
                "name": "write_file",
                "description": "Write or create a file with given content",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path to write"},
                        "content": {"type": "string", "description": "Content to write"},
                    },
                    "required": ["path", "content"],
                },
            },
        })

        self.register_tool(file_tool.list_directory, {
            "type": "function",
            "function": {
                "name": "list_directory",
                "description": "List files and directories at a path",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Directory path"},
                    },
                    "required": ["path"],
                },
            },
        })

        self.register_tool(terminal_tool.execute, {
            "type": "function",
            "function": {
                "name": "execute_command",
                "description": "Execute a terminal command and return output",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "Command to execute"},
                        "working_dir": {"type": "string", "description": "Working directory (optional)"},
                    },
                    "required": ["command"],
                },
            },
        })

        self.register_tool(code_tool.analyze, {
            "type": "function",
            "function": {
                "name": "analyze_code",
                "description": "Analyze code for issues, patterns, and improvements",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Code to analyze"},
                        "language": {"type": "string", "description": "Programming language"},
                    },
                    "required": ["code"],
                },
            },
        })

    @property
    def name(self) -> str:
        return "Coding Agent"

    @property
    def description(self) -> str:
        return "Generates, debugs, and refactors code in any language"

    @property
    def system_prompt(self) -> str:
        return CODING_SYSTEM_PROMPT
