# Published compiler inspection

The published libdragon OCI index is reachable at
`ghcr.io/dragonminded/libdragon@sha256:b68e8dfd393f76ba69c1ba62da6b42dcda8b5b52eaa8fb96adc5aab7865a2d40`.
Its Linux amd64 manifest is
`sha256:efa724f6fa703eadb04aa72e3af230d6b11e0a8cb7487faaa012f6714050b4d3`;
the index also references an attestation manifest at
`sha256:2d21c6dc17d38842e1b5c8026ebd42afaa2fe0a9ff3f3f385fbe30dbcd771cc4`.
The installed published image uses `/n64_toolchain/bin/`, identifies GCC 14.2.0,
and has exactly the same nine executable hashes documented in
[the compiler identity record](../TOOLCHAIN.md).

Its filesystem layers are:

- `sha256:351d919b2c06105efcb263b77e23bff2f166d23bcb487f5185d884bfada142f3`
- `sha256:d214b031b7133e262fbd7000b3cf8f028611570a86ba2f0b2259e8f6c0760da5`
- `sha256:ada4c3c28db9af4ab59554753f8d2331babf97565bcbb0aa5d3aca0c92fbf171`

The local development image has those same three layers plus
`sha256:603ed62100fcc5d2d64e5dfd4e1ef130920649e6f181b8ee7da6fbca41a01fb0`.
No existing image is modified or published by this inspection. The nine-file
comparison is not a claim that every file or host library in both images matches.

The [portable integration specification](../../specs/PORTABLE_TOOLCHAIN.md)
defines actual-image provenance, narrow compatibility with historical metadata
fingerprints, and the required complete clean build. The implementation selects
the public image by default, supports only explicit public/legacy choices, checks
the executable inventory before complete builds, and preserves actual image
provenance separately from historical comparison profiles.

`build/toolchain-public-01.json` records successful execution of the public-image
verifier, SHA-256
`d08cf23283fc57d5a77e6be34ce28e672f043fd8168ec0b82c531989c6d8b549`.
Eight focused compiler/profile tests, seven base-recipe tests, and six v1-recipe
tests pass. The profile tests cover five retained accent/classic profiles and
the complete text-extension profile. They reject changed native code, sources,
symbols, or unknown images, and verify that comparison never rewrites provenance.
Two package tests, three keyboard-overlay tests, four birthday-screen tests,
and sixteen counter tests also pass. Keyboard and birthday tests independently
compile with the public image and retain exact native code and relocation checks.

The first current-cartridge counter check identified an older `compiler_image`
field in the text-extension report. The initial compatibility helper recognised
only `toolchain_image`; the title uses a third existing name, `toolchain`.
Commit `d207133fd930c5216aa2cc46c713cb61970b709b` covers exactly those three
names and retains strict native/source validation. The corrected full counter
passes on the unchanged legacy-built shared-stall candidate, with the same ledger
totals. Its separate evidence is `build/toolchain-legacy-counter-01/latest.json`,
SHA-256 `e8cce8c425c9ef2daa80444218c9946407a43a89d54bfc6ff2b1c155b9b36a9a`.

## First public build and compatibility correction

`build/public-toolchain-rebuilt-01` uses clean source
`11552582c403bdf9312bfb0aa7b5545d98ddc0b1`. All sixty-one base stages complete,
but the final approval gate rejects the unhandled `compiler_image` field. The
run is preserved as failed; no passing result manifest or v1 stages are claimed.
Independent inspection with the corrected validator finds the exact approved v0
ROM and UPS, and only fifty compiler-image metadata changes. The actual canonical
report SHA-256 is
`c1c416e0c9dbd9ffee13f4b82aa205f743bafae36311709ed7f6498d6965e375`;
its corrected comparison profile is the original approved
`5fe4d9b4731470dd9f095f88165133fc629622d6478d9e0b6dd86e65742606a0`.
This is a build-validation compatibility defect, not changed cartridge code.

## Passing complete public-image rebuild

`make complete V0_OUT=build/public-toolchain-rebuilt-02` passes all sixty-one
base and twenty-six v1 stages from clean commit
`d207133fd930c5216aa2cc46c713cb61970b709b`. All 807 build-source hashes remain
unchanged, and the v1 manifest records `worktree_modified: false`. Both recipes
verify the pinned published compiler and its exact executable inventory. No
retained generated translation resource, compiled overlay, or translated ROM
is required. Stage work totals 384.346 seconds for the base and 134.445 seconds
for v1, 518.791 seconds combined, excluding checkout/setup and verification.

The corrected v0 ROM/UPS match their approved identities above; its actual
canonical report is `c1c416e0c9dbd9ffee13f4b82aa205f743bafae36311709ed7f6498d6965e375`.
The final v1 ROM is
`128f19b734565e5e0c3af15aaf1fef8fb066155039404a2bfdd29efe8010bf19`,
and its UPS is
`600ec4b132646673ae8f1894b5131b642439b0b82e171c96ba351175cc1ddef0`.
Both exactly match the supplied candidate. The actual canonical title-report
SHA-256 is `37d01481de8d497a2f129c0908e07d599ca90d6fb69684f83df1ee3ce41fb251`;
its separate historical comparison profile remains
`20f970392d1d60136613ee439b3cc90bcc2abf77941fcf34f42f900b7877a815`.
Actual reports retain public-image provenance; they are not relabelled as the
legacy image or claimed to have the legacy report's actual checksum.

Evidence paths below are relative to the run directory:

| Evidence | SHA-256 |
| --- | --- |
| `inputs.json` | `d8167261d4e602bceff0fa8c265144f04c94b1240d0afe48aefa1acc1ee1177c` |
| `result-61.json` | `503cc60f8066049b8a3800f15be8e7eb8330853bf110fa29ae9578daca2e3873` |
| `source/build/v1-complete/inputs.json` | `b21405dafeee8a2c07e3ae9c71990266355df320f6fabc4355eb1dc189402977` |
| `source/build/v1-complete/rebuild.json` | `99403a6d7a45a557a25dd436d0e967df74d7a57f8548a451fd774a54b79250b6` |
| `source/build/v1-complete/final/preview.json` (stored JSON) | `fd46bc9e1de2d2441b42b4d1732a471f66588a304c5bb95927e907d9dd803c3a` |

Recipe file hashes are
`07aedb8e58dbce3f280886537e42a6b88e6c6f66d4386ea166e23af5bd291365`
for `tools/rebuild_v0.py` and
`afce74dac25bdf23cfc10e21229391373b644e72bde7685b5209c54826d73ca0`
for `tools/rebuild_v1.py`.

## Counter portability correction

The first counter run inside the clean reconstructed checkout stops at the
birthday verifier's hard-coded `build/birthday-draw-03` dependency. The full
cartridge recipe succeeds without that folder: its fresh renderer belongs to
`build/v1-complete/compiled/birthday`. This is a counter dependency, not missing
English code or a failing ROM build.

Commit `fb496aeadb0fe5fce321c260ac315909c50ef519` makes measurement read the
actual installed 800-byte renderer, require its exact approved hash, and verify
the complete native owner, relocation, English assets, and source-bound report.
Compilation retains its ELF-call and compiler-profile checks. All four focused
birthday tests pass in 10.045 seconds, including a new regression that forbids
reading the development compilation folder and rejects modified code, function
padding, unrelated owner bytes, relocation, text, or source metadata. The
independently rebuilt native renderer remains unchanged.

The complete 87-stage build retains its original clean `d207133` provenance.
The newer counter-only verifier does not justify another full cartridge build
or any repeated native gameplay scenario.

The corrected public-cartridge counter check passes in 120.508 seconds on
`source/build/v1-complete/replay/25-stall/replay-only.z64`. It verifies all 51
compiler-image fields as the published image and preserves the same combined
ledger totals: 752,021 replaced source characters out of 752,043 inventoried.
The actual canonical shared-stall report is
`0eea582e23f61caf89e1ad73079b3728c2426bb095a3d4b29a2d59adc7214cd6`.
The run imports only the updated birthday verifier from `fb496ae`, with its
source root set to the unchanged clean checkout; all other validators and
resources come from that checkout. The updated verifier's file SHA-256 is
`9cc86ef6b1b431b7aacf10907d59a954c92f20bcc2322ce7eed221a3607c26d1`.
The development compilation folder remains absent. No clone source or generated
artifact is modified to make the counter pass. These counts retain the existing
inventory limits; the title is separately verified by its complete final identity.

The public final-ROM/package gate also passes using the clean checkout's
`package_v1_playtest.prepare` and exact UPS reconstruction. The package manifest
records actual canonical report `37d01481…41fb251` separately from historical
comparison profile `20f97039…7a815`. No new ZIP is written or supplied for an
unchanged cartridge. The existing candidate ROM remains `128f19b7…010bf19`, and
the supplied package `03` remains
`724ddcaec142a1dddf5708a240c3ecd04ba0a58a059121877c4b8ac71566bebe`.

The passing legacy-image full source rebuild is separately recorded in
[the base](V0_REBUILD.md) and [v1](V1_REBUILD.md) checkpoints. No existing ROM,
patch, package, or save changed. This completes portable compiler setup and
cartridge reproduction, not human/hardware acceptance, public release approval,
or third-party redistribution review. No emulator or speaker output is used.
