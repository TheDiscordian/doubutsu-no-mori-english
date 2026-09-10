# General strings and caller capacities

## Retail contract

The string bank uses VROM `00D16000` with cumulative offsets at `00D18000` and
1,562 entries. `mString_Get_StringDataAddressAndSize` at `800C3E30` rejects stored
entries longer than sixty-four bytes. `mString_Load_StringFromRom` at `800C3F70`
accepts a destination pointer, explicit destination length, and string ID.

Its stack frame is 168 bytes. The eighty-byte aligned-DMA staging array starts at
`sp+50` hexadecimal and ends before the length temporary at `sp+A0`. A maximum
sixty-four-byte entry needs at most seventy-two aligned transfer bytes. The
loader copies the smaller of entry length and destination length, then pads the
remaining destination with spaces. This prevents a larger ROM entry from making
the caller's buffer larger: silent truncation still loses translated text.

## Caller inventory

The optional [Katrina integration](FORTUNE_STRINGS.md) supplies all 128 complete
English fortune fragments in `0164..01E3`. Its caller grows from ten to sixteen
bytes through seven guarded frame/length changes and uses the existing resident
item fields. Enabled builds relocate general-string data to `02600000`, retaining
the native table, entry count, sixty-four-byte getter, and every other caller's
limits. Other IDs do not inherit the fortune group's capacity permission.

The optional [Resetti reply integration](RESETTI_REPLIES.md) supplies all 32
complete rude replies in `04C0..04DF` and updates the native matcher to their
English lengths. All words fit the unchanged ten-byte input/temporary fields.
It shares the string-data relocation but requires no resident module. Other
IDs retain their original budgets; the two glyph-bearing apology targets and
ordinary editor operation remain separate work.

The optional [shop-counter integration](SHOP_UNITS.md) supplies all 120 entries
in `0566..05DD` through the five unchanged ten-byte actor callers. Thirty
English counters are intentionally empty. The native sapling family uses
original sapling/saplings wording because the same-ID English references count
turnips instead. Complete count arithmetic, category mappings, relocation
constants, and free-string consumers are bound to the native actors. This group
shares string-data relocation without requiring a resident module; unrelated
IDs retain their original budgets.

The optional [resident-word integration](RESIDENT_WORDS.md) supplies 136 complete
drinks, colours, places, reading-material words, shop types, and category labels.
Its random-word helper uses the available sixteen-byte BSS span; the shop-name
preparer receives a sixteen-byte local. Seven instruction words change, with
no new resident allocation. Category labels retain their ten-byte free-string
caller. The separate [shared NPC-word import](SHARED_NPC_WORDS.md) installs all
352 complete reply words, including five families used by ordinary dialogue.
It requires both the complete resident caller and cartridge letter creator,
and defers the ordinary bank replacements until all consumers are verified.

The optional [reserve-label integration](RESERVE_STRINGS.md) supplies `spare` in
the 77 explicit native reserve slots. Its permission binds the complete source,
caller inventory, five-byte payload, and unchanged bounded loader. It changes
no selector, save field, or runtime code and grants no general capacity increase.

The optional [native credits integration](NATIVE_CREDITS.md) supplies all 110
rows in `04EA..0557`. Ten twenty-five-byte rows use a separate 256-byte actor
BSS area, with updated ownership metadata and both load/draw lengths and
strides. Native contributors, sixteen pages, scales, and fade timing remain.
The group has its own complete-identity permit; unrelated IDs gain no capacity.

`tools/audit_string_callers.py` scans pinned executable-segment definitions and
records thirty-four direct J/JAL sites. It records nearby instructions, file
hashes, linked addresses, and conservative immediate argument hints. Hints are
not path-complete values or capacity approval; alternate branches, computed IDs,
indirect calls, actual destination storage, and later readers require review.

The inventory finds two sixty-four-byte calls, eighteen ten-byte calls, three
four-byte calls, two six-byte calls, one five-byte call, one fifteen-byte call,
and seven sites without a straight-line immediate length.

| Caller family | Verified use | Remaining work |
| --- | --- | --- |
| `80094664`, `800C31FC` | Default home-gyroid message, string `055C`, sixty-four-byte destination | Actual GameCube initialisation selects four English lines `076A..076D`; complete display and saved/editor limits use the [default-message design](GYROID_DEFAULT.md) |
| `80094F3C`, unreachable English-runtime `8009F4AC` | Town suffix, string `01E4` | Audit non-message town-name display separately |
| `800A6428` | Shop-level name at `0558 + shop level`, ten-byte local and mail free-string copy | Full shop names need larger local storage and handbill substitutions |
| `800A8D70` | Eleven families of randomized NPC-letter words; native ten-byte fields plus complete selected-ID snapshot capture | Shared import requires the complete creator, catalog, reader, eight hooks, and failure gate; normal delivery remains |
| `800A9F7C`, `800AA264` | Saved villager catchphrase at `Animal+4E5`, four bytes | Default main-dialogue display uses a separate ten-byte resource; custom editing, shared choices, mail, and save compatibility remain |
| `800ACDC0` | Special-NPC name table, six-byte singleton then personal-name copy | Main dialogue/nameplates use the separate eight-byte display resource; other readers and identity storage remain native |
| `800C40D4..800C43F4` | Native date/unit suffix formatters | Message/resident and leaflet preparation use complete English; notice and fishing callers remain native |
| `809DC590` in `ovl_Ev_Gypsy` | Four 32-entry fortune families; scoped sixteen-byte local and resident item fields | Complete source-bound English group implemented; normal paid readings and luck effects remain gameplay checks |
| Five shop actors | Complete 120-counter group; count-minus-one indexing, eight native families, unchanged ten-byte locals and free-string slot 8 | Native batch passes all actors; ordinary transactions and presentation remain gameplay checks |
| Ordinary resident overlay | Four helper callers, sixteen-byte shared temporary and item fields; full shop-type local; unchanged ten-byte item-category labels | Complete resident and shared-word groups implemented; normal dialogue and category selection remain gameplay checks |
| Fruit-box actor | Native performance credits, 110 rows, twenty-five-byte owned loader/drawer | Native batch passes every page and fade boundaries; normal K.K. performance, final presentation, and hardware remain |
| Fortune-slip actor | All 68 complete sixteen-byte phrase/outcome values and three full templates through an owned snapshot creator | Native hand-off/readback and guarded payment recovery pass; normal interaction and scene cleanup remain gameplay checks |

The [leaflet integration](LEAFLET_DATES.md) distinguishes all 23 direct date/unit
calls in the built cartridge: seventeen use resident English formatters, two use
the complete English hour at the original entry, and four retain native formatters.
Shop/Redd field preparation passes scoped native execution with unchanged resident
and saved sizes. The optional [event owner](EVENT_LEAFLET_PUBLICATION.md) installs
complete sale/Redd letter publication and sixteen-byte selected-item capture,
with an extended pending flag and separate save/scheduling acceptance. Notice
month/day spacing and fourteen-byte output, and fishing units remain. Target
classification is not a capacity or gameplay completion claim.

The NPC-letter families in `mNpc_SetRemailFreeString` use thirty-two-entry ranges
starting at `0314`, `0334`, `02F4`, `0219`, `01E5`, `0354`, `0374`, `0394`,
`03D4`, `03F4`, and `03B4`. These are handbill fields, not the message window's
similarly named free-string storage.

The gyroid's other-owner display setter uses measured pixel wrapping while
preserving manual newlines and its native 68-byte temporary field. It still
receives the original 64-byte saved message. The complete English default uses
an exact-default actor substitution; owner-editor presentation and wider custom
editing remain unfinished. See [gyroid message](GYROID_MESSAGE.md) and
the [four-line default integration](GYROID_DEFAULT.md).

## Acceptance

Do not globally raise string capacity or import every longer entry. Each group
needs an ID/caller proof, storage and downstream-reader changes where required,
guarded patches, and native loading/display tests. Saved catchphrases, gyroid
messages, names, and mail additionally require save-format compatibility checks.
GameCube wording is the reference; shorter substitutions are explicit translations,
not silent truncation of the supplied text.
