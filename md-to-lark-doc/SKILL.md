---
name: md-to-lark-doc
description: Create Feishu/Lark cloud documents from local Markdown files. Use when the user provides a .md file and asks to 导入到飞书文档, 创建飞书文档, import Markdown to Lark/Feishu, or create a child/sub-document under an existing Lark document link. Supports Markdown import, local image upload/replacement at the original Markdown positions, and Mermaid, PlantUML, and SVG blocks as Lark whiteboards.
---

# Markdown To Lark Doc

## Overview

Create a Lark Docx document from a local Markdown file using `lark-cli docs +create --api-version v2 --doc-format markdown`. If the Markdown starts with YAML front matter, convert it into a readable metadata table. If it references local screenshots/images, upload those files to Lark and replace placeholders at the original Markdown positions, including inside table cells. If the Markdown contains Mermaid, PlantUML, or SVG diagrams, convert those blocks into `<whiteboard>` blocks so Lark creates editable whiteboards instead of plain code blocks.

## Required Skills And References

Before running Lark commands, read the matching current Lark skill files:

- Always read `lark-shared` for auth/profile/path rules.
- Always read `lark-doc` plus `references/lark-doc-create.md` and `references/lark-doc-md.md`.
- If the user provides a parent document link, read `lark-wiki` and `references/lark-wiki-node-get.md`.
- If you need to update or inspect whiteboards after creation, read `lark-whiteboard` and `references/lark-whiteboard-update.md`.

Prefer `--as user` and pass the user's requested `--profile` when provided.

## Workflow

1. Resolve the source `.md` path and read enough of it to confirm it is the intended file.
2. Choose the title:
   - Use the user's requested title when provided.
   - Otherwise use the first Markdown H1.
   - If no H1 exists, use the source filename stem.
3. Prepare the Markdown:
   - Run `scripts/prepare_lark_markdown.py <source.md> --out <tmp.md> --manifest <tmp.json>`.
   - The script converts top-of-file YAML front matter (`--- ... ---`) into a two-column Markdown table headed `元数据`; do not leave raw front matter in the imported document.
   - The script converts fenced `mermaid`, `plantuml`, `puml`, `svg`, and `xml`-with-SVG blocks into Lark `<whiteboard type="...">` XML blocks.
   - The script also converts standalone inline `<svg ...>...</svg>` blocks into `<whiteboard type="svg">`.
   - The script replaces local Markdown image references with stable placeholders and records them in `manifest.local_images`. This includes both `![alt](local.png)` and ordinary links to local image files such as `[截图](screenshot/a.png)`. HTTP/HTTPS images are left for Lark's Markdown importer.
4. Resolve the parent destination:
   - If no parent link is provided, create in `my_library` unless the user specifies another parent position or token.
   - If a parent link is provided, run `lark-cli wiki +node-get --as user --node-token '<url>' --format json` and use the returned `node_token` as `--parent-token`.
   - If `wiki +node-get` cannot resolve the URL because it is a plain Drive folder URL/token, use that folder token as `--parent-token`.
   - Do not invent hierarchy for a normal doc that is not in Wiki and cannot be used as a parent; report the limitation and create in `my_library` only after user approval.
5. Create the document:
   - Use `lark-cli docs +create --api-version v2 --doc-format markdown --title '<title>' --content @<tmp.md> --parent-token <node_or_folder_token> --profile <profile> --as user --format json`.
   - Use `--parent-position my_library` when no parent token is needed.
   - All `@file` paths must be relative to the current working directory.
6. Embed local images, if any:
   - If `manifest.local_image_count > 0`, run `scripts/embed_lark_local_images.py` after document creation:
     ```bash
     python3 .agents/skills/md-to-lark-doc/scripts/embed_lark_local_images.py \
       --doc '<doc_url_or_id>' \
       --manifest .codex_tmp/example.lark.json \
       --profile <profile> \
       --as user
     ```
   - The script uploads each local image with `docs +media-insert`, replaces the original placeholder with `<img src="...">`, and deletes the temporary appended upload blocks after all replacements succeed.
   - Use `--table-width 220` (default) for images detected in Markdown table rows and `--width 800` (default) for normal body images. Override these if the document needs different sizing.
   - If the script fails mid-run, it leaves temporary appended image blocks in place and reports their block IDs; do not delete them until the failed placeholder replacement is resolved.
7. Inspect the JSON result and image embedding result:
   - Return the document URL.
   - Report whether YAML front matter was converted and how many metadata fields were included.
   - Report how many visual blocks were converted and their types.
   - Report how many local images were uploaded/replaced and whether temporary appended upload blocks were cleaned up.
   - If `document.new_blocks` includes whiteboard blocks, preserve their `block_token` values for follow-up update/query work.

## YAML Front Matter Rules

- Only treat a leading `---` block at the very start of the file as front matter.
- Convert simple `key: value` fields into a Markdown table with columns `字段` and `值`.
- Preserve field order and render list-style continuation lines as semicolon-separated values.
- Keep the local Markdown source unchanged; only the prepared temporary Markdown is modified for import.

## Visual Block Rules

Recognized fenced languages:

- Mermaid: `mermaid`, `mmd`
- PlantUML: `plantuml`, `puml`
- SVG: `svg`, and `xml` or `html` when the fenced content contains an `<svg>` root

Keep non-diagram code fences as normal Markdown code blocks. Do not translate or rewrite diagram source unless Lark rejects it and a minimal syntax fix is necessary.

For SVG whiteboards, the SVG must be self-contained. Avoid remote images, scripts, filters, masks, clip paths, radial gradients, and other features likely to fail in Lark whiteboard rendering.

## Local Image Rules

- Treat `![alt](relative.png)` as an image to upload when the target is a local `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, or `.bmp`.
- Treat `[label](relative.png)` as an image upload too when the target is a local image file. This preserves common report tables where the screenshot column stores links like `[截图](screenshot/foo.png)`.
- Resolve relative image paths against the source Markdown file's directory, not the current shell directory.
- Preserve original placement by importing placeholders first and replacing those placeholders after document creation. Do not append images at the end as the final representation unless placeholder replacement fails and the user accepts that fallback.
- Keep HTTP/HTTPS images unchanged; Lark Markdown import can fetch network images directly.

## Command Templates

Prepare content:

```bash
python3 .agents/skills/md-to-lark-doc/scripts/prepare_lark_markdown.py \
  research/example.md \
  --out .codex_tmp/example.lark.md \
  --manifest .codex_tmp/example.lark.json
```

Create in personal library:

```bash
lark-cli docs +create \
  --profile personal --as user \
  --api-version v2 \
  --doc-format markdown \
  --title "Example" \
  --content @.codex_tmp/example.lark.md \
  --parent-position my_library \
  --format json
```

Embed local images after creation when the manifest reports `local_image_count > 0`:

```bash
python3 .agents/skills/md-to-lark-doc/scripts/embed_lark_local_images.py \
  --doc "https://example.feishu.cn/docx/..." \
  --manifest .codex_tmp/example.lark.json \
  --profile personal \
  --as user
```

Create under a parent document:

```bash
lark-cli wiki +node-get --profile personal --as user --node-token "https://..." --format json
lark-cli docs +create \
  --profile personal --as user \
  --api-version v2 \
  --doc-format markdown \
  --title "Example" \
  --content @.codex_tmp/example.lark.md \
  --parent-token "<node_token>" \
  --format json
```

## Failure Handling

- If auth fails, follow `lark-shared` split-flow authorization instructions.
- If `docs +create` rejects Markdown with embedded `<whiteboard>`, retry with a smaller test document to isolate the block, then fix only the failing visual block.
- If local image embedding reports missing files, fix the Markdown image path or place the file where the manifest expects it, then rerun `prepare_lark_markdown.py` and `embed_lark_local_images.py`.
- If local image embedding fails after upload but before replacement, use the reported temporary block IDs and placeholders to repair the document, then delete the temporary blocks only after table/paragraph images render at the original positions.
- If parent resolution returns `permission denied`, ask the user for access or create in `my_library` only with explicit approval.
- If the document is created but a visual block is empty or degraded, use the returned whiteboard token and `lark-whiteboard` to overwrite that board with the original Mermaid, PlantUML, or SVG source.
