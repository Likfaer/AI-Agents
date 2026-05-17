"""
File Agent — manages filesystem operations.
"""

from backend.agents.base_agent import BaseAgent
from backend.tools.file_tool import FileTool
from backend.tools.vscode_tool import VSCodeTool


class FileAgent(BaseAgent):
    """Specialized agent for file system management."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        file_tool = FileTool()
        vscode_tool = VSCodeTool()

        for fn, schema in [
            (file_tool.read_file, {
                "type": "function", "function": {
                    "name": "read_file",
                    "description": "Read file contents",
                    "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
                },
            }),
            (file_tool.write_file, {
                "type": "function", "function": {
                    "name": "write_file",
                    "description": "Write content to file",
                    "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]},
                },
            }),
            (file_tool.delete_file, {
                "type": "function", "function": {
                    "name": "delete_file",
                    "description": "Delete a file",
                    "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
                },
            }),
            (file_tool.list_directory, {
                "type": "function", "function": {
                    "name": "list_directory",
                    "description": "List directory contents",
                    "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
                },
            }),
            (file_tool.create_directory, {
                "type": "function", "function": {
                    "name": "create_directory",
                    "description": "Create directory and parents",
                    "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
                },
            }),
            (file_tool.search_files, {
                "type": "function", "function": {
                    "name": "search_files",
                    "description": "Search for files by name pattern",
                    "parameters": {"type": "object", "properties": {
                        "directory": {"type": "string"},
                        "pattern": {"type": "string"},
                    }, "required": ["directory", "pattern"]},
                },
            }),
            (vscode_tool.open_project, {
                "type": "function", "function": {
                    "name": "open_in_vscode",
                    "description": "Open a directory in VS Code",
                    "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
                },
            }),
        ]:
            self.register_tool(fn, schema)

    @property
    def name(self) -> str:
        return "File Agent"

    @property
    def description(self) -> str:
        return "Manages files, directories, and workspace organization"

    @property
    def system_prompt(self) -> str:
        return """You are a filesystem management AI. You organize, create, edit, and manage files
and project structures. Always verify paths before operations and create parent directories as needed.
Provide clear feedback on every file operation performed."""


# ---------------------------------------------------------------------------

class DevOpsAgent(BaseAgent):
    """Specialized agent for Docker, CI/CD, and deployment tasks."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from backend.tools.terminal_tool import TerminalTool
        from backend.tools.file_tool import FileTool
        terminal_tool = TerminalTool()
        file_tool = FileTool()

        self.register_tool(terminal_tool.execute, {
            "type": "function", "function": {
                "name": "execute_command",
                "description": "Run shell command (docker, git, etc.)",
                "parameters": {"type": "object", "properties": {
                    "command": {"type": "string"},
                    "working_dir": {"type": "string"},
                }, "required": ["command"]},
            },
        })
        self.register_tool(file_tool.write_file, {
            "type": "function", "function": {
                "name": "write_file",
                "description": "Write Dockerfile, docker-compose, CI config, etc.",
                "parameters": {"type": "object", "properties": {
                    "path": {"type": "string"}, "content": {"type": "string"},
                }, "required": ["path", "content"]},
            },
        })
        self.register_tool(file_tool.read_file, {
            "type": "function", "function": {
                "name": "read_file",
                "description": "Read configuration files",
                "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
            },
        })

    @property
    def name(self) -> str:
        return "DevOps Agent"

    @property
    def description(self) -> str:
        return "Handles Docker, deployment, CI/CD pipelines, and infrastructure"

    @property
    def system_prompt(self) -> str:
        return """You are a DevOps AI engineer. You handle Docker containerization, CI/CD pipelines,
deployment configurations, and infrastructure management.
Write production-ready Dockerfiles, compose files, and CI/CD configs.
Always follow security best practices and optimize for production use."""


# ---------------------------------------------------------------------------

class BuilderAgent(BaseAgent):
    """Specialized agent for scaffolding new AI agents and projects."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from backend.tools.file_tool import FileTool
        from backend.tools.terminal_tool import TerminalTool
        from backend.tools.project_generator_tool import ProjectGeneratorTool

        file_tool = FileTool()
        terminal_tool = TerminalTool()
        project_tool = ProjectGeneratorTool()

        self.register_tool(project_tool.generate_project, {
            "type": "function", "function": {
                "name": "generate_project",
                "description": "Generate a complete project structure from a specification",
                "parameters": {"type": "object", "properties": {
                    "name": {"type": "string", "description": "Project name"},
                    "project_type": {"type": "string", "description": "e.g. fastapi, react, python-lib"},
                    "output_dir": {"type": "string", "description": "Output directory"},
                }, "required": ["name", "project_type", "output_dir"]},
            },
        })
        self.register_tool(file_tool.write_file, {
            "type": "function", "function": {
                "name": "write_file",
                "description": "Write a file (agent code, config, etc.)",
                "parameters": {"type": "object", "properties": {
                    "path": {"type": "string"}, "content": {"type": "string"},
                }, "required": ["path", "content"]},
            },
        })
        self.register_tool(terminal_tool.execute, {
            "type": "function", "function": {
                "name": "execute_command",
                "description": "Run setup commands (npm install, pip install, etc.)",
                "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]},
            },
        })

    @property
    def name(self) -> str:
        return "Builder Agent"

    @property
    def description(self) -> str:
        return "Creates new AI agents, project scaffolding, and automation setups"

    @property
    def system_prompt(self) -> str:
        return """You are an AI system builder. You create new AI agents, scaffold complete projects,
and automate development workflows. When building new agents, follow the platform's BaseAgent pattern.
Create fully functional implementations, not templates."""
