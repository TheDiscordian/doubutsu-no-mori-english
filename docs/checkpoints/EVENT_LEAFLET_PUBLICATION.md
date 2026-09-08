# Event leaflet integration work record

The optional event-manager owner installs all sixteen complete sale letters and
three complete Redd letters. It preserves the selected native stock, count,
template, and timestamp; English preparation finishes before native mode-two
receipt. The [specification](../../specs/EVENT_LEAFLET_PUBLICATION.md) records the
saved pending-selector extension and remaining normal-routing acceptance.

## Built artifacts

- Integrated ROM: `build/event-actor-pilot/animal-forest-halfwidth.z64`, SHA-256
  `8c9174ea5bd93da12562571c7e11098e0cf236ce6ee4c34226288e02af8280fe`.
- Original-ROM UPS patch SHA-256:
  `0722c2d091c7a7e30575d611339f1c627c7b06c4fd383399aaf18aa7d2692656`.
- Event actor: 38,112 bytes, SHA-256
  `e8f2a91f82c8b6bac00595186fbb916553c10b0b05f5f6b393b6eecf6dcb7994`.
- Relocations: 1,760 bytes, SHA-256
  `d4e2f5ab1722814e0ee24e154e8c41904dd1a5277222fc9981c0f5ff653dda65`.
- Embedded publication probe: 3,716 bytes, SHA-256
  `b2c6654aaf15a6a06d3245cbad2e7d6477555681f34cec941277484d3d37b99a`.
- Bound 78-case native scenario: `build/event-actor-scenario.json`, SHA-256
  `ae68f202b0a20cfb6a78f2a2aba0604b73dbef24c4ac06788d6d11660109ac18`.
- Passing native results: `build/smoke-event-actor-02/results.json`, SHA-256
  `7780231b8c51bf0729db35e294ad094dd48ffdbbb547063562a93a9ecd97bc78`.
- Native helper SHA-256:
  `6b3ad04bb2743c429ddd546bc1b52feba889705860546b2f087f8100adb7a7ee`.
- Silent runner SHA-256:
  `e66abdb42d17c8136bebbb28734cea8680c578066d5ccc919342959e679d1739`.

`build/event-actor` and `build/event-actor-repro` agree on actor, relocations,
and manifest. The original file/BSS consumes 27,568 bytes, the creator consumes
3,716, and appended adapter code/padding ends at offset 32,384. Owned zero data
fills the rest. Registration/retry frames are 24/40 bytes, and the publication
frame is 72 bytes. No resident-module or saved-layout growth is introduced;
the pending flag does extend saved semantics.

## Executed checks

Four host owner tests pass in 0.651 seconds. They exercise every valid template,
item count, and initial capitalization; complete production formatter output;
retained failures; retries after clearing loaded cache; changed-event rejection;
native save/destructor delegation; invalid pending markers; and non-letter
initializer results. The native callbacks alone are isolated host equivalents.

Three host installer tests pass in 10.706 seconds. They check all original and
appended relocations, profile/caller targets at three loaded bases, original BSS
addresses, stale-source and malformed-inventory rejection, atomic failure, and
independent reconstruction of the complete integrated ROM. Only event code,
relocations, and event ownership metadata differ from the renewal pilot. All
13,383 ordinary applied edits and earlier resource images remain unchanged.

`build/smoke-event-actor-01` completes all 78 letter combinations plus two
cache-loss retries: 80 complete saved-letter readbacks and 1,291 memory
assertions pass. Native cartridge loading, both actual registration JAL/delay
slots with their original frames, the actual schedule pending gate, receipt,
duplicate prevention, full-save comparisons, heap accounting, guards, source
RNG retention, and live-save/global restoration pass. The runner records loading
the checkpoint, then loses its debugger connection at its 250-second outer
process bound before its final resumed-state check. This first run is **not**
a passing end-to-end runner result.

The unchanged scenario passes completely with a 400-second bound in
`build/smoke-event-actor-02`: 78 combinations, two cache-loss retries, 80 complete
readbacks, 322 native calls, and 1,291 helper memory assertions. The additional
post-restore assertion also passes, for 1,292 total. The checkpoint resumes and
the emulator shuts down gracefully. FlashRAM remains all `FF`, and the Pak
matches the independently retained blank fixture. Native code, save state, heap
accounting, RNG, guards, and restored shared fields pass their specified checks.
This is not an actual FlashRAM save/reload or normal event scheduling test.

The full event regression batch passes 930 tests in 495.486 seconds, recorded
in `build/tests-event-actor-regression.log`. It includes the current event owner,
installer, and complete-publication tests. The older 918-test result belongs to
renewal, not to this event installation.

## Reproduction

Build the event publication probe and owner using the pinned Docker compiler:

```sh
python3 tools/build_mail_generation.py --event-leaflets \
  --module build/renewal-actor-pilot/runtime-module.json \
  --output build/event-leaflet-probe
python3 tools/build_event_actor.py \
  --rom 'local/rom/Doubutsu no Mori (Japan).z64'
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
  --npc-mail-generation build/npc-mail-capture \
  --extended-font build/extended-font-cartridge \
  --english-fortune-slips build/fortune-recovery-actor \
  --english-leaflet-dates build/leaflet-dates \
  --english-renewal-letters build/renewal-actor \
  --english-event-letters build/event-actor --output build/event-actor-pilot
python3 tools/event_actor_scenario.py --output build/event-actor-scenario.json
```

The complete NPC creator is `build/npc-mail-capture`, and both catalogues are in
`build/fortune-slip-resources`; older similarly named resource directories are
not interchangeable. Run the scenario through `tools/emulator_smoke.py` with the
pilot ROM, a fresh isolated output directory, the configured Xvfb binary, and
`--seconds 400`. All game assets, ROMs, patches, and generated test records stay
ignored. No user save or physical hardware is used.

## Remaining acceptance and next work

- Native selection routines are retained but not executed by this fixture.
  Stock/date inputs and chosen templates are supplied at the registration
  boundary. The schedule test uses an owned two-instruction exit before
  unrelated event processing; it does not establish full schedule progression.
- The pending flag survives simulated cache loss, not a tested FlashRAM reload.
  Audit all native event/save writers, replacement while pending, actor removal,
  and normal reload paths. Avoid associating an old selector with changed saved
  event fields. Test the extended flag and existing full-letter records together.
- Normal event-manager allocation, sale/Redd gameplay, home notice delivery,
  visual review, and original hardware remain unverified.
- Resume bulk remaining general text and letter consumers after this batch.
  The general bank still contains native date/unit strings, custom catchphrase
  and name storage, the gyroid default, apology targets, reserved labels, and
  auxiliary word/name rows. Existing wide display/catalogue resources already
  cover some of those source identities; do not count or rewrite them twice.
- Complete ordinary gameplay/save acceptance, semantic review, the five native
  sample scripts, title-first artwork, the English grid keyboard, and patch-only
  release preparation. Do not resume the paused atlas-edge investigation.
