# Post-v0 artwork reproduction

`tools/rebuild_v1.py` recreates every post-v0 stage from the corrected v0 and
supplied source inputs. It compiles the two reviewed intermediate/final grid
versions, birthday drawer, full animated title, and native artwork commands.
It does not read any old artwork ROM or precompiled overlay folder. Only its
`final/` cartridge is a playtest result; the recipe requires the corrected
keyboard and exact approved cartridge/UPS/title-report identities.

The first complete execution is `build/v1-rebuilt-01`: all 26 stages pass in a
combined 141.572 seconds of stage work. Final ROM SHA-256 is
`128f19b734565e5e0c3af15aaf1fef8fb066155039404a2bfdd29efe8010bf19`;
UPS SHA-256 is `600ec4b132646673ae8f1894b5131b642439b0b82e171c96ba351175cc1ddef0`;
canonical title-report SHA-256 is
`20f970392d1d60136613ee439b3cc90bcc2abf77941fcf34f42f900b7877a815`.
These exactly match the supplied package `03`. Its `rebuild.json` SHA-256 is
`8d98c10668e1114c5f6c4108e99de1cfe00c29a23d9f94398a6b554fe70ae926`.

This execution uses the recipe under development, not a pristine source
revision. The committed recipe additionally records its own hash, includes
untracked non-ignored build sources in its inventory, and explicitly records
whether the source worktree is modified. The source-inventory/reporting additions
have focused host checks; a source-revision-bound rerun remains to be recorded.

Five recipe tests pass in 0.151 seconds: stage order, exclusive output handling,
only the two reviewed keyboard replay source changes, unknown final-result
rejection, source inventory, all completed stage records, and full validation of
both freshly compiled keyboard versions. The existing independent current-grid
compilation/relocation test passes in 3.167 seconds with an unchanged complete
current profile. No native gameplay scenarios are repeated for this build work.

The original corrected v0, all development artifacts, package `03`, and user
saves remain untouched. This is not a clean-clone base-translation recipe:
`build/v0-hardware-fixes-02` and its canonical report are still explicit inputs.
The local pinned Docker image also needs a reproducible public setup recipe.
Public release approval, third-party provenance, and human/hardware acceptance
are not supplied by successful cartridge reproduction.
