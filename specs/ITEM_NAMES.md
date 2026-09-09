# English item names

## Initial bounded import

Native item names occupy ten-byte fixed fields in DMA file `010F4000`.
The ordinary groups use the low byte of the item ID. Furniture uses the low
twelve bits and stores four equal names per rotation group. The legacy and
GameCube tables have one name per four furniture IDs; the final native filler
slot is excluded. [Legacy extraction](LEGACY_ITEMS.md) establishes these mappings.

Automatic candidate identity requires the complete legacy name to match the GameCube name
after trimming legacy padding and ignoring case only. Do not remove punctuation,
substitute words, or shift indices to manufacture a match. Retain the exact
GameCube capitalisation and spelling. Missing identities remain explicit in each
bank's generated remaining report.

Individually [reviewed native identities](ITEM_REFERENCE_MATCHES.md) provide a
separate hash-bound path where the legacy wording differs or remains Japanese.
The [mapped-name review](MAPPED_ITEM_NAMES.md) also supplies explicit cross-index
matches where the supplied English table inserts unrelated entries. Native
Japanese part names take precedence over swapped legacy fossil/chess glosses.
The native name, reference, four furniture rotations, complete output, and
capacity are independently checked. Unapproved legacy mismatches stay withheld.

An additional alias pass may transfer an already confirmed placed-object name
to the ordinary item that the pinned native `800BF10C` conversion actually reads.
Require identical complete Japanese source fields, a valid donor source/reference
hash, a complete plain-Latin name within the destination capacity, and no original
draft override. Conflicting English values fail. Four rotations yield one target
edit, not four translations. Preserve the donor reference ID and record the native
source/converted item IDs. Remove accepted aliases from the corresponding remaining
report and count modified slots separately from distinct reference IDs.

Require the native slot hash, expected legacy donor ID, and complete padded
sixteen-byte GameCube reference hash. Accept only supported plain Latin text.
Complete names of at most ten bytes are padded to the original native width.
Longer names stay withheld, without abbreviations or truncation. Preserve all
other slots, alignment bytes, and file dimensions. Report both modified storage
slots and distinct reference identities; four furniture rotations are not four
different translations.

## Native loader and further work

`mIN_copy_name_str` at `80096740` uses a sixty-four-byte frame and ten-byte local
name at stack offset `28`. Its helper `80096710` requests ten bytes from the
native DMA service. The final copy writes ten bytes to the caller. Ordinary
group pointers come from `801076BC`; furniture begins at file offset `1D98`.
Item zero copies ten blank spaces; unsupported high-nibble types leave the
destination untouched.

The loader first calls `mRmTp_FtrItemNo2Item1ItemNo` at `800BF10C`. Placed clothing,
insects, fish, and umbrellas resolve to their ordinary item names, so those
furniture storage aliases are not necessarily read. Native tests must exercise
the conversion as well as direct names and destination guards.

The full port requires sixteen-byte display names and a complete audit of every
caller, temporary buffer, message field, inventory label, catalogue, and editor.
Do not increase the existing write length before those destinations are safe.
Item IDs and saved item structures do not change in this initial import.

`tools/audit_name_callers.py` records thirty-five direct item-loader calls across
the main code and twenty-three overlays. This is an evidence inventory, not
proof that indirect references are absent. Main-code destinations include five
handbill fields, the item/free message setters, and the ground-item label.
The handbill setter `80092D10` limits its twenty fields at `80140680` to ten bytes.
The message free-string setter `8009D6D0` has twenty ten-byte fields at window
offset `38`; the item setter `8009D88C` has five at offset `100`.
`mMsg_CopyItem` at `8009F5B4` reads the same ten-byte stride and width.
Every source expansion requires a matching complete destination/read-path change.
The [message item-field integration](ITEM_MESSAGE_FIELDS.md) provides resident
sixteen-byte main-window values and covers the item-ID wrapper at `800BB6A0`.
Other source-loader callers, the ten-byte compatibility getter, and dynamic
choice insertion are not approved wider destinations.

The [ordinary inventory consumer](INVENTORY_ENGLISH.md) uses a branch-specific
sixteen-byte cleared span, retaining separate mail/quest fields. The
[catalogue consumer](CATALOGUE_NAMES.md) retains native ten-byte page fields and
keeps 63 complete names in owned transient storage; its item-name drawer reads
the full copies without per-frame DMA. Neither integration globally widens the
legacy loader or changes saved item IDs.

The [shop/Redd preparers](SHOP_ITEM_NAMES.md) connect six native actors and
eighteen helper calls to the complete resident item fields. The
[player capture/dig preparers](PLAYER_ITEM_NAMES.md) connect all three original
player item-name calls through a zero-safe main-code bridge. Their original
actor/stack fields are not widened. Other actor, free-string, and dynamic-choice
consumers remain to be connected; these routes alone do not complete every name.

## Acceptance

Tests reject stale references, wrong legacy donors, differing rotation names,
partial names, unsupported glyphs, and changed capacity. Native loading tests
compare full ten-byte results and adjacent guards. Gameplay review still covers
inventory, shops, catch messages, gifts, mail, and save/reload; mechanical imports
remain candidates rather than reviewed translations.
