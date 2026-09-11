# Current V1 correction rebuild

## Complete command

`make complete V0_OUT=<fresh-build-directory>` runs the isolated base recipe,
the 28-stage artwork/title recipe inside that checkout, and
`tools/rebuild_v1_current.py` inside the same checkout. These three commands
contain 61 base stages, 28 artwork stages, and 19 correction stages through
RC8: 108 in total. A fourth command adds the
[main-program diagnostic text](MAIN_DIAGNOSTIC_TEXT.md), making 109 stages
and placing the latest result in the isolated checkout's `build/v1-final/`.
The nineteen-stage runner's own output remains the bound RC8 baseline below.
The only initial game inputs remain the original N64 ROM, supplied legacy
reference patch, and English GC disc. Source references and the published
compiler retain their existing pinned identities.

The correction runner also supports an explicit artwork build as input for
incremental development. That mode does not claim to regenerate its base or
artwork inputs; the complete command does. It never reads a retained RC ROM or
old compiled correction directory.

## Correction sequence

Reuse existing builders and their native guards, rather than reimplementing
translation logic in the orchestration layer:

1. Seven RC1 stages: title-start pixels, editor layout, HUD, notice/tune,
   inventory money, letter UI, and keyboard background.
2. Three RC2 stages: hiring notice, remaining player/shop/clock text, and
   keyboard frame/key placement.
3. Two RC3 stages: bordered font and building-transition edges.
4. RC4 font-memory/ordinary-space correction.
5. Catalogue and repayment labels.
6. Tune confirmation.
7. Controller Pak heading.
8. Native title controller warning.
9. Separate player/save-gamestate labels.
10. Complete scene-selector/loading/settings text.

The ten groups contain nineteen construction stages. RC3 is only an intermediate
with a known loading defect; never label it a current playtest. Final output
requires all later corrections.

## Inputs and provenance

Read the artwork recipe's `final/animal-forest-title-preview.z64`,
`final/preview.json`, and `replay/27-civic-interiors/build.json`. Verify exact
cartridge/source hashes, the approved title comparison profile, and the
translation report selected by that title. Pass the actual resident-module
report to the editor builder; do not fall back to a development-directory
profile. GC REL and symbol inputs remain explicit and hash checked.

Record the Git revision, all production source hashes plus Makefile, the recipe
hash, actual compiler verification, clean pinned reference revisions, exact
input paths/hashes, and every completed group. Each group records its complete
artifact hashes, input/output ROM identities, patch identity, actual builder,
and elapsed time. Existing grouped builders retain their internal stage reports.

## Boundaries and failures

Outputs belong to a fresh directory inside the executing checkout's `build/`.
Reject dirty production sources, unknown inputs, symlinked outputs, and existing
destinations. Recheck source/reference identities before final publication.

`--through <group>` permits a bounded successful prefix. `--resume` accepts
only unchanged inputs, sources, recipe, compiler selection, and group order.
Before reusing a group, verify all its recorded files, builder hash, predecessor,
exact output, and original-ROM UPS reconstruction. An incomplete directory is
not a resumable success; keep it for diagnosis and do not overwrite it.
Completed final artifacts are never silently replaced.

Only after all ten groups pass, write `final/Animal Forest English V1-current.z64`,
`final/animal-forest-english.ups`, and its build report. Require ROM SHA-256
`2a04f6e5c54dc2d5ed03009395af815b464bebdef51d67d899554deb54b3bcb4`
and UPS SHA-256
`c3931b2e029bf4182864306ed2cbf28ea4c1d6c9d609cd33d68047132029b769`.

## Validation scope

Preserve the passing order/input/rejection/resume checks and executed nineteen-
stage correction recipe. Its final ROM and UPS match the independently built
scene-menu candidate. Earlier clean base/artwork rebuilds retain their own
recorded evidence. The composed 108-stage command is available, but a fresh
end-to-end execution is not claimed or queued. Do not re-test old candidates or
replay unchanged historical recipes. Verification targets relevant changes to
the current deliverable, not repetition of accepted results.

This work changes build orchestration, not the ROM's content, saved formats,
memory requirement, or human acceptance. It runs no emulator or debug-menu
action, uses no user save, emits no audio, and does not publish a release.
Patch packaging, public documentation, and redistribution approval retain
their separate requirements.
