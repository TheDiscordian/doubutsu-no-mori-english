# Home-gyroid default integration checkpoint

The [default-message specification](../../specs/GYROID_DEFAULT.md) identifies
the four complete GameCube strings actually selected by both initialisation
paths: `076A..076D`, 92 bytes with their three separating newlines. The older
same-ID `055C` concatenation has different third-line wording and no manual
line separators, so it is not the correct full presentation source.

Native creation still loads `055C` into a 64-byte saved field, and the existing
resident formatter writes a 68-byte display field. The resident linked image
is exactly `6000` bytes; it has no remaining linked room. The native Haniwa
routine supplies its owner-message pointer at `sp+20` and selects `0928` for
other-owner messages. This provides an actor-owned selection point without
changing the resident allocation or saved structures.

`overlays/gyroid_default/default.c` recognises only an exact 64-byte original
default requested through `0928`. Every differing byte and every other request
is retained unchanged. Three host tests pass in 0.134 seconds, including all
16,320 single-byte customisations, unaligned inputs, and unchanged sources and
surrounding guards. The original comparison data is extracted from the supplied
cartridge into temporary test data, not committed as a game asset.

The C selector and assembly adapter compile with the pinned Docker VR4300
toolchain. The selector has a zero-byte frame and 76 instruction bytes; the
adapter has a 24-byte frame and 36 instruction bytes. The combined relocatable
object has no writable data or BSS; its only unresolved symbol is the intended
64-byte native comparison source. Its relocation requests are one HI16/LO16
pair for that source and one internal selector call. This is object compilation,
not a linked or installed cartridge feature, native execution, or save validation.
Logs are `build/gyroid-default-host-tests.log` and
`build/gyroid-default-object-build.log`; objects remain ignored under
`build/gyroid-default-objects/`.

## Next implementation

1. Bind the four raw English lines, actual donor functions/tables, native source,
   and complete `0928` introduction. Generate the default variant by replacing
   exactly its one `40` field, retaining the owner field, pauses, page, `0929`
   continuation, and final `01`.
2. Reconcile the existing explicit reserve-label approval for `2AE7` only when
   enabling the complete feature. Keep disabled builds unchanged, repeat its
   source/usage checks, and reject partial actor/text installation. Do not use
   the unreferenced-but-nonreserve `2AED` dialogue.
3. Append the selector/adapter/comparison data to `ovl_Haniwa`, convert the three
   helper relocations and the changed native call, preserve all original
   relocations/BSS addresses, and update actual actor allocation/DMA metadata.
   `tools/secret_actor.py` and its builder provide an existing append/relocation
   pattern, not Haniwa-specific permission.
4. Install the complete actor/text pair, retain every other translated resource,
   validate the full ROM/UPS, and run one bounded silent native batch covering
   default/custom selection, the real adapter, complete loading, continuation,
   guards, saved-state retention, and checkpoint restoration.
5. Address the default in the owner-message editor too. Display-only substitution
   leaves the original Japanese default in saved storage; the editor must not
   expose it as the finished English translation. Keep custom text, explicit
   input limits, and compatibility intact, without silently truncating a longer
   default or edited text. Normal interaction/save/reload remains required.

The current complete ROM remains `build/message-diagnostic-pilot`; the gyroid
selector is not installed and receives no new translation credit. The broader
goal remains active, including other general strings, letters, accented names,
full-name callers, review, gameplay/save validation, patch-only release, and
title/keyboard work.
