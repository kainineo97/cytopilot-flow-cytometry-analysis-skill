# Implemented algorithms

## Contents

1. FCS parsing and event loading
2. WSP parsing and sample binding
3. Compensation selection and calculation
4. Feature space and transformations
5. Gate evaluation
6. Population statistics
7. Replay modes
8. Plot sampling and export provenance

## 1. FCS parsing and event loading

A compatible CytoPilot runtime implements FCS 2.0, 3.0, and 3.1 parsing. The runtime source is not bundled in this skill repository.

1. Read the fixed 58-byte HEADER.
2. Resolve TEXT and DATA byte offsets from the HEADER, falling back to `$BEGINDATA` and `$ENDDATA` when the DATA offsets are zero.
3. Decode TEXT as Latin-1 and honor an escaped delimiter represented by two adjacent delimiters.
4. Require an even number of TEXT key/value tokens.
5. Require valid `$PAR` and `$TOT` values.
6. Build channel records from `$PnN`, `$PnS`, `$PnB`, `$PnR`, `$PnE`, and `$PnV`.
7. Parse the first available `$SPILLOVER`, `SPILLOVER`, `$SPILL`, or `SPILL` keyword as an `n x n` matrix.
8. Memory-map the DATA segment using `$DATATYPE` and `$BYTEORD`.

Supported event encodings are 32-bit float (`F`), 64-bit float (`D`), and uniform-width unsigned integer (`I`) parameters of 8, 16, 32, or 64 bits. Mixed-width integer parameters are rejected. CytoPilot warns when the DATA byte length differs from the length implied by `$TOT`, `$PAR`, and parameter widths.

## 2. WSP parsing and sample binding

CytoPilot parses FlowJo XML without depending on namespace prefixes. It extracts FlowJo/schema versions; sample IDs, names, counts, and dataset URIs; spillover matrices and transform metadata; nested populations; rectangle and polygon gate definitions; and cached population counts.

Bind a WSP sample in this order:

1. Use its original dataset URI if the file still exists.
2. Otherwise match the complete filename case-insensitively in the supplied directory.
3. If duplicates exist, use `$FIL` plus compatible event count only when that yields one unique candidate.
4. Otherwise leave the sample unbound.

Exact replay stops if any sample remains unbound. It also stops when WSP sample count and FCS `$TOT` differ. This deliberately favors false refusal over analyzing the wrong file.

## 3. Compensation selection and calculation

### Exact WSP replay

- If only FCS contains a matrix, use it and record source `fcs`.
- If only WSP contains a matrix, use it and record source `workspace`.
- If both contain matrices, require identical ordered parameter lists and maximum absolute coefficient difference no greater than `1e-6`. Stop on disagreement.
- If neither contains a matrix, record `none`.

### Reusable WSP strategy

- Prefer the new FCS file's embedded matrix and record `fcs_embedded`.
- If both matrices exist but differ, continue with the new FCS matrix and emit a notice.
- If the new FCS lacks a matrix, use the prototype WSP matrix as `workspace_fallback` and require review.
- If neither exists, record `none`.

### Linear algebra

Let `R` be the event-by-channel raw fluorescence matrix and `S` the ordered spillover matrix. CytoPilot solves:

```text
S^T C^T = R^T
```

with `numpy.linalg.solve`, equivalent to `C = R (S^-1)^T`. Solving is preferred to explicitly constructing an inverse. Reject a singular matrix, a non-square matrix, or matrix parameters absent from the FCS detector list. Apply compensation exactly once and expose each result as `Comp-<parameter>`. Preserve finite negative values.

The implementation does not calculate a compensation matrix from single-stain controls and does not perform spectral unmixing.

## 4. Feature space and transformations

The feature map initially contains raw detector arrays keyed by `$PnN`. When a matrix exists, it adds `Comp-*` arrays.

WSP transforms such as biexponential/logicle are currently parsed and returned as axis metadata for display. They are not numerically applied by `build_feature_map` or gate membership evaluation. Therefore:

- interpret gate coordinates in the data space represented by the WSP definitions;
- use FlowJo cached-count agreement as the operational equivalence check;
- reject any claim of exact FlowJo equivalence when counts differ;
- do not use `log1p`, clipping, or another substitute transformation without implementing and validating it as a versioned change.

The web plot resolves display aliases by pairing WSP `$PnN` and `$PnS` keywords. A `Comp-*` feature is matched after removing one leading `Comp-`; the canonical feature name remains unchanged. The current FCS `$PnS` is compared with the WSP label and a mismatch is surfaced for review.

Plot controls can display Linear, Log, or the existing Biex/logicle `asinh` approximation, with native-value min/max and an optional positive Scale. These controls never alter feature arrays or membership. Log omits non-positive plot coordinates and reports that omission while counts continue to use all events. Rectangle dragging applies the display inverse to map the pointer back to native gate coordinates; saving still uses the versioned Gate Editor workflow.

## 5. Gate evaluation

### Rectangle gate

For every dimension `d`, apply inclusive bounds `minimum_d <= value_d <= maximum_d`. Omit a comparison when the corresponding bound is absent. Intersect all dimensions.

### Polygon gate

Require exactly two dimensions and at least three two-coordinate vertices. Use an odd-even ray-casting test across polygon edges. Boundary membership can depend on floating-point geometry; validate representative boundary cases before changing the implementation.

### Complement and hierarchy

If `eventsInside` is false, complement the geometric mask. For population `k`:

```text
membership_k = membership_parent AND geometric_mask_k
```

Root populations use an all-events parent mask. Children can never contain more events than their parent.

Only rectangle and polygon gates are implemented. Ellipsoid, quadrant, Boolean, and other FlowJo/Gating-ML gate types are not executable.

### Four-rectangle quadrant overview

CytoPilot recognizes a quadrant-like sibling group when exactly four rectangle populations have the same parent, identical ordered X/Y dimensions, one open side on each dimension, all four low/high signatures, and numerically equal shared X/Y thresholds (`numpy.isclose`, `rtol=1e-9`, `atol=1e-9`). The renderer draws the two shared threshold lines and labels the four independently computed sibling results. The Gate Editor may move the shared thresholds and persist four linked rectangle edits atomically, but membership is still evaluated as four rectangles and does not execute a native QuadrantGate.

### Gate Edit preview and all-sample recalculation

For rectangle/polygon interaction, the browser first applies the candidate geometry to the displayed parent-event coordinates. If all parent events are displayed, the preview Count is exact; otherwise it estimates Count as `parent_count × displayed_inside/displayed` and marks the preview basis. A debounced server request then deep-copies the prototype tree, applies the validated geometry without writing the WSP, and calls the normal full-event tree evaluator for every compatible FCS recorded in the current session. The exact Gate rows replace the provisional current-sample result and synchronize Count, percent-parent, percent-total, descendants, tree labels, and export data across samples. Saving repeats analysis from the newly versioned WSP and never discovers unrelated FCS files from the surrounding directory.

## 6. Population statistics

For each gate, let `n` be its membership count, `p` its parent count, and `N` the FCS `$TOT` count:

```text
percent_parent = 100 * n / p, or 0 when p = 0
percent_total  = 100 * n / N, or 0 when N = 0
count_difference = n - cached_count
```

Exact replay assigns `CACHE_MATCH`, `CACHE_DIFFERENCE`, or `NO_CACHE_REFERENCE`. Reusable strategies clear prototype cached counts and therefore produce `NO_CACHE_REFERENCE`. Analysis-report schema `cytopilot-analysis-report-1.1` also exports `path_segments` so population names containing `/` cannot corrupt hierarchy validation, plus versioned gate geometry for structural validation.

These are descriptive event statistics. They are not estimates of biological replicate variance and do not justify a hypothesis test by themselves.

## 7. Replay modes

`analyze_workspace` performs strict sample binding, `$TOT` checking, matrix agreement, event loading, gate replay, and cached-count comparison.

`analyze_reusable_workspace` selects a prototype sample, deep-copies its gate tree, removes cached counts, determines required gate dimensions, and applies the tree to each new FCS file. Files lacking required features are marked `INCOMPATIBLE_PANEL` rather than partially gated.

`analyze_template` loads a CytoPilot JSON template, checks `panel.required_channels`, uses an embedded FCS matrix when present, and evaluates the explicit tree.

## 8. Plot sampling and export provenance

Gate plots use the parent population, not all events. If the parent exceeds 12,000 events by default, CytoPilot samples without replacement using a seed derived from SHA-256 of the resolved FCS path and gate path. The result is deterministic for the same resolved path and gate path, but moving the file can change the displayed subsample. Counts always use all events.

Reusable-workbench Excel export uses export contract v2. The client sends an explicit ordered list of Gate × metric selections. Count has no denominator. Percentage requires Parent, Grandparent, Total, or a named ancestor Gate and is computed from all events, never from the plotted subsample. The server validates every Gate/metric/denominator combination and returns the selected-statistic count so the browser can reject a stale backend response before download. It must not expand a selected Gate into unrequested Count or Percentage columns.

The analysis bundle is written through a staging directory and atomically renamed. It contains CSV/JSON results, warnings, an HTML report, a WSP copy, logs, a manifest, and SHA-256 hashes of WSP/FCS inputs. It records but does not copy raw FCS files.
