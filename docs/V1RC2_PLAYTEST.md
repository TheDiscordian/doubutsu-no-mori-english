# Animal Forest English V1RC2 — private playtest

V1RC2 retains V1RC1's English translation, artwork, keyboard sounds, proportional
editor, and tutorial fixes, with these additional corrections:

- Player selection's first-time option uses the full GC `I'm new` wording.
- Keyboard right-hand corners have corrected placement and texture orientation.
  Control hints fit inside the visible frame, and key labels use ink-based
  centring, including `0`, `1`, and underscore. Font artwork remains unchanged.
- One combined symbol page retains all previously supported symbols.
- The shop's separate Japanese currency unit becomes GC `Bells`.
- AM/PM texture clamping prevents the stray PM descender pixels.
- The Nook 'n' Go hiring placard is omitted, matching the English GC room.

An **Expansion Pak is required**. On EverDrive, retain **FLASHRAM (128 KB /
1 Mbit)** with **RTC enabled**. Saved formats and input capacities are unchanged.
Back up the save and test with a copy. Do not migrate English letter snapshots
back to an unmodified Japanese ROM. The patcher never reads or changes saves.

The keyboard controls remain Stick/D-pad to select, A to type, B to delete,
Start to finish, L for case, Z for page, L+Z for alphabetical/QWERTY order,
R for space, C-buttons for the text cursor, and L+A for native character
alteration. Return remains unavailable in single-line editors; sun/skull remain
apology-only. Lucky-bag Japanese decoration is intentionally retained.

The greyer N64-controller-inspired keyboard, matching N64 button icons, and
left-side stick image are **V2 work only, after V1 completion**. They are not
included in this candidate.

## Verification and limits

All three follow-up stages rebuild from V1RC1 and the supplied original games
with freshly compiled helpers. Focused source, pixel, page-control, relocation,
allocation, resource-retention, and patch checks pass. The corrected keyboard
has complete controlled native drawing evidence: five calls/thirty assertions,
correct frame/key rectangles, intact memory guards, unchanged save data, and a
restored emulator checkpoint. Audio is disabled during automated checks.

These checks do not establish ordinary screen appearance or original-hardware
acceptance. Recheck the reported issues above and continue normal playtesting.
Report crashes, loops, save issues, incorrect English, and layout defects with
the V1RC2 label and reproduction steps. Broad seasonal/travel/save-restart
acceptance and the embedded-warning drawing probe remain incomplete.

The earlier full regression is not reported as passed: historical fixture and
accounting failures remain recorded, while the title compiler-metadata failure
has a passing scoped correction. Public release still requires provenance
review and approval. This private candidate is not a completed public release.

## Apply the patch

The local ROM is ready to copy to the flash cartridge. To use the patch-only
archive with the original Japanese retail ROM, not an earlier translation:

```sh
python3 apply_translation.py --rom 'Doubutsu no Mori (Japan).z64' --output 'Animal Forest English V1RC2.z64'
```

The included Python 3 patcher accepts standard N64 byte orders, verifies input,
patch, output, and boot checksums, and refuses existing output files. An ordinary
UPS patcher also supports the checked big-endian source. The manifest and
SHA256SUMS identify the exact contents and source revisions.

Keep this playtest private. The archive contains a patch and original tooling,
not a ROM or loose assets. SOURCES.md and LICENSE-tooling.txt describe provenance
and licensing limits; the tooling licence does not cover Nintendo or legacy work.
