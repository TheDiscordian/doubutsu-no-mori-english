# English catalogue navigation

The native catalogue now uses the complete supplied top/bottom artwork in its
existing texture allocation. Its two native arrows, input, item names, ordering,
prices, and all saved data remain unchanged. Top retains its left edge and
native 0.875 scale with a narrower load/quad; bottom retains its complete quad.
See [the source and layout specification](../../specs/CATALOGUE_ARTWORK.md).

Three focused tests pass in 7.716 seconds: full image/alpha and bounded geometry,
independent native command compilation and source rejection, and complete prior
cartridge retention with UPS reconstruction and strict corrected grid ownership.
No ordinary catalogue navigation or scene acceptance is inferred from these checks.

Candidate: `build/catalogue-artwork-01/animal-forest-halfwidth.z64`.
ROM SHA-256:
`67f72b69017452be3ec83e05a513502fd58752bd0cf96b000a182fee4f880a58`.
UPS SHA-256:
`c34c5f5e1721c30de825e8a70f184c445f62ba684c48beba417d24dee6598b04`.
This untitled batch retains all notice/tune, keyboard, artwork, and main-text
work. The current combined title handoff remains `title-tune-combined-01` until
the next screen-art batch is assembled with the unchanged title.

The short-I4-label scan identifies additional Japanese screen images:

- Post/mailbox heading at `00A7F5B0`, 64×16; corresponding supplied donor is
  `pos_win_post_tex`, `.data:004ABCC0`, also 64×16 I4.
- Money-transfer labels at `00ACC000`: held money `00ACD288` (96×16), transfer
  amount `00ACD588` (96×16), remaining `00ACEA08` (48×16), and Bells `00ACE088`
  (32×16). Native owner is `0079B120` with its asset pair at `0DD8`.
- Month/day labels at `00ADFDB8`/`00ADFEB8`, each 32×16, asset `00ADD000`;
  native owner `0079DA50` contains its asset pair at `0914`. Bind actual screen
  and numeric-field layout before changing the date presentation.
- Notes/page/remaining labels at `00B216E0`/`00B25960`/`00B25AE0`, each 48×16,
  asset `00B1A000`; native owner `007A10E0` has its asset pair at `1730`.
  The nearby `00B25860` already says No. and requires no translation.

Inspected `00A7B0F8`, `00A9CDB0`, `00AA2778`, and `00AA2978` are borders or
decoration, not Japanese words. The letter-editor `00A95318` image contains
punctuation; inspect its actual reader before changing source letter layout.
The scan is not a claim that every short or multi-tile text image is inventoried.
