# Shared console furniture interaction

## Current cartridge

ABI 284 is `build/v3-console-disk-room-imports-01/profile-runtime/build-lock.json`.

- ROM SHA-256: `38dfbe6905917d5f0792cbad451d1d1f29b39bc2f3bfb4deac0e5625c3bc09d5`.
- UPS SHA-256: `a5e1a762dacaacfbd2859b1dbac89e4f2ebedec81fb822697103840f6b4a3e40`.
- Shared category plan: `build/v3-console-disk-room-imports-01/pipeline.json`.
- Twelve complete additional console profiles and models are installed. Eleven
  remain inactive pending their actual reward routes. Excitebike uses the donor
  lottery route, catalogue reordering, source scoring, and its individual
  experimental selection. It is not gameplay-certified.
- Clu Clu Land D has its complete model, disk image, native engine, and profile
  installed. Native gameplay and acquisition remain. The separate game-twenty disk
  furniture has no payload in the supplied donor and stays explicitly unused.

The import-free baseline, main V3 lock, trailer, and both V2-13 patcher deployments
are unchanged. V3 publication still requires user testing and approval.

## Shared import path

The ordinary category command prepares the whole matching batch, reuses every
complete 4,880-byte model, installs the shared callback once, stages all twelve
implemented profiles, and promotes the item whose acquisition is implemented:

```sh
python3 tools/v3_furniture_pipeline.py import \
  --category constant-model-sequence-pending-lifecycle \
  --base-lock build/v3-console-disk-session-01/build-lock.json \
  --reuse-assets build/v3-console-room-imports-01/prepared \
  --output build/v3-console-room-imports-next
```

No model compilation is repeated. All three model lists, their textures/palettes,
and the linked draw sequence are retained per console. The category name records
the source callback shape; checked runtime bindings separately establish which
profiles have their lifecycle installed. No per-game installer is introduced.
Planning verifies the complete installed disk dependency before admitting QD.
Staging changes one readiness byte, publishes its startup checksum, and writes
the full canonical profile/item records. The disk code, room callback, all prior
models/profiles, and nineteen game payloads are retained. Subsequent planning
skips installed profiles. Acquisition remains explicit:
HomePage codes, island rewards, and special presents are not ordinary shop stock.

Registry version ten reserves source IDs `1DC4..1DF0` at additive destinations
`3C4C..3C78`, preserving all prior destinations. The single provenance catalogue
credits all twelve installed names to the actual English donor's `ftrName_table`.
These are fixed identities, not checkbox-order assignments.

## Native dispatch

The 344-byte callback occupies previously unused packet space at `804FB000`.
Twelve source-derived bindings start at `804FC000`; the five-slot native vtable
is at `804FC7E0`. All remain inside the existing authenticated startup packet.
No resident allocation, actor growth, native room rewrite, or saved field is added.
The streamed image code, complete metadata/pool, and save storage remain intact.

The callback validates its table, canonical/aliased runtime index, enabled native
profile, expected callback pointer, and matching live room owner. It forwards
changed-switch interactions to the native clip's `54` callback, preserving busy
and hidden-message checks, the normal play prompt, and native launch/return flow.
Five complete native dependencies are hash-checked. GBA IDs remain in source
receipts; N64 cannot supply the GameCube link-cable feature.

## Evidence and limits

Five focused checks in `tests.test_v3_console_disk_room` pass across two targeted
invocations: complete staged profile/artwork, retained runtime/resources/saves,
damaged-dependency rejection without mutation, idempotent binding and planning,
explicit absent-donor classification, and four private browser/offline builds.
The art receipt records one reused model and zero compiler containers.

The unchanged callback retains five checks from `tests.test_v3_console_room`:
sanitized callback boundaries, complete installed models/profile bindings and
retained resources, malformed-binding rejection, repeat-plan skipping, and four
private browser/offline compositions. The retained-resource test initially
compares shared startup digests as unchanged; the corrected assertion permits
only the digest update caused by the new packet CRC. Its targeted retry passes.
The host callback substitutes the native prompt function; it is not gameplay.

Two silent native setup attempts are retained, not looped:

- `build/v3-console-room-native-01/results.json`: complete startup packet and
  selected Excitebike profile match; the 122,880-byte general-heap allocation
  returns null before any room callback executes.
- `build/v3-console-room-native-02/results.json`: the same current-cartridge
  startup checks pass; the corrected fixture checks the current game arena.
  Its 1,714,352-byte allocation has `head == tail == start`, leaving no free
  fixture space during this title state. The fixture rejects before allocating
  or invoking the callback.

Neither native scenario passes, and neither result demonstrates a console
gameplay crash. No room prompt, game rendering, reset, or return is verified by
these attempts. Both setup attempts are spent; do not replay this title-state
fixture. Use a real console game-state transition for the next execution batch.

## Next work and compatibility

The checked allocator rejects insufficient complete aligned arena space before
native subtraction, image binding, or saved-state changes. The disk engine and
session hooks are installed; see [disk services](../../specs/V3_CONSOLE_DISK.md)
for native interpreter-entry evidence and the remaining execution checks.

Verify native launch/rendering/reset/return for disk and representative cartridge
games using the current combined build. Retain the exhausted title-room fixture
evidence without replay. Ordinary room entry remains unverified. Continue
other import requirements and real acquisition routes without replacing them
with easier stock lists.

Save layout remains format five. V2 and older-format V3 cannot load these saves.
An older format-five build without a required newly selected console is also
not a compatible target; keep original saves backed up. The new console profile
does not establish an ordinary save/restart cycle or hardware verification.
