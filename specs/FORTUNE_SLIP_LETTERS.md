# Complete fortune-slip letters

## Implementation and remaining integration

All 64 random phrases, four outcome labels, and three complete English
header/body/footer triples have source-bound local resources. The portable
creator publishes a complete saved snapshot without truncating any wording.
The N64 CPU probe passes complete creation and older-catalogue restoration.
The optional native Miko adapter installs complete item hand-off with per-instance
retry choices and synchronous temporary work. Native cartridge loading, real
actor callbacks, whole-pocket publication, and complete reader restoration pass.
Normal interaction and cancellation across actor removal remain unverified.

`tools/fortune_slips.py` binds the native actor and complete supplied English
sources. `tools/build_fortune_slips.py` builds ignored reference resources.
`overlays/mail_generation/fortune_slip.c` implements the complete transaction.
The existing native generation builder has an explicit fortune-slip probe
variant, with its own source/export checks; a generic generation probe cannot
silently stand in for that variant.

`overlays/mail_generation/fortune_actor.c` supplies the native init/give callbacks.
`tools/build_fortune_actor.py` appends them to the source-verified original actor;
`tools/fortune_actor.py` guards allocation limits, all relocation records, source
words, reader dependencies, DMA ownership, and the atomic installation.

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

The original give handler is `809E5EA0..809E5FA0`. It advances five
demo orders and switches to action zero before creating/copying a letter.
Creation does not return failure. A replacement must stage complete mail and
verify a free pocket before announcing a hand-off; it must not lose a paid slip
or reroll its choices on a retry. The charge and luck assignment already occur
in the preceding action. The optional adapter replaces the give-table callback
and delays those same five order writes until complete publication succeeds.

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
The optional adapter raises only Miko's requested size to 2,400 and uses those
24 bytes for pending selections. The native initializer's first 48 bytes have
SHA-256 `aef7ac2b327aedb17d1ee2eb6a32c30b51089835db4d9dedec0eb43f4d97cf33`;
its profile-sized clear covers the extension. No shared actor pool grows.

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
metadata come from the caller and remain intact. The optional native adapter
clears/stages a new letter and sets its recipient using the original helpers.

The native probe has 2,244 code bytes, no mutable/global data, and only the
three checked resident catalogue/pack/restore imports. All internal absolute
jumps are inventoried and relocated. Compiler-reported frames are 64 bytes for
the fortune creator and 216 for general generation, before nested reader work.
The resident module uses 24,288 linked bytes, leaving 288 within its existing
24 KiB limit. Its 32 KiB reservation and native saved layouts do not grow.

## Native adapter and retry state

The extended actor has 7,248 loaded bytes and 288 relocation bytes. Its native
8,192-byte slot has 944 loaded bytes free; relocation scratch is separately owned
by the native loader. Original code/data retain their linked addresses, and
the original sixteen-byte BSS is materialised as zero bytes before new code.
Only three original actor words change: profile size, init-table entry two,
and process-table entry three. Original charge, effect, message selection,
outcome initializer, and other callbacks remain unchanged.

The original actor and relocation DMA rows retain their indices and adjacency,
but move to VROM `03600000` and `03608000`. The native loader discovers relocation
data from the next DMA row, not from numerical VROM adjacency. Ownership metadata
at `80101D10` supplies the extended loaded bounds while preserving the profile
address. Original relocations retain their order; original data-section records
use adjusted offsets inside the materialised prefix. New ELF records identify
every internal jump/data reference and all approved fixed native/resident imports.
The complete native loader output agrees with the independent relocation model.

The pending extension starts at actor offset `0948`:

| Offset within extension | Bytes | Value |
| --- | ---: | --- |
| `00` | 8 | Complete phrase/outcome/template selection |
| `08` | 4 | Empty, armed, selected, or delivered state |
| `0C` | 4 | Captured initial capitalization |
| `10` | 4 | Native current-player pointer |
| `14` | 4 | Zero reserved word |

The initializer resets pending state, records the player, and calls the original
one-draw outcome initializer. The give callback requires action three, ready
demo order, the same player, valid outcome/state, and a free pocket. It allocates
5,471 temporary bytes, including alignment slack for 5,456-byte work. Only then
does an armed state draw the four phrase indices and one template. Selected
states reuse every captured value. Generation and a final player/action/order/
pocket recheck precede the native copy. The delivered state blocks duplicate
publication even if the callback is invoked again with a ready order.

Every allocated attempt frees work before returning or issuing hand-off orders.
No heap pointer or large buffer remains in the actor. Complete snapshots carry
all five sixteen-byte values without relying on or changing the native ten-byte
handbill table. These templates contain no sticky-capitalization-setting command;
the adapter preserves the current shared flag instead of overwriting a newer
value with an old retry's captured flag. The unchanged previous action owns the
fifty-Bell charge and luck assignment; the give adapter never charges again.

Pending state belongs to a live actor, not the save. A forced new initializer
resets that state, and actor removal discards it. The current checks do **not**
prove that cancellation/removal cannot abandon an already paid, undelivered slip.
Before release, trace the native talk cancellation and removal routes and either
prove they cannot occur during a pending delivery or implement explicit recovery.
Do not describe the synchronous retry checks as persistent paid-letter recovery.

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

Eleven adapter/installer host tests pass, including complete real formatter
transactions, all sixteen heap alignments, every selected read failure, changed
owners/orders, full pockets, repeat delivery, two independent actor states,
source mutations, missing dependencies, and installer rollback. A mutation of
the compressed main-code file must operate on extracted code before reinsertion,
not use an uncompressed function offset inside compressed physical storage.

The native adapter batch passes all 24 outcome/template/capitalization
combinations, all ten pocket positions, full-pocket rejection, four disabled
resource attempts, successful retained-choice retry, and duplicate prevention.
Its 88 native calls and 578 memory assertions also prove exact loaded relocations,
complete pocket-to-reader text, unchanged heap accounting after attempts,
retained live save/handbill fields, allocation/stack guards, restored checkpoint,
blank isolated saves, and graceful shutdown. This is not normal player input,
visible letter-window rendering, cancellation/removal, or hardware acceptance.

Required next work:

1. Close the cancellation/removal lifetime gap for already paid pending slips;
   preserve native outcome, price, and effects without duplicate delivery.
2. Validate ordinary paid reading and subsequent input/action progression.
3. Batch the remaining visible reader and existing mail/save paths;
   retain outstanding custom editing, normal play, semantic review, and hardware
   acceptance. The unrelated ordinary NPC creator rejection remains deferred.
4. Continue the remaining general text and main-port work. The title screen is
   still the first image task, followed by the GC-style keyboard stretch goal.
