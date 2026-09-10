# Shop interior signs

## Scope and source ownership

Replace seven sign textures in the Nookington ground-floor, raffle-day, and
upper-floor room resources. Use the supplied English GameCube artwork, retaining
the N64 room geometry, lighting, texture coordinates, commands, room selection,
shop hours, raffle rules, allocations, and saved layouts.

| Native owner | Native texture / palette | GC texture / palette | Size | Meaning |
| --- | --- | --- | --- | --- |
| `013CD000` | `4158 / 2638` | `9546A0 / 952B80` | 32×64 | Second floor |
| `013CD000` | `4558 / 2678` | `954AA0 / 952BA0` | 32×16 | Information |
| `013CD000` | `4658 / 2698` | `954BA0 / 952BC0` | 48×64 | Welcome, hours, clearance sale |
| `013D4000` | `4130 / 2690` | `95AAA0 / 958FE0` | 32×64 | Thank you |
| `013D4000` | `4530 / 26B0` | `95AEA0 / 959000` | 32×16 | Information |
| `013D4000` | `4630 / 26D0` | `95AFA0 / 959020` | 48×64 | Raffle-ticket day, big chance |
| `013DC000` | `3330 / 1F70` | `960D80 / 95F9C0` | 32×64 | Thank you |

Native texture/palette numbers are owner-relative; GC numbers are `.data`
offsets in the verified REL.
All textures are CI4. Decode GC tiling, pack native linear nibbles, and require
identical visible colours. No texture scaling or new lettering is required.

Bind each texture, palette, and vertex command through the actual REL relocation
stream and exact symbol map. Verify the native material pointer, load dimensions,
four sign vertices, and matching donor UV/lighting bytes. GC room positions use
a roughly four-fifths scale and slightly quantised coordinates; retain every
native vertex. The comparison permits at most sixteen GC coordinate units from
the corresponding scaled native position, not changes to either model.

## Palette exception

The ground-floor welcome board uses GC palette colour 9, RGB `(156,115,165)`,
where the native palette has `(189,115,115)`. Replace only this opaque colour at
native VROM `013CF6AA`. Its other native user is the board-edge texture at
`013D1C58`, which uses only indices `0,10,11,12,13`; verify that its visible pixels
remain unchanged. Preserve every other palette byte, including invisible RGB.
Other six replacements use the existing palettes without changes.

## Installation and verification

Build after the complete shared-stall layer and before the English title.
Require the exact predecessor ROM/report binding, three complete original room
hashes, no overlapping edits, unchanged resource lengths, and every unrelated
resource retained. Use the existing artwork-chain reconstruction and UPS checks.
Combine the unchanged title afterwards. No new runtime or emulator harness is
needed for this data-only batch; ordinary room appearance remains playtest work.

The installed-text counter verifies all three complete modified room resources.
Count confidently transcribed Japanese portions of the welcome, clearance,
raffle, and thank-you signs under distinct original texture IDs. The existing
`2F` label is not Japanese and receives no Japanese-source weight. The two small
information notices have uncertain original wording and remain an explicit
transcription gap, even after their complete English images are installed.
Do not invent character counts for their tiny marks.
