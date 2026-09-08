# Source glyph encoding for complete English references

## Explicit plus-glyph approval

The GameCube and native N64 character tables put the visible plus sign at
different byte values: GameCube `B4`, native `5C`. The existing N64 Latin font
already includes this glyph. Copying GameCube `B4` into a native message would
display Japanese; requiring the native encoded hash to equal the GameCube raw
hash would incorrectly reject an otherwise complete translation.

An individually reviewed `complete_reference.gamecube_plus_offsets` list binds
each affected encoded-byte offset. Before checking the original GameCube hash,
the importer reconstructs only those `B4` source bytes from complete native
`5C` text tokens. Offsets inside commands or other characters, duplicates,
unordered positions, stale source/reference hashes, and other adaptations fail.
No arbitrary glyph mapping or missing-glyph permission is introduced.

The installed candidate still uses ordinary native encoding. The independent
builder requires its complete final hash, even without edit metadata. All
normal native field, actor, flow, capacity, and layout checks remain. This is
a source-verification correction, not a font, runtime, or controller change.

## Complete controller advice

`14FD` retains all supplied English NES controller advice, including the
highlighted + Control Pad and Control Stick, all manual lines, pages, and pauses.
The native question describes using both the directional pad and analogue stick
to play. The complete 254-byte English record differs from native encoding only
at byte 112. Actual extracted GameCube data and the pinned character decoder
independently establish that correspondence. Both original native expressions
and the existing catchphrase remain; no extra field or actor order is needed.

The record has original-source, original-English, and complete-native-output
hashes in `translations/reference_matches.json`. Other unrepresentable English
punctuation still needs actual glyph support; this approval does not replace it
with shortened or reworded prose. Font-atlas investigation stays paused.

## Verification boundary

Require complete native/reference/output hash checks, token-aligned offset
rejection, no combined permissions, actual English-data agreement, full wording
and presentation retention, ordinary buffer checks, and unchanged font resources.
Normal controller-tip conversation selection and final rendering remain
gameplay/playthrough requirements.

All 109 reference tests pass, including five dedicated source-encoding checks.
The full 254-byte record has a conservative expanded bound of 300 bytes and
passes both basic and resident-runtime validation. Direct comparison against
the supplied raw English data confirms exactly one encoding difference at
offset 112. A new cartridge-load check for `14FD` is queued with the next
content batch; the unchanged runtime retains its separate native evidence.
