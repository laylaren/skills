#!/usr/bin/env python3
"""Upload local Markdown images and replace placeholders in a Lark Doc.

Run after `docs +create` with the manifest emitted by prepare_lark_markdown.py.
The script uploads each local image to the document, reuses the resulting media
token at the placeholder's original location, then removes the temporary
appended upload blocks after all replacements succeed.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from xml.sax.saxutils import escape


IMG_RE = re.compile(r"<img\b[^>]*>")
ATTR_RE = re.compile(r'([\w:-]+)="([^"]*)"')


def run_lark(args: list[str], *, input_text: str | None = None) -> dict:
    completed = subprocess.run(
        args,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"command failed ({completed.returncode}): {' '.join(args)}\n"
            f"stdout:\n{completed.stdout}\n\nstderr:\n{completed.stderr}"
        )
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"command did not return JSON: {' '.join(args)}\n"
            f"stdout:\n{completed.stdout}\n\nstderr:\n{completed.stderr}"
        ) from exc


def lark_base(profile: str | None, identity: str) -> list[str]:
    args = ["lark-cli"]
    if profile:
        args += ["--profile", profile]
    args += ["docs"]
    return args


def ensure_cwd_relative(path: Path, staging_dir: Path) -> Path:
    path = path.expanduser().resolve()
    cwd = Path.cwd().resolve()
    try:
        return path.relative_to(cwd)
    except ValueError:
        staging_dir.mkdir(parents=True, exist_ok=True)
        staged = staging_dir / path.name
        if staged.resolve() != path:
            shutil.copy2(path, staged)
        return staged.relative_to(cwd)


def fetch_img_attrs(doc: str, block_id: str, profile: str | None, identity: str) -> dict[str, str]:
    args = lark_base(profile, identity) + [
        "+fetch",
        "--as",
        identity,
        "--api-version",
        "v2",
        "--doc",
        doc,
        "--detail",
        "with-ids",
        "--scope",
        "section",
        "--start-block-id",
        block_id,
        "--format",
        "json",
    ]
    result = run_lark(args)
    content = result.get("data", {}).get("document", {}).get("content", "")
    match = IMG_RE.search(content)
    if not match:
        raise RuntimeError(f"uploaded block {block_id} did not fetch as an <img> block")
    return dict(ATTR_RE.findall(match.group(0)))


def upload_image(
    doc: str,
    image_path: Path,
    profile: str | None,
    identity: str,
    width: int,
    staging_dir: Path,
) -> tuple[str, dict[str, str]]:
    relative_path = ensure_cwd_relative(image_path, staging_dir)
    args = lark_base(profile, identity) + [
        "+media-insert",
        "--as",
        identity,
        "--doc",
        doc,
        "--file",
        str(relative_path),
        "--type",
        "image",
        "--align",
        "center",
        "--width",
        str(width),
        "--format",
        "json",
    ]
    result = run_lark(args)
    block_id = result.get("data", {}).get("block_id")
    if not block_id:
        raise RuntimeError(f"media insert succeeded but returned no block_id: {json.dumps(result, ensure_ascii=False)}")
    attrs = fetch_img_attrs(doc, block_id, profile, identity)
    return block_id, attrs


def replacement_xml(attrs: dict[str, str], name: str) -> str:
    src = attrs.get("src")
    if not src:
        raise RuntimeError(f"uploaded image has no src token: {attrs}")
    width = attrs.get("width")
    height = attrs.get("height")
    pieces = [f'<img src="{escape(src)}"']
    if width:
        pieces.append(f' width="{escape(width)}"')
    if height:
        pieces.append(f' height="{escape(height)}"')
    pieces.append(f' name="{escape(name)}"')
    pieces.append("/>")
    return "".join(pieces)


def replace_placeholder(doc: str, placeholder: str, replacement: str, profile: str | None, identity: str) -> None:
    args = lark_base(profile, identity) + [
        "+update",
        "--as",
        identity,
        "--api-version",
        "v2",
        "--doc",
        doc,
        "--command",
        "str_replace",
        "--doc-format",
        "markdown",
        "--pattern",
        placeholder,
        "--content",
        replacement,
        "--format",
        "json",
    ]
    result = run_lark(args)
    if result.get("data", {}).get("result") not in {"success", "partial_success"}:
        raise RuntimeError(f"placeholder replacement failed: {json.dumps(result, ensure_ascii=False)}")


def delete_temp_blocks(doc: str, block_ids: list[str], profile: str | None, identity: str) -> None:
    if not block_ids:
        return
    args = lark_base(profile, identity) + [
        "+update",
        "--as",
        identity,
        "--api-version",
        "v2",
        "--doc",
        doc,
        "--command",
        "block_delete",
        "--block-id",
        ",".join(block_ids),
        "--format",
        "json",
    ]
    result = run_lark(args)
    if result.get("data", {}).get("result") != "success":
        raise RuntimeError(f"temporary block cleanup failed: {json.dumps(result, ensure_ascii=False)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--doc", required=True, help="Lark docx URL or document_id")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--profile")
    parser.add_argument("--as", dest="identity", default="user", choices=["user", "bot"])
    parser.add_argument("--width", type=int, default=800, help="display width for normal images")
    parser.add_argument("--table-width", type=int, default=220, help="display width for images whose placeholder is in a Markdown table row")
    parser.add_argument("--staging-dir", type=Path, default=Path(".codex_tmp/lark-local-images"))
    parser.add_argument("--keep-temp-blocks", action="store_true", help="do not delete the appended upload blocks")
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    images = manifest.get("local_images", [])
    if not images:
        print(json.dumps({"ok": True, "local_image_count": 0, "replaced": 0}, ensure_ascii=False))
        return 0

    missing = [image for image in images if not image.get("exists")]
    if missing:
        for image in missing:
            print(f"missing local image: {image.get('target')} -> {image.get('resolved_path')}", file=sys.stderr)
        return 2

    uploaded_blocks: list[str] = []
    replaced: list[dict[str, object]] = []
    try:
        for image in images:
            image_path = Path(str(image["resolved_path"]))
            width = args.table_width if image.get("in_table") else args.width
            block_id, attrs = upload_image(args.doc, image_path, args.profile, args.identity, width, args.staging_dir)
            uploaded_blocks.append(block_id)
            replacement = replacement_xml(attrs, image_path.name)
            replace_placeholder(args.doc, str(image["placeholder"]), replacement, args.profile, args.identity)
            replaced.append(
                {
                    "placeholder": image["placeholder"],
                    "path": str(image_path),
                    "block_id": block_id,
                    "src": attrs.get("src"),
                    "width": attrs.get("width"),
                    "height": attrs.get("height"),
                }
            )
    except Exception:
        print(
            json.dumps(
                {
                    "ok": False,
                    "replaced": len(replaced),
                    "temp_blocks_left": uploaded_blocks,
                    "message": "not deleting temporary image blocks because an error occurred",
                },
                ensure_ascii=False,
                indent=2,
            ),
            file=sys.stderr,
        )
        raise

    if not args.keep_temp_blocks:
        delete_temp_blocks(args.doc, uploaded_blocks, args.profile, args.identity)

    print(
        json.dumps(
            {
                "ok": True,
                "local_image_count": len(images),
                "replaced": len(replaced),
                "deleted_temp_blocks": 0 if args.keep_temp_blocks else len(uploaded_blocks),
                "images": replaced,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
