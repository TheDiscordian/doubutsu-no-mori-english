# V3 furniture inventory icon

The submenu parent selects the native furniture leaf descriptor for enabled
imported furniture. Gift, gyroid, and fossil checks retain their original order
and instructions. The actual leaf palette, texture, and drawing code are unchanged.

`tools/v3_furniture_icon.py` binds the complete current parent at VROM `007749C0`
and its relocation file at `007778B0`. The file has 12,016 bytes and a 79,392-byte
resident allocation, linked at `8085BAC0`. Its 134 relocations and all section
sizes remain unchanged. The installer checks the native allocation descriptor,
instruction pair, relocation locations, and incoming branches/pointers.

Only the shift/constant pair at `8085C880`–`8085C884` is replaced. The mask at
`8085C864` belongs to an earlier branch delay slot and remains intact. The detour
queries the existing full-register classification wrapper using the complete
item in S0, writes type 1 to T1 for an enabled import, reproduces AT = 1, and
returns to `8085C888`. Other inputs retain their native type. No saved identity
is rewritten into an original furniture ID.

The live parent address comes from `8010DCEC`; the continuation is parent +
`0DC8`. RA uses full-width saves/restores, including the final jump delay slot.
The helper occupies 76 bytes at `8046AB00`–`8046AB4B`. ABI 10 keeps the 48-KiB
resident reservation, existing guards, model-tail positions, and heap bounds.
The tag-menu, room, and shared-field helpers remain unchanged.

## Verification and limits

Three focused tests check the complete installed parent, retained resources,
compiled helper and query address, full-width instructions, guards/CRC, exact
composition, patch reconstruction, and the unchanged import-free V2 output.

The [native checkpoint](../docs/checkpoints/V3_FURNITURE_ICON.md) covers the actual
parent load/relocation, full-register detour cases, native descriptor selection,
and complete native drawing-command generation. Both imports generate the same
27 commands as an ordinary furniture leaf. Gyroid, fossil, and gift commands
remain distinct. This test does not submit graphics to the GPU or exercise an
ordinary inventory session, item acquisition, or saving/loading.

Disabled or unknown imported identities do not receive furniture classification.
The required save/profile guard must prevent unsupported saved IDs from reaching
ordinary readers; retaining the native type is not that guard. Catalogue flags,
outside-field consumers, scoring, acquisition, and persistence remain work.
Both web patchers stay V2 pending the user's testing and explicit approval.
