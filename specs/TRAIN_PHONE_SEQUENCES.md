# Complete train phone calls

Rover's complete English first-resident (`2AD0`) and later-resident (`2ADE`)
phone calls exceed the message buffer at 1,235 and 1,259 expanded bytes.
Use `2AD0 → 07DA` and `2ADE → 2B1B`, splitting existing English
wait/newline/page-clear spans `[460,465)` and `[471,476)` respectively.
Part bounds are 513/740 and 494/783. No word, line, emphasis, pause, or other
page break is removed. Both parts must be installed together with the resident
runtime, and final endings remain `00`.

The first call retains the initial business discussion and search for a home;
the later call retains the impression joke and explicit previous-resident
reference. Both retain native town/player fields, full housing request, answers,
and goodbye. Every line keeps its English grey colour, vertical offset, and
small scale. The source voice controls `51/00` and `51/01` remain exact.

## Pacing and cancellation

`72/73` are the existing protected-pacing operations. Each complete lock/unlock
pair stays in the first part. Sequence validation admits them only with verified
resident runtime, rejects nested or unmatched operations, and rejects a span
crossing a message boundary. No new runtime command is introduced.

Native `06/07` enable and disable cancellation; they are not phone-mode or BGM
commands. Their exact order is retained. The `06` appears in part one and `07`
in part two. The native message-change routine `8009E658` loads the next text,
clears its cursor/line positions, and sets the cursor timer; it does not clear
the window's cancellation-enabled word at `2C0`. The regular page transition
resets the active cancellation word at `2BC`, not the enabled state. Thus the
next part remains skippable until its original `07`, just as the next page does.
The protected intro is fully unlocked before the new continuation boundary.

Native `06/07` handlers are `800A0864/800A08B0`. The actual message-change routine
and called cursor-reset helpers require source-hash checks and native execution
with complete cartridge data. Tests must check both active-cancel states, enabled
state retention, complete replacement buffer, and the final original `07` reset.
This is not permission to split arbitrary persistent state or relocate a pacing
command merely to make a test pass.

## Reserved records and acceptance

`07DA/2B1B` are generic native reserve labels with source hash
`b2c0b6f9facf02630f093fd1b6a5a6e47d722ecadd50e6c82fae305db4821e2c`.
Neither is already allocated or targeted by native message scripts. Pinned
executable/data-section scanning finds no relevant code immediate or aligned
data halfword for either ID. This is slot-specific evidence, not exhaustive
proof against indirect ID computation.

Require full reference/part reconstruction, exact cut spans, all bounds,
runtime-only installation, rejection of partial/stale/changed groups, balanced
pacing, unchanged native cancellation/voice operations, repeated reserve scans,
and native loaded transitions with memory/checkpoint guards. Actual train actor
progression, rendered text, real input timing, normal saving, and hardware remain
separate gameplay and playthrough requirements. Fonts, runtime code, native
allocations, and save formats are unchanged.

Five dedicated tests, ten long-advice/pacing tests, 110 reference tests, and ten
special/contextual-actor tests pass. The silent `build/smoke-train-phone-01/`
batch passes 211 steps: 42 native calls, 38 expected returns, eight direct loads,
four actual message changes, four normal-page setup calls, and 104 memory
assertions. Both active-cancel states retain enabled state across each loaded
continuation; ordinary page setup clears only current cancellation, and the
original final `07` clears both. Complete buffers, pacing flags, cursor resets,
timer, guards, one restored checkpoint, and blank FlashRAM/Pak pass.

Full output contains all four parts. Basic output omits both groups and their
two allocated reserve labels, retaining the native reserve sources instead of
installing partial sequence members. This is an intentionally smaller basic
configuration, not lost text from the resident-runtime pilot.
