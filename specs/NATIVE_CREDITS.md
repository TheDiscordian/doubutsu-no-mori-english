# Complete English native credits

## Verified native destination

The fruit-box actor contains the K.K. performance credits, not an item-label
menu. Its original file is VROM `00963DF0`, linked at `80AA3BA0`, with 4,688 bytes
and SHA-256 `e34789965dda5548c380a87e7384b635931fe6d6826356332f3ba6aa8878757c`.
Relocation VROM `00965040` contains 416 bytes with SHA-256
`4eed1aaf28aacc093e4b6bf8c6d1fb773bdaeaba8b0228a05624b758ef6f8e31`.
Its header is text/data/rodata/BSS/relocation-count
`4496, 176, 16, 224, 98` in decimal.

The loader at `80AA3D08..80AA3D94` reads ten fifteen-byte rows into the BSS
buffer `80AA4E20`. Each starting ID is `04EA` plus a page offset. IDs increment
per row and clamp to `0557`, excluding all shop names and item-category labels.
The whole loadable group therefore contains 110 native entries, `04EA..0557`.

The page table at `80AA4D54` begins with these seventeen decimal boundaries:
`0, 3, 9, 18, 27, 36, 44, 52, 56, 64, 69, 77, 85, 91, 98, 105, 107`.
The following three zero bytes are padding. The K.K. controller at
`80A8AAD0..80A8AB34` increments the page after timer 223 and ends drawing at
page 16. Its actor is VROM `00949BE0`, linked at `80A89960`, SHA-256
`d99c2106beef460f2174528941d889edb19be315e6fd1bd5b1f59f5d533dc5ca`.
Thus sixteen actual pages display `04EA..0554`; the ten-row lookahead also
loads the three reserved entries `0555..0557`. No extra page is introduced.

The original `80AA3D94..80AA406C` uses the native fade, role/name scale, vertical
placement, and direct-font flags. Its font call at `80AA3FFC` consumes fifteen
bytes; the original loader and drawer advance their row pointers by fifteen.
The next BSS object begins at `80AA4EB8`, so the current 150-byte buffer cannot
be enlarged in place. The original BSS ends at `80AA4ED0`.

## English identities

The pinned supplied English source uses `aMIK_STRING_NUM = 10` and
`aMIK_STRING_LEN = 25`, with its own page and role-line tables in
`src/actor/ac_mikanbox_clip.c_inc`. The reference drawer calls
`mFont_SetLineStrings_AndSpace` with full row length, scale, and variable-width
drawing enabled. The supplied executable's loader, drawer, page table, and
role-line table are independently bound by full hashes in `credits_strings.py`.
The native direct-font wrapper at `80090E1C` forwards the same stack arguments;
its implementation at `80090CC0` uses the requested width flag. The x origin is
150, not an instruction to centre the row or strip its leading spaces.

All 110 native IDs have explicit English replacements: 74 complete
identity-matched references, nineteen original drafts/transliterations, and
seventeen preserved native blank rows. The imported references use the active
English credits at `077B..07FE`, not the older unused credit strings also in
the disc. Every matched reference retains its full wording and leading spaces.
Fifty-eight resulting rows exceed the old fifteen-byte destination.

The native Japanese identities determine the mapping, not legacy position:

- `0520/0521` retain Kenshirou Ueda and Kunio Watanabe in their native order.
- `0539` uses Atsushi Nishiwaki, not the legacy Nishikawa spelling.
- Native blank `050B` stays blank; the English release's Yumi Yoshimi row is
  not a replacement for a native contributor.
- `054A/054B` retain Keizo Kato and Minoru Narita, not Takao Sawano or a
  Library Support label. Their native project-management role stays distinct.
- `0552` restores Sarugakucho; `0554` retains Hiroshi Yamauchi, not Satoru Iwata.
- Native character/player/data/field and Famicom programming roles remain
  separate. The two-line Famicom sound role retains both lines and its scale.
- The native title becomes Animal Forest; decorative non-Latin legacy marks
  and the English release's title glyphs are not inserted as text bytes.
- The three unused reserve rows say Reserved; they are not credited as
  translated Japanese gameplay text or shown as new pages.

The complete English output group hashes to
`1ab4a9d3d2d0c854cd2ae3d48fc3c40e6114e8867cd50446ee85710203ed5020`.
The 74 complete donor rows in native order hash to
`a1e5e6183398737fa0fdd62854f845a6de1da63bea8c52589142c233c4aa7f09`.
Both digests prefix each encoded row with its big-endian sixteen-bit length.
Source bank hashes and native IDs bind every output identity. A shortened,
reordered, substituted, partial, or stale group fails independently in the
builder. Original wording and romanisation still receive final editorial review.

## Installed caller and ownership

`--english-credits` enables the group in candidate generation and construction.
It shares general-string relocation to `02600000` without requiring new
resident-module code. Other IDs retain their own capacity limits.

The caller uses twenty-five-byte rows in a separately appended 256-byte BSS
area at `80AA4ED0`. The original 224-byte BSS and every existing object offset
remain intact. The resident actor spans 5,168 bytes, ending at `80AA4FD0`.
The relocation BSS header becomes 480 bytes. The actor-table entry at
`80102210`, including profile `80AA4D30`, is checked as a whole before only its
VRAM-end word changes. Both low-half buffer relocations remain type 6.

Seven instruction words change: two buffer pointers, two row strides, loader
length, draw length, and the reference's variable-width draw flag. Page/role
tables, scales, y positions, music behaviour, controller actions, and native
save layout do not change. No approved atlas or font metric changes.

The normal structure route at `80057940` uses `aSTR_get_overlay_area_proc`,
which ignores the requested size and supplies one existing 8,192-byte slot.
The structure actor `008CB690`, SHA-256
`47d03c6fd4526d45a8685747a90253fb0daa102f0a4831a59a9fe472fab62987`,
binds that allocator and its slot initialisation. Its BSS pool at `809EB528`
has nine 8,192-byte slots. The enlarged credits actor plus all 416 relocation
bytes still fits one slot. Generic allocation and overlay loading use the
updated VRAM-end metadata. The next actor starts at `80AA5A70`, beyond the new
credits end; neither linked range nor physical slot overlaps its neighbour.

## Recorded validation

All 860 host tests pass, including nine credits tests for complete identities,
capacity rejection, exact seven-word changes, BSS ownership, all page ranges,
terminal clamping, relocation carry, independent builder output, and unchanged
unrelated entries. Independent reconstruction verifies every one of the
13,383 installed edits, every untouched general string, and the original-ROM
UPS round trip. The import adds 106 candidates and updates the provenance of
four already-applied credit labels without changing their wording.

The silent batch `build/smoke-native-credits-02` contains 282 records. It passes
all sixteen actual pages, all 110 loadable rows, 26 native draws, 3,425 glyphs
and texture loads, and 97 memory assertions. Each glyph vertex stays within
the native screen, and actual primitive-colour commands match fade boundaries
19/20/21/59/60/183/184/222/223/224. Complete rows and original BSS remain intact.
The native renderer stores zero vertex colours and uses primitive-colour
commands for the fade. The fixture checks both representations separately.

The batch uses 4 MiB, disables audio, seeds no user data, enables no cartridge
or Pak writes, restores its checkpoint and complete saved payload, releases its
test allocation, and shuts down gracefully. Both final Flash and Pak hashes
match the canonical blank fixtures. Generated display lists are inspected in
owned test memory, not submitted as a normal K.K. performance.

The build `build/native-credits-pilot/animal-forest-halfwidth.z64` hashes to
`77dc0110732c532147d066424db08d10f07281c6cd9064a937a044eb3b36ea57`;
its UPS hashes to
`49791de1c3fd1a22676ebaeb3d14972552127d0c9874d3d1ec185dbaa846abce`.
Candidate JSON hashes to
`37ceffcd6c6a74d4ea1481689369cca16e2cca7da6dd41932209402dc3d887fd`.
The scenario hashes to
`6d1dfe4afe8100527a951fe859d8fdb744b6e8ca368ba1f981679a83fdd67a1b`,
the native helper to
`b2038dc98b917cbe737ae86c06c8d23061488e0ef887a3c5fe8187e90c07cac2`,
and the 282-record results file to
`e962ee008389bd936f303f0f6d8cc0158aefe86229d494e69db62252fbac45be`.
Only credits actor/relocation, the actor-end word, general strings/offsets, and
DMA metadata differ from the shared-word pilot. Normal scene progression,
whole-screen visual presentation, final editorial review, and original hardware
remain acceptance work; no hardware or complete-game claim follows.

## Acceptance

- Establish every native source/English identity and retain each complete name
  and role; exclude GameCube-only contributors from the native credit list.
- Bind the complete actor, relocation, allocator metadata, source row tables,
  draw signature, and English executable reference.
- Check complete row loading, all actual page boundaries, the terminal clamp,
  new BSS ownership, direct drawing, and unchanged surrounding actor data.
- Preserve placement, scale, and pacing intent when adapting English rows;
  do not infer that a wider buffer alone gives correct visual alignment.
- Use one bounded silent credits batch, retaining isolated saves and restored
  checkpoints. Normal K.K. performance and hardware remain separate checks.
