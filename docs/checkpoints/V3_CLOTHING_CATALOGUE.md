# V3 clothing catalogue checkpoint

## Artifact and implementation

`build/v3-clothing-catalogue-01/animal-forest-v3-asset-loader.z64`, ABI 44.

- ROM SHA-256: `1f53456846a8f7f6ed9cd327ffc06e0e2f8d0253466a2bcdcb8e62b2cd1dab00`.
- UPS SHA-256: `619ac20cdc0bc8fdfedbed911ddddef0c8defaa59e1e080db480a3409409672a`.
- Resident prefix SHA-256: `d373b6c92a5417a3bb28e4585fff18ac392c60934f3a7a9ea724517c9821ff5c`.
- Catalogue image, 56,560 bytes: `d680f0a606e9eeb22789c0da6e741399538d59cec762db5f42683c7bb29880c2`.
- Relocation, 720 bytes: `7cd0df508eea29cdbcd9b405f496892b0c73f2b2d21dab1b2c7ecb9691f920f2`.
- Suffix, 2,880 bytes: `91bed6abbf12a3a6f144b27c23c920f1411a4bcc33fc940a09f34fa42f336e65`.
- Clothing ordering, 492 bytes: `aadf08670a3d6ba0b9671b4c23a45b553041270e0c491e76ef9bd6f8dd713f85`.

The first build succeeds with the pinned Docker toolchain. The actual native
clothing page has 245 rows, not all 255 mannequin identities. Its original
entries/order are preserved and cherry shirt is appended as row 246. The actual
donor's 247-row table includes mannequin 682 once, at position 183; complete
source hashes and its relationship to donor pocket `24BF` are checked.

The [specification](../../specs/V3_CLOTHING_CATALOGUE.md) records catalogue
index `ABF`, display `3AFC`, room index `6BF`, canonical pocket `34BF`, native
ownership fallback, original-initializer bridge, clothing presentation, and
native ordinary-stock eligibility. The two furniture imports stay on their
separate page. The complete menu uses 274,176 of its existing 274,560 bytes;
384 bytes remain. No native allocator, save format/profile, or model bank grows.

## Focused checks

`build/v3-clothing-catalogue-tests-01.log`: both tests pass on their first run,
in 2.523 seconds.

- Sanitized C helpers cover native/imported ownership, wrong-player rejection,
  uncollected/disabled entries, all four aliases, exact three-field presentation
  changes, native garment retention, complete initializer invocation, imported
  profile selection, and native stock-query arguments/results.
- The current cartridge check covers the full 245+1 table, actual donor row,
  pointer/count changes, every declared original-prefix edit, linked suffix,
  parent descriptors, actual pool bound, complete retained main/resident/save
  code and profile, other resources, startup CRC/ABI, and UPS reconstruction.
- Construction independently checks relocation at three load addresses,
  source-function identity, incoming branch safety, all relocation ownership,
  native allocation instructions, and image bounds.

No historical cartridge is replayed. Construction-source hashes match the
current build receipt.

## Native current-cartridge check

`build/v3-clothing-catalogue-native-01` passes all 71 records on its first run.
The existing isolated catalogue fixture is reused with the current 864-byte
save runtime and complete model buffers. Only menu-entry movement is replaced
with a private return stub; list construction, full-name caching, native
selection, profile/model loading, and price functions execute normally.

Passing evidence includes:

- Complete actual native relocation of the expanded catalogue.
- Empty imported collection, followed by real native acquisition of an original
  garment, imported `34BF`, and a static furniture pilot. The clothing page has
  `17AC, 3AFC`, while the barrel remains on the furniture page.
- Full sixteen-byte English name `cherry shirt`, correct partial-completion
  flag, and native buffer-switching selection of the imported row.
- Catalogue index `0ABF`, actual profile `80466608`, native type/timer, price
  380, scale 1.0, viewing height 38, and model Y -4.
- All 4,128 bytes of actual shirt texture, palette, and native mannequin
  geometry match; the remaining preview buffer is untouched. Combined bank
  SHA-256: `f0263a207b8b2d54748dda15853fed70fa00982cf61fc024745ffc4f2d802268`.
- The shared inverse conversion returns pocket `34BF` for the catalogue item.
  This verifies ordering identity, not the complete order/payment procedure.
- All 246 rows and their completion flag, with every original garment retained.
  Removing either required selection bit leaves exactly the original 245 rows.
  Artificial current/working profiles remain consistent during these checks;
  the save guard is never disabled or deliberately tripped.
- Complete restored resident code/profile, all 864 runtime bytes, original
  private record, executable prefix, suffix/tables, memory guards, and a zero
  faulted-thread pointer. The allocation is freed, the checkpoint restored,
  execution resumes, and the emulator shuts down normally.

No physical audio, GPU appearance claim, ordinary shop control, payment,
delivered order, or game-save/restart test is involved. Existing ordinary room
placement/pickup and clothing save/reload evidence remains attached to its
tested build, not relabelled as fresh catalogue execution.

## Compatibility and next work

Complete save code, format 2, selected profile, and runtime state match ABI 43.
Same-profile compatibility is expected both ways, not newly proven by an
ordinary cross-build reload. Older profiles without the display dependency
reject new saves; V2 and format-1 builds remain incompatible. Preserve backups.

Complete rotation and placed-item save/reload, ordinary acquisition/catalogue
payment/delivery, and the remaining villager integration. Keep the full optional
import/profile/browser scope open. Both served patchers stay V2 until the user
tests V3 and explicitly approves switching them.
