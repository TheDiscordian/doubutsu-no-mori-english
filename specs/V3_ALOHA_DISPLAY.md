# V3 complete imported-shirt displays and catalogue

## Fixed identities and dependencies

The three imported garments use separate pocket, resource, room, and catalogue
representations. Selections never renumber these identities.

| Garment | Donor | Pocket | Resource index | Display | Room index | Catalogue index |
| --- | --- | --- | --- | --- | --- | --- |
| Cherry shirt | `24BF` | `34BF` | `10BF` | `3AFC` | 1727 | 2751 |
| Red aloha shirt | `241A` | `341A` | `101A` | `3868` | 1562 | 2586 |
| Blue aloha shirt | `241B` | `341B` | `101B` | `386C` | 1563 | 2587 |

Each display requires both its selected display bit and its selected garment.
The red/blue display dependencies are profile byte 99, masks `04` and `08`;
their garment dependencies are byte 163 with the same masks. Cherry keeps bytes
119 and 183, mask `80`. Disabled or malformed entries retain native fallback
behaviour and cannot supply an imported model. Full pocket IDs survive all four
display rotations and inverse conversion, including catalogue order conversion.

Both aloha garments retain their actual zero donor price and exclusive status.
They are not inserted into ordinary shop lists. Catalogue visibility follows
collection; visibility does not establish ordinary purchasability or acquisition.

## Runtime and memory

`tools/v3_aloha_display.py` builds ABI 58 from the pinned complete-town cartridge.
It replaces guarded shared consumers and recompiles the catalogue from the
immutable translated V2 owner. Native item conversions retain their complete
original bodies behind the existing bridges. Native clothing and furniture,
all twenty town records, original audio positions, and saved-format code remain.

The shared display predicate and register-preserving bridge occupy 304 bytes
at `80466380`. Red and blue use complete 80-byte rows at `80466540` and
`80466590`, ending before the live native conversion bridges at `804665E0`.
Each profile retains all 68 bytes of the native mannequin profile. The preserving
bridge uses 144 stack bytes and retains complete 64-bit caller registers, as
required by the existing compiled callers. No resident allocation grows.

The expanded furniture consumer occupies 1,400 bytes at `80465800`; table
initialization uses 160 bytes at `8046A000`. The canonical item/collection readers
use 544 bytes at `80466C00`, and conversion uses 192 bytes at `80466270`.
The existing 2,051-entry furniture tables cover all three profiles. Each display
loads its full 544-byte garment plus the unchanged 3,584-byte native mannequin,
using the native 4,128-byte transfer and existing callbacks/buffers.

The clothing catalogue preserves all 245 native entries in their original
order, followed by cherry, red aloha, and blue aloha: 248 entries total. The
complete 247-entry donor table and conversion code establish each source index.
Furniture retains its separate 439 entries. Full names, ownership, selection,
prices, preview initialization, and inverse item conversion use shared readers.

The catalogue image is 56,624 bytes, with a 2,944-byte suffix and 720-byte
relocation resource. Its conservative menu requirement is 274,240 of 274,560
reserved bytes, leaving 320 bytes. The permitted code boundary does not enlarge
the pool; both linker bounds and actual allocation checks remain enforced.

The rebuilt catalogue and relocation resource share read-only physical storage
with the final blob, at blob offsets `11EB10` and `12C840`. Original physical
resources are retained. Blob length is `12CB10`, ending at physical `01FFA870`;
22,416 bytes remain before the 32-MiB cartridge boundary. Further large content
requires an explicit storage-capacity change, not unchecked padding use.

## Compatibility and remaining work

Saved format 2 stays unchanged, but the selected profile adds two dependencies.
The actual codec accepts ABI 57 profiles in ABI 58 and rejects ABI 58 profiles
in ABI 57 without writing the source bank or output state. Older builds cannot
load these new-profile saves. This does not establish ordinary cross-build
save/restart compatibility; preserve saves and use disposable copies.

The [checkpoint](../docs/checkpoints/V3_ALOHA_DISPLAY.md) records focused and
native verification. Ordinary aloha acquisition, placement/persistence, combined
villager gameplay, house entry, and the unresolved new-instrument playback still
require work. This artifact is not a complete V3 playtest handoff. Both patchers
remain V2 until user testing and explicit approval.
