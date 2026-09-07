# Native test-call context

## Scope

The isolated emulator can invoke native MIPS functions using reserved module
scratch RAM. This is test instrumentation, not normal gameplay or save evidence.
A complete emulator checkpoint must precede the calls and restore the complete
machine after them. Restore CPU registers after each call only to stage the next
test; register restoration alone does not undo thread queues, DMA, or RAM writes.

## Required thread boundary

An arbitrary debugger pause can stop in any native thread. Never inject a
synchronous cartridge read into the idle thread. Blocking the sole idle thread
can leave the scheduler without a runnable thread. Interrupt, audio, and DMA
manager contexts are likewise not approved test-call contexts.

The `pause_game_thread` action executes before any fixture RAM writes. It uses a
temporary breakpoint at `game_main`, `800D334C`, verifies its original entry
instruction `27BDFFE0`, and waits for a normal frame entry. At that point:

- `__osRunningThread` at `8003CE30` points to `graphThread`, `80145630`.
- The thread has ID four and running state four at offsets `14` and `10`.
- The program counter is `800D334C`, before its stack-frame instruction executes.

Offsets are hexadecimal. Every injected call checks this context again before
changing registers. Unknown register layouts, thread pointers, IDs/states,
entry instructions, and program counters fail. The record retains the original
pause context and the verified test thread. Function return uses the temporary
breakpoint at `8019A8E0`; an explicit test-only `return_address` may select an
aligned address within the isolated test region, at most `8019C780`. This allows
call-site tail shims to exercise relocated return-address arithmetic without
writing outside test RAM. The test stack starts at `8019C880` and must be restored.
Call failures retain the before/after registers and scratch stack for diagnosis.

The module reserves 32 KiB; linked code/data/BSS may occupy at most 24 KiB.
Native-call verification rejects smaller/older reservations, overlapping linked
sizes, and module targets beyond the linked end. Fixture addresses and embedded
pointers live in the separate final 8 KiB. Static JSON fixtures and generators
are checked for obsolete test-region addresses, including decimal arguments.
Emulator checkpoints from another ROM remain invalid after a layout change.

Mail API tests place decoded records at `8019AA00`, wire envelopes at `8019AC00`,
template descriptors at `8019AD00`, text sources at `8019AE00`, and full output
at `8019B400`. Output ends before the low-stack guard at `8019B880`; the stack
has four KiB available above that guard. The independent high-stack guard is at
`8019C8B0`. All pointer-bearing structures use the actual big-endian o32 layout,
not the host's pointer widths.

The cartridge-catalog restoration scenario uses a separate layout: wire at
`8019A8F0` plus alignment skew, the 3,552-byte o32 workspace at `8019AA00`, and
complete output at `8019B800`. The low-stack guard is at `8019BE80`, leaving
2,560 bytes below the test stack top; the high-stack and module guards remain
unchanged. It checks full output against the reference and never supplies host
pointers as cartridge template descriptors.

The read-layout scenario uses a 4,608-byte isolated graphics arena at `8019AEE0`
and a low-stack guard at `8019C120`. It executes the real native font renderer
and checks every vertex position as well as both arena pointers. A sparse fake
submenu supplies only the board and menu-state offsets read by the hooks; it
does not represent an allocated live submenu. The non-read tail-call probes use
return breakpoint `8019B1E0` and small argument-recording targets inside the same
test region. The original board code is not called by those forwarding probes.

No running-thread pointer, native scheduling field, or gameplay progression value
is edited to obtain this context. The existing socket and process time bounds
limit a missing frame breakpoint. Native behaviour and real hardware still need
independent validation.

Debugger socket startup has a bounded readiness wait while the exact emulator
process remains live. A slow connection does not restart the emulator. Confirmed
process exit, an expired readiness deadline, and unexpected protocol errors fail
the test and preserve its logs.

Execution-observation breakpoints must be installed while paused. Installing one
while running can produce a stop before the next continue command, then another
stop on that continue, shifting later responses. The mail-window scenario uses
the verified frame entry before installing its read-hook breakpoints. Generic
commands support exact `expect_result` replies, and bulk `g` supports `expect_pc`
against the complete 71-register packet. Replies are recorded before validation,
including malformed or out-of-order replies; no such reply counts as execution
evidence.

## Exact debugger memory access

The ares GDB interface uses native CPU accesses for one-, two-, four-, and
eight-byte requests. Short unaligned reads may align down, and an eight-byte
read can differ between the bus and a cached line. The runner aligns read spans
to eight bytes and slices the requested range. Writes use byte edges and aligned
word/bulk spans; an eight-byte request at an address aligned to only four bytes
is split into two words. Neighbouring bytes are never rewritten to fix alignment.
Synthetic tests cover every offset and short length, including cached-style
eight-byte alignment. Native source/destination guards test the actual interface.
The upstream [GDB access dispatcher](https://github.com/ares-emulator/ares/blob/v148/ares/n64/system/system.cpp)
and [debug cache access](https://github.com/ares-emulator/ares/blob/v148/ares/n64/cpu/dcache.cpp)
define these short-access paths; the synthetic model includes all four sizes.

Incremental result files are atomically replaced after complete serialization,
so concurrent status readers cannot mistake a partially written JSON document
for a terminal test failure.
