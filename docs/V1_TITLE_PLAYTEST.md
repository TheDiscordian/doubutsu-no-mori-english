# Combined English artwork and keyboard playtest candidate

Local ROM: `build/title-civic-interior-combined-01/animal-forest-title-preview.z64`.
Local patch: `build/title-civic-interior-combined-01/animal-forest-title-preview.ups`.
ROM SHA-256:
`a8072a76783317215ae85afbf31cca77422d5b783512194d8269004f31073780`.
Patch SHA-256:
`7398d8d3c3bd3b7e234057daabbf61684811e367be583ec4d82045dae2d624bd`.

An **Expansion Pak is required**. Without it, the game displays an English
instruction to power off and install one. The ordinary game heap and all saved
formats remain unchanged; only the title overlay owns the extra RAM. Use a
backup/copy of playtest saves, as with any experimental cartridge.

This candidate includes the full GameCube English animated title and Press Start,
both corrected Nook first-job conversation paths, the Shrine wording, twelve
English shop textures, map and inventory headings, Insects/Fish collection
headings, and the translated native clock screen. Nookington's main sign,
SOLD OUT, police-station signs/posters, and Redd's summer sign are English.
Both Nookington seasons include the small GameCube doorway wordmark and full
CLEARANCE banner, retaining the native red offer. Both dump signs use the exact
English GC design. The fishing props match GC's omission of the Japanese barrel
name and headquarters placard, with the remaining geometry and event unchanged.
The New Year fortune table uses the complete matching GC model inside its native
allocation; the shrine and fortune outcomes stay native. The countdown display
uses the exact `min.`/`sec.` artwork, preserving digits, timing, and animation.
The festival stall uses the GC striped-awning, balloon, and pinwheel design,
with one shared mesh and a reflected second placement. The complete adaptation
fits the native allocation and preserves actor/event code, goods, and saves.
The reflected mesh is not an exact import of the separate GC right-hand mesh;
the difference is recorded rather than silently changing a shared memory limit.
Seven Nookington interior signs use their exact English GC textures: second-floor
direction, information notices, welcome/opening hours, clearance sale, thank-you
signs, and the raffle-day board with `RAFFLE-TICKET DAY` and `BIG CHANCE!`.
The native room geometry, lighting, shop hours, raffle rules, and saved layouts
remain unchanged. One isolated palette colour matches the donor without changing
the board edge that shares its palette. Ordinary room appearance remains unverified.
The police-station interior posters use the exact English GC `WANTED!` and
`I want U!` images; the post-office mailbag reads `MAIL`. All three fit existing
native texture slots, with identical donor colours, UVs, and lighting. Room
palettes, geometry, commands, gameplay, and saved layouts remain unchanged.
This postal bag is unrelated to the retained Japanese lucky-bag decoration.
Bulletin-board latest entry/entry 1/Quit/Write and town-tune Play/Erase/OK
controls use the complete supplied English artwork with native N64 button icons.
The catalogue has top/bottom controls, the mailbox has a Mail heading, and
repayment displays Cash:, Payment:, You still owe, and Bells. These use complete
English source images, with unchanged menu logic and saved fields. The birthday
window has the full English prompt, month names, day, and OK, preserving native
date input and saved fields. The Controller Pak screen has English Done, Free,
Notes, and Pages images, with unchanged native Pak operations and layout.
Editor confirmation and all inventory/Controller Pak warning windows are English,
including the native 50,000-Bell limit and explicit repair data-loss warning.
The warning code is unchanged; appended text uses a bounded extra 4 KiB in the
ordinary menu pool, without expanding the heap or changing saves.
The gyroid's twelve sales/configuration responses are also English, using a
separate safe temporary buffer, with native prices and transactions unchanged.
All earlier English dialogue, names, letters, and editor improvements are retained.
The keyboard uses the GameCube-style 10-column, four-row grid, with native N64
controls, corrected direction commands, and unchanged saved input capacities.

Use the stick or D-pad to select keys, A to type, B to delete, and Start for Done.
L changes case, Z changes page, L+Z changes QWERTY/alphabetical order, and R inserts
a space. C-buttons move the text cursor; L+A applies the native character alteration.
Unsupported characters are disabled; the keyboard does not enlarge saved names.

The corrected v0 handoff remains separately available at
`build/v0-hardware-fixes-02/animal-forest-halfwidth.z64`; it does not require an
Expansion Pak and does not contain these later artwork batches. Neither ROM is
overwritten by this candidate.

Focused retention/compilation checks and silent emulator title/START/low-memory
checks pass. The unchanged title reuses its recorded native evidence. A focused
keyboard probe confirms case, insertion/deletion, the six-character name limit,
left/right cursor movement, page selection, and Done returning to Rover's English
conversation. That probe uses a matching older isolated checkpoint with guarded
replacement of the corrected controller code, not a fresh boot of this ROM.
Captured title, name, and conversation frames are visually inspected. A separate
native birthday drawing check verifies the complete ordered English font output
and unchanged birthday/save state with intact memory guards; ordinary date entry
is not inferred from that controlled fixture.
The embedded warning/confirmation host and combination checks pass. Its native
fixture verifies confirmation loading but stops before drawing at a test-script
error; warning drawing is not claimed verified.
The gyroid service batch passes native loading, complete response composition,
zero/five-digit prices, and full font output with its callback/save/guards intact.
This controlled check does not establish ordinary navigation or transactions.
Original-hardware acceptance, the ordinary first-job replay, all changed menus,
multi-line editing, normal save/restart, and return-to-title/existing-save cases
remain playtest work.
The Nookington, dump, fishing, fortune-table, countdown, and stall batches pass focused
source/graphics/retention/patch checks and title combination checks. These do not
establish ordinary seasonal-event appearance or gameplay.
The stall's complete native-command trace also checks both placements, all
triangles, the balanced reflection matrix stack, and restored culling. Actual
in-scene appearance, lighting, and shadow fit remain unverified.
The Japanese decorative lucky-bag artwork is intentionally retained in both
menu and world designs, matching the English GC game and the user's choice.
Other unreviewed artwork and ordinary appearance acceptance remain. This is a
combined experimental build, not a completed v1/public release or exhaustive
acceptance.

ROMs and extracted Nintendo assets remain local and ignored. Public distribution
must use patches after the separate provenance/release review.
