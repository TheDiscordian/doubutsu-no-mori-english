# Completion queue

This is the durable queue for the complete translation project. A working
milestone does not complete the project. Continue through available work without
requiring the user to advance an automated procedure. Commit verified changes
and update the evidence links as each task progresses.

Status meanings: **active** = being implemented or audited; **pending** = required
work remains; **external validation** = cannot be claimed without the specified
hardware or independent permission/evidence. A task becomes complete only when
its acceptance checks pass, not when a candidate or specification exists.

Immediate R05 tasks: validate the ordinary post-office hand-back/error flow and
finish remaining readers/metadata before enabling generation. The Pelly patch
passes 48 native actor receipt cases, eight hand-back initializer cases, sixteen
refusal selectors, and ten index boundaries. Failed letters return to their
original pockets without reporting success. The fixtures run actual action
initializers but do not establish normal animation or subsequent player input.
See [receipt evidence](../specs/PELLY_RECEIPT.md).
Keep generation disabled.

The first-job and ordinary NPC letter-show handlers in overlays `00814FA0` and
`00815B70` pass isolated native caller-level validation. Their three
reverse-conversion paths preserve complete ordinary/snapshot letters and reach
board read mode one. Instruction, BSS-lifetime, relocation, and execution
contracts are recorded in [NPC letter-show design](../specs/NPC_MAIL_SHOW.md).
Read-only letter headers now resolve complete English villager names using the
existing saved identity. Host tests cover all 216 villagers and fallbacks;
eight full native windows and ten ordinary-header cases pass. No saved
name capacity, source letter, font metric, or reference line break is changed.
The NPC caller harness passes all nine windows. It uses both original overlays,
independently checks their relocated file/BSS image, and keeps the temporary
letter allocated through close. Nine window cases cover all three caller
branches with ordinary letters and both snapshot kinds. The complete run and
checkpoint restoration pass. Normal actor interaction remains distinct from
these isolated calls. Next R05 work covers ordinary post-office hand-back/error
progression and the remaining inline metadata/excerpt, travel, and editor paths;
the direct reverse-conversion callers are no longer an untested-reader item.
The isolated [native FlashRAM persistence test](../specs/FLASH_MAIL.md) passes
all 192 saved mail slots in both native save banks. A separate fresh process
receives only the exported cartridge save and passes all 384 complete-record
checks and eight complete English reconstructions. This is not normal save-menu
or post-load gameplay validation; generation remains disabled.

Native Controller Pak writing and fresh-process reading pass for the `1200`-byte
passport and `6700`-byte stored-letter note: all 177 complete letter records,
both file checksums, complete player/NPC imports, and six English reconstructions
in each process. See [Pak persistence contract](../specs/PAK_MAIL.md). Ordinary
travel and storage-menu flows remain separate requirements.

The [native letter-menu selector](../specs/MAIL_MENU.md) passes 120 isolated
status/gift/marker/context cases and retains every complete source letter.
All 44 static tag-label definitions pass native length checks, closing that
specific shared-helper provenance item. Received letters select Read; drafts
select Rewrite. Shared close-helper inspection establishes the read path's
motion-to-end transition without entering edit acceptance. Remaining editor work
includes parent-menu interaction, complete pointer ownership, generation status
assignments, and normal custom editing. These checks do not enable generation
or establish full menu gameplay.

The [whole-letter generation transaction](../specs/MAIL_GENERATION.md) now passes
all 6,398 supported host reference assembly cases and 53 native generation cases,
plus 42 native field-capture cases. It preserves complete saved metadata and
rejects missing fields, overflow, and unavailable resources before publication.
This code is an isolated heap-loaded probe, not an installed gameplay overlay.
Next generation work connects approved field/template sources and complete
native creator boundaries, with bounded loading and failure propagation through
delivery. Keep ordinary gameplay generation disabled while those checks and
remaining reader/editor/normal-interaction requirements are incomplete.
The [NPC creator binding contract](../specs/NPC_MAIL_GENERATION.md) verifies
complete native/reference functions and selection tables. All available reply
parts have supplied source slots across 24 group/gift contexts and 36 classic
selections. One composite footer remains unavailable. Original creation failure
is not propagated to submission. The guarded failure-return gate passes 41
isolated native cases, including twenty actual queue receipts, rejected creation,
both counter components, every queue slot, invalid recipients, and full home
mailboxes. Its creator is a controlled fixture, and the production hook remains
uninstalled. Next steps connect complete word/name capture and runtime ownership
to the real creator, then test creator failures and the pending-reply loop.
The [complete word source resource](../specs/NPC_MAIL_WORDS.md) verifies all 352
phrases against the actual source banks and records full source/reference IDs.
All 83 phrases beyond ten bytes are retained within sixteen bytes. Connect this
resource before native truncation. The [saved-name alias resource](../specs/NPC_MAIL_NAMES.md)
supplies all 216 full names from 394 exact original/short-English keys, without
guessing unknown identities. The scoped source/capture implementation passes
complete host coverage and cross-compiles as a bounded relocatable image.
All 48 original-versus-captured native creator comparisons pass, including full
English generation with unchanged RNG state, gifts, stationery, native fields,
and saved data. Cartridge loading, whole-creator ownership, and publication
through the tested failure gate remain.
The resident capture adapters leave 2,912 linked bytes available inside the
unchanged 32 KiB reservation. Allocation/error ownership tests,
four-MiB town arrival, and all eight complete native letter windows pass.

## Main translation and runtime

| ID | Task | Status | Acceptance/evidence |
| --- | --- | --- | --- |
| R01 | English runtime substitutions, including town/date/time formats | active | Town, seven message date/time fields, and AM/PM pass; other UI callers remain |
| R02 | Choice strings beyond ten bytes | active | All 460 choices import; twenty-byte capacity, thirteen long DMA loads, four rows, insertion, and cancellation pass targeted MIPS tests; full review and actor-specific runtime paths remain |
| R03 | General strings and UI caller capacities | active | Thirty-four direct calls inventoried; ten-byte default catchphrase display passes all 216 default loads and main insertion with unchanged saved bytes; gyroid owner-message pixel wrapping and native insertion pass with unchanged saved/editor limits; longer gyroid default/custom storage, ambiguous borrowed phrases, shared choices, mail, and shop destinations remain |
| R04 | NPC and item names | active | 178 six-byte villager names and all native loads pass; eight-byte API covers all 216 villagers and 64 special-actor rows; main insertion, two nameplate consumers, eight rendered quads, and guards pass native tests; combined train-to-town regression passes; 107 item reference IDs occupy 231 ten-byte slots; all 4,547 item-ID cases have passing runs, with one initial stop retained; sixteen-byte main item fields, one item-ID wrapper, and a confirmed clothing alias pass native tests; other destinations and identities remain |
| R05 | Mail, headers, footers, and NPC mail components | active | Verified 164-byte record and 10/96/16 fields; full-letter codec, formatter, immutable catalog, and restoration pass host/native tests; full snapshot reader retains all wording across pages and matches 6,398 host reference probes; actual window tests cover long classic/composite letters, complete glyph vertices, page input, and unchanged source/preferences; English ordinary scoring and distinct quest word tables pass native tests; complete-record send decoding and post-office failure retention pass 32 N64 cases, including local/visitor replies, friendship, quests, gifts, counters, and unchanged rejected records; experimental split marker is not release-approved; 59 reference parts need glyph support; complete metadata/other-reader handling, semantic identities, generation, lossless editing, normal delivery, and save/reload remain |
| R06 | Remaining GameCube controls | active | AM/PM, capitalization, protected pacing, complete choice-close handling, and pixel-space rendering pass targeted MIPS tests; random-range and wider flow coverage remain |
| R07 | Remaining message matching | active | Hash-bound identities, complete sequences, and 41 unanimous complete-native-record aliases implemented; native loads pass; 79 alias conflicts and further matching remain |
| R08 | Review all candidate dialogue | pending | Meaning, placeholders, branches, actor arguments, and delivery reviewed; candidates are not automatically approved |
| R09 | Embedded UI, calendar, credits, and other uncovered text | pending | Inventory extends beyond the current 29 banks and keyboard UI |
| R10 | Punctuation and layout polish | pending | Preserve GameCube line/page/timing intent; review necessary N64 departures individually |
| R11 | Reported font-atlas edge defect | pending, paused by user direction | Do not resume the discarded font comparison investigation without renewed direction |

## Stability and compatibility

| ID | Task | Status | Acceptance/evidence |
| --- | --- | --- | --- |
| V01 | Repeatable build and regression suite | active | Verified inputs, deterministic outputs, all tests passing, clean tracked worktree |
| V02 | New-town creation through normal gameplay | active | Name/town entry, arrival, house purchase, both explanation choices, English work offer, uniform equipment, and planting completion/acknowledgement pass; meeting villagers, later jobs, and normal save remain |
| V03 | Save/reload and long names | active | Native two-bank FlashRAM writing and fresh-process reading pass all 192 synthetic stored-letter slots, complete records, and English reconstruction; normal save-menu/post-load gameplay, custom editing, longer names, and RTC remain |
| V04 | Keyboard callers beyond player/town names | pending | Catchphrases, apology, song request, mail, and board |
| V05 | Dialogues and menus across progression | pending | All control families, four-choice menus, inventory, shops, item displays |
| V06 | Travel and Controller Pak | active | Isolated native passport/stored-letter writes and fresh-process reads pass all 177 complete letters, file checksums, complete player/NPC imports, and English reconstruction; ordinary travel/storage UI, error paths, different towns, and saved names remain |
| V07 | Dates, RTC, seasons, events, and credits | pending | Event coverage and boundary dates with controlled test saves |
| V08 | Legacy glitch/crash audit | pending | Reproduce reports where possible; distinguish damaged data from mere command differences |
| V09 | Four-MiB memory and resource budgets | active | 32 KiB module reservation and actual malloc arena start pass boot and town-arrival guards; linked mail calls pass separate stack/buffer guards; broader heap/graphics tests remain |
| V10 | Original hardware matrix | external validation | Real console/flash cartridge/Controller Pak evidence; emulator evidence is insufficient |

## Image and keyboard stretch goals

Work on these after the main porting effort, while inventory work may identify
the required resources earlier.

| ID | Task | Status | Acceptance/evidence |
| --- | --- | --- | --- |
| S01 | Identify every Japanese text-bearing image | pending | Asset IDs, dimensions, texture formats, palette use, and in-game location |
| S02 | Match English GameCube images, including title screen | pending | Extract from supplied disc; prove matching asset identity and intended use |
| S03 | Replace images with matching GameCube artwork | pending | Preserve identical artwork where formats allow; document any necessary conversion; check N64 memory/graphics budgets |
| S04 | GameCube-style English keyboard | pending, specified | Real 10×4 grid, case/symbol pages, N64 controller mapping, all editor callers and save limits tested |

## Release

| ID | Task | Status | Acceptance/evidence |
| --- | --- | --- | --- |
| P01 | Complete coverage report | active | Token-aware inventory covers 29 banks and distinguishes candidate presence from review; embedded UI/assets, wider resources, and complete review remain |
| P02 | Provenance and redistribution review | pending | Nintendo inputs remain local; legacy permissions assessed; patch-only package |
| P03 | Reproducible release artifacts and instructions | pending | Source-hash rejection, verified patch application, checksums, install and compatibility notes |
| P04 | Final acceptance | pending | Main work, stretch goals, regression matrix, and required external validation complete |

Current observations and counts live in `PROGRESS.md`. Implementation contracts
live under `specs/`. Dated results and exact build hashes live in `WORK_LOG.md`.
Generated detailed inventories, captures, test saves, and binaries stay ignored
under `build/` and `local/`; original tools and documentation are versioned.
