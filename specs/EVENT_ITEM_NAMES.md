# Complete event and home item names

Seven native item-to-message sequences use the existing zero-safe sixteen-byte
[item-name bridge](PLAYER_ITEM_NAMES.md) at `800BB6A8`. The adapter replaces the
ten-byte stack load and subsequent item-field setter together. It never writes
a wider string into a native temporary or saved field.

| Caller | Sequence | Item at sequence entry | Message item slot |
| --- | --- | --- | ---: |
| Home room, first prompt | `8093931C` | Unsigned item already in `a1`, from `v1+073A` | 0 |
| Home room, second prompt | `80939994` | Unsigned item already in `a1`, from `v1+073A` | 0 |
| Police lost-and-found | `809C28BC` | Unsigned halfword at `a1+6294` | 0 |
| Fishing-event reward | `809D608C` | Unsigned halfword at `s0+0944` | 0 |
| Redd outside his shop | `809D7F74` | Unsigned item already in `a1`, from the selected table entry | 2 |
| Saharah | `809DA8F4` | Unsigned halfword at `sp+003A` | 0 |
| Opening Nook | `80A6D054` | Unsigned nonzero item already in `a1` | 0 |

The home, police, Redd, and opening-Nook sequences obtain their main-window
pointer through `8009D1F0` inside the replaced span. The fishing-event function
obtains the same pointer at `809D5F94`, storing it at `sp+24`. Saharah obtains it
at `809DA840`, storing it at `sp+4C`. These are hexadecimal offsets. The getter's
four instructions return exactly `80142410`; its installed body is checked.
The bridge therefore addresses the same message window, not an arbitrary window.

The first adapter instruction captures the original item before setting `a1`
to the field slot in the call's delay slot. Original load delay-slot halfwords
are retargeted from `a1` to `a0`, preserving their base register and displacement.
Preloaded items instead use `move a0,a1`. Opening Nook's branch targets the
start of its replacement and retains its original invalid/empty-item bypass.
Redd's distinct slot two remains slot two. Item zero clears the whole selected
field through the bridge; nonzero items use the complete resident resource.

All other actor instructions, local branches, quantities, prices, item ownership,
message selection, and timing remain. Saharah's adjacent numeric free-string
field is unchanged. The fishing-event size/unit formatter is unchanged. These
changes apply existing English names; they do not rewrite GameCube dialogue,
reflow lines, alter pauses, or claim to finish other free-string/choice readers.

## Installation and checks

`tools/event_item_names.py` binds all six complete source actors and relocations,
and the seven original sequence hashes. Replaced spans are 28 or 36 bytes and
contain no relocation entries. A scan of pinned executable ranges and aligned
native literals rejects references into replacement interiors. It is not a
general proof about arbitrary computed indirect calls.

Installation requires the verified resident item imports, enabled full resource,
main-message setter/reader, unchanged singleton getter, and installed zero-safe
bridge. It stages all six actors before updating replacements and rejects
unapproved earlier actor modifications. Final cartridge verification reconstructs
every actor and checks unchanged relocation data and application evidence.
The counter verifies the installed connection without crediting unfinished
item-name readers elsewhere or counting original IDs more than once.

Independent MIPS assembly covers all seven adapters. Focused tests cover original
item/slot expressions, zero handling, atomic rejection, relocation at two bases,
unchanged BSS and unrelated cartridge contents, and UPS reconstruction. Existing
resident field checks cover complete-name insertion and bounds. No actor grows,
no allocation is added, and no saved layout or RAM requirement changes.
Ordinary gameplay and save/restart belong in the combined v0 smoke; artifact and
host checks do not establish native gameplay or original-hardware certification.
