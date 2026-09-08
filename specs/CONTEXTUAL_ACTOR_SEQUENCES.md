# Complete dialogue with character-specific expression evidence

Five single-record approvals retain the supplied English in full. Their
additional expressions are individually bound to exact native messages from
the same character and conversation context. This uses the existing sequence
contract, not a new runtime feature or unrestricted cross-actor permission.

| Root | Complete conversation | Native supporting message / expression | Expanded bound |
| --- | --- | --- | --- |
| `0785` | Booker's unknown-owner explanation and hesitant permission to take lost property. | `0786` no-items apology / `17` | 211 |
| `240A` | Gulliver's weekly falls, sea dangers, and clumsiness admission. | `240E` personal seafaring follow-up / `17` | 479 |
| `240D` | Gulliver's ghost ship, pirates, and mistaken Pinnacle Rock recollection. | `240E` personal seafaring follow-up / `17` | 487 |
| `2AC9` | Rover ignores the seat refusal and asks the player's name. | `2AD2` housing/arrival reply / `1D, FE` | 237 |
| `2AD4` | Rover's money reassurance, arrival announcement, encouragement, and goodbye. | `2ACD` housing reply / `1F` | 444 |

The two Gulliver references preserve the complete English localisation of the
native clumsiness wordplay and sea-story boasts. No quest, gift, destination,
or gameplay action is added for the jokes. Booker's small fading-text aside,
Rover's circular-money aside, every manual line/page, and all timing remain.
The train-specific expressions are not borrowed for the generic `0467` record;
that separate source still needs its own review.

Only the named `09`, speaker-zero expression tuples are supplied from supporting
records. Full native-root, supporting-record, English-reference, and output
hashes are checked. Other actor requests retain exact order and multiplicity.
No new field or menu branch is inherited. `2AC9` keeps native name-entry request
`09/09/0001`, command `55`, and final `01`; the other four retain `00`. `2AD4`
keeps the native town field. No continuation slots or production resources change.

Five focused tests pass complete English reconstruction, all bounds, identical
basic/full output, exact additional-expression sets, unchanged native actions,
and rejection of missing/stale support, extra actions, or altered English.
All 110 reference tests and five earlier special-actor tests also pass.
The full artifact audit checks all 12,574 installed payloads, UPS reconstruction,
unchanged earlier full/basic candidates, and unchanged runtime/font/resources.

`build/smoke-contextual-actors-01/` passes 79 recorded steps: fifteen native calls
and expected returns, five complete cartridge loads, and 27 memory assertions.
An independent audit regenerates the scenario and checks every call argument,
return, stack, full read, both ending phases, and one restored checkpoint.
The four-MiB run is silent, has no seeded saves, disables both save-write flags,
shuts down cleanly, and retains blank FlashRAM/Pak.

Actual name-entry progression, expressions, property
collection, actor traversal, final rendering, saving, and hardware remain separate
gameplay and playthrough requirements.
