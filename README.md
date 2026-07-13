# Nocturne evidence

This branch is the inspection surface for Nocturne releases. The normal `main`
branch stays focused on understanding, installing, running, and contributing to
the product.

Evidence folders may contain verification logs, manifests, retained source
media, provenance screenshots, independent reviews, and historical handoffs.
They do not replace real listening, target-hardware, screen-reader, or overnight
tests.

## Release linkage

Each release folder should record:

- product tag and commit;
- Nocturne and Nocturne Pi archive SHA-256 values;
- evidence archive SHA-256;
- verification scope and unresolved human tests.

`releases/alpha11-v0.3.1/` preserves the last completed single-product evidence
bundle. `working/alpha12-v0.4.0-dev/` is the staging record for the dual-profile
transition and should remain pending until Codex finishes and reruns checks.
