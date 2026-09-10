# Police and post-office interior artwork

Install the matching English GameCube wanted poster, recruitment poster, and
postal mailbag texture. Preserve native room geometry, UV coordinates, lighting,
palettes, commands, allocations, room selection, gameplay, and saved layouts.
The postal bag is not the lucky bag; lucky-bag Japanese decoration stays intact.

| Room owner | Native texture / palette | GC texture / palette | CI4 size | English |
| --- | --- | --- | --- | --- |
| `012AC000` | `3968 / 2A68` | `93A9E0 / 939AE0` | 48×32 | WANTED! |
| `012AC000` | `3C68 / 2A68` | `93ACE0 / 939AE0` | 32×48 | I want U! |
| `012BB000` | `5BD8 / 2B18` | `612CE0 / 610760` | 48×48 | MAIL |

Native offsets are owner-relative; GC offsets are in the verified REL `.data`
section. Require the exact source ROM, REL, symbol map, predecessor ROM/report,
and two complete original room hashes. Untile CI4 donor pixels into the existing
native slots without resizing. Every used palette index must have identical
visible colour and alpha; invisible RGB may differ. The mailbag donor does not
use native palette index 9, whose GC counterpart differs. No palette edit is
needed, including at that unused index.

Bind the seven actual donor palette/texture/vertex relocations. The two GC
posters share one eight-vertex load: the recruitment poster draws vertices 0–3,
then the wanted poster uses 4–7 without loading new vertices. Native commands
load each four-vertex quad separately. Check the matching triangles after
normalising those indices. The mailbag retains ten native vertices and six
matching triangles. UV and lighting bytes must match exactly. Positions follow
GC's roughly four-fifths room scale with small quantisation; permit at most
sixteen GC coordinate units from the scaled native position, retaining every
native coordinate unchanged.

Build after the seven Nookington interior signs and before the unchanged English
title. Reconstruct and verify the whole cartridge and UPS, retaining all other
resources and their identities and sizes. Focused checks cover donor pixels,
source rejection, installed ownership/readers, text credit, unchanged room
bytes, and the title combination. This data-only batch does not require a new
native test harness; ordinary room appearance remains human playtest work.

## Text inventory

The wanted headline is `このかおみたら110!`; the recruitment headline is
`ケーカン求ム!`. Count these distinct bitmap originals once, including their
printed digits and punctuation, under the existing non-whitespace source rule.
Tiny lower poster marks are retained by the English donor and receive no
invented transcription. The mailbag's `〒` is a Japanese postal symbol, replaced
by `MAIL`: explicitly recognise U+3012 in the bitmap transcription counter and
count one source character. This is not permission to count arbitrary symbols
or Latin-only images as Japanese text. All three credits require complete
installed room verification. Earlier builds retain the same 19-character
source denominator with no new credit.

GC-only post-office card-reader artwork has no matching native feature in this
batch. Do not replace neutral native wood or counter textures with that device.
