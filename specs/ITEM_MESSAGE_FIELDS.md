# Sixteen-byte message item fields

## Native contract and scope

The main message window is the singleton at `80142410`. Its five item fields
occupy ten bytes each at offset `100`. The native setter is `8009D88C`; the
message insertion reader is `8009F5B4`. The ten-byte copy-out getter `8009DA1C`
has no direct call or literal-pointer references in the verified cartridge.
The reference audit records 27 setter calls, two insertion calls, and five
calls to the item-ID convenience wrapper at `800BB6A0`.

Keep the native structure unchanged. Store complete extended main-window item
values in five resident sixteen-byte rows, with a validity mask. The native
ten-byte fields remain compatibility mirrors for unchanged internal structure
layout. No saved data uses the resident rows. Any setter call replaces the whole
row, clearing unused bytes to spaces; shorter replacement values cannot leave an
old suffix. Null sources and invalid slots retain the native no-write behaviour.
Lengths greater than sixteen fail without a partial update.

Other window pointers retain ten-byte storage and cannot accept a wider value.
The standard getter retains its original ten-byte API; it is not an approved
reader for wider values. Future callers must use the full-capacity API.
The native message initialiser `8009E6F8` does not clear the native item fields;
resident rows likewise persist between message initialisations. Both start with
their BSS-cleared state, and no row is read before its validity bit is set.

## Insertion and item-ID wrapper

The message-handler call at `800A1820` uses a replacement insertion. The separate
choice-handler call at `80065BD8` retains the original ten-byte insertion until
dynamic-choice expansion has its own complete capacity proof. Current imported
reference choices are plain text; wider dynamic choices are not enabled here.

The replacement insertion reads the full valid resident row for the main window,
or the original ten-byte field otherwise. Invalid field indices fall back to zero
as in retail. It retains native command-size calculation and suffix movement,
trims only trailing space padding, and returns the complete resulting message
length. Invalid cursor/length values, missing command bytes, or expansion beyond
1024 bytes cause no insertion. The existing capitalization wrapper still handles
the first inserted character; no line/page/timing commands are changed.

The item-ID wrapper uses the separately verified sixteen-byte resource when it
is installed, then writes the complete result through the widened setter. When
the resource is absent, it calls the unchanged ten-byte native item loader.
Item zero remains a no-op in this convenience wrapper, matching its native
behaviour. This integration covers this wrapper's five identified callers;
the other direct item-name loaders still require their own destination audit.

The [shop integration](SHOP_ITEM_NAMES.md) and
[player integration](PLAYER_ITEM_NAMES.md) add zero-safe adapters for six
shop/Redd actors and three player item-name preparations. They preserve the
quest wrapper's original zero-item no-op contract by handling empty-item clearing
in their adapters. With player integration enabled, the inactive native wrapper
tail `800BB6A8..800BB6F0` is occupied by the shared zero-safe bridge; it is not
available for another allocation. The live eight-byte quest-wrapper entry remains
unchanged. The [event/home integration](EVENT_ITEM_NAMES.md) uses this bridge
for seven more sequences across six actors, preserving original item expressions
and field slots. Other free-string and dynamic-choice consumers remain unfinished.

## Validation

Require source hashes and external-interior-reference checks for all replaced
functions. Test all five fields, replacement with shorter/empty values, invalid
slots/pointers/lengths, non-main windows, all insertion positions, exact buffer
limits, native source fallback, item-ID conversion, capitalization, and adjacent
guards. Whole dialogue and gameplay regressions remain necessary after the
native setter/reader changes. The resource's wider candidates do not all become
gameplay translations merely because one caller family is integrated.
