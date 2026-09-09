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

`build/quest-reply-scenario.json` prepares 144 original-metadata, home-delivery,
and complete-readback cases, spanning all templates and capitalization states.
The batch includes home/slot ownership, resource failure/retry, invalid ranks,
retained quest inputs, original native fields/RNG, guards, restored live state,
and checkpoint restoration. `build/smoke-quest-reply-01` is the assigned isolated
run directory; only terminal results can establish which checks passed.
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

Collect the specific native process's terminal results without restarting an
unobserved live process. Preserve passed bulk cases if an isolated edge needs
follow-up. Continue remaining noticeboard/general/name consumers, review,
normal gameplay/save/travel acceptance, title-first artwork, GameCube-style
keyboard, and patch-only release preparation. This checkpoint is not full
project completion or hardware certification.
