# NPC letter consumers

## Integration requirement

Snapshot letters are not ordinary text. Their complete decoded body must reach
any grading or quest consumer that reads text, while ordinary/custom letters
retain their correct representation and bounds. The full-window decoder alone
does not satisfy this requirement. Generation remains disabled pending this
work, metadata validation, and semantic template approval.

The similarly named gyroid/demo formatter is separate; neither identified
caller passes a stored letter. See [gyroid display](GYROID_MESSAGE.md).

## Native send and reply path

`mNpc_SendMailtoNpc` at `800A8868` obtains the recipient NPC and sender's memory,
then copies the letter into the NPC's saved mail with `mNpc_Mail2AnimalMail`.
That copy preserves all three text fields and the split/font/paper metadata.
The isolated snapshot-copy tests establish copying, not text interpretation.

At `800A8990..800A89A4`, the send routine obtains the original `Mail_c` pointer,
adds `34`, and calls `mNpc_SetRemailCond` at `800A8814` with that body pointer.
The routine chooses local-town or visiting-player handling. Both call the
ordinary body-only grader at `800A86C4`; local handling also records the letter
date, and a non-neutral result updates reply condition flags. The send routine
uses that result, and whether a gift is attached, to adjust friendship.

The unmodified normal grader calls `mNpc_CheckNormalMail_length` at `800A8614`.
It combines the overlay-based word-hit result, a 96-byte repetition scan, and
non-space length. These operations cannot receive the binary body portion of
a snapshot. Do not recover a whole-record pointer by subtracting an offset
from an arbitrary body pointer without proving every caller's source.

## Letter quest path

Outside the first-job exception, the send routine can call
`mQst_SetReceiveLetter` at `800BBB30`. Its call at `800A8A50` reuses the saved
body pointer and supplies the attached item from `Mail_c+24`.

The quest receiver verifies type/kind/progress and the sender slot, then calls
the rank helper at `800BBAB0`. That helper independently calls
`mNpc_CheckNormalMail_length`, assigns length ranks at seventeen and forty-nine
non-space characters, adds three for any non-bad grade, and adds six for a
gift. The result controls the quest's stored score and reply present.
Updating only the ordinary reply grader would miss this second path.

## English reference distinction

In the supplied GAFE01 release, ordinary NPC reply grading instead calls
`mNpc_CheckNormalMail_nes`, which uses the seven-check
`mMck_check_key_hit_nes` scorer. Scores below fifty are bad, scores of at least
one hundred are good, and intermediate scores are neutral. The checks include
punctuation/capitalization, three-letter matches, repetition, spacing, and long
sentences. The optional English grading patch installs this algorithm for
ordinary ninety-six-byte native bodies, using virtual space padding to the
reference's 192-byte capacity. The complete-body API supports up to 1,024 bytes,
but no snapshot-decoding hook is installed at these body-only consumers.

GAFE01's letter-quest rank helper still calls `mNpc_CheckNormalMail_length`.
It does not use the ordinary reply scorer. The two reference paths must remain
distinct in the port. The optional patch replaces the on-demand word checker
with bounded English tables while preserving its original entry point and
the native quest length/repetition/rank routine. All 776 pairs come from the
hash-verified supplied executable. Per-letter bounds prevent the reference's
unterminated tables from reading into the next table.
Source comments alone do not establish a reported translation crash's cause.
See [English grading](MAIL_GRADING.md) for the implementation and test contract.

## Direct-call inventory

`tools/audit_mail_grading.py` verifies these original-ROM references across all
extracted DMA files:

| Callee | Direct call sites |
| --- | --- |
| Ordinary reply, `800A86C4` | `800A8718`, `800A8770` |
| Length/quest grade, `800A8614` | `800A86D0`, `800BBACC` |
| Overlay word rate, `8009C900` | `800A8634` |

No aligned literal pointers match these three entries. This does not prove
the absence of computed indirect references. The old ordinary grader's call
at `800A86D0` is bypassed when the optional entry hook is installed. The quest
call remains active and distinct. Neither inventory nor ordinary-body grading
authorizes treating snapshot bytes as text or enabling generated delivery.

## Source evidence

The native instructions are in the verified main code's disassembly. Relevant
complete-function SHA-256 values are:

| Native range, hexadecimal | SHA-256 |
| --- | --- |
| `800A8614..800A86C4` | `e0075f0d31071ebd5e785c2b1fed3ad2307dcdd369e84e706c5cb79ea62cd81c` |
| `800A8868..800A8AB4` | `877c0a68c685a594f482316e7661a6964590ef0f38e158a288d6a9ad5dc54f58` |
| `800BBAB0..800BBB30` | `7da416d289504d79101acf3e8e431f22670a71212667279a5578ac22a3a9678d` |
| `800BBB30..800BBBEC` | `2b52dbfc483385643ff223d21499f8729eb81eae4cfdd6e562babc7137afbfef` |

GAFE01 REL function SHA-256 values:

| Function | SHA-256 |
| --- | --- |
| `mNpc_CheckNormalMail_nes` | `dd1cbf5d3b4cce3d377d3bf5dac96cc198b819704470a79f4426a55f95d4f3c4` |
| `mMck_check_key_hit_nes` | `3ec6d296c28c3c4ca680c0a0d85012a4b572fc4b9a19d01f25b7d1f99ebdcb57` |
| `mNpc_CheckNormalMail_length` | `4ce7f8589ecb6bbb79f5a1299a037c818b3767678069a5ebeb811667f82303d6` |
| `mQst_GetMailRank` | `86c1152fa12cf4ddf26fabe4aa907c3f413889f4261bef13cb76ccc2c497dbb8` |

These observations identify required integration points, not an exhaustive
body-pointer inventory or an approval to emit snapshots. All direct/indirect
readers, custom editing, delivery, saving, and hardware validation remain.
