# Input, execution, and output guide

## Contents

1. Supported inputs
2. Inspection commands
3. Analysis commands and APIs
4. Validator contract
5. Output bundle
6. Reporting checklist

## 1. Supported inputs

- FCS 2.0, 3.0, or 3.1 files supported by the CytoPilot parser.
- FlowJo `.wsp` XML workspaces containing rectangle or polygon gates.
- CytoPilot JSON templates conforming to schema version `flowagent-template-0.1` in the compatible runtime.
- CytoPilot JSON analysis reports from exact, reusable, or JSON-template workflows.

Treat `.hws` files and unsupported FlowJo gate types as non-executable unless a separate importer converts and validates them.

## 2. Inspection commands

From the CytoPilot repository:

```powershell
cytopilot inspect-fcs "C:\data\sample.fcs" --json
cytopilot scan-fcs "C:\data\batch"
cytopilot inspect-wsp "C:\data\analysis.wsp" --fcs-dir "C:\data\batch"
```

If the console script is unavailable, use the environment's Python with the project installed or `src` on its import path. Do not install packages or change the environment without user authorization.

## 3. Analysis commands and APIs

### Exact WSP replay

```powershell
cytopilot analyze "C:\data\analysis.wsp" --fcs-dir "C:\data\batch" --json-output "C:\results\analysis_report.json"
```

The web application exposes `POST /api/analyze-workspace` and creates a versioned analysis bundle.

The web interface may upload multiple WSP files into one managed input batch. It queues the existing single-WSP API once per WSP, using the same uploaded FCS directory only as a candidate binding pool. Every queued WSP receives its own inspection record, exact-replay report, validator decision, analysis session, project suffix, and immutable result bundle. The interface exposes a current-WSP selector so Gate statistics and Excel columns are selected and exported against one session at a time. Do not merge counts, cached references, gate paths, or validation decisions across WSP files.

After an exact replay completes, the main replay button becomes **开始新的 WSP 重放**. Activating it clears the managed WSP/FCS paths from the form, current session ID, gate selections, visible results, and validation display, then returns to the upload step. It must not silently rerun the previous managed batch. This UI reset does not delete previously saved analysis records or immutable result bundles.

### Reusable WSP strategy

Use the CytoPilot reusable-analysis interface or `POST /api/analysis/reusable/run` after registering/reviewing the WSP template. Record the returned prototype sample ID. The server applies the template to every `.fcs` file in the selected directory.

The workbench plot response includes canonical `available_dimensions`, `feature_labels` with WSP/FCS `$PnS` provenance, label-mismatch notices, WSP axis transform metadata, and native gate geometry. Display transform/range changes remain browser-side and do not change the analysis report.

Reusable Gate statistics are exported through `POST /api/analysis/session/export` with `export_contract_version: 2` and explicit `selected_statistics`. Count and Percentage are selected independently for each Gate. Every selected Percentage records one denominator: Parent, Grandparent, Total, or a named ancestor Gate. The server must generate only those explicit Gate × metric columns and return the selected-statistic count so the browser can reject a stale or incompatible response before download.

Gate Edit calls `POST /api/analysis/session/gate-edit` with geometry and a required `change_reason`. Administrators promote or retire a revision through `POST /api/analysis/template/lifecycle`; ordinary users cannot change lifecycle state.

### CytoPilot JSON template

```powershell
cytopilot analyze-template "templates\my-template.json" "C:\data\sample-1.fcs" "C:\data\sample-2.fcs"
```

`draft` templates are suitable for exploration, not unattended production interpretation.

## 4. Validator contract

CytoPilot's Web/API runtime loads this Skill's validator as the canonical validation implementation. Exact WSP replay, reusable WSP analysis, and Gate Editor recalculation automatically attach:

- `skill.id`, `skill.version`, and local deterministic execution mode;
- `validation.decision`, effective policy and findings;
- validator/policy SHA-256 values and validation timestamp;
- `biological_review_status`, initially `not_started`.

The standalone command below remains available for detached reports and produces the same rule decisions.

The report contract is `cytopilot-analysis-report-1.1`. It requires:

- `report_schema_version`, embedded `analysis_mode`, mode-appropriate report status, and exact sample aggregates;
- unique `sample_id` and `fcs_path` values;
- unambiguous gate `path_segments`, gate type, dimensions, and geometry;
- mode-specific compensation sources;
- template status for JSON-template analysis;
- exact arithmetic relationships among cached count, recalculated count, difference, and status.

Legacy or manually assembled reports missing these fields are rejected rather than guessed. The validator checks report integrity, not raw-file authenticity; retain the generated manifest and input hashes.

Run:

```powershell
python skills/cytopilot-flow-cytometry-analysis/scripts/validate_analysis_report.py analysis_report.json --mode exact-wsp --pretty
```

Modes are `exact-wsp`, `reusable-wsp`, and `json-template`.

Optional policy JSON:

```json
{
  "percent_abs_tolerance": 0.000001,
  "minimum_sample_events": 1000,
  "minimum_population_events": 100,
  "review_zero_event_populations": true,
  "review_report_warnings": true
}
```

Invoke it with `--policy policy.json`. Unknown policy keys, invalid types, negative thresholds, non-finite values, event thresholds above `2^63-1`, and percentage tolerances above `0.01` percentage points are rejected. Any tolerance wider than the default `1e-6` forces `REVIEW_REQUIRED` and must identify the serialization or rounding layer that requires it.

Validator output contains:

- `decision`: `VALIDATED`, `REVIEW_REQUIRED`, or `REJECTED`;
- `mode` and effective `policy`;
- `summary` counts of errors, warnings, and informational findings;
- `findings`, each with severity, rule ID, scope, and message.

Exit codes:

- `0`: `VALIDATED`;
- `1`: `REVIEW_REQUIRED`;
- `2`: `REJECTED` or invalid input/policy.

## 5. Output bundle

CytoPilot's exact replay export contains:

```text
<project>_<analysis-id>/
|-- manifest.json
|-- results/
|   |-- sample_summary.csv
|   |-- population_statistics.csv
|   |-- warnings.csv
|   |-- analysis_report.json
|   `-- validation_result.json
|-- reports/
|   `-- analysis_report.html
|-- plots/
|-- template/
|   `-- <workspace>.wsp
`-- logs/
    `-- analysis.log
```

The `cytopilot-analysis-1.1` manifest records schema, analysis ID, timestamp, CytoPilot/Skill versions, analysis mode, validation decision, validator/policy hashes, biological-review status, WSP hash, FCS basenames/sizes/hashes, and output inventory. It explicitly records `original_fcs_copied: false`. Schema `cytopilot-analysis-report-1.1` exports basenames rather than absolute WSP/FCS paths. Treat bundles from older versions as sensitive; before external sharing, scan the manifest, JSON, CSV, HTML, and logs for the original source-root string.

## 6. Reporting checklist

Include:

- analysis mode and CytoPilot version;
- WSP/template/prototype identity;
- sample binding outcome;
- FCS versions, event counts, detector/stain mapping, and parser warnings;
- compensation source and any matrix disagreement/fallback notice;
- gate path, dimensions, count, parent count, `% parent`, and `% total`;
- exact replay cached count/difference;
- validator decision and every error/warning;
- biological controls reviewed and reviewer status;
- unsupported features and interpretive limitations;
- bundle path and manifest coverage.
