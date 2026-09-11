# Animal Forest English — V1 Final

V1 Final combines the English text, proportional Latin font, English title and
screen/building artwork, GameCube-style keyboard, and all implemented V1 fixes.
This package is prepared privately; it has not been published publicly.

## Included work

The release includes English dialogue, names, items, letters, menus, dates,
editor prompts, and the identified screen/sign graphics. GameCube wording,
intentional line/page breaks, and timing are preserved by the translation
adapters. Native N64 locations, saved identities, and game rules remain.

All 23 reported V1 findings are fixed and human-accepted, including the title
prompt, keyboard layout/sounds, font and transition edges, money displays,
catalogue/payment text, letter/board editing, recipient names, space marker,
and existing-town loading. The earlier Nook conversation-loop and Shrine
corrections are also included and accepted.

Additional implemented source findings cover town-tune confirmation, Pak
instructions, title warnings, player/save menus, all 76 scene-menu strings,
and thirteen main-program literals. The final thirteen occupy existing slots;
they change no instructions, pointers, allocations, save code, or debug access.
Twelve have diagnostic readers; the reserve literal is unused. No debug menu
is enabled by the translation.

## Hardware and saves

- Expansion Pak: required (8 MiB RAM).
- EverDrive save type: FLASHRAM, 128 KB / 1 Mbit.
- RTC: enabled.
- ROM size: 32 MiB, big-endian `.z64`.

RC8 → V1 Final and V1 Final → RC8 save compatibility are expected, with no
migration. Saved formats and readers/writers are unchanged; those particular
loading directions have not been independently tested. Ordinary saving,
restarting, and reloading already have repeated human hardware acceptance.
Keep save backups. Do not use RC3 as a fallback: that preserved build has its
known existing-town loading defect.

A new ROM filename may select a different EverDrive save filename. Preserve
the original save and associate a copy with the new ROM name to keep your town.
The patcher never accesses game saves or Controller Pak data.

## Apply the patch offline

Extract the entire ZIP into one folder. Supply the extracted original Japanese
N64 ROM, not an older English build. Only Python 3 and its standard library are
required; patch application needs no Docker, GC disc, source checkout, or network.

```sh
python3 apply_translation.py --rom "Doubutsu no Mori (Japan).z64" --output "Animal Forest English V1 Final.z64"
```

On Windows, `py -3` may replace `python3`. The patcher accepts `.z64`, `.v64`,
and `.n64` byte orders of the supported original, not archive files. It checks
the original ROM, patch, complete output, and N64 boot checksum, and refuses
to overwrite an existing destination. The original remains untouched.

- Original SHA-256 after byte-order normalisation:
  `d9417be056534fcc0bdff2e6cd5f1135511be7c0a4dace04a96a2649596ce908`.
- V1 Final ROM SHA-256:
  `0561182044c1526010ed77b1b9c72ac268794c2f7b615f8fa70c007f366483bf`.
- UPS SHA-256:
  `acdfe82eae085337cc23d261154fbd06004f56d234b0a76587d2e6885047ae47`.

`manifest.json` records build/source revisions and compatibility. `SHA256SUMS`
covers every other ZIP member. Put only the locally reconstructed ROM on the
cartridge; do not redistribute that ROM.

## Verification and limits

The base, artwork, correction, and final diagnostic stages have passing recorded
construction checks. The final data-only stage passes focused slot/reader/source
checks and full UPS reconstruction. Packaging requires the included standalone
patcher to reconstruct the exact final cartridge before producing the handoff.
No old candidate is rebuilt or re-tested, and no accepted gameplay case is
repeated just because the final filename changes.

Human acceptance covers all reported V1-01 through V1-23 defects, the reported
v0 corrections, and repeated ordinary save/restart/reload. It does not imply
a fresh hardware session of the later source-identified menu/diagnostic labels.
The complete 109-stage source command is composed from verified stages, not
claimed as one newly executed end-to-end run. The retained historical full
suite did not pass as a whole; its fixture/accounting failures and scoped
follow-ups are documented in the source checkout, not represented as green.

Broader seasonal/event/travel/Pak combinations, individual English line layouts,
and ordinary appearance of both adapted festival-stall placements are not
exhaustively tested. Unreported bugs remain possible. Report concrete findings
using the [bug-report guide](BUG_REPORT.md); do not repeat already accepted cases
solely for this release's name. No claim of exhaustive whole-game or hardware
certification is made.

Lucky-bag Japanese decoration is intentionally retained, matching English GC.
Native neutral artwork remains unchanged unless a translation defect warrants
editing it. The grey N64-inspired keyboard redesign belongs to V2, not V1.

## Sources and distribution

[Sources and credits](SOURCES.md) and the [optional source-build guide](TOOLCHAIN.md)
are included and readable offline. Source compilation requires access to the
private repository and separately supplied inputs; patch application does not.

`LICENSE-tooling.txt` covers original tooling, not Nintendo content or legacy
work. This ZIP contains a patch, documents, manifest, checksums, and two Python
files. No ROM, save, emulator state, or loose game asset is included. Technical
packaging is not redistribution clearance; public publication requires separate
review and the user's approval.
