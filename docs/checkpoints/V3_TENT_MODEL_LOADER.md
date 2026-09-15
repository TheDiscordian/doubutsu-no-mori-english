# Tent-model DMA repair

## Result and cause

The complete tent now loads through the installed furniture DMA entry. Review
found that the expanded helper accepted callback-owned objects only for speed
bag. The preceding tent callback probe used a supplied model fixture, so its
passing draw/reader results did not exercise this later loader gate. The ABI-69
tent integration therefore rejected ordinary model DMA despite its installed
profile and callbacks. This is an implementation defect, not a test-setup issue.

`AF_V3_TENT_MODEL` adds the precise reviewed identity/index/vtable to the gate.
The complete object has no separate item-dependent DMA callback. Unknown,
disabled, mismatched, oversized, and incorrectly owned profiles still reject.
Static furniture and speed bag retain their existing handling.

## Construction and artifacts

`tools/v3_tent_model_loader.py` consumes the pinned tent integration cartridge
and report. It recompiles the expanded helper, checks/rebinds all eight public
entries and the bank-owner hook, refreshes the resident-prefix CRC and ROM
checksum, and reconstructs the whole output through its UPS. The directory,
resources, and all allocations retain their sizes. The bank-owner entry remains
at the same address, leaving that native owner resource unchanged.

Full output: `build/v3-tent-model-loader-01/`.

- ROM SHA-256: `6655157c072b0b2e291224c1f22e5d4c45ed9a6299c5a6e478ecaaaf257c35de`.
- UPS SHA-256: `b927cbb5cfdff131582a0046e1575c20c3d98b08e477d1738e6f10a56c671189`.
- Report SHA-256: `82c4ba4a5067d3debd19c5c459205efcba12c005bd371d627326f654b79950e0`.
- Helper: 1,760 bytes at `80465800`, with 288 reservation bytes spare;
  SHA-256 `36c3be66073d733b0d33f5c89e6edc21f2c22c26ef06a570eb9dd0f93b6e16d9`.
- Tent-only output: `build/v3-optional-tent-model-loader-01/`, ROM SHA-256
  `eb6db83eb6bafa9ef4eaf34318b85260b157a62c53bff300be6340851898868c`.

ABI 69, format-2 saves, selected dependencies, package layout, model banks,
catalogue/scoring, all artwork/callbacks, and native heap allocations are unchanged.
The offline composer retains 57 experimental options; empty/all selections
produce the exact V2/current full cartridges. Both served patchers remain V2.

## Verification

`python3 -m unittest tests.test_v3_tent_model_loader tests.test_v3_optional_composition -v`
passes **15 tests in 9.497 seconds**. The actual C DMA helper runs under address
and undefined-behaviour sanitizers, covering all rotations, bank reuse, invalid
rows/vtables/bounds/ownership, DMA failure, and retained static/speed-bag loading.
Cartridge checks verify the complete code and bridges, only intended changes,
resource/checksum retention, and current composition/dependency/save-codec rules.
No old cartridge is re-tested.

The initial silent native run passes **36 records, eight calls, and 24 assertions**.
Evidence: `build/v3-tent-dma-native-01/results.json`, SHA-256
`2a2f5737ddc1d795af243db2b1ea2c318ec68b2134a67bdf4efe7504d4dd10d5`.
It cold-boots the repaired cartridge, verifies the installed public bridge and
full helper, and executes actual ROM DMA into the Expansion Pak model bank.
All 4,288 model bytes match and remaining bank padding is untouched. Rotated
existing-bank reload passes. Disabled and wrong-vtable profiles reject without
modifying the bank. Saved state, owner/private guards, prefix, and no-fault
checks pass. Original bank contents/index/owner restore, the private allocation
is freed, the checkpoint restores, and the emulator exits cleanly.

The owner descriptor and bank slot are isolated fixtures. The test executes
the installed loader and real native DMA, not a copied callback. It does not
establish ordinary bank acquisition, GPU appearance, light interaction, summer
rewards, persistence, or hardware acceptance. No setup retry is needed; new
harness work stays within the batch limit. Retain those remaining gameplay
requirements and continue the full fire callbacks/audio and other donor work.

The selected tent dependency is unchanged: saves require a matching/superset
profile, and must not be loaded by V2. Ordinary cross-build reload is not newly
verified. Neither a private playtest nor source publication authorises switching
either web patcher before user testing and explicit approval.
