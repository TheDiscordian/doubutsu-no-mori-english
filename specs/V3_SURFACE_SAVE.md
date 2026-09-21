# V3 surface selection and ownership saves

## Format and compatibility

`AF_V3_SURFACE_PROFILE` extends the shared codec/runtime with format 4 and save
registry 3. It requires the existing clothing and reward variants. The native
`F980`-byte town payload, full 64-KiB banks, device workers, and every previous
profile/catalogue/reward offset remain unchanged. Surface identity has its own
selection and ownership category; furniture and garment bits are not reused.

Valid NAFJ and formats 1–3 migrate with surface ownership clear and the current
surface selection recorded. Format 4 restores ownership and requires every saved
surface selection to remain selected in the current build. The same conservative
equal-or-larger policy applies to villagers, furniture, and clothing. Selecting
an unused import still makes that selection required by subsequent saves.

**Format-4 saves cannot load in V2 or older format-1/2/3 V3 builds.** Preserve
backups before moving a town forward. The private composer exports this actual
build warning; empty selections still produce the exact pinned translation-only
cartridge and its original save note. Component verification does not establish
an ordinary cross-version game save/restart. Neither website deployment changes.

## Layout

All offsets below are hexadecimal. The `AFS3` extension remains `680` bytes at
bank offset `F980`. Format is 4 at offset `004`, with registry 3 at `008`.
Existing records end at `38F`; the added layout is:

| Extension offset | Bytes | Contents |
| --- | ---: | --- |
| `390` | 64 | Required surface selections |
| `3D0` | 256 | Four players' 64-byte surface ownership sets |
| `4D0` | 432 | Reserved zero |

Each 64-byte set contains 32 floor bytes and 32 wallpaper bytes. A bit is the
complete low-byte native identity, least-significant-bit first, independent of
selection order and donor numbering. The prepared additions use native indices
73–77. Capacity for other indices is not evidence that those imports exist.

Working state retains the first 880 bytes and appends 64 selection bytes plus
256 ownership bytes. It totals 1,200 bytes. Runtime header and guards bring the
allocation to 1,232 bytes at `8046C000..8046C4CF`; guards start at `8046C4C0`.
This fits the already owned space before `8046D000`. Native save RAM is unchanged.
New-town reset clears ownership but retains the current surface selection.

The selected profile is derived from exact enabled surface metadata records,
not a second independently maintained list. Header/version/count/stride, stable
item identities, and enable word 1 are checked. The runtime compares all derived
bytes against its working selection before saving or changing ownership.

Both CRCs and the native checksum retain their definitions. Every owned surface
must belong to the saved surface profile. Decode validates before changing any
output; pack validates before modifying its bank. Unknown format/registry,
nonzero reserved bytes, corruption, missing selections, and inconsistent
ownership remain distinct errors. Old decoders reject format 4 explicitly.

## Installed code and preserved entry points

The existing surface packet grows from 4 to 16 KiB at
`804BC000..804BFFFF`, below the model pool at `80500000`. The added 12 KiB contains
the extended codec/runtime; no heap, scene, actor, or artwork allocation grows.
The original 4-KiB boundary guard is retained, with another guard at `804BFFF0`.

- `804BC900`: 776-byte shared profile/collection/clear helper.
- `804BD000`: 2,792-byte format-4 codec.
- `804BE000`: 2,071-byte save runtime.

The same checked equipment bootstrap loads and CRC-checks the complete packet.
It retains cache flushing and the furniture-table initialization chain. Startup
then calls the stable save-reset entry; the enlarged packet is loaded before
any new save code executes. Startup remains within its 992-byte reservation.

Every original public save-runtime entry and the shared state validator retain
their addresses through checked jumps into the new implementation. Check, pack,
and collect still enter at `8046B400`, `8046B7A0`, and `8046B9C4`. Existing native
FlashRAM hooks, collection callers, reward helpers, original reader/clear bridges,
and other item systems keep their APIs. The complete retained D000 codec/item/
tent-lamp resource is unchanged; the old codec code is no longer the active
public check/pack/collect destination.

Surface collection wraps the existing record/owned entries at `804699C0` and
`80469AD4`. Non-surface items retain the complete display/held/original chains.
Disabled or missing extended surface IDs never reach unchecked native ownership
arrays. Native player deletion at `800B7ADC` clears only that player's surface
ownership, then delegates to the existing reward/catalogue/native clearing chain.
Future display-reader refreshes preserve the outer surface hooks and reject
unexpected movement of their checked predecessor targets.

## Verification and remaining work

The focused tests compare complete banks with an independent Python encoder,
check older-format migration and backward rejection, added/removed selections,
ownership consistency, failure atomicity, unchanged native payload and record
offsets, startup/resource checksums, stable APIs, import-free/all composition,
and UPS reconstruction. Actual C under memory-safety sanitizers covers per-player
ownership, clearing, host device I/O, new-town reset, and failure before writes.

Native results and their limits are recorded in the
[pipeline checkpoint](../docs/checkpoints/V3_FURNITURE_PIPELINE.md).
Catalogue page lists/ownership-bit dispatch use this category; native inventory
actions pass complete IDs to the installed room reservations. Acquisition,
floor sound/scoring, private surface selections, and ordinary save/restart remain work.
No surface becomes selectable merely because its save category exists.
