# Feishu Whiteboard SVG Visual System

Read this file completely before generating an SVG whiteboard.

## Character

- Use a quiet editorial infographic style, not decorative illustration.
- Keep the canvas transparent and let Feishu provide the page background.
- Build clear hierarchy with rounded cards, dark headings, restrained semantic color, and short labels.
- Prefer one strong composition to ornamental clutter.

## Color tokens

| Role | Fill | Stroke/accent | Text |
| --- | --- | --- | --- |
| Canvas | transparent; omit a background shape | — | — |
| Primary text | — | — | `#0f172a` |
| Secondary/axes | — | `#334155` | `#475569` |
| Neutral | `#f1f5f9` | `#94a3b8` | `#334155` |
| Information | `#eff6ff` | `#3b82f6` | `#1d4ed8` |
| Value/recommended | `#ecfdf5` | `#10b981` | `#047857` |
| Condition/attention | `#fff7ed` | `#f59e0b` | `#92400e` |
| Risk/stop | `#fef2f2` | `#ef4444` | `#b91c1c` |

Use color semantically and consistently. Do not use `#f8fafc` as a canvas fill.

For unrelated categorical series, use `#2563eb`, `#059669`, `#d97706`, `#7c3aed`, `#db2777`, then `#475569`. Reserve red for source-defined negative or risk states.

## Geometry and typography

- Use card radius `16–20`, card stroke `1.5–2`, and chart-axis/grid stroke `1–1.5`.
- Align to a clear grid. Route any direction-bearing relationship to the native connector workflow instead of drawing it in the direct-import SVG.
- Use Feishu-compatible `<text>` and `<tspan>`; never turn text into paths.
- Assume CJK text is about `1em` wide and Latin text about `0.6em`; leave generous width.
- Use `22–28px` bold for a diagram title, `18–23px` bold for card titles, and `14–18px` for body labels. Never shrink below `14px` to force a fit.
- Wrap text manually with `<tspan>` and `24–30px` line height.

## Composition patterns

- Maturity: rising staircase.
- Capability sequence: vertical numbered path with full-width cards.
- Inputs to outcome: compact inputs feeding one emphasized outcome.
- Quadrant: four regions, dark axes, and explicit low/high labels.
- Timeline/roadmap: numbered milestones on one spine.
- Quantitative comparison: aligned bars, columns, dots, or dumbbells on one labeled scale.
- Trend: line or small multiples with explicit time labels and visible gaps.

Match form to the relationship; do not force all diagrams into card grids.

## SVG compatibility

- Include `xmlns`, `viewBox`, `role="img"`, `aria-label`, `<title>`, and `<desc>`.
- Keep the root canvas transparent. Do not add a rectangle covering the full `viewBox`.
- Use document-unique IDs for definitions.
- Use standard primitives: `rect`, `circle`, `ellipse`, `line`, `polyline`, `path`, `polygon`, `text`, `tspan`, `g`, `defs`, and `use` with a local `symbol`.
- Use `translate`, `rotate`, or `scale` only when useful. Avoid `skewX`, `skewY`, and `matrix(...)`.
- Avoid remote assets, scripts, external CSS/fonts, `foreignObject`, `image`, `pattern`, `clipPath`, `mask`, filters, and complex gradients. Conservative primitives convert more reliably to editable Feishu nodes.
- Do not use `<marker>`, `marker-start`, `marker-mid`, or `marker-end`. Feishu can drop marker arrows while retaining their lines. Route any semantic arrow to [`native-connectors.md`](native-connectors.md).
- Keep all visible elements inside the `viewBox`.

Minimal structure:

```html
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 520" role="img" aria-label="图示说明">
  <title>图示标题</title>
  <desc>完整说明图中的关系、顺序或数值。</desc>
  <!-- shapes, labels, connectors -->
</svg>
```

## Data-chart construction

- Reserve clear plot margins for labels and units.
- Draw axes with `line` or `path`, ticks with `line`, and labels with `text`/`tspan`.
- Start bars/columns at zero and draw an explicit zero baseline when values may be negative.
- Direct-label up to eight observations. For more, retain an adjacent native Feishu table.
- Use no more than four line series or three grouped-bar series; otherwise use small multiples.
- Pair color with labels, ordering, symbols, or dash patterns.
- Use bubble area, not radius, for magnitude.
- Include unit, time basis, and population/denominator in the chart or adjacent caption.
- For missing data, draw no bar, point, slice, bubble, or area. Put the exact missing state beside the category, below the axis, or in the adjacent table.

### Stacked and segmented bars

Treat every stacked bar as one continuous silhouette, not a row of rounded pills.

- Round only the two exterior ends of the complete bar: the first visible segment has rounded left corners, and the last visible segment has rounded right corners.
- Keep every internal junction square. Adjacent segments must share the exact same vertical boundary with no gap, white slit, rounded notch, or double-rounded overlap.
- Never apply `rx`/`ry` to every segment. A normal rounded `<rect>` rounds all four corners and is therefore invalid for an internal or multi-segment boundary.
- Use a plain `<rect>` for every middle segment. Use corner-specific `<path>` geometry for the first and last segments, or draw one full rounded base in the last segment's color and cover its interior with square-edged preceding segments.
- If only one visible segment remains, round both ends. If an endpoint segment is zero or missing and therefore omitted, transfer the exterior rounding to the first or last segment that is actually visible.

Corner-specific path example (`x=100`, `y=60`, `height=36`, `radius=12`; internal boundaries at `240` and `360`):

```html
<!-- First segment: left corners rounded, right boundary square. -->
<path d="M112 60 H240 V96 H112 A12 12 0 0 1 100 84 V72 A12 12 0 0 1 112 60 Z" fill="#2563eb"/>
<!-- Middle segment: all corners square. -->
<rect x="240" y="60" width="120" height="36" fill="#059669"/>
<!-- Last segment: left boundary square, right corners rounded. -->
<path d="M360 60 H448 A12 12 0 0 1 460 72 V84 A12 12 0 0 1 448 96 H360 Z" fill="#d97706"/>
```

## Visual QA

Export and inspect every whiteboard preview. Verify:

1. Text is legible at document width and stays inside containers.
2. The SVG contains no marker-based or hand-drawn semantic arrows.
3. Axes and grid lines remain visually lighter than card borders.
4. Meaning survives grayscale through labels, position, and borders.
5. The outer canvas remains transparent.
6. Axes, units, baselines, denominators, legends, precision, and missing states are correct.
7. Pie/donut shares, funnel cohorts, waterfall arithmetic, and proportional flows pass their prerequisites.
8. Every stacked or segmented bar has one continuous outer silhouette: only its two exterior ends are rounded, and every internal seam is straight and gap-free.
