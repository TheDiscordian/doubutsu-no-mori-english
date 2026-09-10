# English embedded menu warnings and confirmation

The editor's complete supplied GC confirmation wording, all sixteen inventory
warning windows, and all thirteen Controller Pak status/error/choice windows are
installed. The warnings retain native line counts, choice indices, colours,
vertical spacing, control handlers, and saved formats. The N64 wallet warning
says 50,000 Bells; repair explicitly warns of possible data loss. No GC-only
bank or diary functionality is imported. See [the specification](../../specs/EMBEDDED_MENU_TEXT.md).

The confirmation fits existing slots. The warning images append complete English
strings after zero-filled storage preserving the old BSS addresses. All original
CPU instructions and relocation types/sites/order remain. The shared menu pool
reserves an additional 4,096 bytes; conservative combined growth is 960 bytes,
leaving 3,456 bytes above the required 253,696. The ordinary heap still ends at
`80400000`; no save field is enlarged.

## Verification

Three focused checks pass in 8.629 seconds: complete reference wording, all
source line tables and choices, unchanged handlers/BSS, relocation at three
heap addresses, bounded English pointers/lengths, shared parent and allocation,
complete prior-resource retention, and UPS reconstruction. The combined counter
accepts the installed cartridge; the newly inventoried confirmation and warning
records have verified English credit rather than being left outside the total.
The title combination check passes in 8.747 seconds, with every previous resource
and the unchanged English title/Expansion Pak instruction retained.

The bounded native batch is **incomplete**, not passed. Attempt one at
`build/submenu-text-native-01` stops before any menu call: the fixture's requested
98,304-byte second allocation returns null. Its owned buffer is reduced to the
previously successful 65,536-byte size. The single corrected retry at
`build/submenu-text-native-02` boots with four MiB, allocates both buffers, and
uses the native cartridge loader to verify the complete 3,184-byte relocated
confirmation owner/BSS. It then stops at a Python debugger validation error:
the fixture attempts a zero-length asset write for this text-only case.
There are 35 recorded steps, three native calls, and two passing assertions.
No warning draw, Pak operation, save operation, or gameplay failure occurs.

Empty asset writes/reads are removed from the fixture. Do not repeat this setup
batch; continue unrelated implementation. Full native warning loading/drawing,
fixture guard/save readbacks and normal release/restoration, ordinary menu entry,
and hardware acceptance remain unverified. The isolated failed test processes
exit without touching user saves. The identified failures are test construction
errors, not evidence that the game warnings crash or that their native acceptance
has passed.

## Candidates

Untitled ROM: `build/submenu-text-01/animal-forest-halfwidth.z64`.
ROM SHA-256:
`9f12c83314b048225e87c0c4ba46853caf3dadb21f863a234ca03a879987474d`.
UPS SHA-256:
`fb88663db756c3a0d9f45599ee7ab76ca4acd86165fdb0b8c2b3a6e21459eb58`.

Combined ROM: `build/title-submenu-combined-01/animal-forest-title-preview.z64`.
ROM SHA-256:
`be9b51bada53c9fc8a3abd6cc53ae054689100e9bee8a595334d5da183febe35`.
UPS SHA-256:
`8c1d147e5917de04f9f692293054e779b622660f30bdf4b77eb3112cbf81c990`.
The combined 32-MiB cartridge requires an Expansion Pak. It retains both Nook
conversation corrections, Shrine, the English title, corrected grid, birthday,
all earlier English text/artwork, and unchanged saved formats. Previous ROMs and
the user's saves remain untouched. The candidate is available for experimental
playtesting, not a claim of completed v1 or hardware acceptance.

Continue remaining embedded interface/artwork, particularly decorative building
lettering and item bags without matching English GC donors. Public release still
requires provenance and patch-only packaging review.
