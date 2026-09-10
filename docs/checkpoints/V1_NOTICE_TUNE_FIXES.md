# V1 notice-date and tune fixes

The combined intermediate cartridge is
`build/v1-notice-tune-fix-01/animal-forest-title-preview.z64`.
SHA-256: `e968d09b30f29283086423fe29367026a70ce11a6272947c0cb92865b4b19c74`.
UPS: `6ae34530c117a621ed6c0ee2dd54a1fb0c90f34533fb3728af42094d34006263`.
It retains every prior title, editor, and HUD correction. It requires an Expansion
Pak; original-hardware rechecking remains pending.

`tools/notice_tune_fix.py` addresses V1-03 and V1-06. The two unwanted notice
slashes come from one 128-byte I4 image, not the English date string. Its bound
alpha-consuming model becomes transparent when that image is cleared. The
remainder of the paper and date reader stay unchanged.

The 16 native/GC melody-table rows agree in pitch ordering, vertical position,
and colours. Eight unique note images become the exact GC A–G and ? glyphs;
rest/off already match and remain unchanged. The OK label now uses its actual
GC quad, shifted left relative to the prior native-centred adaptation. Melody
code, note sounds, N64 controls, and saved tune data stay unchanged.

Four focused checks pass in 8.529 seconds: all note identities and complete
decoded pixels, retained rest/off, GC OK geometry, slash-only removal, complete
ROM/resource retention, UPS reconstruction, and changed-source rejection.
No new native harness or audio playback is needed for these data-only changes.
Normal notice/tune appearance remains playtest work.
