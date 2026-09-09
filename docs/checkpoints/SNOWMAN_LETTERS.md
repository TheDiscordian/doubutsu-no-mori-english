# Snowman letter integration checkpoint

## Implemented scope

Twelve complete English gifts, templates `0202..020D`, retain all 36 supplied
parts and twelve complete item names. The actor holds 24 prevalidated snapshots,
including both capitalization states. Full wording, manual breaks, native RNG,
recipient identity, gift, font, paper, and type are preserved. No extra
per-letter allocation or text loading is required. Native allocation and
full-mailbox/queue failure have no durable retry in the original perfect-build
caller; that policy is retained, not described as guaranteed gift retention.

The [specification](../../specs/SNOWMAN_LETTERS.md) describes the immutable table,
creator transaction, receipt gate, original actor ownership, and source binding.

## Artifacts

- Complete ROM: `build/snowman-letters-pilot/animal-forest-halfwidth.z64`, SHA-256
  `dc650cea15d03bfb05b776b733f71c4914b7a2ce5cd4b258f2d4063b378ee7ee`.
- UPS patch: `build/snowman-letters-pilot/animal-forest-halfwidth.ups`, SHA-256
  `3116b6e120799aaa3e0ccfbd8e1e4d46306b04ca3220c3b067107548b1276d44`.
- Actor: `build/snowman-actor/overlay.bin`, 18,384 bytes, SHA-256
  `bdf537175e7b2b82ef20f82b3b5ece33c5020907d6f103668101ac41c717d084`.
- Relocation: `build/snowman-actor/relocation.bin`, 1,104 bytes, SHA-256
  `115c1fb48957d81471b428d7a2e943ee404ae91d5d04211bbe8a9752a4107097`.
- Actor manifest: SHA-256
  `788e874aeaf55a12d01b245bed83d4e9adce8536223957cc5586ddf677ef3623`.

Both actor builds agree on image, relocation, and manifest. All previous DMA
payloads remain unchanged except the DMA table and Snowman ownership metadata in
main code. The original Snowman file/relocation rows move to their new VROMs.
The resident module, complete museum creator, font, and all earlier text remain.
Generated ROMs, extracted text, binaries, patches, saves, and logs stay ignored.

## Verification

- Four creator host tests pass; the same four ASan/UBSan tests pass. Every
  choice/capital pair, full field, exact metadata, rejected choice/capital,
  pointer alignment, overlap, read-only alias, and corrected-input retry is
  covered. The creator has no allocation, DMA, item, formatter, or reader import.
- Independent wrapper and receipt-gate assembly passes in
  `build/snowman-assembly/`; the release C creator uses zero stack bytes and its
  wrapper uses 32 bytes.
- Fifteen focused source/installer/accounting/scenario tests pass in 32.925
  seconds (`build/snowman-focused-tests.log`). Three final scenario tests also
  pass, including the actual player-index address and edge-only resume.
- The final combined Snowman batch passes all eighteen tests in 30.321 seconds
  (`build/snowman-final-tests.log`). Its two native-evidence tests bind the
  complete first-run cases, exact recorded fixture failure, corrected edge
  group, matching-ROM checkpoint, final state restoration, and blank saves.
- Twenty-four reader/relocation/accounting regressions pass: nine record tests,
  six formatter tests, seven combined-counter tests, and two relocation tests.
- Native run `build/smoke-snowman-02` completes all 24 original metadata/RNG
  comparisons, complete creations, and actual reward-queue deliveries, plus
  48 full readbacks. Both full-home and full-queue cases pass. The run then
  stops on the visitor test's wrong fixture address: it wrote `80126EA3`, while
  the verified native helper reads `80136EA3`. This run has 153 calls, 324
  passing assertions, and one failed fixture assertion. It does not reach final
  cleanup/checkpoint restoration and is not an overall passing run.
- The corrected `build/smoke-snowman-03` resumes the same-ROM checkpoint and
  runs only the remaining edge group. All five owner cases, four creator
  rejections, and one complete readback pass. All eighteen calls, 52 assertions,
  heap/stack/actor guards, restored live save/globals and checkpoint, blank
  isolated saves, and graceful shutdown pass. No completed 24-case group is
  repeated. Disabled creation-time text configuration still allows a complete
  fixed snapshot to be queued and read fully after configuration restoration.

Both runs are silent, four-MiB, and capture no screenshots. They load translated
actor code from the cartridge through the original overlay loader. The uploaded
16,912-byte original actor supplies comparison-only metadata and RNG. Direct
injected native calls are not evidence of normal perfect-build scheduling,
gameplay saving, or original hardware.

Native evidence hashes:

- First results: `512a473559b0a4b77b7f7f7f435d1c3a7de485b51574c9e5607b345c1a4e6eb1`.
- Corrected edge results: `1bfc02300595f697211e4b9ab067684591067baf146b0f7dc71de41f062628d3`.
- First scenario: `f4f2ff1a986788d5017af903f14cbd55cd6aa001462e8133932376cdf8fb9b37`.
- Corrected edge scenario: `aefe84b62104474007932105b598a2104099cf6e7f873bae5ff97346d6c79de1`.
- Corrected native helper: `399da93c9bccdf57dd2103922200639503083df0897e5b33e51a1381d2aa26b9`.
- Source checkpoint: `e4062cca98cd4c26955717790634f7e6c7fa59fcc3f9c97a6f6f80f72d872680`.
- Restored edge checkpoint: `4cf5258cded8b02763e739abab42fb01a0926690373e8d477a24e44c0fa6e45f`.

The work record includes two preflight corrections: persisted JSON approval
records needed lists rather than tuples, and the shared receipt-function guard
needed to include the existing, exactly verified NPC result shim. The first
emulator invocation stopped before startup because the rejected scenario had
not produced its files. No gameplay or hardware result is inferred from those
preflight checks.

## Remaining acceptance

Rebuild the actor with `python3 tools/build_snowman_actor.py`. The complete ROM
uses the [museum recipe](MUSEUM_LETTERS.md), retaining every previous option and
adding `--english-snowman-letters build/snowman-actor`, with output
`build/snowman-letters-pilot`. Prepare the silent batch with
`python3 tools/snowman_scenario.py --output build/snowman-scenario.json
--boot-output build/snowman-boot.json`. `--group edges` prepares an edge-only
scenario; `emulator_smoke.py --seed-state` requires the identical ROM and uses
the isolated source checkpoint. Never reuse a checkpoint with another build.

Continue the source-approved spotlight-item/reopening letters and other text
consumers. Normal perfect-build scheduling, full-mailbox gameplay,
queue draining, save/reload, review, and original hardware remain unverified.
The overall translation, title-image replacement, keyboard stretch goal, and
patch-only release requirements remain active.
