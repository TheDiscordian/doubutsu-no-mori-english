# Complete festival and reserve dialogue names

Three festival actors prepare five character-name fields in slots one through
five. The selected actor pointers, skipped participants, loop ordering, message
selection, and random-number calls remain native. Only the name resolver call
and the following field length change: `af_get_display_name` supplies eight
bytes, and the field setter receives all eight.

| Actor | Function | Name temporary | Frame | Changed call / length |
| --- | --- | --- | --- | --- |
| Tukimi_Npc0 | `809DFEB0..809DFFB0` | `sp+44..4C` | `50` | `809DFF2C` / `809DFF44` |
| Tukimi_Npc1 | `809E0704..809E0820` | `sp+48..50` | `58` | `809E0788` / `809E07A0` |
| Turi_Npc0 | `809E31C4..809E32C4` | `sp+4C..54` | `58` | `809E3230` / `809E3248` |

All offsets and frame sizes are hexadecimal. Each eight-byte temporary fits
below the original frame boundary without touching saved registers or other
live locals. No stack growth, actor growth, relocation change, or saved-name
expansion is required. The existing full-name resolver retains native fallback
behaviour and padding for unsupported actor identities.

The reserve actor prepares the special identity `D008`, Tom Nook, in slot one.
Its eight-byte local at `sp+24..2C` fits its `40`-byte frame. The preceding item
preparation uses the already installed free-item bridge, so the old item local
at `sp+2C` is no longer written. A forty-four-byte sequence at
`80A09458..80A09484` loads the complete approved name by ID and inserts it only
after successful loading. Failure leaves the previous field unchanged; no
uninitialized temporary is copied. The main window singleton address is bound
to its native getter. The unchanged following instructions recover the actor
state and choose the original message.

The sequence consumes the final unused instruction of the approved free-item
adapter's padding. Its source is explicitly that installed adapter, not arbitrary
current bytes. Final text-extension verification verifies this complete actor
integration and adds only the approved name sequence to its reconstructed
item-adapter expectation. Both modifications must be present;
neither verifier silently permits unrelated actor changes.

Installation binds full original actors/functions and relocations, the exact
resident imports and name resource, existing startup extension, all changed
instructions, and references into the reserve sequence. Two-base relocation and
independent assembly checks cover the new fixed calls and failure branch.
Unchanged full-name and general-field runtime execution reuse recorded native
evidence; ordinary festival/reserve interaction joins the combined v0 smoke.

This completes these four actor preparations, not every NPC identity-based name
loader, household label, editor, or saved-name consumer. Those routes retain
their explicit queue and translation-counter requirements.
