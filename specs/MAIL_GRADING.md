# English NPC letter grading

## Scope and activation

`--english-mail-grading <directory>` installs the English ordinary-reply scorer
and the bounded English word-prefix checker used by the separate letter-quest
path. It requires a matching resident module and source-verified overlay build.
The native ordinary grader at `800A86C4` receives a guarded entry jump; its
callers and the quest rank helper retain their original control flow.

Ordinary/custom native bodies remain ninety-six bytes. The scorer virtually
pads short inputs to 192 bytes with spaces, matching the GameCube capacity without
reading beyond native storage. A separate complete-body API accepts up to
1,024 bytes. Inputs longer than 192 bytes retain their supplied capacity;
this is a bounded extension, not an existing GameCube storage format.

These APIs receive ordinary text only. A binary snapshot must first be decoded
from a proven whole-record pointer. No such hook is installed here, and native
snapshot generation remains disabled. Ordinary delivery, visitor memory,
friendship outcomes, lossless editing, actual saves, and hardware need separate
validation. See [native consumers](MAIL_NPC.md).

## Ordinary reply rules

The port follows the supplied GAFE01 seven-component scorer, preserving its
unusual details. Spaces are byte `20`; punctuation is `.?!`; prefix separators
also include comma, `85`, and newline `CD`.

| Component | Rule |
| --- | --- |
| A | Twenty points for final punctuation when trimmed length is below capacity; then plus/minus ten for an uppercase byte within three positions after punctuation |
| B | Three points per recognised three-byte prefix at the reference's candidate positions |
| C | First non-space byte uppercase: twenty; otherwise minus ten; empty: zero |
| D | Minus fifty for three identical consecutive alphabetic bytes, case-sensitive |
| E | Twenty when spaces/non-spaces is at least one fifth; otherwise minus twenty |
| F | Minus 150 for the reference's 75-byte non-punctuation run after punctuation, entered only with more than 76 bytes remaining |
| G | Minus twenty per complete, fixed 32-byte block without a space |

Total below fifty returns bad (`0`); fifty through ninety-nine returns neutral
(`2`); one hundred or more returns good (`1`). Complete empty input is handled
without the reference's preceding-byte read. Wider searches do not wrap at an
eight-bit index boundary. No text, spacing, punctuation, or newline is changed.

The older word-rate entry preserves its distinct final-index trimming and
candidate-count semantics. The native quest grader retains its repetition,
length, rate, gift, and rank calculations; it does not use the seven-rule score.

## Prefix data

The builder verifies the complete English REL and symbol file before extracting
all twenty-six `str_*_table` symbols. Their 776 two-byte suffix pairs follow
twenty-seven big-endian sixteen-bit cumulative pair offsets: 1,606 bytes total.
Runtime lookup validates every offset and searches only the selected letter's
interval. Only the first letter permits either case; the following pair matches
exactly. Extracted tables stay in ignored build outputs, not committed source.

This bounded representation intentionally excludes retail table spillover.
The pinned reference's `BUGFIXES` configuration still leaves the `x` table
unterminated, so the independent host reference fixture adds that one terminator
as well. Original retail overreads are not expected scoring behaviour and are
not reproduced. This observation does not identify the legacy patch's reported
crash cause.

## On-demand overlay ABI and memory

The original mail-check DMA allocations remain unchanged: 5,808 bytes at VROM
`00954D30` plus a 592-byte relocation file at `009563E0`. Linked RAM is
`80A94AC0`. Code and read-only data occupy 4,064 bytes, with no BSS.

| Overlay offset | Contract |
| --- | --- |
| `000` | Jump to full scorer: `(AfMailGrade *, body, size)` |
| `008` | Jump to word rate: `(int *words, body, size)` |
| `010` | Four words: `AFMG`, ABI `1`, native capacity `96`, maximum `1024` |
| `24C` | Original two-argument word-rate entry, native capacity `96` |

`AfMailGrade` is thirty-six bytes: seven signed components, signed total, and
unsigned rank. Outputs require natural alignment and must not overlap the
input body. Invalid bounds, null pointers, or invalid table offsets leave the
output unchanged. Word-rate errors return `-1`; full-grade errors return zero.

The resident loader requests one checked 6,400-byte allocation, supplies the
final 592 bytes as relocation workspace to native `ovlmgr_LoadImpl`, checks
the loaded ABI, invokes the scorer, and frees the allocation. Allocation failure
or an absent English overlay returns failure; the ordinary adapter returns
neutral. Native DMA, relocation, and instruction/data-cache maintenance remain
in use. The old quest word-rate loader remains unchanged, including its original
allocation behaviour; this patch does not claim to harden that allocator path.

Resident code occupies 23,424 bytes, including the 320-byte loader/adapter
addition. The 32 KiB reservation, heap start, and final 8 KiB test area are
unchanged. The main scoring function has an eighty-byte compiler stack frame;
its callees use additional small frames. Native tests check stack guards.

## Build and relocation guards

The provided pinned Fado sources generate relocations locally. No tool source
is modified or installed system-wide. MIPS compilation runs in the existing
pinned Docker toolchain with both `-mno-explicit-relocs` and
`-mno-split-addresses`, plus `-fno-merge-constants`. The linker aligns each
input object's sections to sixteen bytes, matching Fado's layout.

Twenty-four relocation entries occupy 128 bytes before padding. Only
text-section jump and paired high/low-address relocations are accepted. The
validator checks section sizes, padding, order, instruction forms, targets,
paired addresses, all three entry jumps, and four-MiB placement. Native DMA
sizes and the trailing relocation-size word remain consistent. The guard is
specific to this generated overlay, not a general ELF relocation interpreter.

Installation checks original ROM/overlay/function hashes, current source
hashes, generated artifact hashes, the module identity, ABI, linked target
bounds, and overlapping patch entries before publishing replacement data.
The default build does not enable English grading without its explicit option.

## Validation

Host tests cover all 776 prefix pairs, case rules, all seven components, exact
49/50/99/100 thresholds, empty input, 192-byte virtual padding, maximum-size
inputs, invalid arguments, output/source guards, and allocation ownership.
One thousand varied-length cases agree with the independent Python model.
Three thousand cases agree with pinned GameCube C component and legacy-grade
functions, using bounded tables and a host-pointer portability adjustment.
These tests execute the reference C on the host, not on a GameCube CPU.

AddressSanitizer and UndefinedBehaviourSanitizer execute eight patterns at
every length from zero through 1,024 using exact-sized heap inputs. Relocation
and installer mutation tests reject missing/invalid entries, stale data,
wrong sources, altered ABI, unbounded module targets, and overlaps without
partially publishing a patch.

The N64 scenario passes ninety-one actual CPU calls and 157 memory assertions:
installed ordinary entry, complete-body loader, original overlay loader,
native length grader, quest rank helper with/without gifts, and local reply
flags. All source, stack, and module guards remain intact. Isolated fixtures
and a restored emulator checkpoint do not establish delivery or saving.
The combined ROM passes the full train-to-town regression and all six long
letter-reader probes. Exact results and hashes are in the work log.
