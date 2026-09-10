# V1RC1 keyboard correction

Combined follow-up: `build/v1rc1-keyboard-fix-01/animal-forest-title-preview.z64`.
SHA-256: `7a265fca118e522591085d0f7ce3a926b46d78a86c67e6f07443c64befe005bb`.
UPS: `6c334b39eeb92801196e3b7712e2ccf8663daa1d14bb92f8aed5ee7bdd393e43`.
It retains the hiring-notice and three text/HUD corrections. V1RC1 and the
user's saves remain unchanged. The [specification](../../specs/KEYBOARD_RC1_FIX.md)
records the exact corner, font, controller, and ownership changes.

The lower-right UV direction is corrected, and the right pair receives the
scaled GC vertical offset. Both lower control hints are centred inside visible
frame alpha. All supported key glyphs use actual ink for horizontal centring;
low punctuation stays inside its key without changing the global font. One
symbol page retains all 24 distinct supported codes and existing input limits.
Accepted sound code and all forty native key positions remain unchanged.

The recovered prefix matches both recorded historical hashes. The replacement
suffix grows the rounded owner by 5,952 bytes, within the existing 8,192-byte
reservation. No additional pool allocation or saved-format change is needed.

Six focused tests pass in 14.234 seconds, including independent compilation to
the same complete ROM/UPS, both runtime relocation addresses, full resource
retention, actual glyph bounds, hint alpha, rejection guards, and sanitizer-
checked page controls. Five existing keyboard controller/keycap/editor checks
also pass in 1.486 seconds.

Native attempt `build/v1rc1-keyboard-native-01` stops before emulation because
Xvfb is not on PATH. The single corrected retry explicitly uses the existing
`/home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb` binary.
`build/v1rc1-keyboard-native-02` passes: five native calls, thirty assertions,
all four corrected frame rectangles, forty unchanged key rectangles, 157 glyph
draws, 14,392 command bytes, and 10,048 back-buffer bytes. Both cartridge-loaded
owners, matrix callback, save data, graphics bounds, and memory/stack guards
pass. The fixture is released, the checkpoint restored, and the emulator exits
normally. Audio is disabled; no screenshot or user-facing preview is opened.

This is complete controlled native drawing evidence, not ordinary keyboard
appearance or original-hardware acceptance. Keep those distinctions in the
combined V1RC2 handoff. V2 remains explicitly deferred until V1 completion.
