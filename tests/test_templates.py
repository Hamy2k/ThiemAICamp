"""Tests for template manager - scaffold, list, validation."""

import os
import pytest
from src.templates.template_manager import TemplateManager, TEMPLATES


class TestTemplateManager:
    @pytest.fixture
    def tm(self):
        return TemplateManager()

    def test_list_templates(self, tm):
        templates = tm.list_templates()
        assert len(templates) == 3
        keys = [t["key"] for t in templates]
        assert "saas" in keys
        assert "crud" in keys
        assert "ai_tool" in keys

    def test_template_has_required_fields(self, tm):
        for t in tm.list_templates():
            assert "name" in t
            assert "description" in t
            assert "tech_stack" in t
            assert len(t["tech_stack"]) > 0

    def test_scaffold_saas(self, tm, tmp_path):
        output = str(tmp_path / "my-saas")
        result = tm.scaffold("saas", output, "My SaaS App")
        assert result["files_created"] > 0
        assert os.path.exists(os.path.join(output, "thiemaicamp.json"))
        assert os.path.exists(os.path.join(output, ".env.example"))

    def test_scaffold_crud(self, tm, tmp_path):
        output = str(tmp_path / "my-crud")
        result = tm.scaffold("crud", output)
        assert result["files_created"] > 0
        assert os.path.exists(os.path.join(output, "backend", "app", "main.py"))

    def test_scaffold_ai_tool(self, tm, tmp_path):
        output = str(tmp_path / "my-ai")
        result = tm.scaffold("ai_tool", output)
        assert result["files_created"] > 0
        assert os.path.exists(os.path.join(output, "src", "agents", "chat_agent.py"))

    def test_scaffold_invalid_template(self, tm, tmp_path):
        with pytest.raises(ValueError):
            tm.scaffold("nonexistent", str(tmp_path))

    def test_scaffold_creates_env_example(self, tm, tmp_path):
        output = str(tmp_path / "test")
        tm.scaffold("saas", output)
        env_path = os.path.join(output, ".env.example")
        assert os.path.exists(env_path)
        with open(env_path) as f:
            content = f.read()
        assert "DATABASE_URL" in content

    def test_scaffold_creates_config(self, tm, tmp_path):
        import json
        output = str(tmp_path / "test")
        tm.scaffold("crud", output, "Test CRUD")
        config_path = os.path.join(output, "thiemaicamp.json")
        with open(config_path) as f:
            cfg = json.load(f)
        assert cfg["template"] == "crud"
        assert cfg["name"] == "Test CRUD"

    def test_scaffold_idempotent(self, tm, tmp_path):
        """Scaffolding twice shouldn't fail."""
        output = str(tmp_path / "test")
        tm.scaffold("saas", output)
        tm.scaffold("saas", output)  # Should not raise

    def test_all_templates_have_base_files(self):
        for key, template in TEMPLATES.items():
            assert len(template.base_files) > 0, f"Template {key} has no base files"
            assert len(template.folder_structure) > 0, f"Template {key} has no folders"
