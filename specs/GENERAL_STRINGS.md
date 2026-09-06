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
| `80094664`, `800C31FC` | Default home-gyroid message, string `055C`, sixty-four-byte destination | GameCube entry is eighty-eight bytes; saved gyroid message and editor limits need a separate design |
| `80094F3C`, unreachable English-runtime `8009F4AC` | Town suffix, string `01E4` | Audit non-message town-name display separately |
| `800A6428` | Shop-level name at `0558 + shop level`, ten-byte local and mail free-string copy | Full shop names need larger local storage and handbill substitutions |
| `800A8D70` | Eleven families of randomized NPC-letter words, ten-byte local and handbill free strings | Expand only with the mail assembly, saved body, and editor design |
| `800A9F7C`, `800AA264` | Saved villager catchphrase at `Animal+4E5`, four bytes | Saved-text compatibility cannot be fixed by enlarging the ROM entry |
| `800ACDC0` | Special-NPC name table, six-byte singleton then personal-name copy | All name readers, dialogue labels, and identity storage need review |
| `800C40D4..800C43F4` | Native date/unit suffix formatters | Message date calls already use resident English formatters; other UI paths remain native |
| Actor overlays | Shops, fortune-telling, fruit-box labels, and an unidentified overlay | Resolve ID tables, local frames, and downstream insertion/draw limits |

The NPC-letter families in `mNpc_SetRemailFreeString` use thirty-two-entry ranges
starting at `0314`, `0334`, `02F4`, `0219`, `01E5`, `0354`, `0374`, `0394`,
`03D4`, `03F4`, and `03B4`. These are handbill fields, not the message window's
similarly named free-string storage.

## Acceptance

Do not globally raise string capacity or import every longer entry. Each group
needs an ID/caller proof, storage and downstream-reader changes where required,
guarded patches, and native loading/display tests. Saved catchphrases, gyroid
messages, names, and mail additionally require save-format compatibility checks.
GameCube wording is the reference; shorter substitutions are explicit translations,
not silent truncation of the supplied text.
