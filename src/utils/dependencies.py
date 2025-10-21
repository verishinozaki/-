from __future__ import annotations

import importlib.util
from typing import Mapping


def ensure_dependencies(required: Mapping[str, str]) -> None:
    """Ensure that the given Python packages are importable.

    Args:
        required: Mapping of package name to a short human friendly
            description of why the dependency is needed.

    Raises:
        SystemExit: If any of the packages are missing. Exits with a
            helpful message so the user can install the dependencies.
    """

    missing = [
        (name, description)
        for name, description in required.items()
        if importlib.util.find_spec(name) is None
    ]

    if not missing:
        return

    message_lines = [
        "以下の依存パッケージが見つかりませんでした:",
    ]
    for name, description in missing:
        if description:
            message_lines.append(f"  - {name}: {description}")
        else:
            message_lines.append(f"  - {name}")

    message_lines.append("次のコマンドを実行してインストールしてください:")
    message_lines.append("  pip install -r requirements.txt")

    raise SystemExit("\n".join(message_lines))
