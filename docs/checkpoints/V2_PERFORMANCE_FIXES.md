# V2-08 museum recipient and credits correction

## Handoff

- ROM: `build/v2-performance-fix-08/Animal Forest English V2.z64`
- SHA-256: `08aa1c4418848138803059a68de667f473f9da490d7c0866ee501c58b8d0896b`
- Original-ROM UPS: `build/v2-performance-fix-08/Animal Forest English V2.ups`
- UPS SHA-256: `fb1e4b2b189a85255edc12db1d52d270a9f9862c84f6cd9bbed0138b9083aa7c`
- Build receipt: `build/v2-performance-fix-08/build.json`
- Receipt SHA-256: `2b6add4d82dee11f7ba14d81ed09580b684240cae56172034554a1f6f844d683`

The build retains V2-07 and every existing save. V2-07 ↔ V2-08 save
compatibility is expected without migration: no saved format, delivery logic,
or gameplay allocation changes. No new cross-version save/reload playthrough is
claimed. Expansion Pak, 128-KiB FlashRAM, and RTC requirements remain unchanged.

## Report and implementation

The user sees Japanese for the faraway museum in the mailing recipient list.
K.K. selects K.K. Dirge without a requested song; audio plays completely while
the picture sometimes freezes for long periods. This is not an audio-stop or
song-request report.

The address helper now resolves canonical museum identities to `Museum`,
preserving complete villager lookup, player/unknown fallback, and saved names.
Its file grows from 8,336 to 8,368 bytes, both within the same 8,384-byte native
rounded allocation. Only its existing owner metadata and relocation are updated.

The credits overflow the real 0x3800-byte font-command arena by drawing every
invisible padded space in their 25-byte rows. The native scheduler rejects frames
when this arena overflows; music runs independently. A 56-byte leaf adapter in
verified unused actor space removes only trailing-space drawing. Leading and
internal spaces, visible text, positions, row spacing, scales, fades, page order,
song choice, audio, actor size, and actor relocation stay unchanged. See the
[implementation specification](../../specs/V2_PERFORMANCE_FIXES.md).

## Verification

Five focused checks pass: four current-cartridge ownership, text, allocation,
rejection, and UPS checks plus the address/prompt/default helper suite under
address and undefined-behaviour sanitizers. The pinned Docker toolchain compiles
both production changes. Unrelated resources match the preserved V2-07.

The silent isolated native run at `build/v2-performance-native-03/` passes
100 function calls and 79 assertions. Its `results.json` SHA-256 is
`d500f75aeef17c63271a5e082f717cd96c66b915c44de5e36a145169084a2665`.

- Both complete executable owners load from the current cartridge through the
  native overlay loader and match independently relocated expected instructions.
- Museum, Limberg, player, and unknown identities display correctly without
  modifying their saved 18-byte identity records.
- The untrimmed nine-row draw reproduces native arena exhaustion: **2,054
  commands**, against the real **1,792-command** capacity. That overflowing
  diagnostic list is never submitted to the GPU.
- All **16 pages** and **10 extra fade points** fit after correction. Peak use is
  **1,295 commands**, leaving **3,968 bytes** after reserving the final branch.
- Every retained glyph on the reproduced long page has identical vertex data;
  all pages retain their full loaded rows and expected colours/fades.
- Executable data, memory guards, and the saved payload pass their checks.
  Diagnostic RAM and globals are restored, the checkpoint is reloaded, and the
  game resumes with no module error before graceful shutdown.

The first native attempt requested an unnecessarily large 192-KiB test heap
allocation and returned zero before fixture writes. The justified retry uses
16 KiB of ordinary heap for executable owners and the existing upper diagnostic
RAM for graphics. A seed-state shortcut was rejected before emulation because
the interrupted first run had not created blank save files; the completed retry
boots the same current cartridge with isolated blank saves. No old build runs.

The build receipt records compilation-time validation as pending; this separate
native record supplies the completed result without rewriting that receipt.
This tests the concrete overflow and fix, not a complete naturally selected
K.K. performance. Original-hardware confirmation of the reported freezes and
museum appearance remains pending; no listening test uses physical outputs.

## Browser patch

`build/web-portal-03/site` and the reviewed `web/release/` recipe target this
exact ROM. Recipe reconstruction from both supplied games passes. The compressed
recipe SHA-256 is
`5d78bca089e2589e5647074662374b2096f10960cf934e27ecc916dbc43b0081`;
its size is 1,889,726 bytes. Five Pages packaging checks pass. The local service
serves this export at `http://127.0.0.1:8073/`; the previous export is preserved.
The real-browser check at `build/web-portal-check-08/` produces this exact ROM
from CISO, sparse ISO, and a Pages-style project subpath. Cancellation, invalid
inputs, stale-download removal, and three viewport widths also pass, with no
browser errors or game-file uploads. All eleven JavaScript engine checks pass.
No trailer, ROM, or save is uploaded as a website asset.
