# V3 additive floors and wallpapers

## Scope and current implementation

The general furniture pipeline's `surfaces` representation discovers complete
GameCube floor/wall banks, preserves existing N64 identities, converts missing
surfaces in a batch, and retains their names, prices, catalogue order, acquisition
lists, and floor-sound selectors. Preparation does not install items or make
them selectable. Resource readers, room application, persistence, acquisition,
and browser composition remain required.

Use the current explicit experimental lock; keep the main lock and both stable
website deployments unchanged:

```sh
python3 tools/v3_furniture_pipeline.py convert --assets-only \
  --representation surfaces \
  --base-lock build/v3-start-disabled-imports-01/cartridge/build-lock.json \
  --output build/v3-room-surfaces-prepared-02
```

`scan --representation surfaces` records the complete inventory. Preparation
accepts individual canonical donor IDs with repeated `--select`, a `floor` or
`wall` category, or all missing surfaces by default. `--reuse-assets` verifies
and copies complete prepared objects. These are developer preparation options;
no experimental choices are added to the served browser patcher.

## Source banks and identities

Both donor banks contain 67 player surfaces followed by four shop surfaces.
The original N64 banks contain 64 player surfaces and four shop surfaces. Floors
contain one 32-byte palette and four 64×64 CI4 tiles, totalling `2020` bytes.
Wallpapers contain the same palette and two tiles, totalling `1020` bytes.
Conversion changes RGB5A3 palettes to native RGBA5551 and untangles each complete
8×8-block texture independently. Unsupported partial alpha rejects.

Full decoded-pixel matching identifies 124 existing player surfaces and ten
additions, with no ambiguous matches. Eight donor shop surfaces map from indices
67–70 to native 64–67; shop textures are not selectable imports. The pinned item
worksheet independently identifies all ten additions as lacking an N64 item.
Equal numerical indices alone never establish identity.

The four edition replacements remain distinct content. N64 bath tile floor,
old plank floor, bathhouse wall, and worn earth wall remain available. Donor
western desert, backyard lawn, western vista, and backyard fence are additions,
not replacements or renamed original items.

## Stable reservations

`tools/v3_registry.py` owns append-only surface reservations independently of
selection order. Native floor-sound identifiers extend through 72 even though
the player/shop texture bank ends at 67. New reservations begin at 73, preserving
the post office, police station, travelling merchant, broker, and igloo sound
identities. Paired wallpaper/floor additions use the same index so the existing
room-series scoring representation can identify a matching pair.

| Donor pair | Contents | New index | Native item pair |
| --- | --- | ---: | --- |
| `2612` / `2712` | western desert / western vista | 73 | `2649` / `2749` |
| `261A` / `271A` | backyard lawn / backyard fence | 74 | `264A` / `274A` |
| `2640` / `2740` | block flooring / mushroom mural | 75 | `264B` / `274B` |
| `2641` / `2741` | boxing ring mat / ringside seating | 76 | `264C` / `274C` |
| `2642` / `2742` | harvest rug / harvest wall | 77 | `264D` / `274D` |

Reservations do not imply working native readers. The current native player
floor getter masks the saved floor to six bits. Do not merely increase artwork
bounds while that reader and the corresponding writers still truncate identity.
Preserve unrelated bits in saved home records; establish complete application
and persistence before enabling any surface. An eventual save-format extension
requires an explicit compatibility warning before a test build is handed over.

## Complete metadata and preparation

The source REL supplies all 16-byte English names, 67-entry catalogue orders,
terminated price tables, and the complete 23-entry acquisition pointer tables.
Every non-null list is resolved through its actual relocation. All lists must
terminate, contain valid unique IDs, and cover each player surface exactly once.
Prices retain their complete source words; catalogue eligibility is not guessed
from the price or acquisition label. Acquisition routes remain genuine donor
routes, including A/C stock, event stock, HomePage/Mario delivery, and Harvest.
Missing routes cannot be replaced with arbitrary shop stock.

The single `translations/provenance.json` catalogue credits the prepared names
to the official GameCube localisation, with source symbol, index, and exact
name-record hash. Existing human edits are checked and preserved. Artwork and
generated metadata stay in ignored `build/` directories.

The complete donor 95-entry and native 73-entry floor-sound selector tables are
source-hash checked and retained. This establishes numbering and dependencies,
not complete sound equivalence: corresponding programs, instruments, and samples
still need checking when the runtime sound reader is connected. The existing
campsite floor getter deliberately uses native sound slot 68; preserve its
wrapper when extending ordinary room-floor identity.

Prepared caches verify source banks, registry, metadata, paths, and complete
converted objects. Partial, changed, ambiguous, or unknown resources reject.
Ten objects total 61,760 bytes; conversion requires no compiler container or
cartridge write.

## Runtime integration queue

1. Install additive surface resource records and shared room/catalogue texture
   readers without moving or changing original surfaces or special-room sounds.
2. Connect full item IDs to names, pricing, inventory actions, catalogue lists,
   ownership, and the existing optional-profile/save validation.
3. Connect floor/wall application, removal, saved home identity, and reload;
   retain existing home flags and native surface behaviour. Keep imports optional.
4. Apply genuine acquisition categories, floor sound mapping, and matching-pair
   HRA scoring. Existing Western, Backyard, and Boxing adapters explicitly lack
   their matching surfaces and must be updated from the same registry.
5. Bind the prepared contact/floor lifecycle to installed surfaces. The mower
   also requires the donor room owner's movement sound dispatch in
   `aMR_SetMoveSE`; that owner handles both lawn mower and stone coin sounds.
   Colour callbacks alone do not complete the parent behaviour.
6. Add individual/all surface browser composition privately, and run focused
   native reader/application/save checks before a playtest handoff.

Do not replay unchanged rendering or earlier cartridge tests for preparation.
Native execution, in-game appearance, ordinary transactions, save/restart, and
hardware acceptance remain separate from source and converted-resource checks.
