import re

def build_prompt(template: str, variables: dict) -> str:
    final_prompt = template

    for variable_name, variable_value in variables.items():
        placeholder = "{{" + variable_name + "}}"
        final_prompt = final_prompt.replace(placeholder, str(variable_value))

    unresolved_variables = re.findall(
        r"\{\{([a-zA-Z_][a-zA-Z0-9_]*)\}\}",final_prompt
    )

    if unresolved_variables:
        raise ValueError(f"Unresolved variables: {unresolved_variables}")

    return final_prompt

