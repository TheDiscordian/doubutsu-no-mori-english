# Complete catalogue item names

## Source and native contract

The native catalogue is VROM `007A28F0`, RAM `808A6100`, with 39,184 file bytes
and 12,576 BSS bytes. Its relocation file is `007AC200`. The source image SHA-256
is `8fad244f38141aa81de27fe539fabcc6c6d2e4ba4f60eb26fdaa6c5f601a6a6b`;
relocation SHA-256 is
`49ca34e8e0a5a5726f99cfd2e9f1537f0c4e12c73f90825b65428270509ce85a`.
The five native relocation header values are `14048, 25024, 112, 12576, 130`.
The shared submenu metadata row is at owner `7749C0` offset `2C90`.

Each of nine native category pages occupies 966 bytes: count/top/selection and
flags, 444 item IDs at offset eight, and seven ten-byte name fields at `380`.
The name fields exactly fill the end of each page. Widening either loader
without changing storage would overwrite the following category or tail state.

Native initialization `808A93A8` visits all nine pages and loads seven names per
page at `808A961C`, advancing the destination by ten bytes. Native page changes
reload seven names at `808A6C20` with the same stride. Drawing uses the matching
seven fields at `808A8A9C`, length ten, with eighteen-pixel row spacing and
`0.875` scale. Native item IDs, order, counts, prices, models, animations, and
selection remain authoritative. The supplied GameCube `mCL_change_item` and
`mCL_window_draw` use complete sixteen-byte fields with the same row scale and
spacing; the existing English full-name resource supplies the exact wording.

## Owned complete-name storage

Append a 63-slot cache to this overlay, one slot for each existing native name
field. Each slot records the native field pointer and a complete sixteen-byte
name. The native constructor calls initialization at `808A9798` on every entry,
including when the original catalogue state already exists. Redirect that call
through a cache reset before the unchanged native initialization.

Redirect both item-load calls through a wrapper which retains the native
ten-byte compatibility write and loads the complete English name into the owned
slot. Repeated page changes update the same keys; drawing performs no ROM DMA.
Only the catalogue item-name font call resolves its original field pointer to
the owned complete name and passes length sixteen. All other font arguments,
coordinates, colour, clipping flags, scale, and return value remain unchanged.
There is no global name-loader or font change.

No cache lookup reads beyond 63 slots. Rejected loads replace the entire owned
field with the explicit English error `Name unavailable`; an unknown pointer
uses that same complete error instead of stale data or a truncated legacy name.
Native construction supplies exactly 63 keys. Reset prevents old ownership from
surviving re-entry. The cache is transient overlay data, never part of a save.

## Integration and verification

Keep original BSS addresses zero-backed in the enlarged overlay. Preserve
native relocation order, including the existing constructor call relocation,
and add the three formerly external hook calls plus appended internal code/data
relocations. Fixed main-code imports must never move with the overlay.
Move the image and relocation together and update only the catalogue owner row.

The catalogue participates in the alternative submenu allocation sum, not the
editor/notice-dominated sum. Verify the actual inventory growth plus enlarged
catalogue sum against the already reserved pool; do not infer allocation safety
from the ROM size or Expansion Pak permission.

Focused checks cover all 63 distinct field destinations, page updates, reset,
resource rejection/recovery, missing keys, original field guards, draw argument
preservation, actual compiled relocations and source bounds, shared allocation,
and retention of earlier translation resources. Ordinary catalogue opening,
scrolling, selection/order, and appearance join the combined v0 safety pass.
No exhaustive catalogue/item native harness is required before other content.
