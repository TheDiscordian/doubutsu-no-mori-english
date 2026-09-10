# English clock checkpoint

## Combined candidate

`build/time-setting-01/animal-forest-halfwidth.z64` adds the complete English
native clock display to all map/inventory/shop artwork and hardware fixes.
ROM SHA-256:
`54a6d643d27cd36345e2298407f47f5bb51ddf2c6f947558391da968cbf717be`.
UPS SHA-256:
`3e890387716ae784a5784ecfed1c210db57f63b45f991c27720c9f2a7ec6bbb8`.
Cartridge size remains 32 MiB, RAM use remains four MiB, and saved fields and
the separate corrected-v0 handoff remain unchanged.

## Implementation and checks

The [clock adapter](../../specs/TIME_SETTING_ENGLISH.md) repacks the four
native records into "Adjust the clock.", "OK", and numeric date/time separators.
Eleven display instruction immediates and five value positions change. The
native year-first order and existing two-digit numeric formatter remain intact.
All time arithmetic, selection logic, colours, font calls, allocation, asset
bounds, save interaction, and the entire relocation file remain unchanged.

Five focused checks pass in 7.300 seconds: independent Docker MIPS assembly,
complete words and glyphs, all two-digit widths, exact field alignment, bounded
reads, only scoped display changes at two heap placements including BSS,
all four relocated text addresses, complete resource retention, UPS recovery,
and rejection of wrong sources/metadata. Sixteen counter regressions pass.
The added predecessor-binding check passes its focused rerun. The complete
combined counter runs successfully on this actual ROM; its four clock records
have 23 source characters and verified English credit. Older builds receive the
same source inventory without unearned credit. Ordinary clock adjustment,
screen appearance/navigation, RTC writes, and hardware acceptance remain
unverified. No new native test harness or user-save mutation is performed.

The counter's older letter checks reconstruct the entire original v0 cartridge.
`tools/post_v0_progress.py` binds reviewed post-v0 ROM/report pairs before those
unchanged base checks, while current installed-route checks still use the current
ROM. Unknown builds and modified reports reject; register another combined
candidate only after its retained-resource checks pass. This is compatibility
for strict verification, not extra text credit for artwork or the conversation
fix. [Source boundaries](SCREEN_ARTWORK.md) retain the native disassembly and
texture bindings; the GameCube month/weekday redesign is not imported.

## Next: collection headings

Both headings are in native inventory asset owner `00A30000`. The insects
heading is I4 `00A31D28`, 128x32, loaded at `00A31508`, with its quad at
`00A30980`. The fish heading is I4 `00A3E438`, 160x32, loaded at `00A3D818`,
with its quad at `00A3CC40`. The small textures at `00A31728` and `00A3DA38`
are butterfly/fish tab icons, not Japanese words; retain them.
The English references are Insects `.data:004362C0`, 80x16 I4,
model `00438590`, vertices `00437C80`; Fish `.data:00441080`, 64x16 I4,
model `00443AF0`, vertices `004431C0`. These fit the original larger texture
slots. Adapt their texture loads and heading quads without changing the native
page layout or collection state; preserve every source pixel.
