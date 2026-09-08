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
The following three zero bytes are padding, not additional proven pages.
The draw routine uses adjacent boundaries and at most ten rows. Actual page
selection/controller limits still need a complete source check.

`80AA3D94..80AA406C` preserves the native fade, role/name scale, vertical
placement, and draw flags. The font call at `80AA3FFC` consumes fifteen bytes;
the loader and drawer both advance their row pointers by fifteen.
The next BSS object begins at `80AA4EB8`, so the current 150-byte buffer cannot
be enlarged in place. The original BSS ends at `80AA4ED0`.

## English reference and planned import

The pinned supplied English source uses `aMIK_STRING_NUM = 10` and
`aMIK_STRING_LEN = 25`, with its own page and role-line tables in
`src/actor/ac_mikanbox_clip.c_inc`. The reference drawer calls
`mFont_SetLineStrings_AndSpace` with full row length, scale, and alignment flags.
Bind the corresponding supplied executable functions before relying on these
source definitions for a production patch.

Use complete native contributor names and role meanings. The English release
adds and rearranges credits, so same-ID copying is not a valid identity rule.
The legacy translation contains complete English candidates, but fifty-one
rows exceed the native fifteen-byte loader; some exceed it even without their
leading spaces. Trimming names or role words is not an acceptable fit strategy.
Source title/padding anomalies also require explicit matching or original edits.

The planned caller uses twenty-five-byte rows, matching the English version's
capacity, with a separately appended 256-byte aligned BSS area for ten rows.
Keep all original BSS objects and offsets intact. Verify and update the actor's
resident-size metadata and relocation BSS length, the two row-buffer pointers,
both row strides, and both loader/draw lengths together. Do not change existing
page timing, source contributor identity, music behaviour, or native save data.
This is a design, not an installed patch.

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
