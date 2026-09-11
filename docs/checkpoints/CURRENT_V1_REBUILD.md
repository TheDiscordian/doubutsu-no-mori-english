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

Six focused orchestration checks pass in 0.162 seconds. The execution-dependent
seventh check subsequently passes in 11.026 seconds against the completed run.
Tests cover all group ordering/predecessors, explicit artwork inputs,
dirty/symlink rejection, complete boundary files and source binding, changed
resume manifests, and refusal to publish an unknown final ROM.

A Make dry run confirms all three commands use the same isolated source path.
The pinned published Linux amd64 compiler image is already installed, and local
free space is sufficient. No tool installation or gameplay test is required.

The correction recipe completes successfully from committed source
`b193042a53c85652195756dfab945c64ba148b42` with explicit artwork input
`build/v1-rebuilt-04` and output `build/v1-current-01`. All ten groups / nineteen
construction stages pass, with 168.869 seconds of stage work and 871 source
hashes recorded, including the Makefile. The pinned published compiler is used.
Each group retains its artifact checks and original-ROM UPS reconstruction.

- Final ROM: `build/v1-current-01/final/Animal Forest English V1-current.z64`.
- ROM SHA-256: `2a04f6e5c54dc2d5ed03009395af815b464bebdef51d67d899554deb54b3bcb4`.
- UPS SHA-256: `c3931b2e029bf4182864306ed2cbf28ea4c1d6c9d609cd33d68047132029b769`.
- `inputs.json` SHA-256: `8ade8c883c8c53265c9fc90723b9d8fb5da7186f137ecdac439f803f00a90837`.
- `rebuild.json` / `final/build.json` SHA-256: `4a0df7d8d6cffa2658303bb633fe45877a418a0e7796df2663af0baa7916cfb6`.
- Recipe SHA-256: `8d37fbd75f99297b18f706e41a3b7dd10e610247d630bb450f166521cfa7d8ff`.

The final ROM and UPS match the independently constructed scene-menu candidate.
No native gameplay or original-hardware execution is claimed for this build run.

## Current work boundary

The user directs that old builds must not be re-tested. The planned complete
108-stage replay is not started and is not queued; the composed command has
dry-run evidence, not a fresh end-to-end execution claim. Earlier base/artwork
results and this successful correction run remain separate recorded evidence.
Do not rerun either solely to renew verification.

The completed output is packaged as [V1RC8](V1RC8_PACKAGE.md), with checked
offline instructions and standalone patch application. Remaining release/content
work takes priority; accepted fixes and saving/reloading stay closed. No existing
candidate, package, or save is modified.
