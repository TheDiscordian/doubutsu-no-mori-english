# V3 Pigleg and Dobie artwork components

## Converted outputs

`tools/v3_villager_art.py` supports explicit selected artwork conversion while
leaving the default Punchy/Cheri batch unchanged. Source disc, REL, symbols,
relocations, and original N64 hashes retain their existing verification.
`build/v3-islander-art-02/` contains four villagers' textures and Pigleg's
separate model: five files, 28,480 bytes total. These outputs stay ignored.

- Pigleg texture: 5,664 bytes, SHA-256
  `69f711c92f77e60b44011c957caa61bc8933f6054fd4c80adf3130752cd22e39`.
- Pigleg model: 7,360 bytes, SHA-256
  `f7f62939189e6e5801eef91212f5902e68aa79ef2511c7473f64d69eaba38ac6`.
- Dobie texture: 4,128 bytes, SHA-256
  `0adce0be6b4bf0b0cb79bd93ea0896ffd2064f761a149a91a30a86a6ac9f8e30`.

Pigleg is donor index 233 / voice 276; Dobie is donor index 224 / voice 274.
Both have no separate accessory in the verified donor records. Their body,
palette, and every actual facial frame are converted. Pig's 896-byte body and
128-byte atlas padding, plus wolf's absent mouth frames and 256-byte padding,
are handled explicitly instead of forcing the cat/cub format onto them.

The shared pig reference reproduces 5,152 non-shirt native bytes. The shared
wolf reference reproduces 3,616. Native body tile dimensions/offsets are read
from actual model commands. Both full padding ranges are zero in the original
objects. Dobie's 374 vertices and 26 joints match the retained native wolf rig.

## Pig geometry adaptation

`build/v3-pigleg-art-01.log` records the first conversion's strict geometry
rejection; no incomplete output is installed. Inspection finds 67 actual head
coordinate changes, not merely different matrix flags. The remaining 252
vertices retain positions, and all 319 retain UVs, normals/colours, alpha, and
ordering. The implemented conversion copies the native model and imports the
verified coordinate triples. Every byte after the vertex array stays native,
including display lists, skeletons, and segmented pointers. All 26 joints and
twelve visible-joint records match. The separate object preserves original
N64 pigs; no shared native model is overwritten.

`build/v3-pigleg-art-02/` records successful first construction. The combined
`build/v3-islander-art-01/` supplies all four textures plus that model.
The final `...-02/` construction adds explicit converted-model comparison
metadata and reports four villagers rather than counting the model as a fifth
villager. Asset contents remain identical.

## Verification and remaining work

`build/v3-islander-art-tests-01.log`: thirteen focused tests pass in 10.803
seconds. They exercise all four supported texture layouts, exact source-pointer
binding, complete source/output coverage, frame/padding bounds, source rejection,
both actual new conversions, full pilot-output retention, and the 67-coordinate
model edit with every unrelated byte preserved. The test uses reversed selection
order and still reproduces the recorded assets in canonical order. No historical
ROM or emulator is executed for this artwork-only change.

No new cartridge is built and no villager becomes playable in this batch.
Pigleg needs a fixed additive model-bank assignment; Dobie needs his shorter
texture and null-mouth draw record connected. Both need voices, full names/
catchphrases, defaults, houses, and explicit islander-to-town behaviour before
move-in and persistence verification. Actual runtime appearance of the converted
Pigleg model remains unverified. The other sixteen islanders still need their
species layouts and accessory handling; no accessory is silently removed.

The current ABI-50 pilot ROM, source saves, public/local V2 patchers, and trailer
remain untouched. V3 source is pushed only on `v3/optional-imports`; either
patcher switch requires user testing and explicit approval.
