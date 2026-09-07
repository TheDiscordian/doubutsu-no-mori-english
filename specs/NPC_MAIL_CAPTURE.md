# Scoped capture beside original NPC reply creation

## Integration design

Keep the native good/bad creators, metadata setup, gift selection, RNG calls,
and sixteen-bit identities. The original preparation still performs every
native name lookup, other-villager selection, string load, and ten-byte setter.
Resident adapters capture complete sources beside those calls rather than
regenerating selections or depending on already shortened temporary text.

An outer creator owns the entire session, on-demand code/resources, temporary
164-byte letter, and generation workspace. It calls the original metadata
routine with its private letter, then validates the captured parts and generates
the complete snapshot. Only successful whole-letter generation copies all 164
bytes to the caller's staging record. A failure publishes nothing and returns
zero through the tested submission gate. The [whole-creator transaction](NPC_MAIL_CREATOR.md)
implements private staging and publication. Its resident cartridge loader and
gameplay installation remain required; the capture code alone installs no hooks.

The session prefix is 32 bytes on N64: an event callback, the private stage
pointer, player/animal/foreign-reply pointers, original condition/origin values,
and initial capitalization. All callback code and borrowed resource storage
remain allocated throughout the synchronous call. No pointer escapes into a
saved letter. The sole resident global is a four-byte active-session pointer.
When no session is active, adapters forward the unchanged native arguments and
results without capturing or changing text handling.

## Guarded call sites

| Original call | Native target | Resident adapter |
| --- | --- | --- |
| `800A8E48`, `800A8F6C` | `800A8C48`, field preparation | `af_npc_mail_prepare` |
| `800A8C90` | `800ACD18`, sender name | `af_npc_mail_sender_name` |
| `800A8CB8`, `800A8CF8` | `800ACD18`, selected other name | `af_npc_mail_other_name` |
| `800A8D70` | `800C3F70`, selected word loader | `af_npc_mail_word` |
| `800A8F0C` | `800A8B84`, complete composite wrapper | `af_npc_mail_composite` |
| `800A8FD8` | `80093F04`, classic loader | `af_npc_mail_classic` |

All eight call sites require complete original-function guards and unchanged
delay slots before installation. No hook replaces the original native function
entry. Thus an inactive adapter can call the original without recursion.

During an active session, the two assembly adapters record the already selected
IDs and skip the old bounded text assembler. Native gift/status/identity/paper
writes continue on the private stage. The bad creator still copies its old
temporary header/footer into that stage; the final complete snapshot replaces
all 122 text bytes. Its stack split output is explicitly initialized to zero,
so no uninitialized split is read. A failed final transaction never publishes
those temporary bytes or the prior global staging letter.

## Complete sources and ownership

`npc_capture.c` checks the complete SHA-256 of both prepared resources before
publishing borrowed source pointers. The fixed approved digests cover all
11,328 word-resource bytes and all 6,368 alias-resource bytes, not just their
embedded header digests. Source storage stays immutable until session teardown.
Failed initialization leaves the descriptor unchanged; the caller must check
the return and must not continue with an older descriptor after failure.

Word lookup retains the native-selected slot and ID. It preserves the full
phrase and space-pads its captured value to sixteen bytes, matching the English
string-loader temporary passed to the handbill setter. This is distinct from
the resource's compact literal length. Formatting alone omits trailing padding;
the snapshot retains the captured bytes. Names retain their full eight-byte
English values, while saved player/town fields remain six bytes. Unknown saved
NPC names and unsupported NPC IDs fail capture rather than guessing a prefix.

The digest implementation is original freestanding C used for resource integrity,
not a cryptographic service. It accepts bounded whole inputs up to one MiB,
handles unaligned source bytes, rejects overlapping input/output, and has no
mutable global state. Host tests compare its complete output with `hashlib` at
every short padding boundary and at actual resource and larger input sizes.

## Event order and rejection

The callback requires fresh state before preparation, original player/animal/
foreign-reply pointer agreement, valid condition/origin/capitalization values,
and validated sources. It resets all twenty captured slots and preserves the
explicit initial capital state. Foreign sender aliases and both town names are
captured from their saved values, not current-world name guesses.

Local preparation captures sender then selected-other identity; foreign
preparation captures only the selected local-other identity after saved-sender
recovery. Both paths then require exactly eleven word events in native family
order. Each full-word lookup checks that family's original 32-entry ID range.
Preparation must finish with exactly the expected local or foreign field mask.

Only completed preparation may select one classic record or five composite
parts. The original condition, origin, and personality constrain the selected
ID ranges. Repeated selection, stale phases, wrong stage pointers, unsupported
IDs, reordered/missing names or words, and incomplete capture set a sticky
session failure. Generation requires final phase three and failure zero.
Range validation is not semantic approval of every native/reference template.

## Remaining acceptance

The resident forwarding adapters and complete-source callback are implemented.
Twelve host tests cover full sources, event ordering, original temporary-field
retention, complete selected IDs, inactive forwarding, relocation validation,
and exact guarded call sites. The 24,176-byte image, including the whole creator,
contains 6,064 bytes
of code and 18,112 read-only bytes; no writable/BSS section is required. Its
208-byte relocation section has 45 entries, independently compared with the
linked ELF inventory. Including capture adapters and the cartridge loader, the
resident module leaves 1,856 bytes inside the unchanged linked-code limit.

The native harness uses the original relocation routine followed by the original
data-cache writeback and instruction-cache invalidation routines. Complete
debugger-visible relocated contents alone do not establish executable cache
coherence. Runtime changes to guarded native call sites require the same cache
maintenance before execution. Source resources remain immutable after validation.
The harness completes original creator baselines before installing capture hooks;
it never substitutes a random selector, metadata writer, gift picker, or native
word loader. Full save and source comparisons, original-instruction restoration,
allocation free, and complete checkpoint restoration are required acceptance.

All 48 native creator comparisons pass: local and visitor replies, good and bad
conditions, all six personalities, and both initial capital states. Each original
creator and captured creator starts from the same seed and has identical final
RNG state, native ten-byte fields, gift, identities, status, type, and stationery.
Thirteen original gifts are retained. Every captured field is checked against
the complete approved English source and its corresponding native temporary;
all 48 selected letters generate complete matching English text. This sample
does not select the unavailable footer and is not semantic approval of all
possible letter combinations.

The run passes 197 native calls and 721 memory assertions across 1,813 recorded
steps. It includes native source-hash rejection, family-boundary word lookups,
complete saved-name recovery, unknown-alias rejection, complete save retention,
instruction/global restoration, heap/stack/module guards, allocation free, and
checkpoint restoration. FlashRAM stays blank and the Controller Pak unchanged.
The image is loaded through isolated debugger fixture writes; actual cartridge
loading and ordinary delivery are not exercised.

The [resident loader](NPC_MAIL_LOADER.md) supplies optional guarded installation,
cartridge loading, allocation ownership, and shared capitalization. Its native
cartridge test passes complete creations, heap cleanup, and failure retention.
The pending-reply loop and normal delivery remain follow-up checks. The font, saved
formats, template wording, reference layout, and RNG algorithms are unchanged.
