# V3 clothing mannequin checkpoint

## Artifact and implementation

`build/v3-clothing-display-01/animal-forest-v3-asset-loader.z64`, ABI 41.

- ROM SHA-256: `8de718f1531e8d5d3652d74664deb7ff3a7ca9352839dc49db7522dc8432ab69`.
- UPS SHA-256: `a8247a577517648fe885cec2f62c50d082dcf454a20de715016880f70c86622e`.
- Resident prefix SHA-256: `f94af1d40b00aac387438dd391b6297473e54982d76062e231abafaa34fd214b`.
- Native relocated program SHA-256: `5d35b0173f4e3d2d6db983b8794fbb4f162b9a135d06a02c85701fd91a473c1a`.
- Index helper SHA-256: `ef640b470700df9fc4d6d2ed0f0fab8a9a6ad2a80f2d656a330c3c03122cf67e`.
- Expanded furniture helper SHA-256: `a788eac745712a68895d6748f092d0f4f11b7207c57436571fdecca1c2bb4880`.
- Table initializer SHA-256: `1cdd3eec2ef0465d84fb3f8db7dc9fe8171666f6094c56eac30faad870aa4a4e`.

The [specification](../../specs/V3_CLOTHING_DISPLAY.md) records stable display
`3AFC`, pocket garment `34BF`, native mannequin callbacks and geometry, memory
ownership, profile checks, and remaining ordinary-reader work. The first build
succeeds with the pinned Docker compiler. The model uses 4,128 of 5,120 bank
bytes. All native garments, resources, and heaps remain intact.

## Focused checks

`build/v3-clothing-display-tests-02.log` records three passing tests, including
explicit zero-padding checks around each new resident reservation:

- Sanitized selection, original and imported indices, four rotations, bank
  ownership, reload, missing dependencies, malformed profile rejection, and
  complete 2,051-entry initialization with guards.
- Complete relocated native program retention outside the nine-word index
  adapter, original profile/draw code retention, installed helper code, preserved
  resident gaps and every other resource, unchanged save code, the single added
  selected-profile bit, startup CRC/ABI, and exact UPS reconstruction.
- The real format-2 decoder accepts the preceding profile under the expanded
  profile, accepts matching new profiles, and rejects a new-profile bank under
  the preceding profile with `AF_SAVE_PROFILE_MISSING`. Rejection preserves
  the entire destination. Banks are independently packed in private host memory.

No original save is modified and no previous ROM is replayed.

## Native check and bounded correction

The initial `build/v3-clothing-display-native-01` run completes 76 records,
including all four imported mannequin loads and identity rotations. The next
direct draw call is rejected by the test helper's entry-address limit below
4 MiB. The draw routine is not invoked by that failed call. The emulator shuts
down with the test marked incomplete; this is a verified test-setup limitation,
not an observed game crash.

The one corrected retry uses the existing private-allocation jump-wrapper
pattern, verifies the complete resident mannequin, and performs native data/
instruction cache maintenance before calling the installed draw routine.
No cartridge bytes or general debugger permissions change for this correction.

`build/v3-clothing-display-native-02` passes all 116 records, restores its
checkpoint, resumes, and shuts down normally. Passing evidence covers:

- Complete startup profile/bank arrays, both expanded-table guards, and actual
  relocation of the current room owner and BSS.
- Both static furniture imports, retained original profile allocation and model
  loading, bank selection, reload, release, and native cleanup.
- The imported clothing profile through the actual bank selector and all four
  full-index reloads, matching all 512 texture, 32 palette, and 3,584 model bytes,
  with all remaining bank padding untouched.
- All four inverse runtime-index rotations returning `3AFC..3AFF`.
- The exact four native drawing commands, command-pointer advancement, and no
  overwrite after the private list.
- Imported profile retention through cleanup, complete restored external table
  reservation, first 32 KiB of resident memory, fixture/stack/translation guards,
  and a zero faulted-thread pointer.

This is native component execution, not ordinary house placement, GPU appearance,
catalogue ordering, acquisition/payment, or save/restart evidence. No physical
audio is emitted. New test work remains within the batch's 30-minute budget.

## Compatibility and next work

The new profile adds display dependency bit `80` at byte 119 without changing
format 2 or its codec. Older profiles lack that bit and reject new saves.
The focused decoder proves the forward profile addition, not an ordinary
cross-build reload. Preserve existing builds and save backups; do not imply
both-way compatibility from unchanged saved formats.

Keep global pocket/display conversion uninstalled until shared item metadata,
collection, HRA/feng shui, and special readers accept the alias. Then complete
catalogue/home display, normal acquisition, and persistence. The full remaining
villager/item and browser-selection scope stays open. Both served patchers stay
V2 pending user testing and explicit approval.
