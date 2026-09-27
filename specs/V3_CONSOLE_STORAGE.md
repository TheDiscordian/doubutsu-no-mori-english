# Compressed console save storage

## Implemented boundary

`save_compressed.c` supplies a bounded, lossless format-five disk envelope around
one complete format-four bank and four independent console-save records. The
ordinary console converter prepares it alongside the recipe executor. It does
not install native hooks, write FlashRAM, allocate live RAM, or enable consoles.
The active cartridge remains format four.

Input is 65,536 canonical bank bytes plus 6,528 console bytes: 72,064 total.
Output remains one 65,536-byte bank, preserving two independent banks on the
128-KiB FlashRAM. No town fields, game progress, players, or backup are discarded.
Changing the save type does not supply a larger ordinary save device: the
[EverDrive-64 X7 manual](https://krikzz.com/pub/support/everdrive-64/x-series/everdrive-64-manual.pdf)
specifies 128 KB of battery-backed RAM and lists SRAM128K and FlashRAM.

Compression is checked before output changes. Uncompressible input returns
`AF_CZ_SPACE`; native preparation must stop before any erase/write call.
Capacity checks do not assert that every possible byte pattern fits. Native
timing and representative capacity still need review during integration;
synthetic fit checks are not exhaustive gameplay.

## Disk layout

Offsets are hexadecimal. Bytes `00..13` retain the canonical town/date header,
except for the native checksum at `12..13`. The `NAF3` marker stays at `04`;
the original town-ID mirror stays at `2F68..2F69`. Native header/town/checksum
readers can therefore validate the stored bank without decoding gameplay data.

The compressed stream occupies `14..2F67`, then `2F6A..F97F`: 63,850 bytes total.
Unused capacity is zero. The `680`-byte extension at `F980` contains:

| Offset | Bytes | Meaning |
| --- | ---: | --- |
| `00` | 4 | `AFS3` |
| `04` | 2 | Format 5 |
| `06` | 2 | Extension bytes `680` |
| `08` | 4 | Registry 3 |
| `0C` | 4 | Decoded bytes `11980` |
| `10` | 4 | Actual compressed stream bytes |
| `14` | 4 | Codec 1 |
| `18` | 4 | CRC-32 of complete disk bank, excluding this field and native checksum |
| `1C` | 4 | CRC-32 of complete canonical format-four bank |
| `20` | 4 | CRC-32 of all four console records |
| `24` | 4 | Reserved zero |
| `28..67F` | 1624 | Reserved zero |

All integers are big-endian. The native additive checksum covers encoded bytes
`00..F97F`. CRCs use CRC-32/ISO-HDLC. The canonical bank retains its existing
format-four checksums and all profile/catalogue/reward/surface bytes.

Codec 1 uses Yaz0 tokens without a file header: eight high-to-low literal flags,
literal bytes, or twelve-bit distance-minus-one and four-bit length-minus-two.
A zero length nibble adds a byte to 18. Distances are at most 4,096 and matches
at most 273. Unused final flags must be zero. Decoding must consume the exact
declared input and produce exactly 72,064 bytes. Invalid distances, overlong
output, truncation, trailing compressed bytes, and nonzero padding reject.

## API and memory

Pack requires disjoint output, canonical bank, console records, and an aligned
16,384-byte hash workspace. A bounded first pass measures capacity; only success
permits the second pass to write output. One hash candidate per source byte
bounds search work. Invalid arguments, malformed canonical data, and capacity
failure leave output unchanged. Hash scratch may change. Inputs must remain
immutable through both passes.

Expand uses separate 72,064-byte scratch. It validates the disk header, native
checksum, full CRC, and reserved bytes before token decoding, then both decoded
CRCs, canonical format/checksums, and matching headers. Scratch may change on
failure; do not commit any scratch content until success. The existing
`save_codec` must additionally validate profile/ownership before live-state
copying. CRC validity is not profile compatibility or semantic game validity.

The 3,368-byte MIPS core has no mutable globals or unresolved symbols. Its longest
stack chain is 152 bytes (pack, encode, key). It links at zero for preparation;
no native RAM location is assigned.

## Native integration plan

Retain stable codec/runtime entries, logical town size, and native two-bank I/O.
Add checked startup loading and independently initialized console state. Preserve
surface, goods, carrying, and exercise packets in every bootstrap refresh.

- Check: expand format five into private scratch, then invoke the checked
  existing format-four decoder. Older formats use the existing decoder.
  Probing a bank must not commit console progress.
- Pack: prepare the canonical copy through the existing format-four packer;
  wrap it and console progress into the original output bank. Capacity failure
  needs a distinct English error and must stop before any FlashRAM operation.
- Commit: validate everything first, then copy the **decoded** town, imported
  state, and console records together. Never copy compressed bytes to live RAM.
  Older formats initialize console records without erasing native game scores.
- Reset/new town/player deletion: clear only the appropriate independent records.
  A new player or town must not inherit the old player's or town's NES progress.
- Repair/verify: retain full encoded-bank comparisons and native checksums.
  Missing profiles and unsupported formats still stop automatic repair.
- Synchronous/travel-related town saving: retain the same complete bounds and
  pre-write gates. Controller Pak travel remains separately incomplete.

Candidate free space follows carrying state `804DC400..804DC7FF` and precedes
the `80500000` model pool. A possible layout is console state at `804DC800`,
code at `804DE200`, decode/canonical scratch at `804E3000`, and hash scratch at
`804F5000`. These are **not installed allocations**. Prove and guard every actual
packet/state boundary against the current immutable build before assigning them.
The decode area can serve as the canonical pack buffer because these operations
are not concurrent; guard against re-entry explicitly.

Format-five saves cannot load in V2 or older format-one/two/three/four V3 builds.
The eventual handoff must warn and preserve backups. Native integration, a fresh
save/reload, and original hardware remain unverified. The main lock and deployed
V2 patchers do not change during this experimental work.
