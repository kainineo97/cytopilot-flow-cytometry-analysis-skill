# Scope and extension requirements

## Current validated computational scope

The current CytoPilot engine supports:

- FCS metadata inspection and event loading within the documented encodings;
- embedded/WSP conventional compensation matrix application;
- FlowJo WSP parsing and safe sample binding;
- rectangle and two-dimensional polygon gate replay;
- nested population counts and parent/total percentages;
- cached-count equivalence checks for exact replay;
- filename-independent reuse of one WSP gate tree;
- deterministic gate-plot subsampling;
- WSP/FCS detector-to-stain display labels with mismatch notices;
- display-only Linear, Log, and Biex/logicle approximation controls;
- graphical rectangle-bound dragging with numeric synchronization and versioned save;
- display-only reconstruction of a full four-quadrant view from exactly four same-parent open rectangle siblings with shared X/Y thresholds;
- reusable WSP revision lineage and administrator-controlled lifecycle;
- traceable result bundles and input hashes.

## Parsed or displayed but not numerically implemented

CytoPilot parses WSP transform definitions and reports them as plot-axis metadata. The browser can switch between Linear, Log, and the current signed `asinh` Biex/logicle approximation and adjust display ranges/Scale. It does not apply those transforms during feature construction or gate evaluation, and it does not persist display settings into the WSP. Treat cache agreement as the equivalence test; do not claim transform parity independently.

## Not implemented under this skill

- compensation-matrix estimation from single-stain controls;
- spectral unmixing;
- time/drift, clog, doublet, viability, or acquisition-anomaly QC unless explicitly represented by gates;
- automated GMM, FlowSOM, clustering, dimensionality reduction, or learned gate transfer;
- CFSE/CellTrace generation fitting and proliferation indices;
- Dean-Jett-Fox or other cell-cycle models;
- native FlowJo/Gating-ML QuadrantGate execution (recognized four-sibling rectangle groups can be edited atomically as linked rectangle revisions, but are not native QuadrantGate objects);
- Annexin V/PI biological interpretation beyond explicit user-defined quadrants;
- batch correction or cross-instrument normalization;
- replicate aggregation, hypothesis testing, multiple-comparison correction, or power analysis;
- phenotype assignment from marker geometry without an explicit reviewed definition.

Do not implement these ad hoc inside an answer. Propose a separate versioned module and validation plan.

## Minimum validation for an extension

For every new algorithm, define:

1. intended use and prohibited use;
2. exact mathematical specification and parameterization;
3. required controls and input-quality checks;
4. deterministic behavior, seeds, and numerical tolerances;
5. failure modes and hard-stop conditions;
6. reference implementation or accepted comparator;
7. synthetic unit tests for known edge cases;
8. independent experimental validation datasets;
9. per-sample and aggregate acceptance metrics;
10. versioning, provenance, and reviewer sign-off.

## Assay-specific examples

### CFSE/CellTrace

Require explicit generation ordering, peak-area rather than peak-height accounting, background/autofluorescence handling, undivided control, fit uncertainty, unresolved-generation behavior, and comparison against an accepted analysis tool. Do not assign generations merely by sorting arbitrary detected peaks.

### Cell cycle

Require singlet gating on DNA pulse geometry, debris/sub-G1 policy, model equations, parameter bounds, optimization diagnostics, residual checks, phase-area integration, and reference comparison. A pair of Gaussian peaks plus an unconstrained linear S-phase is not sufficient to claim a Dean-Jett-Fox implementation.

### Apoptosis

Require explicit quadrant thresholds derived from controls, compensation review, timepoint/treatment context, and terminology policy. Annexin V-negative/PI-positive events must not be called necrotic without experimental context.

### Automated gating

Require population-identity rules independent of cluster index, preprocessing parity, seed control, rare-population metrics, stability analysis, out-of-distribution detection, and human override/audit logs. Never label the middle GMM component as lymphocytes by default.

### Inferential statistics

Use biological samples, not events, as experimental units unless the study design explicitly supports another unit. Prespecify contrasts, transformations, missing-data handling, covariates, multiple-testing control, and effect-size/confidence-interval reporting.
