# V1RC1 full regression result

The existing `python3 -m unittest discover -s tests -v` process completes with
exit status one: 2,103 tests in 3,539.399 seconds, 25 failures, and 75 errors.
The complete local log is `build/v1rc1-regression.log`. The process is terminal;
do not restart the entire suite. It starts before the RC1 follow-up tests exist;
those four tests run separately and pass.

The final exception messages group as follows. These are observed rejection
reasons, not permission to weaken the guards or a claim of whole-game safety.

| Count | Reported error reason |
| --- | --- |
| 27 | Historical runtime module's source inventory differs |
| 25 | Stale/changed NPC capture overlay |
| 14 | Native item-name translation/provenance no longer matches the expected fixture |
| 3 | Stale/altered native generation probe |
| 1 each | Event module, Miko hand-off module, complete Miko actor, leaflet-date module, native-name manifest, and renewal module guards |

Of the 25 assertion failures, 21 hard-code the older combined source-character
total (751,307 rather than the current inventory's 752,115). One compares an
older native-name credit set. Two expect a later rejection message but an earlier
dependency guard rejects the fixture first. The remaining title test compares
a freshly compiled public-toolchain report directly against a retained report
identifying the local legacy compiler. Its assertion precedes the binary checks;
that test does not establish a generated-code mismatch or a match.

Percentage-tool maintenance stays deferred. Do not fix those accounting totals
as a work batch while the reported keyboard defects remain. Fixture generation
or selection needs repair without replacing retained artifacts or bypassing
source/provenance validation. The two academy setup errors are already confirmed
as old `build/runtime-module` inventory failures. Inspect the relevant fixture
and guard before treating another failure as fully classified. Rerun only the
affected checks after a concrete correction.

The suite is not passed. Its broad historical fixtures do not constitute a
V1RC1 original-hardware playthrough, and its guard failures are not evidence
that the reported corner, glyph-placement, or other hardware bugs are fixed.
Current implementation priority remains V1-14; the user accepts keyboard audio
feedback and supplies direct observations of its remaining visual defects.
