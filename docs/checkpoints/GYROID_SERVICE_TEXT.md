# English gyroid service responses

All twelve native gyroid sales/configuration responses use complete supplied GC
English wording, including price/free/display-only states. The native state
order, sales, item/wallet fields, colours, position, scale, and one-character-per-
update reveal remain. The price reads "It's 65535 Bells" at the largest native
unsigned-16-bit value. The GC wide-space glyph and installed ordinary space
both advance six pixels. See [the specification](../../specs/GYROID_SERVICE_TEXT.md).

The native twelve-character temporary buffer sits immediately before an
interrupt callback. English instead uses a new 32-byte buffer after the complete
original state, with a 22-character clear/reveal limit. The callback remains at
its original offset and is not covered by longer writes. Thirteen guarded
instruction words implement these buffer/limit/prefix changes; all other native
code and relocation sites/order remain. Complete strings and zero-filled state
fit a 4,128-byte image. The extra aligned requirement is 256 bytes, leaving
3,200 bytes in the existing 257,152-byte menu reservation. No saved layout changes.

## Verification

Three focused host checks pass in 7.637 seconds: exact complete source mapping,
all native code changes and unchanged actions, every unsigned-16-bit price,
old state/callback and new-buffer bounds, relocation at three heap addresses,
complete cartridge/UPS retention, shared ownership, and installed-text credit.
The complete counter accepts this cartridge and includes all thirteen source
records in its shared inventory, with verified installed English credit.
The title combination check passes in 8.172 seconds, retaining every previous
resource and identical title/Expansion Pak warning implementation.

The single silent native batch at `build/gyroid-service-native-01/results.json`
passes 179 recorded steps, twenty native calls, and 87 fixture assertions. The
actual cartridge loader installs the complete owner and flattened relocations.
Native composition produces all twelve English responses, plus both zero and
65,535 price cases. Native drawing produces all 22 ordered glyphs, including
padding, for the longest response and maximum-price response. Each draw uses
1,616 display-list bytes and 1,408 bytes at the arena's other end.

The original message slot, interrupt callback, new buffer guard, source strings,
native code, submenu/tag state, and heap/stack/module guards remain intact. The
fixture temporarily sets an isolated live price field, restores that field,
and verifies the complete live save. No sale, persistent save, or Pak operation
is invoked. Both allocations are freed, the matching isolated checkpoint is
restored, and the emulator shuts down gracefully without audio.
This is not ordinary gyroid navigation, transactions, or hardware acceptance.
The preceding embedded-warning drawing batch remains incomplete; this passing
gyroid check does not relabel it as passed.

## Candidates

Untitled ROM: `build/gyroid-service-01/animal-forest-halfwidth.z64`.
ROM SHA-256:
`0173bb83decfda63b299fb40aedd22121b546818081754032e60fc3b96d9a257`.
UPS SHA-256:
`c8cf9d9eff2bbbef27836c1a1f499461de88a2b6c11d73fb1e8fe147f813fd0a`.

Combined ROM: `build/title-gyroid-service-combined-01/animal-forest-title-preview.z64`.
ROM SHA-256:
`da66a789341307c625da130ae11e20609b9a023fca82712f303fc59fe95deb94`.
UPS SHA-256:
`6b423b37fc767c73d3490a2c2e5182509ccdf66c52cba4c663a5ac2d3065edbb`.
The combined 32-MiB cartridge requires an Expansion Pak and retains both Nook
conversation corrections, Shrine, English title, corrected grid, all earlier
text/artwork, and the embedded warnings. Previous ROMs and user saves remain
untouched. Continue remaining decorative art and patch-only packaging; keep
ordinary playthrough/hardware and public-release review explicit.
