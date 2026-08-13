---
name: lark-doc-visualizer
description: Visualize an existing Feishu/Lark Doc from a docx, doc, wiki, or doubao.com document link without changing the source. Use when the user provides a Feishu/Lark document URL or token and asks for 文档可视化, 可视化文档, 图表化, 数据图表, 转成表格, 流程图, 架构图, 时间线, 路线图, 象限图, 饼图, 环形图, 柱状图, 折线图, 漏斗图, 热力图, or a new Feishu document named 原文档标题-可视化. First read the source and present a section-by-section visualization plan, then wait for explicit user confirmation in a later message before creating the copy or producing visuals. After confirmation, create and edit only a copied document through lark-cli; use native Lark tables for exact lookup, native Lark whiteboard nodes and bound arrow connectors for direction-bearing diagrams, direct SVG only for charts and non-directional graphics, and Mermaid sequenceDiagram only for technical interaction sequences.
---

# Lark Doc Visualizer

## Goal

Create a scannable Feishu document named `<source-title>-可视化` while preserving the source's facts, meaning, terminology, numbers, qualifications, links, resources, conclusions, and heading order. Never edit the source document.

Use only `lark-cli` and the relevant Feishu/Lark skills. Never use Computer Use, Chrome, or the web UI for Feishu operations.

## Required skill routing

Before running commands, read and follow the currently installed versions of these skills and every reference they mark mandatory for the intended operation:

1. `lark-shared` for authentication, identity, path, JSON-envelope, and confirmation rules.
2. `lark-drive` for URL inspection, destination-folder handling, and `drive files copy`.
3. `lark-doc` for `docs +fetch`, XML syntax and style, block updates, and the document-to-whiteboard workflow.
4. `lark-whiteboard` for native-node diagrams and whenever a whiteboard must be exported, previewed, or updated after creation. For a direction-bearing diagram, read its DSL route, schema, connector rules, and the matching scene guide completely.

If an active skill or runtime policy requires a SubAgent for a complex whiteboard, follow that rule only when delegation is permitted. Otherwise keep the visual simple enough for an inline SVG insertion or explain the limitation; do not bypass the active policy.

## Output contract

- Treat planning and production as two separate user-visible phases. Before explicit approval of the presented plan, allow only read-only Feishu inspection plus local snapshots and ledgers needed to prepare that plan.
- Do not create a destination folder, copy a document, generate production SVG/DSL/Mermaid assets, or run any Feishu write before the approval gate is satisfied.
- Keep the source untouched and create a Drive copy before any write.
- Name the copy `<source-title>-可视化`.
- Use a destination folder supplied by the user. If none is supplied, reuse an exact-name root folder `可视化文档`; create it in the user's Drive root only if it does not exist.
- Store snapshots, ledgers, SVG drafts, DSL/OpenAPI JSON, and previews under `.tmp/lark-doc-visualizer-<timestamp>/`; do not place process files in the project root.
- Return the copied document's URL, not only a token.

## Workflow

### 1. Resolve and read the source

1. Verify `lark-cli` and user authentication as required by `lark-shared`.
2. Resolve the supplied link with `lark-cli drive +inspect --url '<url>' --as user`. For a wiki link, use the returned underlying token and type. Continue only for `doc` or `docx`; route other underlying types to their corresponding skill.
3. Save a full pre-write snapshot:

   ```bash
   lark-cli docs +fetch --doc '<source-url>' --detail full --format json \
     > .tmp/lark-doc-visualizer-<timestamp>/source-before.json
   ```

4. Read the complete document. For long documents, first fetch the outline, then read every section in order with `--scope section`; do not visualize from an outline or partial excerpt alone.
5. Record the source title, canonical token/type, revision ID, heading order, links, embedded resources, and any source-defined visual style.

### 2. Build a visual inventory before writing

Classify every section or candidate by its primary reading task:

- prose;
- native Lark table;
- native-node whiteboard for any diagram whose meaning depends on arrows or connection direction;
- inline SVG whiteboard for quantitative charts and non-directional graphics;
- Mermaid `sequenceDiagram` whiteboard for technical interaction sequences.

Use at most two complementary forms for one information set. Do not repeat the same content as long prose, a full table, and a fully labeled chart unless each form serves a distinct reading task.

For every quantitative candidate:

1. Create a data ledger containing dimension, exact value, unit, denominator, series, time basis, source wording, uncertainty, and missing-value state.
2. Read [`references/chart-selection.md`](references/chart-selection.md) completely.
3. Select the simplest valid chart that answers one clear question.
4. Keep prose or a table if prerequisites are missing or inconsistent.
5. Mark exact deterministic sums, differences, ratios, or percentages as `计算值`. Never estimate, interpolate, or turn missing values into zero.

Do not draw production visuals in this phase. The inventory is a proposal until the user confirms it.

### 3. Present the visualization plan and stop for confirmation

Before any production work, send the user a concise visualization plan in source heading order. Include:

- source title and the promise that the source will remain untouched;
- proposed output title and destination-folder behavior;
- a section-by-section table with `原章节`, `处理方式`, `可视化形式`, `要解决的阅读问题`, and `必须保留的信息/限定条件`;
- the planned number of native tables, native-node whiteboards, direct SVG whiteboards, and Mermaid sequence diagrams;
- for directional diagrams, the main nodes and semantic edges or loops that will be preserved;
- for quantitative visuals, units, denominators, missing-value treatment, and any value marked `计算值`;
- any genuine ambiguity, unsupported visual candidate, or design choice that needs user attention.

End with an explicit approval request such as: `请确认这份可视化规划；你确认后，我才会创建副本并开始正式制作。`

This is a mandatory stop point:

- End the turn after presenting the plan. Do not continue tool work in the same turn.
- The user's original visualization request does not count as approval because it preceded the plan.
- Proceed only when the user sends an explicit approval after seeing the current plan, such as `确认`, `可以，按这个方案做`, or an unambiguous equivalent.
- If the user requests changes, revise the plan, present the complete updated plan, and stop again for confirmation. Approval of an earlier plan does not approve a revised plan.
- If the user asks a question without approving, answer it and keep the gate closed.

After approval, save the confirmed plan under `.tmp/lark-doc-visualizer-<timestamp>/visual-plan.md` and use it as the production contract. If later execution requires a material change in chart type, section treatment, information scope, destination, or output structure, pause, present the revised plan, and request confirmation again. Minor layout corrections discovered during validation do not require renewed approval.

### 4. Create the untouched copy

Start this phase only after the user explicitly approves the current plan.

1. Resolve the destination folder token. If no folder was supplied, list the user's Drive root and reuse the exact folder `可视化文档`; otherwise create it with `drive +create-folder`.
2. Run `lark-cli schema drive.files.copy --format json` immediately before the copy and follow its current schema.
3. Copy the source using `lark-cli drive files copy`, passing the resolved source token, source type, destination folder token, and `<source-title>-可视化` as the name.
4. Capture the returned output token and URL. From this point on, every `docs +update` command must target the output token. If a command is about to target the source token, stop.

Do not recreate the document with `docs +fetch` plus `docs +create`, and do not export/import it. A Drive copy preserves rich blocks more reliably.

### 5. Transform the copy section by section

Fetch the output with `--detail full` or the smallest relevant `section`/`range` scope before each group of block edits. Work serially in source order and refetch after operations that invalidate block IDs.

#### Keep prose

Keep prose when a visual would reduce precision, nuance, or reading flow. Do not convert narrative, analysis, caveats, or conclusions into bullets merely to look structured.

#### Use native Lark tables

Use XML `<table>` when readers need exact lookup, many fields, or heterogeneous comparison. Preserve exact wording and meaningful row order. Use table headers, reasonable column widths, restrained header color, and no decorative coloring.

When replacing existing blocks with a table:

1. Insert the new table after the intended anchor.
2. Refetch and verify the table content.
3. Delete the replaced old blocks only after every material point is present.

#### Use native-node whiteboards for directional diagrams

Use native Feishu whiteboard nodes and connectors for business processes, workflows, decision paths, lifecycles, dependencies, hierarchies, architecture, state transitions, cause-effect chains, loops, and every diagram whose meaning depends on direction.

Read [`references/native-connectors.md`](references/native-connectors.md) completely and follow it. Create an SVG layout draft first, translate the layout and edge ledger into whiteboard DSL with stable node IDs, compile the DSL to OpenAPI raw with `whiteboard-cli`, and write the raw nodes into a blank whiteboard. Never write the SVG draft directly to Feishu for these diagrams.

Every semantic edge must be a top-level native `connector` with explicit `startArrow` and `endArrow`. Default to `lineWidth: 1.25`, never exceed `1.5`, bind endpoints by node ID, and use `polyline` or `rightAngle` unless the relationship requires another supported form.

#### Use direct SVG whiteboards for charts and non-directional graphics

Read [`references/svg-style.md`](references/svg-style.md) completely before drawing any direct-import SVG. Use direct SVG for quantitative charts, quadrants, timelines, roadmaps, maturity models, layered stacks, and decorative graphics only when no semantic direction depends on an arrow.

Insert a complete self-contained SVG through a Lark whiteboard block according to the active `lark-doc` XML rules. Keep exact values in the SVG or in an adjacent native table. Retain the adjacent table when there are more than eight plotted observations, precise lookup matters, or labels would crowd the chart.

Do not use SVG `<marker>`, `marker-start`, `marker-mid`, or `marker-end` as a semantic channel. Feishu conversion can keep the line while dropping the marker. If a visual needs an arrow, route it to the native-node workflow.

#### Mermaid hard boundary

Use Mermaid only when both conditions are true:

1. The diagram shows chronological messages, calls, events, callbacks, acknowledgements, timeouts, or responses.
2. The participants are technical actors such as clients, services, APIs, agents, databases, queues, browsers, or infrastructure components.

Use only Mermaid `sequenceDiagram`. Render business handoffs, operating procedures, user journeys, approval flows, and causal chains as native-node whiteboards. Render ordinary timelines as direct SVG only when arrow direction is not semantically required.

#### Preserve fidelity during edits

- Preserve source headings and their order. Add a local visual caption only when needed; do not invent new analytical sections.
- Preserve numbers, dates, names, proper nouns, policy statements, requirements, rankings, constraints, qualifiers, and causal direction.
- Preserve `<cite>`, `<img>`, `<source>`, `<whiteboard>`, `<sheet>`, `<bitable>`, `<synced_reference>`, tasks, attachments, and their identifiers unless the copy operation legitimately remaps a resource token.
- Preserve ambiguity rather than resolving it.
- Do not add analysis, recommendations, examples, targets, averages, benchmarks, or trend lines absent from the source.
- Prefer insert-verify-delete for structural replacement. Avoid `overwrite`.

### 6. Validate and visually inspect

1. Fetch the output and source again:

   ```bash
   lark-cli docs +fetch --doc '<output-token>' --detail full --format json \
     > .tmp/lark-doc-visualizer-<timestamp>/output-after.json
   lark-cli docs +fetch --doc '<source-url>' --detail full --format json \
     > .tmp/lark-doc-visualizer-<timestamp>/source-after.json
   ```

2. Run:

   ```bash
   python3 .agents/skills/lark-doc-visualizer/scripts/check_visualized_doc.py \
     .tmp/lark-doc-visualizer-<timestamp>/source-before.json \
     .tmp/lark-doc-visualizer-<timestamp>/output-after.json \
     --source-after .tmp/lark-doc-visualizer-<timestamp>/source-after.json
   ```

3. Fix every error and relevant warning.
4. Export every newly inserted whiteboard as a preview PNG with `lark-cli whiteboard +export`, store it in the temporary directory, and inspect it. Check text wrapping, scale, labels, arrows, connector thickness, contrast, bounds, units, denominators, and missing values.
5. For each native-node diagram, export `raw`, run `scripts/check_native_connectors.py` with the exact connector and directed-edge counts from the edge ledger, and fail the task if an expected arrow is `none` or a connector is `medium`/thicker. Adjacent prose does not compensate for a missing arrow.
6. Refetch the edited sections and verify the final reading order, exact values, links, resources, and absence of empty whiteboards or duplicate text.

## Chart integrity rules

- Use pie or donut only for one known whole with non-negative, mutually exclusive parts and at most six slices; displayed shares must total approximately 100% after stated rounding.
- Start quantitative bar axes at zero. Use a dot, range, or line chart when a non-zero baseline is necessary and label the scale.
- Use lines only for ordered time or continuous sequences. Break lines at missing periods.
- Use funnels only for ordered stages from a common cohort, not for ordinary processes.
- Use scatter or bubble charts only for paired observations; describe association, not causation, unless the source supports causality.
- Use histograms and box plots only from raw observations, bins, or sufficient summary statistics.
- Use heatmaps only when both axes and all cell values share a comparable metric; show the scale or exact values.
- Use waterfalls only when signed contributions reconcile to a stated start, subtotal, or end.
- Avoid 3D charts, decorative gauges, radar charts, dual axes, and area-scaled pictograms.
- Keep source order when meaningful. Sort only when the source does not encode a sequence or hierarchy.
- Preserve units, time windows, denominators, ranges, uncertainty, precision, and qualifiers.
- Keep `N/A`, blank, unknown, and not measured distinct from zero. Draw no quantitative mark for a missing value.

## Completion checklist

- A complete visualization plan was shown to the user, and explicit confirmation was received only after that plan.
- No Feishu write, output copy, destination-folder creation, or production visual asset was created before confirmation.
- The confirmed plan was saved locally and material deviations were reconfirmed.
- The source URL/token was never passed to a write command.
- The output title ends with `-可视化` and the output is a Drive copy.
- All source sections were read, and heading order remains intact.
- Every visual is supported by source content and answers a clear reading question.
- Tables preserve exact lookup values; charts use valid units, scales, denominators, and missing-value treatment.
- Mermaid is sequence-only and technical; direction-bearing diagrams use native nodes/connectors; direct SVG is limited to charts and non-directional graphics.
- Every native-node diagram follows `references/native-connectors.md`, has bound endpoints, explicit arrows, connector width no greater than `1.5`, and passes raw-node validation.
- Every direct SVG follows `references/svg-style.md`, contains no marker-based semantic arrow, and has been previewed.
- Every stacked or segmented SVG bar uses square internal seams; only the complete bar's two exterior ends are rounded.
- Source links and embedded resources remain present or are intentionally remapped by the copy operation.
- The validation script exits successfully.
- The final response includes the output title, clickable Feishu URL, validation result, and any genuine caveat.
