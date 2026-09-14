# V3 furniture ground handling

Enabled furniture imports use native furniture drop flags and the normal
ground-drawing descriptor. IDs and rotations remain unchanged throughout.
The adapter changes three windows in the `BgItem` actor overlay:

| Window | Purpose |
| --- | --- |
| `8090F888` | Furniture drop flags on the first drop path |
| `8090FA1C` | Furniture drop flags on the alternate drop path |
| `80911CF0` | Furniture branch in the ground descriptor function |

The owner at VROM `00805E30` is linked at `8090D530`, with 39,216 file bytes and
40,384 resident bytes. Relocations at `0080F760` retain all 1,103 entries.
`tools/v3_furniture_ground.py` binds both complete sources, section sizes, and
the actor allocation descriptor at `80100CB0`. It rejects changed instructions,
relocations inside replaced windows, and incoming branches/pointers into their
interiors. No owner allocation or saved structure grows.

Each detour queries the full-register furniture classifier with the original
item in A0. Two windows retain their original mask temporary. The alternate
window replaces a shift and branch, so the detour reproduces the branch and its
V0 = 0 delay instruction for both outcomes. The earlier mask at `8090F878` is
itself a branch delay and stays intact. The live owner pointer at `80100CC0`
provides each continuation; RA uses full-width saves/restores.

ABI 11 adds 264 bytes at `8046AE00`–`8046AF07`, retaining the 48-KiB reservation,
model tail, guards, all previous helpers, and ordinary heap bounds. Three original
instruction pairs change; surrounding code, descriptors, and graphics remain.

The other reviewed `BgItem` type tests either distinguish zero from nonzero or
accept types below 4. Original furniture type 1 and imported type 3 already follow
the same path there. The hand-over actor's type test at `809644C0` checks type 2;
both furniture types already take the same non-type-2 path. That actor and its
relocation data stay unchanged. These observations do not establish complete
ordinary drop/pickup or hand-over gameplay.

## Verification and remaining work

Three focused tests verify exact owner edits, unchanged relocations and hand-over
files, the resident layout, query binding, full-width instructions, guards/CRC,
patch reconstruction, deterministic composition, and the unchanged import-free
V2 output. The [native checkpoint](../docs/checkpoints/V3_FURNITURE_GROUND.md)
checks actual owner loading/relocation, full-register windows, both native drop
flag paths, and the complete ground-descriptor function.

Original furniture and both selected imports receive drop flag `0200` and ground
drawing entry 47. A disabled import retains the native fallback descriptor;
the required save/profile guard must prevent unsupported imported IDs from
reaching ordinary gameplay. This adapter does not replace that guard.

Inventory furniture-count/index queries, catalogue collection/order generation,
room scoring, acquisition, and ordinary placement/persistence remain required.
Both web patchers remain V2 pending the user's testing and explicit approval.
