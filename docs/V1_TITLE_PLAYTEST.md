# Combined English artwork and keyboard playtest candidate

Local ROM: `build/title-birthday-combined-01/animal-forest-title-preview.z64`.
Local patch: `build/title-birthday-combined-01/animal-forest-title-preview.ups`.
ROM SHA-256:
`4849a83ebcff09fa188cfbe4f54a66f2691769c98f4a1dc787b48417e07fc9f7`.
Patch SHA-256:
`0e4508ff472f0db095a397dfb4e2417a2366c5d14ae2c222c705f44352a90437`.

An **Expansion Pak is required**. Without it, the game displays an English
instruction to power off and install one. The ordinary game heap and all saved
formats remain unchanged; only the title overlay owns the extra RAM. Use a
backup/copy of playtest saves, as with any experimental cartridge.

This candidate includes the full GameCube English animated title and Press Start,
both corrected Nook first-job conversation paths, the Shrine wording, twelve
English shop textures, map and inventory headings, Insects/Fish collection
headings, and the translated native clock screen. Nookington's main sign,
SOLD OUT, police-station signs/posters, and Redd's summer sign are English.
Bulletin-board latest entry/entry 1/Quit/Write and town-tune Play/Erase/OK
controls use the complete supplied English artwork with native N64 button icons.
The catalogue has top/bottom controls, the mailbox has a Mail heading, and
repayment displays Cash:, Payment:, You still owe, and Bells. These use complete
English source images, with unchanged menu logic and saved fields. The birthday
window has the full English prompt, month names, day, and OK, preserving native
date input and saved fields.
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
Original-hardware acceptance, the ordinary first-job replay, all changed menus,
multi-line editing, normal save/restart, and return-to-title/existing-save cases
remain playtest work.
Some signs, buildings, and bags still have Japanese artwork. This is a combined
experimental build, not a completed v1/public release or exhaustive acceptance.

ROMs and extracted Nintendo assets remain local and ignored. Public distribution
must use patches after the separate provenance/release review.
