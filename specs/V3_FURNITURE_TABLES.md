# V3 expanded furniture tables

## Purpose and limits

The clothing-enabled development build uses 2,051 transient profile and bank
entries. The earlier 1,267-entry limit cannot represent all additional clothing
mannequins alongside donor furniture. The new capacity covers the complete
runtime-index range for `3xxx` furniture, with three unused padding entries
to preserve the native unrolled loops' three-plus-four structure.

Unknown indices fail the checked profile lookup. The
[clothing display adapter](V3_CLOTHING_DISPLAY.md) uses index 1,727 for its
stable mannequin dependency; original furniture and pocket identities remain
unchanged. Ordinary catalogue rows and acquisition readers remain integration
work, separate from transient-table capacity.

## Memory ownership

ABI 40 reserves `80470000..8047285F` exclusively for these tables: 10,336 bytes
in Expansion Pak memory. Neither original heap grows. The eight-MiB startup
requirement remains; the four-MiB warning path does not initialise this region.

| Address | Contents |
| --- | --- |
| `80470000` | Four `AF46C0DE` guard words |
| `80470010` | 2,051 resolved profile pointers, 8,204 bytes |
| `80472040` | 2,051 bank indices; `FF` means no bank |
| `80472850` | Four `AF46C0DE` guard words |

The 204-byte initializer is inside the existing resident prefix at
`8046A000..8046A0CB`. The field bridge at `8046A200` is retained. Startup calls
the initializer after checking and loading the resident code and before setting
the installed flag or returning to gameplay.

All native profile entries initialise to zero. Imported static profiles derive
from the checked [canonical sparse rows](V3_IMPORT_STORAGE.md) at `80484000`,
validating both identity and enable state. The speed bag and three clothing
mannequins retain their separate callback profiles. Absent/malformed rows and the
three final padding entries remain zero. Bank indices initialise to `FF`.
The original 947-entry profile allocation and cleanup remain native-owned;
the [100 dedicated model banks](V3_FURNITURE_BANKS.md) retain their fixed pool.

## Readers and stable entry points

All 57 native profile-table and 15 bank-index references use the new addresses.
The three complete-table bounds become 2,051. Native prefix-only cleanup bounds
remain 947. Existing fixed-address references have no remaining relocation
entries; the installer rejects a relocation at any changed word. The full room
owner and its unchanged relocation resource are checked before patching.

The expanded furniture helper is 1,720 bytes at `80465800..80465EB7`. It occupies
the retired native profile-table prefix, not the villager reader at
`80465400..8046578F` or mannequin at `80466000`. The initializer does not read
the retired seed table or copy code into the transient profile table.

All eight existing public helper addresses remain fixed, including profile
lookup at `80465000` and inverse item conversion at `804652E4`. Each forwards
to the corresponding expanded helper with a checked two-word jump. Existing
room, identity, item, shop, and scoring callers therefore retain their targets.
The build report keeps the original compiled entry layout in `furniture.code`;
`furniture.expanded_tables.public_entries` records the installed forwarding
words, and `expanded_code` records the complete new helper.

The catalogue's own profile read changes only two words, at `808B3370` and
`808B3378`. Its original index-minus-1024 conversion is retained. Catalogue
allocation, names, order, prices, model buffers, and relocation do not grow.
The original unexpanded variants retain their existing table addresses.

## Compatibility and verification

Transient-table addresses do not change save format 2, the 192-byte profile
layout, or acquired-item state. The clothing display dependency adds a selected
bit, so its compatibility restriction applies independently of the table move:
older profiles reject new saves. Older format-1 V3 builds and V2 cannot load
format-2 saves. Ordinary cross-build reloads remain distinct from codec checks.

Two focused tests and a 91-record current-cartridge native run pass. The native
check executes real owner relocation, complete table reset, both imported model
loads, bank reuse/release, original heap-profile/model loading, and cleanup.
Both table guards and the entire restored external reservation pass. See the
[checkpoint](../docs/checkpoints/V3_FURNITURE_TABLES.md) for artifacts and limits.
Both patchers remain V2 pending the user's testing and explicit approval.
