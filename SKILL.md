---
name: cytopilot-flow-cytometry-analysis
description: Analyze, replay, adjust, validate, and audit conventional flow-cytometry FCS datasets with CytoPilot using FlowJo WSP workspaces or CytoPilot JSON gating templates. Use when users ask to inspect FCS metadata and channels, bind WSP samples to uploaded FCS files, select and verify compensation matrices, replay or interactively adjust rectangle/polygon gating trees, save an edited gate strategy as a new versioned WSP without overwriting the source, apply a validated WSP strategy to new FCS files, calculate population counts and parent/total frequencies, investigate cache differences, validate an analysis report, or export a traceable analysis bundle. Also use to explain CytoPilot's implemented algorithms and their limitations; do not claim automated gating, spectral unmixing, CFSE, cell-cycle, apoptosis, or inferential-statistics support unless separately implemented and validated.
license: MIT
---

# CytoPilot Flow Cytometry Analysis

Perform a traceable replay of an explicit gating strategy. Treat CytoPilot as a deterministic analysis and audit engine, not as an autonomous biological gate finder.

## Establish the analysis mode

Choose exactly one mode before running calculations:

- **Exact WSP replay**: Pair the original FlowJo WSP with its referenced FCS files. A web batch may queue multiple WSP files against one uploaded FCS pool, but each WSP must be inspected, replayed, validated, versioned, and exported as an independent analysis session and result bundle. Never merge gate trees or cached-count references across WSP files. Require safe sample binding, matching `$TOT`, compatible WSP/FCS compensation, and agreement with cached FlowJo gate counts before calling an individual replay validated.
- **Reusable WSP strategy**: Apply one selected WSP sample's gate tree to new, filename-independent FCS files. Prefer each new FCS file's embedded matrix; use the WSP matrix only as a disclosed fallback. Do not compare new-file counts with the prototype's cached counts.
- **CytoPilot JSON template**: Apply a reviewed template with explicit required channels and rectangle/polygon coordinates. Treat `draft` coordinates as unvalidated until a domain reviewer approves them on representative controls and samples.
- **Gate Editor**: In a reusable WSP analysis session, edit rectangle bounds, polygon vertices, or a recognized four-rectangle quadrant group's shared thresholds. Apply the same gate path/linked quadrant group to every compatible FCS in the current session, recompute with all events, and save a new WSP/versioned template. Never overwrite the source WSP; the edited copy invalidates cached counts from each edited gate and its descendants.
- **Inspection only**: Read FCS/WSP metadata and report compatibility without analyzing populations.

Do not silently change modes. If the request is ambiguous, prefer inspection first.

## Gather minimum inputs

Obtain or infer:

- FCS file(s), plus WSP or CytoPilot template when gating is requested;
- whether files are the WSP's original samples or new samples;
- instrument and acquisition batch, if known;
- expected panel/channel mapping and which parameters require compensation;
- biological controls and gate-review expectations;
- requested outputs and destination.

Ask only when a missing fact changes matrix selection, sample binding, or interpretation. Never invent a gate threshold, channel alias, control result, or phenotype identity.

## Read the required guidance

- Read [references/algorithm-implementation.md](references/algorithm-implementation.md) before explaining calculations, debugging a mismatch, or changing analysis code.
- Read [references/validation-rules.md](references/validation-rules.md) before accepting, rejecting, or interpreting a result.
- Read [references/input-output.md](references/input-output.md) before invoking the CLI, server workflow, validator, or export bundle.
- Read [references/scope-and-extensions.md](references/scope-and-extensions.md) when the request involves transforms, automated gating, spectral cytometry, CFSE/CellTrace, cell cycle, apoptosis, batch correction, or inferential statistics.
- Read [references/gate-editor.md](references/gate-editor.md) before editing geometry, describing edit provenance, or deciding whether an adjusted gate can be used for exact replay.
- Read [references/channel-labels-and-axis-display.md](references/channel-labels-and-axis-display.md) before resolving antibody/stain labels, changing plot transforms or ranges, or using the graphical rectangle editor.
- Read [references/template-lifecycle.md](references/template-lifecycle.md) before creating, reviewing, locking, retiring, or comparing reusable WSP revisions.

## Run the workflow

### 1. Preserve provenance

Work from the supplied files without modifying them. Record absolute input paths only in local provenance, plus file sizes, hashes, CytoPilot version, template/WSP identity, prototype sample for reusable analysis, and analysis mode. Treat the full bundle as sensitive because reports from older CytoPilot versions may contain absolute paths. Before external sharing, create and verify a redacted copy containing logical sample IDs, basenames, hashes, and relative paths only. Keep raw FCS files outside the generated result bundle unless the user explicitly requests a controlled copy.

### 2. Inspect before replay

Inspect every FCS file and the WSP/template. Confirm supported FCS version, readable TEXT/DATA offsets, `$PAR`, `$TOT`, channel names, data type, byte order, matrix presence, required features, gate types, and sample binding. Stop on structural errors instead of guessing.

For an exact WSP replay, require all WSP samples to bind uniquely. A complete basename match is allowed when the original computer path is unavailable; ambiguous duplicate names are not.

For a multi-WSP batch, repeat the complete inspection and replay independently for each WSP. Sharing the uploaded FCS directory is only an input-storage optimization; it does not establish that the WSP files describe the same panel, samples, compensation, gate hierarchy, or validation outcome. Keep a distinct analysis session, validator decision, output directory, and Gate Excel selection context per WSP.

### 3. Resolve compensation

Follow the mode-specific precedence in [references/algorithm-implementation.md](references/algorithm-implementation.md). Never derive compensation from approximate spectra or the CytoPilot panel-design overlap score. Preserve negative compensated values.

For conventional flow, expose compensated features as `Comp-<detector>`. Confirm every compensated gate refers to an available feature. A WSP/FCS matrix disagreement is a hard stop in exact replay.

### 4. Evaluate the gate tree

Use only the implemented rectangle and two-dimensional polygon gates. Apply every child gate within its parent mask. Respect `eventsInside=false` by complementing the gate before intersecting with the parent. Four same-parent open rectangle siblings with the same two dimensions and shared X/Y thresholds may be displayed and edited together. Membership still runs as four rectangle Gates; the editor may atomically version their shared thresholds, but this is not native `QuadrantGate` execution.

Do not rename dimensions or substitute stain labels for detector names. Display a stain/antibody alias only when its WSP/FCS `$PnN`–`$PnS` provenance is recorded; surface a WSP/FCS label mismatch for review. Do not automatically optimize or move gates.

### 5. Edit only through a versioned copy

When the user requests a gate adjustment, require a reusable WSP session and an analyzed sample/gate. Allow only geometry changes that preserve gate type, dimension order, `events_inside`, and parent-child structure. Rectangle bounds may be dragged through visible SVG edge/handle targets, translated as one rectangle by dragging inside the frame, or moved with visible/keyboard arrow controls using explicit X/Y native-value steps and a declared `move`, `min`, or `max` mode. Open bounds must stay open; reject a step that would make `min > max`. Numeric bounds remain available and polygon vertices remain JSON/numeric editing. Show immediate pointer-capture or arrow-step feedback and synchronize the preview with numeric inputs.

During interaction, calculate an immediate displayed-point preview for the current sample, then debounce an exact all-event recalculation of the same gate path across every compatible FCS in the current session. Replace report Gate rows, Count, `% Parent`, `% Total`, the left Gate tree, and export preview with the exact result. Treat any displayed-point value as provisional when the plot is subsampled. **应用到全部样品并重算** performs this step explicitly; **另存 WSP** must perform it automatically when the current geometry has not yet received an exact all-sample recalculation.

Use the Gate Editor API/UI to validate the new bounds or vertices, recompute all compatible FCS files, and write a managed new WSP under the gate-edit storage directory. Record revision lineage, source/edited hashes, actor, session, recorded change reason, gate path, original/edited geometry, and invalidated cached-count scope. When the user clicks **另存 WSP**, request a local destination through the browser's folder picker and copy the generated WSP there without replacing an existing file; choose a collision-safe suffixed filename when needed. If the browser cannot expose a folder picker, fall back to an authenticated file download and disclose the fallback. The managed WSP and manifest remain the audit copies regardless of the local export. Keep the original WSP path read-only.

If the selected Gate belongs to a recognized four-rectangle quadrant sibling group, keep the full cross and all four labels visible in edit mode. Move the shared X/Y thresholds as one group, preview all four siblings, and persist the four linked rectangle edits atomically in the new WSP version. Reject partial or structurally ambiguous groups.

Do not call an edited result an exact replay of the original WSP. It is a new gate strategy and must undergo visual and biological review.

### 6. Calculate statistics

For every gate report:

- event count;
- parent event count;
- total sample event count;
- percent of parent;
- percent of total;
- cached FlowJo count and difference in exact replay;
- gate path, type, dimensions, and status.

Always name the denominator. Do not interpret a low-count population as biologically absent.

### 7. Validate deterministically

Require `report_schema_version=cytopilot-analysis-report-1.1` and an embedded `analysis_mode` matching the requested mode. CytoPilot Web/API analyses automatically run the bundled validator, attach `skill` and `validation` objects to the report, persist the decision in the session/history, and include `validation_result.json` in exact-replay bundles. Do not bypass or replace that result in an explanation.

For a detached report or command-line audit, run the same bundled validator from the workspace root:

```powershell
python skills/cytopilot-flow-cytometry-analysis/scripts/validate_analysis_report.py analysis_report.json --mode exact-wsp --pretty
```

Use `--mode reusable-wsp` for new-file application and `--mode json-template` for template analysis. Resolve paths relative to the current workspace; use the bundled Python runtime if `python` is unavailable.

Treat decisions as follows:

- `VALIDATED`: the report's declared computational invariants passed and no condition requires review.
- `REVIEW_REQUIRED`: calculations are internally coherent, but warnings, fallback compensation, low event counts, or other review conditions remain.
- `REJECTED`: a structural, compensation, binding, cache-equivalence, or arithmetic rule failed.

Never downgrade `REJECTED` to a warning without changing the data, template, implementation, or an explicitly versioned validation policy.

The validator does not authenticate an edited JSON file against raw FCS/WSP content. Validate immediately after analysis, retain the generated bundle and hashes, and do not call a manually edited or detached report source-verified.

Treat every newly registered reusable WSP and every Gate Editor output as `draft` until laboratory review changes its lifecycle status. A draft reusable template may be analyzed for review, but the automatic result must remain `REVIEW_REQUIRED` even when its arithmetic is internally valid.

### 8. Perform biological review

Computational validity is necessary but insufficient. Inspect parent distributions, gate geometry, back-gating, negative/unstained controls, single-stain controls, FMOs for critical or continuous boundaries, expected lineage relationships, sample quality, and cross-sample consistency. Require a qualified reviewer before labeling a template `validated` or `locked`.

### 9. Export and communicate

Prefer the CytoPilot versioned analysis bundle. Report:

1. analysis mode and inputs;
2. binding and channel compatibility;
3. compensation source per sample;
4. population statistics with denominators;
5. cache agreement for exact replay;
6. warnings, validator decision, and biological review items;
7. limitations and unsupported requests;
8. output paths and manifest/hash coverage.

For reusable-workbench Gate Excel, require an explicit Gate-by-statistic selection. Count and Percentage are independent choices. For every Percentage column, record whether the denominator is Parent, Grandparent, Total, or a named ancestor Gate; do not silently add an unselected metric or substitute another denominator.

## Guardrails

- Never claim that a replay reproduces FlowJo when any cached gate count differs.
- Never apply a WSP matrix to new FCS files without disclosing `workspace_fallback`.
- Never overwrite or edit the source WSP in place; every gate adjustment must produce a distinct WSP/template and manifest.
- Never accept an arbitrary browser-entered server filesystem path as the Gate Edit destination. Use the managed storage root plus a user-mediated local folder picker/download, and never overwrite an existing local export silently.
- Never compare an edited gate's counts to the original cached WSP counts as if the geometry were unchanged.
- Never zero-clip compensated fluorescence values.
- Never describe Linear/Log/Biex plot controls as membership transforms. Log may hide non-positive plot coordinates, but statistics must continue to use all events.
- Never call a spectral-overlap estimate a compensation coefficient.
- Never infer population identity from geometric location alone.
- Never substitute automated GMM/clustering for a reviewed gate tree under this skill.
- Never report CFSE, cell-cycle, or apoptosis metrics from ad hoc peak fitting as validated CytoPilot results.
- Never pool events across biological replicates to manufacture sample-level replication.
- Never pool, concatenate, or reconcile gate trees across WSP files in a batch. A failed or rejected WSP must not invalidate or relabel another WSP's independent result, and batch completion must report each per-WSP outcome.
- Never run hypothesis tests without an explicit experimental unit, grouping variable, and prespecified statistical method.

## Coordinate with panel design

Use `$cytopilot-design-panel` when the task is to design or review marker-fluorophore assignments, detector conflicts, reagent availability, or control requirements before acquisition. Use this skill after acquisition to inspect actual FCS metadata, select empirical compensation, replay gates, and validate results. Keep predicted spectral risk separate from measured compensation.
