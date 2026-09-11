# Development scene-menu translation

## Work and scope

The remaining scene-name lead expands to the complete native selector's text:
32 Japanese scene labels, twelve loading messages, and 32 setting labels/values.
All 76 receive complete English, with 25 already-English/neutral strings
retained. This is V1-28, a source-identified finding, not another human bug report.

The [specification](../../specs/SCENE_MENU_TEXT.md) records the native EUC-JP /
graphics-print encoding, all 101 string references, source identity, complete
translations, and layout. The available GC source also retains Japanese in this
menu; the batch supplies original translations instead of guessing English GC
record matches.

All text fits in 1,520 of the existing 1,780 string bytes, leaving 260 bytes
unused. The scene list moves to column one so the complete labels fit beside
settings. Long event values and the repeated loading message use explicit
newlines with the correct reset-X indentation. No layout text is truncated.
The installed owner SHA-256 is
`add4e6880bef107690e08e8a09ec2fba0c40d54dd228a0eeddd6a9025ef584dc`.

## Bounded verification

Six `test_scene_menu_text.py` tests pass in 8.697 seconds:

- Complete 101-string inventory, all 76 translations, and retained English.
- All 101 native string references at three relocated addresses, with original
  scene destinations and callbacks retained.
- Actual drawing-position instructions, complete formatted values, and the
  scene/settings/loading-message grid bounds.
- Only text, its pointer words, and one scene-list X instruction change;
  native initialization, navigation, actions, and following jump tables remain.
- Every other cartridge resource, gamestate metadata, and full UPS reconstruction.
- Refusal of altered inputs, missing translations, unsafe formats, and overflow.

A follow-up adds explicit rejection of unsupported ASCII controls/DEL; the
affected rejection test passes in 5.973 seconds, constructing the complete image
with the final builder. The English output is unchanged by that guard. No
unrelated tests, native scenarios, full suite, or percentage maintenance are run.

The grid model is not a native rendering test. Ordinary reachability and actual
appearance remain unverified. The menu initializer writes player state; it is
not executed, and no original user save or SD-card file is touched. Existing
human acceptance of saving/reloading and all reported fixes remains closed.

## Construction and next work

Build the final committed source into fresh `build/scene-menu-text-01`, retaining
RC7 and every earlier candidate. The output and source hashes belong here after
construction succeeds. RC7 remains the named hardware handoff until a subsequent
combined patch package is checked.

The separate release-build gap is concrete: the documented `make complete`
path does not include the accumulated RC correction stages. Integrate the
current correction sequence into a reproducible final-candidate recipe with
checked stage inputs/outputs, using the verified existing builders and clean
rebuild evidence. Do not rerun unchanged full historical recipes merely to
refresh their timestamps. Keep remaining content review and public distribution
requirements explicit; V2 remains deferred.
