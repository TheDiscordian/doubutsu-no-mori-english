# Summer event-manager integration

## Implemented

ABI 76 extends the complete installed English event-letter manager with the
summer camper. All 28 original controls, their callbacks, original BSS addresses,
letter work, and save/destructor retries remain. The 29th control connects the
installed calendar and chooser to saved identity, independent visitor
registration, native outdoor tent placement/removal, and indoor registration.
Only actual selected camping content enables the event.

Selection persists its full native/imported identity in event save area zero.
Registration failure does not reroll it. A new successful selection resets the
session greeting flag; the first conversation still needs its completion hook.
An existing tent or live temporary marker is retained. Missing fields and failed
allocation/placement/removal leave the transition pending for retry. Stop does
not clear an Animal that a live actor may still reference.

The installed owner at VROM `03800000` is 40,048 bytes; relocation VROM
`03810000` contains 2,192 bytes and 542 records. All 433 original records remain;
98 relocate the copied control table, and eleven relocate the new suffix.
The table at linked `80965180` has 29 rows of 32 bytes. The existing daily list
has capacity 32. All original control pointers remain correct after relocation
at each of three checked RAM bases. Actual native load/relocation also passes.

The loaded manager grows by 1,920 bytes and its transient relocation resource
by 432 bytes. The actor stays 592 bytes. Permanent resident reservation,
normal heap limits, model banks, save formats/profiles, and 3,389 DMA file slots
stay unchanged. The new physical resources are appended to checked import
storage; virtual identities and DMA adjacency remain intact.

## Current artifacts

- Full: `build/v3-campsite-manager-runtime-02/animal-forest-v3-asset-loader.z64`.
- Full SHA-256: `12715890318357a7150abeb8d29d59ed6e867ad00e247f9961be1febed62c195`.
- UPS SHA-256: `c179180a6dfad97de7f76576ef6846a8ff0f16335af305c2ebf9e6f9a609e5a0`.
- Build report SHA-256: `f0c29e139ad55b84df92dd073ac60e71c928c287cc713d7fa98a3b73b2fb9f73`.
- Manager SHA-256: `937af8a6e83b9c52ec06c363800ea4db26b198857374b9b475de6776b26bf390`.
- Relocation SHA-256: `d6de267f91feebef41bc1a18d2460f70ca560a1664c5b20e1c94b7ab4d0db54f`.
- Ten-item camping subset: `build/v3-optional-manager-01/animal-forest-v3-asset-loader.z64`.
- Subset SHA-256: `d9fa3797b6afae21ddd4fc048e14bc47baef940e06e9473a9182ae647fd92f6c`.

The offline composer retains 59 experimental choices, deterministic individual
selections, and exact all/empty full/V2 output. This is not a complete-import
playtest handoff. ROMs, patches, donor assets, saves, and reports remain ignored.
Development source may go to GitHub on `v3/optional-imports`; neither local nor
public web patcher may switch to V3 before user testing and explicit approval.

## Verification

`python3 -m unittest tests.test_v3_campsite_manager -v` passes three checks.
`python3 -m unittest tests.test_v3_optional_composition -v` passes twelve checks
against the final full-cartridge/report pins. These include sanitised actual
adapter/chooser tests, complete English-owner retention and relocation, checked
native bindings, DMA/CRC verification, all/empty composition, and dependency
filtering. No older cartridge is re-tested for this batch.

The silent current native test uses `tests/scenarios/v3_campsite_manager.json`.
`build/v3-campsite-manager-native-02/results.json` contains **79 records,
42 native calls, and 51 passing assertions**, with zero failures. Its SHA-256 is
`453e9bf90735aca8e51e880c6ca8e998ecfd64d459dd9f90143d2ce8fbafcd66`.

Actual native execution covers the full extended owner load/relocation, an
original control plus the summer control in the daily list, Saturday calendar
selection, native selection of Punchy, saved full identity, default/outfit/alias
registration, indoor start, repeated identity retention, failed outdoor
placement and dispatcher retry, all nine tent foreground cells, repeated tent
retention, failed stop and retry, and removal with housing-lot restoration.
Native town Animals, all NpcLists, the import save runtime, and guards remain
intact. The test restores modified RAM and the saved emulator checkpoint,
resumes without a fault, and shuts down gracefully.

### Corrected runtime defect

The initial native run found that the engine's error flag aborts an event rather
than scheduling a retry. `mEv_set_status(type, 20)` clears all other status bits;
the native status reader then masks active/start queries while error is set.
Native placement/removal also set that flag on failure. The initial adapter's
zero return therefore could not make the dispatcher retry a rejected edge lot.

The corrected adapter avoids setting the flag for ordinary setup failures and
restores both the actual daily status and aggregate change word when native
placement/removal fails. The native retry then succeeds without manually
reactivating the event or rerolling the camper. Host mocks use the same
destructive error semantics. The failed runtime-01/native-01 artifacts remain
ignored evidence, not the current composer input or a passing result.

## Remaining work and save boundary

Complete masked NPC construction/quest routing, English first greetings and
subsequent conversations, first-greeting completion state, selected summer
rewards, and scene lighting/floor sounds. Ordinary move-in must exclude the
active camper after appearance-history resets; marking it seen once is not
sufficient. The complete V3 goal also retains other donor content and browser
composition work.

The native test uses a checked field-data fixture, not a constructed gameplay
scene. It does not prove GPU appearance, ordinary entry/exit, conversations,
reward acquisition, the complete event-finish traversal, or save/restart.
Generated blank FlashRAM is not persistence evidence. The earlier exterior
field-background allocation failure remains unresolved; this test does not
classify or close it.

Saved format 2 and selected identities are unchanged. Codec matching/superset
acceptance and missing-dependency rejection retain their existing evidence;
ordinary cross-profile save/reload remains unverified. Never load imported saves
in V2. Private developer verification and any future private test handoff do
not authorise switching either served patcher.
