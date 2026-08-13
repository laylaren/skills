# Feishu SVG Data Chart Selection

Read this file completely whenever quantitative content may benefit from a chart. Select by the relationship in the source, not by novelty.

## Selection matrix

| Reading task | Preferred SVG chart | Use when | Do not use when |
| --- | --- | --- | --- |
| Compare magnitudes or rank | Horizontal bar; column for a few short labels | Values share a unit and basis | Units or bases differ |
| Compare two values per category | Grouped bar, dot, or dumbbell | Series are directly comparable | More than three series crowd the view |
| Show ordered change | Line, period columns, or small multiples | Time intervals and units are explicit | Categories are unordered or gaps would be hidden |
| Show one whole | Donut, pie, or 100% stacked bar | Parts are exclusive, non-negative, and share a denominator | More than six parts, unknown denominator, overlap, or negatives |
| Compare group composition | 100% stacked bars | Components are defined consistently | Absolute totals are the main question |
| Show total and composition | Stacked bars | Components add to the total | Precise cross-group component comparison dominates |
| Show distribution | Histogram, box plot, or strip plot | Raw data, bins, or quartiles exist | Only averages or anecdotal ranges exist |
| Show two-variable association | Scatter; bubble with a trustworthy third measure | Every observation has paired numbers | Only a causal narrative exists |
| Show two-dimensional intensity | Heatmap or labeled matrix | Cells share one metric and both axes matter | Colors would mix units or hide missing cells |
| Show sequential conversion | Funnel or stage bars | One cohort moves through ordered stages | It is merely a workflow |
| Show signed contribution | Waterfall | Contributions reconcile to a total | Values are independent categories |
| Show actual versus target | Bullet, progress bar, or paired dot | Target and actual share unit and period | Target is absent or qualitative |
| Show range or uncertainty | Range or interval plot | Bounds are supplied | Bounds would be fabricated |
| Show two-period change | Slope or dumbbell | The same entities appear in both periods | Missing pairs or crossings make it unreadable |
| Show scheduled duration | Gantt-like SVG or timeline bars | Start/end dates or durations are explicit | Only phase order is known |
| Show conserved flows | Proportional flow | Source quantities reconcile | Flows are qualitative or inconsistent |
| Surface headline values | KPI cards with context labels | Metric, unit, and period are explicit | Cards would detach numbers from caveats |

## Decision rules

1. Prefer a native Feishu table for lookup, audit, or exact multi-field comparison.
2. Prefer a chart for pattern recognition with at least three comparable observations. Two are enough for before/after, actual/target, or a simple share split.
3. Use one chart plus one compact table when readers need both pattern and exact values.
4. Prefer horizontal bars for long Chinese labels. Use columns for short labels, ordered periods, or very few categories.
5. Give each chart one primary question. Split unrelated metrics into aligned small multiples; never use dual axes.
6. Use small multiples for more than four line series or three grouped-bar series.
7. Group small categories into `其他` only when the source already does so or the user permits aggregation.
8. Use direct labels where possible and a legend only when necessary.
9. Never encode an important distinction by color alone.

## Data preparation contract

| Field | Required handling |
| --- | --- |
| Dimension | Preserve label and semantic order |
| Value | Copy exactly; never infer blanks or hidden precision |
| Unit | Preserve currency, percent, count, duration, rate, or index |
| Time basis | Preserve period, as-of date, cohort, and timezone if present |
| Denominator | Preserve the population or total behind ratios and shares |
| Series | Use only source-defined groups |
| Missing state | Keep `N/A`, unknown, blank, and not measured distinct from zero |
| Range/uncertainty | Preserve bounds and qualifiers |
| Derived arithmetic | Allow exact sums, differences, ratios, and percentages only; label `计算值` |

If a required field is ambiguous, keep a table and preserve the ambiguity.

## Scale and fidelity

- Put units in the title, axis, subtitle, or direct value labels.
- Start bars and columns at zero. Use dots or ranges for honest narrow non-zero comparisons.
- Label full-proportion axes from 0% to 100%.
- Keep comparable small multiples on identical scales.
- Show positive and negative regions around an explicit zero baseline.
- Do not smooth lines or infer continuity.
- Break time-series lines at missing values. Put the exact missing state outside the plot area and draw no mark for it.
- Preserve source precision and state rounding when it changes totals.
- Bubble area, not radius, encodes magnitude.
- Add no trend line unless supplied or explicitly requested and labeled as calculated.

## Chart-specific gates

- **Pie/donut:** one denominator, mutually exclusive parts, no negatives, at most six slices, every slice labeled.
- **Bar/column:** common zero baseline, consistent widths, one quantity per bar, meaningful source order.
- **Line:** ordered x-values, visible gaps, direct series labels when practical.
- **Distribution:** source bins or exactly computed statistics; state any calculated binning or outlier rule.
- **Scatter/bubble:** paired observations and labeled axes; never turn association into causation.
- **Funnel:** ordered common cohort with counts and conversion rates when available.
- **Waterfall:** arithmetic reconciliation with increases, decreases, and totals distinguishable without color alone.
- **Flow:** conserved quantities or explicit leakage/unknown portions.
- **Heatmap:** one comparable metric with direct values or a visible scale; missing cells labeled, never colored as minimum.

## Avoid by default

Avoid 3D effects, gauges, radar charts, dual axes, pictograms scaled in two dimensions, decorative perspective, and choropleth maps without supplied geographic boundaries and normalized measures.

