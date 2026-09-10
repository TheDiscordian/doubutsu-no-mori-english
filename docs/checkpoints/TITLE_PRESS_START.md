# English Press Start preview

## Scope and artifacts

`tools/title_press_start.py` creates a separate title preview from the exact
`build/classic-letters-pilot` candidate. The v0 ROM, playtest ZIP, text resources,
save formats, and current text-accounting candidate remain unchanged. The large
Japanese logo is still present; this is the first installed title-art component,
not the finished title screen.

The preview is `build/title-press-start-preview/animal-forest-title-preview.z64`,
SHA-256 `f8257e4d9a0625d51965c551541a3a560267f92ff758437b5c74542767a949db`.
Its adjacent UPS SHA-256 is
`441ae2bbac9dae8aa61d7ee37a096acc415b9b96f376f8916108670c0bc1fc63`.
The report is `preview.json`, deliberately not a new combined `build.json`.
Artifacts and extracted textures remain local and ignored.

## Changes

The complete source-bound GameCube Press Start tiles replace native title-bank
offsets `1110` and `1510`. The third native tile at `1910` becomes transparent,
so no Japanese remainder is drawn. The native actor's literal coordinates place
the visible English tiles at X 96/160, Y 159, matching the supplied reference.
The unused transparent tile is at X 224, Y 159.

Only VROM `0095FEC0` and `01136000` change. Actor executable instructions,
relocations, animation/state transitions, colours/opacity, the 23,760-byte title
allocation, the resident module, and every other cartridge resource are retained.
The constructor's signed low immediate resolves its native asset range to
`01136000..0113BCD0`. The builder validates that exact bank size and the original
three-tile position table before changing anything. The cartridge remains 32 MiB.

## Verification

Three focused cartridge tests pass: exact two-resource changes and transparent
third tile, unchanged executable code/other data, malformed inputs, rejected
missing inherited replacements, complete cartridge retention, and UPS
reconstruction. The title extractor has its own five passing source/texture tests.
Two additional host checks pass for the read-only live-memory observer, including
rejection of wrong actor lists, relocated data, and texture contents.

`build/title-start-native-01` passes nine recorded steps in a fresh, silent,
isolated four-MiB emulator. A read-only observation verifies the complete
relocated title overlay at `802CF020`, title actor at `802D1710`, and complete
23,760-byte loaded asset bank at `802D1A50`. START enters the English opening
message `09C7` with its complete 583-byte script. End guards remain intact,
shutdown is graceful, and FlashRAM/Pak remain blank. No image, code, or gameplay
state is uploaded through the debugger.

This proves actual loading and START progression, not visual/hardware approval.
The main logo's geometry, animation, N64 drawing, and memory ownership remain the
next title work. Do not repeat this standalone check unless those dependencies
change; use a combined title check for the completed logo.
