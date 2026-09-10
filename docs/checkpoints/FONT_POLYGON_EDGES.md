# Name/option font edges

## Candidate

`build/v1-font-edges-03/animal-forest-font-edges.z64` follows V1RC2. Its SHA-256 is
`ee6f792083c6e4a434fdb8dc440cbe667bc5fd1c497b24e03a983b7eb06dc65f`;
UPS SHA-256 is
`21e5222226ef7341df37cf9a15829f945d9c6fc60ad594163fb018a993a450f9`.
The [specification](../../specs/FONT_POLYGON_EDGES.md) describes V1-17's separate
polygon/rectangle paths and the transparent sampling-border correction.

The persistent font allocation grows by 15,824 bytes. The image is 27,744 bytes,
relocations 784 bytes, and complete aligned allocation 28,543 bytes. The native
loader allocates it at `8019C8F0` in the bounded native heap during the controlled
test. Four vertices/64 vertex bytes and nine commands per polygon glyph are
retained. No per-glyph texture allocation, glyph-ink edit, speech change,
advance-width change, or saved-format change is introduced.

## Verification

Four focused `test_font_polygon_edges.py` tests pass, including fresh compilation,
all 97 unchanged glyph interiors and transparent borders, native fallback,
retained resource comparisons, allocation/configuration/CRC checks, two
independent relocation addresses, and complete 32-MiB patch reconstruction.
Compile attempts 01/02 fail before producing cartridges because of a duplicate
SDK typedef and linker-script syntax; corrected build 03 passes.

The isolated comparison in `build/font-sampling-native-04` completes both scales,
save/guard checks, and checkpoint restoration. Transparent borders improve
left strokes and descender filtering; texture half-step offsets alone do not
establish the correction. The original font atlases remain unchanged.

The production check `build/font-edges-native-02/results.json` completes seventeen
steps, with 187 two-times-scale draws and 173 native-scale draws, exact installed
font/entry checks, intact guards, unchanged saved data, and restored checkpoint.
Its directly decoded framebuffers are inspected internally. Production polygon
output agrees with the independently drawn bordered comparison. Speech remains
the unchanged first comparison row, not a substitute for checking polygon edges.

The initial production attempt rejects the live font before installing the
fixture. Read-only decoding of its saved emulator state locates RDRAM at file
offset 103,508, with four-byte host-order words, and establishes that its only
sixteen differences are the town-name buffer at font offsets 11,324–11,339:
the native `af_world_reset` initializes these to spaces, not zeros. The corrected
check requires those exact spaces and the bound resource pointer; it does not
ignore mutable fields. The justified retry passes. The earlier prototype's
generic four-MiB scratch-write rejection is likewise retained separately, not
claimed as a passed attempt.

These are controlled native rendering and memory checks, not a normal town
playthrough or original-hardware acceptance. The user's observed cartridge
revision remains unconfirmed. Recheck names/options and descenders on hardware;
preserve V1RC2 and existing saves.
