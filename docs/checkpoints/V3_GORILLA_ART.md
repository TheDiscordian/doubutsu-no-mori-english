# V3 Yodel model and complete villager-art bundle

## Artifacts

`build/v3-gorilla-art-02/` supplies the complete converted Yodel model:

- Model: 10,112 bytes; SHA-256
  `ef7993c2259d3e910cdf7ff966132f6c067b046c81059380aaf48aa61085b10d`.
- Manifest SHA-256:
  `7e5912b8ee5f5343584790e89b2e2de87b9cbdb9972b7efa1041aa7b69da669c`.
- Generated native command-source SHA-256:
  `7e116c502203fb2d06b6f5b8096683ab7a9d159b40d45423abe002b7e0dafd0e`.

`build/v3-all-villager-art-01/` combines all twenty added villagers and all
sixteen required accessories: 38 files, 162,016 bytes. Manifest SHA-256:
`3c0e9a645d457feddbc17be2dc12eb66670313300d373b6b5a35c70fbef704a5`.
Yodel's complete 5,664-byte texture object has SHA-256
`b49ebadc9665debe1a9ede8c3725501e3abde4dcf3de7bbc9c47d7705a481ba4`.
All 35 files from the nineteen-body bundle remain identical.

Construction:

```sh
python3 tools/v3_gorilla_art.py --output build/v3-gorilla-art-02
python3 tools/v3_villager_art.py --all-supported \
  --accessories build/v3-accessory-art-03 \
  --models build/v3-gorilla-art-02 --output build/v3-all-villager-art-01
```

The model-only first attempt rejects actual repeat wrapping on body tiles
because the initial guard incorrectly permits that mode only for clothing.
Inspection identifies the exact body/material commands; the corrected explicit
mode guard retains those repeats. The second construction compiles successfully.
No emulator or save is involved in this converter correction.

## Verification

`build/v3-gorilla-art-tests-01.log`: 26 focused tests pass in 70.188 seconds.
Seven new tests cover complete vertices, all 284 compiled triangles and matrix
assignments, native render states, palette/wrapping/masks/extents, the full joint
hierarchy and segment pointers, buffer bounds, complete Yodel body/expressions,
all-twenty bundle retention, and refusal of missing/corrupted model dependencies.
Nineteen existing focused body/rig/dependency checks also pass on the changed
converter. These are component checks, not replayed historical cartridges.
Python compilation and diff checks pass.

The source comparison distinguishes 431 original native vertices from 429 donor
vertices; comparing only the donor-sized prefix would miss the last two native
vertices. The donor rig still matches all 26 native joint records. The complete
converted object fits the existing 10,240-byte NPC model buffer with 128 bytes
spare, without dropping donor triangles or substituting native geometry.

No native animation, GPU appearance, ordinary gameplay, or hardware execution
is claimed. The ABI-50 cartridge, saves/profile, both V2 patchers, and trailer
remain unchanged. Generated assets stay ignored.

## Next integration constraint

The current object table has 430 entries at `80461000`. Extending it to 432
entries ends exactly at `80461D80`, where the existing native growth-permission
copy starts; extending it to include sixteen additional accessory banks would
overwrite that copy. `overlays/v3/villager_selection.c` reads the copy, and
`specs/V3_VILLAGER_SELECTION.md` owns its bounds. Relocate/verify the affected
storage or use an explicitly managed separate accessory allocation before
expanding further. Do not assume space merely because the models fit their
per-actor buffers.

Assign stable model/texture banks, connect the new skeleton pointer, and
implement accessory attachment and cleanup. Then connect remaining voices,
text/defaults/houses, explicit town behaviour, moves, and persistence. Both
web patchers remain V2 until user testing and explicit approval.
