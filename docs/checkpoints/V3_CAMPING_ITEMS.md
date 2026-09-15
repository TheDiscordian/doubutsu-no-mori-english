# Seven camping items: complete assets and experimental integration

## Completed batch

ABI 68 installs the complete kayak, backpack, lantern, cooler, mountain bike,
sleeping bag, and propane stove without replacing any original object. English
names, donor prices, complete one/two-cell profiles, catalogue ordering/framing,
non-orderable reward rules, HRA/feng-shui metadata, and selected profile bits are
installed. The [specification](../../specs/V3_CAMPING_ITEMS.md) records exact
source identities, model/material exceptions, memory ranges, and acquisition.

All 524 vertices, 362 triangles, 20,864 CI4 texels, and 112 palette entries are
retained in 24,224 native object bytes. The kayak keeps both opaque model slots;
the backpack keeps its tint and mirrored/clamped materials; the bike keeps its
mirrored saddle; the lantern keeps the original furniture's unlit/off model.
No callbacks or sleep behaviour are invented for the seven static profiles.

Donor camping category 37 maps only in HRA metadata to the verified equivalent
412-point native weight. The actual donor and native base-point consumers,
counter bounds, complete scoring owners, and other field bits are checked.
The actual Tent acquisition route is retained as unfinished work; no ordinary
stock list is changed. All seven remain not for sale in the catalogue.

The package retains its 184,336-byte RAM allocation. Seven empty canonical
profile/item slots become active; all existing rows, save-code bodies, shared
readers, and callback items are retained. There are 32 static and 33 item rows.
The import resource occupies 2,414,528 bytes, leaving 1,714,240 bytes free.
The full DMA directory keeps its 3,389 entries and sole terminator.

Catalogue code/data is 3,408 bytes within a 3,664-byte suffix reservation. Its
469 furniture entries and 248 clothing entries need 280,256 bytes of the
existing 280,704-byte menu allocation. The bike keeps donor scale `0.85` and Y
`-3.0`; native construction and other fields remain unchanged. Resident memory,
ordinary heaps, menu reservation, and dedicated model banks do not grow.

## Artifacts

All generated ROMs, game-derived objects, patches, and emulator saves are ignored.
Original inputs, existing saves, V2, both web patchers, and the trailer are unchanged.

- Full ROM: `build/v3-camping-runtime-01/animal-forest-v3-asset-loader.z64`.
- ROM SHA-256: `3967dedabca6e65a97f57273028aaa19b0b24ed72b405f2498d5a4fce6a1cd29`.
- UPS SHA-256: `76095d1e7a312bd59abafe0042d980a47291f9d6e40c9414395b2c1c3a205378`.
- Build report SHA-256: `7267629efe169d8f12a0a7cd58df65a28051d27eaab8d77f9d7322f22f26ac5a`.
- Resident package SHA-256: `899626842dd33806777bd15753d47e04ec4337e315dd176e074d04f30ffc150e`.
- Complete art report: `build/v3-camping-art-01/art.json`, SHA-256
  `5ac42594d8bb7605fff8b62b2bf8e1a251c9001eb3fd828904266a222ea7daa5`.
- Metadata: `build/v3-camping-items-01/items.bin`, 224 bytes, SHA-256
  `e9d79e365b85e8f7b77cb8f4831366fb56ba529b8f0d34eac347fddf09b78d7e`.
- Metadata report SHA-256: `abb53c160726fe6ee1f6febc882a7d76f8a83037e903054d99a34ef0b2ef4c8e`.

The offline composer has 56 experimental choices: 20 villagers, 33 furniture
items, and three shirts. The kayak/bike/blue-aloha subset has no automatic
dependencies and is generated at `build/v3-optional-camping-01/`:

- Subset ROM SHA-256: `55655e629a9b26fbdad804e632569dce69491de0881e51c9da3444dd4cf0d271`.
- UPS SHA-256: `807f72b94add48d6332bf6dd7433bc4098bdd5cd461f23f04b4ee235b9082c15`.
- Build report SHA-256: `e6e4db17a21460202187007114537d4b0d23824fc05a4a9d40cd24fe50926a53`.
- Selection receipt SHA-256: `183c12ea670966d53a81de8a0b8282f6b9ba182a9917cab366fbe9567d0f1d7a`.

Both full and subset builders reconstruct their UPS outputs. The ROM remains
64 MiB and requires an Expansion Pak, RTC, and 128-KiB FlashRAM.

## Executed verification

Twenty-nine focused checks pass:

- Seven camping asset/metadata checks and five shared parser/profile checks,
  7.443 seconds. Actual complete texels, palette colours, vertices, triangles,
  material commands, native load bounds, two-cell bindings, true reward lists,
  prices, and safe scoring equivalence are checked. Unknown parser states fail.
- Five current-cartridge/sanitized-C checks and twelve current-composer checks,
  10.848 seconds. Checks cover all new objects and sparse records, existing
  code/resources, exact scoring-only changes, unchanged stock, directory and
  physical bounds, CRCs, menu capacity, selection permutations, selected-only
  catalogue/HRA records, and exact all/empty outputs. The actual C save codec
  accepts equal/superset profiles and rejects missing camping dependencies
  without modifying the supplied save, profile, or failure output.

The first cartridge fixture incorrectly expected camping entries to be the
last seven catalogue rows. Donor ordering places an existing import after them.
The corrected assertion filters the seven exact indices while retaining their
verified donor order. No game data or code is changed for that fixture correction.

The first native run passes at `build/v3-camping-native-01/results.json`:

- Result SHA-256: `a2ce9c0378e77862171bc8f900e7cefe25fde109fa5100f8b6bad14fd51df92f`.
- 73 result records, 28 actual native calls, 37 passed memory assertions,
  and no failed assertions.
- Cold boot loads the current ABI, package, all seven full profile/item rows,
  and their derived active profile pointers. Package/table guards are intact.
- Native public dispatches return all seven full English names, correct prices,
  furniture types, and one/two-cell sizes, including rotated identities. Names
  retain guards on both sides of the output buffer.
- No CPU fault occurs. The test-stack guard is intact; the complete emulated
  checkpoint is restored, followed by a final no-fault/package-guard check.
  Shutdown is graceful. Physical audio is disabled; no ordinary save is performed.

No retry or new native fixture framework is needed. The existing isolated
runner and native dispatch mechanism are reused. The previous bank-lifetime
fixture and old candidates are not replayed. The subset is checked on the host;
no subset native execution, new model rendering, native catalogue presentation,
ordinary reward acquisition, or cross-build reload is claimed here.

## Remaining work and compatibility

Summer-camper acquisition needs the actual NPC/event/scene/quest adapter.
The complete donor Tent list also contains campfire `335C`, bonfire `3360`, and
tent `336C`; those callback/animated objects require their own conversion.
Continue them and the remaining donor families, then ordinary combined
placement, interaction, acquisition, and persistence checks. Mailbox reward
delivery, villagers, complete offline/browser composition, and e/e+ investigation
remain in the full goal. This batch does not complete or reduce that goal.

Format 2 and its codec are unchanged, but the full selection adds seven profile
bits. Missing-profile rejection is verified; ordinary cross-build loading is
not. Preserve backups and do not load imported saves in V2.

This is not a public release or a completed playtest handoff. GitHub development
source is allowed. Neither patcher may switch to V3 until the user tests and
explicitly approves the switch.
