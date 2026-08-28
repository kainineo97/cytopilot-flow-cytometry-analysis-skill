# Gate Editor guide

## Purpose

Gate Editor adjusts an existing WSP strategy inside a reusable analysis session and saves the result as a new versioned WSP. It is a controlled geometry editor, not an automatic gate finder.

## Supported edits

- Rectangle: drag visible SVG edges/circular handles on the interactive preview, drag inside the shaded frame to translate finite bounds, use visible or keyboard arrow controls, or change finite/empty `min`/`max` bounds for existing dimensions. Arrow controls require explicit X/Y native-value steps and a declared mode: move all finite bounds, adjust only `min`, or adjust only `max`. Open bounds remain open. A successful pointer press reports capture before movement; every arrow step reports the changed axis and amount.
- Polygon: replace the finite two-dimensional vertex list with at least three vertices.

The first implementation preserves the original gate type, detector/dimension order, `events_inside`, and parent-child hierarchy. It does not add dimensions, rename detectors, change compensation, or convert rectangle to polygon.

## Required workflow

1. Run or load a `reusable-wsp` analysis session.
2. Select a compatible analyzed sample and gate.
3. Open **调整当前圈门**.
4. For a rectangle, drag the plotted boundary, use the visible/keyboard arrow controls, or enter bounds; for a polygon, enter vertices.
5. During dragging/input, inspect the immediate current-sample preview. If the plot is downsampled, treat that value as provisional. CytoPilot then uses all events to recalculate the same gate path for every compatible FCS in the current session.
6. Optionally choose **应用到全部样品并重算** to inspect the exact all-sample result before saving. If this step is omitted or geometry changed afterward, save performs the same exact recalculation automatically.
7. Choose **另存 WSP**, then select a local folder in the browser. Cancelling the picker stops the operation before a new version is created. CytoPilot copies the source WSP to a managed edit directory, changes the selected prototype gate (or all four linked rectangle siblings for a recognized quadrant group), clears cached counts from every edited gate and descendants, and reruns the new WSP strategy on the current session's exact FCS set.
8. CytoPilot registers the managed WSP as a separate reusable template and copies only the edited WSP to the chosen local folder. If a file with the same name already exists, it uses a numbered suffix instead of overwriting it. Browsers without the folder-picker API receive an authenticated download fallback.
9. Review the new counts, gate plots, controls, managed manifest, and locally saved WSP before using it.

## Non-overwrite guarantee

The server refuses a destination equal to the resolved source path. The edit result is written below:

```text
data/storage/analysis_gate_edits/<edit-id>/
├── <source-stem>.gate-edit.v1.wsp
└── gate-edit-manifest.json
```

The manifest contains:

- `source_wsp_sha256` and `edited_wsp_sha256`;
- original and edited geometry;
- sample ID and path segments;
- actor and source session ID;
- modification reason and template revision lineage;
- `original_wsp_overwritten: false`;
- `cached_counts_invalidated_from_edited_gate: true`.

The edited WSP is also registered as a new reusable template with a new template record. The original WSP template record and file remain unchanged. A user-selected local folder receives an additional WSP copy only; the manifest and authoritative audit copy stay in managed storage. The UI does not ask the user to type a server filesystem path.

## Recalculation semantics

The interactive layer first recomputes the current plot's displayed parent events so Count and percentages move with the boundary. When the plot is sampled, Count is an estimate and is marked as a display-sample preview. After a short debounce—or immediately after **应用到全部样品并重算**—the server deep-copies the prototype gate tree, applies the edited geometry in memory, and reevaluates all gates with all events for every compatible FCS in the current session. Those exact Gate rows replace the provisional Count, `% Parent`, `% Total`, left-tree values, and export preview.

The edited copy is then analyzed as `reusable-wsp`. The prototype cached counts are removed from the edited gate and all descendants because their old values no longer describe the new geometry. New FCS files are analyzed with the edited gate tree and the normal compensation precedence.

The result is not an exact replay of the source WSP. `CACHE_MATCH` against the source WSP is no longer an acceptance criterion. Report the edit ID, source/edited hashes, changed path, and new counts instead.

## Server API

The web UI calls the non-persistent preview endpoint:

```text
POST /api/analysis/session/gate-preview
```

Recognized quadrant groups use:

```text
POST /api/analysis/session/quadrant-preview
```

Persistence uses:

```text
POST /api/analysis/session/gate-edit
```

After persistence, the authenticated owner (or an administrator) may retrieve only that edited session's WSP through:

```text
GET /api/analysis/session/edited-wsp?id=<edited-session-id>
```

The endpoint rejects unauthenticated users, non-owners, sessions without Gate Edit provenance, missing files, and non-WSP targets.

Payload shape:

```json
{
  "session_id": "source-analysis-session-id",
  "sample_id": "new-fcs-sample-id",
  "path_segments": ["P1", "P2", "7-AAD"],
  "geometry": {
    "gate_type": "rectangle",
    "dimensions": ["FSC-H", "Comp-BL4-A"],
    "geometry_dimensions": [
      {"parameter": "FSC-H", "min": 1000, "max": 900000},
      {"parameter": "Comp-BL4-A", "min": -1000, "max": 2500}
    ],
    "vertices": [],
    "events_inside": true
  }
}
```

The WSP prototype sample ID is taken from the source session report; the selected sample ID identifies the currently displayed FCS and is not silently treated as the WSP prototype.

## Validation rules

Reject an edit when:

- the session is not `reusable-wsp`;
- the user does not own the session (unless administrator policy permits it);
- the sample or `path_segments` cannot be found uniquely;
- gate type or dimension order changes;
- rectangle bounds are non-finite or `min > max`;
- an arrow step is non-positive/non-finite, targets an absent open bound, or would make `min > max`;
- polygon has fewer than three finite two-dimensional vertices;
- the source WSP is missing;
- the current session contains no compatible analyzed FCS files, or one of its recorded FCS paths is missing;
- the output path resolves to the source WSP.
- the exact all-sample recalculation fails before save.

Human review remains required for boundary placement, self-intersection/biological meaning, rare populations, controls, and cross-sample portability.

Four same-parent open rectangle siblings may be recognized as one quadrant overview only when they form an unambiguous low/high combination on the same ordered dimensions and thresholds. Edit mode keeps the full overview visible, recalculates all four siblings for all current-session samples, and persists their shared threshold change as four linked rectangle edits in one versioned operation. This remains reconstructed rectangle behavior, not native `QuadrantGate` execution.

## What Gate Editor does not do

- It does not modify the original WSP in place.
- It does not infer a new gate from density, clustering, or target frequency.
- It does not treat a downsampled drag preview as final; exact all-event, all-sample recalculation replaces it after debounce/application.
- It does not persist Linear/Log/Biex display controls into WSP transform definitions.
- It does not update an external FlowJo installation automatically.
- It does not make an edited gate comparable to the source WSP cache.
