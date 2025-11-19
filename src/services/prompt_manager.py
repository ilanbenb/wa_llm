from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape


class PromptManager:
    def __init__(self, template_dir: str | Path = "src/templates"):
        self.template_dir = Path(template_dir)
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(),
        )

    def render(self, template_name: str, **kwargs: Any) -> str:
        """
        Render a template with the given context.

        Args:
            template_name: Name of the template file (e.g., 'intent.j2')
            **kwargs: Context variables for the template

        Returns:
            Rendered string
        """
        template = self.env.get_template(template_name)
        return template.render(**kwargs)


# Global instance
prompt_manager = PromptManager()
