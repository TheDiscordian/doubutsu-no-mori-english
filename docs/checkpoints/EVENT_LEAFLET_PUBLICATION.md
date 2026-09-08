# Event leaflet integration checkpoint

The complete sale/Redd publication transaction is implemented, compiled, and
host-tested. Native event-manager registration is the active next task, not
another isolated-probe expansion. Its [specification](../../specs/EVENT_LEAFLET_PUBLICATION.md)
and `tools/event_leaflet_sources.py` pin the source contracts.

## Current artifacts and verification

`build/event-leaflet-probe/generate.bin` is 3,716 bytes, with SHA-256
`b2c6654aaf15a6a06d3245cbad2e7d6477555681f34cec941277484d3d37b99a`.
The complete creator occupies the first 3,100 bytes; event publication starts at
offset 3,100 and adds 616 bytes. The adapter frame is 72 bytes. Caller-owned work
is 5,536 bytes, with explicit sixteen-byte alignment for the native mail object.
The source/import manifest and complete jump relocations are beside the binary.

Five focused tests pass in 0.618 seconds, including 152 complete template/hour/
capitalization cases, item-loader failure/retry, retained notice/capital on failed
preparation, original source contracts, and compiled-variant/relocation checks.
Six generic probe regressions pass in 0.006 seconds. Nine renewal adapter/installer
regressions pass in 8.754 seconds after the probe-tool extension. The completed
918-test full batch belongs to the renewal milestone, before this event work.

No new ROM is built by this probe. The current integrated ROM remains
`build/renewal-actor-pilot/animal-forest-halfwidth.z64`, SHA-256
`7655a1cb1653a2535eebc6fe4addf290bdbd33c5ef9e4ef54114ba31713fb69f`.
No actual event-manager invocation, native selected-item-to-event-receipt batch,
normal delivery, or hardware test is claimed.

## Exact integration points

- Original registration is `8095B9CC..8095BA60`, called by sale at `8095C080`
  and Redd at `8095BC48`. It uses the static native mail at `80962330`.
- Sale field preparation is `8095BA60..8095BB80`; its input count is selected
  before the call at `8095C05C`. Retain this actual count, not the number of
  distinct item names or an inferred count from English text.
- Redd selection is `8095BBFC..8095BC60`, including the original random draw at
  `8095BC08`; retain its selected template without drawing again on retry.
- The original 156-byte event save at `80135C44` contains scheduled Redd time at
  zero, sale start time at 12, and sale item IDs at 28.
- Sale and Redd initializers discard registration results at `8095C088` and
  `8095C24C`. Parent special-event initialization discards its indirect child
  return at `8095C494`. A return-value change at registration alone is insufficient.
- Native receipt mode two copies a complete record to `801361E4`, clears exactly
  two flag bytes at `8013628A`, and returns one. It does not use the ordinary
  queue or allocate after writing. The source helper is fully hash-bound.
- The actor has 27,264 file bytes plus 304 BSS bytes. Keep every original data,
  BSS, profile, and relocation address when appending code. Original DMA rows
  `00850680`/`00857100` must retain adjacency and ownership at `80101310`.

Choose and implement the actor's work ownership and failed-selection lifetime
before installing the registration hooks. Avoid a new allocation after random
selection where practical. A temporary pointer must never survive owner unload
without an explicit owner; do not mistake actor-static retry state for saved
state. Preserve the original stock, schedule, and selected template. Batch the
actual constructor/registration/receipt/readback/failure checks once connected.

Remaining translation text, review, ordinary gameplay/save acceptance, title-first
artwork, English grid keyboard, and patch-only release work remain active.
