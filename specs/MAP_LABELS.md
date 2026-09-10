# English map landmark labels

## Native shrine correction

The native location is labelled **Shrine**, on one line at the existing one-line
offset `-25`. It is not the GameCube wishing well. `shrine_labels.py` supplies
this explicit N64 variant over the source-bound GC-derived image described
below. Only the shrine's sixteen-byte text record, first-line length (six), and
first-line Y position change. The second line is entirely zero-filled. The
renderer, icons, full-name cache, relocation table, allocation, and saved data
remain unchanged.

The supplied GC "Wishing/Well" data remains donor evidence, not the desired
N64 output. A `native_shrine` profile retains its complete predecessor profile;
validation restores just the three approved fields and checks that predecessor
through the original strict validator. The combined counter records "Shrine"
for the installed variant. Existing experimental builds with "Wishing/Well"
remain identifiable and independently verifiable.

## GC-derived baseline

The map-label variant extends the complete villager-name image. It retains its
native prefix/BSS layout, all four resident-name hooks, compiled cache helpers,
and fifteen cache positions. It appends a bounded two-line drawer and six
sixteen-byte label records; each record contains two eight-byte, zero-padded
lines. Native descriptors use the exact first-line length, not a packed length
or an unbounded string scan.

The supplied English GC executable and symbol table bind the text and line
descriptors for Shop, Police/Station, Post/Office, Wishing/Well, Train/Station,
and Dump. Two-line labels use the reference's `-19`/`-31` offsets; one-line labels
use `-25`. All retain the `-83` horizontal text offset and existing label icons.
The native empty-house label at `8088FE84` becomes `free  `, the complete GC word
within the native six-byte field. The donor's additional padding does not add
visible characters or require widening saved player-name structures.

Only the fixed-label call at `8088F1E8` uses the appended drawer. The original
post-office-only second draw at `8088F25C` becomes a no-op because the new drawer
supplies both English lines at the reference positions. Its surrounding branch,
stack stores, and return remain intact. The drawer forwards the original font
arguments and adds twelve pixels only for a nonempty second line. It scans at
most eight second-line bytes. Its 128-byte private stack frame preserves the
native caller's saved registers and prepared argument area.

Native descriptors at `8088FF20 + index*28`, indices two through seven, point to
the corresponding English record and retain their original relocated pointer
slots. Police, shrine, and station first-line Y offsets become `-19`; the native
post-office first-line offset is already `-19`. Other descriptor fields and all
resident-name draw paths remain unchanged.

The complete image is 27,072 bytes. Its DMA pair remains `03B00000`/`03B10000`;
the submenu map-owner endpoints grow to the exact image size. No permanent
reservation, resident code, save layout, icon texture, dialogue, or timing
changes. The existing conservative submenu branch bound includes the image.

Verification binds the native source, supplied GC strings and line descriptors,
unchanged name-cache image, compiled suffix, data pointers/lengths, suppressed
post-office draw, owned constant relocations, and complete combined cartridge.
All eight original text records enter combined accounting once, including in
builds where the labels remain Japanese. Only the verified installed variant
receives their English credit. Ordinary map interaction joins combined v0 smoke;
host checks do not establish gameplay or hardware acceptance.
