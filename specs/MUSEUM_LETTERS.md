# Complete museum letters

## Source scope

Native introduction `00BD`, non-fossil reply `00BE`, and 25 fossil results
`010E..0126` have complete supplied English header/body/footer parts in both
registered creator catalogues. All 81 parts need no free fields. Preserve exact
wording, manual breaks, punctuation, and fossil descriptions. Reference
availability alone does not credit installed translation.

The original native fossil template table at `8010AE50` agrees with the supplied
GameCube executable's `mail_no_table$449`, including the non-numeric order of
head/body/tail and standalone fossil entries. Its 100 bytes have SHA-256
`d47fbce27270ce235e57caf85fa38b71d2ed287b707c6801ada618107b57e55f`.
Native gifts `1E3C..1E9F` map to the 25 rows by `(gift-1E3C)>>2`; retain all four
native item variants per row. Notices have zero gifts. The GameCube-only donation
reply table `022B..022E` is not part of native N64 selection.

`tools/museum_letters.py` verifies the whole native ROM, supplied English
executable/banks/decoder, seven donor functions/data tables, eight native
functions, the native fossil table, and canonical sender bytes. Every encoded
part equals its immutable catalogue entry and has the exact empty field set.

## Complete creation

`--museum` adds `af_museum_mail_create` around the complete postal/score/advice/
event/departed/Mom/NPC chain. Other requests retain that chain. The new animal
argument descriptor is twelve bytes:

| Offset | Bytes | Value |
| --- | ---: | --- |
| `00` | 4 | ASCII `AFMU` |
| `04` | 2 | Native template, big-endian |
| `06` | 2 | Native gift, big-endian |
| `08` | 1 | Paper 24 |
| `09` | 2 | Zero reserved |
| `0B` | 1 | Marker `F8` |

The player identity is sixteen bytes; remail is null and condition/foreign are
zero. Remail requests delegate before reading the animal argument; unaligned
animal inputs reject before dereference. The shared guard checks output/control/
input/immutable-resource overlap before writes or alleged workspace reads. The
museum's own read-only template map is an extra protected resource.

Bad magic, paper, reserved bytes, flags, notice gifts, fossil bounds, and mismatched
gift/template pairs reject. Full workspace reset, recipient capture, native sender
construction, complete record packing, and full reader reconstruction precede
publication of all 164 destination bytes and final capitalization. Failure leaves
destination and capital untouched. No item-name load, native free-field mutation,
date calculation, or random draw is introduced by the creator.

The sender helper `800A3420` retains the canonical six-byte museum identity,
blank town, native `FFFF` identity words, and sender type two. Do not replace
that internal identity with the English display label or change matching/save
semantics. Font zero, mail type zero, paper 24, and the original gift remain.
The ordinary museum-label display is a separate consumer requiring its own
verified English mapping; canonical saved identity bytes are not literal text
to replace indiscriminately.

The combined image is 32,224 bytes with 464 relocation bytes. Its call allocation
is 38,047 bytes including the unchanged 5,344-byte work and alignment. The museum
dispatcher frame is 56 bytes and the shared guard has an 80-byte frame. The image
retains 544 bytes below the current bound. Resident linked size, reservation,
saved fields, and runtime memory bounds do not grow. An Expansion Pak requirement
is permitted for later implementation if needed.

## Native ownership and receipt

`--english-museum-letters` installs only three guarded ranges:

| Range | Function |
| --- | --- |
| `800A345C..800A34E8`, 140 bytes | Complete creation wrapper |
| `800A3580..800A35B4`, 52 bytes | Home-mailbox publication gate |
| `800A3630..800A3644`, 20 bytes | Queue publication gate |

The wrapper retains `(letter, player, gift, template)` arguments and uses a
48-byte frame. It returns the complete destination pointer or zero, and explicitly
clears `a1` after the resident loader returns. The queue gate uses that documented
zero as the native receipt function's second argument, allowing the failure gate
to fit its original span. Both callers and the wrapper are installed atomically.
The gate's delay slot initializes `v1` on both paths, preserving the original
outer function's return convention. Independent assembly checks this contract.

Home selection, recipient matching, free-slot selection, native mailbox copying,
queue capacity/receipt, original random fossil selection, template selection,
initial-contact flags, wrong-item flags, pending fossil counts, and per-player
three-letter scheduling limit remain in original native code. Existing flag and
count changes already depend on successful receipt. Failed complete creation
skips both copy and queue submission, allowing those native checks to retain
pending work. A later attempt keeps eligibility/count, not necessarily the same
randomly selected fossil. Normal save/reload and scheduling require native and
gameplay acceptance; they are not inferred from pure creator tests.

## Validation

Required checks include complete creation in both capital states for both notices
and all 100 fossil item variants, rejected descriptors and overlapping inputs,
every catalogue-read failure, resource retry, and unchanged earlier dispatchers.
Installer tests cover native/source guards, exact three owned ranges, atomic
rejection, compiled source/variant binding, whole-ROM resource/text preservation,
and correct combined translation credit. Native tests must compare original
metadata and RNG, reconstruct every delivered template, exercise real home/queue
success/failure and pending flag/count loops, and restore isolated state and guards.
Original hardware and human playthrough remain explicit broader requirements.

The [installed checkpoint](../docs/checkpoints/MUSEUM_LETTERS.md) records passing
host/sanitizer/installer/regression checks and a completed silent native batch:
54 original comparisons and home deliveries, 75 full readbacks, five fallback
cases, twenty pending-notice/fossil cases, 313 calls, and 666 assertions. Restored
state/checkpoint and blank isolated saves pass. Deliberately mismatched initial
house selection exercises fallback receipt; it is not ordinary scheduling proof.
