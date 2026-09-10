# Animal Forest English V1RC3 — private playtest

V1RC3 retains all V1RC2 translation, artwork, keyboard, editor, and tutorial
corrections, and adds two fixes:

- Names/options use transparent glyph borders to retain left-edge strokes and
  smooth descenders such as `g`. Original glyph ink, speech rendering, and
  character spacing remain unchanged.
- Building-transition wipes extend beyond the framebuffer edges, removing the
  exposed top rows and thin strips at the other edges. The native shape and
  transition timing remain; the shape is about 2.6% larger.

An **Expansion Pak is required**. EverDrive uses **FLASHRAM (128 KB / 1 Mbit)**
with **RTC enabled**. Saved formats and input capacities are unchanged. Back up
the save and test with a copy; do not migrate English letter snapshots back to
an unmodified Japanese ROM. The patcher never reads or changes saves.

Keyboard controls remain Stick/D-pad to select, A to type, B to delete,
Start to finish, L for case, Z for page, L+Z for alphabetical/QWERTY order,
R for space, C-buttons for the text cursor, and L+A for native character
alteration. Return remains unavailable in single-line editors; sun/skull remain
apology-only. Lucky-bag Japanese decoration is intentionally retained.
The greyer N64-controller-inspired keyboard and matching N64 icons remain
V2 work, after V1 completion, and are not included here.

## Verification and remaining acceptance

Seven focused tests cover the two corrections, including fresh compilation,
glyph interiors/borders, relocation, allocation, unchanged resources, exact
changed scale range, and full patch reconstruction. The native font comparison
checks both scales, installed code/data, memory guards, unchanged saved data,
and restored checkpoint. The font's persistent allocation grows by 15,824 bytes;
per-character texture/vertex/command allocations do not grow.

The native transition check reproduces two exposed top rows in the old wipe.
The corrected wipe covers every framebuffer pixel in all three closed shapes,
retains the midpoint opening, and leaves the entire background visible when
open. Guards and saved data remain intact. All automated native checks are silent.
The complete two-stage replay regenerates this candidate from preserved RC2;
the archived standalone patcher is executed before handoff.

Original-hardware appearance remains unverified. Recheck names/options and
descenders, then enter and leave buildings. Continue normal playtesting and
report crashes, loops, save issues, English errors, or layout defects with the
V1RC3 label. Prior RC2 keyboard/HUD appearance also remains hardware acceptance
work. Broad seasonal/travel/save-restart acceptance is incomplete.

The earlier full regression is not reported as passed; historical fixture and
accounting failures remain recorded. Public release still requires provenance
review and approval. This private candidate is not a completed public release.

## Apply the patch

The local ROM is ready to copy to the flash cartridge. To use the patch archive
with the original Japanese retail ROM, not an earlier translation:

```sh
python3 apply_translation.py --rom 'Doubutsu no Mori (Japan).z64' --output 'Animal Forest English V1RC3.z64'
```

The included Python 3 patcher accepts standard N64 byte orders, verifies input,
patch, output, and boot checksums, and refuses existing output files. An ordinary
UPS patcher also supports the verified big-endian source. The manifest and
SHA256SUMS identify the package and source revisions.

Keep this playtest private. The archive contains a patch and original tooling,
not a ROM or loose assets. SOURCES.md and LICENSE-tooling.txt describe provenance
and licensing limits; the tooling licence does not cover Nintendo or legacy work.
