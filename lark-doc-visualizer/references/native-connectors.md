# Native Feishu Whiteboard Connectors

Read this file completely before creating any diagram whose meaning depends on direction.

## Contract

- Use the SVG only as a local layout draft. Never import that SVG directly into Feishu for a direction-bearing diagram.
- Deliver native Feishu nodes and bound native connectors through the whiteboard DSL → OpenAPI raw workflow.
- Record every edge in an edge ledger with: edge ID, source node ID, target node ID, source/target anchors, line shape, line style, start arrow, end arrow, label, and source wording.
- Preserve source direction exactly. Do not infer a direction for an ambiguous relationship.

## Workflow

### 1. Draft the composition in SVG

Create a self-contained SVG under the task's `.tmp/` directory to settle geometry, spacing, labels, and routes. Give every connectable card a stable ID that will also be used in the DSL.

Use at least `40px` between connected cards. Prefer orthogonal routes and shared buses over diagonal fan-out. Treat the draft as disposable: SVG markers are not part of the delivery contract because Feishu may drop `<marker>` and `marker-end` while retaining the line.

### 2. Translate the draft into whiteboard DSL

Read the installed `lark-whiteboard` skill's `routes/dsl.md`, `elements/schema.md`, `elements/connectors.md`, and the matching scene guide. Create a version-2 DSL JSON file.

Use stable IDs for connectable nodes. Put every connector directly in the document's top-level `nodes` array, even when the connected nodes live inside frames. Bind `from` and `to` by node ID; use coordinates only for a genuine free-point annotation.

Write every arrow property explicitly. Never rely on defaults:

```json
{
  "type": "connector",
  "id": "edge-ingest-parse",
  "connector": {
    "from": "node-ingest",
    "to": "node-parse",
    "fromAnchor": "right",
    "toAnchor": "left",
    "lineShape": "polyline",
    "lineColor": "#334155",
    "lineWidth": 1.25,
    "lineStyle": "solid",
    "startArrow": "none",
    "endArrow": "arrow"
  }
}
```

Rules:

- Use `lineWidth: 1.25` by default and never exceed `1.5`.
- Use `endArrow: "arrow"` for ordinary forward direction. Use `triangle`, `circle`, or `diamond` only when the source semantics justify it.
- Set both arrows to `none` for a genuinely non-directional relationship.
- Prefer `polyline`; use `rightAngle` for strict bus/tree routing, `straight` for axes or direct geometric relations, and `curve` only for a deliberate cross-layer/annotation route.
- Omit waypoints first and let native routing avoid obstacles. Add waypoints only after previewing a bad route.
- Use dashed lines only for a source-backed asynchronous, optional, inferred, or feedback relationship, and label the meaning when it is not obvious.
- Keep connectors behind or visually separated from labels; avoid line crossings.

### 3. Validate and compile

Run the connector checker with the exact counts from the edge ledger:

```bash
python3 .agents/skills/lark-doc-visualizer/scripts/check_native_connectors.py \
  .tmp/lark-doc-visualizer-<timestamp>/diagram.json \
  --format dsl \
  --expected-connectors <all-edge-count> \
  --expected-directed <directed-edge-count>
```

Render and visually inspect the DSL before writing:

```bash
npx -y @larksuite/whiteboard-cli@^0.2.13 \
  -i .tmp/lark-doc-visualizer-<timestamp>/diagram.json \
  -o .tmp/lark-doc-visualizer-<timestamp>/diagram.png

npx -y @larksuite/whiteboard-cli@^0.2.13 \
  -i .tmp/lark-doc-visualizer-<timestamp>/diagram.json --check
```

Compile to OpenAPI raw and validate it again:

```bash
npx -y @larksuite/whiteboard-cli@^0.2.13 \
  -i .tmp/lark-doc-visualizer-<timestamp>/diagram.json \
  --to openapi --format json \
  -o .tmp/lark-doc-visualizer-<timestamp>/diagram.openapi.json

python3 .agents/skills/lark-doc-visualizer/scripts/check_native_connectors.py \
  .tmp/lark-doc-visualizer-<timestamp>/diagram.openapi.json \
  --format openapi \
  --expected-connectors <all-edge-count> \
  --expected-directed <directed-edge-count>
```

The OpenAPI result must use `extra_narrow` or `narrow` connector borders and non-`none` native arrow styles for every directed edge.

### 4. Insert and populate a blank whiteboard

Insert `<whiteboard type="blank"></whiteboard>` at the intended position in the copied document and capture its whiteboard token. Never create it in the source document.

Write the compiled OpenAPI JSON through `lark-cli whiteboard +update --input_format raw`, following the installed `lark-whiteboard` update workflow, current schema, idempotency rules, identity rules, and any confirmation gate.

### 5. Verify the actual Feishu result

Export both the preview and raw nodes from the written whiteboard. Re-run the checker against the exported raw JSON with the same expected counts. Inspect the preview at document width.

Reject and rebuild the board when any of these occurs:

- a directed connector has no visible arrowhead;
- a connector is `medium` or thicker;
- an endpoint is not attached to the intended node;
- a route crosses a card or obscures a label;
- a connector direction contradicts the edge ledger.

Do not accept adjacent prose as a fallback for a broken connector.
