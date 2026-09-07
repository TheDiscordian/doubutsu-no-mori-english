# Whole-letter generation transaction

## Implementation state

`overlays/mail_generation/generate.c` implements transient field capture and
complete generated-letter publication using the existing immutable cartridge
catalog and snapshot format. It is separate from the resident module: the
current resident image has only 96 bytes of linked-code headroom. The generation
code is compiled and loaded into private heap memory for isolated native tests.
It is not yet installed as an on-demand gameplay overlay or a native creator
hook. Ordinary gameplay generation remains disabled.

Connecting this transaction to the actual N64 creators, complete English field
sources, approved semantic template mappings, allocation lifetime, and failure
propagation remains required. A successful isolated API call is not an English
letter delivered through normal gameplay.

## Captured fields

`AfMailCapture` is a caller-owned, 368-byte transient structure: a twenty-bit
valid mask, an explicit capitalization state, and twenty eighteen-byte fields.
Each field retains its zero-to-sixteen-byte value and article. Reset clears
the entire structure. Setting a field copies the value immediately, including
leading/embedded/trailing spaces, and clears unused field bytes. The source may
overlap the field being replaced because publication follows staging.

The setter rejects oversized values, invalid articles, missing nonempty input,
and command/extended-glyph bytes. A rejected replacement of a valid slot clears
that slot's valid bit, preventing reuse of its old value. Other slots and the
capitalization state remain unchanged. Out-of-range indices are rejected without
modifying a different slot. Callers must check all returns and must not silently
truncate a source before passing it to this API.

This is not a replacement for native saved player names or arbitrary user text.
Native identities retain their existing formats. Wider display values and
random-word references must be resolved from approved sources when captured,
not reconstructed from current world state when an old letter is read.

## Transaction and publication

`AfMailSelection` names immutable catalog parts, not native numeric IDs. Classic
selection has one ID; composite selection has five. Semantic correspondence is
an independent caller requirement. Sharing an ID number between games does not
approve a translation.

Generation validates the catalog header and selected row indices and gathers
their required-field mask. Only those fields are packed into the snapshot;
unrelated values retained by earlier native operations do not consume its
122-byte capacity. Row masks are only preparation hints. Before publishing,
the existing resident restoration path independently checks directories,
complete selected payloads, CRCs, actual command-derived masks, padding, glyphs,
controls, full formatting, and output limits.

The caller supplies one exact 164-byte letter and a separate, sixteen-byte-aligned
4,720-byte native workspace. The workspace contains the catalog scratch area,
complete formatted output, and staged wire bytes. Letter, capture, selection,
and workspace must not overlap. Invalid sizes, alignments, and overlaps are
rejected before cartridge reads or destination writes.

On success only the letter's split byte at `27` hexadecimal and text at `2A`
change. The split becomes the experimental snapshot marker `80`; all 122 text
bytes receive the validated envelope. Identities, gift, font/status, type, and
paper remain unchanged. The capture's capitalization state advances only after
successful complete formatting and publication. On rejection, the entire letter
and capture remain unchanged; the workspace is disposable scratch.

The transaction does not issue a random selection, regenerate a name, reflow a
line, remove an explicit space, or shorten a letter. It rejects unavailable
glyph rows and storage overflow instead of accepting partial English output.

## Native creator boundaries

The native free-string setter at `80092D10` stores twenty ten-byte rows beginning
at `80140680`. It clamps source lengths to ten and pads with spaces. Capturing
only its resulting table cannot recover a longer English name or phrase after
that clamp. Wider source capture must occur before truncation.

The generic classic loader at `80093F04` takes separate header, split-output,
footer, and body pointers. Not every caller supplies contiguous fields. For
example, `mNpc_GetHandbillz` at `800A8B84` stages its header at `80142CF0` with
twenty bytes and footer at `80142E38` with twenty-six bytes, while its body is
already at the final letter's `+34`. After composite assembly at `800A8BE8`,
the wrapper copies ten and sixteen bytes into the final record and writes its
split. Hooking only the lower-level composite assembler would leave those
later copies capable of overwriting a snapshot.

The NPC free-string preparation at `800A8C48` captures player/NPC/town fields
and selects eleven random general strings before assembly. The selected random
IDs and complete English replacements must be captured at this stage; the
generation transaction must not make new random choices. All addresses in this
section are native linked addresses inspected against the original ROM, not
live overlay addresses or implemented production hooks.

## Verification and integration queue

Host tests cover all 6,398 supported reference assembly cases, checking complete
wire output, metadata retention, complete formatted text, and final capitalization.
Unused fields are deliberately populated to verify pruning. Additional cases
cover every slot/length/article, aliased capture input, rejected replacement,
missing fields, actual ten-field overflow, unavailable parts, invalid selection,
every cartridge-read failure, altered selected metadata, disabled resources,
alignment, overlapping objects, and unchanged destinations on failure.

`build_mail_generation.py` cross-compiles original code for VR4300/o32 with the
existing pinned Docker toolchain. The probe rejects mutable/global data,
unresolved imports, oversized code, untracked jumps, and unsupported relocation
types. MIPS compile-time assertions pin all native structure sizes. The probe
imports only the verified resident pack, restore, and catalog-header functions;
its cartridge access uses the original native DMA service.

`mail_generate_test_scenario.py` and `mail_generate_smoke.py` exercise generation
in a fresh silent process with caller-owned heap fixtures, module/stack/allocation
guards, complete live-save retention, allocation free, and checkpoint restoration.
Exact native outcomes and build hashes belong in the work log.
The native run passes 53 generation cases, 42 capture cases, complete reset,
and disabled-resource rejection across 99 calls and 719 memory assertions.
Six loader tests cover the original synthetic relocation fixture and current
native artifact, including source/build/import changes, incomplete jump lists,
invalid destinations, alignment, and four-MiB bounds.

Remaining work:

1. Finish complete-letter creator and field-source bindings, including native
   status assignments and noncontiguous temporary destinations.
2. Approve native/reference template identities, translate unresolved fields,
   and handle the missing glyph rows without reusing a catalog identity.
3. Install bounded on-demand loading and durable transient capture ownership;
   propagate generation failures without sending partial or stale letters.
4. Validate creator-to-viewer/delivery flows, parent-menu interaction, custom
   editing, normal saving/travel, old-save policy, and original hardware.

The portable ten-field overflow case is classic `0001` with fields ten through
nineteen, each sixteen bytes. Actual source bounds for that template still need
review; this deliberate overflow is not evidence that its normal use overflows.
