# Complete sale and Redd publication transaction

`af_event_leaflet_publish` resolves original selected item identities through the
resident sixteen-byte name loader, captures the original saved event timestamp,
creates the complete English letter, and calls the native mode-two receipt path.
All sixteen sale templates and three Redd templates are supported. This routine
is compiled and host-tested; its event-manager owner hooks are not installed.

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

Owner integration must retain the exact selected template/count and timestamp
across failed attempts without rerolling stock or Redd wording. The sale and Redd
initializers unconditionally return one; their parent at `8095C494` also discards
the child result. Changing only the registration function's return cannot solve
failure handling. Actor unload, scene transitions, save/reload, replaced events,
and retries require an explicit ownership solution before this becomes a normal
gameplay path. Do not publish an untracked pending heap pointer or silently
overwrite an earlier failed selection.

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
Native owner/caller installation, actual selected-item-to-receipt readback,
pending lifetime, normal delivery, and hardware remain. No new ROM or text
coverage claim is made by compiling this probe.
