import typing
import json
import os
import re


def load(file: str) -> dict[str, typing.Any]:
    path = os.path.join(os.path.dirname(__file__), file)
    with open(path, 'r') as f:
        content = f.read()

        # Remove comments (//...) for JSONC
        # This is unsafe if the double slashes are inside values (e.g. key: "http://example.com")
        # Should be safe for this package's use cases, otherwise just switch to a proper JSONC parser
        content = re.sub(r'//.*', '', content)

        return json.loads(content)
