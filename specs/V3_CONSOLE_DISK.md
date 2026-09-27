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

The current preparation is `build/v3-console-games-prepared-14/`.
Its zero-linked MIPS disk service is 5,139 bytes, SHA-256
`14cf5bb33f41256086b24b48a5a8c152844d20e71a2ae25fe41f8b7f0bd766da`.
It uses no mutable globals or unresolved library calls. The largest stack chain
is WDM plus save plus validation: 192 bytes. `console_disk/disk.json` records complete
source and compiled identities. The nineteen-game bundle, compact metadata,
and compressed image pool are identical to the retained complete preparation.

The complete module and disk session hooks are installed. ABI 284 also binds the
shared room table and complete furniture profile. The current cartridge is
`build/v3-console-disk-room-imports-01/profile-runtime/`, SHA-256
`38dfbe6905917d5f0792cbad451d1d1f29b39bc2f3bfb4deac0e5625c3bc09d5`.
Selection, saved layouts, the main lock, and patcher deployments are unchanged.

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

Remaining work is actual acquisition, plus native frame-continuity, drawing,
reset/return, and ordinary gameplay verification. The common furniture importer
installs the complete room binding/profile; it does not invent a shop-stock route.
Installed session hooks are described below.
Preserve the complete source image and BIOS; no substituted cartridge is used.

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
All three consumers have a QD path in the session integration; no fake iNES
header is created. Disk reset retains native common graphics/audio state.

The current code reservation below `804FB000` and gap after the room callback
cannot hold the complete disk module. The current model-pool reservation ends
at `8062C020`; the fault framebuffer begins at `807DA800`. A separate checked
Expansion Pak reservation at `80630000..8064600F` contains the
complete code, immutable/private BIOS copies, boot data, disk context, 32-KiB
programme RAM, 8-KiB characters, and a final guard. `binding.json` records each
subrange. The installer validates all recorded resident ranges and actual
model-bank bindings before appending the packet. Low-memory native game arenas
and room resources remain unchanged.

The title-state fixture supplies the real room's audio handover. Use the compatible
local build below, without replaying exhausted historical scenarios or masking
actual faults. The retained native evidence and its limits are recorded below
and in the [capacity checkpoint](../docs/checkpoints/V3_CONSOLE_CAPACITY.md).

## Prepared native CPU and graphics module

`console_disk_native.c/.h/.ld` and `console_disk_bridge.S` compile with the complete
service into 11,323 bytes at `80630000`, SHA-256
`7498fe789e39b54a075689127f43f4943402d304c02f2d57eb7d8e6c2565dd44`.
The ordinary converter writes its source/compiler receipt to
`console_disk_native/binding.json`. No mutable globals or unresolved calls exist.
This prepared module is not a standalone replacement emulator. The installed
14,295-byte module adds the complete session handlers while reusing the lower
image loader and save executor. Installed code SHA-256:
`801c243277dcc23d7d45e0c5b66dcdc6c13292287913dc387dcf682afd80265e`.

Binding checks complete native state (`16F90` bytes), graphics (`6008` minimum),
disk, programme, character, BIOS, boot, and context extents for overlap before
mutating them. The native bank table contains address biases, not the bounded
service's bank-local pointers: banks 3–6 all use programme base minus `6000`,
and bank 7 uses BIOS base minus `E000`. All four programme banks have actual
write callbacks. The BIOS keeps a no-op store. Native cartridge/disk state and
instruction tables are not globally replaced.

The instance's WDM row retains the checked native size/cycle fields `02FF0200`:
two fetched bytes, native cycle increment `0200`. Its assembly bridge reserves
288 stack bytes, including the o32 argument area, and saves all full-width
integer registers plus HI/LO. It returns through `t6`. Only service-modified CPU
fields change; unchanged values retain their original upper halves. The maximum
known bridge/dispatch/WDM/save/validation chain is 528 bytes. Native wrapper/OS
stack requirements still belong in the installed runtime capacity check.
`.set gp=64` is required: under the ordinary o32 assembler mode, `sd`/`ld` expand
to pairs of instructions using adjacent 32-bit registers, which corrupts this
register frame. The emitted-instruction check rejects those expansions.

Character binding points the native PPU write callback at the complete private
8-KiB raw data and retains all eight identity banks. Converted data reach both
state+`62C8` and graphics+`2008`. The actual native RSP-wait function is called
before conversion, followed by writeback of both buffers. The RSP completion
word at state+`1ACC` is not copied into the donor's unrelated frame flags. The
native dynamic-character path is selected; GPU execution is not established by
these host adapter checks.

Three focused checks pass across targeted invocations. The sanitizer fixture
executes 56,205 checks against the complete actual donor disk/BIOS, including all
bank edges, programme stores, full boot, register preservation, both CHR buffers,
call order, non-mutating binding rejection, and guards. It also exercises cold
initialization using the complete relocated native tables, reset retention,
read/write fallback routes, timer and transfer scheduling, native mirroring,
IRQ destinations, motor delays without bogus audio events, sound initialization,
separate DPCM banks, address wrapping, and cartridge fallback. Native RSP/cache/audio/timer
calls are stubs. The prepared-resource check verifies source/code receipts, actual
64-bit opcodes and returns for all six bridges, and unchanged nineteen-game resources. The
underlying unchanged service retains its earlier donor comparison evidence.
These tests do not execute MIPS or claim installed disk gameplay.

### Resident installation

The shared runtime refresh installs the prepared format dependency:

```sh
python3 tools/v3_furniture_install.py --refresh-runtime \
  --console-disk build/v3-console-games-prepared-14 \
  --base-lock build/v3-console-emulator-capacity-01/build-lock.json \
  --output build/v3-console-disk-resident-next
```

`console_disk_install.py` validates the complete compiled/source receipts, BIOS,
boot data, memory layout, and current model-bank bindings. It rejects overlapping
resident ranges before changing the resource blob. One 90,128-byte packet supplies
code, immutable/private BIOS copies, boot state, zeroed context/work areas, and
the final guard. Native startup reads and verifies the entire packet before
cache writeback/invalidation and the prior init chain. A failed read or checksum
stops initialization. Later shared refreshes preserve this seventh preload.
The bootstrap occupies 668 of its 688 reserved bytes; do not silently overrun it
when adding another dependency.

Four focused checks in `tests.test_v3_console_disk_install` pass: complete installed
resources and preservation of unrelated ROM files, overlap refusal without blob
mutation, seven-packet startup and all fourteen failure paths, and four private
browser/offline compositions. The host preload fixture stubs DMA/cache calls;
native game completion, ordinary return, and hardware remain unverified.
The session installation below adds game hooks; choices stay disabled. Format-five saves are unchanged from ABI
281, but remain incompatible with V2 and V3 formats one through four; preserve
backups and warn explicitly before a hardware handoff.

### Cold initialization and Reset

`af_v3_qd_native_initialize` clears the complete native state, establishes its
actual globals and idle RSP flag, copies the relocated 4-KiB opcode and 360-byte
I/O tables, initializes common renderer state, and maps the real disk buffers.
Work RAM uses the donor's repeating `0F EF FE 7D` pattern; programme and character
RAM start at `FF` and zero. No disk byte is interpreted as an iNES size, trainer,
mapper, or programme-ROM vector. The reset PC comes from the real BIOS vector.
Audio initialization is a separate required integration operation.

The reset button uses donor `ksNesPushResetButton`, not the full cold reset.
Its complete 140-byte function at `8003A13C` is pinned in the receipt. It resets
CPU A/X/Y, stack, interrupt-control state, disk head/control, and readiness while
retaining programme/work/character RAM, PPU state, controller latch, separate
condition flags, disk changes, and the private BIOS's completed-boot patch.
Session hooks must call this operation only after capturing the save executor's
reset recipe. Re-running cold initialization on a running context rejects.

### Disk I/O, IRQ, and motor bindings

Per-instance bank-2 read/write callbacks enter full-width register bridges.
Reads at `4030..4033` return in `v0` through the native load continuation `ra`;
writes at `4020..4026` return through `t6`. Other accesses resume the actual
native default callbacks at `808303E0`/`808308C4`, whose original table entries
are checked. The bridge restores registers before tail-entering those native
callbacks, including controller/APU paths with their interpreter-specific ABI.

Writes synchronize the service's target/latch/enable with native state
`1B30`/`1B32`/`1AF9`. `4025` applies actual native mirroring: bit 3 clear selects
the `0400` vertical mask; set selects the `0800` horizontal mask. `4023` also
enters the existing timed audio-store route at `808308EC`.

The native scanline callback enters the service with live `t4`. It returns to
the main loop at `8082F23C` or the actual interrupt-request path at `8083100C`.
That native path owns the CPU interrupt mask, pending bit `20`, vector, stack,
and continuation. The donor's different pending-bit encoding is not copied into
native state. Source errors are retained in the context for the required session
failure/cleanup path; no disk item is enabled while that path is absent.

Motor changes retain all thirteen 16-ms native timer waits. The complete source
function at `80039D58`, size `94`, is pinned. Its 262 zero-address `Sound_Write`
calls per frame generate samples in the donor; the native function with the same
name instead queues a pulse-register write. Those calls must not be copied to
the N64 event queue. The native audio thread renders independently while the
interpreter sleeps. Host checks verify every delay and reject unwanted events;
silent native execution and synthesis remain unverified.

### Audio initialization and DPCM

The source receipt pins complete `Sound_Make_HVC`, `Sound_Write`, `ProcessSoundE`,
and `Sound_SetMMC` functions. Actual donor mixer calls include only the two pulse
channels, triangle, noise, and DPCM. The native mixer also has these five voices;
neither mixer renders an FDS expansion voice. Preserving this donor does not
require inventing an extra synthesizer. Other donor revisions need their own
verification.

`af_v3_qd_native_audio_initialize` runs after disk state initialization, before
native audio enable (`808549CF`), and rejects a busy audio callback (`808549C4`).
It requires the installed DPCM branch. The pinned reset loop reads ten sliding
halfword pairs from the complete 40-byte table at donor `800D8644`, advancing two
bytes, not four. Nonzero register writes use native `HS_Event` at `808345B8`;
the final channel/queue reset matches donor `Sound_SetMMC(2)`. Zero-address source
calls generate transient initialization samples and are not register writes.
The initializer binds `C000` programme RAM only with the checked bank-aware reader.

The optional shared-owner hook replaces the 28-byte DPCM fetch at `80833DBC`
with a full-width register bridge. Unlike interpreter bridges, this entry owns
`a2=SoundE`, not `s8=NES state`. The callback derives actual owner relocation
from that live audio pointer and returns through `t0` to `80833DD8`, retaining
all other live registers except the original fetched-byte `t5`. It reads
`C000..DFFF` from programme RAM and `E000..FFFF` from the private BIOS; address
overflow wraps to `8000`, never adjacent character memory. Sample starts and
offsets are bounded. No active disk context means the original contiguous
cartridge reader, so this shared hook does not redirect cartridge samples.
Session shutdown invalidates disk context after the native audio thread stops.

The patch helper removes exactly the fetch's high/low address relocations,
preserves all unrelated owner bytes and relocations, and checks two actual load
bases. Without disk symbols it reproduces the retained cartridge-only owner.
These checks and the six emitted bridges do not establish native audio quality
or complete gameplay.

## Installed session lifecycle

The standard `--refresh-runtime --console-emulator` command detects the resident
disk packet and builds combined handlers in its `80630000..80635FFF` code range.
The complete low reader/save packet, room callbacks, metadata, and its guard stay
unchanged. Five explicitly bound shared calls reuse the checked native loader,
metadata validator, save opener, score updater, and final capture. No save layout
changes. The installer verifies the old full owner/relocations before rebinding
and updates the existing disk packet and startup checksum.

Ten hooks cover the six ordinary lifecycle calls, safe arena allocation, each
CPU frame, complete image extent, and DPCM fetch. Exactly thirteen original
relocations are removed. All unrelated relocated owner bytes are checked at two
load bases. The image-extent replacement at `8082E194..8082E1C0` passes the live
image to a normal C callback: original cartridges keep the original expression,
while imports use the authenticated full size. Its two obsolete address pairs
are removed, not left to relocate the replacement instructions.

Disk initialization copies the immutable BIOS to the private copy, binds the
complete native buffers, initializes CPU/PPU and audio, and opens the common save
session before the native caller enables audio. QD bytes never reach the iNES
initializer or reset. Saved disk ranges restore into the complete image before
the first BIOS load; programme RAM is not confused with cartridge battery RAM.
The persistent profile and all four players retain the existing format-five layout.

The call at `8082A554` enters a wrapper around the original CPU-frame function.
After each actual CPU frame it updates disk readiness/motor state using the
native controller latch. The outer wrapper retains the donor's normal zero-flag
behaviour: continue frames while the motor control requests loading. Per-frame
timing is not collapsed into one update per displayed frame. Service errors or
guard damage request the native return path and disable further save capture.

Disk Reset captures the source reset recipe, waits for RSP completion, and uses
the donor reset-button operation, retaining work/programme/character data and
the completed BIOS patch. Exit follows the native audio-thread stop/join, waits
for RSP completion, captures final disk save ranges, and then invalidates context
before the native arena is released. The shared DPCM reader consequently falls
back to ordinary cartridge data on the next non-disk session.

### Session verification

Three checks in `tests.test_v3_console_disk_session` pass. Sanitized execution
performs 117,058 assertions across original and imported cartridge routes plus
the actual QD image, four-player first/repeat entry, full boot loading, image
extent, per-frame motor timing, soft-reset retention, close capture, guards,
and rejection paths. Native CPU/PPU/audio are stubs. Cartridge checks verify all
hooks/relocations, six emitted full-width bridges, current sources, complete
code/data, retained assets, and patch reconstruction. Four private compositions
match and retain the pinned no-import baseline.

The silent native attempt `build/v3-console-disk-game-native-01/` exits before
connection because the local emulator uses renamed debugger settings. The retry
at `build/v3-console-disk-game-native-02/` accepts `QPassSignals:10`, verifies
the complete preloaded disk packet, and launches game 10 through the actual
state manager and audio handover. Its snapshot shows base `803ABE20`, full
65,536-byte image at `80302060`, native state at `80337280`, active save marker
`41464E53`, zero session error, and zero fault-thread pointer. The interpreter
is executing native `8082FA00` with emulated PC `A352`; 707,856 arena bytes remain.
These are entry/execution observations, not a complete gameplay pass.

The helper incorrectly expected active marker `1`, so it stops before later
frame/graphics/context checks or checkpoint restoration. The actual save core
uses `41464E53`; the helper is corrected without a third attempt. Both setup
attempts are spent. Retain this evidence and exercise continuity, graphics,
reset/return with the next changed combined
batch. No speaker output, ordinary room entry, saved-game reload, or hardware
claim is made.

### Shared room/profile binding

ABI 284 uses the ordinary furniture category importer, with retained complete art
from `build/v3-console-room-imports-01/prepared/`. It verifies installed disk and
lower save code, complete BIOS/boot/work packet, all ten hook targets, native owner
and relocation identities, and the existing room callback/table. The common
table gains its disk readiness byte; code, image metadata/pool, and all eleven
existing console profiles/models stay intact. The shared startup embeds the
updated packet checksum. All twelve complete supplied additional console models
now have profiles; no per-game code or model recompilation is introduced.

The full Clu Clu Land D profile and official name occupy their reserved additive
slots, with the parent-selection bit still clear. Its actual `ftr_listHomePage`
reward route remains required. The unused game-twenty record is explicitly
classified as missing from the donor, not missing engine support.

Five focused checks in `tests.test_v3_console_disk_room` pass across two targeted
invocations. They check complete art/profile installation, the single changed
readiness byte, retained runtime/assets/saves, patch reconstruction, non-mutating
rejection of damaged dependencies, idempotent binding and planning, missing-donor
classification, and four private browser/offline compositions. Existing native
session evidence is retained without another unchanged fixture run. The main
lock and public/local V2-13 deployments remain stable. This is not a hardware
handoff or a completed native gameplay test.

## Compatible local native-test emulator

The N64-only test executable is `build/ares-n64-debugger/rundir/bin/ares`, built
from clean `local/ares` revision `af4cbb04f067682a8a3cf42695ff78bed634b38d`.
Executable SHA-256:
`4643dcbfb9ba95b4121e8f1fcb3b578b5f49c02d0835b19bb4a030d19a153c42`.
The build completes and `--version` runs successfully. Native disk launch accepts
`QPassSignals:10`. The runner requires `--ares-debug-settings developer`, because
this build uses `Developer/DebugServerEnabled`, `Developer/DebugServerPort`, and
`Developer/DebugServerUseIPv4` rather than the legacy setting paths.
No system packages, system emulator, user configuration, or saves are changed.

```sh
cmake -S local/ares -B build/ares-n64-debugger -G Ninja \
  -DCMAKE_BUILD_TYPE=Release -DARES_CORES=n64 -DARES_SKIP_DEPS=ON \
  -DARES_ENABLE_LIBRASHADER=OFF -DARES_ENABLE_CHD=OFF
cmake --build build/ares-n64-debugger --parallel 4
```

Use the existing silent, isolated scenario runner and explicitly supply this
binary for the next changed native integration batch. Do not replay exhausted
historical fixtures solely because the tool is now available.
