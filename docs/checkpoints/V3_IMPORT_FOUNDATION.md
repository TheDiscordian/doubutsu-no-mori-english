# V3 import foundation

## Completed batch

The user requests a new V3 goal for optional GameCube villagers and items, with
individual and select-all controls in the browser patcher. The goal is active,
and work is isolated on `v3/optional-imports`. V2-11 and both stable patchers
remain unchanged. The [specification](../../specs/V3_OPTIONAL_IMPORTS.md) owns
the scope, source identity, runtime dependencies, save/profile policy, browser
composition requirements, and milestone order.

`tools/v3_import_catalog.py` inventories the actual supplied N64 ROM and English
GameCube CISO. It validates both donor resources, decoded REL, and pinned symbol
and decoder hashes before reading records. It emits no ROM or extracted asset.
Existing output files are rejected, and no input or save is modified.

## Measured inventory

Local output: `build/v3-import-inventory-01/catalog.json`.

SHA-256: `a8c70ace96eb4610a27746a991057d52e73794f7e6a2187c1c93941f39a89833`.

- 216 native villagers; 236 named donor villagers.
- 20 donor-only villager identities: 18 islanders, plus ordinary villagers
  Cheri and Punchy. Two additional runtime test records are excluded.
- 2,333 donor item-name records across sixteen ordinary groups and two furniture
  groups. Furniture rotations share one identity. This is not a count of new
  items; native matches, aliases, unused entries, and behaviours remain to review.
- Zero implemented/selectable imports. No V3 cartridge is claimed.

The initial source review identifies the native transient 27-byte villager
candidate bitset, 216-entry shuffle array, multiple count bounds, six-byte
default-record stride/eight-byte DMA reads, and eight-bit name identities.
The saved appearance-history table already contains 32 bytes. Runtime conversion
and save compatibility need implementation, not just an increased roster constant.

## Verification

`python3 -m unittest tests.test_v3_import_catalog -v`: **six tests pass**.
Synthetic cases cover the roster/test boundary, islander roles, default metadata,
record truncation, unknown values, ordinary/furniture IDs, rotation grouping,
group overflow, and size/hash rejection.

`python3 tools/v3_import_catalog.py --output build/v3-import-inventory-01/catalog.json`
completes successfully against the real supplied inputs. The current V2 ROM
still hashes to
`8bbd1955536a2a3ac9f76d6f323842f5ce25c037e1ff5fd3da9f28d6dfe20507`.
There is no emulator replay, gameplay test, or save operation in this batch.

## Next implementation

Trace the donor-only ordinary villager model/texture references and the native
species loader; choose one complete ordinary-villager pilot. Then map donor/native
furniture identities and select a simple
decorative item for the first full item conversion. Assign persistent destination
IDs only after the relevant tables and consumers are understood. The web selector
must not label research candidates as working options.
