# Letters from departed villagers

## Verified content and remaining integration

The eighteen native classic templates `00FC..010D` have complete supplied
English header/body/footer parts in catalogue two. All 54 parts match the
verified donor-bank transcoding without unsupported glyphs. They are not yet
connected to complete native creation/publication and receive no new route
credit merely for existing in the catalogue.

The native creator `mPr_GetForeingerAnimalMail` at `800B9C34..800B9DAC`
selects `00FC + personality*3 + RANDOM(3)`. Its full code SHA-256 is
`a23000c283f82ab03d9af62ab377460d27caf3539f316b7717b116ff7d6250f3`.
The corresponding supplied English function has 360 bytes and SHA-256
`e52db84f05b3eeddb0bc4fb2658a2bd9528ab4a1515db932d276d88956607ff3`.
Both use the same six personality groups and three choices per group.

| Field | Native source | Complete English source |
| --- | --- | --- |
| 0 | Player's saved name | Same six saved bytes |
| 1 | Departed NPC ID/name lookup | Full eight-byte English NPC name resolved from that ID |
| 2 | Remembered villager town | Same six saved town bytes |
| 3 | Player's saved town | Same six saved town bytes |

English headers omit the town field present in Japanese. Bodies `0100` and
`0107` also omit Japanese field zero. Preserve the complete English parts and
prune only unused captured fields; do not insert the omitted Japanese arguments
back into the translated wording. English footers still reference the full
villager name, and some also reference the remembered town.

The creator retains native sender/recipient metadata, gift zero, received font
zero, type zero, and the original selected stationery. Its original header/footer
temporaries are twenty/twenty-six bytes before ten/sixteen-byte copies. Complete
snapshot publication must occur after or replace those narrowing copies.
The main static staging letter is shared with Mom at `80144570`.

## Failure boundary

`mPr_SendForeingerAnimalMail` occupies `800B9DAC..800B9E44`, SHA-256
`56babf0ec91465d24802377cc595c1a36ece8e949c549aa586a69e9ca7b6f7de`.
Its supplied English counterpart has 156 bytes, SHA-256
`ecb310217d103a0e450730000121b1baa25e48fbb2fadb9eec9f43fafb527045`.

The native caller clears staging, creates the letter, submits mode-zero receipt,
and unconditionally clears the remembered villager. Installation must guard
both creation and receipt: unavailable text, failed loading, and refused receipt
must not erase that memory or submit an older staged letter. Preserve the native
personality lookup, random selection order, stationery selection, and selected
town/name identity. Do not silently reroll within one synchronous attempt.

An optional extension of the on-demand system creator can use the existing
word/name sources and snapshot machinery without growing resident code. Preserve
the currently validated Mom and ordinary-reply variants. Freeze the actual input
contract and code/stack/publication boundaries before installing the next entry.
Native scheduling, remembered-villager retention through failure/save/reload,
queue capacity, ordinary delivery, and reader reconstruction require validation.
