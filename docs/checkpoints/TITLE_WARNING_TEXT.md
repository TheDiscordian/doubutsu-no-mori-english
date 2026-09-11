# Title warning follow-up

## Finding and implementation

Source review of RC6 identifies V1-26: the live missing-controller title branch
still selects three Japanese lines, and its retained menu contains a Japanese
erase-save label. The complete warning and label have an English correction in
`tools/title_warning_text.py`. The [specification](../../specs/TITLE_WARNING_TEXT.md)
binds the original strings, actual call sites, controller branch, storage,
relocations, and centring.

The full warning says `Controller 1 is not` / `connected. Power off,` /
`then connect it.`. The native menu label says `Erase Save Data`. No GameCube
counterpart is invented: these are original translations of native instructions.
Only existing text and seven immediate/pointer words change. Controller checks,
title animation/graphics, native menu actions, saved formats, and save readers/
writers remain unchanged. No save deletion or Controller Pak operation is run.

## Focused verification

The initial four `test_title_warning_text.py` checks pass in 8.629 seconds:

- Complete English wording, exact seven-word change set, and unchanged title
  extension, artwork, and controller branch.
- Actual counted pointers after relocation at `801A0010`, `802C0010`, and the
  production title address `80400010`, with explicit eight-MiB bounds.
- English line widths 108/123/93 and X origins 106/98.5/113.5, centred at 160.
- Retention of every other cartridge resource and original-ROM UPS reconstruction;
  refusal of changed owners, relocations, metrics, and baseline cartridges.

These are construction checks, not native rendering, menu-access testing,
original-hardware acceptance, or proof of a save/restart cycle. Existing native
title evidence belongs to its original tested builds. It is not rerun or
relabeled as execution of this text correction. The full suite is not rerun.

## Discovery scope and remaining leads

A read-only diagnostic uses the existing pinned executable-section definitions,
native font-call inventory, and current DMA-index mapping. It does not maintain
the percentage tool or scan arbitrary bytes as if every run were text.

For native `80090E98`, the diagnostic finds 68 direct calls: 17 have redirected
call words; 33 have unresolved/dynamic arguments; one addresses a runtime buffer;
and 17 have resolved static reads. Two Japanese candidates in that last group
are retained old readers, not new application gaps:

- The original notice count at `80895310` is inside the superseded entry drawer.
  RC6's caller `80895750` selects `80897968` (`af_notice_draw_entry`) through
  instruction `0C225E5A`; complete English entry formatting is already installed.
- The old radial keyboard's `80887A34` glyph is inside its superseded drawer.
  RC6's keyboard caller `808882D8` selects `8088C9E8` through `0C22327A`.

The companion `80090E1C` scan finds eighteen native calls and identifies the
actual title warning above. Its other leads include the separate
player-selection and save-menu gamestates at `00747AA0` / `007486E0`. Their
Japanese labels are not the ordinary already-corrected player-selection option.
Review reachability and original reader lengths before changing those resources;
no save-menu execution or write is needed to inspect wording. Dynamic buffers
and startup-installed hooks prevent this selected scan from proving a complete
whole-game text inventory.

The old ledger's remaining name slots `00DA/00DB` and final item slot `0ECC`
contain zero padding, not additional live Japanese names. Their native encoding
renders byte zero as `あ` only when treated as counted text. Existing name/item
specifications preserve these reserved slots. They are not modified to make a
counter increase.

## Committed construction

`build/title-warning-text-01/animal-forest-title-warning.z64` is constructed
from clean revision `7b6eddc23503f8172e972534972eb572924711f9` on the exact RC6
baseline. Its receipt records `worktree_modified: false`.

- ROM SHA-256: `614e387ee7591d935c091852512f7a60dc181fe25892843a2458c70a69e87037`.
- UPS SHA-256: `c41973cd35632e5ed511021c826f9d64705b0dcff4e92713c564694a6bd19941`.
- Receipt SHA-256: `49e04f4b2603673d413b6c17b4f0af398451761bddcdb8d4332a2037dde099d2`.
- Builder SHA-256: `430131ad33af441433c6456875587de7d8eed0c69d28fa119050caa92c61a984`.
- Installed title owner SHA-256: `0363362712461f6a30bfe487a2cf4936bdf21a4fcb81cc62f56f9c2fb9e1b379`.

The committed build and full UPS reconstruction pass. Reproduce into a fresh
output directory with `python3 tools/title_warning_text.py --output build/title-warning-text-new`.
The input remains the named RC6 ROM; never overwrite an earlier build or save.

## Handoff state

The named private handoff remains RC6. The title correction is a follow-up
development stage; package it together with further verified corrections before
replacing the named candidate. RC6 saves are expected compatible in both
directions because formats and readers/writers are unchanged. Loading and
save/restart remain independently unverified. Preserve all previous ROMs and
the user's original save backups. V2 and public distribution remain deferred.
