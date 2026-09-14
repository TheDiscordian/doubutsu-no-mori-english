# Complete V3 villager artwork loading

## Scope

`tools/v3_villager_assets_runtime.py` adds the verified twenty-villager artwork
bundle to the complete experimental cartridge. The bundle contains twenty
texture objects, Pigleg and Yodel's separate models, and sixteen accessories.
The shared native object loader can load all 38 objects. This does not install
the eighteen remaining draw records or attach accessories to their owners.
All twenty ordinary move-in flags remain disabled.

The builder requires the exact ABI-50 complete cartridge and pinned artwork
manifest. It builds ABI 51 without rerunning unchanged conversions or rebuilding
unrelated runtime components. The default earlier build stages retain their
430-bank and growth-address constants; the complete-asset suffix supplies the
expanded values explicitly. Both V2 patchers remain unchanged.

## Stable object registry

Registry version 1 assigns banks independently of checkbox or conversion order:

| Content | Bank | VROM |
| --- | --- | --- |
| Twenty English-donor textures | `410 + donor_index - 216` | See below |
| Pigleg's separate model | 430 | `02212000` |
| Yodel's separate model | 431 | `02214000` |
| Accessories, donor tools 52 through 67 | `432 + tool - 52` | `02218000 + (tool - 52) * 2000` |

Cheri's texture keeps bank 426 / VROM `03F30000`; Punchy's keeps bank 429 /
VROM `03F36000`. Their complete existing DMA resources remain untouched.
The other eighteen texture resources use
`02240000 + (donor_index - 216) * 2000`.
Every slot is checked for complete input identity, alignment, size, and overlap.
Unknown donor/tool indices, duplicate banks, altered files, or incomplete bundles
are rejected. These are loading identities, not saved actor or item IDs.

Yodel's model uses skeleton `06002770`, not the native gorilla's `06002610`.
Pigleg's uses `06001CB8`. Each accessory registry row retains its verified joint,
donor tool, and segmented display-list address for the attachment implementation.
Installing the bank does not execute that display list or establish appearance.

## Memory and loading

| Range | Owner |
| --- | --- |
| `80460100..80460F73` | Existing asset/helper code, 3,700 bytes |
| `80461000..80461DFF` | Expanded 448-entry object table |
| `80461E60..80461E73` | Twenty move-in eligibility flags, all zero |
| `80461E80..80461F5F` | Native starting-population permissions, 224 bytes |
| `80463400..804639DF` | Existing selection code, 1,504 bytes |
| `80460000..8046BFFF` | Unchanged 49,152-byte startup reservation |

The complete original 410-entry object table remains intact. The growth table
is the exact original `00E0D000` resource. Its reader uses `80461E80`; no other
selection behaviour changes. Candidate/shuffle arrays, saved appearance history,
profile metadata, and save-code resources remain unchanged.

Recompilation changes exactly four MIPS instructions: asset bank capacity,
startup capacity, startup ABI, and the growth-table load offset. Helper sizes,
all linked symbol addresses, and every other instruction remain unchanged.
The startup header and checked prefix CRC reflect the new table/code contents.
The startup DMA still loads only `C000` bytes, not the entire asset file.

New artwork shares the existing `02200000` demand-loaded file. Its complete
size is 415,264 bytes, ending at `02265620`, within the 2-MiB storage reservation.
Native object DMA reads the interior resource spans. The standard strict arena
end check, low-sixteen-bit signed bank conversion, negative pending ID, alignment,
completion, and ownership rules remain. Indices at or above 448 are rejected.
The native NPC model/texture limits remain `2800` / `1620` bytes. Yodel's
10,112-byte model leaves 128 bytes in its model buffer.

## Cartridge and compatibility

The builder checks all unused physical padding and appends the expanded blob
there, changing only that DMA row. The translation module is patched in its
existing uncompressed physical allocation. All 3,389 directory identities and
all other physical DMA ranges are retained, including the directly addressed
audio files. No additional DMA row or cartridge growth is required: output
remains 32 MiB. N64 checksums and complete UPS reconstruction are verified.

This suffix does not change the existing V3 profile or saved formats. That is
not a new cross-build save/restart claim. Earlier V3 profiles and V2 do not gain
compatibility with imported saves. Keep user saves intact; no new playable
handoff or original-hardware acceptance is claimed.

## Verification and next integration

[The implementation checkpoint](../docs/checkpoints/V3_COMPLETE_VILLAGER_ASSETS.md)
records seven focused host/cartridge checks and the 93-record native run.
Native loading covers an original model, an existing pilot texture, a mouthless
texture, both separate models, the largest accessory, and the last valid bank.
Complete contents, unused destination tails, object status, arena ownership,
invalid indices, signed arguments, and resident/save/furniture guards pass.
Both native initial populations and all four selection entries pass after the
growth relocation, with temporary flags and state restored.

The [attachment variant](V3_ACCESSORY_RUNTIME.md) supplies all twenty draw rows
and all sixteen runtime attachments, with shared storage and frame-local
transforms. Remaining voices, text/defaults/houses, town behaviour, ordinary
appearance, and persistence still require integration. Neither converted
artwork nor loading evidence is a playable islander. Do not enable move-ins
or switch a web patcher on that basis.
