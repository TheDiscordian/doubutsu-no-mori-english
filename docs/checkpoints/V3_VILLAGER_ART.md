# V3 Punchy and Cheri artwork batch

## Completed work

The [artwork converter](../../specs/V3_VILLAGER_ART.md) produces two native
texture objects directly from the verified English donor. Both contain complete
body/palette data and all eight eye/six mouth frames. Cat and cub ordering and
body layout are handled separately. Runtime integration remains pending; neither
villager is described as playable or selectable.

The actual donor draw relocations confirm identity, and source/native comparison
verifies 323 cat vertices, 346 cub vertices, and all 26 joints in each skeleton.
GameCube matrix-transport flag differences are accounted for explicitly. Bob's
shared-art conversion matches all 5,152 non-shirt bytes of the native object.
Generated artwork stays local and ignored.

## Exact artifacts

Directory: `build/v3-villager-art-02/`.

| File | Bytes | SHA-256 |
| --- | --- | --- |
| `punchy.n64tex.bin` | 5,664 | `10c250b0b3e8b57af617bb389024631ca538886e1118a4793712ae075450ae91` |
| `cheri.n64tex.bin` | 5,664 | `17cc0a1986a8e9861c57c6199ede6ff17b7946a457e3f51f0a63f6997d520676` |
| `art.json` | — | `f8e2dc2b5e82e0f8b89ca8f55d65f8ea39760fd9bc57e5d5e00483df37348687` |

Construction:

```sh
python3 tools/v3_villager_art.py --output build/v3-villager-art-02
```

The builder rejects existing output directories. Use a fresh directory for a
new construction; retain the recorded artifacts.

## Verification

`python3 -m unittest tests.test_v3_villager_art -v`: **nine tests pass**, including
actual reconstruction of both generated files and shared native-art/model
checks. Synthetic cases cover palette and alpha rules, odd-row texture ordering,
all expression slots, every body piece, missing frames, overlaps/bounds, actual
REL pointer handling, unknown matrix flags, and symbol identity.

The six inventory tests also pass during this batch. No emulator run, screenshot
review, original-hardware test, or save operation occurs. These are conversion
and source/binary checks, not proof of in-game appearance or persistence.

## Runtime findings and next action

`build/v3-npc-loader-audit-01/code.asm` records the original NPC overlay
disassembly from the pinned Docker toolchain. The draw-copy/index functions and
native/GC structure differences are recorded in the artwork specification.

Next, implement the extended draw/asset lookup without disturbing special NPCs,
resolve the wider donor voice IDs, and connect the normal villager's remaining
name/default/house/selection paths. The furniture pilot and browser composition
remain required work. The stable V2 cartridge, local/public patchers, user saves,
and trailer are unchanged.
