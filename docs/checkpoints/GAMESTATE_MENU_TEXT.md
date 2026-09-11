# Player/save gamestate text follow-up

## Finding and implementation

V1-27 follows the two gamestate leads recorded in the title-warning review.
The current candidate still contains nine Japanese labels in owners `00747AA0`
and `007486E0`. These are separate from the ordinary `I'm new` option and
dialogue-driven saving. Both gamestates remain registered, but ordinary access
is not established; the correction neither enables nor invokes them.

`tools/gamestate_menu_text.py` implements complete `Unregistered`, `<Away>`,
`<Home>`, `Visitor`, `Select a player`, and numbered `Resident` rows, plus
`Save Menu`, `Save to FlashRAM`, and `Save to Pak`. Native slot numbers and
existing A/R/B English hints remain unchanged. These are original translations
of the N64 wording, not guessed GC record matches.

The [specification](../../specs/GAMESTATE_MENU_TEXT.md) records full source,
pointer, relocation, display-copy, stack, and metadata contracts. Repacking
existing label/padding regions fits complete English without file growth or
new allocation. The 200-byte resident-drawer stack frame contains a 27-byte
combined row and a separate prefix pointer; its existing sixteen-byte name/
status field does not grow. The save-choice drawer's unchanged 112-byte frame
holds both full choices in 28 bytes, including padding. No saved names, formats,
save functions, destination choices, controller behaviour, or access paths change.

## Focused verification

The initial six `test_gamestate_menu_text.py` checks pass in 9.111 seconds:

- All nine complete translations, retained original English hints, exact
  declared reader changes, and unchanged unrelated owner bytes.
- Original relocation tables at three load bases with all repacked text
  targets intact, unchanged resource sizes, and no BSS growth.
- Actual resident-copy instructions, twelve-byte unregistered initialization,
  existing registered-name/status capacities, and complete resident row layout.
- Actual save-heading pointer/count instructions, 28-byte mode copy, full
  sixteen/eleven-byte choice readers, and unchanged stack-frame bounds.
- Every other ROM resource, metadata, title warning, and prior correction
  retained; complete original-ROM UPS reconstruction.
- Rejection of changed owners, relocation records, and predecessor cartridge.

The buffer examples model the bound copies; they do not execute the native CPU
or saved-data operations. No emulator, Flash/Pak write, deletion, save-confirmation
harness, full-suite rerun, or percentage-tool maintenance is performed. Ordinary
appearance, access, saving, and original-hardware acceptance remain unverified.

## Follow-up

Build this committed stage on `build/title-warning-text-01`, then package both
stages into the next named candidate with complete receipts and the standalone
patcher check. RC6 remains the existing named handoff without these later
corrections. Preserve earlier ROMs and all original saves. Expected forward/
backward RC6 compatibility follows unchanged formats and save readers/writers;
it is not a verified loading or save/restart cycle. V2 remains deferred.

The read source also exposes Japanese scene labels in the separate `ovl_select`
development scene table. That path uses the debug graphics-print encoding, not
the counted dialogue font. It is an unreviewed lead, not proof of a missing
ordinary player menu or permission to change debug controls/access. Do not rerun
the completed direct-font scans or reopen reserved zero-filled name slots.
