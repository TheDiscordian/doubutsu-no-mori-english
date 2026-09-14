# V3 furniture shop interactions

## Scope and native decisions

`--shop-actors` includes native stock, catalogue, collection, and save support,
then adapts four local furniture decisions in each of the five shopkeeper
actors: Cranny, convenience store, department store, twins, and supermarket.
The decisions choose purchase camera tracking, lottery-ticket eligibility,
conversation camera, and the floor-item purchase conversation callback.

Only selected registered imports act as furniture. Their real item IDs stay
unchanged. Unknown/disabled imports and original item categories keep their
native classification. Existing purchase/sale prices, payment logic, names,
messages, ticket accounting, and translated counter fields are retained.

The [shop-floor adapter](V3_SHOP_FLOOR.md) connects the independent reserve-point,
item selection, and sold-item removal checks. These adapters do not claim
ordinary shop transactions, rendered furniture, or a complete playable item.
Both web patchers remain V2 pending user testing and approval.

## Installation and memory

`tools/v3_shop_actors.py` binds complete current V2 actor hashes, their original
relocations, and exact native allocation descriptors. It replaces twenty
reviewed two-instruction windows with resident detours. Incoming branches,
relocated pointers, delay slots, and displaced relocations are checked.

Most windows contain adjacent mask/shift instructions. Four floor-conversation
windows instead separate the mask from its shift with live stores and a relocated
address load. Those windows replace only the later shift/constant pair, read
the retained original item in `a0`, and preserve the intervening operations.
The twins use the adjacent form. Mask temporary values and overwritten constants
retain their native effects.

Each detour calls the existing full-register-preserving furniture query at
`804680B8`. Continuation uses the corresponding actor's actual loaded-address
field in the native descriptor; it does not assume the linked overlay address
is executable RAM. Integer/FP registers, HI/LO, branch delays, and the caller's
complete return register are preserved apart from the intended native outputs.

The 1,520-byte helper occupies `80467600..80467BEF`, after the 700-byte shared
item helper and before the guard at `80467FF0`. ABI 17 uses the unchanged 48-KiB
resident prefix. No actor/resource size, native relocation, heap allocation, or
saved format changes. V3 imported saves still require compatible V3 profiles.

## Delivery and remaining gameplay

The native pending-order loop and translated mail creator already use the real
imported ID and shared full-name reader. A combined native check confirms both
complete delivered records, attached IDs, complete decoded English text, and
pending-order clearing. No additional mail code or duplicate name hook is needed.
The accent-aware mail reader remains in its V2 Expansion Pak owner `80450010`.

The [checkpoint](../docs/checkpoints/V3_SHOP_INTERACTIONS.md) records three focused
tests and the 148-step combined native pass. It includes actual overlay loading,
forty live-register windows, thirty complete native ticket decisions, and the
previously unfinished delivery/read tail. It does not use ordinary shop controls
or test payment confirmation, shop-floor removal, or FlashRAM writing.

Finish shop-floor handling, scoring, ordinary acquisition/placement/pickup and
persistence, villager houses/move-in, and Controller Pak transport before calling
the pilots complete. The wider English-donor import goal remains in scope.
