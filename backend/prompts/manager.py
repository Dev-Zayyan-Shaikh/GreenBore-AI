import os


class PromptManager:
    """
    Manages loading and formatting prompt templates from files.
    """

    def __init__(self, prompts_dir: str | None = None) -> None:
        if prompts_dir is None:
            # Locate relative to the backend/ directory
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.prompts_dir = os.path.join(base_dir, "prompts")
        else:
            self.prompts_dir = prompts_dir

        self._cache: dict[str, str] = {}

    def get_prompt_template(self, filename: str) -> str:
        """
        Loads the prompt template file and returns its content.
        Caches it to avoid repeated file reads.
        """
        if filename in self._cache:
            return self._cache[filename]

        filepath = os.path.join(self.prompts_dir, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Prompt template file not found at: {filepath}")

        with open(filepath, encoding="utf-8") as f:
            content = f.read()

        self._cache[filename] = content
        return content

    def format_prompt(self, filename: str, **kwargs: str) -> str:
        """
        Loads the template and formats it with keywords.
        """
        template = self.get_prompt_template(filename)
        return template.format(**kwargs)
