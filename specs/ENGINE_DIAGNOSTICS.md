# Native engine test messages and shopping labels

## Complete text scope

`translations/n64-engine-diagnostics.json` supplies fifteen original translations:
test messages `0001/0002/0003/0006/0009..000E/0012`, personality samples `0007/0008`,
and shopping labels `1354/1355`. They use the original native commands, command
arguments, field order, page boundaries, choice IDs, branch targets, and endings.
All are drafts requiring final wording review. Their test/diagnostic metadata
does not establish reachability or make them available as continuation storage.

`0002` retains the unlucky-state command and the literal `%SFN%` test label.
Its End/Continue choices retain `FFFF/0004`. `0003` continues to `0002`.
The two mood menus retain their original normal/angry/sad and happy/sleepy
choices, with Next linking between menus. Every mood response returns through
`0003`. Voice-mode toggles in `0006` stay in their original order with all waits.
No sound output is authorised by this work; emulator checks keep audio disabled.

The personality samples retain the complete descriptions of putting trusted
people above oneself, and valuing humour and a lively atmosphere. The shopping
labels retain Normal girl, Shopping, part 1, and printed numbers `4948/4949`.
Both native labels say part 1; the second is not silently renumbered. Their empty
legacy replacements are not considered translations.

The five larger scripts `0004/0005/000F/0010/0011` remain separate work. They
include deliberate kana/sound/glyph examples and repeated test patterns.
Translate their instructional prose without deleting those samples merely to
remove Japanese from a coverage report. Longer complete English may also need
an approved existing-page split. The paused font-atlas investigation is unrelated.

## Verification contract

- Require every native source hash, exact command sequence and arguments,
  per-page commands, complete wording, printed labels, and native final command.
- Include all fifteen drafts in basic and resident-enabled generation without
  adding a runtime dependency or granting extra control permissions.
- Check encoded round trips, expansion limits, and layout using approved metrics.
- Reconstruct installed text and verify that all previous candidate entries,
  executable code, fonts, choices, general strings, and saved layouts are unchanged.
- Load all complete cartridge messages in a silent, bounded, isolated checkpoint;
  check headers and guards, restore the checkpoint, and retain blank saves.
  Loading does not execute mood/luck/voice changes, diagnostic menus, or saving.

Implementation and verification results are recorded in the work log. Ordinary
caller traversal, actual diagnostic actions, final presentation, and original
hardware remain separate checks.

## Verified scope

All five focused tests and the complete 822-test regression pass. The native
batch loads all fifteen complete messages
through the cartridge loader in 84 recorded steps with 47 memory assertions.
Headers, adjacent/module guards, checkpoint restoration, blank isolated FlashRAM
and Pak, and graceful shutdown pass with audio disabled and four-MiB configuration.
Independent scenario reconstruction and each native load result also pass.

Both generation modes add exactly the fifteen versioned drafts; every earlier
candidate remains identical. All 12,757 installed edits reconstruct correctly,
and the UPS applied to the verified original produces the complete pilot ROM.
Only main text, its offsets, and DMA metadata differ from the reply checkpoint.
All other resource files remain unchanged. This is a loader/retention test, not
execution of the diagnostics' gameplay, mood, voice, or choice actions.
