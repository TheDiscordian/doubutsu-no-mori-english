# Work record

## 2026-09-06: reference framework and English-first keyboard

- Extended reference import across eleven message/string/mail-component banks.
  The generated pilot contains 8,902 edits: 8,301 dialogue reference candidates,
  221 choice candidates, 376 other candidates, and four original drafts.
- Added auditable GameCube article-suppression and N64 actor-demo adaptations.
  Added the dialogue-only existing-text-field policy. Branches, waits, RNG, and
  embedded-mail operations remain strict. No automatic reflow was introduced.
- Added fixed-width GameCube name extraction using pinned REL symbols. Withheld
  legacy item candidates whose offset notes do not match the supplied image.
- Added input preparation, reference-pin checks, archive safety tests, original
  bank integration tests, and rejection of an empty first cumulative-table entry.
- Paused the font-atlas investigation following the user's explicit instruction.
  The diagnostic probe is retained as work history, is not a build dependency,
  and does not establish a fix. Default renderer output retains zero left padding.
- Mapped the N64 keyboard and name-entry overlays. Patched English mode as the
  default, translated five prompts and the destination suffix, and generated ten
  English texture labels from unscaled local retail glyphs. Preserved overlay
  sizes, pointer relocation files, callbacks, and 6/6/4/10/10 field limits.
- Added simultaneous controller inputs, analogue-stick bindings, and keyboard
  memory snapshots to the isolated silent test runner. A first English-keyboard
  run ended externally with exit 143 before reaching the editor; this is not a
  passing test or evidence of a game crash. A bounded transient user service is
  used for the rerun so the test is independent of the invoking shell lifetime.
- `make pilot` passes 31 tests and regenerates the candidate build. ROM SHA-256:
  `c851db851fc4426353d3cad2ea68c122d0ea71b6d40c0c09523d92c9ccf1330e`.
  UPS SHA-256:
  `407f7772c434203994d4fbb1cdcbf23393c4130662a42b1eb4bcee00823e5db1`.
- Documented the GameCube 10×4 keyboard reference and the separate grid port.
  The grid is not implemented, and original hardware remains untested.

### Keyboard input and cursor validation

- `build/smoke-english-keyboard-03` passed 62 recorded steps in silent ares 148
  with four-MiB RAM. Memory assertions verified mode 3 on opening, `CCC` entry,
  `CCc` case conversion, one-character deletion to `CC`, left/right cursor
  movement, six-character enforcement after excess insertion attempts, and mode
  transitions 3→4→0→1→2→3. Name confirmation returned to Rover messages
  `2ACA` and `2AD6`.
- Replaced the name cursor's fixed-cell position calculation with the existing
  proportional prefix-width routine. Assembled and independently checked the
  96-byte MIPS patch; removed only its two obsolete constant relocations.
  `build/smoke-keyboard-cursor-01` passed the same 62-step regression, and entry
  captures confirmed the caret follows the text. No font textures changed.
- Added verification of all ten RDP texture descriptors and strict rejection of
  unsupported label characters. Added an inventory of sixteen embedded/graphical
  keyboard UI entries. The test suite passes 33 checks, including four optional
  retail-input integration checks.
- Rebuilt pilot ROM SHA-256:
  `344d4290c7877f446f01175d9cffb90fcead5bb064f7cde148c8c18c5b9f701a`.
  UPS SHA-256:
  `32a3c109dae53858a0ecf7d4bf5f0d5c85ac8f7cbc0cdaea7f6653cd33baed6c`.
- `build/smoke-keyboard-town-01` passed the extended 93-step regression in
  5 minutes 14 seconds. Destination naming opened in English mode, rejected
  excess letters beyond `AAAAAA`, and returned to Rover dialogue after
  confirmation. The destination prompt and translated “town” label were
  visually checked. Four-MiB RAM remained confirmed at test completion.
- The post-destination dialogue exposed a separate untranslated path: `7F2F`
  appends the Japanese town suffix inside messages such as `2ACE`. This is
  recorded for the main translation work; the keyboard patch does not alter that
  insertion routine. Save/reload and hardware testing remain outstanding.
- Repeated the complete `make pilot` pipeline with 33 passing tests and the same
  output hashes. Confirmed the GitHub repository remains private.

### Full-project continuation and choice runtime

- Added `WORK_QUEUE.md` to track main porting, translation review, stability,
  hardware validation, image replacement, keyboard stretch work, and release.
- Audited all 3,374 decoded DMA files. Five direct choice-loader calls span
  main code, Quest Manager, and Player Select 2; all are covered by the runtime
  patch. The Festival Stall's setter-only path keeps its valid ten-byte inputs.
  No direct jumps, literal pointers, or main-code branches target the reclaimed
  choice-storage region. Detailed local evidence: `build/audits/choice-callers.json`.
- Implemented guarded sixteen-byte rows, selected-answer storage/insertion,
  width measurement, drawing, main staging, and actor stack-frame expansion.
  The English town field no longer appends the Japanese village suffix. The
  permanent code and overlay sizes, save layouts, and font assets stay unchanged.
- All 39 tests passed. The pinned MIPS assembler verified the 132-byte width
  routine, SHA-256 `4884d7eea3c26fc42c5cf3ee1aee92aa66cb742452d18129e949d05e9559a781`.
- Experimental `build/runtime16/` contains 9,127 edits, with 446 English choice
  candidates. Thirteen over-sixteen-byte disc references and one unmatched
  choice remain withheld. ROM SHA-256:
  `6b5f7ce98c4d21565d45c2bcea6969ec2f3e3b81ae8c439282b9a6560595f152`.
  UPS SHA-256:
  `a64fab5c1fc63485e980c6e24d40ecff01ddca93375bc6a42dc8fe1094bd7d62`.
- Started a silent, bounded four-MiB regression with choice snapshots. Early
  observations confirm a sixteen-byte row and its selected-answer copy match.
  The full scenario and town-suffix assertions remain in progress at this checkpoint.

### Choice acceptance and reusable emulator checkpoints

- `build/smoke-runtime16-choice-01` passed 218 recorded steps through town
  arrival. `tools/validate_runtime_smoke.py` verifies ten acceptance conditions,
  including sixteen-byte choice preservation, three long menu rows, player and
  destination limits, and town insertion without the Japanese suffix.
- Promoted the verified sixteen-byte runtime into the reproducible pilot target.
  `make pilot` passes all 39 tests and retains ROM SHA-256
  `6b5f7ce98c4d21565d45c2bcea6969ec2f3e3b81ae8c439282b9a6560595f152`.
- Added isolated cartridge-save seeding, same-ROM emulator checkpoint seeding,
  save/load-state actions, bounded test-RAM writes, and graceful silent shutdown.
  The state round-trip regression restores a deliberately changed RAM marker.
  These are emulator checkpoints, not evidence of in-game save compatibility.
- `build/smoke-arrival-checkpoint-01` repeats the complete choice/name/town
  regression with 220 recorded steps and saves an arrival checkpoint for further
  gameplay tests. All ten post-run acceptance checks pass. FlashRAM is still
  blank; house selection, introductory jobs, and a normal game save remain.

### Resident runtime module and English message dates

- Added a pinned Docker C/MIPS build, bounded linker script, module manifest,
  strict DMA additions, and guarded bootstrap. The new file at VROM `02800000`
  reserves sixteen KiB at RAM `801948E0` before the first heap allocation.
  The original watchdog is preserved at `801949E0`; its callers and relative
  control flow pass the complete DMA reference audit.
- `build/smoke-module-boot-01` passed module magic, readiness, heap bounds, and
  end guards. The hardened bootstrap additionally checks the heap size and
  loaded module version/reservation before executing it.
- `build/smoke-module-arrival-01` passed 225 recorded steps and all ten choice,
  name, and town acceptance conditions, with all module guards intact at arrival.
  ROM SHA-256:
  `16b0511bf706b5b566ab609f8a9d399fbbbed8a9d3c02652a7e6d02d4a13b8fa`.
- Added seven bounded English date/time message formatters. Month and weekday
  insertion frames grow by eight bytes; other UI formatter callers remain
  native. Portable C tests cover every sixteen-bit year, every byte-valued
  component, ordinal exceptions, padding, capacity failure, and guard bytes.
  All calendar words match the supplied English GameCube disc.
- `build/smoke-module-dates-02` passed 39 recorded steps, calling all seven
  real MIPS message-insertion functions and verifying results, surrounding text,
  return lengths, stack restoration, and guards. The complete emulator checkpoint
  is restored after test-only RTC and scratch-memory changes. The initial probe
  exposed the debugger's valid `S05` stop spelling; accepting both standard stop
  spellings fixed the test harness, not the game code.
- The date module links to 2,016 bytes within its sixteen-KiB reservation. Its
  experimental ROM SHA-256 is
  `6e19c9057e4ea3d4be2fe66bedbcc2b3886e5619622e467f0d342759d379f329`;
  UPS SHA-256:
  `e69ba1e6e93ce178562436f3dec998409e408581b4efd3b7975949e4a21deee9`.
  All 47 tests pass. The ordinary pilot remains separate until command handling
  and broader gameplay/save regressions are complete.

### GameCube English command handling

- Added guarded module entry hooks for code size/attributes and message dispatch.
  All native opcode metadata and handlers remain in use. Extended text requires
  verification of the complete module code patches and its added DMA data.
- `build/smoke-module-ampm-01` passes 48 recorded steps. Midnight and late-night
  hour insertions latch the correct meridiem; changing the RTC afterwards does
  not change the corresponding AM/PM result. Length, cursor, metadata, guards,
  and checkpoint restoration pass.
- `build/smoke-module-capital-01` passes 43 recorded steps. The first substituted
  field is capitalized, the following field is not, intervening literals remain
  unchanged, source strings remain lowercase, and date fields do not consume the
  capitalization flag. AM/PM and capitalization flags coexist correctly.
- `build/smoke-module-commands-arrival-01` passes 225 recorded steps and the full
  choice/name/town acceptance checks with the English GameCube calendar question.
  ROM SHA-256:
  `c0a0e5475ab980a74119446dad0c7ec75e79054703e5cc321dc85087b2171833`.
- Added protected-pacing commands and their complete B-button, cancel-order,
  cursor-timer, and explicit-pause handling. `build/smoke-module-pacing-01` passes
  54 recorded steps: locked timers decrement instead of fast-forwarding, unlock
  restores input behaviour, and an eight-frame pause retains speed nine rather
  than the fast-path speed two. The stronger repeated scenario asserts both
  observed pause values explicitly; `build/smoke-module-pacing-02` passes all
  54 steps. `build/smoke-module-pacing-arrival-01` passes 225 steps and all ten
  choice/name/town acceptance checks.
- The new pacing experiment contains 9,284 candidates and links 2,944 module
  bytes. ROM SHA-256:
  `141da327dd49654e8a9d39ab82c1727a819efa93c83a815abcc45cab60ac7d4e`.
  UPS SHA-256:
  `04af7c26e3efe8ba84e4d65722a852e632d3bb9ba88d8371f7de5ed09d3df546`.
- The expanded hook audit found an audio-sample word resembling a MIPS call and
  an unaligned graphics word resembling a function pointer. It now classifies
  executable DMA segments from the pinned definitions, checks aligned literal
  pointers throughout the ROM, and finds no external hook-interior references.
  The 48-test suite and the five focused module checks pass.

### Resident twenty-character choices

- Added module-owned 160-byte choice storage, twenty-byte text capacity, and
  thirty-two-byte global row stride. Actor staging arrays use twenty-byte rows;
  their frames and high temporaries grow by forty bytes. Both width variants
  match independently assembled MIPS source; the baseline variant is unchanged.
- Verified the loader's existing physical thirty-two-byte DMA slot. No stack
  enlargement is needed for its largest aligned read; the adjacent live length
  temporary remains outside the transfer.
- `build/smoke-module20-choice-02` passes 94 recorded steps: all thirteen long
  reference loads, all four rows, maximum width, fifth-row and overflow rejection,
  each selected row, selected-text insertion, stack restoration, and end guards.
  The initial test expected a length difference from an insertion function that
  returns the complete new message length; correcting that test expectation and
  passing the actual input length resolves the test failure without a ROM change.
- The module links 3,168 bytes and contains 9,297 candidates. ROM SHA-256:
  `cec487f850af1ce5a36b1868db0ce2dc02a63f0f21dd4e99645439925c5f7ae6`.
  UPS SHA-256:
  `b571120b2b60b7fc649930f02f1ff8d5d38d699e51561c2288832071d5098366`.
  All 51 tests pass. The full twenty-byte train-to-town regression is running.
- Separate pacing-build gameplay continuations reach Nook's escort and the
  house-selection area. Those snapshots do not establish a completed normal save.

### Reviewed reference identities

- Added individually explained, source/reference-hash-bound identity overrides.
  The final choice `0013` is an abbreviated GameCube label for the N64 message-edit
  action. The gyroid's surrounding GameCube menu changes remain unimported.
- All 460 choice labels now produce candidates. The separate match build contains
  9,298 edits; ROM SHA-256:
  `48a0c7e417da809b5a17953e8b323e7e6fbfb779dfe2e6223c5521a7b017babc`.
  UPS SHA-256:
  `21693a05c3ee9e61a2a78a2d381dd14e875635d06ec0de7cdfed5023f8c0dfe0`.
  All 55 tests pass, including stale/duplicate/unexplained reference rejection.
- `build/smoke-module20-dates-01` passes 39 steps and
  `build/smoke-module20-pacing-01` passes 54 steps on the twenty-byte runtime.
- Exercise entries `2665..266A` need an N64-specific review. In particular,
  N64 `2666` is a counted exercise cue, not the same-ID GameCube warning about
  full hands. GameCube random targets `3A2A..3A31` exceed the N64 message count.
  These findings do not authorise importing or deleting the branch commands.

### N64 exercise cues and general-string audit

- Added original drafts for `2665`, `2666`, `2669`, and `266A`, preserving every
  native pause and end command. The rejected GameCube continuations lead to
  C Stick exercise instructions absent from these N64 cues. Existing compatible
  GameCube exercise lines remain unchanged. Event-specific runtime review remains.
- The exercise build contains 9,302 edits. ROM SHA-256:
  `4c1558d32a53b40a7a6fa74744cb577199fe8f6f5ff5a0da7385810449165b35`.
  UPS SHA-256:
  `680079b7a9845cc6732568417c818822720a25cb8fed35f125b894e76efd7b6c`.
  All 59 tests pass. Original-file loading rejects duplicate IDs and exercises
  all four draft hashes and complete native command signatures.
- `build/smoke-module20-arrival-01` passes 225 steps and all ten acceptance
  conditions. `build/smoke-reviewed-match-choice-01` passes 94 targeted steps
  after the final label changes the choice-bank offsets.
- Pacing-build continuations enter the orange-roofed starter house, leave it,
  and reach Nook's home-gyroid explanation. Several untranslated messages are
  visible in that sequence and need entry-level follow-up. No normal save is
  claimed from those emulator checkpoints.
- Added a thirty-four-site direct string-loader audit. Main-code review
  identifies fixed saved catchphrases, home-gyroid messages, NPC-letter fragments,
  special-NPC names, and shop-level labels as distinct constraints. The inventory
  is evidence for further implementation, not permission to enlarge every entry.

### Reviewed multi-message house explanation

- Added exact all-or-nothing approvals for multi-record GameCube dialogue.
  Nook's `07EA` explanation continues through N64 opening-reserve slots `0838`,
  `0839`, and `083A`, preserving the supplied English pages, timing, and emphasis.
  Independent checks preserve choice-index mappings and other gameplay commands,
  restrict actor arguments and text fields, and reject incoming native branches
  to reserved slots. The builder does not trust an edit's policy flag alone.
- All 67 tests pass. Candidate generation admits four additional records, for
  9,306 edits. ROM SHA-256:
  `c691fa6059b8766df1fbe3432609e48918d04e0ee1914079a783050b9b569f12`.
  UPS SHA-256:
  `bb9a4110046e566e8742a0649278a507be1a92d42560d59d61745774bc7c50f4`.
- `build/smoke-sequence-native-01` passes 99 recorded steps: all four real DMA
  loads, three native continuation assignments, both terminator phases, both
  final choice branches, the native repeat response, and buffer/module guards.
  This injected-call test restores the checkpoint and is not actor-flow approval.
- Pacing-build normal gameplay completes Nook's work offer. Gyroid message `092E`
  is the job-time greeting, not its normal save menu. Choice snapshot data is
  inactive (`choice_state = 0`) and must not be mistaken for a displayed menu.
  FlashRAM remains blank; completing the introductory jobs remains necessary.

### Choice cancellation and closing sounds

- Ported GameCube `62` with both choice flag bytes, native B-to-last selection,
  short/long/decision sound routing, duplicate message-closing sound suppression,
  and wait/initialiser resets. The flag names do not mean B is disabled: native
  input inspection and targeted calls confirm that the flag enables B-to-last.
  Native disappearance setup and animation remain unchanged.
- `build/smoke-cancel-native-01` passes 83 recorded steps, including real native
  A/B selection, neighbouring flag-byte guards, all sound decisions, suppression,
  native setup fields, separate-window reset checks, and module guards. Audio
  output is disabled. All 68 unit/integration tests pass.
- The cancellation build imports four additional inventory prompts: `0A4D`,
  `1348`, `17B2`, and `17B3`. Other GameCube storage/music menus have different
  choices or extra actions and remain rejected. There are 9,310 edits and 3,280
  remaining main-dialogue candidates. ROM SHA-256:
  `34eb6c003b84518182084793875b7d42f142278ed02da7592feec88539dd2b84`.
  UPS SHA-256:
  `4c67293af8f921d217a707e418ba20085b0851a397a92eae02215ef28ea0d616`.
  The module links 3,424 bytes within the existing sixteen-KiB reservation.
- `build/smoke-cancel-choice20-01` passes all 94 long-choice regression steps
  after the additional module code moves its linked text-storage addresses.
- `build/smoke-sequence-arrival-01` passes the English-keyboard scenario through
  Rover's telephone conversation, but that scenario does not record the full
  long-choice/arrival acceptance data. Its validator correctly rejects the missing
  evidence. `build/smoke-sequence-town-01` continues to `07DD` with intact guards.
  The cancellation build uses the complete `runtime-choice-scenario.json` for
  the full regression rather than claiming the shorter run is equivalent.

### GameCube page delivery and introductory farewell

- Added a dialogue-only policy that retains the confirmed GameCube reference's
  native page-clear and button-wait commands even when their count or placement
  differs from the Japanese text. Branches, choices, actor commands, terminators,
  geometry commands, and expansion limits remain checked. No English reflow or
  removal of GameCube waits/pages occurs. Manifests record both delivery counts.
- Added a reviewed identity for `09C9`: the legacy farewell differs only by
  renaming Animal Crossing to Animal Forest, so exact visible-text matching had
  withheld the correct English reference. Native actor arguments and commands
  agree. The new candidate uses the supplied GameCube wording.
- All 69 tests pass. The delivery build contains 9,677 edits, including 366
  newly admitted page-delivery candidates, and leaves 2,913 main messages rejected.
  ROM SHA-256:
  `d034b987952be85a09c3277d0d3ef2a8326fa30bea161d37b3d9e4f0bdf5fa95`.
  UPS SHA-256:
  `492e4d30b4830717f791d3c2822377d494d40ec666ad7c892fb66ee8cf877170`.
  There are 1,117 conservative reference-dialogue layout warnings. These counts
  are not reviewed coverage or release approval.
- `build/smoke-cancel-arrival-01` passes 225 steps and all ten acceptance checks.
  The delivery build's full regression is running. The work-offer `07EC` needs
  its own reviewed split: its supplied English reference is 1,051 encoded bytes
  with an expansion bound of 1,127. The legacy uses reserved slot `2AE9` for its
  second part; the source placeholder and incoming references require verification.

### Bounded English work offer

- Split the complete GameCube `07EC` at its existing wait/page-clear transition
  after the thorny-situation passage. The first 472 reference bytes continue to
  native reserve slot `2AE9`; the second part retains reference bytes 477 through
  1050, including native final end `00`. No English text is omitted or reflowed.
  Expanded bounds are 495 and 650 bytes. The approved five-byte separator is
  replaced by one continuing-message boundary, not an extra button wait.
- Added token-boundary, exact-reference, complete-coverage, and separator checks
  for sliced reference sequences. Every output part remains hash-bound and must
  be installed together. Source `2AE9` is a verified placeholder with no incoming
  native message-script branches. The native Nook guide has no direct reference
  to either record; actor progression still requires runtime verification.
- All 70 tests pass. The work-offer build contains 9,679 edits, with 2,911 main
  messages still rejected and 1,118 conservative reference layout warnings.
  ROM SHA-256:
  `882ff4d076c4c1a566fe4ca152510e79c857890155977de26d226b16dcc2a688`.
  UPS SHA-256:
  `d7fcb38486c277e939c3c1a03e73a711a491e29f32a416d1a56b75a96c6b5087`.
- `build/smoke-work-offer-native-01` passes 45 recorded steps covering both
  cartridge loads, the continuation, native final end, and buffer/module guards.
  `build/smoke-delivery-arrival-01` passes all 225 full-regression steps and all
  ten acceptance checks. Normal sequence-build gameplay also reaches Nook's
  housing area; the English house-explanation traversal is still in progress.
- `build/smoke-work-offer-home-01` passes the 99-step house-explanation DMA and
  branch regression on the same build after the additional message-bank changes.

### Native reference formatting and normal house explanation

- Verified the native sentence and character consumers against the pinned
  GameCube implementation. Added explicit formatting import with parameter guards:
  line anchor 0–2, nonzero character/line scales, and unchanged sound/flow checks.
  No font asset or reference line break changes. The manifest records formatting
  tokens, and geometry remains marked for individual layout review.
- `build/smoke-font-controls-native-01` passes 385 recorded steps, including actual
  sentence dispatch, RGB/span restoration, scale extremes/reset/recalculation,
  token advancement, scratch display-list guards, and checkpoint restoration.
- All 78 tests pass. The layout build has 9,943 edits, 9,099 reference dialogue
  candidates, 264 newly admitted formatting candidates, 2,647 remaining main
  messages, and 1,308 conservative layout warnings. ROM SHA-256:
  `055a6643739ce365499894e51a0e92b5545d5d342e6d36d94acd82a601f16fae`.
  UPS SHA-256:
  `9da4083433566f34a77f83fb06020040d2bdc25eed7af5e7f0b8767d461a19c0`.
- Added bounded normal dialogue advancement that stops on native active-choice
  state, preserving the menu for explicit branch testing. The sequence build
  enters/exits the house, confirms the purchase, and traverses all four English
  explanation records normally. `build/smoke-sequence-home-choice-01` reaches
  `083A` with two active English options and intact module guards. No game save
  has occurred; its FlashRAM remains blank.
- `build/smoke-work-offer-arrival-01` passes all 225 full train-to-town regression
  steps and all ten acceptance checks. The layout build's full regression and
  both normal house-explanation choice outcomes remain to be tested.

### Purchase confirmation and normal explanation outcomes

- Added a hash-bound one-record approval for `07E9`, retaining the full English
  purchase/radio-gift confirmation. Its repeated emotion commands use only the
  original native argument tuples, and its BGM, player field, `07EA` continuation,
  and end marker remain intact. Its small-print aside follows the GameCube's own
  anchor/line-scale commands. Sequence validation now retains and compares the
  original root's outgoing links in the final member instead of dropping them.
- All 79 tests pass, including changed/omitted external-link and actor-argument
  rejection. The purchase build has 9,944 edits, 9,100 reference dialogue
  candidates, 2,646 rejected main messages, and 1,309 layout warnings.
  ROM SHA-256:
  `52dc7bce97a836eb68acd3df62a920ede4d678ab18a0d964b85dc049a18d998d`.
  UPS SHA-256:
  `cf7ca0c96ab8e62ac13fe64afd7588462a41689730871b1e3c8c8405edb6b53b`.
- `build/smoke-purchase-native-01` passes 28 recorded steps: real cartridge load,
  complete payload and buffer guards, unchanged outgoing `07EA`, both continuing
  terminator phases, module guards, and complete checkpoint restoration.
- `build/smoke-sequence-home-repeat-01` passes 59 recorded steps: selecting the
  second option reaches native repeat response `081D`, traverses all four English
  explanation records, and returns to the active `083A` menu. The continuation run
  passes 45 steps: the first option reaches invoice `081E` and then work offer
  `07EC`, with intact guards. These are normal actor/controller paths, not injected
  branch calls. The sequence ROM predates the English work-offer split, so it
  cannot establish that newer split's normal progression. FlashRAM is still blank.

### Complete English pixel-space control

- Added GameCube `67` with size 3, sentence attribute 4, native cursor advancement,
  and a resident sentence-width consumer. The lookup retains all three native
  sentence handler addresses and returns zero for unsupported codes. It applies
  the unsigned pixel amount at the current total character X scale; no glyph is
  drawn. Missing arguments do not advance the cursor. No font assets change.
- Source/build guards include the sentence lookup hook and its replaced-function
  interior audit. The builder rejects an incomplete hook. The module links 3,680
  bytes in its existing sixteen-KiB reservation; module SHA-256 is
  `f499ecd258c8bd7e4b4703ef13f6412a52a4b0b09b47b0af36a1d97e55ed8c93`.
- All 80 tests pass. `build/smoke-space-native-01` passes 476 recorded steps,
  including the original native formatting cases, SPACE arguments 0, 7, and 255,
  scaled width changes, message advancement, malformed-token handling, display-list
  and module guards, and complete checkpoint restoration.
- The space build imports `069A` and contains 9,945 edits, 9,101 reference dialogue
  candidates, 2,645 remaining main entries, and 1,310 conservative layout warnings.
  ROM SHA-256:
  `621474f6455e54a450faa50266f1e3852a21226817e1d47d79dff8d6e464da13`.
  UPS SHA-256:
  `962a18f3a09f34abdbf57787ec2b212ae4be16ea7d8cdf1f98c40ae91c7cf521`.
  No confirmed same-ID candidate is now rejected for an unsupported opcode;
  unconfirmed reference identities and incompatible flow remain unapproved.
- `build/smoke-layout-arrival-01` passes all 225 full train-to-town steps and ten
  acceptance checks. The space build's full regression is in progress.

### Identical native shop and reward records

- Reviewed six additional reference identities: native `02DC`, `02E7`, `02E9`,
  `02EA`, and `02ED` are complete duplicates of confirmed Nook shop records;
  `0DFB` duplicates a confirmed same-personality full-inventory reward response.
  The English meanings match, and all native controls agree. The approval records
  bind source/reference hashes and identify the equivalent native record.
  Generation verifies that donor record as well; similar text is not sufficient.
- All 82 tests pass. The equivalent-record build has 9,951 edits, 9,107 reference
  dialogue candidates, 2,639 remaining main messages, and 1,310 layout warnings.
  ROM SHA-256:
  `7ecbf773c5d35a829b22857bf2db5d0794ba0e9ab575ced39a29c6b0465b69e9`.
  UPS SHA-256:
  `404c509b2c30362b2913dbd1e24da22dfe519206b399379a7a66da4e0cb40055`.
- `build/smoke-space-arrival-01` passes the complete 225-step train-to-town
  regression and ten acceptance checks. The space build also passes the 78-step
  cancellation regression and 89-step twenty-byte-choice regression after linked
  module storage moves. These targeted runs omit the separate six-step post-run
  memory scenario included in some earlier runs; their assertion coverage is
  recorded in each result file.

### Bounded English villager names

- Confirmed all 216 same-index English villager names against the legacy text;
  the first 216 N64/GameCube personality-table entries also agree. Each name
  reference's complete padded eight-byte hash is verified before import.
  Added 178 complete names that fit the native six-byte destination. The 38
  seven/eight-byte names remain withheld, without abbreviations or truncation.
  Four alignment/reserve slots, the file header, and all other bytes remain intact.
- All 87 tests pass, including identity/hash guards, plain-text checks, complete
  storage-span preservation, and overlong-name rejection. The name build has
  10,129 edits; main-dialogue counts remain 9,107 candidates and 2,639 rejected.
  ROM SHA-256:
  `cf2a9ccf541c9dfd41559c7d04b9e76cbe96c0b499b11fcc2eee2780fada7016`.
  UPS SHA-256:
  `bc772a146628b1751112ad0d995b721a499a1246fb7ea05a2ff9fd141b028a9c`.
- `build/smoke-npc-names-native-01` passes 660 recorded steps: all 216 actual
  name DMA loads, exact six-byte results, sixteen-byte guards on both sides,
  the no-write `FF` path, module guards, and complete checkpoint restoration.
  Dialogue labels, quest names, letters, and game-save round trips still need
  their gameplay tests. This does not establish full name coverage.

### Recover actual legacy item references

- Replaced archived item-data offsets with the supplied patched ROM's actual
  guarded loader tables. Verified all sixteen ordinary groups and the furniture
  group's table, count, data range, terminator, and unchanged reconstruction.
  Native furniture has 947 groups of four identical rotation-name slots plus one
  filler; the inventory records the four-to-one donor mapping explicitly.
- All 90 tests pass. The generated inventory now exposes usable legacy names
  without pretending they establish GameCube identities. The first two legacy
  music labels are exchanged, and the GameCube plant list has an inserted entry;
  these differences prohibit blind same-index import.
- The current space-runtime gameplay run reaches Nook's housing escort through
  normal controller input in 66 recorded steps. It reaches `07E1`; FlashRAM
  remains blank, so this is not a game-save result.

### Bounded English item-name import and reader audit

- Added 107 distinct GameCube item-name candidates across 230 native storage
  slots. Complete legacy names must agree after case-only comparison; donor IDs,
  native/reference hashes, plain glyphs, rotation equality, and ten-byte capacity
  are checked. Exact GameCube spelling/case is retained. No overlong name is
  shortened. The entire item DMA file, including untouched bytes, is verified.
- All 98 tests pass. The item build has 10,359 edits with unchanged main-dialogue
  counts. ROM SHA-256:
  `1b0d710d5809debc76889398a4ce22603c9159d34c3ea2513bf44efae9d56801`.
  UPS SHA-256:
  `f7c5be877b587934efdfc9567691ec75376e5f6a411020d469a388019ee6072c`.
  The native regression covers 4,544 item positions plus empty/unsupported types,
  split into nine independent scenarios to retain the runner's ten-minute bound.
  Results remain pending; generating a scenario is not a passed test.
- Added a direct-reader inventory: 35 item-loader calls in main code and 23
  overlays, and two villager-loader calls. The main item paths expose separate
  ten-byte handbill, message-free, message-item, and ground-label destinations.
  Increasing only the source-name loader would not preserve longer English names.
- Normal space-build gameplay reaches the English purchase `07E9`, then `07EA`,
  `0838`, `0839`, and the active `083A` menu. The selection run records 65 steps;
  the bounded menu run records 30 with intact module guards. This verifies the
  approved purchase's normal continuation, not merely an injected DMA call.

### Standalone sixteen-byte item-name runtime

- Added a separately configured `02A00000` resource with 4,544 sixteen-byte
  slots, 648 English candidate slots, and 282 distinct confirmed reference IDs.
  The source is 72,736 bytes including its guarded header. Unconfirmed names
  remain Japanese; native ten-byte callers and save formats are unchanged.
- The original C API checks capacity, item indices after native conversion,
  resource configuration, and header before writing exactly sixteen bytes.
  Aligned staging supports unaligned destinations. The builder reconstructs the
  resource from guarded edits, verifies hashes, and requires the capable module.
  No source text is truncated. This is an API test build, not full integration.
- All 103 tests pass, including all 65,536 possible item values in the portable
  implementation, invalid capacities, no-write failures, source/reference guards,
  resource reconstruction, and complete module configuration checks.
  The module links 4,288 bytes; unconfigured module SHA-256:
  `a6beaa858edcde94e398e2e61c6ecdf8990f028f49bd56c71f6ea3be84632a3b`.
- `build/smoke-extended-items-native-01` passes 1,101 recorded steps. It covers
  every confirmed reference identity, category endpoints, placed conversions,
  invalid IDs/capacities, null pointers, unaligned writes, resource disabling,
  all header words, adjacent/end guards, and complete checkpoint restoration.
  ROM SHA-256:
  `4aaa0600b5d23336bbdd04f010b119f61f98e3620644bce1f078796e0be95f71`.
  UPS SHA-256:
  `f6b5b4143feb4b1376e2bee8aae905fa7869fbfe8e3726456799438f567c7efb`.
- `build/smoke-space-home-continue-01` traverses invoice `081E`, work offer
  `07EC`, and continuation `2AE9` in 45 recorded steps. The subsequent 66-step
  `smoke-space-work-offer-end-01` completes the continuation, closes the message,
  and returns normal player control. FlashRAM remains blank. Read-only native
  layout queries locate homes at acre `(3,2)`, the shop at `(2,1)`, and the station
  at `(3,1)` for this isolated town; no player position is edited.

### Native item regression and exact debugger observations

- The eight `smoke-items-native-batch-0-01` through `-7-01` runs each pass 1,545
  recorded steps. `smoke-items-native-batch-8-02` passes 1,362. Together these
  cover all 4,547 requested native item IDs, including every furniture rotation,
  ordinary names, empty zero, and unsupported types, with adjacent guards.
- The first batch-eight attempt (`smoke-items-native-batch-8-01`) stopped on its
  first injected call for item `1D0C`, with `S0b` and PC `20202020`. The complete
  rerun passes, but the initial failure is unexplained and remains open. This
  is not a clean repeatability result or a hardware claim. Call failures now
  capture complete before/after register packets and scratch-stack bytes.
- A separate focused diagnostic establishes ares' unaligned short-read behaviour:
  raw four-byte reads at offsets one, two, and three all return the aligned
  preceding word. A two-byte read at offset one returns the preceding halfword.
  The corrected exact-read API and byte-edge write API pass portable alignment
  cases and all assertions in `smoke-debugger-alignment-02` (21 recorded steps).
  Two preliminary item-field runs' apparent two-byte guard overwrites result
  from these reads; the complete field regression is rerun with exact reads.
- Read-only native actor snapshots guide ordinary movement into Nook's shop.
  `smoke-space-shop-front-01`, `shop-door-01`, and `shop-entry-01` each record
  eight steps. `smoke-space-job-introduction-01` records 36 steps and reaches
  English `07EE`, `07F1`, and `07F2`, followed by native clothing instructions
  `07F3`. That entry needs an approved GameCube Y-to-N64-START button adaptation.
  No player position or progression is edited; FlashRAM save validation remains.

### Sixteen-byte main-message item fields

- Added five resident sixteen-byte item rows and a validity mask, with ten-byte
  compatibility mirrors in the unchanged native window. Hooked the native
  setter, the main message insertion call, and the item-ID convenience wrapper.
  The separate dynamic-choice reader remains ten-byte pending its capacity proof.
- The pinned subsegment audit distinguishes executable text from embedded data.
  Two texture pointers (`0C027630`) at board offset `1C04` and catalogue offset
  `8A74` resemble calls into the setter's interior but are in verified data
  sections. Real instruction calls and literal function pointers remain guarded;
  mutation tests prove both are rejected when they bypass a replaced entry.
  The item-field audit identifies 27 setter calls, two insertion calls, five
  wrapper calls, and no direct or literal-pointer uses of the ten-byte getter.
- All 115 local tests pass. `smoke-item-fields-native-03` passes 1,634 recorded
  steps and 429 actual MIPS calls using the corrected memory-observation API.
  Tests cover all five fields, full/short/empty replacement, native handler calls,
  exact 1,024-byte limits, invalid/no-write cases, non-main ten-byte windows,
  capitalization, wrapper loads, absent-resource fallback, and intact guards.
  The complete emulator checkpoint is restored; FlashRAM stays blank.
- The module links 5,184 bytes; its unconfigured SHA-256 is
  `9c3961af390b363604f7eadc45334f5229e9cef61d645ed2b4b75b20e90a8faa`.
  ROM SHA-256:
  `7d9a6780411d4280a8addab22b922f609786616a68dd92e25286168b5f7a54f4`.
  UPS SHA-256:
  `b2dc041a7e6dd227fa64ff7900c6bb03a01610836c9bacb2d82855c015538c6d`.
  The build retains 10,359 ordinary edits and the separate 648-slot resource.
  The full train-to-town regression is running; actor-specific wider-item
  gameplay and other name destinations still require work.
- The wrapper tests expose a remaining alias: furniture `0A84..0A87` has the
  confirmed English W-shirt name, but native conversion reads ordinary
  `item_24:00B6`, whose equal Japanese source is not yet translated. This is
  recorded as untranslated destination coverage, not counted as English output
  merely because the requested furniture resource row has a candidate.

### Controller-specific reference wording and full item-field regression

- `smoke-item-fields-full-01` passes all 225 train-to-town recorded steps and
  all ten checks in the acceptance validator. Player/town entry, long choices,
  selected text, arrival, four-MiB memory, and module guards pass. Hardware,
  actual save/reload, and actor-specific choice coverage remain unclaimed.
- Added a hash-bound `inventory_y_to_start` operation for Nook's `07F3` clothing
  reminder. It changes only the GameCube highlighted Y-button span at byte 84
  to START, correcting its count from eight to twelve characters. The remaining
  text, colour, manual line/page breaks, pauses, and actor commands are retained.
  The builder independently rejects unadapted, partial, or modified payloads.
- All 119 local tests pass. The 382-byte adapted message has no layout warning
  and an expansion bound of 398. The generated controller build contains 10,360
  ordinary edits, 9,108 reference dialogue candidates, and 2,638 remaining main
  records; the separate item resource remains at 648 candidate slots.
  ROM SHA-256:
  `7c56f9242a490a4c133f01eb16cbd278aa69ab910adf1c9e1b77f66d8abf6a9b`.
  UPS SHA-256:
  `5be91cbf9fb0e61eb72fe2a16d5f0021a4d27869e8ee06e160819674c410dd7c`.
- `smoke-controller-native-01` passes all 26 recorded steps: actual message DMA,
  complete approved content, native final-termination behaviour, buffer/module
  guards, and checkpoint restoration. The normal space-build shop test confirms
  START opens the inventory and reaches the uniform's native grab/cancel menu.
  The adapted reminder still needs its own ordinary-gameplay traversal.

### Verified clothing alias and ordinary uniform equipment

- Added a guarded native placed-item alias pass. The confirmed W-shirt donor
  `item_10:0A84` has the same native Japanese field as `item_24:00B6`; retail
  conversion reads that ordinary row for all four placed rotations. The pass
  transfers the complete seven-character name and its verified reference hash,
  rejects conflicting/stale/nonplain donors, and preserves original overrides.
  Remaining reports and per-bank slot counters are updated together.
- The alias build contains 10,361 ordinary edits and 231 ten-byte item slots,
  still representing 107 distinct reference IDs. The separate wider resource
  contains 649 candidate slots and 282 distinct reference IDs. Resource SHA-256:
  `a1f6d036f41518d3268236122aedecba52f18a62b1b1ae7fbc8b3e740c1c4341`.
  ROM SHA-256:
  `40b658b275c351ff515696fcfe76b88707c51c7d261d55203a0b12638abd37b2`.
  UPS SHA-256:
  `b9170009c7d8ecec0059daa0e17d0d8a28de2bfd911f0be93eb69e493a713b1f`.
- All 125 local tests pass. `smoke-alias-native-01` passes 29 recorded steps,
  including direct ordinary loading and all four placed rotations with guards.
  `smoke-alias-fields-01` repeats all 429 MIPS field/wrapper calls in 1,634 steps,
  now including the English ordinary alias. The runtime module is unchanged.
- Normal space-build gameplay selects the uniform, grabs it, moves it to the
  avatar, and equips it. `smoke-space-first-job-01` passes 30 steps, with Nook's
  acknowledgement `07F4` and English planting request `07F6`/`07F7`.
  `smoke-space-first-job-outside-01` records nine steps and read-only proof of
  equipped item `2410`, the previous shirt in pocket zero, and ten planting
  items in pockets one through ten. The actual planting/save work remains.

### Planting instructions and token-aware coverage

- Added the individually approved START-button span for Nook's planting reminder
  `07F8`, at encoded offset 80. The 438-byte result retains both GameCube
  pixel-space commands and every surrounding line/page break and pause.
  `smoke-planting-native-01` passes 38 recorded steps covering both approved
  controller messages, real DMA, native termination, guards, and restoration.
- The planting build contains 10,362 edits and 9,109 reference dialogue records;
  its separate wider item resource remains 649 slots. ROM SHA-256:
  `7e28ccd4227a9b3308d5940c3a5f03dffcd4ad15bfbac5099a33be1bf2fe64f4`.
  UPS SHA-256:
  `e317149fdc02183a364e7cec556753773e6b7f66baaf423987f191d224028ea1`.
  The reminder's reference layout has a conservative warning; it is not reflowed.
- The new coverage inventory checks all native bank records against an explicit
  final candidate file. It rejects stale/duplicate/unknown edits and retains raw
  or unmapped glyphs as review needs. Main records without candidates comprise
  1,691 Japanese texts, 23 exact placeholders, 919 without static text, one Latin
  text, and two number/symbol records. Ten of the 919 have dynamic insertions.
  No command-only record is marked unreachable or complete. All 9,116 main
  candidates still require review; 83 use the shared Japanese dash glyph in
  otherwise Latin text, which is listed for punctuation review, not reclassified
  as Japanese words. One original fallback draft explains the difference between
  2,637 reference rejections and 2,636 records absent from the final candidate file.
- All 132 tests pass. Normal space-build gameplay plants the first three flowers
  in `smoke-space-first-flower-01`, `second-flower-01`, and `third-flower-01`.
  Reopening inventory resets its cursor to pocket zero; `next-flower-01` records
  that observation and opens a seed menu, without consuming another item.
  The third-flower run explicitly asserts the full pocket array.
- The remaining-plant generator uses only controller input and read-only pocket
  assertions. A first southward attempt reaches occupied ground and the native
  cannot-plant warning; its item-consumption assertion correctly fails. The next
  route moves east from the preceding successful checkpoint. No item, quest,
  or player-position data is edited. Successful individual plants receive their
  own emulator checkpoints; those are not FlashRAM save evidence.

### Complete native message aliases and planting completion

- A single-stage exact-native-record pass adds 41 English reference candidates
  after verifying complete source equality, donor/reference hashes, the full
  adapted English output, command policy, and capacity. Multiple eligible donors
  must produce identical output; 79 target records with conflicting English
  remain withheld in an explicit report. Drafts, special approvals, and reviewed
  sequence permissions are excluded from transfer.
- The alias build contains 10,403 edits and 9,150 reference dialogue candidates.
  Final main candidate coverage is 9,157 records, with 2,595 absent: 1,664 Japanese
  texts, nine exact placeholders, 919 command-only/empty records, one Latin text,
  and two number/symbol records. These counts do not imply translation review.
  There are 1,312 conservative layout warnings. The wider item resource and
  resident module are unchanged. ROM SHA-256:
  `4bedb03d7bec984b05df5ca85d91278478f21209cfdee2061b54dee412cd523b`.
  UPS SHA-256:
  `068ec1af9db9ff3fbed0f9cf8d99d7a3ff754503d3968fdecbc5b9a933b07b79`.
- All 136 tests pass. `smoke-message-alias-native-01` passes 219 recorded steps,
  including all 41 actual message loads, complete headers/content, adjacent
  and module guards, and checkpoint restoration. The full train-to-town run
  is in progress; ordinary actor traversal of the new aliases remains.
- `smoke-space-plant-flowers-01` passes 21 recorded steps and consumes the four
  remaining flower seeds. `smoke-space-plant-saplings-01` passes 17 steps and
  consumes all three saplings. Every successful plant in these batches asserts
  the full expected pocket array and creates a checkpoint. All ten supplied
  planting items are gone; the previous shirt remains in pocket zero and the
  work uniform remains equipped. The player returns toward Nook through normal
  movement. FlashRAM save/reload and subsequent jobs remain unverified.

### Planting acknowledgement and native greeting-job instructions

- `smoke-message-alias-full-01` passes all 225 recorded steps and all ten
  train-to-town acceptance checks in six minutes twenty seconds. Memory guards
  remain intact and cartridge FlashRAM remains blank; this is not save evidence.
- Normal space-build gameplay re-enters Nook's shop and reaches planting
  acknowledgement `07F9`, followed by greeting request `0821` and reminder
  `0822`. The first is confirmed equivalent to the GameCube record apart from
  repeated existing actor-emotion tuples. Its one-record approval preserves the
  entire English reference, all page breaks/pauses, and native continuing end.
  `smoke-plant-complete-native-01` passes 28 loading/termination/guard steps.
  That intermediate ROM SHA-256 is
  `1ba37819abf26f457aa98166853da239e5d0567c7b0bd69441e090da7da2febc`;
  its UPS SHA-256 is
  `02adf10b989990ad2952b0a25b7e9d96ee0b7bacf16099955e1581027713b16c`.
- Added original N64-specific drafts for `0821` and `0822`. The GameCube text
  adds mayor/wishing-well instructions, and the legacy substitutes shrine wording;
  neither occurs in the native source instructions. The drafts preserve every
  native command, field, pause, page transition, and ending. Full English actor
  traversal remains. These drafts join the default candidate inputs.
- The intro-jobs build contains 10,406 edits, including 9,151 reference dialogue
  candidates and nine original dialogue drafts. Its final main-bank audit finds
  2,592 records without candidates, including 1,661 Japanese texts. The resident
  module and 649-slot item resource are unchanged. ROM SHA-256:
  `ea018a215c2ab7c58b1c1bb3def18cf1d481adf8c6cb53b097204ae0ddc48060`.
  UPS SHA-256:
  `5d890fc786e35b35ea7cee38217d9144d77d2cf3a7f46f52fa23f110cebdd316`.
  `smoke-intro-jobs-native-01` passes 59 recorded steps, loading all nine original
  drafts with complete-content and adjacent/module guards. All 139 tests pass.
- Added read-only native resident/home observations with population, ID,
  duplicate, finite-coordinate, and complete-read guards. The isolated town has
  six villagers. `smoke-space-greeting-outside-01` exits the shop and records
  all six homes in 13 steps. `smoke-space-greeting-east-01` records eleven
  navigation steps toward the nearest home. Recorded list positions are not
  asserted to be live on-screen actors; no schedule, greeting, or position is
  edited. Meeting villagers and actual FlashRAM saving remain open.

### Complete display-name API and verified native test thread

- Added the independent eight-byte name resource: 216 villager rows and 64 native
  special-actor rows representing 23 distinct names. Every identity agrees with
  the supplied English disc and legacy reference; complete source/reference and
  native table hashes guard generation. Its 2,272 bytes have SHA-256
  `261078b6c8bec7f974255ddffba8c2a570b4a2a0526ea699a3cc62ffc2b4e974`.
  VROM is `02C00000`; module header offset `3C` is independent of item offset
  `38`. Existing six-byte name APIs and saved records remain unchanged.
- The original bounded runtime loads aligned sixteen-byte row pairs, validates
  the header, and copies exactly eight bytes into caller storage. Portable tests
  cover every sixteen-bit ID, the actual special table, capacities, disabled and
  malformed resources, and adjacent guards. The module uses 5,664 bytes;
  unconfigured SHA-256 is
  `790c096f8280f362caa26b0c68dccb2dea0fc40e746d27224ecffda391bb599a`.
- `display-api-pilot` retains 10,406 ordinary edits and the 649-slot extended
  item resource. ROM SHA-256:
  `c4ca5e832a096e1bb43c6846111a887c1b395197903ca2dc2f2b67259b15872b`.
  UPS SHA-256:
  `fdf54bf80bfe547ae904c5f6738a177bbf10d16e4738b9e7976c9ed18df29c75`.
- `smoke-display-api-native-01` stops during a test-only synchronous load for
  actor `A00F`, with PC `20202020`. The captured pre-call PC is `80026084`, inside
  the native idle loop. Blocking that thread removes the scheduler's idle
  fallback. No normal gameplay name call is implicated by that injection.
  The older item-batch stop resembles it, but lacks the same saved register
  evidence and is not retroactively declared fully diagnosed.
- Added `pause_game_thread` and mandatory per-call context checks. The runner
  reaches the unmodified `game_main` entry on graph thread four using a temporary
  breakpoint before any fixture writes. It never edits thread queues or IDs to
  obtain that state. All original native-call generators and static fixtures use
  this action. Context failure tests reject arbitrary threads and changed entry
  instructions. See `specs/NATIVE_TEST_CALLS.md`.
- `smoke-display-api-native-02` passes all 1,204 recorded steps in five minutes
  thirty-three seconds: 280 native ID lookups and row loads, invalid capacities
  and IDs, null/disabled resources, header checks, guards, and checkpoint
  restoration. The initial pause happened on thread five; the runner recorded
  its transition to verified graph thread four. FlashRAM remains blank.
- Read-only live NPC traversal validates list count, cycles, actor part, pointers,
  and finite positions. Normal navigation enters and leaves Cousteau's house;
  its interior actor reports world origin rather than an approachable position.
  Outside, `smoke-space-greeting-exit-align-01` locates Cousteau near
  `(2980, 160, 1699)` and the player at `(2700, 160, 1480)`. No greeting has yet
  been claimed. All positions and schedules remain unedited.
- All 150 local tests pass. The guarded-thread repeat of the previously failing
  451-case native item batch is running; wider display consumers remain planned.

### Full dialogue names and native nameplate consumers

- `smoke-display-native-items-8-01` repeats all 451 loads from the previously
  failing native item batch using the verified graph-thread context. All 1,362
  recorded steps pass in five minutes forty-five seconds, including first item
  `1D0C`, guards, and checkpoint restoration. The older failure remains qualified
  by the absence of its pre-call thread/register evidence.
- Added `af_get_display_name`, preserving native animal-versus-special-actor
  resolution, and `af_copy_talk_name`, with complete command/cursor/1024-byte
  destination checks. Two nameplate calls and only the main-message talk-name
  call are redirected. The shared six-byte insertion and its dynamic-choice
  caller remain unchanged. Full-region external-interior-reference checks and
  per-instruction source guards cover the changed consumers. The audit also
  records all three event-overlay world-name callers, which remain native.
- The 6,240-byte module has unconfigured SHA-256
  `9ee268fbadb7d4f04a86cb0975fa52477d6ce835aa32ed0c1b2223a2790c26ab`.
  `display-pilot` retains 10,406 ordinary edits and both independent name resources.
  ROM SHA-256:
  `f15af4049e166dac689d5c3b6a57d411b3ae01a8230832b1b48c3fbcec4747f8`.
  UPS SHA-256:
  `705072e7c9af17901a478224f23f911fdc33bd7bcad429bfa8a6a7d8c160b719`.
- The first consumer run passes resolver, insertion, and nameplate setup tests,
  then exposes an incomplete synthetic graphics fixture: its descending vertex
  allocation pointer is zero. The native draw routine correctly tries to allocate
  from that supplied pointer and faults at `80090848`. The fixture now supplies
  a complete 1,536-byte two-ended graphics arena. No game-code change addresses
  that test-fixture error.
- `smoke-display-fields-native-02` and `03` each pass 222 recorded steps. The
  real nameplate renderer preserves all eight bytes of `Cousteau`, emits eight
  four-vertex loads, uses 600 display-list bytes and 512 vertex bytes, and retains
  adjacent stack and graphics-arena guards. The regions do not overlap.
  `smoke-display-fields-native-04` passes 228 steps, adding the actual `7F1B`
  command dispatch and capitalization-latch consumption. Six-byte shared choice
  insertion, disabled-resource native fallback, and exact message limits pass.
- `smoke-display-full-01` passes all 225 train-to-town steps and all ten acceptance
  checks in six minutes twenty seconds. The following arrival continuation is
  stable but stays on the platform without movement; it is not an additional
  dialogue-coverage claim. FlashRAM remains blank.
- `smoke-display-item-fields-01` passes 429 native calls, 998 memory assertions,
  and 1,629 recorded steps on the combined module in four minutes forty-three
  seconds. The full checkpoint is restored after the injected tests.
- `smoke-display-station-path-01` leaves the platform through normal controller
  movement and reaches Nook's English arrival dialogue, including `07DF` and
  `07E0`. Its final isolated capture shows the complete eight-character
  `Tom Nook` label. This checks an ordinary special-NPC nameplate, not all
  conversations or save compatibility. All 36 recorded steps complete;
  FlashRAM remains blank.
- Bounded adaptive controller navigation follows read-only player/NPC coordinates
  and stops on active dialogue, missing targets, stalled movement, or its fixed
  step limit. `smoke-space-greeting-cousteau-track-01` reaches the English first
  introduction `04E7` in sixteen movement steps. This older normal-gameplay ROM
  still has the native six-byte name and Japanese catchphrase; the latter is a
  separate general-string/field task. No actor position, schedule, or greeting
  data is written to reach the conversation. All 157 local tests pass.

### Complete default catchphrase display and debugger alignment

- Matched all 216 villager catchphrases through confirmed villager identities,
  both actual default tables, and exact legacy/reference agreement. The resource
  has 214 distinct four-byte saved keys and 216 sixteen-byte rows. Key `D0902020`
  has different English defaults for `E014` and `E0C5`; each owner resolves its
  own phrase, while an ambiguous borrowed use remains native. English custom
  text cannot match any original non-Latin key. Native saved/default fields and
  the shared choice insertion remain unchanged.
- The 3,488-byte resource uses VROM `02E00000`, module configuration offset `40`,
  and SHA-256
  `6af738a7c89ce7fea041897efd8c4f95d85732d32cd3de1a3f99aeca5163f675`.
  The module uses 7,488 bytes, unconfigured SHA-256
  `a44c3faa08486be6e3b90e637005025fe93df99de37b5ca6942737af813fffeb`.
  Its only catchphrase consumer patch redirects the main call at `800A114C`.
  The audit records the unchanged choice caller, getter, setter, and resetter.
- `catchphrase-pilot` retains all 10,406 ordinary edits and the item/display-name
  resources. ROM SHA-256:
  `a978f56a5a183a5c14fb2cdafa922bfa6c4510f2c453f85b3c485c2911622b69`.
  UPS SHA-256:
  `78864a5031a647d395206f2d3ba0022dc6823265dd319176441ece4e86b4ebf1`.
- `smoke-catchphrase-native-01` passes all 216 default loads and two borrowed
  cases, then exposes an eight-byte debugger guard-read discrepancy after a
  zero-capacity call. The observed bytes correspond to an aligned-down read,
  not the requested range. The ares GDB/cache source and an expanded synthetic
  test reproduce the missing eight-byte alignment case. The runner now aligns
  read spans to eight bytes and splits unaligned eight-byte writes into words.
  Portable read/write tests cover every offset and length from one to 33 bytes.
- The second native run passes the repaired source guard and empty-phrase
  capitalization, then rejects a negative test argument before calling game
  code. The generator now serializes signed values as their unsigned o32 words;
  the runner already sign-extends those words into MIPS registers. A generator
  test checks every call's argument range before launching the emulator.
- `smoke-catchphrase-native-03` passes all 1,505 recorded steps in four minutes
  sixteen seconds: 261 native calls and 501 memory assertions, all default
  identities, borrowed/custom text, exact 1,024-byte insertion, overflow and
  incomplete-command rejection, actual `7F1C` capitalization dispatch, unchanged
  shared insertion, disabled resources, header checks, and full restoration.
  Blank-phrase capitalization affects the following output byte, as in GameCube.
- `smoke-catchphrase-full-01` passes all 225 train-to-town steps and ten acceptance
  checks in six minutes twenty seconds. `smoke-catchphrase-display-fields-01`
  passes all 228 nameplate/insertion steps with the corrected debugger reader.
  `smoke-catchphrase-item-fields-01` passes 429 calls and 1,629 recorded steps.
  All FlashRAM files remain blank; none establishes actual game save/reload.
- Candidate generation now budgets the larger of four native catchphrase cells
  and ten maximum Latin advances. The 1,353 layout-warning candidates include
  41 additional review flags. The translation file itself remains unchanged,
  SHA-256 `30443536425c3274a814117dd1e4eea800f557c1442ff205b1cd637e6b639d33`.
  No GameCube lines, pages, timing, or font metrics change. All 171 local tests pass.
- `smoke-space-greeting-finish-01` completes Cousteau's normal introduction with
  four A presses and stops before reopening it. Nineteen steps pass; other
  introductions and later introductory jobs remain. Atomic result publication
  prevents live observers from reading a partially serialized JSON document.

### Mail representation and consumer audit

- Added a repeatable mail audit with eight exact capacity-instruction guards.
  Clear/copy use 164-byte records; header/body/footer are ten, 96, and sixteen
  bytes at offsets `2A`, `34`, and `94`. This corrects reliance on misleading
  larger offsets in some native header comments without changing game code.
- Inventoried ten loader/assembly/setter/clear/copy targets across every
  executable segment and aligned literal data. Direct counts are 17 classic
  letter assemblers, three explicit-edge-size assemblers, two each header/footer/
  body loaders, one composite assembler, 54 free-string setters, two message
  excerpt setters, 39 clear calls, and 30 copy calls. No literal pointers to
  those targets are found; inline copies and remaining consumers are not covered.
- Compared raw text sizes across eight mail banks. Of the 544 shared numeric IDs,
  170 English headers, 490 bodies, and 251 footers exceed their native destination.
  All 982 English reference records are retained separately from the native-ID
  subset. Numeric identity and raw byte size are explicitly not semantic or
  dynamic-expansion approval. Two new audit tests pass, including mutation of
  every capacity instruction. `specs/MAIL.md` records the complete text, editing,
  delivery, persistence, and reader requirements for the forthcoming design.
- Verified the independent twenty-handler mail command table and the native
  conversion loops' lack of cursor advancement for unsupported commands. The
  build now rejects main-dialogue-only opcodes in all eight mail banks. Candidate
  regeneration withholds `mailb:00BB`, whose capitalization command is not
  implemented by native mail. This prevents that candidate from reaching a
  stalled conversion path; it is not an attribution of reported legacy crashes.
- The initial 175-test run has one assertion failure: the existing dialogue-policy
  restriction test supplied invalid mail commands and consequently reached the
  new capability guard first. The fixture now uses valid plain mail bytes to
  test the same policy restriction independently; the new opcode matrix retains
  the separate rejection coverage.
- The complete rerun passes 177 tests, including the independently committed
  Xvfb display-allocation tests. The rebuilt `mail-audit-pilot` contains 10,405
  edits, with unchanged main-dialogue candidates and module code. ROM SHA-256:
  `9e1c51f79eb629d56dc2950c13f22364f1407f5f12fafe0e3c724b69a9c659f2`.
  UPS SHA-256:
  `e735de312089ecc613b1550224977152c53e4daf7c77738b96c504ccafe84336`.
  Candidate SHA-256:
  `7569be729af655f5c196c0f4ed4daac5e778710cca81280f5ea0568b784d73b8`.
  This build still requires its own gameplay regression and does not imply that
  English mail assembly, delivery, or saving is implemented.

### Complete generated-letter snapshot prototype

- Implemented a canonical 122-byte envelope with immutable catalog/template IDs,
  exact literal fields, article settings, version/kind, and CRC-16. Six full
  sixteen-byte substitutions and five composite IDs fit exactly, without
  shortening values. Empty and absent fields stay distinct. The Python codec
  and standalone C codec agree on every slot/length/article combination, random
  literal data, corruption checks, malformed payloads with recomputed checksums,
  exact capacity, rejected overflows, unchanged failure destinations, and aliasing.
- Read the actual English bank bytes and computed every possible field union in
  all twelve native reply groups. The group-selection function and start tables
  have mutation-tested guards. All composite groups fit at maximum field width;
  981 of 982 classic references fit, including 543 of the 544 native numeric IDs.
  Record `0001` requires actual field bounds and remains explicitly unresolved.
  These are capacity findings, not approved semantic matches.
- `smoke-mail-native-01` passes 878 steps and 287 injected native calls in three
  minutes fourteen seconds. It verifies all 256 dispatcher opcodes without
  invoking an unsupported token's stalled outer loop, all twenty free-string
  setters, normal conversion, header split adjustment, ordinary mail copying,
  and both directions of villager-owned mail conversion. All three test envelopes,
  including a completely full one, retain their entire encoded contents and
  adjacent guards. The machine checkpoint is restored; FlashRAM remains blank.
- `smoke-mail-audit-full-01` passes all 225 train-to-town steps and ten acceptance
  checks in six minutes twenty-two seconds. Its ROM is the mail-audit build
  recorded above. It does not establish actual save/reload or hardware operation.
- The standalone C codec cross-compiles with pinned GCC 14.2.0 for big-endian
  VR4300/o32, `-Os`, `-mfix4300`, and freestanding/no-PIC/no-library assumptions.
  The object has no undefined symbols and no data/BSS; GNU size reports 1,204
  text-category bytes. Object SHA-256:
  `8a52be441affc758885312e09cf4dd34f9a37d985da3283fc3eb41a2ae2443ab`.
  It is intentionally not linked into the resident module pending reader and
  module/test-memory integration. All 190 local tests pass.
- The next mail work is the complete record-discriminator/reader audit, immutable
  catalog construction and identity review, full-text assembly, and lossless
  editor/save integration. `specs/MAIL_SNAPSHOTS.md` documents the exact format,
  scope, unresolved record, and prohibition on rendering an envelope as text.
- Disassembled and audited the native mail viewer at VROM `007908A0`. Fifteen
  instruction guards and the complete overlay hash bind its 192-byte board
  object, embedded 164-byte mail, field offsets, read-mode branch, 10/96/16-byte
  length scans, sixteen-character/six-line body renderer, and header-split clamp.
  The clamp would erase a proposed split-byte tag before later rendering, and
  footer normalization must not consume opaque snapshot bytes. The `font` byte
  also controls empty/send/attachment state; no metadata tag is assigned yet.
  `specs/MAIL_SNAPSHOTS.md` records these integration constraints and linked
  renderer addresses without claiming a working wider viewer.
- Regenerated `build/audits/mail.json` with the complete guarded viewer and
  independent mail command table. The final full suite passes all 191 tests in
  71.417 seconds. No playable-ROM or saved-record bytes change in this viewer
  audit; its next implementation step remains the decoder/viewer integration.

### Full generated-letter assembly and captured capitalization

- Verified thirteen complete mail-related functions in the supplied GAFE01
  executable. Both article-clear and capital-clear routines are identical and
  reset only the article override. The actual release therefore retains capital
  state between insertions and letters, unlike the source's optional bug fix.
  Snapshot version two captures initial capitalization in an unused bitmap bit,
  retaining the same 122-byte size and all literal field data. Version one is an
  uninstalled prototype and is rejected rather than reinterpreted as version two.
- Implemented full-letter assembly in Python and freestanding C, with exact
  classic/composite processing order, article suppression, sticky capitalization,
  empty insertion behaviour, header split adjustment, and all explicit template
  spaces/newlines. The output holds up to 1,024 bytes and rejects overflow,
  missing fields, unsupported commands, and unsafe literal field bytes without
  partially overwriting the destination. Source buffers are not modified.
- Added a source-verified reference preparation tool with hashes for all eight
  mail banks, the decoder, thirteen executable functions, and the general-string
  article bank. It prepares 4,807 of 4,866 parts without changing glyph identity;
  59 remain explicitly rejected. The output is an ignored local reference
  bundle, not a release catalog or approved native/reference mapping.
- Python, C, and an independent in-place model agree on 6,398 retail-template
  probes and the synthetic field/length/article/capitalization matrix. The probes
  cover classic triples, diagonal composites, each native reply part selection,
  largest-field-union witnesses, and both initial states, not every composite
  combination. Fifty-eight requested combinations encounter rejected glyph rows.
  Two classic `0001` probes use ten-byte fields for formatter testing only; actual
  source bounds remain unresolved. Observed maximum header/body/footer lengths
  are 22/228/51 bytes, with a 255-byte largest aggregate result. No wording is
  shortened to the native or GameCube body storage capacity.
- The combined C implementation cross-compiles with pinned GCC 14.2.0 for
  big-endian VR4300/o32. The relocatable object has no undefined symbols or
  mutable global data/BSS; GNU size reports 2,851 text-category bytes. Object
  SHA-256: `e234b7b47461c8ed5caa48b40e6aabec7522587f2bd371803faa567c47b08d05`.
  The formatter's compiler-reported frame is 1,224 bytes; nested pack and expand
  frames are 152 and 64 bytes. This code is not installed or executed on MIPS.
- The complete local suite passes 199 tests in 77.636 seconds. Production ROM,
  font metrics/assets, and candidate imports are unchanged. The next integration
  step is the resident-module/test-memory layout, followed by actual C execution,
  immutable catalog resources, and native generator/viewer connections.
- `smoke-mail-native-v2-01` passes all 878 steps, 287 native calls, and 293 memory
  assertions in three minutes fourteen seconds. The ordinary and villager-mail
  conversions preserve version-two envelopes with initial capitalization set,
  including the fully occupied 122-byte case. Memory guards pass and the machine
  checkpoint is restored. The unchanged blank FlashRAM hash is
  `b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260`.
  This exercises native copying, not the C formatter or actual save/reload.
- Local reference-bundle SHA-256:
  `f8fa5d0c766dfa7fd520c6e051b66c5a7cf077d06777acf841211a647b94565b`.
  Native version-two scenario SHA-256:
  `8db1073fe6738a2ade24acbfc4f75074ec3ddacb11b96dadb8f9cd8f8001a937`.

### Resident mail execution and separated test memory

- Expanded the resident reservation to 32 KiB with a linker-enforced 24 KiB
  code/data/BSS limit and a separate final 8 KiB test area. Every fixture pointer,
  embedded pointer, decimal argument, return breakpoint, and stack guard moves
  together. The bootstrap loads `8000` with unsigned `ori` instructions and uses
  register addition/subtraction for the heap, avoiding signed immediate overflow.
  The heap starts at `8019C8E0`, size `00263720`, and still ends at `80400000`.
  Checks cover both startup observations and the real malloc arena start pointer.
- The builder compiles nested mail C files, hashes every nested source/header,
  rejects changed sources during compilation, and verifies no undefined symbols.
  Linked size is 10,336 bytes. Independent builds in `build/runtime-module/` and
  `build/runtime-module-mail-repeat/` produce identical module and bootstrap
  contents. Module SHA-256:
  `5c3736861c76183b592f260463234d77da0f73c064241387a4d060f41d586c69`.
  Bootstrap SHA-256:
  `f38de0d2f252c4b9c4e596d85f5ae3f66f9ac27a680d30e874d2f6f476a4cb92`.
  The previous module artifacts remain in `build/runtime-module-16k-5jmxzF/`;
  old-ROM checkpoints are not compatible with the new build.
- `build/mail-runtime-pilot/` retains 10,405 candidate edits and all three wider
  resources, with unchanged production font assets/metrics and reference layout.
  ROM SHA-256:
  `f23a5d8efafafe5ed1e29cd6ae0df896d68da56b4410d1378630c10dbe276779`.
  UPS SHA-256:
  `bfb45be1798d1767811323db2a3526e65538e5b6b57219ac076bbecb7949489c`.
  The independent mail import gate still withholds `mailb:00BB`: installed APIs
  do not make the native mail generator call them.
- Added big-endian o32 fixture serializers for the 380-byte decoded record,
  68-byte pointer-bearing template structure, and 1,040-byte complete output.
  `smoke-mail-codec-native-01` passes 215 resident calls, 303 memory assertions,
  and 779 steps in two minutes 44.265 seconds. It tests every slot, all field
  lengths, unaligned wire buffers, full envelopes, per-byte corruption, rejected
  capacities/catalogs, unchanged failure output, and overlapping buffers.
- `smoke-mail-format-native-01` passes 350 resident calls, 544 assertions, and
  1,652 steps in four minutes 36.453 seconds. Complete assembly preserves exact
  header/body/footer contents and layout metadata, including all 256 opcodes,
  captured capitalization/articles, explicit newlines, rejection, and aliasing.
  Source, output, low/high stack, and module guards pass.
- `smoke-mail-reference-native-01` passes 92 resident calls, 280 assertions, and
  611 steps in one minute 33.137 seconds. The 46 source-verified English cases
  cover output-length witnesses, all twelve native reply groups, both capital
  states, and two classic `0001` probes whose actual field-width bounds remain
  unresolved. These are isolated API calls, not real generated/read/saved mail.
  All three native API runs restore the machine checkpoint, with blank FlashRAM
  SHA-256 `b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260`.
- The first boot attempt fails at the debugger connection before CPU assertions,
  with a still-starting emulator. A bounded socket-readiness wait now retries
  only while that exact process remains live, without restarting it. Synthetic
  tests cover delay, process exit, deadline, and unexpected protocol failures.
  `smoke-mail-runtime-boot-02` passes 13 steps in 28.687 seconds.
- The initial full run, `smoke-mail-runtime-full-01`, exits normally after 226
  steps in six minutes 28.159 seconds, with all memory assertions passing, but
  fails the independent arrival acceptance check. Its fixed button sequence
  ends during `2AD2`, before town arrival. An initial chat update prematurely
  called this a full pass; the subsequent correction distinguishes process
  survival from acceptance. The matching-ROM checkpoint continuation,
  `smoke-mail-runtime-arrival-01`, reaches live `07DD` after five ordinary button
  presses, with all seven memory assertions passing across 25 steps in 26.216
  seconds. The earlier chat's four-press count was incorrect.
- The full scenario now ends with a bounded, observed arrival action. It never
  presses past the target message, rejects unexpected active choices, and fails
  when its press limit is exhausted. Three synthetic tests cover these cases and
  invalid limits. The independent ten-check acceptance validator is unchanged.
- The first complete layout test run passes 206 tests in 156.703 seconds.
  The complete rerun with the arrival helper passes 209 tests in 92.703 seconds.
  An independent full-ROM rebuild in `build/mail-runtime-repeat/` produces the
  same ROM and UPS hashes, using the independently rebuilt module artifacts.
  Generation hooks, immutable catalogs and identity review, native full-text
  readers, editing, delivery, real saving, and original hardware remain required.

Generated assets, logs, screenshots, ROMs, patches, and reference text remain
local under ignored `build/` and `local/` paths. Current status belongs in
`PROGRESS.md`; this file records completed work and test observations.
