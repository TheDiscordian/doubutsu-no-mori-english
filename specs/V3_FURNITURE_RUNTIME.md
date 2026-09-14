# V3 furniture profile and model loader

## Implemented boundary

`tools/v3_furniture_runtime.py` installs the reviewed haz-mat barrel and oil drum
profiles and models into the combined V3 development cartridge. The native room
overlay selects, loads, reuses, and releases their model banks. Original furniture
keeps its own profile-overlay allocations, model loader, and cleanup path.

This is loader integration, not a complete furniture import. Shared item
classification, English names, inventory, prices, acquisition, placement,
collision/rendered appearance, catalogue/scoring, houses, and saved-item/profile
handling remain required. Neither object is selectable in a web patcher.
The [native checkpoint](../docs/checkpoints/V3_FURNITURE_RUNTIME.md) records the
exact current cartridge and tests. Public/local patchers remain V2.

## Stable identities and ROM layout

Furniture registry version 1 assigns explicit identities independent of selection
order. Native indices `0`–`946` and the inverse-conversion sentinel `947` remain
unchanged. Other unused indices do not become enabled merely by extending tables.

| Donor base item | Runtime index | Destination item/rotations | Model VROM |
| --- | --- | --- | --- |
| `3224` | 1,161 | `3224`–`3227` | `03F08000` |
| `32B8` | 1,198 | `32B8`–`32BB` | `03F0A000` |

The native DMA directory has 3,390 rows, including its terminator. The stable V2
uses 3,386 files; the existing V3 resident file and two villager texture files
use the remaining three. Furniture models therefore occupy the ROM-only tail
of the existing uncompressed V3 file at `03F00000`, not additional directory
rows. Interior VROM reads use the ordinary synchronous DMA service.

That ROM file contains 44,176 bytes. Only its first 32,768 bytes are loaded at
startup and included in the resident CRC. Each model is 3,216 bytes, read on
demand into an existing 5,120-byte native furniture bank. The next villager
texture reservation at `03F10000` remains untouched. Bounds reject overlap;
neither the native DMA-directory capacity nor resident RAM allocation grows.

## Resident layout and ownership

V3 ABI 5 retains the 32-KiB reservation at `80460000`. Earlier asset, draw, audio,
and text data retain their offsets. Furniture uses the following additional areas:

| Offset | Content |
| --- | --- |
| `5000`–`57FF` | Furniture helper/bridge code; current compiled length 956 bytes |
| `5800`–`6BCB` | 1,267 resolved profile pointers |
| `6C00`–`70F2` | 1,267 bank indices; `FF` means no bank |
| `7200`–`729F` | Two 80-byte import records |
| `7FF0`–`7FFF` | Existing resident guard |

Each import record contains its 16-bit index, 16-bit item, enabled word, 68-byte
native profile, and padding. Profiles at `80467208` and `80467258` are resident
constants. They retain verified donor dimensions, rendering layers, and scalar
flags from [the artwork conversion](V3_FURNITURE_ART.md). No dynamic callback,
animation rig, or unsupported behaviour is silently removed.

The original overlay-allocation table remains inside `My_Room` and has only its
947 native entries. Native initialization and destruction clear/free that prefix
and retain shared gyroid ownership. They never free the resident imported
profiles. Native furniture bank buffers and their 100-entry address table remain
owned by the room overlay; no replacement bank allocator is introduced.

## Native overlay adaptation

`My_Room` is VROM `0082D7F0`, link address `80936710`, 93,200 file bytes, and
8,944 BSS bytes. Its relocation file at `00844400` has 6,208 bytes. The patcher
binds both the original source and the current V2 owner, including the existing
English name-reader patches at `8093931C` and `80939994`.

The patcher resolves paired HI16/LO16 references using the native relocation
rules. It retargets 57 profile-table and 15 bank-index references, removes their
142 obsolete relocation records, and retains the other 1,401 records. Mixed
high-half groups, unknown targets, changed instructions, and unexpected source
hashes are rejected. Relocation storage and native overlay size remain unchanged.

The bank reset/free-bank scans retain their unrolled three-plus-four structure;
the expanded capacity of 1,267 has the same remainder as 947. Profile interaction
scans, occupied-bank checks, and existing-bank re-DMA traverse the expanded table.
The native re-DMA loop's calculated `1xxx` item value is unused by these static
profiles. Item-dependent callbacks require a separate adapter.

Six native entries route to bounded resident helpers:

| Linked entry | Responsibility |
| --- | --- |
| `8093678C` | Profile load: selected resident import or original native body |
| `80937490` | Whether a supported index has a valid bank |
| `809374C4` | Bank index, rejecting unavailable imports/out-of-range banks |
| `809374F4` | Bank address from the actual loaded room owner |
| `8093885C` | Model DMA: validated import or original native body |
| `80942688` | Index/rotation to native or selected imported item |

Assembly bridges reproduce the original displaced prologues and jump to the
actual loaded overlay, never its link address. The actor descriptor at
`80100DF0` supplies its live address at `80100E00`. Bank lookup verifies owner
identity, bounds, alignment, and the 100-bank limit. Imported DMA additionally
checks the selected profile, expected segment, complete model extent, destination
ownership, and the 5,120-byte bank limit. A failed transfer does not register a
bank. Re-DMA with bank index `-1` requires an already registered matching bank.

## Verification scope

Five focused checks cover sanitized helper/startup execution, registry values,
ROM-only tail bounds and profile contents, current cartridge/UPS reconstruction,
exact import-free V2 retention, preserved English patches, and relocated tables
at two different live addresses.

The bounded emulator fixture uses the real overlay loader and native room
functions. It checks both complete imported model transfers, all four item
rotations, absent IDs, bank selection/reuse/release, original profile allocation
and model DMA, native cleanup, the complete restored resident prefix, memory
guards, and a checkpoint restore followed by resumed execution. It uses an
isolated blank cartridge, disables physical audio, and performs no game save or
Controller Pak write calls.

Ordinary placement, rendered appearance, collision, acquisition, saving/loading,
and original-hardware compatibility are not established by this component check.
V3-with-imports save compatibility remains unestablished; preserve existing saves
and keep the saved V3 phrase-reference warning in every playable handoff.
