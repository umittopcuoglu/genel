from pathlib import Path


class PromptLoader:
    PROMPT_DIR = Path(__file__).parent / "prompts"

    @staticmethod
    def load(agent_name: str, version: str = "current") -> str:
        if version == "current":
            version = "v1.0.0"

        prompt_path = PromptLoader.PROMPT_DIR / version / f"{agent_name}.txt"

        if not prompt_path.exists():
            raise FileNotFoundError(
                f"Prompt not found: {prompt_path}"
            )

        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
