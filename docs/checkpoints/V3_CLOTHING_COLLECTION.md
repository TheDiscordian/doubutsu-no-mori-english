# V3 clothing collection checkpoint

## Completed component

The native item-collection hook recognises selected garments through the checked
shared category reader. Ordinary pocket acquisition with condition zero records
the shirt in that resident's independent clothing ownership. Wrapped presents
and quest items retain native collection timing. Unknown/unselected garments
cannot alias furniture bits or another shirt; original items retain their
native collection path. Visiting-player profile transport remains pending.

The collection helper remains 544 bytes at `804699C0`, with the same public
record/query/clear addresses and a 32-byte gap before shop code. Its shared
selection check is not duplicated into callers, and the linker fixes the query
entry at `80469AD4`. All artwork, extended save/item code, mutable-state layout,
save format, native acquisition instructions, and other resources remain intact.

Build: `build/v3-clothing-collection-01/animal-forest-v3-asset-loader.z64`, ABI 33.

- ROM SHA-256: `ebf12225974351bf4afa74392bf533afaff4c2e085e8091cb97007cd0ae0995a`.
- UPS SHA-256: `51c5809910a250dfdc1483f657c3eaa6f4d68c359e0f64268adef40d80cc3f9e`.
- Resident prefix SHA-256: `dcf48add52db13b371b2ea1f11a6642577e0b15dbaf47a411e2211bbc2aa89b1`.

## Verification

The two current clothing host/cartridge tests pass, alongside the current
non-clothing source's sanitized collection check. They cover all four players,
separate garment/furniture ownership, original fallback, removed/invalid imports,
resident/temporary clearing, visiting-player rejection, stable public entries,
complete retained resources, exact prefix differences, and patch reconstruction.

The initial native run `build/v3-clothing-collection-native-01` passes all
62 records and exits normally. It calls native free-pocket acquisition and the
direct pocket setter for all four residents, retains the full `34BF` identity,
and verifies collection only when present/quest conditions become ordinary.
It queries acquired shirt ownership, collects a rotated oil drum independently,
retains original-clothes behaviour, rejects disabled/adjacent shirt IDs, and
clears only player three's acquired ownership through the native clear entry.
All original player records, active pointer, selection profile, and runtime
state are restored. Complete code, stack/allocation guards, and zero fault
pointer pass; the temporary call bridge is freed and checkpoint restored.

No FlashRAM I/O or ordinary shop/reward interaction occurs in this test. It
establishes the acquisition-to-saved-ownership connection, not a completed
gameplay acquisition or save/restart. Existing format-2 codec evidence remains
applicable to unchanged save code; older format-1 V3 builds and V2 cannot read
these saves. Both web patchers remain V2.

## Next work

Connect menu/icon and clothing-action dispatch, display/mannequin rendering,
ordinary acquisition/buy/sell, catalogue presentation, and combined gameplay/
persistence. Resolve remaining NPC queued/second-owner evidence in the combined
clothing gameplay check. Punchy's defaults and move-in eligibility remain off.
