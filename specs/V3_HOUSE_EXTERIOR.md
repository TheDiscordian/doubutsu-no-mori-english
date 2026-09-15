# V3 imported outdoor houses

## House identity handling

Imported villagers `E0DA..E0ED` own outdoor house IDs `50DA..50ED`.
`tools/v3_house_exterior.py` connects those twenty IDs to the native house
profile, object, palette, shadow, door-knock decision, NPC proximity check, and
daily-growth protection. All original identities and other structures retain
their existing decisions. This requires the complete installed house/default/
town roster; it is not independent evidence of arbitrary profile composition.

The native structure selector uses an exclusive `50DA` upper limit. Values after
that limit enter a different structure table indexed from `5800`; an imported
house must not enter that negative-index path. The installed limit is `50EE`.

| Consumer | Native instruction address | Applied instruction |
| --- | --- | --- |
| Player door-knock decision | `808BB130` | `286150EE` |
| NPC house proximity | `8097714C` | `286150EE` |
| Structure actor/artwork selection | `809E8E50` | `286150EE` |
| Daily-growth first cell | `80AB2278` | `286150EE` |
| Daily-growth second cell | `80AB22EC` | `286150EE` |
| Daily-growth protected structure | `80AB3554` | `284150EE` |

Only immediate bounds change. Register operands, delay slots, branches, complete
other instructions, and relocation resources remain unchanged. Every changed
owner is verified against its complete parent hash. The formerly inclusive
daily-growth bound retains every original result and admits only the additional
actual house identities; the new one-past identity is not admitted.

## Storage and compatibility

ABI 59 changes no saved format, selected profile, or memory allocation. The
compressed daily-growth owner is retained physically and receives an uncompressed
read-only alias at blob offset `12CB10`, preserving all other file/audio positions.
Blob length is `131690`; the 32-MiB cartridge has 3,088 bytes of tail space left.
New content beyond that capacity requires an explicit larger-ROM decision in the
builder. No unchecked overwrite or virtual overlap is permitted.

The selected profile is identical to ABI 58. No new ordinary cross-build reload
claim follows. The prior dependency warning still applies to builds before ABI 58;
retain backups, and do not use V2 with imported saves.

## Temporary foreground markers

The native house actor represents loaded houses with temporary foreground IDs
`F005 + villager_index`. Extending that formula directly produces `F0DF..F0F2`,
overlapping original player houses and other structures. The player-house actor
uses `F0DF` as its own base, so widening all dummy ranges or shifting the original
IDs is not an acceptable solution.

Separate fixed imported marker IDs and their actual consumers remain required.
The existing original-marker constants are deliberately unchanged by ABI 59.
The completed actual-house selector fix does not establish safe final marker
handling or complete house interaction/persistence. The
[checkpoint](../docs/checkpoints/V3_HOUSE_EXTERIOR.md) records the confirmed fault,
corrected house construction, and incomplete entry result. Both patchers remain
V2 until the user's testing and explicit approval.
