# SVG Data Chart Selection

Read this reference whenever Markdown contains quantitative data that may benefit from a chart. Choose a chart by the relationship in the source, not by visual novelty.

## Selection Matrix

| Reading task | Preferred SVG chart | Use when | Do not use when |
| --- | --- | --- | --- |
| Compare magnitudes or rank categories | Horizontal bar; vertical column for few short labels | Values share a unit and basis | Categories use incompatible units or bases |
| Compare two values per category | Grouped bar; dot plot; dumbbell for before/after | Series are directly comparable | More than 3 series make grouping dense |
| Show change over ordered time | Line chart; column for discrete periods; small multiples for many series | Time intervals and units are explicit | Categories are unordered or gaps are hidden |
| Show a single whole | Donut or pie; 100% stacked bar when labels are long | Parts are exclusive, non-negative, share one denominator, and total about 100% | More than 6 parts, unknown denominator, overlapping parts, or negative values |
| Compare composition across groups | 100% stacked bars | Each group has the same component definition | Absolute totals are the main question |
| Show total and composition together | Stacked bars | Components add to each group total | Precise component comparison across many groups is primary |
| Show distribution | Histogram; box plot; strip/dot plot for few observations | Raw data, bins, or quartiles exist | Only averages or anecdotal ranges exist |
| Show two-variable association | Scatter plot; bubble only when a trustworthy third measure exists | Every point has paired numeric values | The source only states a causal narrative without paired data |
| Show two-dimensional intensity | Heatmap or labeled matrix | Cells share a metric and both axes are meaningful | Colors would mix different units or missing cells look like zero |
| Show sequential conversion | Funnel or stage bars with conversion labels | A common cohort moves through ordered stages | It is merely a workflow, checklist, or unrelated stage totals |
| Show signed contributions | Waterfall | Contributions reconcile to a start, subtotal, or end value | Values are independent categories |
| Show actual versus target | Bullet chart, progress bar, or paired dot | Target and actual share a unit and period | Target is absent or qualitative |
| Show ranges or uncertainty | Range bar, interval plot, error bar | Bounds or uncertainty are explicitly provided | A range would be fabricated from a point estimate |
| Show change between two periods | Slope chart or dumbbell | Same entities appear in both periods | There are many crossings or missing pairs; use small multiples or a table |
| Show many comparable time series | Small-multiple lines or sparklines plus exact table | Series share the same scale and time basis | Independent axes would be needed |
| Show scheduled duration | SVG Gantt or timeline bars | Start/end dates or durations are explicit | Only phase order is known; use a roadmap diagram |
| Show geographic comparison | Ranked bars by region by default | Geography is a category | A map would imply precision without supplied boundaries or geographic data |
| Show volume moving between entities | Proportional flow or Sankey-like SVG | Source provides conserved flow quantities | Flows do not reconcile or are only qualitative relationships |
| Surface a few headline values | KPI cards plus context labels | Metrics, units, and periods are explicit | Cards would detach numbers from caveats or denominators |

## Decision Rules

1. Prefer a table when the task is lookup, audit, or exact multi-field comparison.
2. Prefer a chart when the task is pattern recognition and at least three comparable numeric observations exist. Allow two observations for before/after, target/actual, or a simple share split.
3. Combine one chart with one compact table when readers need both the pattern and exact values. Do not repeat long prose, a full table, and a fully labeled chart without a reading need.
4. Prefer horizontal bars for long Chinese labels. Prefer columns only for short labels, ordered periods, or very few categories.
5. Limit a single chart to one primary question. Split unrelated metrics into small multiples instead of using dual axes.
6. Use small multiples when more than four line series or three grouped-bar series would compete in one plot.
7. Group tiny part-to-whole categories into “其他” only if the source already defines that group or the user explicitly permits aggregation. Otherwise use bars and preserve every category.
8. Use direct labels when practical. Add a legend only when labels cannot sit next to marks without overlap.
9. Use color to distinguish meaning, status, or series. Do not encode important differences by color alone; include labels, shapes, or positions.

## Data Preparation Contract

Create an internal ledger before SVG authoring:

| Field | Required handling |
| --- | --- |
| Dimension | Preserve the source label and semantic order |
| Value | Copy exactly; never infer blanks or hidden precision |
| Unit | Preserve currency, percent, count, duration, rate, or index |
| Time basis | Preserve period, as-of date, cohort, and timezone if present |
| Denominator | Preserve the population or total behind ratios and shares |
| Series | Use only source-defined groups |
| Missing state | Keep `N/A`, unknown, blank, or not measured distinct from zero |
| Range or uncertainty | Preserve lower/upper bounds and qualifiers |
| Derived arithmetic | Permit exact sums, differences, ratios, and percentages only; mark `计算值` |

If any field needed for the selected chart is ambiguous, retain a table and preserve the ambiguity.

## Scale And Label Rules

- Put the unit in the chart title, axis label, or direct value labels. Do not make readers infer it.
- Start bar and column value axes at zero. Use a dot or range chart when a narrow non-zero comparison is the honest encoding.
- Label percentage axes from 0% to 100% when showing full proportions.
- Keep comparable small multiples on identical scales.
- Show negative and positive regions around an explicit zero baseline.
- Do not smooth lines unless the source provides a smoothed series.
- Do not show false continuity across missing time periods; break the line and label the gap.
- For a missing category or period, leave the quantitative mark region empty. Put `N/A`, `未知`, or the exact source state outside the plot area: next to the category label, below the x-axis, in the chart subtitle/caption, or in the adjacent table. Do not float the label or an annotation card inside the plot, because its coordinate can be read as a value. Do not draw a bar, point, slice, bubble, or area at any value position, because even a dashed placeholder encodes a false magnitude.
- Preserve source precision. Do not display extra decimals that imply measurement accuracy absent from the source.
- State rounding when it affects totals, especially pie/donut shares.

## Chart-Specific Fidelity Checks

### Pie And Donut

- Verify one denominator and mutually exclusive parts.
- Use at most six slices; order consistently and label every slice with category and value or share.
- Keep the start angle and slice order neutral; do not explode slices for decoration.
- Prefer a donut only when the center contains a source-backed total or short label.

### Bar, Column, Dot, And Dumbbell

- Use a shared zero baseline for bars and columns.
- Keep widths and spacing consistent; do not encode a second quantity through bar width.
- Preserve meaningful source order; otherwise rank descending when comparison is the purpose.
- Use dot or dumbbell charts for narrow differences that bars would visually suppress.

### Line And Small Multiples

- Use ordered time or continuous x-values.
- Label endpoints or series directly where possible.
- Break lines at missing values and label the gap without plotting a point at an inferred value.
- Keep no more than four series in one plot; otherwise use small multiples.

### Histogram, Box Plot, And Distribution Marks

- Use source bins as given. If raw values exist and bins must be calculated, mark the binning as `计算值` and state the rule.
- Construct a box plot only from source-provided or exactly computed minimum, Q1, median, Q3, and maximum. State the outlier rule if outliers are shown.
- Do not infer distribution shape from mean and range alone.

### Scatter And Bubble

- Preserve paired observations and units on both axes.
- Keep bubble area, not radius, proportional to the third value.
- Add a trend line only when provided or explicitly requested; label it as calculated.
- Do not convert association into a causal claim.

### Funnel, Waterfall, And Flow

- Funnel: verify stage order and a common starting cohort; show counts and conversion rates when available.
- Waterfall: verify arithmetic reconciliation and distinguish increases, decreases, and totals without relying on color alone.
- Proportional flow: verify that incoming and outgoing quantities reconcile or explicitly label leakage and unknown portions.

### Heatmap And Matrix

- Use one comparable metric across cells.
- Include a visible numeric scale or direct values.
- Render missing cells with an explicit neutral pattern or `N/A`, never the minimum-value color.

## Avoid By Default

- 3D pie, 3D bars, perspective effects, shadows that change perceived area, and pictograms scaled by both height and width.
- Decorative speedometers and gauges; use a bullet or progress chart.
- Radar charts; axis order and polygon area are easy to misread. Use grouped bars, dots, or small multiples.
- Dual-axis charts; separate into aligned charts with shared x-values.
- Choropleth maps without supplied geographic boundaries and normalized geographic measures.
- Word clouds as evidence of frequency unless the source provides token counts and the limitations are acceptable.
