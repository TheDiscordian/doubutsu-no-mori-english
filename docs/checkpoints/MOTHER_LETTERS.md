# Mom-letter integration work record

The optional system creator installs 113 complete supported Mom letters through
the original home-mailbox delivery routine. The source selects 114 IDs; body
`0136` still requires the missing semicolon glyph. Complete GameCube wording,
spaces, newlines, and capitalization commands are retained. The
[specification](../../specs/MOTHER_LETTERS.md) defines the descriptor, guards,
failure semantics, and scheduling limitations.

## Built artifacts

- Integrated ROM: `build/mother-letters-pilot/animal-forest-halfwidth.z64`, SHA-256
  `d9b2dc88b44328f66f36f7fa996d4d8ff71352d45cd8e3edace26dfa1f60b67a`.
- Original-ROM UPS patch SHA-256:
  `0d7e0a47c1c1b2ed8728498c86c757462ce70f1ec110b62fc223c2879aae86b5`.
- System creator: 25,136 bytes, SHA-256
  `8a555805ed9875d51b60e8fc02f67659c4c146f3d25ac72b5f158c0362db7ca0`.
- Native relocation section: 224 bytes, SHA-256
  `10a610322aa55f16c8b89a3486920ff8db2a6a51593b0595820889b826ed6b04`.
- Native scenario: `build/mother-letter-scenario.json`, SHA-256
  `8a3187e696030c3caae44151504e572129a37d44aae0c727c98490805c472c4f`.
- Passing native results: `build/smoke-mother-letters-01/results.json`, SHA-256
  `ee1666124a50c6f79fb3ce5c5cc873631bb0bb35b26ae486504ce3221a5fd43b`.
- Native helper SHA-256:
  `fe3a8a4903e3783f9ea7bbca9cb0e2fda9b370fb4a632be875e95f82afa97e3b`.
- Silent runner SHA-256:
  `a49dcf694227d6d82ee2a6b73f23565a4c06c01119613f4edaee26ef21e475bb`.

Independent `build/mother-mail-creator` and `build/mother-mail-creator-repro`
images, relocations, and manifests agree. The complete blob consumes 25,360
bytes; including unchanged work and alignment, a call requests 30,719 temporary
bytes. The dispatcher frame is 80 bytes, and the in-place native wrapper retains
a 48-byte frame. No resident code or saved structure grows. All 13,383 ordinary
translation edits remain in the integrated pilot.

## Executed checks

Ten host tests pass in 4.019 seconds. Every one of the 113 supported templates
is compared in both initial capitalization states: complete 164-byte metadata
and snapshot, all reconstructed header/body/footer bytes, final capitalization,
input retention, and output guards. Existing ordinary NPC creator tests run
through the system dispatcher too. Explicit unavailable text, invalid descriptor
fields, unused IDs, each catalogue-read failure, disabled resources, aliasing,
and re-entry retain the promised outputs.

The same ten tests pass with AddressSanitizer and UndefinedBehaviorSanitizer
in 6.624 seconds (`build/mother-letters-sanitizers.log`). Five installer tests
pass in 3.563 seconds; six existing NPC-loader installer/CLI tests pass in
3.413 seconds. The old creator still validates without the optional sources.
`check_mother_assembly.py` independently assembles and compares all 128 creator
bytes, the 48-byte mailbox gate, and the eight-byte queue gate. Its patch digest
is `e52366883efde1aea1001794ac0255164648bc0a1fd82bfc5f14767b31c8bd0c`.

The silent native batch passes all 113 complete templates through the installed
post routine, spanning all four permuted homes and ten mailbox slots. Each
delivered snapshot reconstructs through the actual resident reader. The creator
and resources come from the cartridge; no creator code is uploaded by the
debugger. Seven rejection cases cover unavailable text, disabled catalogue,
full mailbox, full queue, different owner, invalid paper, and oversized template.
Restoring the catalogue permits a complete retry without resetting the mailbox.

The batch records 239 native calls and 729 helper memory assertions, plus the
post-checkpoint assertion for 730 total. Entire-save comparisons restrict
publication to the selected letter. Native RNG, handbill fields, allocation
accounting, guards, and detached capture ownership pass. Live save and globals
are restored, the checkpoint resumes, and shutdown is graceful. The 131,072-byte
FlashRAM fixture remains all `FF`; the 32,768-byte Pak retains its blank-fixture
hash `ab2a6e04fd3ceb36594f1216c888a1b8bd0a3ba0a94f715a7c7601e98c49ec51`.

The full regression batch passes all 945 tests in 463.904 seconds, recorded in
`build/tests-mother-letters-regression.log`. The process exits successfully.
The integrated pilot retains the prior item/name/catchphrase/catalogue resources,
reader, fortune/renewal/event actors, date patch, and persistent font resource.
Its resident source-module hash is unchanged.

## Reproduction

```sh
python3 tools/build_npc_mail_capture.py --mother-letters \
  --output build/mother-mail-creator
python3 tools/check_mother_assembly.py
python3 tools/build.py \
  --rom 'local/rom/Doubutsu no Mori (Japan).z64' \
  --translations build/native-credits-candidates/translations.json \
  --english-keyboard --english-runtime --runtime-module build/runtime-module \
  --english-fortunes --english-resetti-replies --english-shop-units \
  --english-resident-words --english-shared-npc-words --english-credits \
  --english-dialogue-dates --extended-items build/mapped-items-final-resource \
  --display-names build/display-names --catchphrases build/catchphrases \
  --mail-catalog build/fortune-slip-resources \
  --english-mail-layout --english-mail-snapshots \
  --english-mail-grading build/mail-grading-npc \
  --npc-mail-generation build/mother-mail-creator \
  --extended-font build/extended-font-cartridge \
  --english-fortune-slips build/fortune-recovery-actor \
  --english-leaflet-dates build/leaflet-dates \
  --english-renewal-letters build/renewal-actor \
  --english-event-letters build/event-actor --english-mother-letters \
  --output build/mother-letters-pilot
python3 tools/mother_letter_scenario.py --output build/mother-letter-scenario.json
```

Execute the scenario with `tools/emulator_smoke.py`, this pilot ROM, a fresh
isolated output directory, the configured Xvfb binary, and `--seconds 400`.
All game text, compiled resources, ROMs, patches, and generated results stay
ignored. No existing user save or physical hardware is used.

## Remaining work

- Supply the semicolon through the complete mail font/catalogue path; do not
  mutate a frozen catalogue identity or shorten the source letter.
- Exercise normal date/monthly/birthday selection and scheduling, ordinary
  save/reload, and old-save policy. Direct post calls do not establish these.
- Native full-home queue refusal remains unchanged. Failed normal scheduling
  still updates its checked date; exact selected retries across days are not
  made durable by this patch.
- Continue other complete letter creators and general/item text, then batch
  the wider gameplay and save checks. Human playthrough and original hardware
  remain unverified. Title-first artwork, GC-style keyboard, full review, and
  patch-only release preparation remain in the full project queue.
