"""Read-only catalog for the vscode-prompts library."""

import base64
from pathlib import Path
from typing import Any

import yaml


def default_library_root() -> Path:
    """Return the repository's vscode-prompts directory."""
    return Path(__file__).resolve().parents[2] / "vscode-prompts"


def _item_id(relative_path: str) -> str:
    return base64.urlsafe_b64encode(relative_path.encode()).decode().rstrip("=")


def _decode_item_id(item_id: str) -> str:
    padding = "=" * (-len(item_id) % 4)
    return base64.urlsafe_b64decode(item_id + padding).decode()


def _parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    if not content.startswith("---\n"):
        return {}, content

    marker = content.find("\n---\n", 4)
    if marker == -1:
        return {}, content

    metadata = yaml.safe_load(content[4:marker]) or {}
    if not isinstance(metadata, dict):
        metadata = {}
    return metadata, content[marker + 5 :]


def _kind(relative_path: Path) -> str:
    parts = set(relative_path.parts)
    if "agents" in parts:
        return "agents"
    if "prompts" in parts:
        return "prompts"
    if "skills" in parts:
        return "skills"
    if "instructions" in parts:
        return "instructions"
    if "hooks" in parts:
        return "hooks"
    return "other"


def list_library(root: Path | None = None) -> list[dict[str, Any]]:
    """Return metadata for readable files in the prompt library."""
    library_root = (root or default_library_root()).resolve()
    if not library_root.exists():
        return []

    items = []
    for path in sorted(library_root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".md", ".json"}:
            continue
        if path.name.casefold() == "readme.md":
            continue
        relative = path.relative_to(library_root)
        content = path.read_text(encoding="utf-8")
        metadata, body = _parse_frontmatter(content)
        name = metadata.get("name") or metadata.get("title") or path.stem
        description = metadata.get("description") or next(
            (line.lstrip("# ").strip() for line in body.splitlines() if line.strip()),
            "",
        )
        items.append(
            {
                "id": _item_id(relative.as_posix()),
                "name": str(name),
                "description": str(description),
                "kind": _kind(relative),
                "path": relative.as_posix(),
                "vscode_url": f"vscode://file/{path}",
            }
        )
    return items


def get_library_item(item_id: str, root: Path | None = None) -> dict[str, Any]:
    """Return one library item, rejecting paths outside the library root."""
    library_root = (root or default_library_root()).resolve()
    relative = _decode_item_id(item_id)
    path = (library_root / relative).resolve()
    if not path.is_relative_to(library_root) or not path.is_file():
        raise FileNotFoundError(relative)

    content = path.read_text(encoding="utf-8")
    metadata, body = _parse_frontmatter(content)
    return {
        "id": item_id,
        "name": str(metadata.get("name") or metadata.get("title") or path.stem),
        "kind": _kind(path.relative_to(library_root)),
        "path": relative,
        "vscode_url": f"vscode://file/{path}",
        "metadata": metadata,
        "content": body,
    }
