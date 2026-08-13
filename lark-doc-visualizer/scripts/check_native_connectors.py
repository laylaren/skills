#!/usr/bin/env python3
"""Validate native Feishu whiteboard connectors in DSL or OpenAPI JSON."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


DSL_ARROWS = {"none", "arrow", "triangle", "circle", "diamond"}
OPENAPI_ARROWS = {
    "none",
    "line_arrow",
    "triangle_arrow",
    "circle_arrow",
    "diamond_arrow",
}
THIN_OPENAPI_WIDTHS = {"extra_narrow", "narrow"}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def walk(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def connector_nodes(payload: Any) -> list[dict[str, Any]]:
    return [
        item
        for item in walk(payload)
        if item.get("type") == "connector" and isinstance(item.get("connector"), dict)
    ]


def infer_format(connectors: list[dict[str, Any]]) -> str:
    if not connectors:
        return "unknown"
    body = connectors[0]["connector"]
    if "from" in body or "to" in body:
        return "dsl"
    if "start" in body or "end" in body:
        return "openapi"
    return "unknown"


def all_dsl_ids(payload: Any) -> set[str]:
    return {
        str(item["id"])
        for item in walk(payload)
        if item.get("type") != "connector" and item.get("id") is not None
    }


def validate_dsl(
    payload: Any, connectors: list[dict[str, Any]], errors: list[str]
) -> int:
    ids = all_dsl_ids(payload)
    directed = 0

    roots = [
        item
        for item in walk(payload)
        if item.get("version") == 2 and isinstance(item.get("nodes"), list)
    ]
    if not roots:
        errors.append("DSL document must contain {version: 2, nodes: [...]}.")
    else:
        root_connector_ids = {
            id(node)
            for root in roots
            for node in root["nodes"]
            if isinstance(node, dict) and node.get("type") == "connector"
        }
        for index, node in enumerate(connectors, 1):
            if id(node) not in root_connector_ids:
                errors.append(f"connector #{index} is nested; connectors must be top-level")

    for index, node in enumerate(connectors, 1):
        body = node["connector"]
        prefix = f"connector #{index} ({node.get('id', 'no-id')})"

        for endpoint in ("from", "to"):
            if endpoint not in body:
                errors.append(f"{prefix}: missing {endpoint}")
            elif isinstance(body[endpoint], str) and body[endpoint] not in ids:
                errors.append(f"{prefix}: {endpoint} references unknown node {body[endpoint]!r}")

        for field in ("startArrow", "endArrow"):
            if field not in body:
                errors.append(f"{prefix}: {field} must be explicit")
            elif body[field] not in DSL_ARROWS:
                errors.append(f"{prefix}: unsupported {field}={body[field]!r}")

        width = body.get("lineWidth")
        if not isinstance(width, (int, float)):
            errors.append(f"{prefix}: lineWidth must be explicit and numeric")
        elif not 0 < float(width) <= 1.5:
            errors.append(f"{prefix}: lineWidth {width} must be > 0 and <= 1.5")

        if body.get("startArrow", "none") != "none" or body.get("endArrow", "none") != "none":
            directed += 1

    return directed


def validate_openapi(connectors: list[dict[str, Any]], errors: list[str]) -> int:
    directed = 0
    for index, node in enumerate(connectors, 1):
        body = node["connector"]
        prefix = f"connector #{index} ({node.get('id', 'no-id')})"
        style = node.get("style") or {}
        width = style.get("border_width")
        if width not in THIN_OPENAPI_WIDTHS:
            errors.append(
                f"{prefix}: border_width must be extra_narrow or narrow; got {width!r}"
            )

        arrows: list[str] = []
        for endpoint in ("start", "end"):
            endpoint_data = body.get(endpoint)
            if not isinstance(endpoint_data, dict):
                errors.append(f"{prefix}: missing native {endpoint} endpoint")
                continue
            arrow = endpoint_data.get("arrow_style")
            if arrow not in OPENAPI_ARROWS:
                errors.append(f"{prefix}: unsupported {endpoint}.arrow_style={arrow!r}")
            else:
                arrows.append(arrow)

        if any(arrow != "none" for arrow in arrows):
            directed += 1

    return directed


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check native Feishu whiteboard connector arrows and widths."
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("--format", choices=("auto", "dsl", "openapi"), default="auto")
    parser.add_argument("--expected-connectors", type=int)
    parser.add_argument("--expected-directed", type=int)
    args = parser.parse_args()

    try:
        payload = read_json(args.input)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    errors: list[str] = []
    connectors = connector_nodes(payload)
    detected = infer_format(connectors)
    selected = detected if args.format == "auto" else args.format

    if not connectors:
        errors.append("no native connector nodes found")
        directed = 0
    elif selected == "dsl":
        directed = validate_dsl(payload, connectors, errors)
    elif selected == "openapi":
        directed = validate_openapi(connectors, errors)
    else:
        errors.append("could not infer connector format; pass --format dsl or openapi")
        directed = 0

    if args.expected_connectors is not None and len(connectors) != args.expected_connectors:
        errors.append(
            f"expected {args.expected_connectors} connectors; found {len(connectors)}"
        )
    if args.expected_directed is not None and directed != args.expected_directed:
        errors.append(f"expected {args.expected_directed} directed edges; found {directed}")

    print(f"format: {selected}")
    print(f"connectors: {len(connectors)}")
    print(f"directed: {directed}")

    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if errors:
        print(f"FAILED: {len(errors)} error(s)", file=sys.stderr)
        return 1

    print("OK: native connectors use explicit arrows and thin strokes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
