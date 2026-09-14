# V3 secondary villager names

`--villager-readers` connects imported names to map house labels, inventory
quest/letter descriptions, letter headers, recipient selection, conversation
identity fields, and generated mail. It includes the current house foundation
without enabling move-ins or changing either V2 web patcher.

## Display and creator bounds

Six display checks admit identities through index 237 instead of stopping at
215. These checks precede the existing complete-name API; they do not directly
index a larger table. The shared V3 lookup still requires an installed import.
Uninstalled identities and native test rows cannot produce a full display name,
and each caller retains its existing fallback and buffer capacity.

Four generated-content checks admit the same range for departed-villager,
birthday/event/goodbye, quest-reply, and treasure-notice requests. This admits
imported requests to the existing personality/template/metadata checks; it is
not roster eligibility. Their named fields use the guarded capture readers.
Treasure variants without a name field do not need a name lookup.

| Resource | Checks or entries |
| --- | --- |
| Inventory `03950000` | `A9C0`, `AAB0` |
| Map `03B00000` | `6568` |
| Letter header `03B60000` | `1FF8` |
| Address list `03E60000` | `1D94` |
| Persistent text `03A00000` | `04B8` |
| Mail creator `03200000` | `1C00`, `20FC`, `360C`, `448C`; entries `0898`, `0928` |

Offsets are within each resource's unrelocated image. Only checked immediate
words and the two mail entry pairs change. Original relocations, allocation
sizes, draw geometry, museum/player labels, letter templates, and save fields
remain intact. The installer rejects any relocation on a modified instruction.
It preserves the other V3 edits already present in the inventory owner.

## Generated-name capture

The 912-byte resident helper occupies `80465400..8046578F`, between furniture
reader code and the expanded furniture profile table. It has no mutable globals.
Both public entries receive the original capture arguments and keep native
output/source overlap checks, source-ready marker, and valid pointer checks.

For native villagers, name capture retains the existing 394-alias search and
the exact eighteen-byte field format: length eight, no article, eight complete
name bytes, and eight zero bytes. Imported names come from the installed shared
name API. Unknown, disabled, special, and test identities are rejected without
output writes. Original six-byte saved APIs remain unchanged.

Reply capture first retains the original sorted six-byte alias search. Only if
that fails does it consider installed imports. Exactly one matching imported
compatibility spelling is required; ambiguous spellings fail without selecting
an identity by table order. No English name is copied into a smaller saved field.

The text-startup loader retains its complete checked instructions apart from
the updated two-word CRC constant. The generated-letter module's existing
configuration retains every field apart from its full resource CRC. ABI 24
binds the changed resident prefix. The loaded code still verifies both CRCs.

## Remaining villager integration

These readers do not establish roster selection, house visits, ordinary letter
delivery, or saved villager/profile/Controller Pak support. Remaining native
ID-indexed tables and selection arrays must be expanded before move-ins are
enabled. Punchy's starting shirt and animated speed bag remain separate content
dependencies. V3 saves require the compatible V3 import profile and must not be
loaded in V2.
