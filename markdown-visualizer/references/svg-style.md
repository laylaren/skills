# SVG Visual System

Use this visual system for Markdown diagrams. It keeps the card, typography, and semantic-color language from `research/agent/企业数据资产学术调研-20260727-可视化.md`, while deliberately removing the light-gray full-canvas background.

## Design Character

- Quiet editorial infographic, not a decorative illustration.
- Transparent canvas, rounded cards, dark headings, restrained semantic color.
- Clear hierarchy, generous whitespace, short labels, and unambiguous arrows.
- Prefer one strong composition over many small ornamental elements.
- Let the host Markdown or Feishu document supply the page background. Do not draw a page-like background inside the SVG.

## Color Tokens

| Role | Fill | Stroke / Accent | Text |
| --- | --- | --- | --- |
| Canvas | transparent; omit the background shape | — | — |
| Primary text | — | — | `#0f172a` |
| Secondary text / connectors | — | `#334155` | `#475569` |
| Neutral card | `#f1f5f9` | `#94a3b8` | `#334155` |
| Blue / information | `#eff6ff` | `#3b82f6` | `#1d4ed8` |
| Green / value or recommended | `#ecfdf5` | `#10b981` | `#047857` |
| Orange / condition or attention | `#fff7ed` | `#f59e0b` | `#92400e` |
| Red / risk or stop | `#fef2f2` | `#ef4444` | `#b91c1c` |

Use color semantically and consistently. Do not introduce extra hues merely for variety.
Do not use `#f8fafc`; that token was the former canvas background and has been retired.

## Geometry

- Card corner radius: `16–20`.
- Card stroke: `2`.
- Connector stroke: `2–2.5`, color `#334155`.
- Dashed connector: `stroke-dasharray="8 7"`.
- Use arrow markers with `markerWidth="10"`, `markerHeight="10"`, `refX="8"`, and `refY="5"`.
- Keep at least `24px` between cards and at least `32px` between major regions.
- Align cards to a clear grid; use symmetric margins where the meaning does not require asymmetry.

## Typography

Use this system stack:

```text
-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif
```

- Main diagram title: `22–28px`, weight `700`.
- Card title: `18–23px`, weight `700`.
- Body label: `14–18px`, weight `400–700` according to hierarchy.
- Use `#0f172a` for neutral headings and the semantic text token for colored cards.
- Wrap Chinese labels manually with `<tspan x="..." dy="...">`; target `24–30px` line height.
- Do not shrink body text below `14px` to force content into a card. Enlarge the card or canvas instead.

## Composition Patterns

- Process or value chain: horizontal cards with a feedback path below.
- Lifecycle or closed loop: horizontal or circular steps with one clearly visible return connector.
- Maturity model: rising staircase of cards.
- Capability sequence: vertical numbered path with full-width cards.
- Inputs converging on an outcome: compact input cards feeding a central dark outcome card.
- Quadrant: four semantic pastel regions with dark axes and explicit low/high labels.
- Architecture or hierarchy: layers or grouped cards with directional connectors; avoid crossing lines.
- Timeline or roadmap: numbered milestones on a horizontal or vertical spine.
- Quantitative comparison: aligned horizontal bars, columns, dots, or dumbbells on one labeled scale.
- Trend: line or small-multiple plots with explicit time labels and visible gaps for missing data.
- Composition: donut, pie, stacked bar, or 100% stacked bar only when parts and denominator are valid.
- Distribution: histogram, strip plot, range plot, or box plot only from sufficient source data.
- Relationship: scatter, bubble, or heatmap with labeled axes and an explicit value scale.
- Contribution or conversion: waterfall, funnel, or proportional flow only when the arithmetic or cohort relationship is source-backed.

Match the shape to the relationship; do not force every diagram into the same layout.

## Data Chart Construction

- Reserve a clear plot region and margins for labels. Do not let axis labels compete with the title or legend.
- Use solid fills and strokes. Avoid gradients, shadows, textures, 3D effects, and ornamental perspective.
- Draw axes with `line` or `path`, ticks with `line`, and labels with `text`/`tspan`.
- Start bar and column value axes at zero. Draw an explicit zero baseline when values may be negative.
- Use direct value labels whenever the plot has eight or fewer observations. For larger charts, retain an adjacent Markdown table with exact values.
- Use no more than four simultaneous line series or three grouped-bar series. Switch to small multiples when the plot becomes crowded.
- Use circles or distinct dash patterns in addition to color for series that must remain distinguishable in grayscale.
- Keep bar widths, gaps, dot sizes, and line weights consistent. Use bubble area—not radius—to encode magnitude.
- Include units and the time or population basis in the title, axis labels, subtitle, or adjacent caption.
- Preserve missing values by leaving the data-mark region empty and placing `N/A` or the exact source state outside the plot area: beside the category label, below the x-axis, in the subtitle/caption, or in the adjacent table. Never float a missing-value label or annotation card inside the plot. Never draw a bar, point, slice, bubble, or area for a missing value—even with dashed styling—because its position or size would imply a magnitude.

## Chart Color Sequence

For unrelated categorical series, use this restrained, colorblind-aware sequence in order:

1. `#2563eb` blue
2. `#059669` green
3. `#d97706` amber
4. `#7c3aed` violet
5. `#db2777` magenta
6. `#475569` slate

Use semantic red `#dc2626` only for source-defined negative, risk, loss, or stop states. Do not use red merely as the next category color. Pair every important color distinction with labels, ordering, or shapes.

## Accessibility And Compatibility

- Always include `xmlns`, `viewBox`, `role="img"`, `aria-label`, `<title>`, and `<desc>`.
- Keep the root canvas transparent. Do not add a rectangle that covers the full `viewBox`.
- Describe the substantive relationship in `<desc>`, not merely “a diagram”.
- Use unique IDs such as `arrow-value-chain` instead of generic `arrow`.
- Use only standard SVG primitives: `rect`, `circle`, `ellipse`, `line`, `polyline`, `path`, `polygon`, `text`, `tspan`, `g`, `defs`, and `marker`.
- Avoid `foreignObject`, `image`, external CSS, remote fonts or images, scripts, filters, masks, clip paths, and gradients.
- Keep all visible elements inside the `viewBox`.

## Visual QA

Render or preview every SVG and verify:

1. All text is legible at document width.
2. No label crosses a card edge.
3. No arrowhead covers text or ends outside the target.
4. Connectors do not imply a relationship absent from the source.
5. Color meaning remains consistent across the document.
6. The diagram still works in grayscale through labels, layout, and borders.
7. The area outside cards and connectors is transparent, with no pale-gray canvas block.
8. Chart axes, units, baselines, denominators, legends, and missing-value treatment are accurate.
9. Pie/donut shares, funnel cohorts, waterfall arithmetic, and proportional flows satisfy their data prerequisites.
