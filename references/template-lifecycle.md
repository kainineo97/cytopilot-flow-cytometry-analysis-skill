# Reusable WSP template lifecycle

## Revision identity

Every registered reusable WSP has a content SHA-256, immutable template ID, root template ID, revision number, optional parent template ID, actor, timestamps, modification reason, structured change summary, validation decision, reviewer, and review time.

A new content hash creates a new template record. A Gate Edit must point to its source template as `parent_template_id`, inherit the root ID, and use `parent.revision_number + 1`. Re-registering the same content hash updates usage metadata without creating another revision.

## Lifecycle

Supported states and administrator-controlled forward transitions are:

```text
draft -> validated -> locked -> retired
   \-----------> retired
```

- `draft`: exploratory analysis is allowed, but automatic validation remains `REVIEW_REQUIRED`.
- `validated`: a named reviewer has accepted the declared computational and biological review evidence.
- `locked`: approved for laboratory reuse; the same template record cannot be downgraded or changed through ordinary save operations.
- `retired`: no new production use; historical sessions and files remain readable.

Every lifecycle transition requires a reason and is written to the template record and audit log. Locked templates may be used as the parent of a new draft revision; they are never edited in place.

## Gate Edit revision

Require a non-empty modification reason before saving. The structured change summary records edit ID, gate path, original geometry, and edited geometry. The Gate Edit manifest records the reason, source/edited hashes, actor, session, and non-overwrite/cache-invalidation guarantees.

The edited WSP, analysis session, history record, and child template revision are distinct objects. A successful recalculation does not promote the child revision. Controls, back-gating, representative samples, label compatibility, and biological interpretation must be reviewed before administrator promotion.

## Lifecycle API

Administrators call:

```text
POST /api/analysis/template/lifecycle
```

with `template_id`, target `status`, and `change_reason`. Reject missing reasons, missing templates, unauthorized users, and backward or skipped transitions not declared above.
