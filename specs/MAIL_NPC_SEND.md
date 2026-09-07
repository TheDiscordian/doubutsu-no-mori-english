# Complete-letter NPC send integration

## Activation and scope

Combining `--english-mail-snapshots` and `--english-mail-grading` installs
whole-record NPC send handling. The registered catalog and English scoring
overlay are required. Native snapshot generation remains disabled. Template
identity review, other metadata/readers, lossless editing, full post-office
gameplay, actual saving, and hardware compatibility remain separate requirements.

The native 164-byte `Mail_c` retains its alignment, lifetime, identities, gift,
stationery, and saved layout. The wrapper receives that complete record. It
never infers a header by subtracting from an arbitrary body pointer.

## Decode before native mutation

The guarded entry at `800A8868` dispatches to `af_mail_send_npc`. Untagged mail
uses the original routine. Tagged mail requires a used font, validated immutable
snapshot/catalog, complete assembly, and successful ordinary and legacy grades.
Invalid records, unavailable rows, DMA rejection, and either allocation failure
return zero before the native send routine changes NPC or quest state.

A 4,607-byte allocation holds the 4,592-byte workspace/full letter plus alignment
room. The complete body reaches both scoring paths: the seven-rule ordinary
scorer and the distinct legacy length/repetition/word-rate scorer. The latter
retains native repetition counters and counts every non-space byte. Two calls
use the existing on-demand overlay entries. Peak requested temporary storage is
11,007 bytes, excluding allocator bookkeeping and rounding. All decode storage
is freed before native sending begins; no source byte is changed.

## Scoped ownership and original functions

A sixteen-byte stack context holds the exact source body pointer, ordinary
rank, legacy rank, and non-space count. One four-byte resident pointer publishes
it only during that synchronous native send. Decoding/DMA finish first. The
prior pointer is restored afterwards, including nested calls.

The ordinary grader and the entry at `800A8614` use prepared values only for
an exact body-pointer match. Other bodies follow their ordinary paths. Opaque
snapshot bytes do not enter the original word/repetition scans during this send.
The original local/visitor reply, date, quest eligibility, gift selection,
first-job, and friendship code remains in use.

Two sixteen-byte trampolines preserve each displaced stack adjustment and
return-address store, then resume after the original first two instructions.
The direct-call inventory includes one post-office send caller (`800B69B4`),
one reply-dispatch caller, one caller for each local/visitor helper, and one
quest-receiver caller. No aligned literal pointers match these five entries
or the three grading entries. Computed-pointer absence is not proven by that
inventory alone.

## Post-office failure handling

The original receipt checker at `800B690C` ignores NPC sending's return, clears
the source at `800B69BC`, increments the NPC-mail counter, and reports success.
Rejected snapshots must not be discarded this way.

A guarded twenty-four-byte call-site shim replaces that clear call. Success
tail-calls the original clear routine and resumes the original counter update.
Failure jumps to the verified containing-function epilogue at `800B6A24` with
zero in `v1`, retaining both the letter and counter. The epilogue restores its
original stack and saved registers. Player and museum paths remain unchanged.
The public receipt entry at `800B6A3C`, send type zero, forwards this result;
other receipt modes and the full Pelly interaction still need gameplay checks.

The native receipt-function SHA-256 is
`469d58f3b17f22a970ee84225b883080c7afea34edf54e7f7ebf97d32f9e4da8`.
Installation checks complete source hashes, instruction/argument sequences,
all trampoline/shim bytes, target bounds, required grading support, and patch
overlaps before publishing any changed code.

## Memory and validation contract

The resident module uses 24,256 bytes of its unchanged 32 KiB reservation.
Only 320 bytes remain before the final 8 KiB native-test area. Compiler stack
frames are: send wrapper 96 bytes, restoration 256, formatting 1,224, expansion
64, and unpacking 408. Unpacking finishes before formatting. These individual
frames do not establish a whole-game maximum; native tests also check a guard
3,072 bytes below the test stack.

Host tests cover all 6,398 reference assembly cases and both capitalization
states, exact complete-body scores/counts, source/allocator guards, ordinary
fallback, nested context restoration, unrelated-body exclusion, malformed data,
each selected catalog DMA failure, and failure of the second grader allocation.
The width-ten `0001` case remains a formatter fixture, not an approval of its
actual generation bounds.

Native tests start from a matching-ROM town checkpoint and use controlled NPC
memory. They clear the first-job event only inside the isolated test, then
restore the complete machine; normal introductory work is not completed by
that fixture. Cases cover both record kinds, all ordinary reply ranks, local
and visitor handling, quests/gifts, ordinary fallback, rejected records,
complete source/compact-letter contents, affected and unrelated NPC/player
state, date/flags, friendship, quest ranks, and stack/module guards. The original
random prize function executes; its selected item is recorded, not predicted
with another random draw.

Post-office cases call the public receipt function and check exact source
clearing/retention, counters, and failure propagation. These are native in-memory
integration tests, not normal post-office UI or FlashRAM-save tests. Exact runs
and hashes belong in the work log; release compatibility remains unproven.
