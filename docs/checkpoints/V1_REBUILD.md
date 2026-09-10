# Post-v0 artwork reproduction

`tools/rebuild_v1.py` recreates every post-v0 stage from the corrected v0 and
supplied source inputs. It compiles the two reviewed intermediate/final grid
versions, birthday drawer, full animated title, and native artwork commands.
It does not read any old artwork ROM or precompiled overlay folder. Only its
`final/` cartridge is a playtest result; the recipe requires the corrected
keyboard and exact approved cartridge/UPS/title-report comparison identities.

The [public-compiler checkpoint](PORTABLE_TOOLCHAIN.md) records a complete passing
source-to-v1 run with the published image, identical final ROM/UPS, and actual
new report provenance for package `03`. The legacy-image executions below remain
separate evidence.

## Current package 04: twenty-seven stages

`build/v1-rebuilt-03` passes all 27 stages using the published compiler, with
source revision `998d6738fee40ac3bbc6f04bf30b4411e8ffac85`, no modified build
sources, and 808 source-file hashes. Stage work takes 140.781 seconds. The new
shop-interior step is stage 26; the unchanged title follows at stage 27.
Every resource and overlay is recreated from corrected v0 and the source inputs,
without old artwork ROMs or compiled overlay directories. The unchanged 61-stage
base is not rebuilt again for this data-only change; its complete clean-source
evidence remains separate.

The final ROM/UPS match package `04` exactly:

- ROM: `d7fbbffc85eb7c311f980c3945cf035de136b130d9fee6214ad096d60b8c8585`.
- UPS: `4dca9b30625ea76350dcc3198835ad9d7b6d226cda77bc0828519fa630e5a31b`.
- Actual canonical title report: `6a4a0c374bb065d8de6b94dd0c197cf3f8eaa39fa70941624b42b3e8448e8ee9`.
- Reviewed comparison profile: `79b6ee72a933a52a72b918f9c6099ece453b04babe0a2e6d7e9ba81d6017b029`.

Recipe SHA-256 is `7608ae76328cde78f3f2558839841cdd9576cc8021de37478292f88ab30c65e7`.
The output's `inputs.json` SHA-256 is
`b25ed82e9f1c9379b608a22da9bd8aadeda61c228c59ec126a7b9d8a676e7570`;
`rebuild.json` SHA-256 is
`800ce7e7cbdc7231b73753394a52e473e1dc725bca0089d82b60982d22d6005f`.
The stored, non-canonical `final/preview.json` SHA-256 is
`59a34f5e12d932bc391b8d8b24f515f4289225bce5f3866674d562be20d3ae9e`.

All seven recipe tests pass in 0.336 seconds, including the historical package-03
record and the fresh complete package-04 execution. The installed shop-interior
counter verifies all seven signs in the rebuilt final title ROM; its four
transcribed records retain 53 applied source characters. The public-image report
also passes the private packager's exact approval and patch reconstruction.
No new archive is generated from that in-memory compatibility check. The supplied
archive remains the separately tested package-04 artifact.

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
