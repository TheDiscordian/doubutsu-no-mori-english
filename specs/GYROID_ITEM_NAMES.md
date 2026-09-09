# Complete gyroid item names

## Identity and source selection

All 127 native gyroid groups, decimal `364..490`, have explicit source-bound
approvals in `translations/item_reference_matches.json`. Each approval retains
the native Japanese name and ten-byte hash, all four identical rotation fields,
the complete supplied English sixteen-byte reference hash, and the selected
reference ID. The corresponding English indices are also `364..490`, but index
equality is not the identity evidence.

The Japanese family and size spellings identify the supplied English names.
The [bilingual catalogue](https://animalcrossing.soopoolleaf.com/ja/acnl/Catalog/Gyroids/)
corroborates 113 exact pairs. It describes a later game and is used only for
name comparison. The [series inventory](https://nookipedia.com/wiki/Gyroids)
corroborates retention of the original 127 gyroids. No later-game behaviour,
model, sound, or acquisition rule is imported.

Fourteen catalogue spellings differ from the actual native names. The individual
first-generation item pages, linked in each affected approval, confirm the exact
native spelling and supplied English counterpart. The affected native groups are
`379/382/401/406/413/423/424/428/430/434/445/456/472/474`. These are explicit
approvals, not a kana-normalisation rule. For example, the original spellings are
confirmed for [mega lamentoid](https://nookipedia.com/wiki/Item:Mega_lamentoid_(Animal_Crossing)),
[mini clankoid](https://nookipedia.com/wiki/Item:Mini_clankoid_(Animal_Crossing)),
and [wee dingloid](https://nookipedia.com/wiki/Item:Wee_dingloid_(Animal_Crossing)).

The supplied names preserve mini, mega, tall, squat, slim, and wee distinctions.
The legacy use of "Squat" for many mega variants is not copied. Separate families
such as gargloid/warbloid and poltergoid/lamentoid remain distinct. No shortened
names or translated onomatopoeia replace the supplied English names.

## Capacity and integration

All 127 complete names fit sixteen bytes, adding 508 rotation slots to the
existing wider resource. Thirty-one names also fit unchanged native ten-byte
storage, adding 124 slots. There are no new ordinary-item aliases for this range.
Every earlier candidate and non-item ROM payload remains unchanged.

The resource retains its size, header, counts, stride, and VROM. Native item IDs,
rotation conversion, saved structures, runtime code, audio, graphics, and heap
layout do not change. Complete English resource coverage does not establish
that every inventory, catalogue, shop, and editor caller can display wide names;
remaining caller expansion stays in the completion queue.

## Acceptance

Verify every source/reference/rotation and exact selected name, both capacity
totals, retained earlier edits, independent rejection of changed/shortened
approvals, complete resource reconstruction, all unchanged DMA payloads, and
UPS reconstruction. The bounded silent native batch selects every new gyroid
identity and every short rotation, preserving the shared loader boundary,
resource rejection, guard, and checkpoint checks. Do not repeat completed letter
or song-caller batches for this resource-only change. Normal item display,
full-width callers, save/reload, final review, and hardware remain separate.
