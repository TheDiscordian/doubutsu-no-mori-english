# V3 separate imported-house markers

## Fixed identities and consumers

The imported actors `E0DA..E0ED` retain actual house IDs `50DA..50ED` and
receive separate temporary foreground markers `F200..F213`. Assignment follows
the fixed villager registry, never checkbox order. The original NPC markers
`F005..F0DE`, player-house base `F0DF`, and other building markers stay fixed.
These temporary markers are not additional selectable objects.

The marker conversion preserves `(house + A005) & FFFF` for every other
16-bit input. For imported houses it returns `F200 + house - 50DA`. The NPC
proximity predicate recognises the original NPC markers and the separate new
range; player houses are not reclassified as NPC houses.

| Native consumer | Instruction address | Resident entry |
| --- | --- | --- |
| House/player foreground comparison | `80A040EC` | `80461F80` |
| House foreground installation | `80A04834` | `80461FA4` |
| NPC nearby-house predicate | `80977134` | `80461FC8` |

Each caller already saves its return address. The assembly leaves use no stack,
memory, HI/LO, or floating-point state. They change only the original result
register and `at`; conversion returns `at = A005`, and the predicate returns its
Boolean through `at`. The NPC consumer retains its separate actual-house check.
Original relocation resources and all other owner instructions remain unchanged.

The donor's corresponding readers are `aHUS_check_player`, `aHUS_actor_init`,
and the house test in `actor/npc/ac_npc_move.c_inc`. Source comparison does not
replace checking the native instructions. The native forward-item reader uses
the actual foreground value without narrowing it to an original house index.

## Memory and cartridge layout

ABI 60 reserves 128 bytes at `80461F80..80461FFF`; the compiled leaves use 116.
The allocation is between the twenty town-mode bytes at `80461F60..80461F73`
and the drawing records at `80462000`. The native growth data at
`80461E80..80461F5F` is occupied and must not be used for code. Startup transfers
and invalidates the complete resident prefix, with its guard at `8046BFF0`.
No extra RAM allocation is introduced; an Expansion Pak remains required.

The complete patched house owner is appended at blob offset `131690`, with its
existing DMA identity repointed to the uncompressed physical alias. The original
compressed house data remains in the cartridge. Blob length is `132DD0`, and its
physical end is `02000B30`. Output grows to **64 MiB**; the extra tail is zero.
The builder checks the 64-MiB limit and virtual-resource boundaries, retains every
other physical resource, updates startup/ROM checksums, and verifies complete UPS
reconstruction from the supplied original ROM.

## Compatibility and remaining integration

ABI 60 retains ABI 59's selected profile and saved format. This is not evidence
of ordinary cross-build save/restart compatibility. Test only copied saves, keep
backups, and do not load imported saves in V2 or older builds missing dependencies.
Native Punchy-house entry and interior loading restore the actual outdoor house
ID when the exterior actor unloads. His complete scene-arena allocation, ordinary
English conversation, and exit have passing evidence; returning outside
reconstructs the real house and separate marker. Other rooms and ordinary save
restoration remain separate gameplay checks.

The [checkpoint](../docs/checkpoints/V3_HOUSE_MARKERS.md) distinguishes the compiled
checks from the actual native observations. Neither web patcher receives V3
without the user's testing and subsequent explicit approval.
