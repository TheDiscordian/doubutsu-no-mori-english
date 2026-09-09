# Songs, stationery, seeds, tickets, and ordinary item names

## Reviewed content

The explicit item-identity registry adds 209 complete English names: 52 K.K.
songs, thirty stationery designs, three Bell denominations, six tools/umbrellas,
six quest items, mushroom and candy, eight seed bags, 96 raffle-ticket slots,
two grab bags, and four turnip states/quantities. Each approval binds the exact
Japanese source, supplied English reference, and an individual explanation.
Existing approved names are not replaced or reapproved.

The native song list starts with hymn/Chorale, then March. The legacy glosses
swap these two. Full supplied punctuation and wording remain, including
`K.K. D & B`, `Go K.K. Rider!`, and `Two Days Ago`. Native regional/genre titles
use the supplied English localisations, not improvised shortened titles.
The less literal [Aria](https://nookipedia.com/wiki/K.K._Aria),
[Faire](https://w.atwiki.jp/animalcrossing-wii/pages/33.html), and
[Comrade K.K.](https://nookipedia.com/wiki/Comrade_K.K.) identities have additional
bilingual corroboration; the local original ROM and supplied disc remain the
authority for exact storage slots, hashes, and English spelling.

Raffle names preserve all twelve actual months and eight quantity slots per
month. The native October group is not September, despite its old gloss.
The English seed list inserts cedar sapling before the first pansy: eight
explicit cross-index matches preserve the native species and colour. Native
yellow cosmos is not approved against the English white cosmos reference.
Matsutake maps to the supplied mushroom name and the native sweet to candy;
neither uses the shifted legacy candy/coconut pair.

Stationery approvals retain recognisable materials, weather, seasons, floral
patterns, writing formats, and reviewed style localisations. Ambiguous or changed
design names remain unapproved; equal indices alone do not establish identity.
This includes danger/orange, sepia/daisy, morning-glory/bluebell, scroll/octopus,
strawberry/hot-neon, and other design-dependent pairs. Exact reference spelling
is retained even for the supplied `gingko paper` spelling.

## Capacity and exclusions

All 209 names fit the existing sixteen-byte item resource. Fifty also fit the
unchanged ten-byte native names; the other 159 remain complete only in the wider
resource. No runtime code, field width, saved item, name-resource header, stride,
or allocation changes. Existing full item-field and letter consumers can use
the complete wider resource; unexpanded inventory/catalogue/editor destinations
still require their own implementation and acceptance.

`Café K.K.`, `Señor K.K.`, and `Pokémon Pikachu` require accented item-name
encoding and consumer support. They are not stripped of accents to satisfy the
current plain-Latin importer. Yellow cosmos requires a native-specific English
name, not the incorrect same-position donor. Corrupted/unlocalised GameCube
quest labels, species substitutions, and uncertain stationery/umbrella designs
remain in the remaining reports. These are required continuation work, not
permanent omissions or evidence that the whole translation is finished.

## Acceptance

Generation validates all native/reference hashes, exact spellings, approved
cross-index identities, and both capacities. Tests retain every earlier ordinary
and wide candidate, reject shortening even with a rewritten hash, and ensure
excluded names do not inherit displaced English entries. Actual-ROM verification
checks all 209 complete names, the fifty short fields, all unchanged DMA payloads,
and reconstruction from the original ROM plus UPS patch.

A single bounded silent native batch exercises the new complete name resource
and newly translated short names with loader guards and restored state. Existing
bulk letter tests are not repeated for a name-only resource change. Normal
display review, all wider callers, saving/travel, and hardware remain required.
Executed results and artifact hashes belong in
[the checkpoint](../docs/checkpoints/ORDINARY_ITEM_NAMES.md).
