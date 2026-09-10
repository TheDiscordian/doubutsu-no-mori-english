# English birthday window

The birthday window displays the complete supplied GC prompt, "When's your
birthday?", full English month names, a two-digit day, and OK. A bounded native
drawing replacement keeps the original background, scrolling, selection colours,
date validation/input, and saved month/day fields. The obsolete Japanese suffix
images hold the read-only strings; their drawing commands become no-ops.
See [the birthday specification](../../specs/BIRTHDAY_SCREEN.md).

## Verification

One host/sanitizer check passes in 0.166 seconds, covering 42 layouts, complete
text and coordinates, all six background commands, bounds, and read-only state.
Three integration checks pass in 8.559 seconds: independent MIPS compilation,
exact function/asset ownership, relocation at three ordinary-heap addresses,
complete cartridge retention, patch reconstruction, and installed-text credit.
Sixteen counter unit checks pass; the complete counter successfully reads this
cartridge and includes both discovered embedded strings in the shared inventory.

The single silent native batch in `build/birthday-native-01/results.json` passes
112 recorded steps, eight native calls, 42 assertions, and three complete draws:
September 30/month selected, February 29/day selected, and January 10/OK selected.
The native overlay loader installs the complete owner and relocations. Actual
font commands contain all 34, 33, and 32 expected glyphs in order, respectively,
including the prompt's question mark. Native number and matrix functions execute;
the unchanged 48-byte submenu font-matrix callback is copied into owned memory.
The complete live save, birthday state, menu state, assets, and all heap/stack/
module guards remain unchanged. Both fixture allocations are freed, the isolated
checkpoint is restored, and the emulator shuts down gracefully without audio.

This is a fixture-controlled native drawing check, not ordinary menu entry,
interactive date selection, or original-hardware acceptance. Those remain
playtest work. No repeated native title, conversation, or keyboard probes are
needed for their unchanged implementation.

The title combination check passes in 8.010 seconds, retaining all preceding
resources and the identical title/Expansion Pak warning implementation.

## Candidates

Untitled ROM: `build/birthday-screen-01/animal-forest-halfwidth.z64`.
ROM SHA-256:
`179c658a70383d278b2b78aa9f2d339c8582ae2cb714e7b95b120163c0104d5d`.
UPS SHA-256:
`2fbc0d5395c148d48e0a90ef7567beee9c0764bcdd8785e306326f37d7062356`.

Combined ROM: `build/title-birthday-combined-01/animal-forest-title-preview.z64`.
ROM SHA-256:
`4849a83ebcff09fa188cfbe4f54a66f2691769c98f4a1dc787b48417e07fc9f7`.
UPS SHA-256:
`0e4508ff472f0db095a397dfb4e2417a2366c5d14ae2c222c705f44352a90437`.
The combined 32-MiB cartridge requires an Expansion Pak and retains the ordinary
four-MiB heap, both Nook corrections, Shrine wording, all previous text/artwork,
and the corrected GameCube-style grid. Earlier ROMs and user saves are untouched.

Continue Controller Pak labels and remaining Japanese artwork. Public release
provenance and ordinary save/menu/hardware acceptance remain open.
