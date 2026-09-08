# Complete leaflet creation work record

The complete creation transaction covers 22 native-selected templates: three
renewal, sixteen sale, and three Redd letters. All 66 complete English parts are
bound to supplied source banks, native selection tables, and unchanged catalogue
two. Full wording, spacing, body newlines, header markers, article commands,
and footer/capitalization order are retained. No ordinary bank record is added.

The input carries the original selected template, timestamp, count, and item IDs.
Sale names arrive as complete identity-bound sixteen-byte inputs, before native
truncation; resolving those names belongs to the upcoming adapter. The creator
publishes only after complete snapshot packing and resident-reader validation.
Received status/type/paper are set according to the native owner. Other metadata,
inputs, and native state stay intact; failed creation retains the entire output
letter and capitalization word.

## Correct date meaning

The Japanese final-upgrade letter says the shop opens on the supplied date, while
the full English reference says it will be closed that day. The original N64
caller subtracts one day only for earlier shop levels. The supplied GC function
unconditionally subtracts one from a copied planned reopening date before its
recipient loop; its binary prefix confirms the one-day call argument.

The English creator therefore calculates the preceding day locally for every
renewal template. It does not alter the shop's actual schedule or notification
lead time. The adapter must supply the original reopening date, not the already
formatted native date. Leap/year/month boundaries are validated, and an
unrepresentable previous year is rejected rather than announced incorrectly.

## Executed evidence

Seven focused tests pass in 67.287 seconds, covering:

- 528 complete template/month/capitalization combinations.
- All 2,388 month starts across 1901–2099, including rejection when the preceding
  date falls below the supported year range.
- Every allowed native sale count, complete sixteen-byte item fields, and reused work.
- Independent full GC-style in-place formatting and complete saved-envelope comparisons.
- Every cartridge-read failure, disabled catalogue, invalid dates/choices/articles,
  item-ID mismatches, short fields, command prefixes, aliases, alignment, and guards.
- All 66 source-bound parts and exact native/English field sets; changed resources,
  probe variants/imports/relocations, and unsafe code allocation are rejected.

Three final focused checks pass after adding explicit invalid short-month,
shop-count, article, and unused-item cases. Six generic probe regression tests
pass in 0.008 seconds; ten fortune-source/creator regressions pass in 16.939 seconds.
The earlier date checkpoint's 895-test regression batch is not represented as
a full regression run of this later creator change.

The silent native batch in `build/smoke-leaflet-letters-01` passes 77 complete
creation and saved-reader restoration cases: all 22 templates under both capital
states, nine renewal year/leap/non-leap boundaries, and every hour in Redd letters.
It also passes six rejected input combinations and disabled-catalogue retention.
There are 165 native calls and 1,418 memory assertions, plus one post-restore
assertion. Full code/input/save/RNG/handbill retention, unchanged heap accounting,
allocation/stack/module guards, freed fixture memory, restored checkpoint,
blank isolated FlashRAM/Pak, and graceful shutdown pass.

Native selected item names are explicitly synthetic sixteen-byte inputs; native
item lookup is not tested here. The invalid non-sale case includes a non-null item
pointer, so it does not independently isolate the lower-year date rejection.
That boundary is established by the host tests. No production actor or ordinary
delivery hook is installed by the native creation fixture.

## Build and evidence identities

Independent `build/leaflet-letters-probe` and `build/leaflet-letters-repro` outputs
agree. Original native code is 3,100 bytes, without data or mutable globals.
Six imports target verified resident functions; internal absolute jumps have a
complete relocation inventory. Work is 5,280 transient bytes. The leaflet frame
is 104 bytes, and generic generation is 216 before nested reader calls.
Resident module, saved structures, fonts, catalogues, and ROM are unchanged.

- Code SHA-256: `686548ec32157b945c06c3e68b341d1535f201c318cc1f2aa3e414666bbe9a8a`.
- Manifest SHA-256: `7034c846a1250fdee6222fadc31e7b4aa158da1693642dd4ddcca2b252b3b58e`.
- Scenario SHA-256: `85c74fec6a2a70ca745f1cb47506c669f293ba34b6acf30db2feb61c21d4dad6`.
- Native results SHA-256: `94b43a8569557a773787adbe80e44bd3ab96fadfa3a86b07f0f8e0ab20051e08`.
- Native helper SHA-256: `69a3b6cca79b6feca055ebf777976053d82c6878616f63a5e1b0f938e1208a71`.
- Runner SHA-256: `f97e9c6e15e949280fb7896bb9c341720ecdfbb67024dd5f6977a8e541292d05`.

`build/leaflet-letter-evidence.json` records all selected-part source/reference/
encoded hashes, native summary, and independent build checks. Test logs are
`build/tests-leaflet-letters-focused.log`, `build/tests-leaflet-letters-final.log`,
`build/tests-leaflet-probe-regression.log`, and
`build/tests-leaflet-fortune-regression.log`.
The native fixture uses the unchanged date-pilot ROM with SHA-256
`6b2c9a01dec248f9a51c4efc8a0ad3f82e90f4302f6647351a5c5c9e244f2055`.

## Next required implementation

Install renewal publication first, using one complete staged letter before any
home copy and retaining the notification flag on failed preparation. Then connect
sale/Redd selected inputs, complete item lookup, and event publication without
rerolling or losing failed attempts. The native mode-two event leaflet is a
separate saved record, not the ordinary five-slot queue. The exact owner,
call-site, flag, and receipt contracts are in
[the leaflet specification](../../specs/LEAFLET_LETTERS.md).

Check the general-actor allocator before extending those actors; their allocation
rules are not the fortune NPC's rules. Preserve original relocation/DMA-row
ownership, all schedule calculations, existing field-date patches, and normal
recipient eligibility. Batch actual constructor/receipt/readback/failure checks
after integration. Normal delivery and hardware still need their own evidence.

Remaining general text, notice/fishing consumers, all semantic/layout review,
stability/save acceptance, title-first artwork, GameCube-style keyboard, and
patch-only release requirements remain active. Inputs, donor assets/text,
ROMs, patches, and saves stay ignored in the private repository.
