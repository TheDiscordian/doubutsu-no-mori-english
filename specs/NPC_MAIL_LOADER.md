# On-demand NPC creator loading

## Implemented resident boundary

The resident entry keeps the original metadata function's six arguments:
destination letter, player identity, animal identity, visitor reply, condition,
and origin. It returns the caller's complete destination pointer on success,
zero on failure. The submission gate skips receipt without using older staging
contents. `af_npc_mail_load` is implemented and optionally installed together
with complete capture and delivery hooks. Default builds keep it disabled.

Keep the existing 32 KiB resident reservation and heap boundary. The complete
creator, word/name resources, relocation table, and 5,344-byte creator workspace
belong in one short-lived heap allocation. No pointer into that allocation may
outlive the synchronous creation call. Persistent state consists only of the
active-session pointer, a busy flag, and the GameCube-compatible capital word.

The linked module uses 24,192 bytes, leaving 384 bytes before test scratch.
The loader's own native stack frame is 104 bytes. Its shared capital word is
`af_mail_generation_capital`; a local copy is committed only on successful,
detached completion. Invalid or failed requests cannot advance that shared word.

## Cartridge configuration

Use the unused resident header area starting at offset `48` hexadecimal, before
the watchdog at `100`. The exact configuration remains zero in ordinary builds.
The resource VROM is `03200000`; installation verifies that its entire range is
unused and that the expanded DMA table retains a terminating entry.

Eight big-endian words occupy offsets `48..67` hexadecimal:

| Word | Meaning |
| --- | --- |
| 0 | Creator blob VROM, exactly `03200000` |
| 1 | Complete DMA byte count, image plus relocation |
| 2 | Linked image bytes, nonzero, sixteen-byte aligned, at most `8000` |
| 3 | Relocation bytes, sixteen-byte aligned, `20..1000` |
| 4 | Four-byte-aligned whole-creator entry offset inside text |
| 5 | Nonzero, sixteen-byte-aligned text bytes, within the image |
| 6 | CRC-32 of the entire unrelocated blob |
| 7 | ABI/version `41464E01`, with a 32-byte session prefix and 5,344-byte work |

Sizes in the table are hexadecimal except the explicitly stated workspace size.
The complete blob is 24,384 bytes. Including work and alignment, each call requests
29,743 temporary bytes. The allocation is released before the loader returns.

The configuration must bind the complete blob size, image and relocation sizes,
text range, whole-creator entry offset, full-blob checksum, and ABI/version.
The blob is the verified linked image immediately followed by its verified
native relocation section. Its overall DMA range is sixteen-byte aligned.
Build-time approval uses complete source/module/image/relocation SHA-256 checks
and the existing independent relocation validator. A runtime checksum checked
against the module's approved configuration detects damaged cartridge reads
before relocation or execution; a checksum embedded only in the blob is not
independent approval.

The resident loader must reject disabled/unknown configurations, invalid sizes
or alignment, arithmetic overflow, out-of-range entry points, and insufficient
four-MiB allocation bounds. Source validation inside the creator is additional
verification, not a replacement for checking code before executing it.

## Required call order

1. Reject invalid inputs, an existing session, or a busy loader; take ownership
   before allocation or synchronous DMA can yield to another game thread.
2. Allocate image, relocation, alignment space, and the complete creator work.
   Handle a null allocation without touching the caller letter or capital state.
3. Read the configured complete blob through the native synchronous DMA service.
   Reject any read failure or mismatched approved checksum before relocation.
4. Run the original `DoRelocation` on the verified section. Perform native data
   cache writeback and instruction-cache invalidation before executing the image.
5. Populate only the creator's five input session fields and invoke the bounded
   whole-creator entry with the caller destination, actual resident session
   pointer, and a local copy of resident capital state. Preserve failure.
6. Confirm the scope is detached, free the one owned allocation, clear loader
   ownership, and return the destination pointer only after success.

Do not use the existing native overlay allocation path without independent
failure handling: that path assumes its allocation succeeds. Do not reroll the
original selected words/parts, widen saved identities, or publish temporary text.

## Installation and acceptance

Optional experimental installation requires the complete compatible module,
English catalog, complete reader, all eight scoped capture calls, and the guarded
submission failure gate as one validated change. A partial hook/resource setup
must fail the build. Default builds continue to leave generation disabled.

The ROM builder's `--npc-mail-generation` option also requires English runtime,
snapshot-reader, and English-grading options. Native test tools use the resulting
ROM directory's `runtime-module.json`, which carries explicit whole-blob approval.
The plain compiler report cannot approve a configured generation ROM. Symbol
verification checks the complete image, relocation, source inventory, imports,
resource hashes, and exact eight configuration words before normalizing them.

Seven host tests pass allocation and four-MiB bounds, every byte corruption in
the synthetic blob, failed DMA, all alignment offsets, all seven re-entry
boundaries, argument forwarding, repeated capitalization, creator failures,
scope cleanup, and caller/allocation overlap. AddressSanitizer and
UndefinedBehaviorSanitizer pass. Six installer/CLI tests cover complete and
atomic installation, missing readers/resources, stale sources, changed native
functions/targets, cartridge overlap, DMA termination, and external approval.

The native cartridge test passes 48 original-metadata comparisons, eight
successive letters, and eight rejected calls. It uploads no creator code or
resources through the debugger. Actual allocation, DMA, relocation, cache
maintenance, native creation, English reconstruction, and free execute from
the installed ROM. Complete original metadata, selected source values, RNG,
capitalization, full save retention, and unchanged native heap totals pass.
Controlled exhaustion of native free blocks also exercises allocation failure.
All fixture globals/hooks/configuration, memory guards, and the checkpoint are
restored. The new ROM also passes four-MiB boot through town arrival.

Creator-to-receipt-to-reader flows, full queues with the actual creator, pending
reply retention, and broader allocation placements remain follow-up integration
checks. These do not hold up unrelated content work. Normal gameplay, complete
text review, ordinary saving/travel, and original hardware remain separate
acceptance, including the planned human playthrough and bug pass.
