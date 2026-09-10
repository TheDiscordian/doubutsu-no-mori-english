# Combined English-title playtest candidate

Local ROM: `build/title-combined-01/animal-forest-title-preview.z64`.
Local patch: `build/title-combined-01/animal-forest-title-preview.ups`.
ROM SHA-256:
`fd5ea14491387de19229847fdd3fbf5dd46dd14c461bb07a2fe6b9d7515682da`.

An **Expansion Pak is required**. Without it, the game displays an English
instruction to power off and install one. The ordinary game heap and all saved
formats remain unchanged; only the title overlay owns the extra RAM. Use a
backup/copy of playtest saves, as with any experimental cartridge.

This candidate includes the full GameCube English animated title and Press Start,
both corrected Nook first-job conversation paths, the Shrine wording, twelve
English shop textures, map and inventory headings, Insects/Fish collection
headings, and the translated native clock screen. All earlier English dialogue,
names, letters, and editor improvements are retained. It still uses the English-
first N64 radial keyboard; the GameCube-style grid is not installed.

The corrected v0 handoff remains separately available at
`build/v0-hardware-fixes-02/animal-forest-halfwidth.z64`; it does not require an
Expansion Pak and does not contain these later artwork batches. Neither ROM is
overwritten by this candidate.

Focused retention/compilation checks and silent emulator title/START/low-memory
checks pass. A captured title frame has been visually inspected. Original-
hardware acceptance, the ordinary first-job replay, all changed menus, normal
save/restart, and return-to-title/existing-save cases remain playtest work.
Some signs, buildings, and bags still have Japanese artwork. This is a combined
experimental build, not a completed v1/public release or exhaustive acceptance.

ROMs and extracted Nintendo assets remain local and ignored. Public distribution
must use patches after the separate provenance/release review.
