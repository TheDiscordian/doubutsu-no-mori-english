# Main-program diagnostic translations

V1-29 adds thirteen original English translations outside the dialogue banks
and scene-selector owner: eleven generation stages, one Famicom index label,
and one unused reserve literal. This is a source-identified omission, not a
new human bug report or evidence of a gameplay failure.

## Applied text

| Native RAM | English |
| --- | --- |
| `801175B0` | Init BG/FG |
| `801175C0` | Make rivers/cliffs |
| `801175D4` | Make sea |
| `801175E4` | Make bridges/slopes |
| `801175F8` | Make police box/plaza |
| `80117614` | Make shop/post office |
| `80117634` | Make ponds |
| `80117640` | Set base |
| `80117654` | Make river mouths |
| `80117668` | Select blocks |
| `8011767C` | Generation complete |
| `801176C0` | Famicom %d |
| `80117CD4` | Reserve |

The last literal is the compiled `(予約)` from a discarded expression in
`cfbinfo.c`; it is not a newly found ordinary player message. The other twelve
have actual graphics-print readers. The supplied GC room source also retains
Japanese for its diagnostic Famicom label, so no English GC payload match is
claimed. The N64 game identities and eight-entry index limit stay unchanged.

Every complete ASCII string, terminator, and padding fits its original slot.
Combined storage remains 252 bytes. The eleven-word pointer table, both complete
reader functions, existing English prefixes, `%d` argument, screen origins,
and every main-program byte outside those slots remain unchanged. No pointer,
instruction, allocation, save reader/writer, or debug-access change is made.
The [specification](../../specs/MAIN_DIAGNOSTIC_TEXT.md) records the exact contract.

## Verification and committed construction

Four focused `test_main_diagnostic_text.py` checks pass in 0.145 seconds. They
cover all thirteen complete strings, untouched bytes, actual table-selected
strings, screen-column bounds, changed-source rejection, control/overflow/format
rejection, and the new final Makefile command's ordering and explicit input.
These checks use the original source resource, not historical candidate tests.

The new stage executes from clean committed revision
`5dcc07ed779f18ba1973e055e67c65b9855190d5` against the exact current RC8.
Complete cartridge reconstruction and original-ROM UPS application pass.

- ROM: `build/main-diagnostic-text-01/animal-forest-diagnostic-text.z64`.
- ROM SHA-256: `0561182044c1526010ed77b1b9c72ac268794c2f7b615f8fa70c007f366483bf`.
- UPS SHA-256: `acdfe82eae085337cc23d261154fbd06004f56d234b0a76587d2e6885047ae47`.
- Receipt SHA-256: `20f302a4b1f37a4ba9f7a6e168e8015a569f64c87f36406d34a490e0564368b0`.
- Builder SHA-256: `570750f79c90ad4fd8c4fbc13e116d176143b8ec7939bb88c3a66aa9b18ff00b`.
- Changed main-owner SHA-256: `be45233133210e9515425bd9074a0004f8b9fc846dd3d2aeb9d15aa4ec0748f1`.

`make complete` includes this new stage after the existing nineteen-stage
correction runner. The four-command dry run passes. Its final outputs are
under the isolated checkout's `build/v1-final/`; the complete command has 109
construction stages. No full historical replay or old-build re-test runs.
The new stage's actual execution is not presented as a fresh full-chain run.

## Handoff and limits

RC8 remains the named packaged playtest until the next combined package includes
this stage. The new development ROM retains all RC8 text, artwork, and accepted
fixes. RC8 saves are expected compatible in both directions without migration;
those particular loading directions are not independently tested. Expansion Pak,
128-KiB FlashRAM, and RTC requirements remain unchanged.

No debug menu is enabled, town generated, item spawned, or save accessed for
verification. No new native drawing or hardware session is claimed. Preserve
human acceptance of ordinary saving/reloading and all reported fixes. The three
zero-filled reserved-name/item entries in the old ledger remain the already
classified padding, not new untranslated text or a reason to maintain the counter.

Include this completed stage in the next combined patch package, then continue
remaining content/release work. Do not rerun the completed scene-menu, household,
or diagnostic batch to refresh evidence. Public approval and distribution review
remain separate; V2 stays deferred.
