# Additional raw-texture review before V1RC1 feedback

The hardware follow-up interrupts unrelated artwork discovery. Preserve these
completed direct inspections rather than repeating them after the fix batch.
Thirty-nine new native images are decoded and inspected under
`build/artwork-inspection/`; no cartridge changes result from this review.

Seven `item-<VROM>.png` images at `0140C120`, `0140C440`, `0140CDA0`,
`0140D0C0`, `0140E060`, `0140E9C0`, and `0140F9F0` show fruit, axe, fossil,
roll, sapling, and umbrella imagery, without Japanese wording. Each uses a
32×32 CI4 image and its adjacent 32-byte palette immediately before it.
Every reviewed image/palette is compared with V1RC1 and remains native.
The shared owner `0140C000` is not wholly unchanged: its SOLD OUT image
`0140F6D0` is already translated. That completed replacement is excluded.

The following `interior-<VROM>.png` images are also inspected. Their complete
owners are verified unchanged between native and V1RC1 before decoding:

| Images | Finding |
| --- | --- |
| `01129678`, `01129878`, `01129978` | Wooden/sled surfaces; no wording |
| `0138D828`, `0138DAA8`, `0138DB28`, `0138D628` | Igloo cooking/stove surfaces; no wording |
| `0138DEA8`, `0138E178`, `0138E3F8` | Shaded/effect images; no wording |
| `0138DA28` | Small orange pattern; retain pending exact material-role confirmation, not counted as a closed text review |
| `013923A0`, `01391BA0`, `013913A0` | Grass, earth, and rock faces; no wording |
| `01395F38`, `01395538`, `01395D38`, `01395138` | Snow, rock, and earth faces; no wording |
| `01397658`, `01397C58`, `01397A58` | Grass, earth, and water-light pattern; no wording |
| `013A1488`, `013A0C88`, `013A0888`, `013AA488`, `013A9C88`, `013A9888` | Wooden windows, wall, and floor; no wording |
| `013A7388`, `013A7788`, `013A8388`, `013A8788` | Wood, plaster, and windows; no wording |
| `013F1678` | Clock-face/case/pendulum atlas; no Japanese wording |

CI4 palettes are selected from the preceding native material's `FD100000`
load; intensity images use no palette. Dimensions come from the existing
`artwork-matches-01.json`, not guessed image sizes. The guessed 16×16 GC
`gc-igloo-nabe1.png` view is not used as evidence: its actual reader is 8×32,
so that decoded file does not establish any native material correspondence.

Thirty-eight selected images need no translation; the small orange pattern
remains a scoped review lead. This is not whole-game coverage, scene acceptance,
or English application credit. Six older `hud-native-*.png` files are visually
blank bubble/background pieces, but lack a rechecked binding in this batch and
are not added to the closed native-image inventory.
