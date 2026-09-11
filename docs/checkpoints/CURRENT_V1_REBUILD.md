# Current V1 complete-build integration

## Implemented work

`tools/rebuild_v1_current.py` connects the complete artwork/title output to all
nineteen correction stages through the scene-selector translation. The updated
`make complete` invokes it inside the isolated source checkout after the base
and artwork recipes. No retained RC ROM or compiled correction folder is an input.

[The specification](../../specs/CURRENT_V1_REBUILD.md) binds the ten groups,
input/report selection, source and compiler identities, output hashes, checked
resume boundaries, and final-only publication. The runner explicitly supplies
the freshly built resident-module report to the editor correction.

## Checks and execution

Six focused orchestration checks pass in 0.162 seconds; the execution-dependent
seventh check is skipped until the new recipe runs. The earlier initial preflight
also passes. Tests cover all group ordering/predecessors, explicit artwork inputs,
dirty/symlink rejection, complete boundary files and source binding, changed
resume manifests, and refusal to publish an unknown final ROM.

A Make dry run confirms all three commands use the same isolated source path.
The pinned published Linux amd64 compiler image is already installed, and local
free space is sufficient. No tool installation or gameplay test is required.

The correction-only execution and complete 108-stage clean command remain to be
run from committed sources. Record results and any concrete missing dependency
here; written orchestration and passing preflight checks are not execution proof.
RC7 remains the named hardware handoff; accepted fixes and saving/reloading stay
closed. No existing candidate, package, or save is modified.
