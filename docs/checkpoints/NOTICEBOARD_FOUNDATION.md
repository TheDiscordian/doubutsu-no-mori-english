# Bulletin-board foundation checkpoint

## Implemented scope

The compact board codec stores complete generated-text identities and literal
substitutions within the existing 96-byte message. It retains the eight-byte
timestamp and 104-byte saved stride. Its independent Python and freestanding C
implementations agree, including maximum capacity, corruption rejection, and
overlapping-input handling. All 63 scoped reference templates fit with complete
sixteen-byte dynamic fields; maximum used storage is 84 bytes.

The four initial English announcements have explicit source and native-control
bindings. Complete bodies are 141, 166, 137, and 156 bytes. Only `C Stick` changes
to `C Buttons`; the supplied wording, punctuation, spaces, and manual newlines
otherwise remain exact. The full-body restorer uses immutable catalogue four
without changing saved-mail semantics or the catalogue itself.

The page planner retains complete six-line, 192-pixel pages and advances through
additional lines without discarding text. It preserves all tested full-field
reference bodies, including the seventh visible line of `01AE`. The initial
four fit one page with the approved font advances.

These helpers are not installed in the ROM. Native drawing, tag discrimination,
creation/publication, full-board shifting, editor interaction, and persistence
remain. The current complete ROM stays `build/native-items-pilot/`; no translation
coverage is credited for uninstalled board helpers. No fonts, saved layouts,
memory bounds, title graphics, or user saves change in this checkpoint.

## Verification

Eighteen focused host tests pass: thirteen codec/initial-body checks and five
page-planner checks. The same eighteen tests pass under AddressSanitizer and
UndefinedBehaviorSanitizer in 1.971 seconds, recorded in
`build/noticeboard-foundation/sanitizer-tests.log`.

The checks include every field position/width/article, 500 random literal-field
records, every single-bit envelope corruption, exact storage exhaustion and
one-byte overflow, unsupported versions/kinds/catalogues, output guards and
aliasing, both capitalization states, and 120 initial-post writes across all
fifteen saved positions. Full initial-body restoration checks the supplied
wording and every manual break. Each actual mock cartridge read is failed in
turn; output remains unchanged, and subsequent recovery succeeds. These are
host calls through a bounded DMA adapter, not N64 execution or native saves.

Page checks preserve full dynamic fields for all 63 scoped bodies, glyph pairs,
all 1,024-byte bodies, blank lines, and invalid data beyond the requested page.
Seasonal and treasure reference feasibility does not approve their meanings,
native calendars, or field sources.

Two independent builds with the existing Docker VR4300 toolchain produce the
same relocatable object SHA-256:
`aebdf95d86635cc6d62acc711afa698c5ffafc750690838f0c05cacb2507f23b`.
The object has 1,608 instruction bytes, fifty constant bytes, and no mutable
global data/BSS. Its five imports are the existing mail pack, unpack, restore,
line-scan, and CRC32 routines. The largest new individual stack frame is 536
bytes; this is not a bound on the entire nested decoder call stack. No linked
resident image or native overlay is changed by this compilation.

The first host compile rejects fixed-size string initializers that omit their
NUL under the installed GCC warning policy. The constants retain their NUL in
source and explicitly compare only the seven controller-text bytes. The final
host, sanitizer, and VR4300 builds all pass with warnings treated as errors.

## Reproduction

```sh
python3 tools/audit_noticeboard.py
python3 -m unittest discover -s tests -p 'test_notice*.py' -v
python3 tools/check_notice_assembly.py
```

Local inputs, generated approvals, compiled objects, and logs remain ignored.
Source-format, controller, and ownership details are in
[the noticeboard specification](../../specs/NOTICEBOARD_TEXT.md).

## Continue implementation

1. Finish native editor/tag discrimination, including conversion paths and old
   manual posts. Keep compact records out of ordinary draft editing.
2. Integrate the full-body reader with the actual notice overlay. Preserve
   C-button post navigation, animations, date/entry labels, and A/B/START actions;
   provide complete extra-page access without stealing existing post controls.
3. Connect initial creation only with the complete reader, validate allocation
   and relocation, and update fresh-build accounting only after installation.
4. Review and implement the 41 seasonal and eighteen treasure bodies, with full
   English fields and unchanged native calendar/reward/coordinate meaning.
5. Batch native full-content, corrupt-input, publication/retention, editor,
   shifting, and save/reload checks. Normal gameplay, human review, original
   hardware, remaining other text, patch-only release preparation, title-first
   artwork, and the GameCube-style keyboard remain in the full project goal.
