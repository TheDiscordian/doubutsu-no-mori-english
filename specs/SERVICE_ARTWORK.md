# Mailbox and repayment artwork

Port the supplied Mail heading and complete Cash:, Payment:, You still owe, and
Bells images. Keep native input, item ownership, financial arithmetic, numeric
fields, saved data, and loaded file sizes unchanged.

## Mailbox

Asset `00A7C000`, 20,784 bytes, SHA-256
`675e45d3a2b53151fecf8316e48bb39d099c15994cc4c71485002108a345eaa6`.
Replace the 64×16 I4 heading at offset `35B0` with GC `.data:004ABCC0`, bound
by texture command `004AD8D8` in `pos_win_post_model`. The full source image
says Mail. Its native load at `0960`, quad at `03D0`, display colour, position,
and scale stay unchanged. The native asset binding is in overlay `00789B60`
at offset `0984`.

## Repayment

Asset `00ACC000`, 17,040 bytes, SHA-256
`d04e4d7008026baea0793c7d9b97511eda3e95a71474dacdaeb5e66f51cc9c2f`.
The native owner at `0079B120` binds its asset start/end at offset `0DD8`.

| Label | GC image / actual texture command | Dimensions | Native destination | Native load |
| --- | --- | --- | --- | --- |
| Cash: | `004D8C00` / `004DB578` | 64×16 | `1288` | `08E0` |
| Payment: | `004D8A00` / `004DB590` | 64×16 | `2A08` | `0890` |
| You still owe | `004D7F00` / `004DB5A8` | 96×16 | `1588` | `07E0` |
| Bells | `004D8E00` / `004DB550` | 32×16 | `2088` | `0830` |

All donors are complete I4 images from `fkm_win_moji_model`. Untile without
resizing, truncating, or redrawing the images. The native Cash/Payment textures
share `1288..1887` (1,536 bytes); remaining and a 16×16 border tile share
`2A08..2C07` (512 bytes). Repack those existing regions as follows:

- Cash occupies `1288..1487` (512 bytes).
- The unchanged 128-byte border tile moves from `2B88` to `1488`; its sole
  native texture command at `0A80` changes only the pointer word. Clear the
  following unused 128 bytes.
- You still owe occupies `1588..1887` (768 bytes).
- Payment occupies `2A08..2C07` (512 bytes).

Each label's sole native texture reader is bound, including all references to
the moved border tile; its geometry and other load commands remain unchanged.
Four independent compiled 56-byte clamp loads retain the original command space
and palette 15. No texture exceeds 768 bytes of the 4-KiB TMEM limit.

Cash/Payment/remaining quads retain their native right edge -12, native Y/Z,
colours, flags, winding, and 0.75 display scale. Widths become 48/48/72 units,
with full source U coordinates. The three Bells quads remain unchanged. Retain
the numerical field positions and heading/control layout; do not import GC
controller pictures or modify repayment/save logic. Full resource and patch
checks do not establish ordinary screen or original-hardware acceptance.
