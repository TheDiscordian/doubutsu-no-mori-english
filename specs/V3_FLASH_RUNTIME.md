# V3 native FlashRAM integration

## Implemented scope

The [surface-enabled variant](V3_SURFACE_SAVE.md) uses format 4 and separate
surface selection/ownership. Its 1,232-byte runtime has guards at `8046C4C0`.
Stable entry jumps preserve the existing native I/O and caller APIs; the active
runtime resides in the checked surface packet. Valid older formats migrate, but
older builds reject new saves. Use this variant's actual sizes and code records.

The [reward variant](V3_REWARD_SAVE.md) uses format 3, the same 192-byte immutable
profile, and 912-byte runtime state with guards at `8046C380`. It retains all
public runtime entries and native I/O. Valid older banks migrate on decode;
format-1/2 builds cannot read format-3 saves. The added reward state is separate
from catalogue ownership, and player deletion clears only that player's records.

The [clothing-only variant](V3_CLOTHING_SAVE.md) uses format 2, a 192-byte immutable
profile, and 864-byte runtime state. Its separate checked codec keeps the public
save-entry addresses stable. The format-1 sizes below describe the non-clothing
variant; do not use those working-buffer sizes with the clothing variant.

`--save-runtime` connects the [checked save codec](V3_SAVE_PROFILE.md) to native
town loading, normal two-bank saving, synchronous save-menu writing, bank repair,
and the town FlashRAM portions of travel-related saving. Imported catalogue
state has a separate owned RAM allocation. Missing imports or an unsupported
extension format produce an English instruction screen and stop the caller
before it can continue loading or repairing the save.

This variant installs persistence, not item acquisition or catalogue-menu integration.
The [collection variant](V3_COLLECTION.md) additionally connects native item
collection and live-player clearing; its catalogue-menu integration remains work.
Controller Pak transport of imported identities/profile/catalogue data remains
work. Do not describe the complete travel feature or an ordinary imported-item
lifecycle as tested merely because its town FlashRAM calls are connected.

V3 saves use `NAF3` and require this format and compatible imports. V2 and older
experimental V3 builds cannot safely load them. Keep backups and use disposable
saves for development. Both web patchers remain on V2.

## Memory and startup

| RAM range | Use |
| --- | --- |
| `80460020..804600BF` | Immutable 160-byte current import profile, covered by startup CRC |
| `80469200..8046994A` | 1,867-byte save runtime in the unused room/field gap |
| `8046BA60..8046BA7F` | Two 16-byte original-reader/header-clear bridges |
| `8046C000..8046C2BF` | Explicitly initialised, 704-byte runtime state |

The resident prefix remains 48 KiB, ABI 14. The code installer verifies the
preceding room code ends before `9200`, the save codec ends before `BA60`, and
all newly used bytes are empty. Startup verifies/loads the complete prefix,
initialises the object loader, then calls `af_v3_save_reset` before marking V3
installed. The current profile contains the installed pilot actor identities
and furniture identities, independent of record order. A furniture runtime
index is `1024 + ((item & FFF) >> 2)`; it is not `(item - 1000) >> 2` for `3xxx`
items.

State contains magic `AF535633`, an error code, ready/town fields, the 672-byte
working profile/catalogue, and four `AF53C0DE` guard words at `8046C2B0`. Each
operation checks the magic, guard, error latch, and profile before proceeding.
Native live save RAM still receives only `F980` bytes. The unnamed RAM tail is
not used for V3 metadata. ROM-only models at VROM `03F0C000`/`03F0E000` remain
separate from RAM state at `8046C000`.

## Installed routes

| Native location | Installed behaviour |
| --- | --- |
| `8008EEE8` | Signature check accepts `NAFJ` or `NAF3`, including mutable live data |
| `8008EF94` | Preserve header clearing; reset V3 state only when clearing the live town |
| `8008F8A0` | Read a complete bank, validate it, and normalise legacy padding |
| `8008F8D4` | Original reader bridge processes 512 pages instead of 499 |
| `8008F938` | Route direct loads through the guarded allocated loader |
| `8008F9EC` | Validate/decode state before the original live-payload copy |
| `8008F7C8` | Prepare a complete private bank before erase/write; preserve single-bank semantics |
| `8008FBA0`, `80095874`, `80096260` | Prepare the final header and checked extension before native writing |
| `8008F4B8` | Compare complete normalised banks, not just the original payload |

The temporary allocation/request sites at `8008F98C`, `8008FAFC`, `80095498`,
and `80096030` request `10000` bytes. The native payload copies at `8008F9F0`,
`8008FB84`, `80095820`, and `800961F8` retain `F980`; they must not overread live
save RAM. The normal and travel-related asynchronous writers already write 512
pages per bank. Their device worker, chunking, retries, and completion queues
remain native.

The installer binds the complete native flash module and worker hashes in
`FLASH_MAIL.md`, both affected travel-code ranges, and every modified instruction
window. It verifies all twelve direct bank-reader calls in the retail image and
rejects address-taken references. Bank-selection/repair destinations are already
complete-bank buffers; the direct live-RAM destination is removed, and the other
private/framebuffer capacities are explicitly raised.

## Read, commit, and repair

`af_v3_save_read` accepts bank base page 0 or 512. It calls the original reader
through a bridge, then validates checksum, town, extension, and current imports
using the codec. It does not commit loaded metadata while probing/repairing
banks. Valid legacy padding is zeroed in the temporary buffer, so two valid V2
banks with arbitrary tail contents compare correctly.

Some native callers ignore the read return before checking the header/checksum.
For an I/O or damaged-data failure, the wrapper also forces the temporary
payload's additive checksum to exactly 1. It preserves any recognised header,
allowing the native damaged-save flag to distinguish damage from an empty slot.
It does not alter the stored chip during validation. Native backup repair can
still operate on a valid accepted bank.

A missing required import or format error instead stops immediately with the
warning. This deliberately prevents silently choosing an older compatible bank
and overwriting an incompatible one. Format rejection is conservative: malformed
format/reserved fields also stop rather than entering automatic repair.

The allocated loader keeps its native retry/free path. Immediately before its
copy, `af_v3_save_commit` checks the exact destination/length, decodes the state,
copies the original payload, and records the town/ready fields. Any failure
stops before the copy. The live header predicate remains a header/town check,
not a CRC over data that gameplay is actively modifying.

## Save preparation

`af_v3_save_prepare` checks runtime state, rejects a live-RAM destination, calls
the original header writer, then packs the final payload and catalogue/profile.
An error stops before native callers can proceed to device writes. The original
checksum producer can safely recompute the already balanced additive checksum;
the generic checksum implementation is unchanged.

A new town identity clears the previous town's catalogue. Explicit native live
header clearing also resets the V3 state, while clearing temporary buffers does
not. First-save preparation retains ownership already collected since startup.

The synchronous writer allocates a private 64-KiB bank, copies `F980` live bytes,
prepares/validates it, and only then invokes the original erase/page-write APIs.
It writes all 512 pages of bank zero, retains the original one-bank convention,
and returns the native success/failure domain. Allocation/erase failures and
exhausted page retries return failure. A successful write updates the live header
and frees the temporary buffer. No work buffer occupies the original live tail.

The asynchronous saver retains its native full-bank framebuffer ownership.
`800D97A0` accepts a request smaller than `25800` bytes, and 64 KiB fits. Native
framebuffer zero at `80000400..80025BFF` is valid even though it is below the heap.
Verification matches the prepared pointer against the actual framebuffer table,
the retired pointer at `80146084`, and owner state 4. It does not assume every
framebuffer lies after the resident translation module.

## Incompatibility warning

The warning uses existing CPU framebuffer/font routines `800292F4`, `80027CF8`,
and `8002A448`, then `osStopThread(NULL)` at `8002DE10`. It does not intentionally
raise a CPU exception or offer an erase/new-town action. Missing selections tell
the player to power off, rebuild with the required imports, and keep the save.
The error latch prevents further save operations if execution is incorrectly
resumed. A normal restart with a compatible cartridge can load the original save.

The native cold-boot check supplies an incompatible first bank and a compatible
second bank. It verifies all 108 glyphs/6,912 pixels, the stopped graph thread,
absence of a faulted thread, and the unchanged complete flushed FlashRAM file.
The save is not silently rolled back to the second bank.

## Evidence and remaining work

The [checkpoint](../docs/checkpoints/V3_FLASH_RUNTIME.md) owns exact hashes and
commands. Six focused tests cover sanitized control flow, failure-before-I/O,
profile encoding, seed integrity, installed hooks/capacities, retained models,
composition, and import-free V2 retention.

Actual synchronous writing passes. The complete normal writer passes 141 steps
with 31 dispatches and 30 real frame advances. A separate process seeded only
with the exported FlashRAM passes 54 steps and both native load entries, including
complete payload, catalogue/profile, native header, and unchanged live-tail checks.
The warning passes on a normal cold boot, with no fixture register or RAM edits.

These are isolated storage fixtures, not an ordinary acquired-item/save-menu
playthrough. The collection variant adds native marking/query/clearing checks;
remaining work includes catalogue menu/list/preview/order consumers,
ordinary import acquisition/placement/gameplay, actual V2-save migration testing,
additional repair/device-error scenarios where warranted, Controller Pak profile
transport, and original-hardware testing. No completed import or public handoff
is claimed by this batch.
