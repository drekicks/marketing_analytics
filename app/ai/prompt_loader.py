from app.config.paths import PROMPT_DIR

def load_prompt(prompt_name: str):
    prompt_path = PROMPT_DIR / f'{prompt_name}.md'

    if not prompt_path.exists():
        raise FileNotFoundError(
            f"Prompt file '{prompt_name}.md' not found as {prompt_path}."
        )

    with prompt_path.open('r', encoding="utf-8") as file:
        return file.read()

