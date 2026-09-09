# Letter-quest reply integration checkpoint

## Implemented scope

All 72 quest-reply templates `0075..00BC` and their 216 complete parts are
installed in the full translation ROM. The supplied English wording, manual
layout, commands, eight-byte villager signatures, and sixteen-byte required
item names remain complete. Original rank/personality selection, gifts, native
short-field preparation, received font, sender/recipient metadata, and paper 22
remain. A guarded mailbox copy prevents incomplete resource preparation from
publishing a letter. See the [source and ownership specification](../../specs/QUEST_REPLY_LETTERS.md).

The shared creator is 34,096 image bytes plus 528 relocation bytes, with a
39,983-byte temporary loader request including its existing workspace/alignment.
The new C creator has a 120-byte compiled stack frame. The native wrapper uses
64 bytes and fits its original function slot; the delivery owner's 240-byte
frame and eligibility/return paths remain. Resident instructions, reservation,
four-MiB bounds, and saved layouts do not grow.

## Artifacts

- ROM: `build/quest-reply-letters-pilot/animal-forest-halfwidth.z64`, SHA-256
  `9be7922f38df67001fa06ce9a5f13efd9e0736166bfdb9d4e0417c3c7e093f27`.
- UPS: `build/quest-reply-letters-pilot/animal-forest-halfwidth.ups`, SHA-256
  `54e12cf8ad48670b235aa0860e965944b2d938df5b8ddcf3e5d89e3140fddb68`.
- Creator: `build/quest-reply-creator/overlay.bin`, SHA-256
  `b0f6c4d2ebbd608230461302081f32b365993794a3cd0cff96be5bf414e8917c`.
- Relocation: `build/quest-reply-creator/relocation.bin`, SHA-256
  `07b07979d117ba0f5ac5601257adb51dccc2bf75cd3f1bfdad1e640c883039d8`.
- Wrapper/gate: `build/quest-reply-owners/owners.bin`, SHA-256
  `b23b76480287f8d3d658b0faef098a8777264ae52273d62a7bfa96f7de3eaf0a`.

Only main-code wrapper/gate instructions, creator contents, resident creator
configuration, and DMA metadata differ from the complete secret-letter ROM.
Every earlier text/font/actor resource remains. Local game data and generated
ROM/UPS/binaries remain ignored.

## Verified checks

All 41 host tests pass in `build/quest-reply-host-tests.log`, including all
72 templates, both capitalization states, every villager name, complete wide
item values, each catalogue-read failure, invalid inputs, preserved outputs,
and the complete earlier creator dispatch chain. All 41 also pass AddressSanitizer
and UndefinedBehaviorSanitizer in `build/quest-reply-sanitizer-tests.log`.

Independent `build/quest-reply-creator` and `build/quest-reply-creator-repro`
builds have identical image, relocation, and complete manifest. The native
wrapper/gate assembly agrees with an independently encoded instruction model.
Thirteen installation, accounting, secret-window evidence, and reader-observer
tests pass in `build/quest-reply-install-tests.log`. They check actual cartridge
contents, the UPS round trip, all earlier DMA payloads, unchanged resident
instructions, guarded original reward/grading code, and rejected rehashed edits.

All 67 selected scenario, loader, date, birthday, resident-word, show-overlay,
reader, and counter regressions pass in `build/quest-reply-regression-tests.log`,
using the current `build/shop-notice-runtime` without rewriting older artifacts.

The combined counter preserves its denominator and all prior credit. It credits
212 static English parts in this group. Four complete English signatures have
only a dynamic name field; the existing conservative static-text rule leaves
their thirteen total Japanese-source characters uncredited. This is a small
known approximation limit, not missing implemented signatures.

## Native acceptance

`build/smoke-quest-reply-01` completes successfully with 2,420 result records,
597 native calls, and 1,505 passing assertions. All 144 original-metadata and
home-delivery cases pass, spanning 72 templates, both capitalization states,
every home, and every mailbox slot. All 146 complete readbacks pass, including
two resource-recovery retries. Six owner failures and four full-width invalid
ranks retain outputs and selected inputs. Original identities, gifts, paper,
native temporary fields, and random selection remain intact.

The native batch restores all 63,872 saved-state bytes and five globals, retains
heap accounting, passes twelve fixture/stack guards and five code guards, and
reloads the checkpoint with a successful scratch-memory assertion. Isolated
FlashRAM and Pak files retain their blank fixtures; shutdown is graceful. Audio,
screenshots, Expansion Pak, and game-save writes are disabled. Production creator
code comes from the cartridge; the only uploaded comparison function is the
292-byte original creator. `tests/test_quest_reply_results.py` freezes these
results and verifies the source-bound scenario without repeating native calls.

- Results SHA-256: `85ebdffa4caa1f786dc12cf5140c94d8077812d3192e5a15a3e1d26e2b82da64`.
- Scenario SHA-256: `7c0322fc47f14114b722be57a9484742e750e5f7c69d22c9ae27cfe145b6f96a`.
- Native helper SHA-256: `71e073882508fce0a4dcafc5ac4fd89dc57f523186c98930ee46a855523244fd`.
- Restored checkpoint SHA-256: `013b860253e3a9b216054476f6bd8a77d92f589991d2c1fe560ebbc71c549e8b`.

Normal conversation selection/cleanup, save/reload, presentation review, and
original hardware remain unverified.

## Reproduction and next work

Use `build/shop-notice-runtime/module.json` unchanged. Build the creator with
all [shop-notice creator options](SHOP_NOTICE_LETTERS.md), adding
`--quest-replies` and output `build/quest-reply-creator`. Build native entries
with `python3 tools/build_quest_reply_owners.py`.

Use the complete [shop-notice ROM command](SHOP_NOTICE_LETTERS.md), retaining
every flag. Replace its creator directory with `build/quest-reply-creator`, add
`--english-secret-letters build/secret-actor` and
`--english-quest-replies build/quest-reply-owners`, and set output to
`build/quest-reply-letters-pilot`. Prepare the silent batch with:

```sh
python3 tools/quest_reply_scenario.py --output build/quest-reply-scenario.json \
  --boot-output build/quest-reply-silent-boot.json
```

Do not repeat the completed native bulk batch. Continue remaining
noticeboard/general/name consumers, review,
normal gameplay/save/travel acceptance, title-first artwork, GameCube-style
keyboard, and patch-only release preparation. This checkpoint is not full
project completion or hardware certification.

The next [noticeboard inventory](../../specs/NOTICEBOARD_TEXT.md) identifies
the native fifteen-slot layout, four-post initializer, append/shift writer,
automatic-post call, and reference field families. Its bodies require their
own storage/reader integration and native-event matching; they are not credited
merely because the mail catalogue contains English references.
