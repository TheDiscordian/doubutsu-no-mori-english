# QD disk services

## Shared conversion and current state

The ordinary console converter prepares QD dependencies alongside all cartridge
images and persistence recipes. There is no per-game installer:

```sh
python3 tools/v3_furniture_pipeline.py convert --representation console \
  --assets-only --donor-disc 'local/gamecube/Animal Crossing (USA, Canada).ciso' \
  --base-lock build/v3-console-emulator-capacity-01/build-lock.json \
  --output build/v3-console-games-prepared-next
```

The current preparation is `build/v3-console-games-prepared-09/`.
Its zero-linked MIPS disk service is 5,139 bytes, SHA-256
`14cf5bb33f41256086b24b48a5a8c152844d20e71a2ae25fe41f8b7f0bd766da`.
It uses no mutable globals or unresolved library calls. The largest stack chain
is WDM plus save plus validation: 192 bytes. `console_disk/disk.json` records complete
source and compiled identities. The nineteen-game bundle, compact metadata,
and compressed image pool are identical to the retained complete preparation.

This is prepared engine code, not installed QD emulation. The current cartridge
remains ABI 281. No profile, selection, save, or patcher deployment changes.

## Donor resources and contract

`tools/v3_console_disk.py` checks the complete GAFE01-r0 executable and archive,
six complete source instruction spans, and the compressed/decoded noise resource.
The source spans cover fast loading, fast saving, reset, disk reads, BIOS special
instructions/interrupts/writes, and per-frame disk state. The preserved source
receipt includes the BIOS vectors and the donor's private reset modifications.

`noise.bin.szs` supplies the complete 8,192-byte disk BIOS at decoded offset zero.
Its SHA-256 is `eef78986e952e1b3bdac95d9a627768632e75853f538d2fb17bb31b6c6ebce38`;
NMI/reset/IRQ vectors are `E18B`, `EE24`, and `E1C7`. The converter writes the
unmodified region to ignored `console_disk/bios.bin`. Binding requires a private
writable copy; service reset applies the donor's `EBD=42` and `1A0` changes.
The native adapter must provide that copy and its actual lifetime.
No additional game or BIOS download is required.

The fast-boot initialization span is the complete 260 bytes at donor executable
address `800D6671`, SHA-256
`05177da7b020892c9a592d39a9d67562661ece6958a79c71bedf0cf26e3f558b`.
The converter writes it to ignored `console_disk/boot-state.bin`. Actual checked
instructions at `8003C4B4..8003C4CC` copy this span to work RAM `00FA..01FD`.
The eleven-byte `ksNesInitQDDataTbl` declaration does not describe the whole read:
the loop starts at symbol+1 and advances 260 times. Preserve the checked span,
not just the declaration or a guessed replacement initialization table.

The actual complete Clu Clu Land D side is 65,536 bytes with four files:
copyright/nametable data, 32-KiB programme data, 8-KiB character data, and 84 bytes
of top-score data. The donor boot helper skips the unmapped nametable file;
that skip is retained. All original disk bytes, including block CRC fields and
unused tail bytes, remain present. The converter does not fabricate an iNES
header, substitute another release, or reduce the saved game to a score label.

## Service behaviour

`console_disk.c/.h` owns the source disk-service state, not a replacement NES CPU:

- Binding validates one to four complete sides and disjoint context, work,
  programme, character, BIOS, and image buffers. Required work/programme/character
  sizes are 2,048/32,768/8,192 bytes. The private BIOS and immutable boot state
  require another 8,192 and 260 bytes, all disjoint. Reset restores BIOS opcode
  `42` and selects the donor's normal or `koro` disk-specific BIOS mask.
- Boot follows the first side's actual file count and boot-file ID, retains
  protected-load refusal, clears the source work range, and loads complete
  eligible files. It marks character conversion pending; the native adapter
  must invoke the converted native-layout operation on its actual buffers.
- Fast saving consumes the complete 27-byte BIOS request, matches a real side's
  ten-byte identity, preserves the source file-slot/count and header writes,
  and reads complete data through bounded CPU-bank views. The source does not
  rewrite block CRCs in this fast path; neither does this service. Ordinary
  disk-byte writes preserve the source dirty-state behaviour.
- Disk reads cover `4030..4033`, including acknowledgement, within-side head
  wrapping, BIOS-PC-specific status, readiness, and the expansion connector.
- Writes cover `4020..4026`, including source timer division by 114, transfer
  control, disk writes, head reset, and nametable selection. Return flags require
  the native adapter to perform audio writes, motor synchronization, and actual
  nametable updates; returning a flag is not implementing those consumers.
- The interrupt callback retains the donor's scanline scheduling, frame wrap,
  transfer byte, timer repeat/control-bit transitions, and interrupt request.
  Its caller supplies the native CPU interrupt dispatch. It is not a free-running
  timer merely because a register has been written.
- Frame updates retain the donor's button-gated readiness counter and motor
  countdown. They do not replace native frame timing or synthesize disk sound.

`af_v3_qd_wdm` supplies all five source BIOS special-instruction services. Its
`AFQCpu` view contains the fetched-next PC, accumulator, stack pointer, internal
zero-result value, and cycle counter. Unmentioned registers/flags remain owned
by the native interpreter and unchanged. The adapter must call this only for
the disk CPU, after the two-byte WDM instruction fetch:

| PC | Source operation |
| --- | --- |
| `E7A6` | Retain the low three cycle bits and rewind PC by two to wait. |
| `E408` | Store accumulator in work byte 1, match an eight-byte disk identity, and select the complete side. |
| `EEBF` | Skip accumulator `6x`; otherwise perform fast boot, change the private BIOS opcode to `A9`, and set the internal zero result. Success sets both drive-status bytes, clears work `0000..00F9`, copies the full initialization span, and rewinds PC by `24`. Accumulator is unchanged. |
| `EEF6` | Update disk status unless the controller's top nibble is six; load accumulator from work `90` without changing flags. |
| `E23B` | Consume the stacked return and both descriptor pointers, perform the complete fast save, and update accumulator/zero result. Success pops two stack bytes and returns to the saved address plus five. Accumulator `FF` only writes the slot sentinel. |

The stacked descriptor read follows the donor's linear work-RAM fetch; the
resulting stack pointer wraps to eight bits. Source BIOS errors are written to
CPU result registers without pretending that a save succeeded. Unsafe input
returns a negative API result before changing the CPU or disk; temporary slot
writes are restored on malformed requests.

`af_v3_qd_native_characters` converts the complete 8-KiB character data into the
native interpreter/RSP's paired-plane tile layout. The complete 88-byte native
converter at `808328DC` is checked against SHA-256
`9fa9e3ec527d580461933ab99d188678992496f44d8dc15e1ba9d92a1c162126`.
The full native emulator is also pinned. Destination capacity and separation
from every disk-service buffer are checked before writing; successful conversion
clears `chr_dirty`. Native PPU writes at `8083055C` use the same layout. The
adapter must bind the actual working patterns at state+`62C8`, graphics transfer
buffers, cache updates, and RSP lifetime; a converted private buffer does not
establish drawing or install those consumers.

Invalid/truncated blocks, cross-buffer boot writes, overlong save requests,
unmapped/aliased CPU views, invalid side/slot values, and disk-head underflow or
overflow reject before the affected operation mutates output. Unsafe source
overreads are not reproduced. CPU-bank views explicitly mirror bounded work RAM;
they do not expose adjacent emulator state as save input. The adapter must bind
real buffer lifetimes and capacities, not merely claim a pointer is non-null.

## Focused evidence and remaining integration

Two focused tests pass across targeted runs in `tests.test_v3_console_disk`.
The sanitized host test executes the actual donor C boot/save routines against
the complete supplied disk and compares full output buffers and disk sides.
It covers boot, score-file saving, a programme-bank boundary, a second-side
identity, protected/locked states, and non-mutating malformed-input rejection.
Register/timing checks cover all control-byte values, transfer and timer
interrupts, acknowledgement, readiness, and motor state. BIOS checks cover all
five services, complete boot output, reset patches, no-op/error paths, descriptor
bank boundaries, stack wrap, and malformed-request/alias rejection. There are
15,594 checks, including reconstruction of every tile/plane in the native CHR
layout and untouched buffer guards. Register and WDM expectations derive from the checked donor
assembly, not execution of that PowerPC assembly or proof of native N64 operation.

The prepared-resource check verifies MIPS/source receipts, complete BIOS/boot-state
identity/vectors, unchanged nineteen-game resources, and explicit non-installation.
No historical ROM or unchanged native scenario is replayed for this preparation.

Remaining implementation is required: native disk memory/reset mapping, the
WDM dispatch/register bridge, CPU/PPU read/write and interrupt bindings,
native character-buffer/cache bindings, expansion sound and motor synchronization, complete
save/frame/reset/return integration, and enabling the actual source furniture
only when those dependencies work. Reuse partial native disk-register machinery
where verified; a missing mapper-20 table entry is not an inventory of all
native disk code. Preserve the complete source image and BIOS.

## Native integration bindings

The existing native interpreter keeps a per-instance 4-KiB opcode table at
state+`0800`; WDM `42` occupies the sixteen-byte row at state+`0C20`. Dispatch
loads its callback and size/cycle fields at `8082F274..8082F290`. Native register
ownership is accumulator/X/Y in `s0/s1/s2`, PC in `s3`, stack in `s4`, zero-result
in `s5`, carry/overflow in `s6/s7`, negative in `gp`, and cycles in `t9`.
The instruction returns through `t6`, not an ordinary C return address. The
bridge must preserve those live values around C service calls and bind only the
disk instance; replacing a global table would also affect cartridge games.

CPU bank pointers start at state+`1A38`; native load/store callback tables start
at `18E4`/`18C0`. Raw character memory is pointed to by `1A78`; the native PPU
working patterns begin at `62C8`. The native converter accepts a raw character
base, a sixteen-byte tile offset, and a destination pattern base. The native
reset initially converts graphics+`2008`, then copies into its working patterns.
The real adapter must handle both initialization and later PPU writes.

The native reset at `8082E590` mixes common state initialization with iNES header
parsing, programme/vector selection, and mapper callbacks. Calling it unchanged
on QD bytes is unsafe. The earlier initializer at `8082A6EC` also derives iNES
sizes, and startup at `8082E194` recalculates image extents from header bytes.
All three consumers need a real QD path; do not create a fake iNES header to get
past one of them. Reset must still preserve native common graphics/audio setup.

The current code reservation below `804FB000` and gap after the room callback
cannot hold the complete disk module. The current model-pool reservation ends
at `8062C020`; the fault framebuffer begins at `807DA800`. A separate checked
Expansion Pak reservation above the pool is a candidate for complete code,
32-KiB programme RAM, 8-KiB characters, private BIOS, and disk context. It is not
allocated yet. Validate the actual build's complete reservations before choosing
the range, and retain low-memory native game arenas and room resources unchanged.

The [capacity checkpoint](../docs/checkpoints/V3_CONSOLE_CAPACITY.md) records the
startup-test correction and incomplete native evidence. The title-state fixture
now supplies the real room's audio handover. Its corrected launch reaches native
console audio, where the debugger stops on recoverable lazy FPU ownership.
The installed debugger lacks the required signal-pass capability; its local
source supports it. Both corrected-fixture attempts are spent. Build a compatible
local test emulator before the next relevant native batch, without repeating the
unsupported command or masking actual faults. No gameplay, ordinary save cycle,
or original-hardware claim is made.
