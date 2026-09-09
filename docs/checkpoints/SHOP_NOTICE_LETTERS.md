# Shop notice integration checkpoint

## Implemented scope

All nine spotlight/reopening templates, `0012..0017` and `001B..001D`, retain
the 27 complete supplied parts. Four bodies capture the complete sixteen-byte
item field seven; five have no fields. Native shop/type selectors, recipient
identity, sender, type, paper, and publication modes are retained. Reopening
prepares one complete letter before any home publication or notification clear.
The original no-eligible-home policy still clears the notification after
successful preparation. A failed preparation leaves the notification pending.

The spotlight owner retains old mailboxes and the saved leaflet on resource
failure. Eventual delivery/retry is not proved: the original selection caller
does not consume a delivery result. This remains explicit scheduling/recovery
work, not an invented persistent retry mechanism.

## Memory and artifacts

The creator uses 33,008 image bytes and 480 relocation bytes, requesting 38,847
temporary bytes including its unchanged 5,344-byte work area and alignment.
The C loader, Python validator, and all creator linkers agree on a 65,536-byte
image maximum. Maximum allocation is 74,991 bytes and remains bounded by the
existing four-MiB heap. The resident reservation, saved layout, and ABI do not
change. The resident retains 24,576 linked bytes, with identical exports and
bootstrap. Its only instruction change at offset `3408` is `34038000` to
`3C030001`, the larger size comparison.

- ROM: `build/shop-notice-letters-pilot/animal-forest-halfwidth.z64`, SHA-256
  `5c304588db91dbe8267a6aae4f5f3fd2ad48ecf89fb31d30ee44837d5e1ba61d`.
- UPS: `build/shop-notice-letters-pilot/animal-forest-halfwidth.ups`, SHA-256
  `b710660b9cee773b9478a4395b2ac2776e96a86bb5a5ef56951b4eacfabddb9f`.
- Resident: `build/shop-notice-runtime/module.bin`, SHA-256
  `493bc25a922bbd9d321759677134520bbb179413985f0e047df45e6e432664c6`.
- Creator: `build/shop-notice-creator/overlay.bin`, SHA-256
  `d0ad9769499070deddf6f60082691b3a19361224e5dde63777e59ddc979268cb`.
- Relocation: `build/shop-notice-creator/relocation.bin`, SHA-256
  `172b4537062d565ea9ed3ddd3666855db24680a1e5e28d2858ad8ea50f935109`.
- Owners: `build/shop-notice-owners/owners.bin`, SHA-256
  `d9c4cfe6a2796439e8a81c92bc25909fdb62d4f1bdaee4ef7b9db919a7d27a51`.

The owners occupy 384 and 360 code bytes inside the original 472-byte and
504-byte functions. Their stacks use 304 and 288 bytes. The intervening
448-byte native selection caller and both template tables are unchanged.
The creator's native stack frame is 72 bytes; the resident loader uses 112.

Fortune, renewal, sale/Redd, and Snowman components are recompiled against the
new module rather than having their source approvals relabelled. The completed
ROM differs from the Snowman build only in the two owner functions, the one
resident size instruction and creator configuration, the enlarged creator, and
DMA metadata. Every earlier text resource and actor remains unchanged.
Historical build/evidence artifacts retain their original source approvals;
tests requiring current source cannot validate those older artifacts directly.

## Verification

- `build/shop-notice-creator-tests.log`: all 37 creator tests pass, including
  the entire preceding dispatcher chain, complete words/fields/capitalization,
  both recipient modes, malformed descriptors, overlap, every catalogue-read
  failure, item failure, and corrected-resource retry.
- `build/shop-notice-loader-tests.log`: all eight loader tests pass, including
  above-32-KiB images and all sixteen alignments at the maximum image/relocation
  size and exact four-MiB heap end. One byte beyond the heap limit is rejected.
- `build/shop-notice-sanitizer-tests.log`: all 45 creator/loader tests pass with
  AddressSanitizer and UndefinedBehaviorSanitizer.
- `build/shop-notice-install-tests.log`: all six installer/artifact/accounting
  tests pass. They verify full UPS reconstruction, installed source/image
  approvals, two-function-only edits, native tables, unchanged earlier resources,
  the one resident instruction difference, the real above-32-KiB creator, and
  complete-letter credit without changing the denominator.
- `build/shop-notice-regression-tests.log`: all 24 scenario, reader, record,
  relocation, and combined-accounting tests pass.

The silent native run is `build/smoke-shop-notice-01`, with log
`build/smoke-shop-notice-01.log`. Its scenario contains 32 spotlight cases,
eight reopening cases with four home deliveries each, 64 full readbacks, and
seventeen owner-fault cases. It uses a fresh ROM-specific checkpoint, no
screenshots, no audio, and isolated saves. The test uploads only the 1,424-byte
original code for comparison; translated code/resources load from the cartridge.
Completion and restored save/global/heap/stack/checkpoint evidence remain to
be collected. Direct native calls are not normal scheduling or hardware proof.

## Rebuild

Use `build/shop-notice-runtime/module.json` as the explicit module for the
creator and all rebuilt actor/probe tools. The complete creator options are
`--mother-letters --departed-letters --villager-events --academy-letters
--academy-scores --post-office --museum --shop-notices --mail-glyphs`.
Build both owners with `tools/build_shop_notice_owners.py --module
build/shop-notice-runtime/module.json --output build/shop-notice-owners`.

The full ROM command is:

```sh
python3 tools/build.py \
  --rom 'local/rom/Doubutsu no Mori (Japan).z64' \
  --translations build/interior-items-candidates/translations.json \
  --english-keyboard --english-runtime --runtime-module build/shop-notice-runtime \
  --english-fortunes --english-resetti-replies --english-shop-units \
  --english-resident-words --english-shared-npc-words --english-credits \
  --english-dialogue-dates --extended-items build/interior-items-resource \
  --display-names build/display-names --catchphrases build/catchphrases \
  --mail-catalog build/mail-glyph-resources --english-mail-layout \
  --english-mail-snapshots --english-mail-grading build/mail-grading-npc \
  --npc-mail-generation build/shop-notice-creator --extended-font build/mail-font-cartridge \
  --english-fortune-slips build/shop-notice-fortune --english-leaflet-dates build/leaflet-dates \
  --english-renewal-letters build/shop-notice-renewal --english-event-letters build/shop-notice-event \
  --english-mother-letters --english-departed-letters --english-villager-event-letters \
  --english-academy-letters --english-academy-scores --english-post-office-letters \
  --english-museum-letters --english-shop-notices build/shop-notice-owners \
  --english-snowman-letters build/shop-notice-snowman --output build/shop-notice-letters-pilot
```

Prepare the silent batch with `tools/shop_notice_scenario.py --output
build/shop-notice-scenario.json --boot-output build/shop-notice-boot.json`.
Never reuse an older-ROM checkpoint. Keep future unresolved tests grouped for
the later bug pass while continuing bulk text, name callers, remaining notices,
review, save/travel compatibility, patch-only release, and stretch goals.
