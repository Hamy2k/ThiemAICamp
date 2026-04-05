"""
UPGRADE 7 - TEMPLATE SYSTEM
3 templates: SaaS, CRUD App, AI Tool.
Mỗi template có: folder structure, base code, config.
"""

import os
import json
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TemplateConfig:
    name: str
    description: str
    tech_stack: list[str]
    folder_structure: dict
    base_files: dict[str, str]  # filepath -> content
    dependencies: dict[str, str] = field(default_factory=dict)
    env_vars: list[str] = field(default_factory=list)


# ============================================================
# TEMPLATE 1: SaaS Application
# ============================================================
SAAS_TEMPLATE = TemplateConfig(
    name="SaaS Application",
    description="Full-stack SaaS với auth, billing, dashboard, multi-tenant",
    tech_stack=["Next.js", "TypeScript", "Prisma", "PostgreSQL", "Stripe", "Tailwind CSS"],
    folder_structure={
        "src/app": ["layout.tsx", "page.tsx", "globals.css"],
        "src/app/api/auth": ["route.ts"],
        "src/app/api/billing": ["route.ts"],
        "src/app/dashboard": ["page.tsx", "layout.tsx"],
        "src/components/ui": ["button.tsx", "card.tsx", "input.tsx"],
        "src/lib": ["db.ts", "auth.ts", "stripe.ts"],
        "prisma": ["schema.prisma"],
    },
    base_files={
        "src/lib/db.ts": '''import { PrismaClient } from "@prisma/client";

const globalForPrisma = globalThis as unknown as { prisma: PrismaClient };
export const prisma = globalForPrisma.prisma || new PrismaClient();

if (process.env.NODE_ENV !== "production") globalForPrisma.prisma = prisma;
''',
        "prisma/schema.prisma": '''datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

generator client {
  provider = "prisma-client-js"
}

model User {
  id        String   @id @default(cuid())
  email     String   @unique
  name      String?
  plan      String   @default("free")
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}

model Subscription {
  id               String   @id @default(cuid())
  userId           String
  stripeCustomerId String
  stripePriceId    String
  status           String
  createdAt        DateTime @default(now())
}
''',
        "src/app/layout.tsx": '''import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SaaS App",
  description: "Built with ThiemAICamp",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
''',
    },
    dependencies={
        "next": "latest",
        "@prisma/client": "latest",
        "stripe": "latest",
        "tailwindcss": "latest",
    },
    env_vars=["DATABASE_URL", "STRIPE_SECRET_KEY", "NEXTAUTH_SECRET"],
)


# ============================================================
# TEMPLATE 2: CRUD Application
# ============================================================
CRUD_TEMPLATE = TemplateConfig(
    name="CRUD Application",
    description="FastAPI backend + React frontend với full CRUD operations",
    tech_stack=["FastAPI", "Python", "SQLAlchemy", "React", "PostgreSQL"],
    folder_structure={
        "backend/app": ["main.py", "config.py"],
        "backend/app/models": ["__init__.py", "base.py"],
        "backend/app/schemas": ["__init__.py"],
        "backend/app/api": ["__init__.py", "routes.py"],
        "backend/app/crud": ["__init__.py", "base.py"],
        "backend/tests": ["test_api.py"],
        "frontend/src": ["App.tsx", "index.tsx"],
        "frontend/src/components": ["DataTable.tsx", "Form.tsx"],
        "frontend/src/hooks": ["useApi.ts"],
    },
    base_files={
        "backend/app/main.py": '''from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="CRUD App", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}
''',
        "backend/app/models/base.py": '''from sqlalchemy import Column, Integer, DateTime, func
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
''',
        "backend/app/crud/base.py": '''from typing import Generic, TypeVar, Type
from sqlalchemy.orm import Session
from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class CRUDBase(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    def get(self, db: Session, id: int) -> ModelType | None:
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(self, db: Session, skip: int = 0, limit: int = 100) -> list[ModelType]:
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, obj_in: dict) -> ModelType:
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, db_obj: ModelType, obj_in: dict) -> ModelType:
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, id: int) -> bool:
        obj = db.query(self.model).filter(self.model.id == id).first()
        if obj:
            db.delete(obj)
            db.commit()
            return True
        return False
''',
    },
    dependencies={
        "fastapi": "latest",
        "uvicorn": "latest",
        "sqlalchemy": "latest",
        "alembic": "latest",
    },
    env_vars=["DATABASE_URL", "SECRET_KEY"],
)


# ============================================================
# TEMPLATE 3: AI Tool
# ============================================================
AI_TOOL_TEMPLATE = TemplateConfig(
    name="AI Tool",
    description="AI-powered tool với LangChain, vector store, và chat interface",
    tech_stack=["Python", "LangChain", "ChromaDB", "FastAPI", "Anthropic"],
    folder_structure={
        "src": ["main.py", "config.py"],
        "src/agents": ["__init__.py", "chat_agent.py"],
        "src/chains": ["__init__.py", "rag_chain.py"],
        "src/vectorstore": ["__init__.py", "store.py"],
        "src/api": ["__init__.py", "routes.py"],
        "data": [],
        "tests": ["test_agent.py"],
    },
    base_files={
        "src/main.py": '''from fastapi import FastAPI
from src.api.routes import router

app = FastAPI(title="AI Tool", version="1.0.0")
app.include_router(router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok", "model": "claude"}
''',
        "src/agents/chat_agent.py": '''from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage


class ChatAgent:
    def __init__(self, model: str = "claude-sonnet-4-5-20250514"):
        self.llm = ChatAnthropic(model=model, temperature=0)
        self.system_prompt = "You are a helpful AI assistant."

    async def chat(self, message: str, history: list = None) -> str:
        messages = [SystemMessage(content=self.system_prompt)]
        if history:
            messages.extend(history)
        messages.append(HumanMessage(content=message))

        response = await self.llm.ainvoke(messages)
        return response.content
''',
        "src/vectorstore/store.py": '''import chromadb
from chromadb.config import Settings


class VectorStore:
    def __init__(self, persist_dir: str = "./data/chroma"):
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection("documents")

    def add_documents(self, texts: list[str], ids: list[str], metadatas: list[dict] = None):
        self.collection.add(documents=texts, ids=ids, metadatas=metadatas)

    def search(self, query: str, n_results: int = 5) -> list[dict]:
        results = self.collection.query(query_texts=[query], n_results=n_results)
        return [
            {"id": results["ids"][0][i], "text": results["documents"][0][i]}
            for i in range(len(results["ids"][0]))
        ]
''',
        "src/chains/rag_chain.py": '''from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from src.vectorstore.store import VectorStore


class RAGChain:
    def __init__(self, model: str = "claude-sonnet-4-5-20250514"):
        self.llm = ChatAnthropic(model=model, temperature=0)
        self.vectorstore = VectorStore()

    async def query(self, question: str) -> str:
        # Retrieve relevant documents
        docs = self.vectorstore.search(question, n_results=3)
        context = "\\n".join(d["text"] for d in docs)

        messages = [
            SystemMessage(content=f"Answer based on this context:\\n{context}"),
            HumanMessage(content=question),
        ]
        response = await self.llm.ainvoke(messages)
        return response.content
''',
    },
    dependencies={
        "langchain": "latest",
        "langchain-anthropic": "latest",
        "chromadb": "latest",
        "fastapi": "latest",
        "uvicorn": "latest",
    },
    env_vars=["ANTHROPIC_API_KEY", "LANGSMITH_API_KEY"],
)


# Registry
TEMPLATES = {
    "saas": SAAS_TEMPLATE,
    "crud": CRUD_TEMPLATE,
    "ai_tool": AI_TOOL_TEMPLATE,
}


class TemplateManager:
    """Quản lý và scaffold projects từ templates."""

    def __init__(self):
        self.templates = TEMPLATES

    def list_templates(self) -> list[dict]:
        """Liệt kê tất cả templates."""
        return [
            {
                "key": key,
                "name": t.name,
                "description": t.description,
                "tech_stack": t.tech_stack,
            }
            for key, t in self.templates.items()
        ]

    def scaffold(self, template_key: str, output_dir: str, project_name: str = "") -> dict:
        """Tạo project mới từ template."""
        if template_key not in self.templates:
            raise ValueError(f"Template '{template_key}' không tồn tại. Chọn: {list(self.templates.keys())}")

        template = self.templates[template_key]
        created_dirs = []
        created_files = []

        # Tạo folder structure
        for folder, files in template.folder_structure.items():
            dir_path = os.path.join(output_dir, folder)
            os.makedirs(dir_path, exist_ok=True)
            created_dirs.append(folder)
            for filename in files:
                filepath = os.path.join(dir_path, filename)
                if not os.path.exists(filepath):
                    with open(filepath, "w") as f:
                        f.write(f"# {filename}\n")
                    created_files.append(os.path.join(folder, filename))

        # Tạo base files
        for filepath, content in template.base_files.items():
            full_path = os.path.join(output_dir, filepath)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w") as f:
                f.write(content)
            if filepath not in created_files:
                created_files.append(filepath)

        # Tạo .env.example
        if template.env_vars:
            env_path = os.path.join(output_dir, ".env.example")
            with open(env_path, "w") as f:
                for var in template.env_vars:
                    f.write(f"{var}=\n")
            created_files.append(".env.example")

        # Tạo .gitignore
        gitignore_path = os.path.join(output_dir, ".gitignore")
        gitignore_lines = [
            "node_modules/", "__pycache__/", "*.pyc", ".env", ".env.local",
            "dist/", "build/", ".next/", "*.egg-info/", ".pytest_cache/",
            "data/", ".DS_Store", "*.pem",
        ]
        with open(gitignore_path, "w") as f:
            f.write("\n".join(gitignore_lines) + "\n")
        created_files.append(".gitignore")

        # Tạo package config based on primary framework
        effective_name = project_name or template.name
        slug = effective_name.lower().replace(" ", "-")
        is_python_primary = template.tech_stack[0] in ("FastAPI", "Python")
        is_node_primary = template.tech_stack[0] in ("Next.js", "React", "TypeScript")

        if is_node_primary:
            pkg_path = os.path.join(output_dir, "package.json")
            pkg = {
                "name": slug,
                "version": "0.1.0",
                "private": True,
                "scripts": {"dev": "next dev", "build": "next build", "start": "next start"},
                "dependencies": template.dependencies,
            }
            with open(pkg_path, "w") as f:
                json.dump(pkg, f, indent=2)
            created_files.append("package.json")

        if is_python_primary or any(t in template.tech_stack for t in ["Python", "FastAPI"]):
            pyproject_path = os.path.join(output_dir, "pyproject.toml")
            py_deps = {k: v for k, v in template.dependencies.items()
                       if k not in ("next", "tailwindcss", "stripe")}
            deps = "\n".join(f'    "{k}",' for k in py_deps)
            with open(pyproject_path, "w") as f:
                f.write(
                    f'[project]\nname = "{slug}"\n'
                    f'version = "0.1.0"\n'
                    f'dependencies = [\n{deps}\n]\n'
                )
            created_files.append("pyproject.toml")

        # Tạo thiemaicamp config
        config_path = os.path.join(output_dir, "thiemaicamp.json")
        cfg = {
            "template": template_key,
            "name": effective_name,
            "tech_stack": template.tech_stack,
            "dependencies": template.dependencies,
        }
        with open(config_path, "w") as f:
            json.dump(cfg, f, indent=2)
        created_files.append("thiemaicamp.json")

        return {
            "template": template.name,
            "output_dir": output_dir,
            "dirs_created": len(created_dirs),
            "files_created": len(created_files),
            "files": created_files,
        }
