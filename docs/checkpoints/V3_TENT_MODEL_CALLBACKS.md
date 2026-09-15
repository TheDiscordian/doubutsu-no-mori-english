# Tent-model native light callbacks

## Completed component

The complete tent model has compiled native create/move/draw/destroy callbacks.
They preserve its switch-controlled light, floating-point fade, all sixteen
palette entries, four model parts, and draw order. There is no shared mutable
light state or palette heap allocation.

The adapter uses four bytes of otherwise unused per-instance joint storage.
Verified native constructor/update/draw guards leave that storage to the callback
because this profile has no generic rig or texture animation. Every rendered
palette belongs to the graphics frame, so subsequent updates, removal, or actor
reuse cannot alter previously submitted palette data.

The current cartridge remains **ABI 68**, and this tent is **not installed or
selectable yet**. Native execution, GPU appearance, ordinary switch interaction,
acquisition, and persistence remain unverified. No new playtest ROM is handed
over. Both web patchers and saved data remain unchanged.

## Artifacts and source

Complete callback output: `build/v3-tent-model-callbacks-02/`.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `code/code.bin` | 580 | `0a4753b07d64bcf911b23f491e34b64509a45a920c212b24b1d635eef8711cb7` |
| `callbacks.json` | — | `c25559956fd409f0472d259811983144257218216e1804f1cb8fde5a417f1ee8` |

Source: `overlays/v3/tent_model.c`, `overlays/v3/tent_model.ld`, and
`tools/v3_tent_model.py`. The existing pinned Docker compiler performs the
big-endian VR4300 build. Callback code has no writable data/BSS and only two
external dependencies: `_Matrix_to_Mtx` at `800E139C` and `osWritebackDCache`
at `8002FE00`. Absolute calls are checked against those exact targets.

| Entry | RAM |
| --- | --- |
| create | `80483400` |
| move | `8048341C` |
| destroy | `80483490` |
| draw | `80483498` |
| code end | `80483644` |
| proposed vtable | `80483700` |

The proposed object VROM is `0244E000`; it is not allocated by this component
builder. The future cartridge installer must check that model slot and code/table
reservations against the actual package before writing them. The generated
68-byte profile and five-pointer vtable are retained in `callbacks.json`.

The complete object remains
`build/v3-camping-actor-art-01/tent-model.n64obj.bin`, 4,288 bytes, SHA-256
`b56aeeb6e542e9742706ca510e054fdb81f87a82e91b9ff684ed669d32c14af7`.
All four segmented model pointers and both palette offsets match that artifact.

## Executed checks

`python3 -m unittest tests.test_v3_tent_model -v` passes all three focused tests
in 1.636 seconds:

- The original and current ABI 68 ROMs retain the exact relevant rig guards,
  callback calling conventions, native switch toggle, matrix converter, and
  cache-writeback function. This is binary/source evidence, not execution.
- Complete source palettes/models, scalar profile, absent generic rig/texture
  state, callback entries, source hashes, absolute dependencies, and vtable
  bounds are checked. Invalid object alignment and out-of-code callbacks reject.
- ASan/UBSan executes the actual C callbacks with the complete converted palette
  endpoints. Two independent instances fade in opposite directions and reverse
  mid-fade, then reach their endpoints. Tests check all sixteen colours, unchanged
  transparent entries, actor-write guards, six exact commands, frame ownership
  after updates/destruction, and tight/insufficient arena bounds.

The first source preflight compared the entire boot owner and rejected existing
unrelated startup/fault changes. It now checks the exact 116-byte cache-writeback
function against its established native hash and current code. No guard for the
actual callback dependency was removed. The complete build then passes. The
initial compile-only artifact in `build/v3-tent-model-callbacks-01/` is retained;
the `02` directory is the complete reported output.

No native emulator scenario or new native harness is run in this batch. Do not
relabel the host callback execution as N64/GPU or hardware verification.

## Next integration

1. Use the current full ABI 68 cartridge and report from
   `build/v3-camping-runtime-01/`, not a replay of earlier build chains.
2. Reserve the checked object range and callback/vtable bytes in the existing
   import resource/package. Add the full custom profile and exact English item
   row for `336C`/index 1243; do not register it as callback-free static furniture.
3. Add its non-orderable catalogue entry, actual framing, native HRA/feng data,
   and selected save dependency. Preserve the `ftr_listTent` acquisition route.
4. Refresh the package/prefix/startup checksums, build into a new cartridge, and
   extend the offline composer without changing either served patcher.
5. Combine the affected native callback/reader checks within the existing setup
   budget. Ordinary switch behaviour and persistence stay open until tested.
6. Continue the two fire callbacks and the summer-camper reward system. These
   tent callbacks do not satisfy those separate required behaviours.

No save format or profile is changed by the component build. The eventual
installed tent changes the selected-import dependency set; warn about profile
compatibility before handing over that new ROM.
