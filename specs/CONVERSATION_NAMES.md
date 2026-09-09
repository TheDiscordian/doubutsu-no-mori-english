# Complete identity-based conversation names

## Integration contract

The conversation preparer at `80919BC4` has three six-byte villager-name loads
into existing eight-byte-safe temporaries: `sp+38..40` and `sp+40..48`, within
its original `58`-byte frame. Their plain/coloured fields are zero, one, and
five; both coloured names retain colour one. Calls are `80919BDC`, `80919C18`,
and `80919D08`; the corresponding length words are `80919BFC`, `80919C40`, and
`80919D30`. The neighbouring full-item adapter and town/player fields remain.

The ordinary resident preparer at `8091EA94` writes a selected other-villager
name into the existing sixteen-byte-safe BSS temporary at `80921E08`. Call
`8091EB04` and length word `8091EB28` supply dialogue field thirteen. The other
fields, other-villager selection, RNG, message selection, and timing remain.
This image also contains the complete secret-letter creator and existing
date/word integrations; those must remain independently verifiable.

## Shared display adapter

A variant of the startup-owned text extension supplies an eight-byte display
adapter at a fixed bridge, `800BB708`, inside the already bypassed native item
wrapper. The existing reference audit covers the complete reclaimed wrapper;
no original external caller may target its interior. The new initializer checks
the bridge's original instructions before calling the preceding complete
choice/field initializer, then installs and cache-synchronizes the bridge.
The resident module, packed records, and saved identity APIs remain unchanged.

The adapter first obtains the original six-byte name and pads two spaces. Only
a non-null identity with ID `E000..E0D7` may replace it using the complete
eight-byte English resource. Failed loads and unsupported identities retain
that fresh padded native fallback; null destinations receive no writes.
It is used only by the four verified display temporaries, never by saved-name
writers. Main-dialogue field storage and colour duration already support eight.

The variant has its own pinned compiled profile and loader. Older field-only and
choice-only profiles remain valid. All four call patches use a fixed main-code
bridge, so native actor sizes, BSS, allocation metadata, and relocation files
need not change. Layered verification reconstructs the exact approved name
instructions alongside the retained item and secret-letter integrations.

## Bounded verification

Check fresh fallback, null/unsupported IDs, successful full names, destination
guards, initializer rejection before writes, original source/frame/colour and
selection preservation, relocation, independent builds, and complete ROM/UPS
retention. Reuse unchanged resident loader and complete field native evidence.
Use one bounded startup/native check for the new shared bridge; ordinary
conversation and save/restart remain in combined v0 smoke. No exhaustive
per-villager emulator matrix is required.
