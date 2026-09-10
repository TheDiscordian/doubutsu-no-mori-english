# Nookington's doorway and clearance banner

Complete the small Nookington details without replacing its native building or
the already installed main English sign. Native T2 is a 128×32 CI4 atlas at
slice offset `BD8`, in summer/winter slices `659A0`/`67F80` of object `D5E000`.
The current structure loader streams the appended copies at `95480`/`98100`
of object `03D00000`. Patch both retained originals, the expanded prefix, and
both actual streamed copies; a change only to the old object is not installed.

## Doorway

The native doorway word is Latin "TANUKI", not an additional Japanese source
record. Port the small GameCube Nookington wordmark from the winter T2 donor
at `.data:58C7C0`, palette `58C7A0`, without changing the door or its surrounding
texture. The complete source wordmark occupies U 29–37 and V 3–28. All visible
donor colours in this rectangle match both native seasonal palettes at
`D5BA08`/`D5BA28`. The donor's transparent palette entry has no visible colour.
Do not copy the entire atlas: other palette entries and geometry differ.

The GC door models at `58C5D8`/`58EBD8` load their corresponding T2 textures.
Their vertex fixups resolve to `58BA40`/`58E040`; the door uses U 0–1536 and
mirrored V 0 to −1024. Native door vertices at slice offset zero use U 0–1536,
V 0–1024, and native mirrored sampling. Retain native positions, UVs, normals,
door animation, display lists, and palette selection.

## Clearance banner

The native poster quad at `690`–`6CF` uses U 2304–4096 and V 0–1024. U runs
vertically with the wall's Y coordinate, so the atlas itself is not an upright
view. The native blue column reads `クリアランス` ("clearance"), beside a red
"30% OFF" column. The English GC T2 texture has floor tiles and a leaf doormat
in this region, consumed by different geometry. It is not a wall-banner donor.

Retain the original red offer and the blue banner, translating the complete
word as "CLEARANCE". Compose the nine letters from the exact installed Latin
glyphs, without another resize or a font-atlas change. The word fits in 54×12
pixels after removing only empty glyph rows/columns and adding one empty column
between letters. Rotate its placement into the existing blue rectangle: native
U 73–126, V 17–29. The upright banner reads from top to bottom, with the word
turned clockwise, as on a narrow English sale banner. Preserve all surrounding
pixels, transparency, the red offer, and the native palette. Map glyph intensity
to the existing blue, pale blue, and white entries only.

## Verification and accounting

Bind the original ROM, supplied REL and symbol map, exact installed font,
source slices, both GC texture and vertex fixups, and native display-list/UV
readers. Verify every pixel outside the two declared rectangles is unchanged,
both active seasonal streams contain the new textures, and all 92 building
ranges remain within their original slots. Preserve every other resource and
reconstruct the UPS. Inspect upright texture projections in both seasons;
ordinary scene appearance remains a human playtest check, not a new emulator
matrix for unchanged graphics commands.

Each original seasonal Japanese banner contributes its six source characters
to the shared counter. The retained copies do not create more source IDs, and
the Latin doorway and numeric/Latin red column contribute no Japanese weight.
Credit requires both installed seasonal textures and their current native
readers; earlier builds retain the Japanese source weight without that credit.
