# English town-name suffix

The supplied GameCube English string `01E4` is empty. Native Japanese `01E4`
contains the two-character village suffix. English town-name construction omits
this suffix rather than translating it into an extra word after every town name.
The candidate is bound to the original source hash, complete English bank/table,
and three GameCube town-name functions. It contains no new line, timing, or
capitalisation commands.

The native formatter at `80094F24` loads this entry into a ten-byte temporary,
measures its non-padding length, copies that many bytes after the town name,
and returns the combined length. With an empty entry, the existing string loader
provides padding, the suffix length is zero, and no suffix bytes are appended.
The two constructors through `800950D8` retain their six-byte saved-name reads,
eight-byte output/padding, and existing free-string setter. The complete native
consumer span is hash-guarded and remains unchanged. There is no RAM allocation,
saved-field change, global width increase, or machine-code patch.

`--english-town-suffix` adds the one exact empty candidate to the selected
translation batch. The normal importer preserves every other entry, cumulative
table structure, source identity, and bounds. A non-leading empty entry repeats
the preceding positive cumulative end; it does not introduce a zero bank
terminator. Planned and final-cartridge verification require the empty entry
and unchanged consumers. The complete recipe is
`bash tools/build_town_suffix_pilot.sh`.

The combined progress counter credits this grammatical omission only through
its verified source/reference/installed-consumer approval. Arbitrary blank
translations still receive no credit. This is an applied text change, not a
claim of gameplay, save/reload, or original-hardware acceptance.
