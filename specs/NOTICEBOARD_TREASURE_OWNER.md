# Transactional treasure-post ownership

The native scheduler keeps its eligibility checks, item selection, acre/unit RNG,
animal selection, template selection, and RTC capture. Two calls enter the existing
on-demand creator loader. No saved structure or resident allocation grows.

## Native bridge and lifetime

`overlays/notice/treasure_owner.s` replaces the treasure-only 176-byte field helper
at `800A5E58..800A5F08`. It contains 168 instruction bytes and eight zero padding
bytes. The town helper remains intact because seasonal notices also call it.

| Native address | Operation |
| --- | --- |
| `800A6170` | Load phase one before original burial |
| `800A6214` | Remove obsolete Japanese free-field preparation |
| `800A62A0` | Load phase two after original animal/template/RTC selection |
| `800A62A8..800A62C0` | Remove duplicate publication/timestamp writes; the owner performs them only on success |
| `8008EA8C` | Forward the placement callback in the incoming fourth-argument home slot |
| `8008EC44` | Forward six original deposit arguments and the seventh context argument |

The bridge allocates 224 stack bytes. Loader output occupies `20..C3`, and the
twelve-byte request occupies `C8..D3`; saved return is at `DC`. The request is
`AFNR`, BE32 parent-frame address, phase `1/2`, two zeros, and marker `244`.
The return address distinguishes the two guarded native callers. The coordinator
checks the exact request/destination/parent relationship before reading the parent.

The original parent frame remains 352 bytes. Its post is at `68`, timestamp at
`C8`, selected item at `66`, column at `60`, row at `5C`, and template at `10`.
Its original candidate-animal list at `FC` and current RTC at `140` are retained.
Only the first 96 loader-output bytes are copied into the post; copying all 164
would overwrite parent state. No text buffer is silently enlarged or truncated.

The stack-only undo record at parent `D0..DF` contains:

| Offset | Meaning |
| --- | --- |
| `0..3` | Native foreground halfword address |
| `4..7` | Native buried-row halfword address |
| `8..9` | Original foreground value |
| `10..11` | Original buried-row value |
| `12..13` | Placed foreground value |
| `14..15` | `4E54` marker |

The record survives freeing the phase-one image and work. Any phase-two failure,
including failure before its image executes, reaches the fixed bridge's two
halfword stores and restores burial. No second allocation or cartridge read is
needed for undo. The original native game thread owns this synchronous operation;
the undo record is not a persistent queue or a cross-thread save protocol.

## Phase one: exact original burial

`af_notice_owner_create` uses 544 bytes of the existing generation workspace's
character representation for the selected acre's 512 foreground bytes and 32
buried-flag bytes. It does not cast that object to an incompatible structure.
The text generator resets the workspace before typed catalogue use resumes.

The original `8008EA5C` selects the acre. Its extra callback/context arguments
exist only on this guarded call chain; the original native direct-call inventory
finds no other caller. The forwarding thunk preserves all six deposit arguments,
the native saved registers, and return at `8008EC4C`. The callback validates the
acre pointers/count, snapshots them, and calls the unchanged deposit function
at `800A3E34` exactly once.

Success requires exactly one previously empty foreground cell to change. Ordinary
treasure must produce the selected item and only OR its own buried flag. Pitfall
`2512` must produce `002A..0042` without changing buried flags. The guarded native
hole selector `80072610..800727D8` returns `0..24` or `-1`; its SHA-256 is
`f4d337b99523a97c1d805a83bdfb51a0dd33f2792fa08d2ae3d2fdfed152c9b8`.

No-change deposit, unexpected edits, repeated callback, or inconsistent placement
result restores the full selected-acre snapshot before returning failure. This
also handles the original placement function reporting success after a pitfall
deposit finds no usable hole shape. Successful placement writes the bounded undo
record and returns through the loader. Allocation/read failure before phase one
executes never calls the burial function.

## Phase two: full English creation and publication

The coordinator validates undo against the original coordinates, item, current
map cell, and current flags. It constructs the text creator's `AFNT` request using
the original native `s6` animal, template, item, and coordinates. The real complete
creator verifies names, articles, source bodies, and compact decoding. Failure
leaves the draft, board, and buried timestamp unchanged for bridge cleanup.

After complete creation, the coordinator copies exactly 96 bytes to the parent
post, calls original writer `800A5D30`, and copies the captured RTC to `8013673C`
with original helper `800D5D6C`. No resource read or allocation follows publication.
The original writer retains its existing full-board shift policy.

## Compiled evidence and integration boundary

`tools/notice_treasure_owner.py` compares assembly with an independent complete
44-word encoding, verifies native function hashes, and constructs only the listed
patches. It rejects duplicate installation, changed instructions, unknown loader
addresses, and forged self-checksums. Independent native bridge and creator builds
agree. The creator is 48,752 bytes plus 752 relocation bytes, with the unchanged
5,344-byte workspace: the loader requests 54,863 bytes including alignment slack.
Compiler stack frames are 96 bytes for the coordinator and 48 for its callback;
these are not a measured complete native gameplay stack bound.

Host tests cover thirty acres, all 256 unit positions, all 25 pitfall shapes,
existing flag bits, exact undo, failed/malformed deposits, and all eighteen full
bodies in both capitals with ordinary items and pitfalls. The complete earlier
creator chain also passes through the new dispatcher. Sanitizer tests pass.
Five artifact tests verify independent builds, all bridge words, unchanged native
code outside the intended intervals, and retained verification of older creators.
The current playable ROM's main code also accepts guarded patch construction.

These are compiled/host results, not executed native ownership. The actual ROM at
`build/notice-treasure-pilot` installs the `--notice-owner` creator, a complete
treasure reader, and the native bridges together. The full builder and independent
verifier require the real configured creator, matching article/name resource,
reader profile, and every guarded native interval. ROM/UPS and combined accounting
checks pass. See [reader installation](NOTICEBOARD_TREASURE_READER.md).

Execute a bounded native batch for real placement, loader failures, rollback,
posting, reading, heap/stack state, and scheduling eligibility. Save/reload, old
saved automatic posts, ordinary gameplay, and hardware acceptance remain.
Do not replay passed initial-post batches.
