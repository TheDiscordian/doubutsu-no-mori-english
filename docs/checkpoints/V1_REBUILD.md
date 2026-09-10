# Post-v0 artwork reproduction

`tools/rebuild_v1.py` recreates every post-v0 stage from the corrected v0 and
supplied source inputs. It compiles the two reviewed intermediate/final grid
versions, birthday drawer, full animated title, and native artwork commands.
It does not read any old artwork ROM or precompiled overlay folder. Only its
`final/` cartridge is a playtest result; the recipe requires the corrected
keyboard and exact approved cartridge/UPS/title-report comparison identities.

The [public-compiler checkpoint](PORTABLE_TOOLCHAIN.md) records a complete passing
source-to-v1 run with the published image, identical final ROM/UPS, and actual
new report provenance. The legacy-image executions below remain separate evidence.

## Complete clean-source pipeline

`build/v0-rebuilt-02/source/build/v1-complete` passes all twenty-six stages
using only the [freshly reconstructed base](V0_REBUILD.md), newly extracted GC
resources, and cloned source/reference files. Both recipe runs use clean source
revision `04539bd1daa310ae5c98e4a41f93e001cd3d88f9`, with 805 build-source hashes.
The post-v0 run records `worktree_modified: false` and completes in 135.107
seconds of stage work. Together, the sixty-one base and twenty-six v1 stages
complete in 513.362 seconds of stage work, excluding checkout/setup and the gap
between invocations.

Final ROM, UPS, and canonical title report match the package `03` identities
below. The complete run's `inputs.json` SHA-256 is
`65316ac3ee2b267cbad65bd6877bbe09ca8fbcfffd908317ea514b40543cf99a`;
`rebuild.json` SHA-256 is
`a7b22faba2a8ab525c1a65187e6d476ad1efb02a0bbff37b913adcc7f32ffaa9`.
The post-v0 result records that component's corrected-v0 input boundary; the
separate base ledger supplies proof that the input was regenerated from source.

An earlier attempt at `build/v0-rebuilt-02/v1` passes twenty-four stages, then
rejects the outside-checkout generated stall-source path. It retains its
`failure.json` and partial outputs; no final cartridge is published by that
attempt. The corrected complete command places v1 output under the cloned
checkout's `build/`. An early output-location check rejects unsupported paths
before compilation, with a focused regression. The six current recipe tests
pass in 0.231 seconds, including retained artifact validation; no native gameplay
probe is repeated for these orchestration changes.

## Retained post-v0-only executions

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
saves remain untouched. These retained post-v0-only runs take corrected v0 and
its canonical report as explicit inputs; the complete pipeline above regenerates
that dependency. The public-image execution above removes the local development
Docker image as a build prerequisite.
Public release approval, third-party provenance, and human/hardware acceptance
are not supplied by successful cartridge reproduction.
