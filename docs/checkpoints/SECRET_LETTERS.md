# Villager secret-letter integration checkpoint

## Implemented scope

All fifteen secret letters, `0022..0030`, retain the complete supplied English
headers, bodies, footers, manual breaks, and glyphs. Thirty fixed snapshots
cover both capitalization states. The ordinary-conversation overlay preserves
all earlier date, birthday, and wider-word patches, static compact metadata,
original random selection, and paper selection. No text is shortened.

The 19,392-byte image fits the quest manager's existing `8800`-hexadecimal-byte
conversation allocation. The original BSS addresses are zero-initialized through
the enlarged file DMA. The addition requires no resident, saved-layout,
conversation-allocation, or per-letter-allocation growth. The
[specification](../../specs/SECRET_LETTERS.md) records ownership and relocation.

## Artifacts

- Full ROM: `build/secret-letters-pilot/animal-forest-halfwidth.z64`, SHA-256
  `86ba113d88ef0f6f978018290275a8afbbb5227a40b12469f29eefb8d6889af3`.
- UPS: `build/secret-letters-pilot/animal-forest-halfwidth.ups`, SHA-256
  `c6727a6918abd8022a2754b7ecaa9a4a1a6387b2d7a6a327c588e48e6a3e9fac`.
- Overlay: `build/secret-actor/overlay.bin`, 19,392 bytes, SHA-256
  `cbaea96323349378d4155823b41d7faf61e4fddc32e110a44ce2bafe97d9deb4`.
- Relocation: `build/secret-actor/relocation.bin`, 2,192 bytes, SHA-256
  `cafc6c298d54915be15feef31c6661d20cff68e4d3f9817f454991e784ded12e`.
- Compiled creator: 464 aligned bytes at original linked `80921F40`, zero
  stack bytes, SHA-256
  `4595cc9ec74b14bd755a57d95a56b30711f6ef9d80d99fbdd0d0551655228c82`.

The resident module and all earlier text resources/actors match the complete
shop-notice build. Only the ordinary overlay, its relocation, the quest-manager
metadata, and the DMA directory differ. ROMs, extracted assets, binaries, and
patches remain ignored local artifacts.

## Verified checks

Thirteen source/creator/installer/accounting/scenario tests pass in
`build/secret-focused-tests.log`. All thirty host creations preserve every
unowned metadata byte and guard; invalid inputs, overlaps, table aliases, and
retry pass. The four creator tests also pass AddressSanitizer and
UndefinedBehaviorSanitizer in `build/secret-sanitizer-tests.log`.

Independent builds in `build/secret-actor` and `build/secret-actor-repro` agree
on both binaries and the complete manifest. Independent native wrapper
assembly passes in `build/secret-assembly`. Full-ROM tests verify the UPS
round trip, every unrelated DMA payload, retained native prefix, original DMA
row ownership, and rejection of rehashed code/table/prefix/relocation mutations.
The combined counter adds only the 45 installed parts without changing its
denominator or removing any prior translation credit.

All 56 date, birthday, resident-word, NPC-show relocation, reader, and counter
regressions pass against the current runtime in
`build/secret-current-regression-tests.log`.

The silent native batch `build/smoke-secret-01` passes the actual quest-manager
loader at two allocation bases, all thirty original metadata/RNG comparisons,
sixty complete readbacks through compact and native-converted full records,
and three wrapper rejections. All 194 calls and 439 assertions pass, with
memory guards, unchanged save data, restored globals, retained heap accounting,
checkpoint restoration, blank FlashRAM/Pak files, and graceful shutdown.
No creator code is uploaded by the debugger; only the original comparison
overlay is copied. Two frozen-evidence tests pass in
`build/secret-evidence-tests.log`, binding the recorded scope and limits.
Normal conversation selection and the actual letter-show window remain separate
acceptance checks; injected loader/creator calls do not establish gameplay.

Evidence SHA-256 values:

- Results: `fd7ed4656db4f65e7f98d35a770a62c3512354b35372d26334fa016610968ffc`.
- Scenario: `28228eb9ef8e9f1abdb4bc5aac546365970caac0d7757abf0c6e04b3e02545b0`.
- Native helper: `21b021123986f9bc3de9b654f861b3d0e9a465508ece0153a05a6bef879eed02`.
- Restored checkpoint: `d70f44f34e1965f75503a75bb78ec2391715028aae11727730e390017306127e`.

## Reproduction and next work

Build with `python3 tools/build_secret_actor.py`. Use the complete
[shop-notice recipe](SHOP_NOTICE_LETTERS.md), retaining every flag, and add
`--english-secret-letters build/secret-actor`, with output
`build/secret-letters-pilot`. Prepare the silent batch using
`python3 tools/secret_scenario.py --output build/secret-scenario.json
--boot-output build/secret-silent-boot.json`.

The regression suites accept `AF_TEST_RUNTIME_MODULE=build/shop-notice-runtime`
to test current compiled code without overwriting earlier checkpoint artifacts.
Run date, birthday, resident-word, NPC-show relocation, reader, and combined
counter regressions against that build.

Check the ordinary show-window path and fallback with this exact cartridge.
Do not repeat the completed bulk letter cases or owner-loader batch.
Continue other untranslated text, including noticeboard consumers and remaining
name identities. Normal interaction, save/reload, review, original hardware,
title replacement, the GameCube-style keyboard, and patch-only release remain
in the full project queue.
