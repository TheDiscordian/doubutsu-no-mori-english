# V3 static furniture artwork checkpoint

## Completed batch

The donor house investigation identified two static furniture dependencies in
Cheri's room: the haz-mat barrel and oil drum. Both are converted by
`tools/v3_furniture_art.py`, including every texture, palette, vertex, opaque
triangle, and translucent decal triangle. Their donor profile/actual item-table
bindings are verified, and the native profile constructor retains their different
lighting-map flags. No custom donor code is copied.

The [specification](../../specs/V3_FURNITURE_ART.md) records the graphics conversion
and the separate runtime work still required. Output is not installed in a ROM,
and neither object is offered as a selectable import. The source work belongs
on `v3/optional-imports`; public/local V2 patchers remain unchanged.

## Construction and checks

Executed from the supplied GAFE01 revision 0 disc:

```sh
python3 tools/v3_furniture_art.py --output build/v3-furniture-art-01
python3 -m unittest tests.test_v3_furniture_art -v
```

Construction succeeds with the existing pinned Docker compiler. All **seven
focused tests pass**, including both actual converted objects and independent
decoding of the compiled native display lists. There are no skipped tests in
this local run. No new native testing harness is built and no emulator or
physical audio playback is started for this data-conversion batch.

Local outputs:

- `build/v3-furniture-art-01/haz-mat-barrel.n64obj.bin`, 3,216 bytes,
  SHA-256 `27693e1512114e3091a7675b228e0e60643ec6114ceb55e59cb5a09c8316a42a`.
- `build/v3-furniture-art-01/oil-drum.n64obj.bin`, 3,216 bytes,
  SHA-256 `0c5e51be4d6bda888fd52b5f5c25ca1dc5e5b93e9b2ada16b3aef2198845d2f2`.
- `build/v3-furniture-art-01/art.json`: complete source/resource/output hashes,
  converter/compiler identities, profile fields, native offsets, and explicit
  not-installed/not-selectable status.

Each object retains 36 vertices, 4,096 texels, sixteen palette colours, eighteen
opaque triangles, and eight translucent triangles. Both use the same compiled
command structure, with different texture/vertex data and profile lighting:

- Opaque commands: 336 bytes, SHA-256
  `0623a4724f79a72c408e6e2b131a2a67bf5a28ae14bed770549c5071ffc63333`.
- Translucent commands: 224 bytes, SHA-256
  `6009517adcc6a9a7a8f3b8cf13a7122b753f02a752463181b4c8ada5323bcfb8`.

Tests preserve all triangle windings, material boundaries, UVs, normals, vertex
alpha, native texture extents, clamp loading, and recognised rendering state.
They reject missing/extra pointers, bad vertex/triangle bounds, unknown commands,
changed source identity, and invalid native profile allocations. These checks
do not establish rendered appearance, working collision, or ordinary gameplay.

## House findings and next runtime entry

The actual donor `npc_house_list` records are:

- Cheri: `00003F2102020203`, type 0, palette 0, groovy wall (`273F`), kitchen
  flooring (`2621`), main layer `0202`, secondary layer `0203`.
- Punchy: `0201271401EA01EB`, type 2, palette 1, mod wall (`2727`), blue flooring
  (`2614`), main layer `01EA`, secondary layer `01EB`.

The walls/floors above are verified **donor** names/IDs, not approved native
artwork mappings. Donor room layers come from `forest_2nd.arc/data/fgnpcdata.bin`,
not the first archive's ordinary field data. That member has 510 records of 518
bytes, SHA-256 `f443f2f451e3a579d183176ba97a81a6685be4746509a4c8a9979e7c900f6fa5`.
Each record contains a layer ID, 16×16 item IDs, and four trailing bytes.

Cheri's `0202` contains donor `3224` and `32B8`. Punchy's `01EA` contains `3352`,
a rotation of the speed bag. The speed bag's profile points to custom keyframe/
interaction code and remains a separate animation/behaviour port, not a static
placeholder. Secondary layers contain K.K. Samba (`2A09`) and K.K. Love Song
(`2A23`) respectively; their native mappings still need verification.

The native house table at VROM `00E02000` is 1,744 bytes, including 218 records.
`mNpc_SetNpcList` at `800AB134` directly indexes that table and copies its eight
bytes into each `NpcList` at `+2C`. Its existing actor-ID-indexed reader needs a
bounded import path; native room lists must not index past that table.

The furniture loader is in native `ovl_My_Room`, VROM `0082D7F0`, link address
`80936710`, 93,200 resident bytes, SHA-256
`4c67db43a7cebe9a35119621a13bac2fe8cb977cd7ab894b6b5e6b08e1d296a0`.
Its relocation resource at `00844400` is 6,208 bytes, SHA-256
`418c53a6dc9d7a2e76eb87054394348fa03db0a4a6385251308dd808b438a71f`.
The local disassembly is `build/disassembly/v3-my-room/code.asm`.

Observed native loader addresses, still **unmodified**:

- `80936710`: clears original allocation/profile-pointer tables.
- `8093678C`: allocates/loads the per-furniture profile overlay, consulting
  sixteen-byte overlay descriptors at `80947638` and profile symbols at
  `8094B168`.
- `8094D320`: allocated overlay pointers; `8094E1F0`: resolved profile pointers.
- `8094F0C0`: per-furniture bank indices; `8094F478`: bank-address table.
- `80937578`: counts occupied banks across 947 native furniture indices.
- `809375E8`: finds a free bank with an unrolled original-table scan.
- `80942688`: maps a furniture index/rotation back to a native item ID, using a
  bound of 948 and a native fallback. Preserve its sentinel/alias distinctions
  before assigning imported indices.

These are linked overlay addresses, not fixed live RAM addresses. Runtime work
must respect relocation, all direct table readers, initialization, and cleanup;
raising a single count is insufficient. No new N64 item IDs or production RAM
reservations are assigned by this batch. Full furniture lifecycle and shared
item-reader integration are the next implementation work.

## Compatibility and scope

The latest development cartridge remains the
[initial-default build](V3_VILLAGER_DEFAULTS.md). No cartridge, existing save,
baseline, website recipe, or web service changes in this batch. V3-with-imports
save compatibility is still unestablished, and saved V3 catchphrase references
retain their existing warning. No ordinary villager or complete furniture import
is declared finished by the converted artwork.
