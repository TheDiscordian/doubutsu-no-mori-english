# Shared built-in furniture profiles

## Current cartridge

ABI 287 is `build/v3-builtin-model-profiles-01/profile-runtime/build-lock.json`.

- ROM SHA-256: `3326f6b88da257ca5adaad7b6b0f11b38705215a87907c0179d4337eb19c60ff`.
- UPS SHA-256: `92d521ae6f4b35aea233fa972792d70f6c3227d5e33df628b4363c77407301a2`.
- Final category plan: `build/v3-builtin-model-profiles-01/pipeline.json`.
- Complete built-in profile resources: 49 objects, 183,408 artwork bytes.
- Development catalogue: 167 selectable imports, plus 100 inactive furniture
  profiles awaiting acquisition. Inactive profiles are not selectable imports.

The main build lock and both stable V2-13 patchers are unchanged. This is an
experimental development cartridge, not a hardware-test handoff or public release.

## Common importing path

The ordinary category planner stages complete models independently of missing
reward routes. It covers direct native drawing/contact, beds and seating,
constant model sequences, indexed flower palettes, and building-palette fades.
The complete source profile, geometry, textures, palettes, and scalar fields
are retained. No per-item installer or new behaviour code is needed for these
already implemented native categories.

The palette-fade path verifies the actual shared resident packet, both callback
tables, expanded loader, and public entry instructions before reusing them.
Direct models and flattened sequences have no custom native callback. All
canonical profiles, prices, and official names are installed with selection,
acquisition, catalogue, and scoring disabled. Later ordinary promotion checks
the staged record and reuses its model without copying it.

The 25-object direct-model batch at `build/v3-plain-model-profiles-01/` retains
103,616 artwork bytes and reuses all 25 converted objects. The 24-object batch
at `build/v3-builtin-model-profiles-01/` retains 79,792 bytes, reuses 23 objects,
and compiles the remaining object in one common compiler job. Existing code,
audio, models, selections, resident allocations, and saved formats stay intact.
All name credits live in `translations/provenance.json`.

## Legacy identity and ordinary paintings

Registry version eleven has append-only destinations for basic, scary, quaint,
and classic paintings, chocolates, tissue, and bottled ship. The pinned worksheet
has no N64 ID/name/model/texture correspondence in columns C/H/CG/CJ for these
seven rows. The original-ROM/donor dependency check finds no approved native
mapping or shared identity for them. Prior mappings and display reservations
remain unchanged. Source table indices and N64 destination indices stay separate.

The four paintings are fully installed through the existing ordinary importer
at `build/v3-legacy-paintings-imports-01/cartridge/`: 14,624 complete artwork bytes,
four cached conversions, real stock/event groups, catalogue/scoring, and official
names. Basic/scary/quaint retain `ftr_listEvent`; classic retains `ftr_listC`.
The three gifts have staged profiles but still require their real reward routes.
No arbitrary shop acquisition is substituted.

The worksheet maps source school desk `3208` to native `1200` and bus stop `3270`
to native `10A0`. Their older approved name references do not establish the
GC-added artwork correspondence. Keep that review separate from new identities;
these two records are not duplicate imports.

## Evidence and limits

Five focused `tests.test_v3_room_rig_runtime.ProfileTests` pass against ABI 287:

- Complete new records, every retained resource, no resident/save growth, and
  original-ROM UPS reconstruction.
- Exact retained choice set and both empty/all offline compositions.
- Source acquisition remains pending, repeated planning is empty, and promotion
  reuses complete models with all native scalar fields intact.
- Modified profile bindings reject, and the ordinary artwork validator still
  accepts the retained selectable batch with its single provenance catalogue.
- Changed palette code, loader, entry, feature flag, and callback table reject
  without modifying the supplied data or report.

The direct-model stage also has four focused passing checks across targeted
invocations. Painting source-table/identity integration and four private
browser/offline compositions have passing evidence. The preserved console
code/resources retain the [combined native evidence](V3_CONSOLE_ROOM.md).
No new ordinary room appearance, controller gameplay, save/reload, or hardware
verification is claimed for these models.

## Compatibility and next work

Format five is unchanged. V2 and older V3 save formats cannot load these saves;
older format-five builds lacking a selected painting or other import are also
not compatible targets. Preserve original saves before any experimental handoff.

Resolve remaining parent/native representations and genuine importing gaps,
then source acquisition and gold-tree work. Complete the V2-13 no-import baseline
alignment and bounded combined gameplay checks before the private playtest build.
Do not repeat static model conversion or unchanged console execution checks.
