#!/usr/bin/env python3
"""Validate a visualized Lark Doc snapshot against its source snapshot."""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any


HEADING_TAGS = {f"h{i}" for i in range(1, 10)}
RESOURCE_TAGS = {
    "img",
    "source",
    "whiteboard",
    "sheet",
    "bitable",
    "synced_reference",
    "synced_source",
    "task",
    "chat_card",
    "sub-page-list",
    "okr",
}
VISUAL_TAGS = {"table", "grid", "whiteboard", "figure"}
IDENTIFIER_ATTRS = {
    "user-id",
    "doc-id",
    "task-id",
    "chat-id",
    "sheet-id",
    "table-id",
    "src-token",
    "src-block-id",
}


def normalize_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def read_snapshot(path: Path) -> tuple[dict[str, Any], str]:
    raw = path.read_text(encoding="utf-8")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {}, raw

    candidates: list[Any] = [payload]
    if isinstance(payload, dict):
        candidates.extend([payload.get("data"), payload.get("document")])
        data = payload.get("data")
        if isinstance(data, dict):
            candidates.append(data.get("document"))

    for candidate in candidates:
        if isinstance(candidate, dict) and isinstance(candidate.get("content"), str):
            return payload, candidate["content"]
    raise ValueError(f"{path}: JSON does not contain data.document.content")


def parse_fragment(content: str, path: Path) -> ET.Element:
    # Lark fetch returns an XML fragment rather than one guaranteed root element.
    try:
        return ET.fromstring(f"<root>{content}</root>")
    except ET.ParseError as exc:
        raise ValueError(f"{path}: invalid XML content: {exc}") from exc


def iter_named(root: ET.Element, names: set[str]):
    for element in root.iter():
        if local_name(element.tag) in names:
            yield element


def element_text(element: ET.Element) -> str:
    return normalize_text("".join(element.itertext()))


def title(root: ET.Element) -> str:
    for element in iter_named(root, {"title"}):
        return element_text(element)
    return ""


def heading_sequence(root: ET.Element) -> list[tuple[str, str]]:
    return [
        (local_name(element.tag), element_text(element))
        for element in iter_named(root, HEADING_TAGS)
    ]


def is_subsequence(needles: list[Any], haystack: list[Any]) -> bool:
    cursor = iter(haystack)
    return all(any(candidate == needle for candidate in cursor) for needle in needles)


def attribute_counter(root: ET.Element, attr: str) -> Counter[str]:
    return Counter(
        value
        for element in root.iter()
        if (value := element.attrib.get(attr))
    )


def resource_counts(root: ET.Element) -> Counter[str]:
    return Counter(local_name(element.tag) for element in iter_named(root, RESOURCE_TAGS))


def visual_counts(root: ET.Element) -> Counter[str]:
    return Counter(local_name(element.tag) for element in iter_named(root, VISUAL_TAGS))


def structural_signature(root: ET.Element) -> list[tuple[str, str]]:
    signature: list[tuple[str, str]] = []
    for element in root.iter():
        name = local_name(element.tag)
        if name in {"root", "title"}:
            continue
        signature.append((name, element_text(element)))
    return signature


def revision_id(payload: dict[str, Any]) -> Any:
    data = payload.get("data") if isinstance(payload, dict) else None
    document = data.get("document") if isinstance(data, dict) else None
    return document.get("revision_id") if isinstance(document, dict) else None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare source/output JSON snapshots from lark-cli docs +fetch."
    )
    parser.add_argument("source_before", type=Path)
    parser.add_argument("output_after", type=Path)
    parser.add_argument("--source-after", type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []

    try:
        source_payload, source_content = read_snapshot(args.source_before)
        output_payload, output_content = read_snapshot(args.output_after)
        source_root = parse_fragment(source_content, args.source_before)
        output_root = parse_fragment(output_content, args.output_after)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    source_title = title(source_root)
    output_title = title(output_root)
    expected_title = f"{source_title}-可视化" if source_title else ""
    if not source_title:
        errors.append("source title is missing")
    if not output_title:
        errors.append("output title is missing")
    elif output_title != expected_title:
        errors.append(
            f"output title must be exactly {expected_title!r}; got {output_title!r}"
        )

    source_headings = heading_sequence(source_root)
    output_headings = heading_sequence(output_root)
    if not is_subsequence(source_headings, output_headings):
        errors.append("source heading tag/text order is not preserved in the output")

    for attr in ("href", *sorted(IDENTIFIER_ATTRS)):
        required = attribute_counter(source_root, attr)
        actual = attribute_counter(output_root, attr)
        missing = required - actual
        if missing:
            errors.append(f"missing source {attr} values: {dict(missing)}")

    source_resources = resource_counts(source_root)
    output_resources = resource_counts(output_root)
    for tag, count in source_resources.items():
        if output_resources[tag] < count:
            warnings.append(
                f"resource count decreased for <{tag}>: {count} -> {output_resources[tag]}; "
                "confirm this is a legitimate copy-token remap or intentional replacement"
            )

    source_visuals = visual_counts(source_root)
    output_visuals = visual_counts(output_root)
    visual_delta = sum(output_visuals.values()) - sum(source_visuals.values())
    if visual_delta <= 0:
        warnings.append(
            "no net increase in table/grid/whiteboard/figure blocks; confirm that the copy "
            "contains a substantive visual transformation"
        )

    if structural_signature(source_root) == structural_signature(output_root):
        errors.append("output differs only by title; no substantive transformation detected")

    if args.source_after:
        try:
            after_payload, after_content = read_snapshot(args.source_after)
        except (OSError, ValueError) as exc:
            errors.append(str(exc))
        else:
            if source_content != after_content:
                errors.append("source content changed between before and after snapshots")
            before_revision = revision_id(source_payload)
            after_revision = revision_id(after_payload)
            if (
                before_revision is not None
                and after_revision is not None
                and before_revision != after_revision
            ):
                errors.append(
                    f"source revision changed: {before_revision!r} -> {after_revision!r}"
                )

    print(f"source title: {source_title or '[missing]'}")
    print(f"output title: {output_title or '[missing]'}")
    print(f"source headings: {len(source_headings)}")
    print(f"output headings: {len(output_headings)}")
    print(f"source visuals: {dict(source_visuals)}")
    print(f"output visuals: {dict(output_visuals)}")

    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)

    if errors:
        print(f"FAILED: {len(errors)} error(s), {len(warnings)} warning(s)", file=sys.stderr)
        return 1
    print(f"OK: 0 errors, {len(warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

