# Complete fortune-slip letters

## Implementation and remaining integration

All 64 random phrases, four outcome labels, and three complete English
header/body/footer triples have source-bound local resources. The portable
creator publishes a complete saved snapshot without truncating any wording.
The N64 CPU probe passes complete creation and older-catalogue restoration.
The native Miko actor is unchanged: normal item hand-off, allocation lifetime,
retry ownership, and delivery are not installed or validated by this work.

`tools/fortune_slips.py` binds the native actor and complete supplied English
sources. `tools/build_fortune_slips.py` builds ignored reference resources.
`overlays/mail_generation/fortune_slip.c` implements the complete transaction.
The existing native generation builder has an explicit fortune-slip probe
variant, with its own source/export checks; a generic generation probe cannot
silently stand in for that variant.

## Native selection and metadata

The native actor is VROM `008C8F10`, linked RAM `809E5740`, file size 2,992.
Its SHA-256 is
`29bb1d033017871b77d40d246c7fe892e4fe61ba4f2fb067a43757a782ac8a1b`.
Relocations are at `008C9AC0`, 240 bytes, SHA-256
`66afae771d50c718d584d4590aad187191f492d33d1eb735adfa7a1d7f7c2ee5`.
The section header is `(2848, 144, 0, 16, 51)`. The native profile/ownership
record at `80101D10` ends at `809E6300`; original temporary BSS starts at
`809E62F0`. Those are linked addresses, not resolved live allocations.

The creator at `809E5BC4` draws four independent random indices in `[0,16)`.
The source pools and captured fields are:

| Field | Meaning | Native first ID | Entries |
| --- | --- | --- | ---: |
| 0 | Luck | `02B1` | 16 |
| 1 | Love | `02A1` | 16 |
| 2 | Wealth | `02DA` | 16 |
| 3 | Health | `02CA` | 16 |
| 4 | Outcome | `02C1` | 4 |

The outcome is already selected by `809E5FA0` and stored at actor offset `0940`.
The native creator adds that index directly to `02C1`. The English GC actor
instead applies `{2,3,1,0}`. Copying that permutation would change the native
slip's meaning; the complete native-order labels are preserved. Native effect
bytes `{0,3,4,5}`, outcome selection, and the fifty-Bell charge stay unchanged.
Reserved general strings `02C5..02C9` are not valid native outcomes.

A fifth creator RNG draw selects classic template `0072`, `0073`, or `0074`.
All three English templates retain their complete wording, four category fields,
outcome field, explicit spaces, and six body newlines. The header's newline
remains its native name-placement marker. Fortune mail type five suppresses
recipient-name insertion in the existing full reader.

The native give handler is `809E5EA0..809E5FA0`. It currently advances five
demo orders and switches to action zero before creating/copying a letter.
Creation does not return failure. A replacement must stage complete mail and
verify a free pocket before announcing a hand-off; it must not lose a paid slip
or reroll its choices on a retry. The charge and luck assignment already occur
in the preceding action. The current transaction does not solve that caller.

## Native allocator evidence for the hand-off adapter

The NPC controller at VROM `008681F0`, linked RAM `809735B0`, has 66,400 file
bytes and SHA-256
`460777a8c6d6b57e9c83a7c9f3efe02593fd01b75f9a4e108db5b9c2a54a18e3`.
Its constructor installs `80980624` as the overlay-allocation callback and
`80980830` as the actor-instance allocator. Miko's native identity is `D03D`.

The `D` branch at `8098068C` checks the event table. A matching event uses an
8,192-byte slot; the non-event fallback for `D03D` also uses 8,192 bytes. The
10,240-byte branch lists other explicit identities, not Miko. The 2,048-byte
normal-villager branch is selected by identity high nibble `E`, not `D`.
Pool constructors use 8,200-byte strides for the 8,192-byte overlay areas.
The allocation helper does not enforce its supplied maximum-size argument;
the patch builder must enforce the complete loaded image/relocation bounds.

The actor-instance allocator rejects sizes above 2,400 (`0960` hexadecimal).
Miko's profile requests 2,376 (`0948`), leaving 24 bytes inside that existing
limit. The main actor initializer clears the profile's requested instance size.
This provides a candidate per-instance location for captured selections and
retry ownership without a retained heap allocation or shared global pending
state. No profile-size change or new state layout is installed yet.

Function-region hashes for the next adapter's guards:

- `80980510..80980764`: `3a5575f93788ef882ff14d43737c3077716697375d77cbec13e8218740657afa`.
- `80980830..80980950`: `258398720c3722020119184908a76c844a870e77b2d4ef25fdffb143e25f5b9b`.
- `80980BA4..80980CDC`: `c93a5c3a4b6df09dd19a5dcf8d67032e41ed2df1560fdb2f2656b0fa4afd4c1d`.

## Complete sources and catalogue preservation

The phrase resource contains four sixteen-row pools followed by four outcomes,
each in a sixteen-byte slot: 1,088 bytes total. Every full English value agrees
with the complete legacy text, with the actual native caller establishing pool
and outcome identity. SHA-256:
`23163c7dacc3e3aef3924267447f02a58824e0a778352e6aa508ae17e0530231`.
Trailing field padding is captured in the saved record and omitted only during
display by the existing GC-compatible formatter. No reference is shortened to
fit the old ten-byte setter.

Frozen catalogue two remains at VROM `03000000` with its original content and
hash. Catalogue three is a separate optional resource at `03050000`, preserving
every available catalogue-two part and adding only `ps:0072..0074`. The original
three rows remain unavailable under identity two. Unknown IDs do not fall back
to another catalogue, and missing catalogue-three data cannot become a partial
successful slip.

The English decoder calls code `2A` a tilde, while the native decoder calls
code `2A` a fullwidth wave. These three signatures explicitly use the existing
native wave decoration, matching the legacy mapping. The native and GC glyph
artwork is not identical; this is not an identical-image replacement claim.
No font pixels, approved spacing, or global character mapping changes. The
ASCII representation of encoded byte `2A` must not be mistaken for an asterisk
when inspecting raw buffers.

Catalogue three has 4,810 available parts and 56 unavailable parts. It retains
all 4,866 indices and the original assembly semantics. Its 319,392-byte resource
has SHA-256
`c75cc7d6c672e1f708a827cddb426895c3b15b7d3fc3c9337b6928174c71f254`;
payload fingerprint is
`a9a2b2cd78c729046b8be42473b75938c2a9bbc0ce8782fb99097d76dc13bd0d`.
The immutable registry assigns both identities independently. The installer
requires an explicit companion manifest and the current multi-catalogue reader,
rejecting changed metadata, untracked files, and occupied resource addresses
before modifying the build's additions.

## Transaction contract

`AfFortuneSlipChoice` is eight bytes: four phrase indices, one outcome index,
one template index, and two zero reserved bytes. It is caller-owned, immutable
during creation, and contains previously selected values. The creator performs
no RNG calls and does not touch native handbill free-string storage.

The caller supplies one prepared 164-byte native mail record, the complete
verified phrase resource, a separate capitalization word, and sixteen-byte-aligned
`AfFortuneSlipWork`. Native work occupies 5,280 bytes; its general generation
workspace starts at offset 560. Work is temporary, not a saved structure.
Inputs require their documented sizes, ranges, and alignments. Mutable outputs
may not overlap another input or one another. Rejection preserves the entire
destination letter, choice, words, and capitalization state; work is scratch.

The creator captures all five full sixteen-byte fields, selects immutable
catalogue three, and validates complete packing and cartridge-backed restoration
before publication. The saved envelope occupies 97 of the existing 122 text
bytes, including its CRC. Publication sets received status zero, split `80`,
fortune type five, and paper 25. Native identities, attachment fields, and other
metadata come from the caller and remain intact. A native adapter still has to
clear/stage a new letter and set its recipient using the original helpers.

The native probe has 2,244 code bytes, no mutable/global data, and only the
three checked resident catalogue/pack/restore imports. All internal absolute
jumps are inventoried and relocated. Compiler-reported frames are 64 bytes for
the fortune creator and 216 for general generation, before nested reader work.
The resident module uses 24,288 linked bytes, leaving 288 within its existing
24 KiB limit. Its 32 KiB reservation and native saved layouts do not grow.

## Executed checks and required next work

Ten focused host tests pass, including 384 complete phrase/outcome/template/
capitalization combinations, maximum-length phrases, reused work, every selected
cartridge-read failure, invalid inputs/aliases, source mutations, immutable
catalogue differences, installer rollback, and native probe validation.

The silent four-MiB native batch passes forty complete creations, eight invalid
choices, disabled-resource rejection, and four classic/composite reads under
the old catalogue. All 525 memory assertions pass. The native RNG, ten-byte
handbill table, complete live save, compiled code, words, and guards remain
unchanged. The allocation is freed, checkpoint restored, emulator shut down
gracefully, and isolated FlashRAM/Pak files remain blank. This tests creation
and decoding in owned memory, not normal delivery, the visible letter window,
arbitrary player editing, save-menu operation, or original hardware.

Required next work:

1. Enforce the verified 8,192-byte overlay and 2,400-byte instance limits when
   appending the native adapter; verify its complete relocation ownership.
2. Install the creator at the native give boundary, with complete recipient and
   paper metadata, transaction-before-hand-off, and durable retry selections.
3. Prove no lost charge/item, rerolled phrase, duplicate delivery, or retained
   heap allocation on failure, repeated action, cancellation, and actor removal.
4. Batch creator-to-pocket-to-reader checks and the existing mail/save paths;
   retain outstanding custom editing, normal play, semantic review, and hardware
   acceptance. The unrelated ordinary NPC creator rejection remains deferred.
5. Continue the remaining general text and main-port work. The title screen is
   still the first image task, followed by the GC-style keyboard stretch goal.
