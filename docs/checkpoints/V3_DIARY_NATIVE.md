# Diary connected native verification

## Current result

Inconclusive before menu opening. Neither attempt reaches diary interaction,
drawing, editing, save encoding, or reload. This is not a passing UI/save test
and does not establish an in-game diary crash.

Both attempts target ABI 312, not a historical candidate:

- Lock: `build/v3-diary-category-work-01/catalogue-03/build-lock.json`.
- ROM SHA-256: `f61dd92710d80fc6197d754902abd7aedb45516effc9e3a1185d7a1acb976d0a`.
- Runner: local ares debugger, Expansion Pak, audio disabled, isolated blank
  storage, no supplied save, and no permitted FlashRAM or Controller Pak writes.
- Scenario: `tests/scenarios/v3_diary_connected.json`.
- Detailed evidence: `build/v3-diary-category-work-01/native-01/` and `native-02/`,
  each containing `run.json`, `results.json`, emulator logs, and a disposable
  checkpoint. No user ROM or save is changed.

## Recorded attempts

1. `native-01`: all four complete resident packets match the current cartridge,
   and the native CPU-fault pointer is zero. General-heap allocation of `90000`
   bytes returns zero. The probe stops before loading or opening its menu.
2. `native-02`: the same packet and initial fault checks pass. The corrected
   fixture checks the current game's two-ended arena before allocation.
   Start, head, and tail are all `80236860`; the declared arena size is
   1,713,328 bytes, but available head-to-tail space is zero at this title
   checkpoint. The guard stops before allocating or opening a menu.

These terminal results exhaust the initial attempt and single justified retry
for this setup. Renaming the output or increasing the timeout does not justify
another title-arena attempt. There is no live process being waited on.

## Scope of the retained probe

`tools/v3_diary_smoke.py` retains the intended connected native menu/keyboard
and in-memory save-codec check. Everything after the arena guard is unexecuted
and remains unverified. Its eventual graphics commands would not by themselves
prove rasterized appearance, and an in-memory codec round trip would not prove
FlashRAM device saving or hardware operation.

The next useful native check needs an ordinary disposable town/menu context
with a verified live allocation, as part of the assembled gameplay check. It
must not fabricate free heap space, overwrite live allocations, reuse personal
saves, or replay the exhausted title fixture. Required Tortimer implementation
continues independently; native verification remains open.
