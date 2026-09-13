# Compact N64 keyboard layout

## Deliverable

V2-09 places the unchanged forty-key grid inside a compact grey tray. Separate
grey shoulders and tapered controller grips carry the animated N64 stick,
native L/Z/R/Start, blue A, green B, and four yellow C buttons. The GameCube
reference informs the separated arrangement, not the controller identity.
The visible `L+A: Alter` and `L+Z: ABC` hints are removed; both shortcuts and
all ordinary editor controls remain implemented.

- ROM: `build/v2-keyboard-layout-09-final/Animal Forest English V2.z64`.
- ROM SHA-256: `980760ee4153490ad4041b4424795167ddd2e078616261f17e93bac1924551a6`.
- Original-ROM UPS: `build/v2-keyboard-layout-09-final/Animal Forest English V2.ups`.
- UPS SHA-256: `003b063ebdb333eaf13c9fe85b6b3c01458f349b3418a90e3bcf48224a95935f`.
- Receipt SHA-256: `b95e5a423c14864b1a83e1ae6cbf14488a1a3f94f184b27a828fe25559941828`.
- Exact V2-08 input SHA-256: `08aa1c4418848138803059a68de667f473f9da490d7c0866ee501c58b8d0896b`.

The build receipt records construction-time native validation as pending;
the subsequent exact-ROM native result below supplies that evidence without
rewriting the original receipt.

## Implementation and cartridge checks

`tools/keyboard_v2_layout.py` compiles only the keyboard-owned presentation
suffix using the existing pinned Docker compiler. The new panel/control sources
live in `overlays/keyboard_v2_layout/`. The donor key-tray textures and native
N64 button/stick images receive no pixel edits. Seven shaded code-drawn shells
sit under the tray rim and follow the same menu slide coordinates.

The six `tests.test_keyboard_v2_layout` tests pass in 2.839 seconds:

- Current builder-source identities, output identity, and complete original-ROM
  UPS reconstruction.
- Every unrelated resource, including museum identity handling, credits,
  native controller textures, and saved-format code, retained unchanged.
- The full 30,272-byte editor/input prefix retained except its existing
  four-byte draw hook, including comparison at two relocated load addresses.
- Retained optical glyph origins, all eleven native icon bindings and pressed
  frames, absent combination hints, and preserved shortcut/input flags.
- Existing 8-KiB allocation and graphics guard, unchanged key positions,
  exclusive one-cycle rectangle edges, and correctly recorded tray bounds.
- Compiled shell/letter tables, all 112 band rectangles within the screen,
  and the aligned N64 button-letter coordinates.

The final editor is 38,272 bytes. Its rounded suffix uses 8,000 bytes of the
existing 8,192-byte reservation; no shared pool or resident module grows.
Per-font-call graphics-space checks remain intact.

## Ordinary in-game verification

`build/v2-keyboard-layout-native-03/` cold-boots the exact final ROM in isolated,
silent ares with eight MiB and reaches ordinary name entry through normal
controls. `tests/keyboard-v2-layout-scenario.json` completes all 44 result
entries, including empty-name assertions, native fault zero, resident guard
checks, and graceful shutdown. No original/user save is opened.

The eight captured states are visually inspected: neutral, diagonal stick,
A held/typed character, L held/lowercase, Z held/symbols, R held/space,
C-right held/caret movement, and restoration of the same-build neutral state.
The key tray fits the grid, shell bands are contiguous, captions remain on
their sections, and the native stick and pressed artwork remain visible.
The screenshot skill guides inspection of the isolated emulator display.

- Native results SHA-256: `2bfe62dd862febcb8be412cb0fb197f25b303ddde4669d0973bafc28d39e492f`.
- Native run identity SHA-256: `1d316daae67b16e6f2f48a1040decf920174ac989dacdbc2aa06c73ae455f638`.

Draft-only checks are preserved, not substituted for this final pass. The
first draft's boxy sections prompted tapered geometry; visual review of that
geometry caught gaps caused by treating one-cycle rectangle edges as inclusive.
The final build fixes those edges and receives its own native pass. Rejected
over-budget builds produce no handoff ROM. No historical candidate is replayed.

## Patcher integration

`build/web-portal-04/site` serves the same ROM through the local portal. The
tracked `web/release/` recipe and Pages hash guards target V2-09. The recipe
contains 23,085 commands, genuinely copies 2,783,500 bytes from the English
GameCube donor, and occupies 1,889,751 compressed bytes.

Recipe SHA-256:
`06181af88864856eb38125870a7e485ef45f939755b5890bfb9a0fe15c01531b`.

Five Pages staging checks and eleven JavaScript parser/patch checks pass.
`build/web-portal-check-09/` records actual silent Chromium downloads with
CISO, sparse ISO, and a Pages-style project subpath. All three match the ROM
above, taking 0.68, 0.69, and 0.75 seconds respectively. Cancellation, incorrect
inputs, stale-download clearing, and 375/768/1440-pixel layouts pass; there are
no browser errors or non-local requests. Website prose and the released
YouTube trailer are unchanged.

## Compatibility and limits

Saved formats are unchanged. V2-08 → V2-09 and V2-09 → V2-08 compatibility are
expected without migration, not newly exercised loading claims. Prior builds
and original saves remain preserved. Expansion Pak, 128-KiB FlashRAM, and RTC
remain required.

Hardware acceptance of this presentation and other keyboard callers remain
human playtest work. The retained prefix/metrics/artwork establish continuity
for unexercised shortcuts and button poses, not a claim that every combination
is freshly played. The completed K.K. performance and all-credits-page checks
remain applicable to unchanged resources; neither is replayed for this layout.
