#!/usr/bin/env python3
"""Lightweight checks for Markdown visualization outputs."""

from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
MERMAID_START_RE = re.compile(r"^```mermaid[ \t]*$", re.MULTILINE)
MERMAID_BLOCK_RE = re.compile(
    r"^```mermaid[ \t]*\n(.*?)^```[ \t]*$",
    re.MULTILINE | re.DOTALL,
)
SVG_BLOCK_RE = re.compile(
    r"<svg\b(?P<attrs>[^>]*)>(?P<body>.*?)</svg>",
    re.IGNORECASE | re.DOTALL,
)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text()


def headings(markdown: str) -> list[str]:
    return [match.group(2).strip() for match in HEADING_RE.finditer(markdown)]


def count_visual_markers(markdown: str) -> dict[str, int]:
    return {
        "tables": len(re.findall(r"^\|.+\|\s*$", markdown, re.MULTILINE)),
        "mermaid_blocks": len(MERMAID_START_RE.findall(markdown)),
        "svg_blocks": len(SVG_BLOCK_RE.findall(markdown)),
    }


def first_mermaid_statement(block: str) -> str:
    for line in block.splitlines():
        statement = line.strip()
        if statement and not statement.startswith("%%"):
            return statement
    return ""


def check_mermaid_policy(markdown: str, issues: list[str]) -> None:
    starts = len(MERMAID_START_RE.findall(markdown))
    blocks = list(MERMAID_BLOCK_RE.finditer(markdown))
    if starts != len(blocks):
        issues.append(
            "One or more Mermaid fences are unclosed or malformed; "
            f"found {starts} starts but {len(blocks)} complete blocks."
        )

    for index, match in enumerate(blocks, start=1):
        statement = first_mermaid_statement(match.group(1))
        if statement != "sequenceDiagram":
            diagram_type = statement.split(maxsplit=1)[0] if statement else "(empty)"
            issues.append(
                f"Mermaid block {index} starts with {diagram_type!r}; "
                "only technical sequenceDiagram blocks are allowed. "
                "Render every other diagram as inline SVG."
            )


def check_svg_policy(markdown: str, issues: list[str], warnings: list[str]) -> None:
    seen_ids: dict[str, int] = {}
    forbidden_tags = (
        "foreignObject",
        "image",
        "script",
        "style",
        "filter",
        "mask",
        "clipPath",
        "linearGradient",
        "radialGradient",
    )

    for index, match in enumerate(SVG_BLOCK_RE.finditer(markdown), start=1):
        attrs = match.group("attrs")
        body = match.group("body")
        svg_text = match.group(0)
        root: ET.Element | None = None

        try:
            root = ET.fromstring(svg_text)
        except ET.ParseError as error:
            issues.append(f"SVG block {index} is not valid XML: {error}.")

        required_checks = {
            'xmlns="http://www.w3.org/2000/svg"': re.search(
                r"""\bxmlns\s*=\s*["']http://www\.w3\.org/2000/svg["']""",
                attrs,
                re.IGNORECASE,
            ),
            'role="img"': re.search(
                r"""\brole\s*=\s*["']img["']""", attrs, re.IGNORECASE
            ),
            "viewBox": re.search(
                r"""\bviewBox\s*=\s*["']\s*-?(?:\d+(?:\.\d+)?|\.\d+)\s+-?(?:\d+(?:\.\d+)?|\.\d+)\s+(?:\d+(?:\.\d+)?|\.\d+)\s+(?:\d+(?:\.\d+)?|\.\d+)\s*["']""",
                attrs,
                re.IGNORECASE,
            ),
            "aria-label": re.search(
                r"""\baria-label\s*=\s*["'][^"']+["']""", attrs, re.IGNORECASE
            ),
            "<title>": re.search(r"<title\b[^>]*>.*?</title>", body, re.IGNORECASE | re.DOTALL),
            "<desc>": re.search(r"<desc\b[^>]*>.*?</desc>", body, re.IGNORECASE | re.DOTALL),
        }
        missing = [label for label, found in required_checks.items() if not found]
        if missing:
            issues.append(
                f"SVG block {index} is missing required accessibility or compatibility "
                f"markers: {', '.join(missing)}."
            )

        if re.search(r"#f8fafc", body, re.IGNORECASE):
            issues.append(
                f"SVG block {index} uses the retired light-gray canvas color #f8fafc; "
                "keep the SVG canvas transparent and remove the full-canvas background."
            )

        if re.search(
            r"<(?:text|tspan)\b[^>]*>[^<]*(?:N/A|\bNA\b|未知|缺失|未测量|尚未完成|未完成核算|未核算)[^<]*</(?:text|tspan)>",
            body,
            re.IGNORECASE,
        ):
            warnings.append(
                f"SVG block {index} labels missing data; manually verify that its "
                "data-mark region is empty, its missing-state label is outside the plot "
                "area, and no bar, point, slice, bubble, or area implies a value."
            )

        if root is not None:
            view_box_value = root.attrib.get("viewBox", "")
            try:
                min_x, min_y, canvas_width, canvas_height = (
                    float(part) for part in view_box_value.split()
                )
            except (TypeError, ValueError):
                min_x = min_y = canvas_width = canvas_height = None

            if canvas_width is not None:
                for element in root.iter():
                    if element.tag.rsplit("}", 1)[-1].lower() != "rect":
                        continue
                    try:
                        x = float(element.attrib.get("x", "0"))
                        y = float(element.attrib.get("y", "0"))
                        width = float(element.attrib["width"])
                        height = float(element.attrib["height"])
                    except (KeyError, ValueError):
                        continue
                    fill = element.attrib.get("fill", "black").strip().lower()
                    opacity = element.attrib.get("opacity", "1").strip()
                    fill_opacity = element.attrib.get("fill-opacity", "1").strip()
                    visible_fill = (
                        fill not in {"none", "transparent"}
                        and opacity not in {"0", "0.0"}
                        and fill_opacity not in {"0", "0.0"}
                    )
                    covers_canvas = all(
                        abs(left - right) < 1e-9
                        for left, right in (
                            (x, min_x),
                            (y, min_y),
                            (width, canvas_width),
                            (height, canvas_height),
                        )
                    )
                    if visible_fill and covers_canvas:
                        issues.append(
                            f"SVG block {index} contains a filled rectangle covering the "
                            "entire viewBox; remove the canvas background and keep it transparent."
                        )
                        break

        if re.search(r"\b(?:href|xlink:href)\s*=", body, re.IGNORECASE):
            issues.append(
                f"SVG block {index} contains href/xlink:href; external or linked assets "
                "are not allowed in self-contained Markdown SVGs."
            )

        for tag in forbidden_tags:
            if re.search(fr"<{tag}\b", body, re.IGNORECASE):
                issues.append(
                    f"SVG block {index} uses forbidden <{tag}>; replace it with "
                    "Feishu/Lark-compatible standard SVG primitives."
                )

        for id_match in re.finditer(r"""\bid\s*=\s*["']([^"']+)["']""", body):
            svg_id = id_match.group(1)
            if svg_id in seen_ids:
                issues.append(
                    f"SVG id {svg_id!r} is reused in blocks {seen_ids[svg_id]} and "
                    f"{index}; IDs must be document-unique."
                )
            else:
                seen_ids[svg_id] = index


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: check_visualized_md.py <source.md> <output.md>", file=sys.stderr)
        return 2

    source = Path(sys.argv[1]).expanduser().resolve()
    output = Path(sys.argv[2]).expanduser().resolve()
    issues: list[str] = []
    warnings: list[str] = []

    if not source.exists():
        issues.append(f"Source file does not exist: {source}")
    if not output.exists():
        issues.append(f"Output file does not exist: {output}")
    if issues:
        for issue in issues:
            print(f"ERROR: {issue}")
        return 1

    if source.suffix.lower() != ".md":
        warnings.append(f"Source does not end with .md: {source.name}")
    if output.suffix.lower() != ".md":
        issues.append(f"Output does not end with .md: {output.name}")
    if not output.stem.endswith("-可视化"):
        issues.append(f"Output filename should end with -可视化.md: {output.name}")
    if source == output:
        issues.append("Output path must be different from source path.")

    source_text = read_text(source)
    output_text = read_text(output)

    if len(output_text.strip()) < max(200, int(len(source_text.strip()) * 0.35)):
        warnings.append("Output is much shorter than source; verify content was not summarized away.")

    visual_markers = count_visual_markers(output_text)
    if sum(visual_markers.values()) == 0:
        warnings.append("No tables, Mermaid blocks, or SVG blocks detected.")

    source_headings = headings(source_text)
    output_headings = set(headings(output_text))
    missing_headings = [heading for heading in source_headings if heading not in output_headings]
    if source_headings and missing_headings:
        preview = "; ".join(missing_headings[:8])
        warnings.append(f"Some source headings are missing from output: {preview}")

    check_mermaid_policy(output_text, issues)
    check_svg_policy(output_text, issues, warnings)

    for issue in issues:
        print(f"ERROR: {issue}")
    for warning in warnings:
        print(f"WARNING: {warning}")

    print(
        "Visual markers: "
        f"{visual_markers['tables']} table lines, "
        f"{visual_markers['mermaid_blocks']} Mermaid blocks, "
        f"{visual_markers['svg_blocks']} SVG blocks"
    )

    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
