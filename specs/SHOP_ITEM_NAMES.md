# Complete shop and Redd item names

All five Nook shopkeeper variants and the in-shop Redd actor contain an identical
seventy-two-byte helper that loads a ten-byte item name and sets a main-message
item field. The installed helper routes complete names through the existing
sixteen-byte resident item resource and fields. It does not widen an actor,
saved item ID, native temporary, or packed message-window field.

| Actor | VROM | Helper entry |
| --- | --- | --- |
| Nook's Cranny | `008ADF40` | `809CAFAC` |
| Nook 'n' Go | `00889440` | `809A6500` |
| Nookington's main shopkeeper | `0088DD00` | `809AAE20` |
| Nookington's upstairs shopkeepers | `0089A1B0` | `809B7328` |
| Nookway | `008B2CE0` | `809CFEDC` |
| Redd inside the shop | `008BBAA0` | `809D8560` |

The native item and field-slot arguments remain in `a0` and `a1`. Nonzero item
IDs are masked to sixteen bits and tail-call `af_quest_set_item`. Item zero
instead tail-calls `af_set_item_str` with the actual main window, the same slot,
a non-null source, and length zero, clearing the whole selected field. This
retains the native shop helper's blank-item behaviour; the quest wrapper alone
would intentionally leave the previous field unchanged for item zero.
Both paths preserve the caller's stack and return address. Invalid fields remain
bounded by the existing setter. The complete resource and reader are required;
the existing loader's guarded failure behaviour remains unchanged.

All six source actors, relocations, and helper spans are hash-bound. Eighteen
direct helper entry references are recorded across the six actors. The scan
checks aligned literals and direct jumps/relative branches in pinned executable
ranges and rejects references into replaced interiors. No relocation acts on a
replaced instruction. The helper occupies its original span; actor sizes, BSS,
relocation records, prices, quantity/plural logic, message selection, and timing
remain unchanged. The supplied English item names and message text are unchanged.

`overlays/shop/item_name.s` is independently assembled and linked in the pinned
Docker toolchain. `tools/shop_item_names.py` requires the exact resident module,
enabled item resource, complete setter, and main-message insertion hook before
changing any actor. It stages all actor changes before publishing replacements.
Final cartridge verification reconstructs all six patched actors from source,
checks their unchanged relocations, and compares the application evidence.

This connects these six readers, not every item-name consumer in the game.
The combined counter verifies the installed integration without prematurely
crediting resource-only names whose other readers remain unconnected.
The [checkpoint](../docs/checkpoints/TEXT_NAME_CONSUMERS.md) records artifacts,
focused checks, and the remaining combined gameplay smoke.
