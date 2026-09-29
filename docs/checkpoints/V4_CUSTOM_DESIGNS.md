# Deferred custom-design work

## Scope and location

Able Sisters, the Museum building, custom designs, and comparable large new
features belong to V4. V3 imports items and villagers with working behaviours;
it does not require these buildings. Design-dependent sign boards and saved
pattern representations remain unavailable, not completed imports.

Unfinished implementation is preserved on `v4/deferred-custom-designs`, based
on V3 commit `8cd9c0e5`. The active V3 branch excludes this experimental code.
The installed V3 proposal remains ABI 368 / save format 19 at
`build/v3-carried-npc-installed-08/build-lock.json`. No new ROM or user save is
produced by this checkpoint.

## Prepared work

- Shared model conversion supports validated native row-major I4 block textures,
  retained tile state, and dynamic projected vertices.
- `build/v3-carried-design-fields-01/` contains four complete sign model roots
  (4,208 bytes), eight donor template records (4,352 bytes), and a compiled
  pattern service (2,624 bytes). None is installed or selectable.
- Pattern services represent four players with eight saved patterns each,
  palette/name editing, painting, flood fill, ordering, and atomic commits.
  Five official template-name source credits are in the provenance catalogue.
- Conditional save-format-20 integration is unfinished and not installed.
  It needs checked RAM reservations, MIPS integration, native consumers, and
  successful save validation. Do not enable it in V3.

## Verification limits and resumption

Four focused preparation/conversion/pattern tests passed before the save test
was added. The current five-test suite is not green: the new save fixture stops
with `Unexpected save halt 1 at phase 0`, before saving. A possible cause is the
fixture repeatedly calling the guarded accessor while incrementally replacing
the order array, temporarily creating duplicate indices. This is an unverified
diagnosis, not a passed test or a demonstrated game defect. Inspect the fixture's
mutation sequence when V4 work resumes; do not spend V3 time debugging it.

Full editor UI, Able Sisters integration, native sign placement/rendering, world
and travel consumers, and complete persistence remain unfinished. Existing
prepared assets and passing evidence can be reused when V4 begins. No native
gameplay or hardware result is claimed.
