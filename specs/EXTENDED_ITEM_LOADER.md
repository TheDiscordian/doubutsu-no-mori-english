# Capacity-aware item-name loading

## Scope

Provide a separately tested sixteen-byte item-name source and loader before
changing existing ten-byte callers. This is foundation work; merely adding the
new DMA file does not enable wider names in gameplay. Original item IDs, native
name banks, save structures, and existing callers remain unchanged until each
destination and its readers are approved.

## Cartridge resource

The uncompressed resource at VROM `02A00000` contains a 32-byte header followed
by sixteen-byte, space-padded entries. The header words are magic `AFIN`, ABI 1,
entry width 16, entry count 4544, and four reserved zero words.
Groups `20..2F` appear first, followed by 3788 furniture rotation slots. The
ordinary counts are `64, 4, 36, 32, 255, 30, 64, 64, 7, 10, 55, 1, 96, 32, 2, 4`.
The final native furniture filler is excluded.

Generation begins from the verified retail names, pads them to sixteen bytes,
then overlays complete, hash-bound GameCube candidates accepted by the same
identity checks as the bounded importer. Longer-than-sixteen names are rejected.
Unconfirmed identities retain the original Japanese name; the manifest separates
those entries from English candidates. No caller silently loses a suffix.

The ROM builder requires a complete resident module and verifies the resource
header, exact size, source/data hashes, and generated manifest. It adds the new
file only when explicitly selected. Resource inclusion is recorded separately
from ordinary translation edits.

## Runtime API

`af_load_item_name(destination, capacity, item_id)` returns one on success and
zero without changing the destination when the pointer, capacity, item type,
index, or installed resource is invalid. Capacity must be at least sixteen.
A successful call writes exactly sixteen bytes, never the caller's entire
capacity. Empty item zero writes sixteen spaces.

The native `800BF10C` conversion handles placed clothing, insects, fish, and
umbrellas before group lookup. All group indices are bounded. File headers are
checked before loading names. A DMA request copies an aligned sixteen-byte entry
to a local staging buffer, then the result is copied to the destination. This
also supports unaligned caller buffers without unaligned cartridge DMA.

The API does not hook `mIN_copy_name_str` or change message/handbill storage.
Those integrations require the [item reader audit](ITEM_NAMES.md), complete
field/read-path expansion, and dedicated native/gameplay tests.

## Acceptance

Portable tests verify every index, conversion boundary, capacity/no-write cases,
header validation, exact write count, and padding. Native tests verify real DMA,
full sixteen-byte results, unaligned destinations, adjacent guards, invalid
indices, and restoration of the emulator checkpoint. Existing native ten-byte
loads and normal game flow remain regression requirements.
