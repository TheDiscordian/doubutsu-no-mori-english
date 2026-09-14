# V3 additive object-bank loader

## Implemented boundary

`tools/v3_asset_loader.py` constructs a local development cartridge from exact
V2-11 and verified donor artwork. The new loader retains all 410 existing object
banks and provides twenty additional, subset-independent villager texture slots.
Cheri and Punchy's converted texture objects occupy their assigned slots.
Other new slots are empty and rejected by the loader.

The asset-only variant installs loading, not new villagers. The optional
[`--npc-draw` variant](V3_NPC_DRAW.md) adds pilot draw records, reserved actor
identities, and full voice-ID transport in a 16-KiB ABI-2 blob. Neither variant
enables move-ins, houses, dialogue, or imported audio playback. Villager construction,
saved identity, item imports, and browser selection remain required. Do not
present this development cartridge as a playable-import handoff.
The [audio variant](V3_VILLAGER_AUDIO.md) and
[villager text variant](V3_VILLAGER_TEXT.md) add their separately documented
runtime paths. The text variant uses a 32-KiB ABI-4 blob and patches shared
translation readers; the asset-only memory/code preservation statements below
do not describe those additional text hooks.

## Memory ownership and startup

| Range | Owner |
| --- | --- |
| `801948E0..8019A8DF` | Existing translation code/data, unchanged |
| `8019A8E0..8019ACBF` | V3 startup helper, within the existing resident reservation |
| `8019ACC0..8019ACCF` | V3 VROM, byte count, CRC-32, and configuration ABI |
| `8019ACD0..8019ACDF` | Installed flag and reserved state |
| `8019ACE0..8019C8CF` | Remaining isolated diagnostic scratch, not production allocations |
| `8019C8D0..8019C8DF` | Existing translation guard |
| `80460000..80461FFF` | V3 header, asset code, expanded object table, and guards |

V3 owns the `80460000..8046FFFF` region for further import data/code. Only the
first 8,192 bytes are loaded in this batch. The native test uses
`80463000..80464FFF` for disposable object-DMA readback. Neither region overlaps
the title reservation, font reservation, ordinary arenas/framebuffers, or the
emergency fault framebuffer. No system/game heap growth is required.

The existing resident reservation remains 32 KiB. Its header, first 24 KiB,
initialiser, cache setup, and end guard remain intact. V3 explicitly consumes the
first 1 KiB of the former diagnostic scratch; do not use the old `+6000` native
test return address with this cartridge. The V3 scenario uses `+6480`, with its
mock object arena at `+6500` and the existing guarded test stack above it.

Change only the startup-chain call at `800D65D0`: call the V3 helper instead of
`8009D6D0`. The helper first calls that preceding initializer, preserving all
existing startup work. On a machine without eight MiB, it returns without
touching upper RAM or changing the object loader, retaining the low-memory
English Expansion Pak warning path.

With eight MiB, validate the exact VROM/size/configuration ABI, synchronously DMA
the blob, verify CRC-32 and its header/guard, write back the data cache, and
invalidate the code cache before executing the blob's installer. The installer
checks the native object entry before patching it, then performs both cache
operations on the changed instructions. Failures propagate to the existing
startup failure path; no new object hook is installed after a failed DMA/CRC.

## Object lookup and allocation

The original `func_800C5AA0_jp` consumes `gObjectTable` while preparing a shared
scene object-arena allocation. Its synchronous and queued paths use that function.
The installed entry jumps to `af_v3_object_status` in the checked V3 blob.
NPCs also fill their own preallocated model/texture slots through separate
[reserved-bank streaming functions](V3_NPC_DRAW.md#reserved-bank-streaming).
The draw variant connects both of those direct table readers to the expanded
table. Testing the shared scene allocator alone does not verify NPC streaming.

Preserve the original low-sixteen-bit, signed bank conversion explicitly; do
not rely on every caller to sign-extend its argument. Reject negative indices,
indices at or above 430, reversed bounds, and uninstalled extended banks before
writing object or arena state. Preserve native empty-bank handling for indices
below 410. Reject arithmetic overflow and retain the native strict arena limit:
an aligned allocation equal to the arena end is refused.

For accepted allocations, retain the native status layout, negative loading ID,
segment/VRAM/VROM/size fields, keep/pending flags, and 16-byte arena alignment.
The ordinary native DMA and completion code still load the object and mark its
ID positive. Do not replace those native ownership or DMA lifetimes.

The complete original 410-entry table is copied from V2 into the V3 blob at
`80461000`; every nonempty entry is checked against the current cartridge DMA
range. The remaining twenty entries are reserved in English donor order:

`bank = 410 + donor_index - 216`

`texture_vrom = 03F10000 + (donor_index - 216) * 2000`

| Identity | Bank | Texture VROM | Bytes |
| --- | --- | --- | --- |
| Cheri, `GAFE01-r0/villager/00E8` | 426 | `03F30000` | 5,664 |
| Punchy, `GAFE01-r0/villager/00EB` | 429 | `03F36000` | 5,664 |

These are object-bank assignments, not actor/name/save IDs. Do not compact or
reassign the slots when selecting a different subset. The
[separate actor registry](V3_NPC_DRAW.md) preserves existing normal, test, and
special-character distinctions; bank IDs are not saved actor IDs.

## Cartridge composition and compatibility

The V3 blob uses VROM `03F00000`. All added resources occupy verified unclaimed
ranges and append DMA rows without renumbering any existing row. Repack from
the verified original to avoid appending to the already padded cartridge. Retain
both physical and virtual startup copies, all unrelated resources, and N64 CRCs.
An empty composition returns exact V2-11. Complete UPS reconstruction is checked.

No saved format or villager roster changes in this batch. That does not establish
future imported-ID/profile compatibility. Use disposable saves for development;
the current native check restores its emulator checkpoint and does not validate
a game save/restart cycle. V2, user saves, and public/local patchers remain intact.

## Focused verification

Host address/undefined-behaviour sanitizers cover startup configuration, missing
RAM, DMA/CRC/header/entry failures, repeated initialization, guard failure,
native status fields, signed arguments, bank limits, and allocation rejection.
Cartridge checks bind actual textures, all original table entries and DMA indices,
the only permitted code changes, the import-free path, and UPS reconstruction.

`tools/v3_asset_loader_scenario.py` generates ignored native expectations from
the exact current development cartridge. In a silent, isolated emulator, verify
startup installation, the complete upper-RAM blob, and the real synchronous
native object-loader path for an existing cat model and both imported texture
banks. Compare every loaded byte and the complete test arena, reject uninstalled
and out-of-range banks, exercise a non-sign-extended bank argument, check guards,
and restore the checkpoint. No rendered appearance, complete NPC behaviour,
save compatibility, or original-hardware acceptance follows from these checks.
