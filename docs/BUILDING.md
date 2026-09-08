# Building and reproducing tests

Run commands from the repository root. Python 3 uses only its standard library.
Input preparation additionally uses `7z`; source bootstrap uses Git. Inventory
the local machine before installing tools. Disassembly uses the existing pinned
Docker toolchain listed in [sources](SOURCES.md); ordinary builds do not need it.

## Inputs

`tools/prepare_inputs.py` accepts `--n64-archive`, `--legacy-zip`, and
`--gamecube-archive`. It extracts only the expected members, verifies the retail
ROM and legacy patch, and refuses to replace differing existing inputs.

Expected local files:

- `local/rom/Doubutsu no Mori (Japan).z64`
- `local/legacy/AFProjectDistro/NAFE-WIP-2_12_2010.ups`
- `local/gamecube/Animal Crossing (USA, Canada).ciso`

`python3 tools/check_references.py --bootstrap` initialises the pinned N64
submodule and fetches the pinned GameCube reference checkout if missing.
`make references` verifies both pins and tracked source cleanliness.

## Outputs

`make pilot` runs the tests, validates inputs, extracts inventories and GameCube
reference text, generates candidate edits, and builds the English-first keyboard
and sixteen-byte choice runtime pilot. It writes the ROM, UPS patch, checksummed build manifest, and diagnostic
atlas files under `build/pilot/`. Candidate and rejection reports live under
`build/candidates/`. Nothing in those directories is committed.

`make opening` builds only the four original dialogue drafts plus the renderer
and English-first keyboard. `make halfwidth` builds only the renderer experiment.

To rebuild a particular candidate set without regenerating references:

```sh
python3 tools/build.py \
  --rom 'local/rom/Doubutsu no Mori (Japan).z64' \
  --translations build/candidates/translations.json \
  --english-keyboard --english-runtime --output build/pilot
```

The supported input ROM hash, relocation addresses, and command policies are in
[the framework specification](../specs/TEXT_FRAMEWORK.md). Wrong inputs, stale
edits, unknown commands, and unsafe expansion fail the build.

Exact development labels are classified separately from missing dialogue.
Candidate generation retains valid English reference labels and translates
remaining recognised labels without allocating continuation pages. Existing
sequence approvals remain protected even when their runtime is disabled.
Audit a generated resident candidate set with:

```sh
python3 tools/audit_placeholders.py \
  --rom 'local/rom/Doubutsu no Mori (Japan).z64' \
  --translations build/placeholder-candidates/translations.json \
  --resident-runtime --output build/placeholder-audit
```

Omit `--resident-runtime` for a basic candidate set. The report retains source
hashes, candidate validity, sequence allocations, and native script references;
it does not establish unreachable code or gameplay completion. See
[label contract](../specs/PLACEHOLDER_TEXT.md).

## Silent emulator tests

Complete sale/Redd publication uses `tools/build_event_actor.py` and the builder's
`--english-event-letters <compiled-actor-directory>` option. It requires complete
item names, leaflet dates, and the full snapshot reader. The pending-selector
flag extends saved semantics; this remains an experimental build. The
[event work record](checkpoints/EVENT_LEAFLET_PUBLICATION.md) contains the complete
integrated build command, source-bound scenario, and actual validation limits.

Complete renewal mailbox publication uses `tools/build_renewal_actor.py` and
the ROM builder's `--english-renewal-letters <compiled-actor-directory>` option.
It requires `--english-leaflet-dates`, `--english-mail-snapshots`, the complete
leaflet creator, and their full resource/module dependencies. The
[renewal specification](../specs/RENEWAL_LETTERS.md) and
[work record](checkpoints/RENEWAL_LETTERS.md) record installation, reproduction,
the bounded silent test, and its gameplay/hardware limits.

Reviewed long dialogue can span linked native records without increasing the
1,024-byte buffer. Runtime-dependent groups, including the late-night resident
introduction and its AM/PM field, are included only when candidate generation
and building both use `--runtime-module`. The group installs all members
together. See [sequence contracts](../specs/REFERENCE_SEQUENCES.md).

The isolated late-introduction check uses the actual built ROM and its bound
module report:

```sh
python3 tools/sequence_test_scenario.py \
  --rom build/late-intro-pilot/animal-forest-halfwidth.z64 \
  --module build/late-intro-pilot/runtime-module.json \
  --sequence resident_late_night_introduction \
  --output build/late-intro-scenario.json
```

Run the resulting scenario through the silent emulator runner described below.
This checks cartridge loading and native continuation, not a rendered resident
conversation. Animation-selection testing likewise records its deliberate
initializer boundary; see [animation evidence](../specs/RESIDENT_ANIMATIONS.md).

The experimental resident-module build uses the existing pinned Docker compiler:

```sh
python3 tools/build_runtime_module.py --rom 'local/rom/Doubutsu no Mori (Japan).z64'
python3 tools/build.py --rom 'local/rom/Doubutsu no Mori (Japan).z64' \
  --translations build/candidates/translations.json --english-keyboard \
  --english-runtime --runtime-module build/runtime-module --output build/module-pilot
```

Module source changes, including nested mail files, require rebuilding its
artifacts. The 32 KiB reservation contains at most 24 KiB of linked code/data/BSS
and a separate 8 KiB native-test area. The ordinary non-module pilot does not
enable the module. See [module design](../specs/RUNTIME_MODULE.md).

Generate module-aware candidates with `tools/reference_candidates.py`, passing
`--english-runtime --runtime-module build/runtime-module --output build/module-candidates`
and the verified `--rom`. Use that directory's `translations.json` in the module
build to include the implemented GameCube commands and bounded calendar fields.
The build verifies the entire module capability before accepting those edits.
Pass `--english-dialogue-dates` to both the candidate generator and ROM builder
to include the native moon-viewing drafts and English resident-date and birthday
preparation. All 33 native birthday-request conversations require this feature,
including references that already had English wording. The builder derives that
dependency from the original cartridge, so omitted metadata cannot disable it.
Both commands require `--runtime-module`. Without that option, dependent drafts
stay out of the candidate file and appear in `drafts-withheld.json`; basic builds
remain supported. The ROM builder independently verifies the complete installed
overlay and relocation files before accepting dependent edits. See
[date preparation](../specs/DIALOGUE_DATES.md).

Shared-string groups use the same explicit option in candidate generation and
ROM construction:

- `--english-fortunes`: all 128 Katrina fragments and their sixteen-byte native
  caller; requires the resident module.
- `--english-resetti-replies`: all 32 rude replies and their native matching
  lengths; does not require a resident module.
- `--english-shop-units`: all 120 native quantity counters, including explicit
  empty counters and the sapling identity correction; does not require a module.
- `--english-resident-words`: 136 complete drinks, colours, places, reading
  material, shop types, and category labels; requires the resident module and
  installs the scoped native caller changes. It composes with dialogue dates.
- `--english-shared-npc-words`: all 352 complete reply words, including 160 shared
  with resident dialogue; requires resident words and the module. ROM building
  also requires `--npc-mail-generation` with its full dependencies. Bank changes
  are deferred until both complete consumers are installed and verified.
- `--english-credits`: all 110 native credit rows, with complete identity-matched
  names/roles and an owned twenty-five-byte loader/drawer buffer. The native
  structure slot, page sequence, and timing remain; no resident module is needed.

Each group requires its complete source-bound values and caller changes. These
options share the relocated general-string data bank and do not enlarge other
callers. See [general strings](../specs/GENERAL_STRINGS.md) and
[resident words](../specs/RESIDENT_WORDS.md), and
[shared NPC words](../specs/SHARED_NPC_WORDS.md). Basic non-module generation omits
the module-dependent options.

`tools/credits_test_scenario.py --rom <built-ROM> --module <build.json>
--translations <candidate-json> --output <ignored-scenario.json>` generates the
bounded silent credit test. It requires a resident-module build for test-only
scratch space, not for the production credit patch. The native batch loads all
110 rows, draws all sixteen pages and fade boundaries into owned graphics
memory, and restores its isolated checkpoint. It does not play music or use a
user save. See [native credits](../specs/NATIVE_CREDITS.md).

Changing the module source also requires rebuilding the module-bound NPC creator
and generation probe using `tools/build_npc_mail_capture.py` and
`tools/build_mail_generation.py`. Each report binds its imports to the exact
compiled module; old reports must not be reused after symbol addresses change.

The separate dialogue glyph feature uses source pixels from the supplied English
disc. Generate `build/extended-glyphs/` with `tools/extended_glyphs.py --output
build/extended-glyphs`, then build its cartridge image with
`tools/build_extended_font_cartridge.py --output build/extended-font-cartridge`.
Pass `--extended-font build/extended-font-cartridge` to both candidate generation
and the ROM builder, alongside `--english-runtime --runtime-module
build/runtime-module`. Unsupported builds withhold the dependent references.
The builder verifies the complete resource and startup integration before
publishing text that uses it. The allocation stays in the system heap across
scene changes; the native atlas, saved formats, and test reservation stay intact.
This capability is main-dialogue-only, not editor or mail support. See
[glyph contracts and validation](../specs/EXTENDED_GLYPHS.md).

`tools/extended_font_cartridge_scenario.py --rom <built-ROM> --module
<configured-runtime-module.json> --translations <candidate-file> --output
<ignored-scenario.json>` generates the combined cartridge draw/reveal/message
batch. It uses startup-loaded font code and pixels, with no debugger upload.
Its ordinary native calls still require an isolated checkpoint and restoration.

The resident variant also enables twenty-character choices. Generate its native
four-row and DMA test with `tools/choice_test_scenario.py --rom <built-ROM>
--output <ignored-scenario.json>`, then pass that scenario to the test runner.
The generated fixture contains local game text and stays under `build/`.
The silent runner accepts an explicit wall-clock limit of at most 1,200 seconds
for combined native batches; its default remains forty seconds. Use a large
batch's measured duration when setting `--seconds`. A timeout is an incomplete
test, not evidence of a game crash. NPC mail-generation fixtures require a
populated matching-ROM town checkpoint or execution after the train-to-town
scenario; a fresh title-screen fixture does not supply that precondition.

The separate sixteen-byte item resource is generated by `tools/extended_items.py`
with the verified `--rom` and an explicit `--output <resource-directory>`.
Pass that directory, containing both `names.bin` and `names.json`, to the ROM
builder's `--extended-items` option. The resource alone does not widen native
callers; only separately verified resident hooks use its sixteen-byte names.

`tools/display_names.py --rom <native-ROM>` generates the independent eight-byte
villager/special-character resource in `build/display-names/`. Pass that directory
to `tools/build.py --display-names`; main dialogue and nameplates use the complete
names, while saved names and unrelated callers retain their native limits.

`tools/catchphrases.py --rom <native-ROM>` generates the independent ten-byte
default catchphrase resource in `build/catchphrases/`. Pass that directory to
`tools/build.py --catchphrases`. This translates recognised default saved phrases
at display time without expanding four-byte saved fields or custom editing.
It verifies the actual GameCube default table and confirmed villager identities.
All three resource options may be supplied together to a resident-module build.
See [catchphrase design](../specs/CATCHPHRASES.md) for ambiguous borrowed phrases
and the remaining editor/mail/save work.

`tools/mail_catalog.py --rom <native-ROM>` builds the source-verified catalog in
`build/mail-catalog/`. Pass that directory to `tools/build.py --mail-catalog`
after rebuilding the resident module. The registry in
`translations/mail_catalogs.json` freezes complete resource hashes; changed
content cannot retain an assigned catalog ID. The proposal option produces
local review output only and does not authorize installation. The current
catalog retains all eight reference bank indices, with 59 unavailable glyph rows
explicitly rejected. Generation, viewing, editing, and saving remain separate
integration work; this resource is not an approval of semantic matches.

`tools/mail_catalog_test_scenario.py --rom <built-ROM> --output <ignored-json>`
generates complete snapshot-to-letter tests using actual cartridge DMA. The
caller-owned workspace is separate from both output and the saved snapshot.
The scenario preserves guards, checks full output, and restores its checkpoint.

`--english-mail-layout` optionally enables measured-width body lines and footer
alignment for native read mode only. It requires a rebuilt resident module and
retains the native editor, saved field sizes, header, and explicit newlines.
It does not yet decode generated snapshots. See [reader design](../specs/MAIL_VIEW.md).
`tools/mail_view_test_scenario.py --rom <built-ROM> --output <ignored-json>` checks
the compiled read hooks, actual font vertices, graphics bounds, and editor-mode
argument forwarding. `tools/mail_open_test_scenario.py` generates a separate
synthetic letter-open probe for a matching-ROM town checkpoint. It uses the
actual submenu/board loader, verifies resident hook execution, exercises the
three close buttons, checks unchanged letter/preferences, and restores the
checkpoint. This is not ordinary mail delivery or a game-save test.

`--english-mail-snapshots` additionally enables the experimental complete-letter
cache and reader, requiring both `--english-mail-layout` and `--mail-catalog`.
It does not enable native snapshot generation or establish save compatibility.
`tools/mail_reader_test_scenario.py --rom <built-ROM> --output <ignored-json>`
generates long classic/composite snapshot-window probes for an identical-ROM
town checkpoint. All pages, actual glyph vertices, graphics bounds, and unchanged
source/preferences are checked. See [full reader](../specs/MAIL_READER.md).

`tools/build_mail_grading.py --rom <native-ROM> --output build/mail-grading`
builds the on-demand English scoring overlay. It extracts verified English
prefix tables locally, builds the provided Fado relocation tool without a
system installation, and uses the pinned Docker MIPS compiler. Rebuild the
resident module, then pass `--english-mail-grading build/mail-grading` to the
ROM builder. This optional patch changes ordinary reply scoring and the quest
word tables. Combining it with `--english-mail-snapshots` also installs complete
record decoding before NPC sends and preserves post-office letters on failure.
These options alone leave native snapshot generation disabled.
See [grading design](../specs/MAIL_GRADING.md).

`tools/build_npc_mail_capture.py --module <module.json> --output <creator-directory>`
builds the complete NPC reply creator and immutable word/name sources against
that exact resident module. Pass `--npc-mail-generation <creator-directory>` to
the ROM builder together with English runtime, full snapshot reader/catalog,
and English grading. This explicitly enables experimental cartridge-loaded NPC
generation, the eight scoped capture calls, and submission failure handling.
It does not establish complete gameplay, semantic review, or hardware acceptance.

The complete fortune-slip resources use `tools/build_fortune_slips.py --rom
<native-ROM> --output build/fortune-slip-resources`. This retains catalogue two
and adds independently registered catalogue three. Rebuild the resident module
and the module-bound NPC creator, then pass that resource directory as
`--mail-catalog build/fortune-slip-resources` to the full ROM build. The native
Miko hand-off is not installed by these options.

`tools/build_mail_generation.py --fortune-slip --output build/fortune-slip-probe`
compiles the complete fortune transaction for isolated native tests.
`tools/fortune_slip_test_scenario.py --rom <built-ROM> --module
<ROM-directory>/runtime-module.json --output <ignored-json>` prepares forty
complete creations, failure cases, and older-catalogue reads. The ordinary
silent emulator runner executes the scenario with a checkpoint and owned heap
memory. See [fortune-slip contracts](../specs/FORTUNE_SLIP_LETTERS.md).

`tools/build_fortune_actor.py --rom <native-ROM> --output build/fortune-actor`
builds the complete native Miko adapter against the current module and full
fortune phrase resource. Add `--english-fortune-slips build/fortune-actor` to the
full ROM build to install its two callbacks, extended actor size, and relocated
DMA pair. It requires the complete snapshot reader and immutable catalogue three.
The actor stays within its existing native pool; it adds no resident reservation
or saved field. This remains experimental pending cancellation/removal recovery
and normal gameplay acceptance.

`tools/fortune_actor_scenario.py --rom <built-ROM> --build-report
<ROM-directory>/build.json --output <ignored-json>` prepares the silent native
hand-off batch. It tests 24 complete outcome/template/capitalization cases,
all ten pocket positions, native relocation and metadata, complete reader
restoration, failed-resource retries, duplicate prevention, and heap accounting.
Run with the existing silent emulator runner and isolated checkpoint/save files.

For configured-generation ROMs, native test tools require the ROM output's
`runtime-module.json`, not the unconfigured compiler report. The build report
binds the approved creator blob, complete source/import checks, and header words.
`tools/npc_mail_loader_test_scenario.py --rom <built-ROM> --module
<ROM-directory>/runtime-module.json --output <ignored-json>` tests actual
cartridge loading, complete letters, failure retention, and heap cleanup against
a matching-ROM town checkpoint. See [loader contract](../specs/NPC_MAIL_LOADER.md).

`tools/mail_grade_test_scenario.py --rom <built-ROM> --output <ignored-json>`
generates ordinary reply, complete-body, and native quest calls with memory
guards. It accepts `--module <module.json>` and `--overlay <overlay.json>` for
non-default builds. Run it in a fresh silent emulator instance; it establishes
and restores its own checkpoint. `tools/audit_mail_grading.py --rom <native-ROM>`
reproduces the direct-call and aligned-pointer inventory independently.

`tools/mail_npc_test_scenario.py --rom <built-ROM> --output <ignored-json>`
generates full native NPC/post-office send tests for a matching-ROM town
checkpoint. It accepts the matching `--module` and `--overlay` manifests.
Tests set controlled in-memory NPC/player/quest state and temporarily clear the
first-job event; the complete checkpoint must be restored. They do not complete
introductory jobs or validate FlashRAM saves. See [send integration](../specs/MAIL_NPC_SEND.md).

`tools/audit_mail_storage.py --rom <native-ROM>` records selected status/storage
functions and Pelly's outstanding failure path. `tools/mail_storage_test_scenario.py
--rom <built-ROM> --output <ignored-json>` generates isolated metadata, NPC-copy,
queue, leaflet, and all-home-mailbox probes for a matching-ROM town checkpoint.
These tests restore all touched storage and the complete checkpoint; they do
not execute normal inventory interactions or actual saving.

The corresponding native-call generators are `tools/display_fields_test_scenario.py`
and `tools/catchphrase_test_scenario.py`. Both require the exact built ROM and
matching module/resource manifests. Generated fixtures remain local under
`build/`. Native calls run only at the verified graph-thread boundary and must
restore the complete checkpoint; see [test-call contract](../specs/NATIVE_TEST_CALLS.md).

`tools/mail_runtime_test_scenario.py --rom <built-ROM> --suite codec
--output <ignored-scenario.json>` generates direct resident snapshot tests.
The `format` suite covers complete assembly, every opcode, rejection, and guards;
`reference` uses 46 selected cases from the verified English disc extraction.
All three require the matching module manifest (`--module` when not using the
default directory). These tests do not enable gameplay mail generation or viewing.

After town entry, the full runtime-choice scenario uses a bounded
`advance_to_message` action for arrival record `07DD`. It observes each live
message and stops before pressing past arrival. Only the first choice in four
explicitly named train messages is accepted; unknown prompts, a different
cursor, and an exhausted press limit fail. It uses ordinary button input and
does not change text pacing or gameplay state directly.
`tools/validate_runtime_smoke.py <test-directory>`
independently requires arrival and all other recorded acceptance checks;
a runner exit code alone is not a full regression pass.

`tools/text_coverage.py --rom <native-ROM> --translations <candidates.json>
--output build/coverage` audits final candidate presence across all 29 native
banks. It distinguishes static text from commands and dynamic-only records,
without treating candidate presence as review or establishing reachability.
See [coverage classification](../specs/TEXT_COVERAGE.md).

Reviewed reference identities live in `translations/reference_matches.json`.
The candidate generator's `--matches` option selects another explicit record
file when needed. Identity overrides do not bypass runtime or control checks.
The default original edits comprise `translations/opening.json`,
`translations/n64-exercise.json`, `translations/n64-intro-jobs.json`,
`translations/n64-shop-menus.json`, `translations/n64-advice-travel.json`,
`translations/n64-festivals.json`, and `translations/n64-seasonal-conversations.json`,
subject to declared runtime requirements.
Repeat `--drafts <file>` to select a different
explicit set; duplicate IDs fail instead of silently overwriting each other.

`tools/emulator_smoke.py` requires ares, Xvfb, FFmpeg, X11, and XTest. Pass an
explicit `--xvfb` path if the existing binary is outside PATH. Every test requires
a fresh `--output` directory, copies the ROM, disables audio, isolates saves,
and enforces a bounded process lifetime. It never replaces a user save. An
explicit `--seed-save <test-directory>` copies cartridge saves into a fresh run;
the source directory stays unchanged. `--seed-state <test-directory>` resumes
an emulator checkpoint only when its recorded ROM matches the tested ROM.
Checkpoints are not FlashRAM save/reload validation.

`tools/flash_mail_test_scenario.py --rom <built-ROM> --output <ignored-json>`
generates the isolated native FlashRAM writer test. Run its scenario on a
matching-ROM town checkpoint using `--allow-test-flash-write`; the harness also
requires a completely blank isolated chip before writing. It exports the
native-read cartridge contents and manifest to the run's `exported-save/`.
Generate the read scenario with the same tool plus
`--export <writer-output>/exported-save/manifest.json`, then run a separate
emulator with `--seed-save <writer-output>/exported-save`, without `--seed-state`
or the write opt-in. Both runs need fresh output directories. This validates
the native two-bank writer and fresh-process reader with synthetic stored
letters, not normal save-menu gameplay. See [scope and guards](../specs/FLASH_MAIL.md).

`tools/gyroid_message_test_scenario.py --rom <built-ROM> --output <ignored-json>`
generates native entry/insertion tests for measured home-gyroid message wrapping.
It verifies the installed hook, uses the actual native text insertion routine,
checks full source/destination and stack guards, and restores its checkpoint.
Its `--module` option selects the matching module manifest when not using
`build/runtime-module/module.json`. This tests the existing saved-message
capacity; it does not install the longer English default or a wider editor.

Use `--scenario tests/english-keyboard-scenario.json --seconds 410` for the
English-entry sequence. Generated `results.json` records ROM hash, message
snapshots, memory assertions, and captures. The controller test mapping is in
[validation](VALIDATION.md). Emulator process survival alone is not a pass.

The long-choice and town-arrival sequence uses
`--scenario tests/runtime-choice-scenario.json --seconds 500`. Afterwards,
`python3 tools/validate_runtime_smoke.py <test-directory>` verifies the recorded
long rows, selected answer, name limits, town substitution, and arrival message.
The final emulator checkpoint supports continued exploration with the same ROM.

Use `tests/emulator-state-roundtrip-scenario.json` to test the checkpoint
mechanism itself. It deliberately writes a marker to unused-at-boot choice RAM,
saves state, changes the marker, reloads, and verifies restoration. These test
markers are never translation edits or release content. Successful runs close
ares normally and record the hashes of the flushed cartridge files.

`make test` runs all tests. Retail-input integration tests are skipped
when the source ROM is absent; synthetic format and safety tests still run.

`python3 tools/check_keyboard_assembly.py` separately verifies the embedded
name-cursor patch against its assembly source using the pinned Docker toolchain.
`python3 tools/check_runtime_assembly.py` verifies the choice-width routine.
`python3 tools/audit_choice_callers.py --rom '<retail-ROM-path>'` repeats the
complete DMA caller and reclaimed-code reference scan.
`tools/audit_string_callers.py --rom '<retail-ROM-path>'` records the direct
general-string callers and their immediate argument hints for capacity review.
`tools/audit_mail.py --rom '<retail-ROM-path>'` repeats the instruction-guarded
mail-layout and reference inventory using local GameCube text metadata. Its size
counts are evidence, not approval to expand saved mail fields.
`tools/audit_mail_templates.py --rom '<retail-ROM-path>'` checks the storage
budget of complete generated-letter snapshots using actual extracted English
banks and guarded native reply-group selection. `tools/mail_test_scenario.py
--rom '<built-ROM-path>'` generates the isolated native command/copy regression.
The snapshot prototype and its uninstalled C codec are specified in
`specs/MAIL_SNAPSHOTS.md`; the playable build does not use encoded mail yet.

For module tests, append `--post-scenario tests/runtime-module-memory-scenario.json`
to verify heap bounds and guards after any scenario. The dedicated
`tests/runtime-date-scenario.json` invokes the real MIPS message insertion
functions using bounded debugger scratch RAM. It requires a checkpoint and
restores the complete emulator state afterwards; it does not alter a release ROM
or establish game-save compatibility. The runner rejects an unrestored call test.
The same checkpoint discipline applies to `runtime-ampm-scenario.json`,
`runtime-capital-scenario.json`, and `runtime-pacing-scenario.json` under `tests/`.
