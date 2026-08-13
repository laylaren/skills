#!/usr/bin/env python3
"""Prepare Markdown for Lark Doc creation.

Transforms YAML front matter into a readable Markdown table, converts diagram
blocks into Lark whiteboards, and marks local images for post-create upload.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path


FENCE_RE = re.compile(r"(?ms)^([ \t]*)(`{3,}|~{3,})([^\n]*)\n(.*?)(?:\n\1\2[ \t]*$)")
SVG_RE = re.compile(r"(?is)(<svg\b[^>]*>.*?</svg>)")

MERMAID_LANGS = {"mermaid", "mmd"}
PLANTUML_LANGS = {"plantuml", "puml"}
SVG_FENCE_LANGS = {"svg"}
SVG_CONTAINER_LANGS = {"xml", "html"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}
LOCAL_IMAGE_PLACEHOLDER_PREFIX = "LARK_LOCAL_IMAGE"


@dataclass(frozen=True)
class ProtectedRange:
    start: int
    end: int


def protected_ranges(markdown: str) -> list[ProtectedRange]:
    ranges: list[ProtectedRange] = []
    for match in re.finditer(r"(?ms)^([ \t]*)(`{3,}|~{3,})([^\n]*)\n(.*?)(?:\n\1\2[ \t]*$)", markdown):
        ranges.append(ProtectedRange(match.start(), match.end()))
    for match in re.finditer(r'(?is)<whiteboard\b[^>]*>.*?</whiteboard>', markdown):
        ranges.append(ProtectedRange(match.start(), match.end()))
    return ranges


def in_protected_range(pos: int, ranges: list[ProtectedRange]) -> bool:
    return any(item.start <= pos < item.end for item in ranges)


def split_front_matter(markdown: str) -> tuple[str, str] | None:
    lines = markdown.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return None

    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            front_matter = "".join(lines[1:index])
            body = "".join(lines[index + 1 :])
            return front_matter, body
    return None


def is_top_level_yaml_field(line: str) -> bool:
    if not line or line[0].isspace() or line.lstrip().startswith("#"):
        return False
    if ":" not in line:
        return False
    key, _value = line.split(":", 1)
    return bool(key.strip())


def normalize_front_matter_value(first_value: str, continuation: list[str]) -> str:
    value = first_value.strip()
    extra = [line.strip() for line in continuation if line.strip()]

    if value in {"|", ">"}:
        value = " / ".join(extra)
    elif extra:
        cleaned_extra: list[str] = []
        for line in extra:
            if line.startswith("- "):
                cleaned_extra.append(line[2:].strip())
            else:
                cleaned_extra.append(line)
        value = "; ".join(([value] if value else []) + cleaned_extra)

    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        value = value[1:-1]
    return value


def parse_front_matter_rows(front_matter: str) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    current_key = ""
    current_value = ""
    continuation: list[str] = []

    def flush() -> None:
        nonlocal current_key, current_value, continuation
        if current_key:
            rows.append((current_key, normalize_front_matter_value(current_value, continuation)))
        current_key = ""
        current_value = ""
        continuation = []

    for raw_line in front_matter.splitlines():
        if is_top_level_yaml_field(raw_line):
            flush()
            key, value = raw_line.split(":", 1)
            current_key = key.strip()
            current_value = value.strip()
            continuation = []
        elif current_key and raw_line.strip():
            continuation.append(raw_line)

    flush()
    return rows


def escape_table_cell(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ").strip()


def front_matter_to_table(rows: list[tuple[str, str]]) -> str:
    table = ["## 元数据", "", "| 字段 | 值 |", "|---|---|"]
    for key, value in rows:
        table.append(f"| {escape_table_cell(key)} | {escape_table_cell(value)} |")
    return "\n".join(table) + "\n\n"


def convert_front_matter(markdown: str) -> tuple[str, dict[str, object]]:
    split = split_front_matter(markdown)
    if not split:
        return markdown, {"converted": False, "field_count": 0}

    front_matter, body = split
    rows = parse_front_matter_rows(front_matter)
    if not rows:
        return body.lstrip("\n"), {"converted": False, "field_count": 0}

    converted = front_matter_to_table(rows) + body.lstrip("\n")
    return converted, {"converted": True, "field_count": len(rows)}


def first_language(info: str) -> str:
    return (info.strip().split(None, 1)[0].lower() if info.strip() else "")


def is_svg(text: str) -> bool:
    return bool(SVG_RE.search(text))


def wrap_whiteboard(kind: str, source: str) -> str:
    source = source.strip()
    return f'<whiteboard type="{kind}">\n{source}\n</whiteboard>'


def convert_fences(markdown: str) -> tuple[str, list[dict[str, object]]]:
    manifest: list[dict[str, object]] = []

    def repl(match: re.Match[str]) -> str:
        indent, fence, info, body = match.groups()
        lang = first_language(info)
        kind = ""

        if lang in MERMAID_LANGS:
            kind = "mermaid"
        elif lang in PLANTUML_LANGS:
            kind = "plantuml"
        elif lang in SVG_FENCE_LANGS or (lang in SVG_CONTAINER_LANGS and is_svg(body)):
            kind = "svg"

        if not kind:
            return match.group(0)

        manifest.append(
            {
                "index": len(manifest) + 1,
                "source": "fenced_code",
                "language": lang,
                "whiteboard_type": kind,
                "chars": len(body.strip()),
            }
        )
        return wrap_whiteboard(kind, body)

    return FENCE_RE.sub(repl, markdown), manifest


def convert_inline_svg(markdown: str, manifest: list[dict[str, object]]) -> str:
    ranges = protected_ranges(markdown)

    output: list[str] = []
    cursor = 0
    for match in SVG_RE.finditer(markdown):
        if in_protected_range(match.start(), ranges):
            continue
        before = markdown[cursor : match.start()]
        after_start = match.end()
        output.append(before)
        svg = match.group(1)
        manifest.append(
            {
                "index": len(manifest) + 1,
                "source": "inline_svg",
                "language": "svg",
                "whiteboard_type": "svg",
                "chars": len(svg.strip()),
            }
        )
        output.append(wrap_whiteboard("svg", svg))
        cursor = after_start

    if not output:
        return markdown

    output.append(markdown[cursor:])
    return "".join(output)


def is_remote_or_special_url(target: str) -> bool:
    lower = target.lower()
    return bool(re.match(r"^[a-z][a-z0-9+.-]*:", lower)) or lower.startswith("#")


def split_markdown_link_target(raw_target: str) -> str:
    target = raw_target.strip()
    if target.startswith("<") and ">" in target:
        return target[1 : target.index(">")].strip()
    if not target:
        return target
    # Markdown allows an optional title after whitespace. Paths with spaces
    # should be written as <path with spaces.png>.
    return target.split(None, 1)[0].strip()


def is_local_image_target(target: str) -> bool:
    if not target or is_remote_or_special_url(target):
        return False
    path_part = target.split("?", 1)[0].split("#", 1)[0]
    return Path(path_part).suffix.lower() in IMAGE_EXTENSIONS


def resolve_local_image_path(target: str, source: Path) -> Path:
    path = Path(target)
    if path.is_absolute():
        return path
    return (source.parent / path).resolve()


def is_table_line(markdown: str, pos: int) -> bool:
    line_start = markdown.rfind("\n", 0, pos) + 1
    line_end = markdown.find("\n", pos)
    if line_end == -1:
        line_end = len(markdown)
    line = markdown[line_start:line_end].strip()
    return line.startswith("|") and line.endswith("|")


def convert_local_images(markdown: str, source: Path) -> tuple[str, list[dict[str, object]]]:
    """Replace local Markdown image/link references with stable placeholders.

    Lark's Markdown import can fetch HTTP images, but not local files. We keep
    local images at their original text positions by importing placeholders first
    and replacing them with uploaded image tokens after document creation.

    Supported forms:
    - ![alt](relative/or/absolute.png)
    - [label](relative/or/absolute.png) for local image extensions
    """

    ranges = protected_ranges(markdown)
    image_manifest: list[dict[str, object]] = []
    pattern = re.compile(r"(!?)\[([^\]\n]*)\]\(([^)\n]+)\)")

    output: list[str] = []
    cursor = 0
    for match in pattern.finditer(markdown):
        if in_protected_range(match.start(), ranges):
            continue

        bang, label, raw_target = match.groups()
        target = split_markdown_link_target(raw_target)
        if not is_local_image_target(target):
            continue

        index = len(image_manifest) + 1
        placeholder = f"{LOCAL_IMAGE_PLACEHOLDER_PREFIX}_{index:04d}"
        resolved = resolve_local_image_path(target, source)
        image_manifest.append(
            {
                "index": index,
                "placeholder": placeholder,
                "syntax": "image" if bang else "link",
                "label": label.strip(),
                "target": target,
                "resolved_path": str(resolved),
                "exists": resolved.exists(),
                "in_table": is_table_line(markdown, match.start()),
            }
        )
        output.append(markdown[cursor : match.start()])
        output.append(placeholder)
        cursor = match.end()

    if not image_manifest:
        return markdown, []

    output.append(markdown[cursor:])
    converted = normalize_adjacent_image_placeholders("".join(output))
    return converted, image_manifest


def normalize_adjacent_image_placeholders(markdown: str) -> str:
    placeholder = rf"{LOCAL_IMAGE_PLACEHOLDER_PREFIX}_\d{{4}}"
    pattern = re.compile(rf"({placeholder})\s*/\s*({placeholder})")
    previous = None
    current = markdown
    while current != previous:
        previous = current
        current = pattern.sub(r"\1<br/>\2", current)
    return current


def infer_title(markdown: str, source: Path) -> str:
    for line in markdown.splitlines():
        match = re.match(r"^#\s+(.+?)\s*$", line)
        if match:
            return match.group(1).strip()
    return source.stem


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()

    markdown = args.source.read_text(encoding="utf-8")
    converted, front_matter_manifest = convert_front_matter(markdown)
    converted, manifest = convert_fences(converted)
    converted = convert_inline_svg(converted, manifest)
    converted, local_images = convert_local_images(converted, args.source.resolve())

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(converted, encoding="utf-8")
    args.manifest.write_text(
        json.dumps(
            {
                "source": str(args.source),
                "output": str(args.out),
                "title": infer_title(markdown, args.source),
                "front_matter": front_matter_manifest,
                "visual_block_count": len(manifest),
                "visual_blocks": manifest,
                "local_image_count": len(local_images),
                "local_images": local_images,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    front_matter_note = ""
    if front_matter_manifest["converted"]:
        front_matter_note = f", {front_matter_manifest['field_count']} metadata field(s)"
    image_note = ""
    if local_images:
        missing = sum(1 for image in local_images if not image["exists"])
        image_note = f", {len(local_images)} local image placeholder(s)"
        if missing:
            image_note += f", {missing} missing"
    print(f"wrote {args.out} ({len(manifest)} visual block(s){front_matter_note}{image_note})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
