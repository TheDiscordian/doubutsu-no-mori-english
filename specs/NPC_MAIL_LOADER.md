# On-demand NPC creator loading

## Planned resident boundary

The resident entry keeps the original metadata function's six arguments:
destination letter, player identity, animal identity, visitor reply, condition,
and origin. It returns the caller's complete destination pointer on success,
zero on failure. The tested submission gate can then skip receipt without using
older staging contents. This loader is not implemented or installed yet.

Keep the existing 32 KiB resident reservation and heap boundary. The complete
creator, word/name resources, relocation table, and 5,344-byte creator workspace
belong in one short-lived heap allocation. No pointer into that allocation may
outlive the synchronous creation call. Persistent state consists only of the
active-session pointer, a busy flag, and the GameCube-compatible capital word.

## Proposed cartridge configuration

Use the unused resident header area starting at offset `48` hexadecimal, before
the watchdog at `100`. The exact configuration remains zero in ordinary builds.
The proposed resource VROM is `03200000`; installation must verify that its entire
range is unused and that the expanded DMA table retains a terminating entry.

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
   pointer, and resident capital state. Preserve the entry's failure result.
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

Tests must cover every allocation/DMA/validation failure, repeated and nested
requests, relocated execution at multiple addresses, complete original metadata
and RNG retention, successful creator-to-receipt-to-reader flows, full queues,
and retained pending replies after rejection. Normal gameplay, complete text
review, ordinary saving/travel, and original hardware remain separate acceptance.
