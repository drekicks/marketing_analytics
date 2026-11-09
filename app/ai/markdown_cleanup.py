"""
Small fixes to model replies so Markdown renders in Streamlit and Chainlit.

Models sometimes write "##Key Strengths" (no space), which Markdown shows as
literal "##", or wrap the whole reply in a ```markdown code fence.
"""

import re

# A heading marker at the start of a line directly followed by a letter.
_HEADING_WITHOUT_SPACE = re.compile(r"^(\s{0,3}#{1,6})(?=[^\W\d_])")
_FENCE = re.compile(r"^\s{0,3}(```|~~~)")
_WRAPPING_FENCE = re.compile(
    r"\A```(?:markdown|md)?[ \t]*\n(?P<body>.*)\n```[ \t]*\Z",
    re.DOTALL | re.IGNORECASE,
)


def normalize_markdown(text: str) -> str:
    """Unwrap a reply fenced as a whole and add the space missing after heading markers."""
    wrapped = _WRAPPING_FENCE.match(text.strip())
    if wrapped and "```" not in wrapped.group("body"):
        text = wrapped.group("body")

    lines = []
    in_code_block = False
    for line in text.split("\n"):
        if _FENCE.match(line):
            in_code_block = not in_code_block
        elif not in_code_block:
            line = _HEADING_WITHOUT_SPACE.sub(r"\1 ", line)
        lines.append(line)

    return "\n".join(lines)
