# Native reference text formatting

## Scope

The dialogue-only `reference_layout` policy retains the English GameCube's own
colour-span, line-offset, line-anchor, character-scale, and line-scale commands.
It includes the existing reference page-delivery and read-only-field rules.
It never rewrites line breaks, changes the font atlas, or enlarges saved fields.
Sound, actor requests, choices, branches, and message termination remain ordered.

The native font consumer, not just the message cursor, establishes compatibility:

| Code | Native consumer | Meaning and argument constraint |
| --- | --- | --- |
| `50` | `800914FC` | RGB and an unsigned character-count span; alpha becomes 255 |
| `52` | `80091900` | Unsigned byte minus 128, added to the sentence's base Y |
| `53` | `8009193C` | Line anchor 0, 1, or 2; offsets are 0, 8, or 16 pixels |
| `54` | `80091554` | One-character scale, unsigned byte divided by 32; zero is invalid |
| `5A` | `80091980` | Persistent line scale, unsigned byte divided by 32; zero is invalid |
| `67` | Resident `af_font_space` | English-only unsigned pixel advance multiplied by the character's current total X scale |

The corresponding GameCube consumers are in the pinned reference's
`src/game/m_font_main.c_inc`. Their arithmetic and reset behaviour agree with
these N64 routines. Code `51` changes message voice/sound state; it is not a
layout command and is never ignored by this policy.

English `67` requires the complete resident module. It has size 3 and sentence
attribute 4. The native sentence-control lookup at `800919D0` redirects to a
bounded resident lookup that preserves the original `52`, `53`, and `5A`
function pointers and adds `67`. The space consumer adds to sentence width at
`34`, using the current character total X scale at sentence offset `68`, exactly
as the GameCube does. It draws no glyph and changes no other sentence field.
The message cursor separately advances by all three bytes; a missing parameter
does not advance or read beyond the message. An incomplete renderer hook cannot
enable this command in the builder. Unsupported lookup values still return zero.

## Native state and dispatch

The N64 sentence structure embeds its 64-byte character at offset `48`.
Sentence source, index, Y offset, width, line scale, and inverse line scale are
at `00`, `2C`, `30`, `34`, `38`, and `3C`. The character's source, flags,
scale, inverse scale, total scale, anchor, RGBA, and span counter are at relative
`00`, `05`, `10`, `18`, `20`, `30`, `34`, and `38`.

`80091C98` obtains the token size and attribute, dispatches attribute 4 through
`800919D0` and attribute 5 through `800915A4`, then advances by the complete
token size. Formatting tokens do not render their parameter bytes as letters.
`800913D4` decrements a colour span after a drawn character and restores the
sentence colour at zero. It also restores one-character scaling to 1 and marks
the combined scale for recalculation. `80091470` combines character, sentence,
and line scales and clears that recalculation flag.

## Safety and review

Every translated entry rejects out-of-range line anchors and zero scales before
building. RGB, span counts, and signed-offset encodings cover their full byte
ranges. There is no arbitrary scale clamp or replacement of reference parameters.
Conservative width checks continue to flag explicit geometry for individual
review; acceptance is not a claim that every bubble fits.

The candidate manifest records the native and GameCube formatting tokens. Native
tests exercise the actual sentence dispatcher, parameter extremes, colour-span
restoration, scale reset/recalculation, token advancement, and adjacent guards.
These tests use scratch display lists in an isolated, muted emulator. They do
not modify or present the font atlas.
