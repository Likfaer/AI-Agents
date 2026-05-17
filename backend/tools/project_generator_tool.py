"""
Project Generator Tool — scaffolds complete project structures.
Fixed: no longer creates double-nested directories.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

TEMPLATES: dict[str, dict] = {
    "fastapi": {
        "app/": {
            "__init__.py": "",
            "main.py": '"""FastAPI Application"""\nfrom fastapi import FastAPI\nfrom fastapi.middleware.cors import CORSMiddleware\n\napp = FastAPI(title="My API", version="0.1.0")\n\napp.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])\n\n@app.get("/health")\nasync def health():\n    return {"status": "ok"}\n',
            "routes/": {"__init__.py": "", "api.py": "from fastapi import APIRouter\nrouter = APIRouter()\n"},
            "models/": {"__init__.py": ""},
            "services/": {"__init__.py": ""},
        },
        "tests/": {"__init__.py": "", "test_main.py": "from fastapi.testclient import TestClient\nfrom app.main import app\n\nclient = TestClient(app)\n\ndef test_health():\n    r = client.get('/health')\n    assert r.status_code == 200\n"},
        "requirements.txt": "fastapi>=0.110.0\nuvicorn[standard]>=0.27.0\npydantic>=2.0.0\n",
        "README.md": "# FastAPI Project\n\n## Run\n```\nuvicorn app.main:app --reload\n```\n",
        ".env.example": "API_PORT=8000\n",
        "Dockerfile": 'FROM python:3.12-slim\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install -r requirements.txt\nCOPY . .\nCMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]\n',
    },
    "react": {
        "src/": {
            "App.jsx": "import React from 'react';\n\nexport default function App() {\n  return <div className='min-h-screen bg-gray-100'><h1>My App</h1></div>;\n}\n",
            "main.jsx": "import React from 'react';\nimport ReactDOM from 'react-dom/client';\nimport App from './App';\nimport './index.css';\n\nReactDOM.createRoot(document.getElementById('root')).render(<App />);\n",
            "index.css": "@tailwind base;\n@tailwind components;\n@tailwind utilities;\n",
            "components/": {},
            "pages/": {},
        },
        "public/": {},
        "index.html": "<!DOCTYPE html>\n<html>\n<head><meta charset='UTF-8'/><title>App</title></head>\n<body><div id='root'></div><script type='module' src='/src/main.jsx'></script></body>\n</html>\n",
        "package.json": '{"name":"my-app","version":"0.1.0","type":"module","scripts":{"dev":"vite","build":"vite build"},"dependencies":{"react":"^18","react-dom":"^18"},"devDependencies":{"@vitejs/plugin-react":"^4","vite":"^5","tailwindcss":"^3","autoprefixer":"^10","postcss":"^8"}}\n',
        "vite.config.js": "import { defineConfig } from 'vite';\nimport react from '@vitejs/plugin-react';\nexport default defineConfig({ plugins: [react()] });\n",
        "tailwind.config.js": "export default { content: ['./index.html','./src/**/*.{js,jsx}'], theme: { extend: {} }, plugins: [] };\n",
        "postcss.config.js": "export default { plugins: { tailwindcss: {}, autoprefixer: {} } };\n",
    },
    "python-lib": {
        "src/": {"__init__.py": "", "core.py": '"""Core library module."""\n\n\ndef main():\n    pass\n'},
        "tests/": {"__init__.py": "", "test_core.py": "from src.core import main\n\ndef test_main():\n    assert main() is None\n"},
        "pyproject.toml": '[build-system]\nrequires = ["hatchling"]\nbuild-backend = "hatchling.build"\n\n[project]\nname = "my-lib"\nversion = "0.1.0"\nrequires-python = ">=3.12"\n',
        "README.md": "# My Python Library\n\n## Install\n```\npip install -e .\n```\n",
    },
}


class ProjectGeneratorTool:
    """Generates complete project structures from templates."""

    async def generate_project(
        self, name: str, project_type: str, output_dir: str
    ) -> str:
        """
        Generate project structure from template.
        
        FIXED: output_dir is the PARENT directory.
        The project folder named `name` is created inside output_dir.
        Example: name='my-api', output_dir='./projects' → creates ./projects/my-api/
        """
        template = TEMPLATES.get(project_type)
        if not template:
            available = ", ".join(TEMPLATES.keys())
            return f"Unknown project type '{project_type}'. Available: {available}"

        # Нормализуем пути — output_dir это РОДИТЕЛЬСКАЯ папка
        # Убираем имя проекта из output_dir если оно там уже есть (защита от двойного вложения)
        out = Path(output_dir)
        if out.name == name:
            # Агент уже включил имя в путь — используем output_dir как финальный путь
            base = out.resolve()
        else:
            # Стандартный случай: добавляем имя
            base = (out / name).resolve()

        results = [f"Generating {project_type} project: {name}", f"Location: {base}", ""]

        async def _create(path: Path, nodes: dict):
            for node_name, value in nodes.items():
                target = path / node_name
                if isinstance(value, dict):
                    target.mkdir(parents=True, exist_ok=True)
                    results.append(f"  📁 {target.relative_to(base)}/")
                    if value:  # не создаём файлы если словарь пустой
                        await _create(target, value)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(str(value), encoding="utf-8")
                    results.append(f"  📄 {target.relative_to(base)}")

        await _create(base, template)
        results.append(f"\n✅ Project '{name}' created successfully at:\n   {base}")
        results.append(f"\nProject type: {project_type}")
        return "\n".join(results)

    def list_templates(self) -> str:
        return "Available templates:\n" + "\n".join(f"  - {t}" for t in TEMPLATES.keys())
