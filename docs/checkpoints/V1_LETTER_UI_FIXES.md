# Letter UI corrections

The combined intermediate is
`build/v1-letter-ui-fix-02/animal-forest-title-preview.z64`.
ROM SHA-256: `0032a12d0c84810b89e2186dab524130b7f09506c6ab163c27c357fddf1d8ae3`.
UPS SHA-256: `b4bfffa4ab1e1e1c438604465c859aa32f0c6fc7175785e5e6b1eb5ed861f757`.
It retains the Press Start, proportional editor, HUD, notice/tune, and inventory
money fixes, and requires an Expansion Pak. Earlier artifacts/saves are intact.

The [fix contract](../../specs/V1_PLAYTEST_FIXES.md) binds native readers and
GC text sources. Address prompts now use the complete English GC wording.
Recipient display resolves all supported villager identities through the
existing full-name resource. Limberg is the one human-reported case, not a
hard-coded exception or evidence that every name was wrong. Already-correct
names and player-name fallbacks are preserved. Stock draft To/from defaults
change without replacing custom text, enlarging saved fields, or migrating
arbitrary mail.

## Verification record

- Three focused host/ROM tests passed in 2.743 seconds. Address-sanitizer and
  undefined-behaviour checks cover names, partial lookup failure, prompts,
  stock/custom defaults, read modes, and unchanged data. Artifact checks cover
  source/ROM/UPS identity, native DMA ownership, two relocation bases, complete
  unrelated-resource retention, and bounded allocation.
- `build/v1-letter-ui-native-01/results.json` passed the real cartridge loads
  and representative Limberg/Buzz/player name calls with unchanged records.
  The next draw call was rejected by the runner's nine-argument ceiling before
  game execution. This is a classified setup failure, not a game crash or a
  successful complete scenario.
- The justified retry is `build/v1-letter-ui-native-02/results.json`: thirteen
  calls, thirty assertions, eighty-four records, all passing. It reuses the name
  evidence and runs the remaining English prompt translation and native font
  draws, Limberg drawing, WRITE/EDIT defaults, READ/custom-text retention, full
  live-save retention, and RAM/stack guards. Cartridge code was loaded by the
  actual native loader, not uploaded by the test. The allocated fixture was
  freed, the checkpoint restored, emulation resumed, and shutdown was graceful.
- Ten debugger-thread checks passed in 0.002 seconds. Verified native calls can
  use up to sixteen o32 words, fitting below the existing stack guard; ordinary
  JSON calls retain nine. Invalid counts fail before debugger writes.
- The expanded reconstructor also retains the passing three Press Start and
  four pixel-editor focused checks; their existing artifacts remain unchanged.

The native probe exercises the new defaults helper, not the complete ordinary
menu constructor. Human letter opening/selection, visible layout, and original-
hardware rechecking remain pending. No audio was played. The keyboard background
and combined patch packaging remain implementation work, not passed acceptance.
