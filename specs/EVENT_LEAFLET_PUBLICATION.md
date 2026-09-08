# Complete sale and Redd publication transaction

`af_event_leaflet_publish` resolves original selected item identities through the
resident sixteen-byte name loader, captures the original saved event timestamp,
creates the complete English letter, and calls the native mode-two receipt path.
All sixteen sale templates and three Redd templates are supported. The optional
`--english-event-letters` build installs this routine in the native event manager.
The owner retains the original stock/date selection and the complete snapshot
reader. Normal scheduling, save/reload, and hardware acceptance remain open.

## Source contracts

`tools/event_leaflet_sources.py` binds seven complete original actor functions,
the original mail-clear helper, and the complete native receipt helper. It reads
the verified retail ROM, not guessed structure comments from another platform.
The original event save is 156 bytes at `80135C44`. Sale time starts at offset
12; Redd time starts at offset zero. Selected sale item IDs start at offset 28.
The date bytes retain their native eight-byte layout; year is the last halfword.

The selected template and item count belong to the caller. The routine never
draws random values, chooses replacement stock, changes the schedule, or reads
the ten-byte handbill scratch fields. Every selected item is loaded through
`af_load_item_name` with sixteen-byte capacity and retained original identity.
The complete supplied GC shop-field setter uses `mHandbill_Set_free_str`, which
sets no article. This adapter likewise sets article zero; it does not guess
articles from English spelling. Native same-ID fallback names in the installed
resource do not become reviewed English merely by passing through this loader.

## Publication and lifetime

The caller provides sixteen-byte-aligned 5,536-byte work, including an explicitly
aligned native mail object. The MIPS adapter frame
is 72 bytes. There is no allocation, global mutable state, or escaping pointer
inside this routine. Source event, work, and capitalization must not overlap.
Template family, count, pointer/alignment, and complete creator constraints are
validated. Full-name lookup and complete snapshot restoration precede receipt.

Native receipt `800B6A3C`, mode two, copies all 164 bytes to `801361E4`, clears the
two flag bytes at `8013628A`, and returns one. Unlike mode zero, it does not use
the ordinary five-slot queue or allocate after writing. Other letters/flags are
outside the destination. Capitalization updates only after successful receipt.
Failed preparation retains the previous saved notice and caller capitalization.

## Native event-manager owner

`event_actor.c` owns aligned work and a 172-byte selected-input cache in the loaded
singleton actor image. It allocates nothing during registration or retries.
The installed image is 38,112 bytes, with 1,760 relocation bytes. Original
27,264-byte file offsets and 304-byte BSS addresses remain intact; old BSS becomes
zero-initialized file data. Native metadata at `80101310`, profile at `809622EC`,
592-byte actor instance, and DMA-row adjacency remain. Only the save/destructor
profile callbacks change; they retry before calling the original callbacks.
The original constructor, movement callback, stock algorithms, and Redd random
draw are retained. File/relocation VROMs move to `03800000`/`03810000`.

The sale count is captured at the original field-preparation call. Both original
registration JALs target the complete publisher. Three instructions that forced
success in the sale, Redd, and parent initializers become NOPs. The schedule gate
at `8096191C` processes any nonzero pending flag, and its unconditional flag clear
is removed. The wrapper clears the flag only after successful publication.

### Pending selector and save compatibility

The existing saved byte at `80135CE1` retains native meanings zero (complete) and
one (fresh initialization). Values 2..103 encode a selected template/count and
initial capitalization, without adding bytes or pointers to the save:

- Sale choice index: `(template - 2) * 3 + count - 1`.
- Redd choice index: `48 + template - 49`, with count zero.
- Pending byte: `2 + choice * 2 + initial_capitalization`.

Unsupported sale count/template combinations and other flag values are rejected.
The native 156-byte event record retains the selected stock and date. The pending
byte is written before preparation. A loaded cache must still match that record;
changed records are not overwritten with stale cached notices. When a normal
new event sets flag one, fresh initialization replaces the old cache. With a
retained pending byte but no loaded cache, the wrapper reconstructs the chosen
inputs and retries without entering the native selection routine. Capitalization
is sticky: a later letter's set bit is not cleared by an older pending zero.

This is a saved-flag semantic extension, **not** proof of unchanged save
compatibility. Host cache-loss tests do not prove real FlashRAM save/reload.
Audit native schedule/save writers, event replacement while pending, scene
removal, and loading a pending save through every normal entry path. The saved
record could change while no cache exists; normal routing must prove that it
does not silently associate an old selector with new stock/date. Downgrading to
an unpatched ROM with a pending extended flag is not supported or validated.

## Build and evidence

`python3 tools/build_mail_generation.py --event-leaflets --module
build/renewal-actor-pilot/runtime-module.json --output build/event-leaflet-probe`
builds the current original native probe with the pinned Docker toolchain.
Its 3,716 bytes contain the complete existing creator plus the 616-byte event
adapter. Seven resident imports and two explicitly named native helpers are
bound in its manifest. Internal absolute jumps have checked relocations; there
is no separate data/BSS. Existing generic, fortune, and leaflet variants retain
their own source/import contracts.

Four host behaviour tests exercise 152 template/hour/capitalization combinations,
complete sixteen-byte selected names, source retention, metadata, untouched
adjacent bytes, each selected-item load failure and retry, disabled catalogue,
failed cartridge reads, receipt rejection, aliases, and invalid inputs.
An artifact test checks original native source contracts, current compiled code,
imports, relocation bases, stale reports, and wrong-variant rejection.
These tests use an isolated receipt equivalent, not a production native actor.

The code SHA-256 is
`b2c6654aaf15a6a06d3245cbad2e7d6477555681f34cec941277484d3d37b99a`.
The probe alone does not install letters. The owner builder is
`tools/build_event_actor.py`; `tools/event_actor.py` guards the full native prefix,
profile/caller changes, fixed helpers, source hashes, embedded creator, owned
objects, and merged relocation inventory. Its installation is atomic and requires
the current full reader, catalogue, complete item resource, and date patches.
The [work record](../docs/checkpoints/EVENT_LEAFLET_PUBLICATION.md) identifies
the integrated ROM and the executed native test scope.
