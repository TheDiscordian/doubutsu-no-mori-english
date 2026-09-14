# V3 expanded furniture-table checkpoint

## Artifact

`build/v3-furniture-tables-02/animal-forest-v3-asset-loader.z64`, ABI 40.

- ROM SHA-256: `5be3318a84a7655a1334465bfb83fffa6818bb85e5770d22f18a5a5afcd81826`.
- UPS SHA-256: `0d71ef1a10aba310ac50ae798cc72f7cad919a9d5cdbedcbdcf81f25efc6ef8c`.
- Resident prefix SHA-256: `09bc93f5ef3a85dee657f87b1b9d772af3ad0f844814b34c6af559f16f982e34`.
- Initializer SHA-256: `f8236ea637ad18db9aeab27b306648a1a80ac3b6f261fc00120275652d18cca5`.
- Expanded helper SHA-256: `9ef85a2362de014d1c43ae488d61b2b5372ce41c16b6e2adefa0cd8d9db7042e`.
- Full room-owner SHA-256: `68fadce2d8b8f1e0e63520bb694b54a8ef084287514f66de22788a06971fa873`.

The [implementation](../../specs/V3_FURNITURE_TABLES.md) moves transient profile
and bank-index storage into a guarded 10,336-byte Expansion Pak reservation.
All eight public helper entries remain fixed, and all 72 native table readers
plus the catalogue use the new storage. No new item is enabled, no native heap
or model buffer grows, and saved format 2 is unchanged.

## Build and focused checks

The first build stops at the public-entry guard: recompiling for the new table
base adds eight bytes to `find`, shifting later functions. No failed ROM runs.
The corrected layout places the expanded helper in retired native table space
and installs fixed-address forwarding jumps. The second build succeeds.

`build/v3-furniture-tables-tests-02.log` records two passing focused tests.
Sanitizers check complete initialization, guard values, ignored retired seed
storage, bounds, existing bank helpers, all unavailable indices, and retained
native/imported behaviour. The cartridge check restores every recorded owner
edit and compares the complete original owner; it checks the unchanged
relocation, both catalogue-only pointer words, all helper jumps/code, retained
field bridge, complete remaining resident payload, every other resource,
unchanged save runtime/profile, startup CRC, and UPS reconstruction.

The initial host invocation uses a nonexistent report `abi` key. The corrected
assertion reads the ABI directly from the prior cartridge header; it passes.
This is a test-schema correction, not a cartridge defect.

## Native execution

`build/v3-furniture-tables-native-01` passes all 91 records on the current ROM,
restores its checkpoint, resumes, and shuts down normally. It uses the existing
bounded furniture fixture with reported live table addresses and capacities.

Passing checks include:

- The complete 2,051-entry startup profile and bank arrays, and both new guards.
- Full actual native relocation of the current room owner and BSS.
- Native complete bank reset and the retained 947-entry profile-prefix clear.
- Full haz-mat barrel and oil drum model transfers, all four rotations, bank
  selection, existing-bank reload, and normal release.
- Rejection of unsupported indices and out-of-range banks.
- Original furniture profile allocation/relocation, model DMA, and heap cleanup.
- Imported profile retention, every byte of the restored external reservation,
  the retained first 32 KiB of resident memory, fixture/stack/translation guards,
  and zero faulted-thread pointer.

No physical audio, user-save changes, ordinary room graphics, shop payment, or
save/restart is tested by this component run. Catalogue pointer installation
is checked on the host; a fresh ordinary catalogue view is not claimed.
Passing earlier evidence remains attached to the build on which it ran.

## Next work

Connect actual clothing display aliases, native mannequin profile/DMA/draw
callbacks, and corresponding room/catalogue readers. Native pocket-to-display
conversion is `800BEFCC`; inverse conversion is `800BF10C`. Original clothing
uses `17AC + 4 * (item - 2400)`, with the last index excluded from the ordinary
display range. The shared native mannequin profile must receive a full imported
shirt index; using another shirt or a generic decorative model is not a port.
No new display-ID reservation is implemented by this capacity batch.

The [ordinary shop check](V3_CLOTHING_SHOP_GAMEPLAY.md) remains incomplete;
do not restart its navigation retries in this batch. Continue the remaining
imports and profile-aware browser composition without changing either patcher.
