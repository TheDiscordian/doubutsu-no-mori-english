# Post-v0 artwork reproduction

`tools/rebuild_v1.py` recreates every post-v0 stage from the corrected v0 and
supplied source inputs. It compiles the two reviewed intermediate/final grid
versions, birthday drawer, full animated title, and native artwork commands.
It does not read any old artwork ROM or precompiled overlay folder. Only its
`final/` cartridge is a playtest result; the recipe requires the corrected
keyboard and exact approved cartridge/UPS/title-report identities.

The source-revision-bound execution is `build/v1-rebuilt-02`: all 26 stages pass
in a combined 132.852 seconds of stage work. Source revision is
`d54f2f89bd832bc59957441dc9101010fc52a740`, with no modified build sources and
804 source-file hashes retained. The recipe SHA-256 is
`7e18153dc40d73fc6a12d455f49fdbc3094420851631d9f60a91453bbe9cac64`.
Final ROM SHA-256 is
`128f19b734565e5e0c3af15aaf1fef8fb066155039404a2bfdd29efe8010bf19`;
UPS SHA-256 is `600ec4b132646673ae8f1894b5131b642439b0b82e171c96ba351175cc1ddef0`;
canonical title-report SHA-256 is
`20f970392d1d60136613ee439b3cc90bcc2abf77941fcf34f42f900b7877a815`.
These exactly match the supplied package `03`. Its `rebuild.json` SHA-256 is
`f878fd612e4fc42d49d46d542bd8f9eabd22535c977347dce562559f66c2ff1e`;
`inputs.json` SHA-256 is
`0546073391350639c872c17e63eb99410033965895721636d517262154edf627`.

The prototype at `build/v1-rebuilt-01` also completes all 26 stages in 141.572
seconds, with the same final identities. It precedes complete recipe/self-source
recording and is not claimed as a pristine-revision build. Its retained result
SHA-256 is `8d98c10668e1114c5f6c4108e99de1cfe00c29a23d9f94398a6b554fe70ae926`.
The committed run above supplies the explicit clean source-revision evidence.

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
