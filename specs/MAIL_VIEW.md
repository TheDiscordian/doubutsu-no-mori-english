# English mail reading layout

## Scope

`--english-mail-layout` installs experimental read-only body/footer hooks in the
native board overlay. This is part of the full English reader work, not a full
snapshot viewer. Current hooks still consume the native 96-byte body and
sixteen-byte footer. Full snapshot decoding before normalization, longer text,
and pagination are provided separately by the opt-in
[full snapshot reader](MAIL_READER.md).
Generation, complete discriminator/reader validation, and editor integration
remain required. No source text or newline is rewritten by these layout hooks.

The approved font and advance metrics remain unchanged. Layout measures those
actual rendered advances, rather than treating each Latin character as a
twelve-pixel Japanese cell.

## Reference and native contracts

The supplied GameCube executable's `mBD_strLineCheck` retains explicit `CD`
newlines, admits a character when the accumulated width is at most 192 pixels,
and leaves an overflowing character for the next line. There is no word-based
rewrapping or whitespace trimming. The body has six lines, sixteen pixels apart.
The footer's right edge is the starting x position plus 192, with the complete
rendered footer width subtracted. Verified English function hashes are:

| Function | Bytes | SHA-256 |
| --- | --- | --- |
| `mBD_strLineCheck` | 188 | `a669f2d29e6e130a98a1b7a638fa5b675331ff0039f5dc9d03e3df0ccd54070f` |
| `mBD_set_writing_body` | 752 | `46fb6340c13090fc23c422abaf9f2df9fe4591a2d809dc0efa921d1b2c680cf2` |
| `mBD_set_writing_footer` | 288 | `2238abc9e2c2672e84beef7e1ac32b7532a5d5945396b0f893ecf7b669bc1cd3` |
| `mFont_GetCodeWidth` | 52 | `5b601d0bb6d7c257c1caa7f391daef85e449e4a945781dd3e6fd557db52d5448` |

The native viewer uses the same six-line/sixteen-pixel vertical geometry and
192-pixel paper width, but stops after sixteen body bytes per line and computes
footer position as `(16-length)*12`. The read-only hooks replace those fixed-cell
assumptions. Actual advances come from native `mFont_GetCodeWidth` at `8009028C`,
including the already installed halfwidth metrics. Glyph rendering uses
`80090E98`, with the original colour, alpha, scales, flags, and polygon mode.
Native and GameCube glyph metrics are not claimed identical.

## Hook and relocation safety

Only two JAL instructions change in board VROM `007908A0`:

| Call | Original target | Resident shim | Return-to-original difference |
| --- | --- | --- | --- |
| `8088A0A0` | `80889A9C` body | `af_mail_body_hook` | `060C` |
| `8088A0D4` | `808899E4` footer | `af_mail_footer_hook` | `06F8` |

All delay slots and original functions remain unchanged. Each shim selects the
new renderer only when `menu.data0` is one, the native read-open mode. The body
receives its menu directly. The footer obtains the board menu at submenu overlay
offset `103E8`, with `data0` at `10420`. This is an open-mode check, not a
procedure-state check: opening/closing animation states remain read-only too.
Other modes tail-call the original function, deriving its actual loaded address
from the caller's return address and the guarded difference. No saved registers,
stack arguments, or return address are changed by the shims.

The two old `R_MIPS_26` records, `44001210` and `44001244`, must be removed from
relocation VROM `00792610`; retaining them would incorrectly relocate resident
targets. The native relocation resource is 240 bytes, with 52 records and SHA-256
`cb3f980f865ca0b9fad1c82c88280ce83080a9ff8ae1c38075990cf492589b68`.
The patched resource keeps the section sizes, all fifty other records in order,
total file length, and trailing size word. Vacated padding becomes zero.
Installation requires verified original overlay/relocation hashes, exact call
words, a source-matched resident module, and no overlapping viewer patches.

## Validation requirements

Host tests cover measured line boundaries, narrow characters, unchanged explicit
newlines and spaces, full-width glyphs, malformed inputs, complete draw spans,
footer right alignment, and unchanged board bytes. The N64 CPU scenario executes
the real font renderer, checks graphics allocations and every glyph quad, and
verifies non-read argument forwarding through unchanged compiled shims.

The separate real-window probe uses the guarded native open routine `800C4DD8`,
with program twelve, read mode one, and an ordinary synthetic letter in isolated
test RAM. The game loads and relocates its actual submenu and board overlays.
Live observations verify wait state two, the source pointer, full field lengths,
and both installed call words. Execution breakpoints verify the actual program
counter at each resident hook. The runner pauses at a verified game-frame entry
before installing those breakpoints, so a hook cannot fire before its continue
request and leave an extra stop response queued. All breakpoint replies and
complete register packets are checked; failed packets remain in the result log.
Separate A, B, and START closes preserve the complete source letter and
the player's 28-byte saved header/footer preferences. The machine checkpoint is
restored afterwards. This is an injected letter-open request, not ordinary
mail delivery or an inventory-selected letter.

Native editor behaviour, complete generated-letter reading, ordinary delivery,
game-save/reload, and hardware compatibility remain unvalidated. The option
remains experimental until those paths are exercised.
