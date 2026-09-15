# V3 islander arrival rooms

## Town adaptation

The GAFE01-r0 islanders have sparse arrival rooms: each contains one furnishing.
Their separate furnished layouts belong to the island gift/progress system and
contain dynamic `FEB3..FEC2` placeholders. Copying those layouts as ordinary town
houses would assume an unimplemented island subsystem and alter their initial
contents. The town imports retain the authentic arrival rooms instead.

`tools/v3_islander_houses.py` binds all eighteen islander identities to the actual
`npc_grow_list`, `npc_house_list`, and `fgnpcdata.bin`. It verifies the separate
best-layout table and island room consumers, rejects dynamic gift placeholders,
and preserves each arrival room's house type/palette, six-by-six usable area,
furnishing position/orientation, entrance, and complete secondary layer.

The donor uses zero in 190 cells outside the room and entrance. Those exact
outside cells become the N64 layout's `FFFF` empty padding. The converter
checks their complete position mask; a zero inside the usable room is not
silently normalised. Walls, doors, furniture, and four-byte layer tails retain
their source meanings. No arrangement is generated or filled with substitute
furniture. Island furnishing quests and evolving island-room state are not
claimed as ported.

## Actual furnishings and surfaces

| Villager | Arrival furnishing |
| --- | --- |
| Maelle | pineapple bed |
| O'Hare | Nook's portrait |
| Bliss | petal parasol |
| Drift | red clock |
| Bud | round cactus |
| Boomer | extinguisher |
| Elina | red sofa |
| Flash | croton |
| Dobie | tea vase |
| Flossie | pear dresser |
| Annalise | sunflower |
| Plucky | pine chair |
| Faith | wobbelina |
| Yodel | scale |
| Rowan | gold econo-chair |
| June | daffodil |
| Pigleg | globe |
| Ankha | Master Sword |

All eighteen have reviewed existing N64 identities. Master Sword, pineapple bed,
and sunflower additionally use pinned identity-sheet rows 140, 237, and 468,
with matching model/texture references, exact donor names, and verified native
Japanese source records. This is the existing shared-item review mechanism,
not approval inferred solely from equal item numbers. Petal parasol maps
`1D1C` to `1CBC`; red clock maps `1E68` to `1DB8`. Rotations remain intact.

Every wall and floor is compared against the complete native artwork after
donor texture/palette conversion. Each has exactly one matching native record.
No new furniture object or room-surface asset is needed for the arrival rooms.

## Installed layout and storage

All twenty imported villagers have fixed main/secondary house slots within
856–895. The eighteen islanders occupy their previously empty eight-byte house
records; original villagers, the two native tests, and Cheri/Punchy remain intact.
The complete house table stays 1,904 bytes. The foreground contains 472 records:
the retained 432 native rows plus all forty imported layers. It occupies
244,496 bytes, with no partial row or trailing alignment record.

The existing sparse pointer table stays at 498 entries. Only the foreground
loader's two end-address instructions change; they retain signed-low address
construction and the original complete scanning/selection implementation.
The scene foreground allocation grows by 18,648 bytes. No resident code,
accessory/audio package, sparse-table allocation, or saved field grows.

The new foreground is stored read-only at blob offset `E3000`. Its original
virtual file identity `03F60000` points at the same physical bytes through a
separate DMA entry. The two virtual ranges do not overlap. This deliberate
physical sharing retains the blob's original position, all fixed audio/sample
positions, every other file location, and the old foreground bytes. Both file
views are read-only; neither is a mutable alias. The expanded blob is 1,174,288
bytes, within its two-MiB virtual reservation and existing 32-MiB cartridge.
Build checks reject overlaps, nonempty destination padding, or changed inputs.

## Verification and remaining work

The [checkpoint](../docs/checkpoints/V3_ISLANDER_HOUSES.md) records five passing
source/cartridge tests and the combined native check. Native checks load all
forty appended layers through actual DMA, build every sparse pointer, initialise
native/Maelle/Ankha/Punchy house records, and transfer the representative rooms.
They do not establish ordinary house entry, the full scene's larger foreground
allocation, move-in progression, or villager persistence.

ABI 56 retains ABI 55's exact save profile and formats. Same-profile loading is
expected in either direction, but ordinary cross-build reload is not newly
verified. Preserve backups; older builds missing imported dependencies still
reject these saves. V2 must not load imported saves.

All move-in flags stay off, and donor growth permission remains 2. Explicit
town schedules/dialogue, remaining gameplay readers, ordinary move-ins, and
persistence require integration. The new audio sample-playback issue remains
unresolved. Both web patchers remain V2 until user testing and explicit approval.
