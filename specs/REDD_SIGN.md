# Redd's English summer sign

The supplied GameCube summer tent replaces the native Japanese crest with the
English BLACK MARKET artwork. Import the complete 128×32 CI4 texture at
`.data:0050EF80` into native object offset `10C8` (VROM `00D5F0C8`). The actual
donor model is `0050FC70`, with vertex array `0050F800`. All 31 native vertex
uses match its positions and UVs, including the animated door reference.

The new red lettering uses palette indices 13 and 14. Neither index is used
by either native summer CI4 texture; the window uses I4, not this palette.
The native palette table at `00D5D000` has exactly one reference to the summer
palette `00D5BA48`, at offset `108` (BR_SHOP palette 40). The winter palette
is separate. Replace only the two unused summer entries, at `00D5BA62`, with
the exact GameCube opaque colours encoded as native RGBA5551. All colours of
previously existing summer pixels and all other palettes remain unchanged.

Winter's entire sign face is covered in snow, and its texture already matches
GameCube. Retain winter exactly; do not put summer lettering over the snow.
Apply the summer texture to both the original object and the actually streamed
expanded object at `03D00000`, retaining the complete police and Nookington work.

Verify input identities, actual donor texture pointers, native palette ownership
and unused entries, complete visible colour equality, geometry bindings, exact
texture conversion, unrelated resource retention, and UPS reconstruction.
No new code, allocation, save format, model, or timing is introduced. Ordinary
appearance and hardware acceptance remain pending until observed.
