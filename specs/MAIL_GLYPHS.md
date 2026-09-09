# Complete missing mail glyphs

## Source inventory

`tools/audit_mail_glyphs.py` checks the frozen catalogue-two resource against all
eight supplied English banks, the decoder, and the donor mail implementation.
It walks every complete part and skips verified command arguments. The ignored
report `build/mail-glyph-audit/report.json` records all occurrences, not only the
first transcoding failure in a part. Three synthetic parser tests pass.

The 59 unavailable catalogue-two parts contain 100 unsupported occurrences:

| GameCube code | Character | Occurrences | Existing separate resource |
| --- | --- | ---: | --- |
| `2A` | Tilde/wave | 46 | No; three Katrina signatures have a scoped native decoration mapping |
| `3B` | Droplet | 2 | No |
| `5C` | Anger mark | 2 | No |
| `60` | c with cedilla | 6 | No |
| `7C` | e with acute | 1 | No |
| `AE` | Slash | 3 | `80AE` |
| `BF` | Smiling face | 30 | No |
| `D0` | Semicolon | 5 | `80D0` |
| `F7` | Division sign | 5 | No |

Five bodies require only glyphs already present in the separate font resource:
`003D`, `00F6`, `0136`, `01F8`, and `0328`. The first three are the known pending
HRA score, birthday, and Mom bodies. The other two still need native identity and
creator matching; appearance in a GameCube catalogue is not translation credit.
The scan includes GameCube-only and diagnostic data. Keep those identities
distinct from actual N64 text and do not discard unexpected diacritics as noise.

## Required implementation

The source importer, catalogue-four parser, C/Python formatter, and token-aware
line/page/footer consumers implement points one through six below. The new
catalogue contains all 4,866 reference parts. All 80 final focused tests pass,
including complete C restoration and full page/footer drawing for glyph-bearing
references. Both formatters and the C restorer pass all 6,514 declared reference
assembly cases. Cartridge execution passes the complete glyph and old-catalogue
batch; affected creator routing remains active.
The [checkpoint](../docs/checkpoints/MAIL_GLYPHS.md) records exact evidence.

Catalogue four uses format one, semantics two, VROM `030A0000`, and 326,288
bytes. Its SHA-256 is
`76aa61189ccc1043ee4d91f3fd7a2d351b0914b4a932515b47b5bcbe426323bb`.
Semantics two accepts only the fourteen registered pairs; previous catalogue
semantics still reject them. Composite parts cannot split a pair. Empty
substitutions capitalize `8060` to `8008` and `807C` to `800A`, matching the
complete donor `tbl$1185` uppercase table. Field literals still reject `7F/80`.

The 1,600-byte separate font resource uses the same row geometry and first five
cells. Added codes/advances are `2A:6`, `3B:12`, `5C:12`, `60:6`, `7C:6`,
`BF:12`, `F7:6`, `08:6`, and `0A:6`. Its SHA-256 is
`12a90673f21a6c0bfa3fc05039279b1efc65d96319460ae36993eafa0822c105`.
Source code identities are explicit; Unicode aliases are not interchangeable.
The full donor uppercase table is 112 bytes with SHA-256
`fe8c41e0392639364d87bbcb9c0eda5a9991304c76cf49319a4a5d293bd2c897`.

The catalogue installer requires the current complete resident sources and an
exact approved fourteen-cell cartridge font. The final ROM builder checks the
actual installed font digest and requires snapshot read mode. Main-dialogue
import capability remains restricted to its existing five glyphs.

1. Keep immutable catalogues two and three readable and unchanged. Register new
   complete wording/encoding under a new catalogue identity only after its exact
   bytes, semantics, source identities, and consumer capabilities are verified.
   Do not mutate an existing saved letter's catalogue interpretation.
2. Extend source transcoding and catalogue field scanning with explicit registered
   two-byte glyph pairs. Reject unknown/truncated pairs, including pairs split
   at invalid part boundaries. Commands remain two bytes and keep their field,
   forced-article, and capitalization semantics. Do not normalize punctuation.
3. Extend `runtime/mail/format.c` and its independent Python model to retain
   complete glyph pairs atomically. Keep output byte bounds and saved literal
   field restrictions; template glyph support does not authorize arbitrary
   two-byte input in player/villager names or edited letters.
4. Make `af_mail_next_line` consume a registered pair once and retain byte offsets
   for drawing. The current single-byte width loop would split it or count the
   second byte independently. Preserve explicit newlines and existing page/footer
   rules; never automatically reflow the donor's intended line/page layout.
5. Make snapshot footer alignment in `runtime/mail/reader.c` token-aware. Its
   current per-byte width loop must not double-count a pair. Verify that native
   sentence drawing receives complete byte spans and the existing separate-font
   hooks select the correct source pixels and advances.
6. Extend the separate exact-source font for the seven remaining glyph identities.
   Its sixteen-cell row has space, but header/count/mapping hashes and startup
   validation require a new verified build. Preserve existing cells/widths and
   every native atlas pixel. The paused atlas-edge issue stays paused.
7. Connect native letter creators only after complete reader and catalogue
   installation is verified. Preserve original field sources and save metadata.
   Batch all affected Mom, birthday, HRA, composite-reply, and other verified
   letter identities instead of enabling one glyph-bearing body at a time.

The glyph reader occupies exactly 24,576 linked resident bytes, with no remaining
linked headroom. Shared `af_crc32` and `af_mail_draw` remove duplicate instructions
without changing validation or rendering semantics. Its reservation remains
32,768 bytes and its test scratch remains separate. The last integrated
on-demand creator has 256 image bytes free; its new source-bound build and
glyph routing are pending. Measure actual new code before choosing where it lives.
Do not enlarge the resident reservation into its test scratch or assume the
creator's current 32 KiB bound permits a larger image. Any required bound change
must update loader/build checks and prove four-MiB allocation and rejection paths.
Avoid keeping additional complete formatters resident when a shared implementation
can retain the old catalogue semantics and fit the established memory limits.

## Acceptance

Compare every source glyph occurrence and complete translated part. Check all
registered/unknown/truncated pairs, command adjacency, empty-field capitalization,
output limits, line/page boundaries, footer alignment, both draw paths, and
unchanged original glyphs. Reopen snapshots from all supported catalogue IDs,
then verify isolated save round trips without changing saved structure sizes.
Cartridge-created affected letters must reconstruct and draw completely before
translation credit. Normal gameplay, visual/editorial review, and hardware still
require their own evidence; this inventory is preparation, not installation.
