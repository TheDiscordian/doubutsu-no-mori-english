# Complete Mom letters

## Installed scope

`build_npc_mail_capture.py --mother-letters` builds the optional system creator.
The ROM builder's `--english-mother-letters` installs complete supported Mom
creation and failure-aware publication. It requires that creator, the existing
resident loader, immutable catalogue two, and the complete snapshot reader.
Ordinary NPC replies continue through the unchanged original creator.

The native selectors reach 114 classic IDs: `012C..0181`, `0184..0185`, and
`018A..01A3`. These cover everyday, matching-day, seasonal-event, birthday, and
monthly letters. Native monthly selection retains its original repeated IDs
and August choices. GameCube-only Christmas selectors `0182..0183` are not added
as N64 events. Gifts, stationery selection, recipients, RNG, and scheduling
remain native operations.

113 complete letters are available. Body `mail:0136` requires a semicolon glyph
absent from the mail font and remains unavailable. Its source wording must not
be shortened or have punctuation substituted to manufacture completion. Other
parts of this unavailable letter do not count as a completed Mom letter.

`tools/mother_letters.py` verifies the native selector/creator/scheduler bodies,
the supplied English executable's corresponding functions, full text-bank hashes,
and all 342 selected header/body/footer parts. Every available part must equal
the complete donor transcoding and have no free-string fields. Catalogue-only
presence is insufficient to establish an installed translation.

## Runtime contract

The resident six-argument loader and 5,344-byte workspace remain unchanged.
The optional `af_system_mail_create` entry recognises a synchronous twelve-byte
descriptor in the existing animal argument slot:

| Offset | Value |
| --- | --- |
| 0..3 | `AFMO` |
| 4..5 | Selected classic template, big-endian |
| 6..7 | Native selected gift, big-endian |
| 8 | Paper ID, 0..63 |
| 9..10 | Zero |
| 11 | `FE`, outside native personality range 0..5 |

The player argument is the unchanged sixteen-byte recipient identity. Visitor
reply, condition, and origin arguments must be zero. The descriptor lives only
on the wrapper stack during the call; no pointer is saved or retained.

Input/output overlap checks precede marker reads, including pointers into the
smaller session/capital control objects. Complete text generation happens in
private staging, with no active NPC capture callback. Only successful formatting
copies all 164 bytes to the destination and updates shared capitalization.
Received metadata matches Mom's native clear/recipient/gift/type/paper operation:
font zero, type four, invalid empty sender, original gift and paper. The saved
split marker and 122-byte text area carry the existing snapshot format.

The same resident allocator, synchronous DMA, approved checksum, original
relocation, cache maintenance, and free routines load both creator variants.
Legacy creator source inventories and binaries remain valid. The system image
has no writable/BSS section. No resident code or saved structure is enlarged.

## Native entry and delivery gates

The 128-byte creator at `800B8FB8` is replaced in place. Its 48-byte stack frame
holds the descriptor and forwards the original five-argument request through
the six-argument loader. Invalid full-width template and paper arguments reject
before narrowing. The loader returns the complete destination pointer or zero.

`800B9038..800B9170` retains native recipient eligibility, player-to-home mapping,
first-free mailbox selection, and queue policy. The mailbox gate at `800B90DC`
and queue gate at `800B9148` branch to the original zero-result epilogue when
creation fails. No stale staging record is copied or submitted. The mailbox
copy still uses the native 164-byte copy helper.

The queue policy rejects a recipient whose home is full, even if queue capacity
remains. This is existing native behaviour, not a successful queue-delivery claim.
The installed gates propagate failure without changing that policy.

The original date caller renews its sent date only on successful publication.
Monthly/normal sent bits likewise follow successful publication, but the native
normal scheduler still updates its checked date on a failed attempt. This patch
does not add persistent retry selections or claim delivery retries across days.
Saved-record layout is unchanged; compatibility acceptance remains required.

## Verification and remaining acceptance

Host tests compare complete snapshots, all metadata, reconstructed English text,
and final capitalization for every supported letter in both initial states.
The entire existing ordinary NPC creator contract also runs through the system
dispatcher. Invalid descriptors, unavailable text, every catalogue-read failure,
disabled resources, output guards, and input/control aliases must retain outputs.

`check_mother_assembly.py` independently assembles the creator and both gates
with the pinned Docker VR4300 toolchain. Installer tests bind optional exports,
preserve legacy artifacts, reject incomplete dependencies atomically, and check
the completed ROM. Native batch evidence belongs in the
[integration checkpoint](../docs/checkpoints/MOTHER_LETTERS.md).

Normal scheduling, dates across saving/reloading, human playthrough, old-save
policy, and original hardware are not established by direct creator/post calls.
The missing semicolon remains a translation requirement.
