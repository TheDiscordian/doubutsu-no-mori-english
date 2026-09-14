# V3 furniture shop-floor integration

## Native contract

`--shop-floor` includes all five shopkeeper interaction adapters and connects
the separate `Shop_Design` owner's furniture range checks. Selected imports
use the native furniture reserve point, remain selectable by their actual floor
IDs, and enter the original sold-furniture removal path. Existing event status,
other goods categories, sold markers, and original furniture remain unchanged.

The owner is VROM `00848BF0`, linked at `80953E20`, with 3,792 bytes and no BSS.
Its 144-byte relocation resource is at `00849AC0`. Section sizes are 3,680 text
and 112 data bytes, with 29 relocations. Its loaded-address field is `80101140`.
All native allocation and relocation data remains unchanged.

The clothing-enabled variant also includes three separate
[clothing decisions](V3_CLOTHING_SHOP_FLOOR.md). Its 728-byte combined helper
retains the complete 340-byte furniture helper and all its public entries.

| Branch | Purpose | Native branch/delay |
| --- | --- | --- |
| `80953E54` | Reserve point | `BEQL`; `AT = 1F36` only when taken |
| `80954888` | Floor selection | `BNE`; `AT = item < 2000` on both outcomes |
| `80954AD0` | Sold furniture removal | `BEQ`; `V0 = 80130000` on both outcomes |

All three use the original `1ECD` upper bound. Lower-bound paths remain native.
The adapter queries the existing selected-furniture reader at `804680B8` and
preserves each branch's intended register effects and continuation.

## Delay-slot preservation

Only the three branch words are replaced. The original delay instructions stay
in the actor. This matters because a preceding native branch enters the floor
selector's delay instruction directly; replacing a two-word window with a jump
and NOP would break that original path.

The retained delay can run on the jump into the helper. Its effects are limited
to the explicitly verified register assignments above. The helper recomputes
the upper predicate, then reproduces the original branch/delay or annul result.
The likely branch skips its delay result when furniture is accepted. No memory,
I/O, or other side effect is duplicated. The native complete floor selector's
low-value fallback verifies the retained incoming path.

## Memory and bounds

The helper occupies 340 bytes at `80467C00..80467D53`, after the shopkeeper
adapter and before the guard at `80467FF0`. ABI 18 uses the same loaded 48-KiB
prefix and the same saved format/profile. Imported saves still require V3.

The builder verifies the complete source/relocation hashes, actual allocation
descriptor, inventory of all three upper checks, expected branch/delay words,
absence of displaced relocations, compiled dependencies, free destination,
composition, startup CRC, and ROM checksums. Import-free composition returns
the pinned V2 unchanged. Neither web patcher changes.

## Verification and remaining work

Three focused tests and a 63-step native check pass. Native verification covers
actual owner loading/relocation, fifteen full-register branch cases, eight
complete reserve selections, and eight complete floor selections. The latter
uses a real one-block field description with native existence, bounds, index,
and grid lookup functions; no lookup callback is substituted. Both imports,
rotations, originals, unknown/disabled items, event priority, and sold markers
are represented. Guards, state restoration, and graceful shutdown pass.

The sold-removal classification branch is verified, but the actual model
extinguish callback, payment, shop drawing, and ordinary transaction are not
executed by this check. Finish room scoring and the combined ordinary
acquisition/placement/pickup/persistence check before claiming complete items.
See the [checkpoint](../docs/checkpoints/V3_SHOP_FLOOR.md) for exact artifacts.
