# Household artwork and igloo-material findings

## Household images

Direct inspection of 28 previously unreviewed images finds no readable Japanese
wording. All 28 already match the supplied English GC artwork in complete visible
RGBA colours, not only palette indices. Their complete native owners remain
unchanged in current RC8. Preserve them; copying the donor adds no English text.

| Native textures | Visible content |
| --- | --- |
| `01430468` | Christmas-tree ornaments, foliage, and base |
| `01432708`, `01432908`, `01432A08`, `01432D88`, `01432F88` | Fan grille, housing, vents, base buttons, and pole detail |
| `0143B708`, `0143B908`, `0143BA08`, `0143BD88`, `0143BF88` | Second fan's corresponding surfaces |
| `0145AFD0`, `0145AE30`, `0145AEB0`, `0145AC30`, `0145AA30`, `0145A830` | Wardrobe mirror, woodwork, and decorative dolls |
| `014CDAF8`, `014CD9F8`, `014CDBF8`, `014CDC78`, `014CDD78`, `014CDF78`, `014CE078`, `014CE178` | Alarm-clock hands, case, bells, and dial markers |
| `0151E898`, `0151E598`, `0151EA18` | Blue chest panels and tabletop |

The already reviewed book `0151EB18` is excluded. The tabletop `0151EA18` is
CI8 16×16 with a 256-entry palette at `0151E578`; the other 27 images use CI4.
The GC tabletop is `int_sum_blue_chest02_top_tex`, `.data:009ABE60`, read by
`int_sum_blue_chest02_on_model` at `009AC340`, with palette `009AB9C0`.
All texture/palette/reader bindings are recorded per image in the receipt.

## Igloo detail

The unresolved `0138DA28` detail is a native CI4 16×16 image, not a verified
Japanese label. Its actual material reads palette `0138BC08` at `0138BA60`
and the texture at `0138BA90`, with the sixteen-entry TLUT and 16×16 tile bounds.
At `0138BAC8`, the drawer loads twenty vertices from `0138ACC8`; the following
twelve triangles apply the same image to the top and side faces of two small
rectangular blocks. Y is 1400–1520 in model coordinates; the upper faces sample
the brown-on-cream patterned region and the sides use the lower texture strip.

Direct inspection shows a browned food-surface pattern without reliably readable
wording. The geometry is consistent with small grilled rice cakes; that food
identification is an interpretation, not an extracted native asset name. Preserve
the texture. The material-role investigation is complete; do not invent a
Japanese transcription or replace a native food object to make it more Western.

The proposed GC `rom_kamakura_nabe1` source is not an interchangeable donor.
Its actual reader is CI4 **8×32**, not 16×16, and the correctly decoded image
is a grey pot surface. The 128-byte allocation alone is misleading. Its texture
is `.data:0087C180`, palette `0087A1E0`, and reader `0087E7F0` inside
`rom_kamakura_model`. Its referenced vertices begin at `rom_kamakura_v[162]`
and differ from the native block geometry. The separate GC `rom_kamakura_etc`
atlas at `0087C200` is CI4 64×64, also not a direct 16×16 donor. Neither is
installed. The earlier guessed 16×16 GC pot view remains excluded from evidence.

Native igloo owner SHA-256:
`88e62405640b83d1efe04ff1cfba983ad0a5735a8adf3ea0a8e97f77140b4cf0`.
Its complete contents remain native in RC8. Selected material SHA-256:
`d2f3c1b48e42fa4150b00214340ade1fd864be91f30447fe1129f855f65e590b`.
Twenty-vertex SHA-256:
`9a02364f846dec2e296143c45d977d1243be3afa921cbac9ea99648595fda886`.

## Recorded evidence

- Current RC8 ROM SHA-256: `2a04f6e5c54dc2d5ed03009395af815b464bebdef51d67d899554deb54b3bcb4`.
- Receipt: `build/household-artwork-review-01/inspection.json`.
- Receipt SHA-256: `5181179f6ca47cc4abf18d81cc06174ef01785267c1e82e5261c199204062416`.
- Review script SHA-256: `bf3273769b018d499fe061f9c7e8c636537022bcba3939997644089c99888622`.
- Decoder SHA-256: `6d82a9b78a397540ffc9b3083804e0727e01c6b3b43e278cab9dc57ac9eef5b7`.
- Existing inventory SHA-256: `424fb279c90e7ac27a30ecbdf6c578b58cdfaeb3cd8549148a2d866816ad276f`.
- Contact sheet SHA-256: `9140b2e5c69ee18cd260c5c3702b34d912a746a3cb4988f1dff4f823f11b659f`.

The receipt includes original-ROM, REL, and symbol-map identities, native-owner
hashes, exact palette/texture/material ranges, GC reader bindings, RGBA hashes,
and all individual PNG hashes. The contact sheet is only a viewing aid for the
28 native household PNGs; it does not edit those assets or supply runtime proof.

The correctly decoded GC pot views are in `build/igloo-material-review-01/`:
`gc-pot-8x32.png` SHA-256
`0c518a909886dcf03f4e5b0481a6e1b084e0a87a14705dc58800d18a14f82abe`,
and `gc-other-pot-detail.png` SHA-256
`83400d512449b2d9f0686140fe156cc60c358124b89d7713afb4ba6a580387af`.
GC model source `src/data/model/rom_kamakura.c` SHA-256 is
`2020cbeb6b5af0ff58f6ad57b4edfb7bd3dc7b1ccd939158c1f9e8992e6b8ca0`.

## Decoder verification and limits

Three new synthetic `test_texture_preview_ci8.py` checks pass in 0.001 seconds:
all native palette indices/alpha, independently tiled GC rows with distinct
colours and transparent RGB5A3, and invalid texture/palette sizes. The actual
CI8 tabletop decode and full native/GC visible-colour comparison also pass.

No ROM, patch, game artwork, gameplay code, or save changes. No old candidate,
emulator, full suite, compiler, percentage tool, or gameplay scenario is run.
RC8 remains the current handoff. This closes this selected household set and
the igloo material-role lead, not every dynamic material or game image. Other
unreviewed content and the existing public-distribution requirements remain.
