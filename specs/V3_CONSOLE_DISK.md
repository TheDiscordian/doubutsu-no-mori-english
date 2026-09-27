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

The current preparation is `build/v3-console-games-prepared-07/`.
Its zero-linked MIPS disk service is 3,659 bytes, SHA-256
`d72cfab92348d6265c996bf986b20b3509541182be1db76ab9babd98c328e385`.
It uses no mutable globals or unresolved library calls. The largest stack chain
is bind plus validation: 112 bytes. `console_disk/disk.json` records complete
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
unmodified region to ignored `console_disk/bios.bin`. The eventual native reset
must copy it privately before applying the donor's `EBD=42` and `1A0` changes.
No additional game or BIOS download is required.

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
  sizes are 2,048/32,768/8,192 bytes. The BIOS is another 8,192-byte input.
- Boot follows the first side's actual file count and boot-file ID, retains
  protected-load refusal, clears the source work range, and loads complete
  eligible files. It marks character conversion pending; the native renderer
  must actually perform that conversion.
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
interrupts, acknowledgement, readiness, and motor state. There are 2,935 checks.
The register cases are expectations derived from the checked donor assembly,
not execution of that PowerPC assembly or proof of native N64 operation.

The prepared-resource check verifies MIPS/source receipts, complete BIOS
identity/vectors, unchanged nineteen-game resources, and explicit non-installation.
No historical ROM or unchanged native scenario is replayed for this preparation.

Remaining implementation is required: native disk memory/reset mapping, the
BIOS special-instruction bridge, CPU/PPU read/write and interrupt bindings,
character conversion, expansion sound and motor synchronization, complete
save/frame/reset/return integration, and enabling the actual source furniture
only when those dependencies work. Reuse partial native disk-register machinery
where verified; a missing mapper-20 table entry is not an inventory of all
native disk code. Preserve the complete source image and BIOS.

The unresolved native console startup stall remains tracked in the
[capacity checkpoint](../docs/checkpoints/V3_CONSOLE_CAPACITY.md). Its two attempts
are spent; this preparation is not a reason to replay an unchanged cartridge.
No new gameplay, ordinary save cycle, or original-hardware claim is made.
