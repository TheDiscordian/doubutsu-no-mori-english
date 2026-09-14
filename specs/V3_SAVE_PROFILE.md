# V3 save profiles and imported-item catalogues

## Implemented boundary

`overlays/v3/save_codec.c` implements a bounded bank encoder, validator/decoder,
and four-player imported-furniture catalogue. `--save-codec` installs this code
in the combined development cartridge, but **does not change native saving,
loading, or catalogue calls**. All codec execution uses private test buffers.
The actual FlashRAM hooks, player-facing incompatibility warning, fresh-process
round trip, and ordinary gameplay persistence remain required.

The existing [FlashRAM layout](FLASH_MAIL.md) supplies two 64-KiB banks on the
128-KiB chip. The original logical payload is `F980` bytes. The codec uses the
remaining `680` bytes of each complete bank for a checked extension; it never
puts additional bits beyond an original catalogue array.

## Native audit and integration constraints

Addresses and offsets below are hexadecimal. Bind changes to the complete
native module and worker hashes in `FLASH_MAIL.md`, not isolated constants.

- Live save data starts at `80126EA0`. The upstream `Save` declaration occupies
  `10000` bytes, followed by `CommonData` runtime fields. Its final named field
  is at `F8B1`; the remaining array is unnamed. That declaration alone does not
  establish that writing an extension into the live RAM tail is safe.
- The normal asynchronous pipeline already writes all 512 pages of each bank,
  in four 128-page chunks. It copies and checks only `F980` bytes. Existing
  on-chip tail contents can therefore be stale framebuffer data, not zeros.
- Writer state 0 at `8008FAE0` requests a framebuffer through `800D97A0` with
  size `F980`; state 1 at `8008FB64` copies the live payload, writes its header,
  and computes the native checksum before starting the full-bank write.
- The bank reader at `8008F8A0` reads 499 pages, not 512. Its callers include
  bank selection/repair at `8008F24C`, direct load at `8008F938`, allocated load
  at `8008F968`, and asynchronous write verification. The allocated loader
  allocates/copies only `F980` bytes. Bank-selection buffers are cleared for
  `10000` bytes. Every changed reader needs a proven destination capacity.
- Bank selection does not consistently branch on the reader's return before
  checking signature/checksum. A failed extension read or incompatible profile
  must also prevent the existing acceptance path, without silently presenting
  a valid V3 town as an empty slot or encouraging an overwrite.
- The synchronous erase/write path at `8008F7C8` writes only 499 pages. It needs
  explicit handling; changing only the normal asynchronous saver is incomplete.
- `8008EE7C` is the generic native checksum. The checksum producer at
  `8008EEB4` also calls it. Do not add extension validation indiscriminately to
  that shared function: preparing a new checksum is not validating a stored save.
- `8008EEE8` is the `NAFJ` signature predicate; `8008EF0C` adds town checks.
  The live-data predicate at `8008EF6C` uses this header path while gameplay is
  modifying the payload. A full saved-payload CRC is not valid on mutable live
  data. Stored-bank acceptance and live header checks need distinct handling.
- The header writer at `8008EFDC` updates the marker, town identity, and dates.
  The extension must bind the final prepared payload, not a pre-header copy.
- Comparing both banks at `8008F4B8` covers only `F980` bytes. A complete V3
  comparison must include the extension; legacy padding must be normalised or
  excluded, because valid V2 banks can have different uninterpreted tails.
- Controller Pak paths also contain `F980` lengths at `80095498`, `80095820`,
  `80095880`, `80095A70`, `80096030`, `800961F8`, `8009626C`, and `80096484`.
  These are review sites, not approved replacements. Travel must not drop V3
  identities/profile dependencies without safe handling and a clear warning.

The main-code call audit also identifies `8008F530` as the bank-repair rereader:
it rereads a selected source bank at `8008F56C` before repairing the other bank.
The shared asynchronous bank writer at `8008F1BC` also reaches 512 pages; the
travel-related preparation paths use that writer. Their allocations at
`80095498` and `80096030` are framebuffer requests through `800D97A0`, not heap
allocations. Their payload copies at `8009581C`/`800961F4`, header preparation at
`80095874`/`80096260`, and verification reads at `80095A54`/`80096468` must stay
coherent with the normal save path.

The two load entries both return the native success boolean. The direct entry
`8008F938` reads the selected bank into live RAM without a temporary allocation.
The allocated entry `8008F968` already retries failed reads, validates the header,
copies only `F980` bytes into live RAM, and frees its buffer. A candidate
integration can route direct loads through the allocated path, grow only that
private allocation to `10000`, and decode V3 state before committing the original
payload copy. This avoids assuming ownership of the unnamed live-RAM tail;
caller/overlay verification remains required before installing that change.

Do not merely replace the header-writer call with packing and ignore its result.
Native preparation callers continue into writing without testing that call's
return. Packing/profile failures must stop the write before device I/O. The
synchronous path must likewise validate its complete private prepared bank
before its existing whole-chip erase operation. An incompatible otherwise-valid
bank must not be silently replaced using an older compatible bank during repair.
Preserve a distinct profile error and gate load/repair/save until the explicit
incompatibility path is handled.

V3 already owns RAM `80460000..8046FFFF`; the current loaded prefix ends at
`8046BFFF`. A future explicitly initialised state at `8046C000` can avoid
repurposing unnamed native save RAM. ROM-only model data beginning at VROM
`03F0C000` is not resident at RAM `8046C000`. No persistent state is assigned or
initialised there by the codec-only build.

## Version 1 bank format

The original header marker at offset `04` becomes `NAF3`. The town checks and
native 16-bit additive checksum remain intact over `F980` bytes. The original
signature predicate rejects `NAF3`; this is intentional backward-incompatibility
protection, not evidence of a complete user-facing error path.

The extension at bank offset `F980` has this big-endian layout:

| Offset | Size | Meaning |
| --- | --- | --- |
| `000` | 4 | `AFS3` |
| `004` | 2 | Format version 1 |
| `006` | 2 | Extension length `0680` |
| `008` | 4 | Identity registry version 1 |
| `00C` | 4 | CRC-32 of the original payload, treating checksum bytes `12..13` as zero |
| `010` | 4 | CRC-32 of the entire extension, treating this CRC field as zero |
| `014` | 4 | Reserved, zero |
| `018` | 32 | Required villager selection bits |
| `038` | 128 | Required furniture selection bits |
| `0B8` | 8 | Reserved, zero |
| `0C0` | 512 | Four players' 128-byte imported-furniture catalogue bitsets |
| `2C0` | 960 | Reserved, zero |

Both CRCs are CRC-32/ISO-HDLC, matching `zlib.crc32`. The payload binding detects
an extension paired with another otherwise-checksummed payload. Excluding the
native checksum field avoids a circular dependency during save preparation;
the native sum still validates that field. These checks detect accidental
corruption; they are not authentication or proof of semantic game-data validity.

Bits use least-significant-bit-first order within each byte. A villager bit is
the stable actor index, without the `E000` prefix. A furniture bit is
`(item & FFF) >> 2` for the reserved `3000..3FFF` range, so all four rotations
share ownership. The two pilots use bits 137 and 174; Cheri/Punchy use actor
indices 234 and 237. The current registry builder remains responsible for
assigning real supported identities; bit capacity does not enable unsupported
imports. Clothing and other future imported item classes require a reviewed
registry/format extension, not reuse of furniture bits.

The 672-byte working state is the 160-byte selection profile followed by the
512-byte catalogue. Packing checks that every owned imported item is in the
profile, preserves all original payload bytes except marker/checksum, clears
the complete extension, writes both CRCs, and balances the native checksum.
Packing twice with the same payload/state produces the same complete bank.

## Acceptance and profile policy

A valid `NAFJ` bank is treated as legacy: validate its original checksum and
town identity, ignore all extension bytes, and initialise an empty imported
catalogue with the current profile. This is codec-level V2 migration, not a
completed native load/migration path.

A `NAF3` bank additionally requires the exact format/registry, zero reserved
bytes, both CRCs, and internally consistent catalogue bits. Every saved required
selection must exist in the current profile. Additional current selections are
allowed; decoded state contains that expanded current profile and preserves
existing catalogue ownership. Removing a required villager or furniture bit
returns a distinct incompatibility result, without altering input/output data.

The conservative required profile records the selected set, not only actors
currently living in town. This also retains dependencies such as an imported
catchphrase borrowed by an original villager. Removing even an unused selected
import is rejected under this policy; a future dependency-aware migration can
relax this, but must prove safety before doing so.

`af_v3_save_check` returns `0` for valid legacy, `1` for valid V3, and negative
results for arguments (`-1`), header/town (`-2`), native checksum (`-3`), extension
format (`-4`), payload binding (`-5`), extension CRC (`-6`), missing profile
selection (`-7`), or inconsistent catalogue (`-8`). Output state is optional
and is written only on success. It must not overlap the bank or current profile.
`af_v3_save_pack` requires disjoint bank/state and an exact complete-bank size;
validation failures leave the bank untouched. `af_v3_save_collect` validates
player, item range, selection, and query/mark operation before changing a bit.

## Placement and verification

The codec occupies `8046B400..8046BA47` in the existing 48-KiB ABI-13 resident
prefix. The three entries are check at `8046B400`, pack at `8046B7A0`, and
collect at `8046B9C4`. The helper is 1,608 bytes; check/pack use 24-byte stack
frames, and collect is a leaf. The loader rejects overlaps and preserves both
resident guards, ROM-only models, and every original DMA identity.

Six focused host/cartridge tests pass. They cover an independent complete-bank
encoder, ordinary and compensated payload damage, torn payload/extension
pairing, CRC/format errors, profile additions/removals, arbitrary legacy padding,
all four players and all 1,024 furniture groups/rotations under sanitizers,
invalid/overlapping buffers, unchanged native flash code, exact import-free V2,
and complete patch reconstruction.

The [checkpoint](../docs/checkpoints/V3_SAVE_CODEC.md) records the native result.
Private-buffer checks do not establish actual two-bank persistence, fresh-process
reload, normal catalogue ordering, Controller Pak travel, or hardware operation.
Keep V2, user saves, and both web patchers unchanged.
