# Complete map and opening-guide names

## Installed state

`build/guide-name-pilot` includes the complete fifteen-position map villager-name
cache and opening-guide coloured dialogue name, alongside every preceding
translation layer. The [map specification](../../specs/MAP_NAMES.md) and
[guide specification](../../specs/GUIDE_NAME.md) record exact call sites, packed
records, stack boundaries, relocation, and allocation ownership.

Map names occupy separate display storage; player names, empty-house records,
sex/house fields, block sorting, colours, geometry, and original saved identities
retain their native layout. Both resident-name draw branches use the cache.
The map image grows by 768 aligned bytes inside the existing submenu pool;
no additional permanent reservation is required. Invalid animal identities and
failed resource loads retain the native fallback without stale English text.

The opening-guide actor appends a 112-byte private adapter and uses the existing
eight-byte-safe temporary. Dialogue field five retains colour one. Numeric
fields three/four, messages, timing, saved identity, and the caller's stack frame
remain unchanged. The adapter's own frame is 32 bytes.

The actual cartridge configuration remains four MiB. Neither change modifies
the resident module, font, letter resources, default catchphrases, or text-bank
edits. Ordinary interaction and save/restart remain part of combined v0 smoke,
not claimed results of host or cartridge checks.

## Reproduction and artifacts

```sh
python3 tools/build_map_overlay.py
bash tools/build_map_names_pilot.sh
bash tools/build_guide_name_pilot.sh
python3 -m unittest discover -s tests -p test_map_names.py -v
python3 -m unittest discover -s tests -p test_guide_name.py -v
```

Current combined `build/guide-name-pilot`:

- ROM: 33,554,432 bytes; SHA-256
  `3064813dfc4da20d04a299d48e2d8b48b7aafb97a530ba7c85e1cb4476936e97`.
- UPS: 5,117,648 bytes; SHA-256
  `53ea039528859af35bd5fc6ee31303fffc7b8d8ca72f825d28665481ff95f62c`.
- Guide actor: 9,264 bytes; SHA-256
  `39ee32d3bf1e30ed043ac0edad1071061cefd95c85e75239010d552811bf5bc5`.
- Guide relocation: SHA-256
  `427ffa0b689c60233e52ad3701a73d8138ce4ef2ff25c2b58604fd945d764a36`.

Retained map-only `build/map-names-pilot`:

- ROM: 33,554,432 bytes; SHA-256
  `102efdee826a5f433d29e9c466abc910c9ad2b09aa604e92a9867e3c686ce1eb`.
- UPS: 5,106,502 bytes; SHA-256
  `13129e4767275ae6f8510b76327cd5f10f70d346ce33c9acd1a95e9ec27bfece`.
- Map image: 26,544 bytes, including original BSS at its original offsets.
  Appended image SHA-256:
  `a5b2870aa29a5958be5b949b76ee772a490108a41c357dbb63a00a650fd8b15a`.
- Map relocation SHA-256:
  `70eb5d92ee6f7466f420df56adfc44b2c9a9c1e70286e5380349f19695bcbf8f`.
- Conservative map branch bound: 176,768 of 243,072 reserved submenu bytes.

## Bounded verification and limitations

Risk and stopping condition: check that full names cannot overwrite packed map
status bytes or the guide's saved pointer; preserve player-name lengths and
colours; validate frame/relocation/ownership; and reconstruct both complete
cartridges and UPS patches. No new emulator harness or per-record native matrix
is required for this batch. Ordinary map/guide interaction joins v0 smoke.

All six map checks pass. The four core/artifact checks take 0.337 seconds and
cover sanitizers, fifteen cache positions, player names, null/unsupported IDs,
staged load failure, reset/replacement, overflow fallback, exact draw arguments,
unchanged native fields, source guards, and two relocation bases. The two
cartridge/accounting checks pass in 96.708 seconds. Independent pinned-toolchain
builds in `build/map-names-overlay` and `build/map-names-rebuild` agree.

All six guide checks pass. The four assembly/frame/relocation/source-guard checks
take 3.855 seconds; the two complete-cartridge/accounting checks take 67.060
seconds. Independent assembly matches the installed adapter. Only two native
guide instructions and its allocation row change, and all map/prior resources
remain installed. Both builders reconstruct the UPS patches successfully.

Six existing catalogue tests and twelve combined-counter tests pass. Four of
five existing display-name tests pass. The remaining configuration test first
rejects the obsolete `build/runtime-module` source inventory. Its single
corrected retry uses the current `build/notice-seasonal-runtime`, whose complete
source inventory matches, then rejects the old `build/alias-items` fixture's
translation/provenance contract. The test now accepts `AF_TEST_RUNTIME_MODULE`
and defaults to the current module. The legacy item fixture is still unresolved;
no third attempt or fixture rebuild is made in this batch. This is a source-bound
fixture rejection, not an observed game crash, and it is not counted as a pass.
The current cartridge's `build/design-items-resource` remains covered by both
successful full builds and retained-resource checks. Refresh or select the
current item fixture during the later combined test-fixture pass.
The generalized catalogue/map build driver also reproduces the approved
catalogue image and relocation exactly in `build/catalogue-shared-builder-check`.

No screenshots, audio, real-save modifications, or fresh emulator gameplay tests
are performed. New map/guide execution is not inferred from earlier native
helper evidence. Original hardware and ordinary save/restart remain unverified.

## Next implementation

The fishing event's native name call `80A90270` writes through a six-byte
temporary into the saved record's player-name field, immediately before its
town name. Do not widen that writer. The actual dialogue reader is the field-zero
setter call at `80A9031C`, within `80A902CC..80A90334`. Preserve the numeric field
one preparation and real player winners.

Native event initialization marks NPC winners with both PersonalID numeric IDs
`FFFF` and the dummy town prefix `98 A6 8F A1 20`; the town clear fills the rest.
The chosen NPC or random-animal selection stays native. Resolve the displayed
name only from this proven NPC-record shape and an exact saved-name alias,
including loaded older saves; unknown keys and player identities retain native
text. Do not rely on a session-only cache or guess from an English prefix.

`npc_mail_names.prepare` supplies 394 exact aliases covering all 216 original
Japanese names and every complete six-byte English name. Its existing 6,368-byte
resource SHA-256 is
`a79b6bc3c5b36c7ce2bcea55932ccdf4ce694608e5dcfb896226a24d368bf5d6`.
A direct comparison confirms every one of the current cartridge's 216 native
six-byte NPC keys resolves to the correct identity. Reuse this mapping for the
fishing reader; the full stored name does not require changing the save layout.

Map embedded landmark/empty-house strings still need their own application:
the GC map source exposes exact Shop, Police/Station, Post/Office, Wishing/Well,
Train/Station, and Dump labels. `akiya_str$483` is the eight-byte `free    `
reference; the native six-byte empty-house source is at `8088FE84`.
The supplied GC executable confirms these exact strings. Native descriptors
are at `8088FF20 + index*28`; indices two through seven point to text at
`8088FF00`, `FF04`, `FF08`, `FF10`, `FF14`, and `FF18` with lengths
3, 4, 4, 4, 2, and 5. The separate post-office continuation uses `8088FF0C`.
Preserve GC line intent when adapting landmark labels. These strings are not
completed by the villager-name cache. Image-only labels remain in v1 scope.
Include each original embedded string once in combined accounting when applying
these labels; do not treat them as copies of the bank-name resources.

Continue the remaining live identity readers/editors, catchphrase input/display,
item readers, residual general strings/letters, accents, and combined v0 checks.
Do not redo finished owned letter/quest paths merely because their original
native instructions remain. Combined accounting verifies both installed name
readers but keeps incomplete name families pending; source IDs are not counted
again for each consumer.
