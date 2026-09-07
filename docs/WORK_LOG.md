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
- `smoke-mail-runtime-items-01` passes the existing wider-item consumer regression
  against the new module and alias resource: 429 native calls, 998 assertions,
  and 1,629 recorded steps in four minutes 44.208 seconds. All five main-message
  fields, the item-ID wrapper, actual DMA, capitalization, exact output limits,
  fallback, and guards pass. The machine checkpoint is restored. This verifies
  that moving the linked code/BSS and isolated fixtures preserves these callers;
  it does not approve the other direct item-name destinations.
- `smoke-mail-runtime-display-01` passes 37 native calls, 98 assertions, and 228
  steps in 43.487 seconds. Complete main-message/nameplate output, centering,
  eight rendered character quads, exact message limits, and stack/graphics/module
  guards pass with the expanded module. The machine checkpoint is restored, and
  FlashRAM remains blank.
- `smoke-mail-runtime-full-02` reaches live `07DD` at recorded steps 201 and 204,
  but the retained fixed press sequence closes it before the appended arrival
  action begins. That action correctly refuses the stale, closed message and
  exhausts its limit; the run fails after eight minutes 3.732 seconds. This is a
  test-sequencing failure, not a passing full run or a demonstrated ROM crash.
  The fixed post-town loop is replaced by the observed arrival helper itself.
  It may choose the first option only in the four observed train prompts
  `2AE4`, `2ACB`, `2ACC`, and `2AD1`, with a live message and cursor zero. It stops
  at arrival before another press. Five synthetic tests cover bounds, explicit
  choice permission, unexpected prompts/cursors, and stale loaded state.
- The full suite with explicit train-choice permissions passes 211 tests in
  88.746 seconds. The emulator runner changes no gameplay code, saved data,
  reference line breaks, or dialogue timing.
- Extended the native viewer audit to its five-entry state table, read-wait,
  edit-acceptance, end-callback, dispatcher, and destructor functions. State two
  handles A/B/START through a shared transition callback; state three performs
  the persistent mail copy and header/footer preference writes. The destructor
  only clears the board pointer. Instruction and state-table mutation tests now
  bypass the full hash deliberately to verify the individual guards themselves.
  Shared submenu callback effects and opening callers remain unapproved; these
  observations do not install a snapshot viewer or authorize saved-record tags.
- `smoke-mail-runtime-catchphrases-01` passes all 261 native calls, 501 assertions,
  and 1,505 steps in four minutes 16.955 seconds. All 216 default rows, wider main
  insertion, unchanged four-byte saved/custom values, ambiguous-default fallback,
  capitalization, exact limits, and guards retain their previous behaviour with
  the expanded module. The checkpoint is restored. The viewer audit's three
  targeted tests also pass in 12.625 seconds, and its local report is regenerated.
- `smoke-mail-runtime-full-03` passes the fresh complete train-to-town regression
  in six minutes 1.620 seconds: 188 recorded steps, all ten independent acceptance
  checks, and all seven memory assertions. The observed post-town sequence uses
  thirty ordinary presses, accepts only the four expected first choices, and
  stops on live `07DD`. The actual malloc arena starts at `8019C8E0`; four-MiB
  size, reduced heap size, ready/header values, and `AF32C0DE` guards all pass.
  The smaller step count removes fixed-loop screenshot records, not acceptance
  checks. The checkpoint belongs to the new ROM and ends at arrival; FlashRAM
  is still blank. This is not game-save/reload or hardware validation.
  GitHub confirms `TheDiscordian/doubutsu-no-mori-english` remains private.

### Immutable cartridge catalog and complete letter restoration

- Registered experimental catalog two with immutable format/assembly semantics,
  complete resource/payload hashes, all eight original bank counts, and explicit
  unavailable indices. The local builder preserves all 4,866 indices and 4,807
  complete available parts; 59 parts still require glyph support. Proposed or
  changed catalogs cannot be installed. Registration does not approve native
  semantic matches, and future wording/encoding changes require a new identity.
  The resource is 319,344 bytes. Complete SHA-256:
  `d77591525d105391cf8190257b8ea768f521810d4ae5a36d27bcca991442a5e1`.
  Payload SHA-256:
  `a042bd72f6158472722717dd3f19e761ea693ce632ae51acc9aca26c4d99c385`.
  Independent catalog builds compare equal.
- Added the optional VROM `03000000` resource and resident configuration word
  `44`, preserving the other three configured resources and verifying the
  complete module before installation. The reader validates the saved envelope,
  immutable header, selected directories/rows, DMA results, lengths, padding,
  field masks, and CRCs before full-letter assembly. Failures leave the saved
  envelope and published output unchanged. The caller-owned o32 workspace is
  3,552 bytes, including 3,104 bytes for source text and DMA alignment gaps.
- Host C restoration agrees with the independent reference model on 6,398
  probes, including both capitalization states. Fault tests cover each selected
  DMA failure, damaged tables/data, missing fields, unavailable IDs, malformed
  headers, aliasing, alignment, and disabled resources. The complete suite passes
  219 tests in 88.720 seconds. A subsequent strict snapshot-kind validation check
  passes the eight targeted catalog tests in 2.846 seconds. The final full suite,
  including catalog source/symbol inventory checks, passes all 219 tests in
  78.362 seconds; the four targeted runtime-layout checks also pass.
- `smoke-mail-catalog-native-01` passes 84 actual N64 CPU calls, 259 assertions,
  and 540 recorded steps in one minute 24.602 seconds. Forty-six verified
  English reference cases restore through real cartridge reads, including both
  captured capitalization states and unaligned envelopes. Unknown/unavailable
  identities, disabled configuration, every header-word mutation, complete
  output, and source/stack/module guards are checked. The checkpoint is restored;
  FlashRAM remains blank. This does not exercise ordinary mail generation or
  saving. Scenario SHA-256:
  `934f4e2e7e0d42ff8b0cbb91860c234bd73c3d2ab88ed736586bc3a2166bdbb1`.
- The three freestanding mail objects cross-compile without undefined symbols,
  data, or BSS, with 4,403 text-category bytes. Combined object SHA-256:
  `8d0ea79219509c9f34a0c122572e701161eca4dd6706c35dcfa7193c860ed68d`.
  Compiler stack frames are restoration 256, DMA wrapper 24, assembly 1,224,
  packing 152, and unpacking 408 bytes. Real gameplay caller depth still needs
  validation; the workspace must not be allocated on a small nested stack.
- The resident module occupies 11,872 linked bytes within the unchanged 32 KiB
  reservation. Independent builds compare equal for both module and bootstrap.
  Module SHA-256:
  `f3ed2863d70ea86fd9ebdb4fad41b7abdc89d777bcf03093c0dd57e7a1dc6467`.
  Bootstrap SHA-256:
  `f38de0d2f252c4b9c4e596d85f5ae3f66f9ac27a680d30e874d2f6f476a4cb92`.
  The preceding module remains in `build/runtime-module-pre-catalog-7BtqxP/`.
- `build/mail-catalog-pilot/` preserves the 10,405 candidate edits, approved
  font/metrics, reference layout, and all three wider-name resources. ROM SHA-256:
  `4142659eaba13e2b18b74ddbdafbe9658a8320182f310e51db7b50c79fe4f3d1`.
  UPS SHA-256:
  `9fc78e0a78b444b15fec8046643b549dc8ba415f56438ab3ac74325da66c13ac`.
  The independent build in `build/mail-catalog-repeat-pilot/`, using independently
  rebuilt module and catalog artifacts, produces identical ROM and UPS contents.
- `smoke-mail-catalog-full-01` passes the fresh train-to-town regression in six
  minutes 4.839 seconds: 190 recorded steps and all ten independent acceptance
  checks. Four-MiB memory, the real reduced malloc arena, and runtime guards pass.
  The checkpoint belongs to this ROM and reaches live arrival dialogue `07DD`.
  Game-save/reload and original hardware remain unvalidated. Native mail
  discrimination, semantic matches, generation, full-text viewing, editing, and
  persistence remain required; gameplay does not yet call the restoration API.

### Read-only English mail layout and actual letter-window checks

- Added an optional read-only body/footer renderer using the approved native
  proportional advances. It preserves explicit newlines, blank lines, spaces,
  six lines, sixteen-pixel line spacing, and the 192-pixel paper width. The
  footer aligns using its complete measured width. No font pixels, metrics,
  reference wording, editor fields, or saved representation change. The actual
  English executable's line/body/footer routines and width helper were checked
  against the reference source; their hashes are recorded in `MAIL_VIEW.md`.
- Only two native board JALs change. Their two obsolete `R_MIPS_26` entries are
  removed, with the other fifty relocation entries, section sizes, file length,
  and trailing size word preserved. Original overlay and relocation hashes,
  exact calls, linked targets, and source-matched module bytes gate installation.
  Read-open mode one selects the new functions; other modes tail-call the
  unchanged original functions using the loaded caller's return address.
- The four mail objects cross-compile without undefined symbols, mutable data,
  or BSS. Combined object SHA-256:
  `609b168d01685d3ced2e7bf4342f576dfff8577b29d2c8334a040e72904a44c8`.
  Text-category size is 5,615 bytes. Compiler stack frames for drawing, line
  scanning, body, and footer are 64, 48, 192, and 72 bytes. This is not a whole
  gameplay call-stack high-water measurement. An initial host-test adapter macro
  collided with the line structure's width member and was renamed. The stale
  module/source guard correctly rejected installation until the module rebuilt.
- `smoke-mail-view-native-02` passes 22 N64 CPU calls, 328 memory assertions,
  and 425 recorded steps. It executes the real font renderer and verifies 264
  vertex coordinates across 66 glyphs, graphics bounds, source preservation,
  and stack/module guards. Cases include 33 Latin characters continuing onto
  another line, narrow text remaining together, explicit blank lines/spaces,
  and the footer's exact right edge. Eight non-read shim probes forward the
  arguments to isolated recorder stubs; those probes do not execute the native
  editor itself. The complete machine checkpoint is restored.
- `smoke-mail-view-open-01` opened and closed a synthetic ordinary letter through
  the actual submenu loader and observed unchanged letter/preference bytes.
  However, its loose breakpoint logging allowed out-of-order stop responses;
  that run is not accepted as proof of execution at the new hooks. The stricter
  `open-02` run rejected an invalid bulk-register response. Installing a hook
  breakpoint while the game was running allowed a stop before the next continue
  packet, leaving another stop response queued. The test now pauses at the
  verified graph-frame entry first, checks every breakpoint reply and exact
  program counter, and records raw replies before validating them. No ROM change
  was needed for this test-protocol correction.
- `smoke-mail-view-open-03` passes 56 recorded steps. Three separate ordinary
  synthetic letters open through native `800C4DD8`, use the actual loaded and
  relocated submenu/board overlays, and reach both resident hook PCs each time:
  `80194C5C` and `80194C80`. A, B, and START each close the window. All three
  checks preserve the complete 164-byte source letter and the player's 28-byte
  header/footer preferences. Wait state two, read mode one, source pointers,
  full field lengths, and installed JALs are verified. The matching-ROM machine
  checkpoint is restored; FlashRAM remains blank. This is an injected open
  request, not ordinary delivery, inventory selection, saving, or hardware proof.
- The module occupies 13,184 linked bytes within the unchanged 32 KiB
  reservation, with eight KiB separately reserved for tests. Independent module
  and bootstrap builds compare equal. Module SHA-256:
  `8259c1571e5ab0034358c14b7aeadb8742868ee92b4da6a8710a81d0908969a1`.
  Bootstrap SHA-256:
  `f38de0d2f252c4b9c4e596d85f5ae3f66f9ac27a680d30e874d2f6f476a4cb92`.
  The previous module remains in `build/runtime-module-pre-view-qNB74J/`.
- `build/mail-view-pilot/` retains 10,405 candidate edits and all four optional
  resources. ROM SHA-256:
  `7e99d9e4e4e5799a7533d432dbf11619bba99941afd7aeeb74dba85c80423532`.
  UPS SHA-256:
  `176d5639344ab11ac11e120ff4ae8df906053bce5e157096d410c711970f7ba8`.
  Independent builds in `build/mail-view-repeat-pilot/` compare equal. The fresh
  `smoke-mail-view-full-01` train-to-town run passes 188 recorded steps and all
  ten independent acceptance checks. Four-MiB memory, actual reduced malloc
  arena, module readiness, and guards pass. Its matching checkpoint ends on
  live arrival dialogue `07DD`; game-save/reload remains unvalidated.
- The layout hooks still read native 96/16-byte body/footer fields. Full snapshot
  decoding before normalization, a validated record discriminator, semantic
  template matches, generation, longer-text viewing, custom editing, delivery,
  and persistence remain required. This milestone does not complete mail or the
  translation project.
- The final full host suite passes 231 tests in 63.066 seconds, including the
  three-button scenario's paused-breakpoint ordering and strict reply checks.
  Earlier 226- and 230-test runs also passed before the final probe additions.

### Complete snapshot-letter reading and pagination

- Connected catalog restoration to the native board copy at `8088A47C`, before
  native field scanning, split clamping, or footer normalization. The guarded
  delay slot supplies the real menu pointer. A separately enabled experimental
  reader recognizes split marker `80`, decodes into resident display state, and
  blanks only the temporary board text fields. Source metadata, the complete
  snapshot, and saved header/footer preferences remain unchanged. No native
  generator emits this marker; other-reader/discriminator and save approval
  remain required before release. Generated snapshots are read-only pending
  lossless editor integration; invalid snapshots show an explicit error.
- Added complete measured-width pagination without word reflow or whitespace
  trimming. A one-line header repeats; longer headers continue before the body.
  Body rows retain the native six-line geometry. Complete signatures wrap,
  right-align, and move to continuation pages when necessary. D-pad Left/Right
  changes pages without fresh DMA. A/B/START preserve native closing and take
  priority over simultaneous page input. The input hook verifies the active
  cached board and read-open mode, preventing an old cache from taking page input.
- Checked 6,398 reference assembly probes for layout pressure: no header exceeds
  192 pixels with the six-byte test recipient; 2,322 bodies and 754 signatures
  contain a wider line before pixel wrapping. Maximum observed line widths are
  162, 424, and 304 pixels for header/body/footer. These are probe observations,
  not semantic-match approvals or exhaustive dynamic-field combinations. Classic
  `0001` retains its explicitly limited ten-byte probe and actual-source-bound
  requirement. The full host reader preserves every body/signature character in
  all 6,398 probes, including both captured capitalization states and all pages.
- Added the native header and trigger calls alongside the copy hook. Exactly
  five board JALs change. Only three local-call relocation entries are removed;
  the other forty-nine, file lengths, original functions, and delay slots remain.
  A separate installer test restores the five original calls and compares the
  complete overlay, while also checking every retained relocation entry.
- The first native compile exposed compiler-generated `memset`/`memcpy`
  dependencies from aggregate initialization/assignment in the page builder.
  Explicit bounded byte loops replace those operations. The final six mail
  objects compile without undefined symbols or mutable globals other than the
  exact 5,792-byte reader cache. Combined object SHA-256:
  `30599b8be50a2ed3c896aa795421796f0520c265c5aa8b3a47741674c4ee548d`.
  Text-category size is 9,308 bytes. Compiler frames include page construction
  496, reader copy 40, page selection 48, header drawing 120, trigger 32, and
  font adapter 64 bytes. The 3,552-byte DMA workspace is in the cache, not a
  nested native stack. This is not a measured whole-game stack high-water bound.
- `smoke-mail-reader-open-01` passes four actual long-reference window opens,
  eight pages, 1,080 glyphs, 4,320 vertex positions, all forward/backward page
  checks, and four unchanged source/preference checks across 120 recorded steps.
  Bodies contain 228, 174, 199, and 159 bytes; signatures contain 22, 51, 26,
  and 37 bytes. The decoder is called by actual native initialization, and
  entry/return breakpoints enclose real font drawing. The observed font arena
  retains at least 59,808 free bytes after those complete page draws. This run
  precedes the additional active-board input guard, which is revalidated on its
  own freshly built ROM and matching checkpoint.
- The final resident module occupies 22,688 linked bytes including display BSS,
  within the unchanged 32 KiB reservation and separate final eight-KiB test area.
  Independent module/bootstrap builds compare equal. Module SHA-256:
  `fa77b89c90a26cc4651de0f8635a7b1849c335580cb6a78d3ab27ff388806ebd`.
  Bootstrap SHA-256:
  `f38de0d2f252c4b9c4e596d85f5ae3f66f9ac27a680d30e874d2f6f476a4cb92`.
  The previous experimental module remains in `build/runtime-module-pre-reader-UppdtK/`.
- `build/mail-reader-final-pilot/` retains the 10,405 candidate edits, approved
  font/metrics, and all four optional resources. ROM SHA-256:
  `344e91d72b3b62f16ea97b076486e24471b1c039be0b0ee0f7c4984b98658e0e`.
  UPS SHA-256:
  `bce41a957f88bbc04791049573f3039cdbfc7dd75ea7c5aeb6d009a3ed2665bc`.
  Independent module and ROM builds in `build/runtime-module-reader-repeat/`
  and `build/mail-reader-repeat-pilot/` produce identical artifacts.
- Both fresh `smoke-mail-reader-full-01` and `full-02` train-to-town runs pass
  188 recorded steps and all ten acceptance checks on their respective ROMs.
  The final-ROM checkpoint belongs only to `full-02`. Four-MiB size, actual
  reduced malloc arena, module header/readiness, and guards pass. FlashRAM is
  blank; these checkpoints are not game-save/reload validation.
- The initial complete host suites pass 239 tests in 70.789 seconds and 244
  tests in 72.293 seconds. The additional all-reference reader test passes with
  the four other reader tests in 1.149 seconds. Tests of cache ABI/bounds,
  incomplete page traversal, ordinary-record fallback, explicit tag permission,
  and snapshot-only edit-open permission also pass.
- `smoke-mail-reader-open-02` passes on the final ROM: 156 recorded steps,
  six window opens, ten pages, 1,134 glyphs, and 4,536 vertex positions. All four
  complete reference letters remain intact across paging. The fourth requests
  edit-open mode two and reaches read-only mode one safely. A bad checksum and
  an unknown catalog display the real error glyphs without rendering snapshot
  bytes. All six source/preference checks pass, the checkpoint is restored,
  and FlashRAM remains blank. The minimum observed free graphics gap is 59,808
  bytes after a complete page draw. This is not delivery or game-save evidence.
- `smoke-mail-reader-ordinary-01` passes all three ordinary letter open/close
  cycles in 56 recorded steps, including actual body/footer hook PCs, A/B/START,
  unchanged source/preferences, and checkpoint restoration. The separate layout
  regression in `smoke-mail-reader-layout-01` passes 554 steps and 28 native
  calls, extending previous body/footer checks with ordinary recipient insertion,
  special no-recipient headers, and all three non-read tail shims. Every new
  header glyph quad and the complete stack/graphics/module guards pass.
- The final full suite passes 245 tests in 69.848 seconds. The optional reader
  remains experimental: semantic identity review, full metadata/other-reader
  handling, native generation, lossless editing, delivery, actual saving,
  original hardware, and public release preparation remain required.

### Gyroid owner-message wrapping and actual NPC letter-reader distinction

- Traced both `mMsg_Set_mail_str` callers through their actual MIPS arguments.
  The sample actor supplies static sixty-four-byte text; the home gyroid supplies
  its saved owner message, not `Mail_c` text. Added complete caller-file and
  instruction guards, corrected the mail-audit classification, and documented
  the still-separate saved-message/editor capacity. No snapshot decoder is
  installed at this unrelated routine.
- Implemented the English reference's after-glyph `width > 186` wrapping rule
  using the actual native font width routine. Manual/blank lines and spaces stay
  intact. The destination remains sixty-eight bytes and both callers still
  supply sixty-four saved/static bytes. Output staging preserves overlapping
  source/destination and rejects invalid widths without partial output. The
  original row limit is retained; no wider default/custom text is imported.
- Disassembled the supplied 300-byte PowerPC formatter to verify capacity,
  proportional width mode, strict threshold, and row limits. Host comparisons
  execute the unchanged pinned reference C function with the native destination
  layout/capacity. All 3,000 varied-width cases agree. All 256 byte values,
  lengths through sixty-eight, explicit newlines, boundary widths, invalid
  inputs, and source overlaps pass separate tests. Instruction mutations fail
  independently of the containing hashes. An initial reference compilation
  rejected its `for (dst; ...)` no-effect expression under `-Werror`; only that
  warning is permitted for the unchanged local reference, not production code.
- The new N64 function is 400 bytes, with a 128-byte frame, no undefined
  symbols, and no mutable globals. Linked module size is 23,104 bytes, an
  increase of 416 including alignment; the 32 KiB reservation and final 8 KiB
  test area remain unchanged. Independent module builds match. Module SHA-256:
  `bbf7b6cabd88d9558c499656c629d978d995c8240c493d7522415b538ad0343a`.
  Bootstrap SHA-256 remains
  `f38de0d2f252c4b9c4e596d85f5ae3f66f9ac27a680d30e874d2f6f476a4cb92`.
  The default module artifacts match `build/runtime-module-gyroid/`; the
  previous reader module remains in `build/runtime-module-reader-repeat/`.
- `build/gyroid-message-pilot/` retains all 10,405 edits, four optional resources,
  approved font/metrics, and full snapshot reader. ROM SHA-256:
  `1e008a8e6da7f3b800c16b2d777ca2003a618c084e785d68af626b1345833f1a`.
  UPS SHA-256:
  `e2309bae9e124ed3a7bb24a7d01bec47fb6d3f142aa83038b777859ea47c2fca`.
  The independent `build/gyroid-message-repeat-pilot/` has identical artifacts.
- `smoke-gyroid-message-full-01` passes 188 recorded train-to-town steps and all
  ten acceptance checks. Four-MiB memory, module readiness, actual reduced malloc
  arena, and module guards pass. This is the matching-ROM town checkpoint;
  FlashRAM remains blank, not a validated game save.
- `smoke-gyroid-message-native-01` passes 297 steps: thirty-eight installed
  setter calls and nine actual native dialogue-insertion calls, with 165
  assertions. Exact 1,024-byte message insertion, every output/source byte,
  overlapping sources, negative/oversized lengths, invalid pointers/slots, and
  stack/module guards pass. This run starts fresh, pauses the verified graph
  thread, uses isolated fixtures, and restores its checkpoint. It does not
  simulate a normal visit to another player's home gyroid.
- `smoke-gyroid-message-reader-01` passes all six real letter-window probes
  across 156 steps, including full-reference pagination, corrupt-record errors,
  unchanged sources/preferences, and the read-only edit-open safeguard.
  `smoke-gyroid-message-layout-01` passes 554 steps, twenty-eight native calls,
  and 436 assertions covering ordinary headers, measured body/footer vertices,
  non-read forwarding, and stack/graphics/module guards. Both restore the
  matching town checkpoint and leave FlashRAM blank.
- The initial complete host suite passes 251 tests in 79.119 seconds. The
  additional native-scenario mutation guard also passes with all six gyroid
  tests, for seven targeted tests in 3.220 seconds.
  The final full suite passes 252 tests in 71.214 seconds.
- Traced actual NPC letter consumption independently: the send path passes
  `Mail_c+34` to reply grading and later to letter-quest scoring. The GameCube
  ordinary reply uses its seven-check English scorer, but its quest helper still
  uses the separate length/word-hit grader. Recorded function hashes and call
  sites in `specs/MAIL_NPC.md`. Neither path is ported or snapshot-aware yet;
  native snapshot generation remains disabled. Normal delivery, lossless editing,
  saving, the longer gyroid default, and hardware validation remain required.

### English ordinary reply scoring and bounded letter-quest word tables

- Ported the seven-rule GAFE01 ordinary reply scorer and retained the separate
  native letter-quest length/rate/repetition/rank path. The source-verified
  prefix extraction includes all 776 pairs in twenty-six explicitly bounded
  tables, preventing reads into adjacent tables. Extracted data remains local.
  Native ninety-six-byte bodies receive virtual 192-byte space padding; a
  separate complete-body API accepts up to 1,024 ordinary text bytes. No
  snapshot decoder or generated-mail delivery hook is enabled by this change.
- The new overlay uses the original 5,808-byte mail-check allocation and
  592-byte relocation allocation. It occupies 4,064 linked bytes without BSS.
  The original two-argument loader entry remains at linked `80A94D0C`.
  Twenty-four Fado relocation entries use 128 bytes before padding. Compiler
  flags enforce compatible high/low address pairs, and the linker explicitly
  aligns each object's sections. The host model checks entry jumps, pairs,
  section sizes, padding, targets, order, and four-MiB placement.
- Initial overlay extraction exposed a non-allocatable `.ovl` section and an
  unaligned text-to-rodata gap. Explicit objcopy section flags and per-object
  linker alignment corrected those build failures before native execution.
  The pinned Fado tool is built locally from the existing submodule without
  editing or installing tool sources. Reports include C, header, and included
  data/version-source hashes.
- The resident adapter adds 320 bytes, for 23,424 linked bytes within the
  unchanged 32 KiB reservation and separate 8 KiB test area. Its checked
  allocation includes both overlay and relocation workspace, avoiding a second
  unchecked allocation in the native loader. It invokes the native DMA,
  relocation, and cache-maintenance path, frees temporary storage, and returns
  neutral on allocation failure or an absent English overlay. The old quest
  loader retains its original allocation behaviour.
- All seven score components and the separate legacy grade agree with 3,000
  independent host executions of pinned GameCube C. The reference fixture
  uses its `BUGFIXES` bounds, one pointer-width portability adjustment, and an
  explicit terminator for `x`: the source's existing fix still permits `Xen`
  to spill into the `y` table otherwise. Empty input receives a safe preceding
  space in the reference fixture; the port does not read before the body.
  These are host reference comparisons, not GameCube CPU execution.
- All 776 prefixes in both permitted first-letter cases, 1,000 varied-length
  Python-model comparisons, exact 49/50/99/100 rank thresholds, source/output
  guards, invalid arguments, and allocation ownership pass. AddressSanitizer
  and UndefinedBehaviourSanitizer pass eight patterns for every length from
  zero through 1,024 using exact-sized heap allocations. Relocation/installer
  mutations reject stale artifacts and sources, missing or malformed entries,
  wrong ABI, bad module targets, and overlaps without publishing partial edits.
  The targeted suite passes seventeen tests in 2.442 seconds. The complete
  suite passes 269 tests in 74.071 seconds.
- `smoke-mail-grading-native-01` passes 327 recorded steps, ninety-one actual
  N64 calls, and 157 memory assertions. It exercises the installed ordinary
  grader, complete-body API, unchanged native word-loader entry, native length
  grader, quest rank with/without gifts, and local reply condition flags.
  Complete sources, stack guards, module guards, and output buffers pass.
  It uses isolated test memory and restores its fresh-boot checkpoint.
- `smoke-mail-grading-full-01` passes 188 train-to-town steps and all ten
  acceptance checks, including four-MiB configuration, long choices, arrival,
  and memory guards. This is the matching-ROM town checkpoint.
  `smoke-mail-grading-reader-01` passes 156 steps, six full-letter windows,
  ten pages, 1,134 glyphs, and 4,536 vertex coordinates. All six source letters
  and preferences remain unchanged. Both native and window tests shut down
  cleanly. All FlashRAM files remain blank, not actual save/reload evidence.
- The original, repeated, and final pilot builds retain 10,405 candidate edits,
  all four optional resources, approved font/metrics, and full snapshot reader.
  Independent overlay, relocation, module, ROM, and UPS outputs match.
  The current source-bound reports are in `build/mail-grading/`,
  `build/runtime-module/`, and `build/mail-grading-final-pilot/`.
  The previous resident module remains in `build/runtime-module-gyroid/`.
  Artifact SHA-256 values:

  - Prefix blob: `ea42bb88f4d8b0649550fc90923cfa8f2862311501168c6e9a6f954b578b6ae7`.
  - Overlay: `ad74645e6ea19f864e697db220e614194eb01e52ceacdc90e3cce77722f80513`.
  - Relocations: `00a5eb11061a591500e06b884e6516dc226307837835b3ff2332f268b9f03421`.
  - Resident module: `ed322b018b368ae591ec8ce77f04d30485365643862fa2798e2505e1061d34d3`.
  - ROM: `3b3bf194d3eef069e1c87678881342b9db444b1a27f77a4318515f4828389bf1`.
  - UPS: `15d168ce73eaf975c3bc0c12122f49789ff5f86d10d9d6ce33a58af2e6077cc4`.
- Reproduced the direct-call inventory: ordinary entry at two local/visitor
  callers; length grade at the old ordinary entry and separate quest helper;
  word-rate loader only inside the length grader. No aligned literal pointers
  match these three targets. The guarded audit is reproducible through
  `tools/audit_mail_grading.py`; computed pointers remain a separate audit.
  Native generation stays disabled until complete-record discrimination and
  reply/quest decoding are safe. Visitor outcomes, actual delivery/friendship,
  semantic template approvals, custom editing, saving, hardware validation,
  and the remaining translation work are not marked complete.

### Complete-letter NPC sending and post-office failure retention

- Connected complete-record decoding to the actual NPC send entry at `800A8868`.
  The wrapper validates and assembles tagged letters before any NPC mutation,
  computes separate ordinary and legacy grades across the complete body, and
  frees its temporary allocation before calling the original send routine.
  An exact-pointer context supplies those values to both existing body consumers
  and restores any previous context afterwards. Ordinary mail bypasses decoding.
  The original reply, friendship, date, quest, gift, and first-job code remains.
- Audited the actual post-office receipt checker and found it discards NPC mail
  without checking the send result. A guarded twenty-four-byte shim now lets
  successful sends clear/count normally and returns failures through the existing
  epilogue without clearing the letter or incrementing counters. The public
  `mPO_receipt_proc` path with send type zero propagates this result. The other
  receipt modes and ordinary Pelly UI still require gameplay validation.
- Added source-hash, displaced-instruction, trampoline, target-bound, prerequisite,
  and overlap checks before any installer changes are published. The reference
  inventory verifies eight entry points across all DMA files, including the one
  direct NPC send caller. No aligned literal pointers match these entries;
  computed indirect references remain unproven.
- Host tests pass every one of the 6,398 full-reference cases, checking both
  grades and non-space counts without changing the source. Other tests cover
  ordinary fallback, unaligned allocations, nested contexts, unrelated body
  pointers, bad envelopes/catalogs/fonts, selected DMA failures, and failure of
  the second grader allocation. All failures free their storage and avoid
  native sending. An initial DMA-failure test accumulated read counts across
  cases; resetting that test counter corrected the overlong injection range.
  The final complete suite passes 281 tests in 180.694 seconds.
- The first controlled N64 send test exposed an incorrect expected visitor date
  in the fixture: native invalid time is `00FFFFFF`, not zero. The guarded native
  date constant at `80117AE8` now supplies the expectation. No production change
  was needed for that mismatch. The corrected pre-post-office run,
  `smoke-mail-npc-sends-02`, passes twenty-six cases, sixty-six native calls,
  231 assertions, and 508 steps. Its failed predecessor remains local evidence.
- The final combined build's `smoke-mail-npc-post-full-01` passes 188 train-to-town
  steps and all ten acceptance checks. Four-MiB configuration, approved font and
  input, actual reduced malloc arena, and module guards pass. This run supplies
  the matching-ROM town checkpoint for the following tests.
- `smoke-mail-npc-post-sends-01` passes thirty-two cases, eighty actual native
  calls, 313 assertions, and 649 steps. Twenty long-letter cases cover both
  record kinds and all ordinary ranks across local, visitor, quest, and gift
  paths. Two ordinary-letter and four rejection cases also pass. Six additional
  cases call the public post-office receipt function: two successful letters
  clear/count correctly and four rejected letters remain intact with unchanged
  counters and a failure return. Exact affected/unrelated NPC and player state,
  saved compact-letter text, dates, flags, friendship, quest score, source records,
  scoped context, and stack/module guards pass. The original prize function runs;
  its random selected item is recorded, not independently predicted.
- The isolated fixture clears the first-job event only for native send testing
  and restores the complete machine checkpoint afterwards. It does not establish
  normal introductory-job completion or ordinary post-office UI progression.
  Every test FlashRAM remains blank with SHA-256
  `b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260`.
- `smoke-mail-npc-post-reader-01` passes all six actual letter windows across
  156 steps, ten pages, 1,134 glyphs, and 4,536 vertex positions. Full reference
  text, error letters, edit-open safeguarding, sources/preferences, and guards
  pass on the final matching-ROM checkpoint. Both final runs restore their
  checkpoints and shut down cleanly. Earlier pre-post-office native grading and
  reader regressions also pass in `smoke-mail-npc-grade-01` and
  `smoke-mail-npc-reader-01`.
- Resident linked usage is 24,256 bytes, leaving 320 bytes before the separate
  final 8 KiB test area in the unchanged 32 KiB reservation. The send workspace
  requests 4,607 bytes including alignment; concurrent grading storage brings
  peak requested temporary allocation to 11,007 bytes before allocator overhead.
  Compiler stack-usage reports record the send frame at 96 bytes, restoration
  at 256, formatting at 1,224, expansion at 64, and unpacking at 408. Unpacking
  finishes before formatting. Native tests also verify a guard 3,072 bytes below
  the injected test stack; this does not prove a whole-game stack maximum.
- Independent module, ROM, and UPS rebuilds match. The source-bound module is
  in `build/runtime-module/`, repeated in `build/runtime-module-mail-npc-repeat/`.
  The final and repeated pilots are `build/mail-npc-post-pilot/` and
  `build/mail-npc-post-repeat-pilot/`. They retain all 10,405 candidate edits,
  four optional resources, approved font/metrics, full reader, and English
  grading. The overlay and relocation binaries retain their preceding hashes.
  Final artifact SHA-256 values:

  - Resident module: `b52e6a94d8a24ca2962261ed96c9a22a083bb947d6942342664b8481c33c8be1`.
  - ROM: `ea1129ef7c189c5eecff727a611503c5f37608bb5f2f8143d71e4e2dacdce960`.
  - UPS: `93e02c48cde02ceea77d094ece32906e959afbe064e50a49ba8b038f8a9a2c21`.
- Native snapshot generation remains disabled. Complete metadata/other-reader
  coverage, semantic template approvals, missing glyphs, lossless editing,
  normal delivery, actual save/reload, and original hardware remain required.
  The repository remains private; no ROM, reference asset, or patch is published.

### Native mail metadata/storage validation and Pelly failure audit

- Added a reproducible audit of eight complete native functions: slot occupancy,
  send/gift predicates, both NPC record conversions, receipt dispatch, queue
  storage, and home-mailbox copying. Direct-call counts are respectively
  twenty-six, five, three, one, three, twelve, one, and four. No aligned literal
  pointers match these selected targets. The audit does not cover every inline
  metadata access or exclude computed indirect references.
- `smoke-mail-storage-native-01` passes 140 controlled cases, 217 actual N64
  calls, 267 assertions, and 656 recorded steps on the unchanged final NPC pilot
  ROM `ea1129ef7c189c5eecff727a611503c5f37608bb5f2f8143d71e4e2dacdce960`.
  The matching town checkpoint comes from `smoke-mail-npc-post-full-01`.
  Both classic and composite letters are restored successfully from the immutable
  catalog while preparing their source fixtures.
- The storage cases compare all three native metadata predicates for nine
  font/status values and ordinary/snapshot split values. They check complete
  NPC conversion and reverse conversion, including the fact that mail type
  and absent identity arguments do not transfer from the compact record.
  The native code retains every envelope byte and the split/status/gift/paper
  fields without interpreting text.
- Both leaflet modes preserve their source and update only the selected record
  and delivery flag. Every one of the five queue positions accepts a complete
  record and clears its source; a full queue rejects without consuming it.
  All ten mailbox slots in all four homes accept complete records and retain
  their source; all four full-mailbox failures preserve their sources/arrays.
  Neighbouring memory, unrelated post-office fields, and stack/module guards
  pass. All touched arrays and neighbours are restored locally, then the complete
  checkpoint is restored. The emulator exits cleanly; FlashRAM remains blank.
- Traced the actual Pelly actor overlay, not only the English source. Its
  receive-menu handler at `809C471C..809C4884` calls the receipt function at
  `809C47C0`, ignores failure, unconditionally selects successful receipt, and
  clears the staged letter at `809C4828`. Therefore the preceding lower-level
  failure guard does not establish end-to-end loss prevention. This is a newly
  identified required fix, not a passing normal-UI result.
- The existing refusal path copies the staged letter back into the selected
  player slot at `809C480C`, using submenu slot byte `DF` and current-private
  mail offset `40A`. A fix must preserve original pocket ownership, return a
  failed letter, choose an accurate failure message/state, and retain success
  behaviour. Simply routing corruption to the full-mailbox or unknown-recipient
  refusal would give a false explanation. Generation remains disabled.
- Recorded Pelly's complete handler hash
  `c29e3901cf539f63a16043228bccc787ec14fbf4a58613db350a06f9618b0e73`
  and overlay hash
  `a2fe6daee4180fd7fdcbe04cb62e514a8d88067b74bf7e43506f17986c204db6`.
  Mutation tests preserve the unfixed-failure evidence explicitly. Three targeted
  tests pass in 0.187 seconds. The initial complete suite passes 283 tests in
  158.222 seconds before the additional Pelly audit test. The final complete
  suite passes 284 tests in 155.951 seconds. Detailed inventory,
  native traces, extracted instructions, and fixture text remain ignored.

### Pelly receipt rollback and accurate English failure messages

- Fixed the menu-level unconditional clear following a failed receipt. A
  thirty-two-byte resident shim sends failure through the existing native
  pocket-return path with a distinct reason four; success keeps action three,
  next action five, and the original message/clear path. A twenty-four-byte
  index shim reuses the neutral hand-back introduction while retaining every
  original refusal index. No original animation handler was replaced.
- Verified the N64 inventory send function at `808725C8..80872684`, SHA-256
  `7145ad292f25dcaf9e67d4c8f26368eda658627dd747e52f5f1cfc9e8110f47b`.
  It stages status zero, copies the full letter, clears the selected player
  pocket, and remembers that slot. The native status differs from the assumed
  GameCube numeric value; the actual N64 instruction determines the fixtures.
  Rejected letters return as native sendable status one with all other bytes
  retained. The discarded tag disassembly used a base 0x400 too high; it was
  regenerated at the verified `8086F310` base before recording these addresses.
- Added original English errors at `2DE8/2DE9`, with native order-nine/continue
  controls. All existing 11,752 records remain unchanged by this extension.
  Both count bounds become 11,754, the table uses two spare end words, and its
  terminator/length remain intact. A pinned-executable-section scan finds only
  the two patched immediate bounds at the native count or its adjacent values.
  The new selector preserves all ordinary refusal messages and does not label
  corrupted mail as an unknown recipient or a full mailbox.
- The initial build guard rejected a mistyped expected instruction for the
  return-address adjustment (`27EF000C` instead of assembled `27FF000C`). The
  expected-byte guard was corrected; no output ROM was published from that
  failed build. All shim words, table words, target ranges, required lower-level
  hooks, message counts, and ownership overlaps have mutation rejection tests.
- Added a bounded native-call proof for Python test helpers. Heap overlay and
  boot-loader calls require complete expected resident instructions, remain
  within four-MiB RAM, cannot overlap module/test RAM, and retain the verified
  graph-thread requirement. Ordinary JSON targets are not broadened. The native
  loader performs DMA, relocation, and cache maintenance; an independent model
  of Pelly's exact relocation list checks all loaded text and data.
- `build/smoke-pelly-receipt-native-01` passes 48 receipt cases, 16 refusal
  selectors, 351 native calls, 720 memory assertions, and 104 complete message
  checks across 1,933 steps. Eight accepted cases cover both snapshot kinds,
  both sisters, and first/last pockets; forty rejected cases cover both kinds
  and all ten pockets for both sisters. Player state, NPC population, counters,
  staged clearing, returned complete records, actor choices, and memory guards
  pass. The action callback records its argument instead of starting animation
  on the synthetic actor. This is not a normal post-office gameplay test.
- The complete machine checkpoint is restored and the emulator exits normally.
  FlashRAM remains 131,072 blank bytes, SHA-256
  `b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260`.
  The separate `smoke-pelly-receipt-full-01` passes 188 train-to-town steps and
  all ten acceptance checks. No hardware or game-save compatibility is claimed.
- `smoke-pelly-receipt-indices-02` separately passes ten native index-boundary
  calls across seventeen recorded steps, preserving the original `reason+1`
  result except reason four's index two. The first supplemental run checked
  `v0`, but this call-site shim intentionally outputs `v1`; that test failed
  before any game change. The debugger now records both result registers, and
  the corrected assertions check `v1`. Production instructions are unchanged.
  The corrected run restores its checkpoint and exits with blank FlashRAM.
- Six targeted patch/relocation/ownership tests pass in 4.051 seconds. The
  complete suite passes 291 tests in 162.894 seconds, recorded in
  `build/tests-pelly-receipt-final-full.log`. The first complete run passed 289
  tests before the two ownership/relocation tests were added.
- Independent `build/runtime-module-pelly-repeat/` and
  `build/pelly-receipt-repeat-pilot/` reproduce the module, ROM, and UPS from
  `build/runtime-module/` and `build/pelly-receipt-pilot/`. The module occupies
  24,320 bytes with the unchanged 32 KiB reservation and 256 bytes left before
  the linked-code limit. Module SHA-256:
  `8cd34afd054df1f4e69f291f7966487e958da8bd59d27bf12ed193e79c443675`.
  ROM SHA-256:
  `3dc3f15dbb4f010510bda6217fcdc304928e078688604a7899b6442276b0e0e5`.
  UPS SHA-256:
  `8cc4916623c667c639899f586e926e00afa18502eb4ad208025ed12a76194abc`.
  The patched Pelly overlay remains 7,680 bytes, SHA-256
  `2edef515242f5833eb983ac56ba40db086e4600f2017b61fa84c03852740831b`.
  Its original 624-byte relocation file is unchanged, SHA-256
  `ac371d4f4c5d0c87f2ffb3d56bbddfdd7f1384ecca4cca5d3e769e4306241d2f`.
- The private GitHub repository remains private. All 10,405 existing candidate
  edits, approved font metrics, GameCube layout/timing, and save formats are
  unchanged. Snapshot generation remains disabled. Ordinary post-office
  animation and error progression, remaining metadata/readers, lossless editing,
  normal saving/reloading, semantic approval, and original hardware remain.

### State-eight hand-back review and follow-up validation

- Final direct-field review finds a second read of actor offset `949` at
  `809C4A98`. The state-eight initializer indexes its introduction table by the
  refusal reason; reason four would select the unrelated following table's
  `08DF` message. The earlier native fixture replaces setup with a recording
  callback, so its passing receive/selector cases do not exercise this lookup.
  The initial receipt pilot is not sufficient for the full hand-back sequence.
- Added a separate twenty-four-byte index shim at that lookup, retaining all
  original reasons and mapping reason four to the same neutral `08E1/08E2`
  introduction as reason one. The native initializer's complete source range
  `809C4A74..809C4AD4` has SHA-256
  `e725bc1f15690888bddd4a338ce85e5aeea42d39e1893a06801bdabdd989ecf5`.
  Its high/low table-address relocations remain unchanged.
- Expanded the fixture to use the real native setup function and initializers
  for actions three, six, eight, and ten. It tests state eight for every failed
  receipt and all four supported reasons for both sisters. Animation itself
  remains outside this fixture. All three original direct reason-byte accesses
  are now inventoried, and an additional/changed access fails installation.
- `smoke-pelly-handback-native-01` passes all 48 receipt cases, eight hand-back
  initializer cases, sixteen refusal selectors, and ten index boundaries. The
  407 native calls, 760 memory assertions, and 152 complete-message checks span
  2,084 recorded steps. The actual state-eight initializer is checked after all
  forty rejected receipts as well as for all supported reasons independently.
  The real state-ten initializer also executes. The checkpoint is restored,
  FlashRAM remains blank, and the emulator exits normally. This supersedes the
  earlier callback-only fixture for handler validation, not for normal gameplay.
- The corrected build's `smoke-pelly-handback-full-01` passes all 188 town steps
  and ten acceptance checks. Seven targeted guard/relocation tests pass in
  6.252 seconds. The final full suite passes 292 tests in 161.961 seconds,
  recorded in `build/tests-pelly-handback-final-full.log`.
- Independent module and pilot builds reproduce identical artifacts in
  `build/runtime-module-pelly-handback-repeat/` and
  `build/pelly-handback-repeat-pilot/`. The current linked size is 24,352 bytes,
  leaving 224 bytes within the same reservation/test layout. Module SHA-256:
  `8cd9e5419d8b1872a4bd1d983a1727035a57d6f5bbc449667004479fd0a8cac4`.
  ROM SHA-256:
  `db00d1c5d9335f5f3ace810ac9479faa335c99a3ca92732516bd338aedbd345a`.
  UPS SHA-256:
  `42f0a8c2a480a0c5cd78b9714cdb7d665b400e130d3801459fddabf825836974`.
  The Pelly overlay is still 7,680 bytes, SHA-256
  `6b90728930fe6009a700947d3d459e630a140a02f7dc1ec6bac62eb8f6a20048`.
  Its relocation file remains unchanged. The source and repeated pilots live
  in `build/pelly-handback-pilot/` and `build/pelly-handback-repeat-pilot/`.
- Prepared the next reader investigation while the native run completed.
  The first-job reverse-conversion call at `8091D428` and normal NPC calls at
  `80921678/80921690` lead to native board-read mode one at `8091D448` and
  `809216CC`. The normal unknown-sender path clears six sender-name bytes, not
  snapshot text. Source-matched disassemblies are retained in
  `build/disassembly/first-job-mail/` and `build/disassembly/normal-npc-mail/`.
  Complete caller-level native execution remains required; these observations
  do not establish generation or save compatibility.

### Complete English NPC names in read-only letter headers

- Traced the native NPC mail identity setter `8009C70C..8009C780` and reverse
  setter `8009C780..8009C80C`. Type one identifies NPC recipients; byte `0C`
  stores the villager index, while `0D` stores palette. Added read-only lookup
  of the complete eight-byte English name for indices zero through 215 in
  ordinary and snapshot headers. Player names and unsupported identities retain
  saved text; missing or malformed resources fall back without source changes.
  Header types two, three, and five retain recipient suppression.
- Expanded the snapshot header to 1,032 bytes and the ordinary stack buffer to
  eighteen bytes. Existing padding absorbs the snapshot's two additional bytes,
  leaving its cache at 5,792 bytes. Updated native cache observations to the
  formatted-letter offset 1,196; workspace offset 2,236 is unchanged. The native
  compiler reports a 32-byte helper frame, a 40-byte copy-wrapper frame, and a
  120-byte header-renderer frame. `build/mail-assembly-names/` passes standalone
  MIPS compilation, symbol resolution, stack reporting, and mutable-state checks.
- Host tests exercise every one of the 216 villager indices in both reader
  branches, resource and identity fallbacks, and the widened header boundary.
  The first all-villager run found a test-fixture guard reset missing between
  ordinary and snapshot iterations; resetting the guard before each iteration
  corrected the fixture. No runtime change was needed for that failure.
  The full suite passes 294 tests in 176.546 seconds, recorded in
  `build/tests-mail-names-full.log`.
- `smoke-mail-names-reader-01` passes eight windows and fourteen pages across
  218 steps. It verifies 1,705 glyphs and 6,820 vertex positions, both directions
  of paging, six complete long reference letters, two explicit error windows,
  and eight unchanged-source/preference checks. Two letters call the guarded
  original NPC identity setter before opening and render full eight-byte names.
  The fourth reference probe still redirects edit-open mode two to read-only
  mode one without rewriting the original snapshot.
- `smoke-mail-names-view-01` passes all ten ordinary-header cases, body/footer
  rendering, complete glyph vertices, and non-read-mode forwarding, with
  36 native calls and 842 assertions across 1,010 steps. Header cases cover
  the first and last eight-byte villager-name witnesses, the shortest name,
  unsupported index 216, player/other recipient types, disabled display-name
  resource, and suppressed-name types. Both native scenarios restore complete
  machine checkpoints and exit normally. FlashRAM remains 131,072 blank bytes,
  SHA-256 `b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260`.
- The new build's `smoke-mail-names-full-01` passes 188 train-to-town steps and
  all ten runtime acceptance checks. The independent builds in
  `build/runtime-module-mail-names/` and `build/runtime-module/` produce the
  same module; `build/mail-names-pilot/` and `build/mail-names-repeat-pilot/`
  produce the same ROM and UPS. Linked size is 24,480 bytes, leaving 96 bytes
  before the unchanged linked limit; reservation remains 32 KiB. Further
  runtime additions must respect this budget or provide a verified layout change.
  Module SHA-256:
  `173ea820b693bdc4faf014f4ce0be20106967deb448110f724e70715ca363a23`.
  ROM SHA-256:
  `00b1d985277d4a4600f6c4855344280e28c0c42ee5145e6fe5f537750058bf0f`.
  UPS SHA-256:
  `22e4e639a48c2a8e587625f106d47c5707e0602600f4c870627edfec4083789c`.
- Recorded the three remaining NPC show callers' exact instruction contracts,
  complete overlay and relocation hashes, BSS sizes, sender handling, and
  window ownership in `specs/NPC_MAIL_SHOW.md`. These are audit findings, not
  caller-level execution results. That execution remains the next reader task.
- All 10,405 candidate edits, approved font metrics, explicit reference layout,
  saved identity formats, and snapshot generation settings are unchanged.
  Generation stays disabled. Normal post-office animation/error progression,
  remaining readers, lossless editing, ordinary delivery, actual save/reload,
  and original hardware remain required. Ordinary-header cartridge lookup
  timing also remains unverified on hardware.

### Actual NPC stored-letter show caller validation

- Added a relocation model restricted to the original first-job and ordinary
  NPC dialogue overlays. Both file hashes, relocation hashes, section sizes,
  and all memory bounds are required. The model includes BSS address targets
  and the original loader's reused HI-register behaviour; Pelly's no-BSS model
  is not reused. Two host tests cover both layouts at several heap bases,
  complete pointer relocation, unchanged non-relocated bytes, BSS, and rejection
  of altered inputs or invalid destinations. Eleven debugger tests also pass.
- Added a silent bounded caller harness that loads both overlays through native
  `LoadImpl` and compares every relocated file byte and the zeroed BSS before
  execution. Each synthetic manager/client/sender-memory fixture is privately
  allocated and guarded. Every overlay stays allocated until its last window
  closes. Native handlers, clear/conversion functions, and submenu-opening
  calls execute unchanged; no production patch to either overlay is necessary.
- `build/smoke-npc-mail-show-01` passes all nine cases: classic, composite, and
  ordinary letters through first-job, known-sender, and unknown-sender paths.
  The actual handler-generated temporary letter matches the complete native
  conversion baseline, including the unknown sender's six cleared name bytes.
  Complete source letters, compact sender memory, saved player state, and saved
  NPC population remain unchanged during each caller invocation. Source letters
  and saved header/footer preferences also remain unchanged through window close.
  Ordinary frame updates are not compared against stale NPC data snapshots.
- Six snapshot windows pass twelve complete pages, 1,713 rendered glyphs, and
  6,852 vertex positions. All three ordinary windows preserve their complete
  source and expected text lengths and reach the installed header, body, and
  footer hooks. Full ordinary glyph-position coverage comes from the separate
  passing `smoke-mail-names-view-01` regression, not from these hook-entry checks.
- The caller run totals 510 recorded steps, 45 native calls, 151 assertions,
  three complete relocated/BSS checks, nine ordinary draw-hook observations,
  and three successful frees after close. The complete checkpoint is restored;
  the emulator remains alive and exits gracefully. FlashRAM stays blank with
  SHA-256 `b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260`.
- The final full suite passes 296 tests in 174.206 seconds, recorded in
  `build/tests-npc-mail-show-full.log`. The runtime and ROM remain unchanged
  from the committed header-name build: the caller scenarios run
  `build/mail-names-pilot/animal-forest-halfwidth.z64`, SHA-256
  `00b1d985277d4a4600f6c4855344280e28c0c42ee5145e6fe5f537750058bf0f`,
  using its own town checkpoint. No cross-ROM checkpoint is used.
- These results complete isolated validation of the three direct reverse-
  conversion callers, not ordinary NPC actor interaction or save compatibility.
  Remaining mail work includes normal post-office hand-back/error progression,
  inline/computed-pointer readers and metadata, travel, semantic identities,
  missing glyphs, generation, lossless editing, delivery, and actual save/reload.
  Snapshot generation remains disabled. No font, candidate translation, source
  asset, memory reservation, saved record, or public-release setting is changed.

### Native FlashRAM write and fresh-process letter persistence

- Added a source-guarded N64 flash model and a complete 192-slot saved-letter
  inventory: forty player records, forty home-mailbox records, five queued
  post-office letters, two leaflet records, and 105 compact NPC letters.
  The native payload is 63,872 bytes in each of two 65,536-byte banks. Both
  signatures, town IDs, payload checksums, and complete payload equality are
  required. The 1,664 padding bytes in each bank are not interpreted as mail
  or required to be zero. Complete native flash/worker code and the seven-entry
  state table are hash-guarded and covered by mutation tests.
- Distinguished the English GameCube debug save-data checker from the actual
  N64 flash module. The former is not evidence that N64 saving rejects the
  experimental header-split marker. Other N64 metadata readers still require
  their own audits. The native saver obtains a temporarily reserved framebuffer
  through the graph/framebuffer-retirement handshake, not ordinary heap malloc.
- The first fixture, `smoke-flash-mail-save-01`, failed safely because its
  135,744-byte temporary heap allocation returned null. It never reached any
  flash-writing call. Reduced the writer to a 16 KiB streaming chip-read buffer
  plus separate decoder storage; the fresh reader reuses one 64 KiB bank buffer.
  No production memory reservation or allocation policy changed.
- `smoke-flash-mail-save-02` reached the native save allocator but exhausted
  its eleven native allocation attempts without advancing out of state zero.
  The harness was resetting a breakpoint at the frame entry where execution
  was already stopped. Added guarded `advance_game_frame`, which executes the
  native prologue instruction before waiting for the next real frame entry.
  It does not write registers, instructions, or framebuffer ownership to fake
  progress. Thirteen debugger tests pass, including the two new frame-advance
  guard/order tests. Both unsuccessful runs remain recorded; neither reached
  a native flash write or changed a user save.
- `build/smoke-flash-mail-save-03` passes the actual native save pipeline in
  138 recorded steps: 44 native calls, 27 assertions, 25 save dispatches, and
  24 real frame advances. Both snapshot kinds populate every native letter
  array. All 192 complete records match the native prepared payload before
  writing, including retained identities, gift fields, and compact date/padding.
  Both complete banks read back through the native flash API and match that
  payload. The native state machine verifies both banks and clears its state;
  its framebuffer request also returns to zero. The original live save payload
  and complete machine checkpoint are restored, and ares exits gracefully.
- `build/smoke-flash-mail-read-01` starts a separate ares process seeded only
  with the exported `test.flash`; no emulator checkpoint, RTC, or RAM image is
  supplied from the writer. It passes 448 recorded steps, 19 native calls, and
  406 assertions. Native bank reads, both native checksum/identity checks,
  all 384 complete stored-record comparisons, and eight full English decoder
  outputs pass. Those decodes cover both classic/composite formats and both
  full/compact source layouts in each bank. Heap, stack, and module guards,
  that process's own checkpoint restoration, and graceful shutdown pass.
- The native-read export, writer's flushed cartridge save, and reader's
  flushed cartridge save have the same SHA-256:
  `a67bf983a3e7f8640de3a3fa57c153caadb7e8de1bb7d39c8c53957546fc047d`.
  Both logical payloads have SHA-256:
  `540e9afff587bfa8e3e88b47f1acc0ce934a45d50cae8ee454f0cebf74b5d082`.
  The isolated fixture town ID is `3069`. The save contains synthetic test
  letters and remains ignored under `build/`; it is not a user-play save.
- The final full suite passes 301 tests in 163.759 seconds, recorded in
  `build/tests-flash-mail-final.log`. The earlier complete run also passed
  299 tests before the two frame-advance tests were added. Python compilation
  and whitespace checks pass. The tested runtime, candidate file, and ROM are
  unchanged: `build/mail-names-pilot/animal-forest-halfwidth.z64`, SHA-256
  `00b1d985277d4a4600f6c4855344280e28c0c42ee5145e6fe5f537750058bf0f`.
- Documented the exact isolation and acceptance contract in
  `specs/FLASH_MAIL.md`, added repeatable writer/fresh-reader scenario generation,
  and recorded explicit flash-write opt-in in runner provenance. The writer
  refuses a nonblank isolated chip. The reader refuses a checkpoint-seeded run.
  Normal save-menu/post-load gameplay, user-created or edited letters, remaining
  readers/metadata, semantic identities, missing glyphs, generation, delivery,
  travel, and original hardware remain required. Generation stays disabled;
  no production code, text, font, saved record size, or release setting changes.

### Native Controller Pak write and fresh-process letter persistence

- Guarded the original native Pak module, `sCPk` transport, pad-manager serial
  lock/unlock, raw PIF read routine, and both file sizes. The passport holds ten
  full player letters and seven compact NPC letters in its 4,608 bytes. The
  26,368-byte stored-letter file holds eight ten-byte page labels followed by
  160 complete letters at offset `52`, with 46 trailing padding bytes. Native
  storage initialization and tag pointer arithmetic establish that layout.
  The ten temporary inventory pockets at storage offset `6700` are outside the
  persisted file. The complete original storage overlay is hash-guarded.
- Added an original test-only 144-byte assembly probe that locks the native
  serial queue, reads 1,024 Pak blocks through `__osContRamRead`, and unlocks
  on success or error. Independent Docker assembly agrees with the checked
  fixture bytes, SHA-256
  `e4bc4002ce0fe02410dfb88990742cc0b7c2392e6adeed1b948f42e79d914e91`.
  It runs in a freed private native heap allocation, not the production module.
  A single 33,280-byte allocation reuses its chip buffer for note/decoder work.
- The writer uses the original passport save function and first stored-letter
  writer stage. The latter's following FlashRAM stage is deliberately excluded.
  It requires an empty isolated Pak, enough native-reported space, and explicit
  `--allow-test-pak-write`. Host refusal tests cover nonempty and insufficient
  Paks before fixture allocation or writes. No format, repair, or delete routine
  is called. Existing user saves and Paks are never write targets.
- `build/smoke-pak-mail-save-01` stops before either native note-writing call:
  the fixture used an incorrect current-player pointer address. Corrected that
  test address from `80126FD8` to the verified `80136FD8`. No production change
  is involved. The failed run and its successful initial raw Pak read remain
  recorded. The first audit-report attempt also exposed makerom's absence from
  the DMA table; the executable scan now reads its actual pre-DMA ROM region.
- `build/smoke-pak-mail-save-02` passes all 433 steps, 189 native/test-probe
  calls, and 209 assertions. Native note counts change from zero to two, and
  free bytes change from 31,488 to 512: exactly 121 allocated pages. Complete
  file checksums, all 177 complete records, whole player/NPC import copies, and
  six English reconstructions pass. Both snapshot kinds cover player, compact
  NPC, and stored-letter sources. The unchanged live save payload, all memory
  guards, allocation free, checkpoint restoration, and graceful shutdown pass.
- `build/smoke-pak-mail-read-01` starts a new process from only the exported Pak
  and an entirely blank FlashRAM control file. No RTC, town save, RAM image, or
  writer checkpoint is supplied. It passes 258 steps, 21 native/test-probe calls,
  and 208 assertions, including all 177 complete records and six reconstructions.
  Complete native raw reads match the exported chip both before and after the
  read-only checks. The process restores its own checkpoint and exits gracefully.
- The native export and fresh reader's flushed Pak share SHA-256
  `476a2001dfe0c4523a0c7a2ff4e864a351987147c54e46e850c5a69be0d11876`.
  Restoring the writer checkpoint restores its original empty Pak, with SHA-256
  `ab2a6e04fd3ceb36594f1216c888a1b8bd0a3ba0a94f715a7c7601e98c49ec51`.
  This is why the test exports via native reads before restoration instead of
  treating the writer's eventual flushed file as the result. Both runs retain
  blank FlashRAM. Original isolated input files are unchanged.
- Extended the repeatable mail audit with 28 narrow executable marker-offset
  candidates and complete reference inventories for the three shared text
  helpers: 22, one, and zero direct calls, with no aligned literal pointers.
  The report explicitly does not establish complete computed-pointer coverage.
  Documented PIF, unrelated-array, and item-label false positives, identity-only
  tag name sizing, and the Pak UI's separate ten-byte page-label length/render
  path. Report: `build/audits/mail-storage-pak.json`.
- The final full suite passes 307 tests in 164.904 seconds, recorded in
  `build/tests-pak-mail-final.log`. The earlier full run passes 305 tests in
  167.252 seconds before the final audit and refusal tests are added; the
  targeted six-test Pak suite also passes. Python compilation and whitespace
  checks pass. Production
  code, all text candidates, font metrics, snapshot-generation gating, and ROM
  remain unchanged. Tested ROM SHA-256:
  `00b1d985277d4a4600f6c4855344280e28c0c42ee5145e6fe5f537750058bf0f`.
  The Pak test proves only the specified transport path. Ordinary travel and
  storage-menu operation, error progression, editing, remaining metadata/readers,
  semantic template approval, generation, delivery, and original hardware remain.

### Shared text-reader follow-up

- Disassembled the remaining inventory, editor, recipient-selector, number-label,
  map, noticeboard, and Pak-directory overlays into ignored audit directories.
  Traced their shared text-length call inputs against native instructions.
  The six-byte player/town/recipient names, five-byte formatted number, and
  sixteen-byte Pak directory game name are not snapshot-envelope readers.
- The 96-byte call at `8089571C` reads the distinct noticeboard table at
  `Save+2F6A+index*68`, not a letter body. The English GameCube noticeboard source
  supports the semantic match; its larger record is not substituted for the
  native one. Documented these input regions in `specs/MAIL_STORAGE.md`.
- Kept generic editor-input ownership, editor acceptance reachability, and
  tag-option pointer-array provenance as explicit remaining checks. The
  pre-scan snapshot-copy hook covers the board initializer's ordinary text
  scans, but this does not establish every editor transition or computed-pointer
  consumer. No production code or test harness changes follow from this
  additional source inspection; the passing 307-test checkpoint is unchanged.

### Native letter-menu selection and static-label provenance

- Added source-guarded native TAG overlay inspection, a bounded independent
  relocation model, a fresh-process scenario, and an isolated heap fixture.
  The original overlay has SHA-256
  `eee60f36d61212bd1719b752916be4825ba0952660fafe1c68054dbd1e9fa9d5`;
  its relocation file has SHA-256
  `d5703988bd132d02415c4db7cbc2ac9a794dc1908cf9e6fb33f01f03def92af2`.
  The complete native-loaded file and BSS agree with the independent model.
- `build/smoke-mail-menu-01` passes 973 recorded steps, 167 native calls, and
  138 memory assertions. All 120 status/gift/marker/context cases choose the
  expected menu and retain the complete source letter. All 44 static tag-label
  definitions pass actual native maximum-length calls, including empty rows.
  Current-player/field globals, complete live save payload, source image,
  allocation/stack/module guards, allocation free, checkpoint restoration,
  blank FlashRAM, and graceful shutdown pass. The fixture allocates 116,576
  bytes in a fresh process, including the whole fake overlay prefix.
- Received-letter types 19/20/21 point to Read; draft types 22/23/24 point to
  Rewrite. Source inspection establishes Read's mode-one and Rewrite's mode-two
  board opening calls. This harness does not execute those wrappers, paper
  collection side effects, or the normal UI. Opaque marker fixtures are not
  valid snapshot envelopes and make no decoder claim.
- Traced board program 12 through recipient-selector program 13 to keyboard
  editor program 10. The recipient selector passes the board's temporary body
  to the editor with sixteen columns; the editor remains a real text consumer.
  Snapshot read mode bypasses the recipient opener after the installed copy
  hook. All input ownership, generated status values, parent-menu interaction,
  and player-created/custom edited letters remain required. Generation stays
  disabled; production ROM, text candidates, saved formats, and font are unchanged.
- Added seven passing portable/retail tests covering all reference status-byte
  values, paired marker cases, source mutation rejection, static pointer graphs
  at three RAM bases, unrelocated bytes, BSS, and invalid destinations. The full
  suite passes 314 tests in 162.870 seconds, recorded in
  `build/tests-mail-menu-full.log`. Python compilation and whitespace checks pass.
- Inspected the actual shared submenu callback assignments, change-motion,
  movement, end, and return instructions. Read close takes state two through
  motion state zero to end state four, not edit-accept state three. Recorded
  complete original file/function hashes in `specs/MAIL_MENU.md`. The return
  routine restores parent procedures or destroys loaded programs; it does not
  read or copy letter text. The board's saved parent-move callback remains an
  explicit ordinary-interaction check, not an inferred passing gameplay test.

### Whole-letter generation transaction development

- Implemented caller-owned complete field capture, immutable-selection field
  pruning, and atomic 164-byte letter publication in a separate generation
  source directory. Complete English restoration must succeed before the
  snapshot marker/text or transient capital state is published. Missing or
  invalid fields, unavailable catalog parts, and overflow retain the old letter.
  Failed field replacement invalidates its slot rather than reusing old text.
- The first host test run exposed an incorrect fixture assumption: classic
  `0000` has no substitutions, so it cannot test a missing required field.
  Changed that test to `0002`. The deliberate `0001` overflow fixture now uses
  its actual required slots ten through nineteen and independently asserts
  that packing exceeds capacity. The first log remains at
  `build/tests-mail-generate-targeted.log` (five pass, one fixture failure).
- Replaced C structure assignments with explicit staged byte copies after the
  VR4300 compiler emitted unresolved `memcpy` references. The corrected probe
  compiles to 1,380 bytes without mutable data or unresolved symbols. Its three
  entry points require zero, thirty-two, and 216 bytes of direct stack, before
  nested resident calls. SHA-256:
  `7760f4d3dcaa1402318e2a6fc882d5803599357d259e0c55667873bdfc96313d`.
  Source/build hashes, imports, relocation audit, and disassembly are recorded
  under `build/mail-generation-probe/`.
- The corrected six-test host run passes in 1.177 seconds, including all 6,398
  supported reference assembly cases and unchanged source/destination guards.
  Reference parsing is shared within the bulk test rather than repeated for
  every case. Additional stale-replacement and late-failure capitalization
  checks also pass in `build/tests-mail-generate-targeted-03.log` (1.196 seconds).
- `build/smoke-mail-generation-01` passes 1,149 recorded steps, 99 native calls,
  and all 719 memory assertions. It covers 46 complete English reference cases,
  seven rejected generation cases, 42 capture cases, complete capture reset,
  and an additional disabled-resource rejection. Complete generated text,
  snapshots, metadata, capture state, immutable inputs/code, live-save payload,
  heap/stack/module guards, allocation free, checkpoint restoration, and graceful
  shutdown pass. The 8,192-byte fixture is private native-allocated heap memory;
  the new C code uses actual cartridge DMA and existing resident restoration.
  Blank FlashRAM and the empty Controller Pak remain unchanged.
- Six probe-loader tests pass for source/build/import hashes, exported entries,
  exact internal-jump relocation, immutable external calls, stale or altered
  inputs, invalid relocation inventories, reserved memory, alignment, and the
  four-MiB boundary. The twelve combined generator/probe tests pass in 1.156
  seconds at `build/tests-mail-generation-probe.log`.
- Ordinary gameplay generation remains disabled. The production module, ROM,
  font, and candidate texts are unchanged. Native creator bindings, field-source
  identities, production loading, and failure propagation remain required;
  see `specs/MAIL_GENERATION.md`.
- The complete regression suite passes 326 tests in 165.498 seconds at
  `build/tests-mail-generation-full.log`. Python compilation and whitespace
  checks pass. The production ROM still has SHA-256
  `00b1d985277d4a4600f6c4855344280e28c0c42ee5145e6fe5f537750058bf0f`.

### NPC creator, failure-return, and source-slot bindings

- Added exact source guards for seven native reply functions and six native
  tables, including staging, metadata, post-office submission, and pending-state
  processing. Also verified five English executable functions and five tables
  directly from the supplied decoded REL and pinned symbol definitions.
- Traced the unpropagated assembler failure through good/bad creation and
  unconditional receipt. The native submission wrapper reuses staging at
  `80142F80` without first clearing it. Specified a complete-pointer/zero return
  gate at `800A9164` which skips receipt and the stale `v1` result copy on
  creation failure. This is an uninstalled design, not a passing native gate.
- Source-slot coverage passes all 24 composite group/gift contexts and all 36
  classic bad-reply selections. No available template needs an uncaptured slot;
  the existing unavailable composite footer is `psz:004D`. Selection helpers
  retain original offsets, reject invalid origins/personalities/gift gates,
  preserve body-B gift halves, and never issue random choices.
- Nine targeted tests pass in 0.229 seconds at
  `build/tests-npc-mail-generation.log`, including complete function/table
  mutation rejection, all part ranges, gap exclusion, and source-hole fixtures.
  The local source report is `build/audits/npc-mail-generation.json`.
- Compared all eleven selected word families directly from native, legacy, and
  English banks. All 352 complete legacy values equal their transcoded English
  references, including the first 32 entries of the relocated/expanded fish and
  insect families. Eighty-three values exceed ten bytes; all fit sixteen bytes.
  This observation does not install word capture or approve every letter's
  meaning. A guarded source-mapping implementation remains next.
- The full regression suite passes 335 tests in 165.222 seconds at
  `build/tests-npc-mail-generation-full.log`. Python compilation and whitespace
  checks pass. No production ROM/module, save, font, or translation candidate
  changes accompany this binding audit.

### Complete randomized NPC reply-word mappings

- Implemented guarded preparation directly from the original, legacy, and
  English string banks. All 352 selected full values match exactly; source,
  legacy, reference, and captured hashes are retained for each native ID and
  field slot. The fish/insect mappings preserve the original first-32 selection
  ranges without introducing a new random draw or replacing a selected creature.
- The canonical 11,328-byte resource at `build/npc-mail-words/words.bin` has
  SHA-256 `698e26d21c20eddcc25766317aa52024949f4eba51db99d73d58d46f6c5a12c1`.
  All values fit sixteen bytes; 83 exceed ten bytes. The guarded English setter
  proves that this preparation path supplies article zero. Its complete function
  SHA-256 is `1d6b2bef84d1cd4d296852a60df2951382d796cfa9a99e84233dd4fb41b2d62b`.
- Seven targeted tests pass in 0.122 seconds at `build/tests-npc-mail-words.log`.
  Coverage includes every full value and lookup, snapshot field round trips,
  family boundaries, ordering, padding, lengths, articles, glyph restrictions,
  header/payload integrity, bound whole-resource hashes, all three source banks,
  and a changed decoder. A recalculated embedded payload hash does not bypass
  the separate complete-resource hash requirement.
- The resource remains local and uninstalled. No production ROM/module, saved
  record, font, or main translation candidate is changed. Native capture before
  truncation, on-demand loading, full names, and submission failure handling
  remain required; see `specs/NPC_MAIL_WORDS.md`.
- The full regression suite passes 342 tests in 165.677 seconds at
  `build/tests-npc-mail-words-full.log`. Python compilation and whitespace
  checks pass. Repeated preparation produces the same resource hash.
- A read-only name-source check finds 394 distinct six-byte keys across all
  216 original villager names and the current pilot's 178 replaced short-name
  rows, with no keys identifying multiple villagers. This offers a bounded
  exact-name recovery path for visitor replies; the source-guarded alias builder,
  full display-name agreement, unknown-name policy, and native integration are
  not implemented by this observation. The initial attempt to use the generic
  whole-bank helper on a relocated pilot ROM failed because its main text bank
  moved; direct extraction of the unchanged `E04000` name DMA entry succeeds.

### Short-lived reader scratch and complete saved-name sources

- Removed the 3,552-byte decoder workspace from permanent reader state. Each
  snapshot open allocates 3,567 bytes, aligns the workspace, and releases the
  original allocation after restoration on both success and failure. Drawing
  uses only the independently owned complete cached text. Allocation failure
  shows the existing English error without changing the source letter.
- The resident cache is 2,236 bytes and explicitly aligned to sixteen; MIPS
  assertions pin its size and the formatted-text offset. The module links to
  20,928 bytes, leaving 3,648 bytes within the existing linked limit. The 32 KiB
  reservation, test region, and actual native heap boundary are unchanged.
- Nine reader tests pass at `build/tests-reader-scratch.log`. New cases cover
  deliberately unaligned allocations, every decode-read failure, poisoned freed
  scratch, original-pointer release, guards, repeated opens, and no allocation
  for ordinary/unused letters. Cross-compilation passes with the expected
  2,236-byte BSS and no undefined symbols.
- `build/smoke-reader-scratch-full-01` passes 188 train-to-town steps and all
  ten acceptance checks in four MiB. `build/smoke-reader-scratch-pages-01`
  passes all eight letters across fourteen pages: 1,705 glyphs, 6,820 vertex
  positions, all eight source/preference checks, checkpoint restoration, and
  graceful shutdown in 218 recorded steps. The cartridge save remains blank.
- Independent module and ROM builds match. Module SHA-256:
  `2ae761c6bd9c1e0cd0707555b60bda3e9e3b988e6ab34d2fb1c306a06406ef94`.
  The ROM at `build/reader-scratch-pilot/animal-forest-halfwidth.z64` and its
  independent repeat have SHA-256
  `300c8b5b4de252d3962d649c31496578ee8db12a4624e8db423ecbf3876f4fc0`.
  UPS SHA-256:
  `7384668a29132d8800063888b2e7cc19e7fae32ffad4b85ba50c32586f741227`.
- Implemented source-bound exact saved-name aliases: 394 unique original and
  fitting English keys recover the complete eight-byte names of all 216
  villagers. Original ROM and complete display resource hashes are checked;
  reconstructed source edits must agree. No truncated English prefix is a key,
  and unknown names remain unresolved. The 6,368-byte local resource has SHA-256
  `a79b6bc3c5b36c7ce2bcea55932ccdf4ce694608e5dcfb896226a24d368bf5d6`;
  independent preparation matches. Native lookup/capture remains uninstalled.
- Six name tests pass at `build/tests-npc-mail-names.log`, covering every real
  key, complete output, collisions, unknown values, invalid resources, and source
  changes with recalculated manifest hashes. The complete regression suite
  passes 350 tests in 181.567 seconds at `build/tests-reader-scratch-full.log`.
  Python compilation and whitespace checks pass. Font metrics, reference line
  breaks, candidate text, saved record formats, and the disabled gameplay
  generation setting are unchanged.
- Rebuilt the isolated generation probe against the new resident symbol
  addresses; code SHA-256 is
  `158959692289be5b336a53adc73699abb6671e0cc56ce13f622e6af9a53b916e`.
  `build/smoke-reader-scratch-generation-02` passes all 53 generation cases,
  42 capture cases, 99 native calls, and 719 memory assertions in 1,149 steps,
  including complete save retention, allocation free, checkpoint restoration,
  and graceful shutdown. The first launch stopped before emulator startup
  because the scenario output was a JSON file rather than a directory; the
  corrected launch uses that actual file. Both logs remain local.

### Native NPC creation-failure submission gate

- Implemented the exact three-instruction submission patch as a guarded helper.
  It verifies the complete original function, rejects unsupported target
  addresses, retains native argument setup/receipt/epilogue, and returns zero
  directly after creator failure rather than copying stale `v1`.
- Added a bounded native harness with a heap-owned copy of the wrapper and a
  64-byte test creator. The creator logs all six o32 arguments, returns a
  configured complete-letter pointer or zero, and poisons `v1`. The actual native
  counter, recipient, receipt, capacity, queue copy, and clear routines execute;
  no production submission instruction is modified.
- The initial scenario preparation correctly rejected a changed helper range:
  the combined pilot already contains the approved NPC-send result shim at
  `800B69BC`. Preparation now reconstructs that one expected call from the
  verified module, checks the complete shim, and continues to reject any other
  changed instruction. The player-receipt path in these tests does not enter
  the NPC-send branch.
- `build/smoke-npc-mail-delivery-01` passes all 41 cases, 44 native calls, and
  224 memory assertions across 578 steps. Cases include eight counter pairs,
  creator rejection, both snapshot kinds and origin arguments, every queue slot,
  full queues, invalid recipients, and a full home mailbox. Twenty cases reach
  successful native receipt. The old staging letter is never submitted; the
  returned source is cleared only after receipt succeeds. All six creator
  arguments and the low-byte origin conversion pass.
- Full save comparisons permit only the expected queue/counter/recipient-flag
  writes on success and no changes on failure. Complete original save/staging
  restoration, unchanged resident instructions, heap/stack/module guards,
  allocation free, machine checkpoint restoration, and graceful shutdown pass.
  FlashRAM remains blank and the Controller Pak unchanged.
- Three targeted host tests pass, including mutation rejection at every byte
  of the original function. Independent VR4300 assembly in the existing pinned
  Docker toolchain verifies all three patch words and the entire test creator.
  Assembly report and disassembly are in `build/npc-mail-delivery-assembly/`.
  Fixture SHA-256 at test log address `802F8010` is
  `1a2afee67ea73126dcda09a17378adda66263fe4c2b19a1304c8831e20393962`.
- The real creator, native full-source capture, pending-reply loop, and normal
  gameplay are not exercised by the controlled creator. Production generation
  and gate installation remain disabled. The existing ROM, module, font,
  candidate translations, and saved formats are unchanged.
- The full regression suite passes 353 tests in 167.739 seconds at
  `build/tests-npc-mail-delivery-full-01.log`. Python compilation and whitespace
  checks pass.

### Complete sources captured beside real native NPC reply creation

- Implemented scoped resident adapters at eight guarded original call sites.
  Inactive adapters forward all original arguments/results. Active preparation
  still runs every original name lookup, other-villager selection, random word
  load, and ten-byte setter. Full English values are captured from verified
  identities and already selected IDs; the native RNG algorithm is unchanged.
- Implemented the bounded callback state machine and immutable full-resource
  validation. It recovers all 216 complete English names from 394 exact saved
  keys and retains all 352 phrases with the English loader's sixteen-byte space
  padding. Unknown names, wrong source families, reordered/missing events,
  incomplete preparation, and invalid template groups reject the session.
  Complete word/name resources stay local, and saved identity widths do not grow.
- Added original freestanding SHA-256 with host `hashlib` comparisons at every
  short padding boundary, unaligned inputs, whole resource sizes, and one MiB.
  Both complete English string-loader and handbill-setter routines are now
  guarded. Independent word preparation with this source evidence produces
  the same resource digest. The first native digest build exposed an unwanted
  compiler-generated `memcpy`; explicit scalar state initialization removes it.
  One initial host fixture restored its own deliberately changed header digest;
  the corrected mutation fixture passes without weakening source checks.
- Built the complete capture/generation overlay using the existing pinned GCC
  14.2 VR4300 container and the pinned project's Fado tool. Its image is 23,280
  bytes: 5,168 text and 18,112 read-only data, with no writable/BSS section.
  The 160-byte native relocation table has 33 entries and agrees with the
  independent linked-ELF inventory. Image SHA-256 is
  `20485485c3e08170f57d3cacbfff5fbb4c7900b1c0291485613486dc48e62f75`;
  relocation SHA-256 is
  `2ecc4a40aae21de8f10077ecb78f7353826b87a67b56f9613ef6ac5c6f031e23`.
- The resident adapters add 736 linked bytes. The module occupies 21,664 bytes,
  leaving 2,912 before the separate native-test area; the 32 KiB reservation and
  original heap boundary stay unchanged. Module SHA-256 is
  `9db4b422849fdee0f438dcf5e71ec260a02c50551f9efc1ae064724b044c0979`.
  Independent module, ROM, and UPS builds match. ROM SHA-256 is
  `c7e76de3ad4ccfc03c125566cd9c072a5ff8d7b61ef6c2074ce260053105dc9b`;
  UPS SHA-256 is
  `d11959db1b02ae2ef7e01b1077b11291206f13ff5ab56d5b9f04b7e5460bf222`.
  `build/smoke-npc-capture-full-01` passes 188 train-to-town steps and all ten
  acceptance checks in four MiB.
- `build/smoke-npc-mail-capture-04` passes all 48 real-creator comparisons:
  both origins, good/bad replies, six personalities, and both initial capital
  states. Original and captured creators start with identical seeds and end
  with identical RNG state, native free strings, identities, gifts, status,
  type, and stationery. All 48 produce complete matching English snapshots;
  thirteen original gifts are retained. Selected fields and template IDs are
  checked without substituting a native random, gift, or metadata routine.
- The native capture run passes 197 calls and 721 memory assertions in 1,813
  recorded steps. It checks complete relocation, actual source integrity,
  complete-name and word-family boundaries, unknown-key rejection, full save
  retention, complete code/resource retention, instruction/global restoration,
  allocation free, memory guards, checkpoint restoration, and graceful shutdown.
  FlashRAM stays blank; the Controller Pak is unchanged. The isolated fixture
  writes code/resources into owned heap memory, not the cartridge loader.
- Earlier native attempts remain in the local logs. One invocation supplied a
  state file where the runner requires its isolated directory. The first live
  loader run omitted native cache maintenance and stopped at source validation.
  Adding the original writeback/invalidate sequence allowed execution. A later
  alternating-hook run passed 29 cases before rejecting a fresh session with
  phase zero. The final harness completes all original baselines first, installs
  hooks once, performs explicit cache maintenance, and restores/flushes them
  after capture; all 48 cases and restoration pass. These are fixture changes,
  not unexplained successes from rerunning the same stalled process.
- Twelve capture/relocation/hook tests and eight word-source tests pass. The
  complete suite passes 366 tests in 169.271 seconds at
  `build/tests-npc-mail-capture-full-02.log`. Python compilation and whitespace
  checks pass. The unavailable composite footer is not selected by this native
  sample, and source/range checks do not approve every possible letter's meaning.
- Independent capture-overlay and relocation builds also match.
  `build/smoke-npc-capture-reader-02` passes the full eight-letter/fourteen-page
  reader regression on the new resident module: 1,705 glyphs and 6,820 vertex
  positions, source/preference retention, module guard, checkpoint restoration,
  and graceful shutdown across 218 steps. The first reader launch passed a
  directory-style path for a generated JSON file and failed before emulator
  startup; the corrected invocation uses the actual scenario file.
- Ordinary gameplay generation stays disabled. Whole-creator allocation and
  ownership, actual cartridge loading/failures, sticky capital across successful
  creations, the tested submission gate's real creator binding, pending-loop
  validation, normal delivery/save/editor flows, semantic review, and hardware
  acceptance remain. Font assets/metrics, candidate wording, explicit reference
  layout, and native saved record formats are unchanged.

Generated assets, logs, screenshots, ROMs, patches, and reference text remain
local under ignored `build/` and `local/` paths. Current status belongs in
`PROGRESS.md`; this file records completed work and test observations.
