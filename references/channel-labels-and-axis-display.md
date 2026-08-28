# Channel labels and axis display

## Canonical feature and display label

Gate membership always uses the canonical feature name from the WSP, such as `Comp-BL5-H`. A stain or antibody name is a display alias and must not replace that key in geometry, compensation, export, or validation records.

For each WSP sample, pair `$PnN` with `$PnS` from its `Keywords` block. Resolve a compensated feature by removing one leading `Comp-`, then matching the remaining detector to `$PnN`. For example:

```text
Comp-BL5-H -> BL5-H -> $P14N -> $P14S -> PE-Cy7-CD41-61-H
```

Use the WSP `$PnS` as the template-semantic label. If it is absent, use the bound FCS `$PnS`; otherwise fall back to the detector. Display both semantics and computation, for example `PE-Cy7-CD41-61-H · Comp-BL5-H`.

When both WSP and current FCS provide non-empty `$PnS` values for the same detector and they differ case-insensitively, keep the WSP label but emit a review notice. Do not silently treat detector compatibility as proof that the same antibody or stain was acquired.

## Display transforms

Axis controls are a visualization layer. They do not change `build_feature_map`, membership masks, counts, percentages, compensation, or the source WSP.

- **Linear**: `display(x) = x`.
- **Log**: `display(x) = log10(x)` for `x > 0`. Non-positive coordinates are omitted from the plot only; report how many plotted coordinates were omitted and retain all events in statistics.
- **Biex/logicle display**: the current web renderer uses the existing signed `asinh(x / cofactor)` approximation. The default cofactor is derived from WSP `maxRange` and positive decades, unless the user supplies a positive display Scale.
- **WSP default**: use the transform kind and attributes parsed from the prototype WSP.

User-entered axis minimum and maximum values are native feature-space values. Transform them for plotting only. Require finite values, `minimum < maximum`, a positive Scale, and positive Log bounds. Reset restores the gate dimensions and WSP display metadata.

For automatic ranges, calculate the 0.05% and 99.95% quantiles in display space, expand the range to include every finite current-gate boundary, then add 20% display-space headroom to each non-explicit side. This is a visualization rule: rare extreme event outliers may remain outside the viewport, but every finite current-gate boundary must remain visible unless the user supplies an explicit range that clips it. An absent rectangle minimum or maximum is an open boundary, so the display may correctly extend that side to the chart edge.

On first display, write the computed native minimum, maximum, and Scale into the controls instead of leaving opaque `auto` placeholders. Store transform kind, native min/max, and Scale as a reusable-session profile keyed by axis and canonical parameter. Reuse the same parameter's profile while switching samples or Gates so comparable plots keep identical axes. Do not copy a detector's numeric profile to a different detector. Reset clears the session profile and recomputes WSP-derived defaults.

Do not claim FlowJo transform parity from this renderer. Exact replay remains established by all cached gate counts matching. Before replacing the Biex approximation with an exact implementation, version the algorithm and validate forward/inverse values and representative FlowJo plots.

## Interactive rectangle mapping

When the rectangle editor is active, canvas pointer coordinates are mapped into the displayed axis range and then passed through the display transform inverse to recover native gate bounds. Use a canvas-sized SVG overlay whose visible edge lines, circular handles, and filled frame are the actual pointer targets. Give edges a wider invisible SVG stroke only as a hit tolerance, retain coordinate-based fallback hit testing, capture the pointer on the SVG, and display immediate capture feedback. Dragging inside the frame translates both finite bounds in display space and then inverts them back to native values, preserving the rectangle's visible width and height under nonlinear display transforms. Clamp a resized minimum so it cannot exceed the corresponding maximum, and vice versa. Synchronize the numeric inputs with the canvas preview.

Provide a keyboard-accessible fallback for environments where pointer dragging is unreliable. Left/Right operate on the first dimension and Down/Up operate on the second dimension. Require separate positive X/Y native-value steps and an explicit mode: `move` translates every finite bound on that axis, `min` changes only a finite minimum, and `max` changes only a finite maximum. Do not synthesize a missing open bound. Reject any step that crosses the opposite finite bound, update the numeric inputs and preview immediately, and report the axis and applied amount.

## Rectangle-sibling quadrant overview

Some FlowJo workspaces encode a four-quadrant view as four open rectangle sibling Gates rather than a native `QuadrantGate`. Recognize an overview only when exactly four rectangle siblings share one parent, the same ordered two dimensions, one common finite X threshold, one common finite Y threshold, and cover all low/high combinations. Draw the shared vertical and horizontal threshold lines across the complete plot and label all four sibling counts/frequencies. Each membership and percentage still comes from its independently evaluated rectangle Gate.

When editing a recognized group, keep the sibling overview visible and move the shared X/Y thresholds together. Recalculate all four rectangle siblings across every compatible current-session sample and persist four linked edits in one versioned WSP operation. Do not call this native FlowJo QuadrantGate support: execution remains four independent rectangle memberships.

Dragging first changes the in-memory displayed-point preview, then triggers a debounced full-event recalculation across all compatible current-session samples. Persistence must use the versioned Gate Editor workflow, record a change reason, save a distinct WSP, invalidate cached counts from the edited gate and descendants, rerun the reusable strategy, and register a draft child revision.

Polygon editing remains numeric/JSON in this version. Display-axis changes are not persisted into WSP transform definitions.
