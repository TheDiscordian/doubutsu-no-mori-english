# English shop-interior signs

## Implementation and artifacts

Source commit `76f49551ee106953ba1afb61566b599ccc5ad12c` installs seven complete
English GC textures in three native Nookington room resources. The
[specification](../../specs/SHOP_INTERIOR_ARTWORK.md) lists each native/donor
address, source bindings, palette exception, and counting limits.

The new ordinary-room board reads WELCOME with the original 9:00 AM / 10:00 PM
hours and Clearance Sale. The raffle variant uses RAFFLE-TICKET DAY / BIG CHANCE!
instead of the Japanese raffle board. Both thank-you signs, both information
notices, and the second-floor direction sign use their own exact donor images.
Native raffle-day room selection and shop hours are not changed.

Untitled complete build: `build/shop-interior-artwork-01`.

- ROM SHA-256: `8f26fe26c1f1bc57fc462bb427d0a122f2aba072b5e6cbbbddb58c38573ea5a2`.
- UPS SHA-256: `b376601ff2323ac658ffadb4209f3575742c09a41239afd2f9646d697f44a411`.
- Report comparison SHA-256: `f2dec6683a78f94046d4eb540eff05dc0374ab84ae9b5b13db1eeef2790a4dd1`.

Combined title build: `build/title-shop-interior-combined-01`.

- ROM SHA-256: `d7fbbffc85eb7c311f980c3945cf035de136b130d9fee6214ad096d60b8c8585`.
- UPS SHA-256: `4dca9b30625ea76350dcc3198835ad9d7b6d226cda77bc0828519fa630e5a31b`.
- Canonical title report SHA-256: `79b6ee72a933a52a72b918f9c6099ece453b04babe0a2e6d7e9ba81d6017b029`.

The combined ROM still requires an Expansion Pak. Prior ROMs, package `03`, and
the user's saves remain untouched. [Package `04`](V1_PLAYTEST_PACKAGE.md) supplies
the new private patch-only handoff.

The complete [27-stage public-image rebuild](V1_REBUILD.md) passes from clean
committed build sources and matches these ROM/UPS identities. Its actual title
report retains public compiler metadata; the comparison profile above matches.

## Focused verification

Four new asset/reconstruction/counter/rejection tests pass in 8.244 seconds;
the additional complete-title retention test passes in 1.818 seconds.

- Verify the actual REL fixups for all seven texture, palette, and vertex
  loads: 21 selected pointers, plus exact source and symbol-map identities.
- Compare every visible installed pixel and alpha value with the corresponding
  decoded English donor. Independently inspect the native/donor images and the
  installed welcome, raffle, thank-you, and information outputs.
- Preserve native geometry and require identical donor UV/lighting bytes on
  all seven four-vertex sign faces. GC model positions differ in scale; no
  native vertex or drawing command is replaced.
- Change only palette entry 9 at `013CF6AA`. The other material using its
  palette retains identical visible pixels; all other palette bytes remain.
- Reconstruct the UPS and compare every other resource, every object length,
  and every native room byte outside the seven textures and two palette bytes.
- Compare all 3,386 DMA identities between the previous and current title
  builds. Only `013CD000`, `013D4000`, `013DC000`, and rebuilt DMA table owner
  `00019D40` differ. The physical boot copy, title/grid/runtime, other artwork,
  Nook fixes, and saved-format code are unchanged.
- Reject altered textures, palette bytes, native reader pointers, vertex data,
  reports, source ROMs, donor data, and symbol maps instead of awarding credit.

The full installed-text counter passes on `build/shop-interior-artwork-01`:
752,074 / 752,096 inventoried source characters have applied English routes.
The four newly transcribed original image records add 53 characters to both
the inventory and applied total. The 22 retained structural-tail characters
identified in the [preceding counter record](STALL_ARTWORK.md) remain unchanged. This
approximation does not claim exhaustive artwork inventory or gameplay review.
Counter report `build/shop-interior-counter-01/latest.json` has SHA-256
`e1bdcf1ee4a4421891217215745b325038ce3a5a090b80fddcc70051f0e2102a`.

The second-floor source is already Latin/numeric. Two tiny information notices
have uncertain original wording and receive no invented Japanese character
weight, despite installation of their full English textures. Existing opening
hours receive no new Japanese translation credit. Distinct thank-you source
slots retain separate original IDs; extra cartridge copies do not.

No new native test harness, desktop preview, emulator launch, save mutation,
or audio playback is used for this data-only batch. Ordinary room appearance,
raffle-day gameplay, and original-hardware acceptance remain human playtest work.
