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
breakpoint at `801968E0`; the test stack starts at `80198880` and must be restored.
Call failures retain the before/after registers and scratch stack for diagnosis.

No running-thread pointer, native scheduling field, or gameplay progression value
is edited to obtain this context. The existing socket and process time bounds
limit a missing frame breakpoint. Native behaviour and real hardware still need
independent validation.

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
