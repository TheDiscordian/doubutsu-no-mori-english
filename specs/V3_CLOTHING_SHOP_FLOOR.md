# V3 clothing shop-floor integration

## Scope

The clothing build connects imported garments to the native shop's reserve-point,
floor-selection, and sale-reporting paths. Selected cherry shirt `34BF` uses
clothing reserve `1F29`, remains selectable by its full ID, and reaches native
sold-clothing handling. Existing furniture hooks, native clothing, other goods,
and sold markers remain intact. This is distinct from the
[mannequin count and artwork adapter](V3_SHOP_MANNEQUIN.md).

## Native owner and branch handling

The owner, descriptor, and relocation sizes are unchanged from
[furniture shop-floor integration](V3_SHOP_FLOOR.md). The builder validates the
complete original owner and then applies the three clothing edits to the
already-patched furniture owner, preserving those earlier instructions.

| Branch | Meaning | Retained delay instruction |
| --- | --- | --- |
| `80953F14` | Clothing reserve point | `AT = 1F35`, original branch-likely |
| `809548C8` | Clothing floor selection | `AT = item < 2200` |
| `80954A74` | Clothing sale/removal | `A0 = u16[SP + 46]` |

Only each branch word changes. In particular, native lower-bound paths may
enter a retained delay instruction directly. Those paths must remain available.
The helper recomputes the `2500` upper bound; original garments use the short
path. Higher IDs invoke mode 3 of the existing checked full-register query.
A selected installed garment gives its nonzero full render index; unknown or
unselected garments do not enter the clothing path.

For the reserve-point branch, the helper reproduces the original likely-branch
delay only when taken. For selection, its register-only comparison is recomputed
in the corresponding branch delay. The sale's retained jump delay performs its
stack read once before the helper; the query preserves that loaded A0 and does
not repeat the memory read. Continuations use the actual loaded-owner pointer
at `80101140`, preserving all other native instructions.

## Sale processing

The complete native function beginning `80954970` obtains the selected full ID
and checked price, updates the shop's existing sales total, and calls native
`800BFFC0` to replace only the purchased goods entry with `1F35`. It then calls
the real mannequin clip callback at `8095A024`, which sets the matching slot's
naked-model flag, and clears the foreground tile through native `8008A81C`.
No substitute sale routine or model callback is installed.

## Memory, saves, and verification

ABI 39 uses a combined 728-byte shop-floor helper at `80467C00..80467ED7`.
Its original 340 bytes and public addresses are unchanged; the three clothing
entries start at `80467D54`, `80467DD8`, and `80467E58`. The 280 bytes before
the existing `80467FF0` guard remain available. The shared query retains its
32-byte caller frame and 256-byte register wrapper; continuations use a separate
16-byte frame. No actor, model buffer, DMA resource, or saved field grows.

The saved format remains 2 with the same 192-byte selected profile and
864-byte guarded runtime. Same-profile ABI-38 clothing saves retain their
representation; older format-1 V3 builds and V2 cannot load format-2 saves.
Both patchers remain V2 pending user testing and explicit approval.

The current cartridge check and initial native check pass. Native verification
executes full reserve/selection functions and the complete sale-reporting flow,
including the native mannequin callback and foreground write. It does not
execute ordinary player confirmation/payment or GPU drawing. Exact artifacts
and limits are in the [checkpoint](../docs/checkpoints/V3_CLOTHING_SHOP_FLOOR.md).
