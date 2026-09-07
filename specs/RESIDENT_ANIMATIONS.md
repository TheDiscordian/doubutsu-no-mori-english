# Reviewed resident animation delivery

## Scope

Complete English references may place or repeat ordinary resident expressions
differently from the Japanese text. An individual `resident_animations` approval
permits only NPC0 slot-zero commands, encoded as `7F 09 00 vv vv`, in the native
resident-talk context. It does not permit quest operations, speaker handoffs,
other NPC0 slots, new fields, changed gameplay decisions, or missing wording.

The source record, complete English reference, and final encoded output each
have independently checked hashes. Only `reference_layout` with the verified
resident runtime can use this permission. It cannot combine with choice,
controller, actor-request, added-field, catchphrase, native-alias, or sequence
permissions. The ordinary adapter still restores native demo arguments unless
this explicit permission requests the reviewed English animation sequence.
The builder independently derives permission from the repository, never from
candidate metadata. Ordinary size, field, flow, and formatting guards remain.

## Native consumer

The shared resident overlay is VROM `008681F0`, RAM `809735B0`, with relocation
file `00878550`. Its complete file hash is
`460777a8c6d6b57e9c83a7c9f3efe02593fd01b75f9a4e108db5b9c2a54a18e3`;
the relocation hash is
`177536da108299742fb608a2e8d0a26bef9cd2ecf1f4a18e93213f3a01ecee6c`.
The sections are 58,256 text, 7,808 writable data, 336 read-only data, and 69,488
BSS bytes, with 1,235 relocations. Installation requires the original complete
overlay/relocations and unchanged core order getter, setter, and dispatch bytes.
No production animation code is patched.

Native selector `80976284..809763DC` reads order row four, index zero through
`8007B49C`. Actor `842` supplies the held item; actor byte `92A` is the previous
expression. Six 42-entry signed-word tables supply primary/secondary animation
sequences for empty hands, held fish, and other held items:

| Held state | Primary table | Secondary table |
| --- | --- | --- |
| Empty (`0000`) | `80982B14` | `80982BBC` |
| Fish (`23xx`) | `80982C64` | `80982D0C` |
| Other | `80982DB4` | `80982E5C` |

A new nonzero expression different from the previous value starts its primary
sequence through `809749D0`. Native `FF` selects TALK sequence 21 and sets the
talk flag; other approved expressions clear that flag. A stopped animation can
advance to its secondary sequence. Repeating the same expression while it is
running does not restart it. The consumer clears only its consumed order slot.

The permission accepts existing standing-expression values `01..17` and native
TALK reset `FF`, not zero, later table indices, sitting reset `FE`, or singing
reset `FD`. The native consumer has unchecked indexing outside its explicit
reset branches. These approvals are not a general bounds repair. The GameCube
consumer has a different table length and repeat behaviour; it is a comparison
source, not replacement N64 executable code.

## Native relocation evidence

The independent host relocation model accepts two explicit constants for this
fully hash-verified overlay only:

- `80969690` is the item-table base before adding twice one of the bounded
  `D01E/D03A/D03B/D03C` item IDs. Effective addresses fall within overlay data.
- `80994880` is the exclusive BSS end used by the native two-buffer initializer.

The first constant is below the overlay's nominal start; the second is exactly
its end. Both follow the original loader's relocation behaviour. Ordinary
mail-overlay checks retain their existing rejection of outside pointers; the
shared helper does not generally allow arbitrary relocation targets.

## Approved content

Eighty-three complete references have individual approvals. Eighteen cover resident introductions, the hungry/peaceful/
howling moon conversations, a secret spot, dusk-road fear, the heat challenge,
and an interrupted home visit:

`04D3 04D8 04E3 04EA 04EF 04F0 04F6 04FE 04FF 0519 1EA2 1EDD 1EE7
1F09 1FF5 20AE 20D7 2104`.

The [resident conversation and clothing-errand batch](RESIDENT_CONVERSATIONS.md)
covers the other 65 records. All retain complete supplied English wording and
presentation. Four remove only a redundant pre-field `CUTARTICLE` using the
existing adapter; no English text is removed. A read-only
classification identifies 255 reference-rejection records whose non-expression
signatures agree; this is a review pool, not 255 approved translations. Different
topics, special actors, unapproved values, and other semantic differences still
require review. The long `04F7` introduction uses its separate
[complete linked-record approval](REFERENCE_SEQUENCES.md), not this permission.
Fishing advice `2008` has an original native-complete draft because the reference
omits the final timing instruction.

## Verification and limits

Eight host tests cover exact command scope, value/context/hash guards,
incompatible combined permissions, unchanged adapter defaults, all 83
complete references, actual consumer tables, two relocation bases, unchanged
installed consumers, and independent builder rejection of tampered text.

The silent four-MiB native batch in `build/smoke-resident-animation-01/` passes
213 animation-selection cases, eighteen complete cartridge loads, and 88 actual
NPC0 command dispatches: 322 native calls, 654 assertions, and 1,616 recorded
steps. It runs the actual cartridge overlay loader and independently compares
the complete relocated file and zeroed BSS. Complete actor/order outputs, saved
game data, allocation/stack/module guards, restored code/order pointers, heap
release, and checkpoint restoration pass.

The test temporarily replaces only the animation initializer in its privately
allocated test overlay with a recording boundary. The selector and six tables
remain native. This establishes selected sequence IDs, talk flags, repeat and
secondary behaviour, not actual pose initialization or rendering. Production
code is not instrumented. Normal resident conversation, full animation playback,
human wording/layout review, saving, and hardware compatibility remain separate
acceptance requirements.
