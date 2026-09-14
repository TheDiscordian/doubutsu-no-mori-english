# V3 furniture feng shui

## Scope and properties

The optional furniture adapter connects the native feng shui evaluator to the
haz-mat barrel and oil drum. It retains N64 room sizes, money/item-luck weights,
facing penalties, final item-luck clamp, and rounding. It adds no GameCube rooms,
basement, or separate island rules. The [HRA adapter](V3_HRA.md) remains intact.

The actual donor's haz-mat barrel metadata is `02 00`: red, with no facing
penalty. Oil drum is `03 00`: orange, also without a facing penalty. Thus red
benefits the east side, and orange benefits the north side, using native room
position/footprint calculations. Both rotations retain their actual IDs.

Donor and native money-power tables agree. Donor item-luck weights are four
times the native values; the converter verifies this relationship and leaves
the original N64 weights unchanged. Red contributes 2 raw item-luck points;
orange contributes 2 money and 1 raw item-luck point. Native whole-room
item-luck totals are capped at 40, then halved and rounded upward.

## Verified sources

The original owner at VROM `00827DE0` contains 3,616 bytes, SHA-256
`783bfaf1bf8fa58872ae2c3f9f55e686482f5434c2f42c49e3562de9ee284c47`.
The 80-byte relocation at `00828C00` is SHA-256
`326ba552f9fb152e9c0e174c5ed0f03d9b5f4adf40941e340209f05ee90f06dd`,
with sections `(1600, 1920, 96, 0, 12)`. Linked RAM begins at `80930960`.

The pinned donor REL has two local `mMkRm_ftr_info` symbols. This adapter selects
the feng shui table at section-five offset `4EBF0`, with 2,532 bytes and SHA-256
`5700370581b13dd85eb1102656f858c9c4dbb4752c646c3ad563893937a2517a`.
The other symbol belongs to HRA and has a different record format.

The expanded 1,267-row two-byte table preserves all 947 original records and
places selected imports at stable runtime indices 1,161 and 1,198. Unselected
rows and the original one-past marker have neutral metadata. Only selected,
valid imported profiles pass the room scan's extended range check.

## Implementation and memory

The checked range window at `80930D90..80930DA0` preserves both original bounds,
their delay semantics, and the move into the X-coordinate argument. The index
window at `80930990..80930998` uses the shared room query to retain rotation and
produce the correct runtime index. It retains the existing footprint reader,
which supplies the pilots' verified 1×1 cells. The original table-pointer pair
at `80930998` / `809309A0` points at the appended metadata.

Generated detours reuse the full-register-preserving resident query and return
through the actual loaded owner pointer at `80107010`. No new resident helper
or saved field is allocated. Original native instructions outside the declared
windows/table-pointer pair remain intact, including all scoring arithmetic.

The expanded owner occupies 6,400 bytes, adding 2,784 bytes on demand. Its
relocation remains 80 bytes. It moves to `03F50000` / `03F54000` without changing
DMA indices or consuming a directory slot. The scheduler's allocation-end and
ROM-load operands are updated; its entry selection, allocator, free helper,
and failure behaviour remain unchanged. V3 ABI 20 retains the same 48-KiB
permanent prefix. HRA's separately loaded image does not change.

Exact input hashes, symbol definitions, donor/native rule correspondence,
table/code bounds, relocation ownership, scheduler words, and independent
relocation at three addresses are checked. The import-free path remains exact
V2. The [checkpoint](../docs/checkpoints/V3_FENG_SHUI.md) records executed checks
and ordinary gameplay/hardware limits. Both web patchers remain V2 pending the
user's testing and explicit approval.
