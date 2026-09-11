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

## Committed construction

`build/scene-menu-text-01/animal-forest-scene-text.z64` is constructed from clean
revision `a87e682a431d26a7f2a533adca7af6a24dfc37dd` on the exact RC7 baseline.
The receipt records `worktree_modified: false`; construction and full original-
ROM UPS reconstruction pass.

- ROM SHA-256: `2a04f6e5c54dc2d5ed03009395af815b464bebdef51d67d899554deb54b3bcb4`.
- UPS SHA-256: `c3931b2e029bf4182864306ed2cbf28ea4c1d6c9d609cd33d68047132029b769`.
- Receipt SHA-256: `8ea67e5a9948c78fd219cd2da989c09986c78de99dbd1ffe104a11dddbc5d160`.
- Builder SHA-256: `d0530c869d840258119281e2984228a8883cbc2e903a720be93ea1ca23fad6a2`.

Reproduce into a fresh directory with
`python3 tools/scene_menu_text.py --output build/scene-menu-text-new`.
The complete output retains all RC7 corrections and prior human-accepted fixes.
RC7 saves are expected compatible in both directions, with no migration or
saved-format change; these particular directions are not independently tested.
The new development menu is not entered or enabled. RC7 remains the named
hardware handoff until a subsequent combined patch package is checked.

## Next work

The [current correction recipe](CURRENT_V1_REBUILD.md) includes this batch and
all preceding RC corrections; its nineteen-stage committed run passes and
matches this ROM and UPS. Prepare the current combined patch package and finish
remaining release/content work. Do not re-test old builds or queue a complete
historical replay. Public distribution requirements remain explicit; V2 stays
deferred.
