# Eight-byte display names

## Scope

The separate resource and `af_load_display_name` API provide complete GameCube
villager and special-character names. The resident module integrates these at
two nameplate call sites, the main-message talk-name insertion, and read-only
NPC recipient names in letter headers. These changes
remain experimental pending broader conversation, save, and hardware validation.
Six-byte saved names, identity structures, catchphrases, the shared dynamic-choice
insertion, and unrelated name-loader callers remain unchanged.

Letter headers use the existing packed villager identity only when the native
recipient type is one and the index is below 216. Player names and unsupported
or unavailable-resource cases retain their saved names. Ordinary and snapshot
readers share the lookup; editors and saved records retain native capacities.
See [letter header rules](MAIL_READER.md#recipient-display-names).

## Native consumers

The main code has three direct calls to `mNpc_GetNpcWorldName` (`800ACDF8`):

| Site | Use | Existing temporary | Eight-byte boundary |
| --- | --- | --- | --- |
| `8009D324` | Client-name setup, function `8009D308` | Six bytes at `sp+1C` in a `30`-byte frame | Ends at `sp+24`, below all following used storage |
| `8009ED48` | `mMsg_CopyTalkName`, function `8009ED14` | Six bytes at `sp+2C` in a `38`-byte frame | Ends exactly before the size temporary at `sp+34` |
| `800A2BCC` | Client-name draw, function `800A2BB0` | Six bytes at `sp+50` in a `58`-byte frame | Ends exactly at the frame boundary |

Offsets and frame sizes in this table are hexadecimal. The length argument at
`8009D334` is widened to eight; `8009ED58` remains six. The draw function reads the length
stored in the window at `28`. Client-name setup retains a seventy-two-pixel
centering span; eight approved Latin glyphs fit within it without a font or
nameplate texture change. Every instruction replacement has exact source guards
and complete-capability checks. An all-DMA reference scan rejects external jumps
or literal pointers into the changed nameplate/message-handler interiors.

Executable-segment auditing also finds calls in `ovl_Tukimi_Npc0` at `809DFF2C`,
`ovl_Tukimi_Npc1` at `809E0788`, and `ovl_Turi_Npc0` at `809E3230`.
Those overlay destinations remain native. `mMsg_CopyTalkName` itself serves both
the main message handler (`800A1100`) and dynamic choices (`800656B0`). The latter
does not have an approved widened destination. A separately bounded main-message
insertion at its caller leaves the shared six-byte function and its choice caller
unchanged. The existing move routine can report an oversized result without
moving the suffix; replacement insertion rejects expansion beyond 1024 bytes
before calling it or copying the name.

The native name resolver checks actor part byte `2` against NPC part three.
For NPC actors, the animal pointer is at actor offset `174`; an available animal
supplies the native ID at offset zero. Other cases use actor `fgName` at offset
`6` and the special-name table. `af_get_display_name` preserves these distinctions:
an animal pointer can resolve only villager identities, whereas an absent animal
pointer uses only special actor identities. Unsupported/null actor inputs and a
disabled resource fall back to the unchanged native resolver with two padding
spaces. A null destination causes no write. The six-byte resolver itself is not
redirected.

`af_copy_talk_name` replaces only the main-message call. It checks cursor/length
bounds and complete command size, stages the eight-byte name, trims trailing
padding, and rejects expansion beyond the 1024-byte message buffer. A null actor
inserts zero bytes, matching the original insertion behaviour. The surrounding
native command handler retains its header update and capitalization dispatch.

## Reference resource

All 216 native villager identities have exact legacy-confirmed GameCube names of
at most eight bytes. The native special table at `8010B510` has 64 twelve-byte
records ending before `8010B810`, with 23 distinct string IDs. Every referenced
special name exactly matches the supplied English disc and fits eight bytes.
The table includes shared names for multiple actor IDs; count these separately
from distinct names. The native table and all source/reference payloads require
hash guards.

A separate optional DMA resource at VROM `02C00000` contains 216 villager rows
followed by the 64 special-table rows, each eight bytes wide. Its 32-byte header
has words `41464E4E`, ABI one, width eight, total 280, villager count 216, special
count 64, and two zero reserves. Total resource length is 2,272 bytes. The module
configuration word at offset `3C` enables the resource only at the expected VROM.
The item-resource configuration at `38` remains independent and is installed first.

The API accepts a destination capacity of at least eight. Unsupported IDs, null
destinations, undersized buffers, disabled resources, and malformed headers cause
no destination writes. It validates the header on every load, loads the aligned
sixteen-byte pair containing the requested row into aligned stack storage, then
copies exactly eight bytes to the possibly unaligned caller destination. Native
special-actor lookup uses the guarded original table, not a guessed sequential ID
range. Villager IDs are limited to `E000..E0D7`.

## Validation requirements

Audit literal and executable references to the affected routines and calls.
Verify the complete eight-byte nameplate temporaries, the widened setup length,
and unchanged shared insertion/choice lengths.
Test every villager, every special actor mapping, unsupported IDs, nulls,
resource disabling, malformed headers, aligned DMA, and adjacent stack guards.
Native tests must exercise client-name setup, talk-name insertion and exact
message limits, and the draw consumer. Normal conversations must show full names
and retain page/timing behaviour. Other dynamic-name fields, house signs, mail
editors, and saved-name consumers remain separate work.
