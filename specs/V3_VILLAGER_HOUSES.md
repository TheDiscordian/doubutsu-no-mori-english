# V3 villager house data

## Installed scope

`--villager-houses` installs Cheri's complete two-layer GAFE01-r0 house alongside
the existing furniture, scoring, and save foundation. It does not enable move-ins
or change the browser patchers. Punchy's room metadata and item dependencies are
identified, but his house stays uninstalled until the speed bag's real behaviour
and his default cherry shirt are available.

No original villager or house is repurposed. Shared furniture uses reviewed
existing identities and native behaviour; the two new barrel items use their
installed V3 identities. Item coordinates, rotations, structural markers, and
the secondary-layer music position remain as supplied by the donor.

## Sources and identity checks

The builder verifies the original N64 ROM, the English donor's complete REL and
`forest_2nd.arc`, and the pinned symbols. Donor `npc_house_list` contains 238
eight-byte records. `data/fgnpcdata.bin` contains 510 records of 518 bytes:
two-byte layer ID, 256 big-endian item IDs, and four retained trailing bytes.
Its SHA-256 is
`f443f2f451e3a579d183176ba97a81a6685be4746509a4c8a9979e7c900f6fa5`.

The native house table at VROM `00E02000` contains 218 eight-byte records,
including the two test characters. Native foreground at `011AB000` contains
432 records, IDs 398–829. Its sorted-pointer allocation reserves 458 slots,
IDs 398–855. The installer preserves all of these records and reservations.

| Villager | Actor | Donor layers | Reserved N64 layers | Wall / floor indices |
| --- | --- | --- | --- | --- |
| Cheri | `E0EA` | 514 / 515 | 888 / 889 | 63 / 33 |
| Punchy | `E0ED` | 490 / 491 | 894 / 895 | 39 / 20 |

`v3_registry.villager_house_layers` reserves two slots for each of the twenty
English-donor identities, starting after the original 458-slot range. These
IDs are independent of selected subsets, table order, and which pilot is ready.

## Shared room surfaces and items

Walls contain two independent 64×64 CI4 tiles and a sixteen-colour palette;
floors contain four tiles. Decode each GX tile and convert the RGB5A3 palette
before comparing every colour pixel against all 68 native surface records.
Both pilots have unique complete matches at the indices above. Their complete
converted palette/texture records also match the native records. The native
wall bank `0182A000` and floor bank `017A1000` remain unchanged.

Existing item mappings bind the actual source and donor name hashes to reviewed
identities. The five common items absent from the explicit translation-match
list—red sofa, retro stereo, gold stereo, blue bed, and blue table—use the
pinned cached identity worksheet, verified original Japanese names, supplied
English names, exact IDs, and matching model/texture references. Absence from
that partial approval list is not evidence that an item is absent from N64.
This is existing-identity reuse, not a claim of newly converted artwork.

Cheri's ordinary dependencies are red sofa, eagle pole, bear pole, retro stereo,
timpano drum, djimbe drums, and K.K. Samba. The imported dependencies are the
haz-mat barrel and oil drum. Their complete installed mappings are required;
the builder rejects an unresolved or missing dependency. Doors (`4080`), wall
markers (`FFFE`), and reserved spaces (`FFFF`) retain native semantics.

## Native installation

The house table grows from 1,744 to 1,904 bytes within its existing ROM interval.
All 218 original rows are retained. Cheri's new row is
`00003F2103780379`; the other uninstalled import rows remain zero and unavailable
to move-in selection. This table expansion is not an eligibility decision.

The foreground grows from 223,776 to 224,816 bytes: two appended 518-byte rows
and four alignment bytes. Its end is `011E1E30`, below the next file at
`011E2000`. Both DMA indices stay unchanged and no new DMA row is required.

Five checked immediate instructions connect the new bounds:

- `800AB194` and `800AB1B0`: both allocation routes of `mNpc_SetNpcList` use the
  house-table end `00E02770`. Native copying, placement, and cleanup remain.
- `80086104`: the NPC foreground load ends at `011E1E30`; the native divide by
  518 obtains 434 records and ignores the four alignment bytes.
- `80086118` and `8008611C`: allocate 1,992 bytes for 498 sorted pointers,
  covering every fixed import layer reservation. Sparse slots remain null.

The complete native functions are checked before these five words change.
The house-table allocation grows by 160 bytes. The NPC foreground allocation
grows by 1,040 bytes and its temporary pointer array by 160 bytes. Resident
helpers, model banks, and ordinary heap bounds do not change.

The assembled startup uses ABI 23. Only the resident header's ABI word changes;
all resident code, furniture metadata, model tails, and saved layouts remain.
Experimental V3 saves still require their compatible V3 import profile and are
not safe to load in V2. Ordinary imported-villager move-in, conversations,
house visits, gifting, and saved identity need the remaining villager readers
and selection/profile integration.

The [house checkpoint](../docs/checkpoints/V3_VILLAGER_HOUSES.md) records current
cartridge hashes, focused checks, and native execution results.
