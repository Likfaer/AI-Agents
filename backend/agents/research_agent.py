"""
Research Agent — web search, documentation analysis, summarization.
"""

from backend.agents.base_agent import BaseAgent
from backend.tools.web_search_tool import WebSearchTool
from backend.tools.file_tool import FileTool


RESEARCH_SYSTEM_PROMPT = """You are an expert research AI assistant.
You find accurate, up-to-date information through web search and analysis.

Capabilities:
- Search the web for current information, documentation, and solutions
- Analyze and summarize findings from multiple sources
- Find code examples, library documentation, and best practices
- Compare technologies, frameworks, and approaches
- Extract key insights and actionable recommendations

Guidelines:
- Always search before answering questions about specific tools/versions
- Cross-reference multiple sources for important information
- Provide sources and context for your findings
- Be objective and highlight both pros and cons
- Format findings clearly with key takeaways"""


class ResearchAgent(BaseAgent):
    """Specialized agent for web research and information analysis."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._setup_tools()

    def _setup_tools(self):
        search_tool = WebSearchTool()
        file_tool = FileTool()

        self.register_tool(search_tool.search, {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "Search the web for information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "max_results": {"type": "integer", "description": "Max results (default 5)", "default": 5},
                    },
                    "required": ["query"],
                },
            },
        })

        self.register_tool(search_tool.fetch_page, {
            "type": "function",
            "function": {
                "name": "fetch_webpage",
                "description": "Fetch and extract text content from a URL",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "URL to fetch"},
                    },
                    "required": ["url"],
                },
            },
        })

        self.register_tool(file_tool.write_file, {
            "type": "function",
            "function": {
                "name": "write_file",
                "description": "Save research findings to a file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "content": {"type": "string"},
                    },
                    "required": ["path", "content"],
                },
            },
        })

    @property
    def name(self) -> str:
        return "Research Agent"

    @property
    def description(self) -> str:
        return "Performs web research, documentation analysis, and information synthesis"

    @property
    def system_prompt(self) -> str:
        return RESEARCH_SYSTEM_PROMPT
