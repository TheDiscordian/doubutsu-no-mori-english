# Character-name application boundary

## Completed reader family

The combined counter enables wider character-name credit only when all of the
following installed integrations are present and verified. Original short-bank
English keeps its independent credit in older builds. Additional name displays
do not add source IDs or repeat the original Japanese weight.

| Native use | Complete display or internal-key handling | Installed verification |
| --- | --- | --- |
| Speaker nameplate and main insertion | Both full-name calls, eight-byte field length, bounded talk insertion | `display_name_readers.verify_main_routes`, resident module |
| Shared choices | Complete bounded talk-name substitutions | `text_extension` / choice profile |
| Three festival actors and reserve actor | Eight-byte display temporaries and fields | `actor_display_names` |
| Map residents and opening guide | Private full-name cache and safe guide temporary | `map_names`, `guide_name` |
| Fishing winner | Exact saved aliases and complete NPC-only identity marker | `fishing_name` |
| Three conversation fields and resident's other-villager field | Shared eight-byte identity bridge | `conversation_names`, `text_names` |
| Villager house sign | Exclusive position lookup into initialized eight-byte temporary | `house_name` |
| Inventory recipient/sender and quest descriptions | Full-name composition and relocated quest resolver | `inventory_english` / descriptions profile |
| Letter recipient while reading or writing | Full read header, editor header, matching header cursor | `mail_view_patch`, `letter_names` |
| Ordinary local and foreign replies | Complete capture and exact saved-key resolution | `npc_mail_capture`, `npc_mail_loader`, creator profile |
| Departed, event/birthday/goodbye, and quest letters | Complete names captured before snapshot publication | Corresponding installed letter-route verifiers |
| Treasure announcement | Complete owned name field, not the old short handbill | `notice_overlay` / treasure owner |

`tools/display_name_readers.py` requires the complete set, including the full
inventory-description, snapshot-reader, shared-choice, and identity-bridge
profiles. `translation_progress.measure` verifies every required installed
route and resource before returning the ledger. The main speaker-name calls and
field length receive additional explicit instruction checks. Removing a required
integration keeps the family pending; changing its installed code rejects the
measurement instead of crediting an unconnected resource.

## Retained six-byte internal uses

The existing executable/literal inventories are
`build/audits/identity-name-callers.json`, `special-name-callers.json`,
`display-names.json`, `name-callers.json`, and `remaining-name-readers.json`.
These ignored inventories describe original instructions; an original call
remaining in the ROM is not automatically a live untranslated display.

- `8009C730` constructs saved mail identity metadata. Its complete read and edit
  headers resolve the packed NPC index separately; the writer must remain six.
- `800A87E0` stores the foreign-reply sender key. The creator's exact 394-key map
  resolves complete names for all 216 villagers without using truncated prefixes.
- `800A8C90`, `800A8CB8`, and `800A8CF8` use complete scoped NPC capture hooks.
- `800A94F8`, `800A9A20`, and `800AC2D8` prepare native short event fields, but
  the installed common creator at `800A93AC` captures the complete selected
  identity for friendship, birthday, and goodbye snapshots. Those short fields
  are not the rendered English source.
- `800ACE48` is inside the six-byte compatibility actor resolver. The audited
  player-facing actor callers use the complete display adapter; native fallback
  remains available for unsupported identities.
- `800ACF4C` is inside the random-name generator. Its only external caller,
  fishing initialization at `80A90280`, writes the six-byte saved winner key.
  The table-ID call at `80A90270` serves the same saved record. The winner's
  separate display resolves the complete English name.
- `800BB514`, `800BB524`, `800BB570`, `800BB5A8`, and `800BB5BC` belong to the
  native quest-name composition. The installed inventory description uses the
  relocated full-name resolver and its own display storage.
- `800BB8A0` is inside the replaced quest-reply creator. `800B9CA8` is inside
  the replaced departed-letter creator. Their complete snapshot owners supply
  the actual displayed name.
- The old treasure preparer at `800A5E74` is replaced by its complete owner.
  Compatibility resolver-to-resolver calls remain six bytes by design.

This closes the known character-name resource readers, not item names,
catchphrases, arbitrary user-written names, travel/foreign-hack compatibility,
or exhaustive gameplay validation. Newly discovered player-facing readers must
reopen this accounting gate until integrated. No missing-implementation claim
is inferred solely from unperformed human playtesting.
