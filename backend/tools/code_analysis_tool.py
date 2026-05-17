"""
Code Analysis Tool — static analysis, pattern detection, improvement suggestions.
"""

import ast
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


class CodeAnalysisTool:
    """Analyzes code for issues, patterns, and improvements."""

    COMPLEXITY_KEYWORDS = ["if", "elif", "else", "for", "while", "try", "except", "with", "and", "or"]

    async def analyze(self, code: str, language: Optional[str] = None) -> str:
        """Analyze code and return structured feedback."""
        if not language:
            language = self._detect_language(code)

        results = [f"Language: {language}", f"Lines: {len(code.splitlines())}", ""]

        if language == "python":
            results.extend(self._analyze_python(code))
        else:
            results.extend(self._analyze_generic(code, language))

        return "\n".join(results)

    def _detect_language(self, code: str) -> str:
        """Simple language detection from code content."""
        if "def " in code or "import " in code or "class " in code:
            return "python"
        if "function " in code or "const " in code or "let " in code or "var " in code:
            return "javascript"
        if "fn " in code or "let mut" in code or "impl " in code:
            return "rust"
        if "public class" in code or "System.out" in code:
            return "java"
        return "unknown"

    def _analyze_python(self, code: str) -> list[str]:
        issues = []
        suggestions = []

        # AST parsing
        try:
            tree = ast.parse(code)
            functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
            classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
            issues.append(f"✅ Syntax: Valid Python")
            issues.append(f"Functions found: {len(functions)}")
            issues.append(f"Classes found: {len(classes)}")

            # Check for missing docstrings
            for fn in functions:
                if not (fn.body and isinstance(fn.body[0], ast.Expr) and isinstance(fn.body[0].value, ast.Constant)):
                    suggestions.append(f"⚠️  Function '{fn.name}' missing docstring")

            # Check complexity
            for fn in functions:
                complexity = sum(
                    1 for node in ast.walk(fn)
                    if isinstance(node, (ast.If, ast.For, ast.While, ast.ExceptHandler))
                )
                if complexity > 10:
                    suggestions.append(f"⚠️  Function '{fn.name}' high complexity ({complexity})")

        except SyntaxError as e:
            issues.append(f"❌ Syntax Error: {e}")

        # Style checks
        lines = code.splitlines()
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                suggestions.append(f"⚠️  Line {i}: too long ({len(line)} chars)")
            if "except:" in line and "except Exception" not in line:
                suggestions.append(f"⚠️  Line {i}: bare 'except:' — use 'except Exception'")
            if "print(" in line and "debug" not in line.lower():
                suggestions.append(f"ℹ️  Line {i}: print() detected — consider logging")

        result = issues + [""] + (suggestions if suggestions else ["✅ No major issues found"])
        return result

    def _analyze_generic(self, code: str, language: str) -> list[str]:
        lines = code.splitlines()
        results = [f"Lines of code: {len(lines)}"]

        # Count basic complexity
        complexity = sum(
            line.strip().startswith(kw)
            for line in lines
            for kw in self.COMPLEXITY_KEYWORDS
        )
        results.append(f"Estimated complexity score: {complexity}")

        # TODO/FIXME detection
        todos = [f"Line {i}: {line.strip()}" for i, line in enumerate(lines, 1)
                 if re.search(r"TODO|FIXME|HACK|XXX", line, re.IGNORECASE)]
        if todos:
            results.append(f"\n⚠️  TODOs/FIXMEs ({len(todos)}):")
            results.extend(todos[:5])

        return results
