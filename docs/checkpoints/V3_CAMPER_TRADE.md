# V3 camper trade selection and rewards

## Deliverable

- Full ROM: `build/v3-camper-trade-runtime-02/animal-forest-v3-asset-loader.z64`.
  SHA-256 `d01afeb17c4c0a306e892037808268b675f8f02179dba7dd2261b397f03f55a9`.
- UPS: `build/v3-camper-trade-runtime-02/animal-forest-v3-asset-loader.ups`.
  SHA-256 `dfb606a8643dab1abb9729ae5d7a6686b152c413a39fcd72be9739852614f45b`.
- Build report SHA-256
  `9aa0289d9cc46fe9eb75ddfaa3d61de6bce085ceed96e651102a9c9ec0d0d56e`.
- Offline two-item profile: `build/v3-optional-camper-trade-01/`, kayak
  and propane stove. ROM SHA-256
  `697b095b990299bf198b64d97a18e48fad2cfdcaa3cda0096981048ab5c54c77`.
  All 59 experimental choices remain available to the offline
  composer; all/empty selections retain exact full/V2 output.

ABI 81 builds on the corrected official-credits cartridge. The single provenance
catalogue remains the authority for player-facing wording. This batch adds no
text and does not alter any text resource. Both served patchers remain V2.

## Implemented

The actual furniture/carpet/wall picker recognises enabled imported furniture
and excludes the last gift only inside the summer tent. It retains original
item conditions, random slot selection, and no-candidate output behaviour.

Summer trade preparation uses the actual donor normal-owner rules, including
the 20% tent-list roll followed by the separate 10% house-gift roll. The complete
ten-item camping list is profile-filtered. The donor's small-list duplicate
allowance remains, without re-enabling missing imports. Other exclusions and
the saved rare item are respected. The list choice carries into carpet/wall A
fallback, and fish/bug trades retain their clothing/stationery/fruit candidates.
Full English item-name insertion, existing normal state, final random/pitfall
selection, and original non-summer preparation remain connected.

The 1,344-byte compiled suffix uses 72 stack bytes for the picker and 128 for
common preparation, plus native callees. It extends the current normal owner
from 19,392 to 20,736 bytes; relocation storage becomes 2,272 bytes/560 entries.
The complete 23,008-byte load fits the existing 34,816-byte conversation buffer.
Both original physical resources remain, with the current aliases appended to
the existing import blob. No permanent RAM or heap allocation grows.

Owner SHA-256 `938af5b464f94542870a754b6dfaeb67df1395af9117a765608eb0085f84101f`.
Relocation SHA-256 `673c89ec6829445b3c8db15ad79ff3b50f2d4a87675ec4d7e5f04b66d633b0dd`.
The [campsite specification](../../specs/V3_CAMPSITE.md) records exact native
hooks, source-owner offsets, fallback semantics, and allocation limits.

## Verification

`python3 -m unittest tests.test_v3_camper_trade tests.test_v3_optional_composition -q`
passes eighteen tests. Six trade checks cover sanitized actual C execution,
all ten reward identities, threshold/house order, one/two/three/zero-item
profiles, rare/existing exclusions, exhausted-list termination, retained
categories, complete source/relocation checks, preservation, CRC, and DMA
identity. Twelve current composer checks cover dependencies, selected fields,
save profiles, and exact all/empty cartridge composition.

Initial native run: `build/v3-camper-trade-native-01/results.json`, SHA-256
`0dff425ab14777d5e9e2702ac811acc862295baf2bb90fc4debc9265a0c148ca`.
Twenty-three records include thirteen passing assertions and one failure.
Three complete owners load and relocate, and four pocket-selection cases pass.
The first common-preparation fixture mistakenly supplies unregistered `3260`,
which correctly returns no eligible input. Correct the fixture to registered
barrel `3224`; no ROM change is required.

Corrected remaining-only run:
`build/v3-camper-trade-native-02/results.json`, SHA-256
`cd4b302c7ea01a806956d3c61680f6dbb3cd7e10a7eb2930562daf769d2d9488`.
It passes 55 records, nine full native calls, and 37 assertions, without
replaying the four passed pocket cases:

- Actual loading/relocation of current normal, quest, and greeting owners.
- Complete common preparation with only `3364` enabled, then only `33B0` enabled,
  producing each expected camping reward through the real RNG and runtime
  metadata. Native carpet/wall candidates are `2616` and `2703` in both cases.
- The actual original non-summer body, displaced prologue, full imported input,
  and pitfall result, with the summer last-gift exclusion correctly inactive.
- Both original gift callback windows retain manager/count transport and store
  the full last-gift identity. The constructor resets it and preserves its
  original five-byte clear. The bounded callback is native `bzero`, not an
  award animation or complete conversation.
- The complete unchanged greeting initializer returns message 11947 and restores
  its stack, using actual current owner loading in ordinary lower heap memory.
  The earlier upper-scratch intermediate breakpoint remains unexplained; do not
  label its missing stop a confirmed game crash. This check supplies complete
  return evidence without changing the greeting code to satisfy the debugger.
- Saved-town restoration, guards, no faulted thread, fixture deallocation,
  checkpoint restoration, and clean isolated emulator shutdown.

The run is silent and uses an isolated cartridge save. No original-hardware,
ordinary conversation, handover-animation, or save/restart result is claimed.
The first partial run is retained, not relabelled as a complete pass.

## Continue

Finish remaining masked NPC readers and scene lighting/floor sounds, then
combine ordinary tent/NPC construction, entry/exit, conversation handover, and
saved camping acquisition checks. Retain the unresolved earlier exterior
construction/allocation result until ordinary integration classifies it.
Continue other donor groups and the full V3 queue; this batch does not narrow
the goal to camping or to the currently installed content.

Saved format 2 and selected identities are unchanged. A matching/superset
profile remains required; never load imported saves in V2. Ordinary cross-profile
reload is not established by the codec checks. This is not a complete-import
playtest handoff. GitHub development source is allowed; neither web patcher
changes until the user tests V3 and explicitly approves the switch.
