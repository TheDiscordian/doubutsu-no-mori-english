# V3 imported NPC draw routing

## Implemented boundary

The `--npc-draw` variant of `tools/v3_asset_loader.py` installs Punchy and Cheri's
native draw records, routes both NPC overlays to those records, and transfers
their full donor voice IDs into the existing actor. It does not enable move-ins,
complete audio playback, or claim playable villagers. Ordinary gameplay,
name/default/house, and persistence readers still need integration.

## Stable identity reservations

`tools/v3_registry.py`, registry version 1, assigns donor indices 216–235 to N64
identity indices 218–237. These are literal reservations, independent of selection
order; unimplemented slots remain unavailable. Native ordinary identities 0–215
and test identities 216/217 retain their IDs. Special characters retain `Dxxx`
identities and their original draw-table rows.

| Import | Donor identity | N64 actor | Texture bank | Voice sequence |
| --- | --- | --- | --- | --- |
| Cheri | `GAFE01-r0/villager/00E8` | `E0EA` | 426 | 285 |
| Punchy | `GAFE01-r0/villager/00EB` | `E0ED` | 429 | 286 |

These reservations do not establish saved-identity or roster-reader support.
No new identity enters ordinary selection in this development build.

## Records and memory

The draw variant uses configuration/blob ABI 2 and loads 16 KiB at
`80460000..80463FFF`. The asset-only variant retains ABI 1 and 8 KiB.
Header/startup checks, CRC, cache maintenance, object-table position `80461000`,
and original heap bounds remain unchanged. The draw variant's end guard is at
`80463FF0`; diagnostic allocations must not use that region as scratch space.

Twenty fixed 104-byte slots start at `80462000`. Each contains a big-endian
sixteen-bit actor ID, sixteen-bit voice ID, and 100-byte native draw record.
An empty slot is all zero. Slot index is the registry identity minus 218.
The builder binds every pilot row to its previously verified donor artwork.

Retain native model/skeleton, expression pointers, and species texture-memory
placement. Set the new texture bank. Copy donor scale, talk type, species index,
umbrella/eye-height flags, and collision dimensions at their verified offsets.
Reject unsupported extra flags. Do not copy the 108-byte donor structure into
the native 100-byte destination.

The native draw voice byte uses `FF` only for imported metadata lookup. All 327
original draw records are checked not to use that marker. Full voice IDs live
in the slot header. Metadata lookup validates actor and texture bank before
returning the full voice.

## Both native consumers

| Owner VROM | Original link base | Draw-copy entry | Constructor tail |
| --- | --- | --- | --- |
| `008681F0` | `809735B0` | `809809FC` | `8097F93C` |
| `008798C0` | `80995BF0` | `809A0AB8` | `8099FCEC` |

Patch each entry with an absolute jump to checked resident V3 code and a NOP
delay slot. Assert original instructions and no relocation at either changed
word. Neither overlay size nor relocation data changes. These are link
addresses; the native loader relocates the containing overlays normally.

Draw lookup masks the input to sixteen bits. Normal/test `Exxx` indices below
218 use their original row. Imported identities use their installed slots.
`Dxxx` lookup preserves the native same-event texture override through
`800AA14C`, then uses either that normal/imported identity or native special
row `218 + special_index`. Reject missing imports and invalid bounds without
changing the caller's destination.

Native rows remain in VROM `00E05000`, with an eight-byte header and 327 complete
100-byte rows. DMA **must** use an eight-byte-aligned temporary buffer, then
copy 100 bytes to the caller: real callers can supply destinations aligned
to only four bytes. The N64 DMA manager rejects those destinations. The helper
uses a 136-byte stack frame, within the original draw-copy frame's 144 bytes.

The actor's voice field at `+0930` is already a 32-bit word. Constructor-tail
bridges read the final draw row from the original frame, assign the full voice,
restore saved RA/S0 and SP, and return to the original caller. The first overlay
uses frame size `C0`, row at `SP+58`; the second uses `B8`, row at `SP+50`.
Both save RA/S0 at `+24`/`+20`. No actor layout grows.

## Reserved-bank streaming

Ordinary NPC construction has its own object-table lookup; it does not use
the shared scene allocator at `800C5AA0`. The two streaming functions are
`8097FDF0..8097FE7F` and `809A0378..809A0407`. Each finds a free preallocated
status, uses the requested object bank's VROM bounds, and schedules the existing
scene DMA. The callers provide `2800` bytes for models and `1620` for textures.
Both imported texture resources fit the complete native texture reservation.

The builder verifies each complete native function and changes only its
two-instruction table address at `8097FE24` / `809A03AC`: `8010DDD0` becomes
`80461000`. The original 410 table entries remain identical; banks 426 and 429
are now available to these consumers. Neither changed word is relocated by the
native overlay loader. Status selection, capacity limits, pending flags,
asynchronous completion, reuse/release, and all arena allocations remain native.
All newly built draw variants use at least configuration ABI 27 for this fix.
This configuration revision does not change saved layouts or import profiles.

The [gameplay checkpoint](../docs/checkpoints/V3_CHERI_GAMEPLAY.md) records the
actual acre-entry failure and the targeted current-build verification.

## Audio integration

Full voice transport is not full sound support. Native `Na_VoiceSe` at
`800F91FC` rejects IDs at or above 256. `Na_Inst` (`800FCE80`), melody start
(`800FCEEC`), and melody voice (`800FD280`) also contain eight-bit truncations.
Sequence-size and offset arrays at `80119240`/`80119640` each have 256 entries.
The cached ID is sixteen bits, but sequence-player ports use eight-bit tags;
count/continuation readers need coordinated treatment.

The donor has 299 melody records. DOL `melody_seq_size`/`melody_seq_offset` arrays
are at `800A9B98`/`800AA044`, each `4AC` bytes. Extract through actual DOL section
mapping, not RAM addresses used as file offsets. The donor audio header selects
sequence 248, offset `B2180`, size `1D580`, in `audiorom.img`. Cheri's fragment is
offset 116384, length 448; Punchy's is offset 116832, length 288. Neither is an
existing native fragment. Both include nineteen relocatable track offsets.
Inspect sequence opcodes and instrument-bank dependencies; do not substitute
another villager's instrument or strip padding by guesswork.

The native combined melody is sequence 205, offset `A4ED0`, size `18D10`, within
the audio-sequence resource at VROM `00027130`. Its original physical fragment
base is `000CC000`. The donor interpreter's `EB` command selects a bank-map
selector and instrument. Pilot selector 3 resolves to actual bank 2, not bank 3.
The [audio variant](V3_VILLAGER_AUDIO.md) verifies all four used instruments
and samples, installs the fragments, and connects the widened native paths.
That variant uses ABI 3; the draw-only variant does not add audio support.

## Verification and compatibility

The [checkpoint](../docs/checkpoints/V3_NPC_DRAW.md) binds exact artifacts and
focused host/native evidence. The native fixture targets both real overlays
through the native loader and their actual patched draw entries/constructor
tails. Synthetic actor/frame setup is explicit: it does not prove complete NPC
construction, animation, dialogue, audio, or saving.

Use disposable saves. No saved layout changes, but imported-profile and cross-
version save compatibility remain unverified. Stable V2 and both patchers stay
unchanged. No V3 browser import is selectable yet.
