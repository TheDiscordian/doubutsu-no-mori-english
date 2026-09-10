# English bulletin-board and town-tune controls

## Implemented

The bulletin board uses the complete supplied GameCube latest entry, entry 1,
Quit, and Write artwork. The four labels fit the existing 4,096-byte region;
the two navigation arrows retain their native pixels and move beside their
English labels. Native button symbols, animation, notice text, CPU code,
allocations, and saved fields remain unchanged. See [the notice specification](../../specs/NOTICE_ARTWORK.md).

The town-tune editor uses the supplied Play, Erase, and OK artwork. Play and
Erase replace same-size IA8 images. OK fits half the original I4 allocation,
centred on the original finish control with a narrower source-compiled load
and quad. Native Z/R/Start images, notes, input, and saved melody remain unchanged.
See [the tune specification](../../specs/TUNE_ARTWORK.md).

## Verification

Three notice checks pass in 30.216 seconds, including exact pixel/alpha
conversion, independently compiled native texture commands, complete prior
resource retention, strict installed notice/grid ownership, and UPS recovery.
Three tune checks pass in 7.230 seconds, including the complete converted images,
unchanged controls/geometry outside the finish label, independent MIPS commands,
strict corrected grid ownership, full resource retention, and UPS recovery.
The combined-title check passes in 7.921 seconds. Unchanged title, low-memory,
conversation, and controller code reuse their recorded native evidence;
these data-only checks do not establish ordinary appearance or navigation.

## Candidates

Notice-only batch: `build/notice-artwork-01/animal-forest-halfwidth.z64`.
ROM SHA-256:
`96d2b253bdf727bf537c416d49fdd0a0eb70abfe0be8a0c8ade9dafbd46de941`.
UPS SHA-256:
`9b0beff8a8a7be14ac54aa59170095cf04d1520f4b52b20533197147a04f25df`.

Both batches: `build/tune-artwork-01/animal-forest-halfwidth.z64`.
ROM SHA-256:
`4fcebd1758f3ca5bed1a9c7dd3659f961f27d51572ea5b4f13c49039e2b8d963`.
UPS SHA-256:
`e9be809d6b391ba0677462e9381b49f95266e7a2407d7e65a55b1de38462139b`.

Combined English title: `build/title-tune-combined-01/animal-forest-title-preview.z64`.
ROM SHA-256:
`41282aa2c64a946a7588cc0434a8ddf1f3b51727b52205ae708b71f16c0b4cca`.
UPS SHA-256:
`540faec94f2b6e4c4ca575d2ba76821b2377624656723ad7e277ced9eba56cc8`.
The combined 32-MiB cartridge requires an Expansion Pak. Ordinary heap bounds
and saved formats remain unchanged. All earlier conversation corrections,
Shrine wording, English text, corrected keyboard, and artwork remain installed.
Normal scene, input, save/restart, and hardware checks remain playtest work.

## Remaining art

The train-station atlas audit covers all eighteen 128×32 CI4 textures across
three station types and both seasons. Fifteen match the supplied GC pixels
exactly; three differ only in clock/surface details. No lettering appears in
the inspected station atlases, so none is changed. Summer station-one T2 and
winter station-one T2 differ in 24 stored bytes each; summer station-two T3
differs in nine. This is not a claim about every separate object near a station.

The remaining native first/last labels belong to the catalogue: its overlay
at VROM `007A28F0` contains the asset start/end pair `00B2A000/00B35930` at
offset `9890`. Bind corresponding English artwork and native readers next.
Other decorative marks, bags, and uncovered interface images remain in scope.
