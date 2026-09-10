# Reproducible artwork build from corrected v0

`tools/rebuild_v1.py` recreates the combined artwork playtest from the verified
corrected v0 ROM/report, the original Japanese ROM, and the supplied English GC
REL and pinned symbols. It does not read any retained intermediate artwork ROM
or compiled grid/title/birthday directory. Native drawing commands and all three
new overlays are compiled in the pinned published Docker image by default.

This is the post-v0 portion of the complete source build. The
[base recipe](V0_REBUILD.md) regenerates its corrected v0 input and source-bound
report from an empty build directory. Do not imply that shipping a patch ZIP publishes
its source inputs or resolves third-party redistribution terms.

Verify every input before creating an output directory. Extract the complete
preceding editor from the verified corrected v0 itself and validate its source
report. Compile both reviewed keyboard revisions from their recorded source
definitions: version one exists only to replay exact intermediate hashes, and
version two must replace it before the final result can pass. The two historical
source differences are reconstructed in the ignored compiler directory; the
current checked-in keyboard remains corrected. No existing file is overwritten.
The output belongs inside the executing checkout's `build/`, because generated
stall commands compile through the read-only source mount. Reject an existing,
redirected, or outside-build output before reading inputs or starting compilation.

Replay the existing guarded builders in order: shops, map, inventory, clock,
collections, grid, Nookington, SOLD OUT/hints, police, Redd, corrected cursor,
noticeboard, tune, catalogue, service controls, birthday, Controller Pak,
embedded menu warnings, gyroid responses, Nookington details, dump, fishing,
fortune table, countdown, shared stall, shop-interior signs, civic-interior
posters/mailbag, and title. Each builder retains its
source, preceding-cartridge, allocation, other-resource, and UPS assertions.

Record each stage's hashes and duration outside the cartridge's existing build
report. Keep intermediate ROMs explicitly labelled replay-only. Publish the
final result only after its ROM, UPS, approved title-report profile, eight-MiB memory
contract, and installed corrected-grid identity match the supplied package.
The [compiler compatibility contract](PORTABLE_TOOLCHAIN.md) allows only the two
verified compiler-image identities. Preserve actual image provenance and record
the actual report hash separately from its comparison profile.
This recipe does not run emulator scenarios or manufacture gameplay acceptance.

Store the source revision, input identities, source inventory, and completed
stage records in the fresh output directory. Reject concurrent source changes
and preserve partial failure evidence without replacing the playtest artifact.
