# Complete retained classic letters

## Installed result

`build/classic-letters-pilot/animal-forest-halfwidth.{z64,ups}` connects all
eighteen retained variants to complete English catalogue-four snapshots. The
54 original header/body/footer IDs retain their complete wording and deliberate
line breaks. All existing live creators, scheduling, full-name capture, glyph
pixels, native identities, and saved layouts remain unchanged.

- ROM SHA-256: `31c85f23c996b70bd7a4779b43f1039716a77c84806dfa5a7dd52e3780d50860`.
- UPS SHA-256: `b2169a5f3bd2141e67b67e94c376ed6349bbe02d6ffbf674ff8af7fe6464ae32`.
- Build adapters: `python3 tools/build_classic_letters.py`.
- Build combined cartridge/patch: `python3 tools/classic_letters.py`.

Only the existing startup font, transient creator, and resident configuration
resources change. The 12,000-byte font/704-byte relocation image requires 12,719
system bytes; the 61,200-byte creator/960-byte relocation image and unchanged
workspace require 67,519 temporary bytes. Both remain inside the existing
four-MiB loader bounds. The cartridge remains 32 MiB.

The classic wrapper publishes only proven contiguous text and the explicit split
output; it does not overwrite preceding metadata. Unsupported IDs, separate
buffers, and allocation/validation failure retain valid native fallback. The
selected retained variants do not replace live wider-name owner routes.

## Verification

Five host tests cover all eighteen IDs, exact field masks, snapshot/metadata
retention, full formatted text, source rejection, overlap, allocation failure,
separate buffers, old-route delegation, and atomic startup/cache publication.
Three profile tests cover independent matching MIPS builds, unchanged relocated
prefixes/state/glyphs, and rejection of altered code, relocation, or metadata.
All three cartridge/accounting tests pass, verifying all 54 source/reference
parts, exact prior-resource/index retention, patch reconstruction, rejection of
incomplete replacement lists, and combined installed-route credit.

The installed ledger verifies 751,262 replaced source characters out of 751,284.
Its only remaining flagged IDs are the two six-byte NPC tail slots and the
ten-byte furniture tail slot, all zero-filled structural storage rather than
Japanese phrases. All inventoried Japanese-bearing general and letter records
have their English replacements applied. No runtime-testing or polish effort is
added to that text count.

The silent native run `build/classic-letter-native-02` passes nine calls and
thirty memory assertions. It uses actual startup installation and the existing
on-demand allocator/DMA/relocation/creator path, creates a long Mom letter,
dynamic raffle letter, and ten-field test letter, and restores their full text
through the resident reader. The native reserve fallback reads English. Saved
payload, allocation/stack/module guards, fixture release, retained startup owner,
checkpoint restoration, resumed execution, and cleared scratch checks pass.
Its separate test allocation is 8,192 bytes. Audio is disabled, no images are
uploaded, and saves are isolated and initially blank. Checkpoint restoration is
not normal gameplay-save validation.

## Corrected integration issue

The first native run exposed a real packaging failure, not a formatter failure:
the reserve-letter report omitted newly replaced body/data-table files from its
inherited replacement list. A following assembler therefore restored the native
Japanese reserve body. The complete new snapshot/reader checks already passed
in that run; the reserve fallback correctly failed.

The reserve builder now records every newly replaced file. The following builder
also compares every retained resource and DMA index with its actual predecessor,
and a regression deliberately removes the body entry to prove that omission
fails. The corrected combined cartridge retains the English bank. The native
fixture's split output is also disjoint from its mail guard. The single corrected
native run passes; the first run is not recorded as a complete success.

## Next work

Continue ordinary v0 progression,
menus/editors, mail/board reading, and normal save/restart. Three zero-filled tail
slots are structural storage, not Japanese phrases to replace. Do not add another
standalone letter matrix or repeat unchanged accent tests. Run the assembled
candidate's regression suite, fix concrete failures, and prepare the patch-only
human-playtest handoff before broader seasonal/hardware/polish testing or v1.
