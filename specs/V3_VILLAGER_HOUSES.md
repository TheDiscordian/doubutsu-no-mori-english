# V3 villager house data

## Installed scope

`--villager-houses` installs Cheri's complete two-layer GAFE01-r0 house alongside
the existing furniture, scoring, and save foundation. The complete `--speed-bag`
variant also installs Punchy's two layers and imported cherry-shirt default.
Neither variant enables move-ins or changes the browser patchers. The combined
house/default build passes focused host checks; native foreground arithmetic
verification remains unresolved, so ordinary house integration is not accepted.

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
All 218 original rows are retained. Cheri's row is `00003F2103780379`.
The complete variant adds Punchy's row `02012714037E037F` at fixed index 237.
All uninstalled import rows remain zero. This expansion is not an eligibility
decision; move-in flags stay disabled.

The Cheri-only foreground has 224,816 bytes: two appended 518-byte rows and
four alignment bytes, ending at `011E1E30`. The complete variant needs 225,848
bytes and cannot fit before the next native resource at `011E2000`. It moves
the complete foreground to the checked `03F60000..03FA0000` reservation and
ends at `03F97238`. All 432 original rows precede the four imported rows;
the complete 436-row resource is eight-byte aligned without padding. The original DMA identity
is retained, and adjacent native files stay unchanged.

Checked instructions connect the new bounds:

- `800AB194` and `800AB1B0`: both allocation routes of `mNpc_SetNpcList` use the
  house-table end `00E02770`. Native copying, placement, and cleanup remain.
- `80086104`: the NPC foreground load ends at `011E1E30`; the native divide by
  518 obtains 434 records in the Cheri-only variant and ignores its padding.
- The complete variant changes both signed-low address pairs at
  `800860FC` / `80086108` and `80086100` / `80086104` to the relocated start/end.
  The assembled arithmetic represents 436 complete records. The native test
  instead reports 492; this discrepancy is unresolved, not a passing check.
- `80086118` and `8008611C`: allocate 1,992 bytes for 498 sorted pointers,
  covering every fixed import layer reservation. Sparse slots remain null.

The complete native functions are checked before five words change in the
Cheri-only variant or eight in the complete variant. The house-table allocation
grows by 160 bytes. Foreground allocation grows by 1,040 or 2,072 bytes, and
the temporary pointer array by 160 bytes. Native heap bounds do not change.

The complete house/default build uses ABI 50. Its save profile and format are
unchanged from the speed-bag gameplay build; cross-build reload is expected but
not independently verified. V3 saves still require compatible V3 imports and
must not be loaded in V2. Ordinary Punchy gameplay, house visits, gifting, and
saved identity remain unverified.

The [Cheri checkpoint](../docs/checkpoints/V3_VILLAGER_HOUSES.md) retains the
accepted component evidence for that variant. The
[combined checkpoint](../docs/checkpoints/V3_PUNCHY_HOUSE.md) records current
artifacts, focused checks, and the unresolved native result.
