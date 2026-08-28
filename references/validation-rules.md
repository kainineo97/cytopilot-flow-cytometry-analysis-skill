# Validation rules

## Contents

1. Decision model
2. Pre-analysis hard stops
3. Computational invariants
4. Exact replay equivalence
5. Reusable-strategy review
6. Biological validation
7. Default event-count policy
8. Change-control rules

## 1. Decision model

Use three decisions:

- `VALIDATED`: all implemented computational checks pass and no declared review condition remains.
- `REVIEW_REQUIRED`: the report is arithmetically coherent, but a fallback, warning, low event count, unsupported biological claim, or manual review item remains.
- `REJECTED`: inputs cannot be safely associated, an algorithm prerequisite fails, arithmetic is inconsistent, or exact replay disagrees with its reference.

Never equate `VALIDATED` with biological correctness. It means validated against the stated computational policy and available reference data.

## 2. Pre-analysis hard stops

Reject before population interpretation when any of these occurs:

- unsupported or malformed FCS version, HEADER, TEXT, DATA, `$PAR`, `$TOT`, parameter metadata, or event encoding;
- invalid spillover dimensions, missing matrix parameters, or singular matrix;
- ambiguous or incomplete WSP-to-FCS binding in exact replay;
- WSP sample count different from FCS `$TOT` in exact replay;
- WSP and FCS matrices disagree in exact replay;
- required gate feature/channel is absent;
- unsupported gate type, empty rectangle dimensions, non-2D polygon, or polygon with fewer than three vertices;
- template schema or status is unsuitable for the requested use;
- output path would place the bundle inside the raw FCS input directory.

## 3. Computational invariants

The bundled validator enforces these rules for every analyzed sample and gate:

- report schema and embedded analysis mode match the validator invocation;
- sample IDs, FCS paths, and gate path segments are present and unique;
- counts are finite non-negative integers;
- `gate_count <= parent_count <= total_count`;
- each root's parent count equals the sample event count, and each child's parent count equals its actual parent gate count;
- gate `total_count` equals sample `event_count`;
- percentages are finite and strictly within `[0, 100]`;
- `percent_parent` equals `100 * count / parent_count`, or zero for an empty parent;
- `percent_total` equals `100 * count / total_count`, or zero for an empty sample;
- gate type, dimensions, geometry, and polygon vertices are structurally valid;
- compensation source belongs to the mode-specific allowlist, and a gate using `Comp-*` cannot have source `none`;
- report/sample aggregates equal the actual arrays and statuses;
- an analyzed/replayed sample contains at least one gate result;
- incompatible, unbound, or error sample status cannot be accepted as validated.

Default absolute percentage tolerance is `1e-6`. The hard maximum is `0.01` percentage points. A wider-than-default policy always requires review; override it only with a recorded policy file when a named serialization or rounding layer requires it.

## 4. Exact replay equivalence

Require all of the following:

- every WSP sample binds uniquely;
- sample `$TOT` equals the cached sample count;
- matrix selection passes the strict equality policy;
- every supported gate has a cached reference count;
- `count_difference` equals recalculated count minus cached count, status is derived from that difference, and every recalculated gate count exactly equals its cached count;
- report and sample statuses contain no cache-difference state.

One event of difference is still a failed equivalence check. Investigate transform semantics, boundary inclusion, matrix order/precision, event decoding, unsupported gate types, or an incorrect file binding. Do not normalize the difference by population size to call it a match.

If the scientific goal permits a tolerance-based comparison, define a separate versioned validation protocol. Do not alter the meaning of `CACHE_MATCH`.

## 5. Reusable-strategy review

Do not compare new sample counts with prototype cached counts. Instead require:

- required detector/`Comp-*` features are present;
- acquisition settings and panel mapping are compatible with the template's intended domain;
- embedded per-file compensation is preferred;
- `workspace_fallback` is disclosed and manually reviewed;
- gates are visually reviewed on representative parent distributions;
- edge populations and expected lineage relations are checked;
- gate coordinates are not assumed portable across changed scaling, voltage, detector, sample preparation, or transform conventions.
- WSP `$PnS` template labels and current FCS `$PnS` labels are compared for each matched detector; a non-empty mismatch requires review and must not be hidden by detector compatibility.

Mark `INCOMPATIBLE_PANEL` or `PARTIAL_INCOMPATIBLE` as rejected for a complete-run claim. A partial report may still be delivered if every omitted sample is clearly listed.

## 6. Biological validation

Require evidence appropriate to the experiment:

- unstained/negative samples for baseline and autofluorescence context;
- single-stain controls acquired under compatible settings for compensation review;
- FMOs for dim, continuous, spread-affected, or decision-critical gates;
- viability and singlet strategy when required by the assay;
- back-gating into scatter space;
- expected parent-child phenotype relationships;
- sufficient events for the intended rare-population precision;
- replicate-level consistency and explicit exclusion criteria;
- blinded/manual comparison when releasing a reusable template.

Store reviewer identity, date, representative dataset hashes, CytoPilot version, template version, and acceptance outcome outside or alongside the analysis bundle according to the project's audit policy.

## 7. Default event-count policy

The validator defaults are conservative triage thresholds, not universal biological laws:

- fewer than 1,000 total sample events: `REVIEW_REQUIRED`;
- a non-empty reported population below 100 events: `REVIEW_REQUIRED`;
- zero-event population: `REVIEW_REQUIRED`, never automatically “marker-negative” or “population absent.”

Use binomial precision or a study-specific power/LOD model to set assay thresholds. For a proportion `p` observed from `n` independent events, the rough standard error is `sqrt(p(1-p)/n)`, but event independence and sampling representativeness must be justified.

## 8. Change-control rules

When changing parsing, compensation, transforms, or gating:

1. Add unit tests for nominal, boundary, and failure cases.
2. Replay versioned representative WSP/FCS fixtures.
3. Compare every gate count, not only final populations.
4. Explain expected differences and obtain domain review.
5. Bump the relevant code/template/schema version.
6. Preserve old outputs and hashes for traceability.

Do not validate new automated or assay-specific algorithms solely against synthetic data. Use independent, representative experimental datasets and an accepted reference method.

For interactive edits, additionally require a modification reason, immutable source hash, distinct output path/hash, parent/root revision lineage, forward-only lifecycle transition, cache invalidation from the edited gate and descendants, and reusable-strategy recalculation. Axis display changes alone must not change counts. For Log display, reject non-positive user bounds and disclose non-positive coordinates omitted from the visualization.
