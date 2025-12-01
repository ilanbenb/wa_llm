import pytest
from unittest.mock import patch
from services.prompt_manager import PromptManager


@pytest.fixture
def mock_template_dir(tmp_path):
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    (template_dir / "test.j2").write_text("Hello {{ name }}!")
    return template_dir


def test_prompt_manager_init_default():
    with patch("services.prompt_manager.Path") as mock_path:
        mock_path.return_value.parent.parent.__truediv__.return_value = (
            "/default/templates"
        )
        pm = PromptManager()
        assert str(pm.template_dir) == "/default/templates"


def test_prompt_manager_init_custom(mock_template_dir):
    pm = PromptManager(template_dir=mock_template_dir)
    assert pm.template_dir == mock_template_dir


def test_render_template(mock_template_dir):
    pm = PromptManager(template_dir=mock_template_dir)
    rendered = pm.render("test.j2", name="World")
    assert rendered == "Hello World!"


def test_render_template_not_found(mock_template_dir):
    pm = PromptManager(template_dir=mock_template_dir)
    with pytest.raises(
        Exception
    ):  # Jinja2 raises TemplateNotFound, but we can catch generic Exception for simplicity or import jinja2
        pm.render("non_existent.j2")