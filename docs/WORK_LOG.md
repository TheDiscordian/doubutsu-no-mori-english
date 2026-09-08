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

### Whole NPC reply transaction and shared capitalization

- Implemented `af_npc_mail_create` in the on-demand image. Its 5,344-byte aligned
  workspace owns capture, a complete private 164-byte native letter, and full
  generation scratch. It validates object separation, request origin/personality,
  existing scope, and capitalization before mutation; then it clears stale work,
  validates both complete sources, calls original native clear/metadata with
  scoped capture, and publishes all 164 bytes only after full English generation.
  Failure retains caller text and capitalization; successful calls advance the
  shared capital word. No temporary session pointer remains active after return.
- Six host tests pass every origin/condition/personality/initial-capital
  combination, full metadata/text, padding, source retention, sixteen successive
  dirty-workspace generations, nested calls, missing preparation/selection,
  unknown identities, lost ownership, corrupted resources, disabled catalog,
  unavailable footer, every catalog-read failure, invalid requests, and object
  alignment/overlap. The initial test mock required explicit unsigned-character
  pointer casts for its conditional string sources; that compile error is fixed.
- Hardened preflight ordering: an alleged workspace aliased to a smaller active
  pointer or capital word is rejected before reading its session fields. A native
  C stack fixture uses actual small control objects. AddressSanitizer and
  UndefinedBehaviorSanitizer pass all six tests at
  `build/tests-npc-mail-creator-sanitized-01.log`, with leak checks disabled for
  the host Python process and no system installation. Sanitizer instrumentation
  and suppression of the host preload apply only to this test/compiler invocation.
- The complete image is 24,176 bytes, comprising 6,064 bytes of code and 18,112
  read-only bytes. It has no writable/BSS section. The 208-byte relocation
  section has 45 entries, verified independently against the linked ELF.
  Native assertions pin capture/stage/generation offsets; the creator's own
  stack frame is 120 bytes. The new entry adds no resident module bytes.
  Image SHA-256 is
  `febefdce556213c49358ab4f393e74cec65812e0cdd93c3aedfae5454484b8ab`;
  relocation SHA-256 is
  `7e3363bd8992441587eba275d8824aac6bec23989a6ec23db02655e1ae1bd82f`.
  Independent builds in `build/npc-mail-capture/` and
  `build/npc-mail-creator-repeat/` match completely.
- `build/smoke-npc-mail-creator-03` passes 48 original-versus-whole-creator
  comparisons with real native RNG, preparation, gift, identity, and stationery
  routines. Complete metadata, native temporary fields, both final RNG words,
  full English snapshots/text, and all original save bytes agree. Thirteen
  gifts are retained. Eight more letters pass in sequence using one shared
  capitalization word and deliberately stale workspace state.
- Six native failures pass: altered embedded source, disabled catalog, unknown
  visitor sender, an existing session, and workspace aliases to the capital
  and active-session words. All retain the complete caller letter and capital;
  rejection before native creation also retains the two RNG words. Existing
  sessions are retained, and sessions owned by the creator are detached.
- The final native run passes 163 calls and 898 assertions across 2,101 steps.
  Complete source/code retention, hook restoration with cache maintenance,
  original globals, full save retention, heap/stack/module guards, allocation
  free, checkpoint restoration, and graceful shutdown pass. FlashRAM stays blank
  and the Controller Pak unchanged. Earlier passing runs are retained: `01`
  tests the first complete transaction; `02` adds successive capitalization;
  `03` exercises the final preflight ordering and both small-control aliases.
- Documented the next resident loader boundary, bounded allocation, approved
  blob/configuration checks, cache-maintenance sequence, failure cleanup, and
  optional all-or-nothing hook installation. That loader is not implemented
  yet. Native code/resources still enter through isolated fixture writes;
  ordinary creation-to-receipt and pending-loop gameplay remain untested.
  The resident module, ordinary ROM/patch, approved font/spacing, reference text
  layout, and existing saved formats are unchanged.
- The complete regression suite passes 372 tests in 172.872 seconds at
  `build/tests-npc-mail-creator-full-02.log`. Python compilation and whitespace
  checks pass; the repository remains private.

### Cartridge-loaded NPC creator and batch-validation priority

- Implemented the six-argument resident creator loader and opt-in complete
  installation. It owns one 29,743-byte transient allocation, checks an externally
  approved complete-blob CRC before relocation/execution, performs native cache
  maintenance, preserves caller capitalization on failure, and frees before return.
  Configuration is disabled by default. Eight capture calls, the tested submission
  gate, catalog, and complete reader must be present together. Configured native
  tests require the ROM build's enriched `runtime-module.json` approval.
- Thirteen loader/installer/CLI tests pass at
  `build/tests-npc-mail-loader-targeted-01.log`. Seven loader tests also pass
  AddressSanitizer and UndefinedBehaviorSanitizer at
  `build/tests-npc-mail-loader-sanitized-01.log`. The initial MIPS compile exposed
  an implicit `memcpy` from struct assignment; explicit volatile configuration
  copying removes that unavailable dependency. No host installation was needed.
- Independent module builds match at 22,720 linked bytes, 1,856 bytes free,
  with the unchanged 32 KiB reservation. Module SHA-256 is
  `60c05ab0295e43afa71a1e9b1d5ff4750a890f4a7b3141aec1ecaae94d483aea`.
  Independent creator builds match: image SHA-256
  `a61414849256df574c859877c7728f84752eb7e1fa50e597c6b76a962a4df6ae`,
  relocation SHA-256
  `7e3363bd8992441587eba275d8824aac6bec23989a6ec23db02655e1ae1bd82f`.
- The opt-in ROM in `build/npc-loader-pilot/` has SHA-256
  `bf8537f212f299f6e2df2db0cc2e1435a209041fc39b3045f3e498a163550ce1`;
  its verified round-trip UPS has SHA-256
  `cdd1138de8c55afeb3459c9259fbb25a98075c32284c30015aa3b23aed2888f7`.
  Fresh four-MiB boot-to-town passes all 188 steps and ten acceptance checks in
  `build/smoke-npc-loader-full-01`. This ROM supplies its own matching checkpoint.
- `build/smoke-npc-mail-loader-01` passes all 48 original-metadata comparisons,
  eight successive letters, and eight rejected requests across 1,763 steps and
  539 assertions. The creator and its resources are loaded only from cartridge;
  zero creator bytes are debugger-uploaded. Complete English reconstruction,
  original metadata, selected full words/names, RNG, capitalization, complete
  save retention, and unchanged native heap totals pass. Controlled free-block
  exhaustion exercises actual allocation failure. Hooks/globals/configuration,
  guards, allocation free, full checkpoint restore, and graceful shutdown pass.
  FlashRAM remains blank and the Controller Pak unchanged. Delivery itself is
  not exercised by this loader test and remains a follow-up integration item.
- The full regression run covers 385 tests in 179 seconds with one stale
  module-bound generation-probe error, recorded in
  `build/tests-npc-mail-loader-full-01.log`. Rebuilding the affected ignored probe
  and rerunning its six-test group passes at
  `build/tests-npc-mail-loader-probe-refresh.log`. No further full-suite rerun is
  needed solely for that generated-artifact refresh.
- Recorded the user's batching direction: prioritise bulk English coverage and
  playable sections; difficult isolated edge cases must not repeatedly hold up
  unrelated implementation. A human playthrough follows the main work and drives
  the broad bug/polish pass. Main work returns to missing introductory-job text.
  Font metrics/assets, reference layout, saved formats, and repository privacy
  remain unchanged.

### Introductory-job text batch

- Closed all ten functional text gaps in Nook's `07E0..083D` introductory range
  with fourteen added records: thirteen complete/reference-derived candidates
  and one original native-command-preserving debt reminder. Four additions are
  reserved continuation slots, not separate gameplay conversations. No existing
  candidate changed. Only the opening-reserve `083E/083F` placeholders remain
  without candidates in the wider range.
- Added exact source/reference/payload approvals for six wage/reminder/HRA
  records, the complete four-part employment-ending speech, and the two-part HRA
  explanation. Splits replace only existing GameCube wait/page separators and
  retain complete wording, layout, pauses, choices, and final termination.
  Supporting Nook speaker emotions require individually listed existing native
  tuples and source hashes; other actor operations and gameplay controls cannot
  inherit approval. Mixed whole/sliced reference groups require complete ordered
  coverage. The map instruction changes only X to the native R button.
- Added explicit batch-ID selection to the existing native cartridge-load test
  generator. One fresh four-MiB run loads all fourteen complete messages,
  checks all adjacent buffer/module guards, restores its checkpoint, and exits
  gracefully: `build/smoke-nook-jobs-complete-01`, 79 recorded steps and 44 memory
  assertions. FlashRAM remains blank and the Pak unchanged. This is message-load
  validation, not ordinary job traversal or final HRA-choice gameplay.
- All 389 tests pass in 175.996 seconds, recorded at
  `build/tests-nook-jobs-complete-full-01.log`. The new sequence, controller,
  original-draft, and explicit-batch groups also pass separately. An initial
  targeted draft test needed its expected ID set and final-terminator assertion
  updated for the new native `01` record; the corrected group and full suite pass.
- `build/nook-jobs-complete-pilot/animal-forest-halfwidth.z64` has SHA-256
  `cda1ed232c0be2e854ce70c550efecf622ec3808f4bba534e5a4ec387ed545c9`;
  its round-trip-verified UPS has SHA-256
  `607f9adbfc3de01224b8882ad0093f88e034da53da5fd8c288f192bf55feb49a`.
  The current candidate file has 10,419 edits, including 9,164 reference dialogue
  candidates and ten original dialogue drafts. The original-bank audit leaves
  2,578 records without candidates, including 1,647 with Japanese static text.
  Wider resources and embedded UI remain outside those counts. All candidates
  retain their review status. Detailed reports are in
  `build/nook-jobs-complete-candidates/` and `build/nook-jobs-complete-coverage/`.
- The HRA invitation contributes one conservative line-width warning; it is
  queued for polish without altering the GameCube line layout. Ordinary job
  progression and new continuation/choice traversal remain combined gameplay
  checks. No new full train-to-town repetition is required for this text-only
  batch. Font assets/metrics, runtime code, saved layouts, and opt-in generation
  settings remain unchanged. Broader missing dialogue is the next content task.

### Shop-service dialogue and native menu choices

- Added 22 complete English shop-service/sale/order/disposal messages: twelve
  Nook records and ten twin-shopkeeper records. Each approval retains the exact
  N64 choice IDs and selection order instead of importing the GameCube action
  arrangement. The only existing candidate changed is `select:0009`, whose
  native Japanese asks for today's turnip price; its original fourteen-byte
  translation is `Turnip prices?`, not the GameCube Other things submenu label.
- Implemented exact, individually hash-bound `native_choices` adaptations.
  Each source/reference must contain one approved menu, with equal choice count,
  an exact offset, and the complete native command. The builder independently
  requires the final adapted hash. Other commands, fields, capacity, and actor
  arguments keep their normal checks. No runtime or saved structure changes.
  Full GameCube text remains in ignored inputs/generated candidates.
- The two twin-shopkeeper records `172A/1737` remain withheld because their
  speaker/echo controls differ after the menu correction. Existing font assets,
  metrics, English line/page breaks, and pause intent are retained. Eleven
  additional conservative layout warnings are queued for the later polish pass.
- The four new native-choice tests pass, together with existing reference-match
  and controller groups. The combined 32-test reference batch passes in 4.753
  seconds at `build/tests-shop-menu-reference-batch-01.log`. This meaningful
  content batch does not repeat the full 389-test baseline run. Python compilation
  and whitespace checks pass.
- `build/smoke-shop-menu-01` passes all 22 complete native cartridge message
  loads and six referenced choice-label loads, including the full corrected
  turnip label. The fresh four-MiB run records 143 steps, 28 native calls, and
  74 memory assertions. Buffer/module guards, full checkpoint restoration, and
  graceful shutdown pass; FlashRAM remains blank and the Pak unchanged. Ordinary
  menu selection, sale/order gameplay, and echo rendering remain batch/human
  playthrough work, not claimed by these isolated loader calls.
- `build/shop-menu-pilot/animal-forest-halfwidth.z64` has SHA-256
  `620180612973a02ca95590b6bd89a87eb8e58ea2d4585d676cea2df765425e60`;
  its verified round-trip UPS has SHA-256
  `1ad1654fc1ea381e67d493cd039fdfddf3dae511e2da1531ed0610077686d403`.
  The current candidate file contains 10,441 edits, including 9,186 reference
  dialogue candidates, ten original dialogue drafts, and all 460 choices
  (459 reference labels plus the original price label). The original main-bank
  audit leaves 2,556 records without candidates, including 1,625 with Japanese
  static text. There are 1,365 conservative layout warnings. Detailed reports
  remain in `build/shop-menu-candidates/` and `build/shop-menu-coverage/`.

### Earlier N64 shop text and human-playthrough handoff requirements

- Filled the sixteen remaining records in the native `02DC..02F0` shop range.
  Five reviewed cross-ID matches use complete later English shop responses;
  eleven original drafts preserve every native command/argument and all purchase
  exits. The GameCube same-ID slots are empty. Reachability remains unestablished,
  so these are text-coverage additions, not newly proven gameplay interactions.
  Existing candidates and reserve records `02F1..02F4` are unchanged.
- The combined reference batch passes 33 tests in 4.485 seconds at
  `build/tests-native-shop-reference-batch-01.log`. Native-command-preserving
  draft checks include both `02E6/02E5` purchase exits. No new runtime or font
  code is required; no full-suite or full intro repetition is needed for this
  content-only batch.
- All sixteen complete native cartridge loads pass in
  `build/smoke-native-shop-01`: 89 recorded steps, sixteen native calls, and fifty
  memory assertions. Buffer/module guards, complete checkpoint restoration, and
  graceful shutdown pass. FlashRAM remains blank and the Pak unchanged. Ordinary
  caller progression and final wording/layout review remain separate checks.
- `build/native-shop-pilot/animal-forest-halfwidth.z64` has SHA-256
  `1a3609f102134c048a6f825f5d80c28bbfa2c86c32599d645bcf225e46d08535`;
  its verified round-trip UPS has SHA-256
  `294e248e74aded61b659f7e3b1a4472989f3f1de534639e5f7d42809a36af495`.
  The candidate file has 10,457 edits: 9,191 reference dialogue candidates,
  21 original dialogue drafts, and all 460 choices among the covered banks.
  The original main-bank audit leaves 2,540 records without candidates, including
  1,609 with Japanese static text. Reference layout warnings remain 1,365;
  original drafts still need their separate presentation review. Reports remain
  local in `build/native-shop-candidates/` and `build/native-shop-coverage/`.
- Added `docs/PLAYTESTING.md` for the final human test-build handoff, concise bug
  reports, save-backup discipline, and batched fixes. It does not require the user
  to act during development, schedule a playthrough now, or count planned tests
  as completed evidence. The validation matrix's choice row now reflects the
  existing twenty-byte and native four-row/cancellation evidence.

### Favour/task responses with original native actor requests

- Added 25 complete English dialogue candidates covering failed-favour reactions,
  apologies/reassurance, and a rejected-advice response. Reviewed IDs and original
  request values are in `specs/ACTOR_REQUESTS.md` and the source/reference/payload-
  bound approval records. All 10,457 existing edits remain unchanged; the only
  candidate-file difference is these 25 additions.
- Verified native `09` and `0C` wrappers, shared parser, order setter, and dispatch
  table against the original code. `09` writes NPC0 row four and `0C` quest row
  nine, at `object + 0x10 + 20*row + 2*index`. They are not interchangeable
  presentation commands. Each approval restores the original N64 slot-five
  request and exact value while retaining the complete native actor-command
  sequence and English wording/layout. No general opcode conversion is enabled.
- Added five host tests covering exact replacement, stale evidence, bad offsets,
  values and schemas, duplicate/changed actor requests, all 25 retail records,
  and the independent builder payload guard. The combined 44-test reference
  batch passes in 5.128 seconds at
  `build/tests-actor-request-reference-batch-01.log`. The complete prior 389-test
  baseline is not repeated for this content-only batch; shared reference groups
  and the whole-content build are checked together.
- `build/smoke-actor-request-01` passes 267 recorded steps, fifty native calls,
  and 132 assertions in a fresh four-MiB process. Each complete English message
  loads from the cartridge, then its actual native request is dispatched into
  an isolated order table. Only the original row-four/index-five value changes;
  all other entries, including quest row nine, and adjacent/module guards match.
  Complete checkpoint restoration and graceful shutdown pass; FlashRAM remains
  blank and the Pak unchanged. Subsequent actor actions, animation, friendship,
  and quest traversal remain combined gameplay/human-playthrough checks.
- `build/actor-request-pilot/animal-forest-halfwidth.z64` has SHA-256
  `cd4502abb05beb489a1f9642b315081f1d2301a1c3fa772e7e93d8fb94fa5870`;
  its verified round-trip UPS has SHA-256
  `34c86ccca585c1e945e4ec9b79b0160ed43514f78cad3522d15ee4acc4a98785`.
  The candidate file has 10,482 edits: 9,216 reference dialogue candidates,
  21 original dialogue drafts, and all 460 choices among the covered banks.
  The original main-bank audit leaves 2,515 records without candidates, including
  1,584 with Japanese static text. Reference layout warnings remain 1,365.
  Candidate/rejection/coverage details remain local in
  `build/actor-request-candidates/` and `build/actor-request-coverage/`.
- Runtime code, approved font metrics/assets, saved structures, and opt-in mail
  generation settings remain unchanged. Follow-up read-only field inspection
  identifies the actual player/town-name consumers and their global sources;
  no added-field permission is enabled without individual meaning/context review.

### Reviewed current-player/current-town dialogue insertions

- Added 26 complete English candidates using individually approved `1A`/`2F`
  insertions. Native instruction review establishes current-player name reads
  through `80136FD8` and current-village name reads through `800950D8`, returning
  `80129E00`. These fields do not use actor-prepared free-string slots. Complete
  native/reference meanings are reviewed for the selected resident conversations;
  separate other-player and destination-town fields remain intact.
- Implemented `available_fields` approvals with complete source/reference/final
  hashes, exact added-command sets, typed validation permissions, and independent
  builder checks. Only current player/town fields are supported, only for the
  resident main-message `reference_layout` policy. Other field requests, actor
  changes, flow changes, format errors, and expansion bounds keep their checks.
  Controller, menu, actor-request, sequence, and alias permissions do not transfer
  into this approval. GameCube wording, manual lines/pages, and pauses remain.
- Seven new host tests pass, including all 26 retail pairs, stale/altered evidence,
  article-prefix reference hashes, wrong scopes and added sets, overflows, flow
  changes, and independent builder rejection. Since the shared validator changes,
  the complete suite runs once for the batch: 406 tests pass in 176.659 seconds,
  recorded at `build/tests-global-fields-full-01.log`.
- `build/smoke-global-field-01` passes 339 recorded steps, 53 native calls, and
  194 assertions in a fresh four-MiB process. All 26 complete cartridge messages
  and 27 added insertions pass through their actual native sources/dispatcher.
  Complete messages, lengths, colour prefixes, cursor positions, unchanged source
  names, buffer/module guards, verified consumer code, the English suffix return,
  and checkpoint restoration pass. FlashRAM stays blank, the Pak unchanged, and
  shutdown is graceful. This is not ordinary actor traversal or visual/hardware
  acceptance; those remain batched gameplay and human-playthrough requirements.
- `build/global-field-pilot/animal-forest-halfwidth.z64` has SHA-256
  `014835ffbd32087b491b17707c04c9395f16f84936d6e0ee209308f16f0c7a6a`;
  its verified round-trip UPS has SHA-256
  `7539e80ad9a8b44bda450ea989bf62fbf90ab70d0b00194413d0bc6711de472d`.
  The candidate file contains 10,508 edits: 9,242 reference dialogue candidates,
  21 original dialogue drafts, and all 460 choices among the covered banks.
  All 10,482 existing edits are unchanged. The original main-bank audit leaves
  2,489 records without candidates, including 1,558 with Japanese static text.
  There are 1,382 conservative reference-layout warning records. Reports remain
  local in `build/global-field-candidates/` and `build/global-field-coverage/`.
- The full missing-field wording audit identifies incompatible Harvest Festival,
  meteor-shower, tailor-shop, and travel/storage references. They remain withheld
  for native-specific translation, not a general name-field import. Twenty-seven
  additional catchphrase-only candidates have plausible native meanings and
  matching remaining flow/bounds, but need the distinct speaker-context audit.
  Their IDs and the native-specific draft queue are recorded in `WORK_QUEUE.md`.
  Runtime code, font assets/metrics, saved layouts, and generation settings stay
  unchanged; all candidates still require final review.

### Original N64 advice and Controller Pak dialogue

- Added seven original drafts for `0945`, `11F1`, `147F`, `14CF`, `14FE`,
  `1BD3`, and `1BD4`. They translate native errand-note advice, sunlight/time
  advice, post-wait conversations, the named-record erasure warning, and both
  post-office original-Pak requirements. The incompatible GameCube tailor,
  town-entry farewell, missing-town-data warning, and blanket traveller-letter
  refusal are not imported.
- Every native command and argument remains except seven colour-span lengths
  changed from nine to fourteen for the full English term `Controller Pak`.
  The new focused test verifies complete command sequences and each highlighted
  term. The erasure warning keeps choice IDs `0029/0062`, branches `0946/0947`,
  and explicit data-loss wording. Phyllis retains the muted aside. No saved
  structures, actions, runtime code, or font metrics/assets change.
- The combined reference batch passes 52 tests in 5.544 seconds at
  `build/tests-native-advice-reference-batch-01.log`, including the new draft
  test. The 406-test full-suite baseline from the shared-field batch remains
  available; the content-only additions do not repeat the full suite or intro.
- `build/smoke-native-advice-01` passes all seven complete native cartridge
  message loads: 44 recorded steps, seven native calls, and 23 assertions.
  Buffer/module guards, checkpoint restoration, and graceful shutdown pass.
  FlashRAM remains blank and the Pak unchanged. The batch does not execute
  a passport overwrite, ordinary travel, or post-office storage actions.
  Those interactions and final original-draft presentation remain for gameplay
  and human-playthrough review.
- `build/native-advice-pilot/animal-forest-halfwidth.z64` has SHA-256
  `dae1b056ad8bc26e793067b8bd2a1866bfc1e6767e34de25c1bc87c73b2cb5b4`;
  its verified round-trip UPS has SHA-256
  `9f0f151995e3a05cb47b95b7ba116a79f6203f8ec572d306ecf032e96c57f6ef`.
  The candidate file contains 10,515 edits: 9,242 reference dialogue candidates,
  28 original dialogue drafts, and all 460 choices among the covered banks.
  All 10,508 existing edits are unchanged. The original main-bank audit leaves
  2,482 records without candidates, including 1,551 with Japanese static text.
  Reference-layout warnings remain 1,382; original draft presentation is tracked
  separately. Detailed reports remain local in `build/native-advice-candidates/`
  and `build/native-advice-coverage/`. The next queue retains native festival
  drafts, their dynamic fields, and the separately reviewed catchphrase batch.

### Resident-speaker catchphrase dialogue

- Added 27 individually hash-bound resident conversations under the separate
  `speaker_catchphrase` approval. Complete source/reference/output hashes, the
  `native_resident_talk` context, and exact added field `1C` are mandatory.
  Other fields, combined permissions, aliases, new gameplay controls, and changed
  payloads remain rejected. English wording, manual layout/timing, and original
  corresponding actor values are preserved. See `specs/REFERENCE_CATCHPHRASES.md`.
- Audited the actual native talk caller at `8007BF64`, appearance request
  `8009D3E4`, initializer `8009FFB0`, client setter `8009D308`, and catchphrase
  consumer `800A1124`. The current actor passes from demo `E0` through window
  request `2E0` into client `20`; the installed nameplate changes leave the actor
  stores intact. The separate actorless event-message caller is not treated as
  a resident context. Source/meaning evidence is recorded separately for all
  27 references; normal per-message callback traversal remains unclaimed.
- Eight new host tests pass. The complete suite passes 415 tests in 175.047
  seconds at `build/tests-resident-catchphrases-full-01.log`, covering all retail
  approvals and independent builder rejection as well as existing regressions.
- The initial native run loads and opens the first complete message and inserts
  its full phrase, then stops at a test cursor assertion. The fixture placed
  the cursor only 384 bytes below the test SP, overlapping nested native call
  workspace. Moving all fixtures lower and leaving over two KiB below the SP
  fixes the harness without changing production code or the expected cursor.
  The initial evidence remains at `build/smoke-resident-catchphrase-01`.
- The corrected complete batch at `build/smoke-resident-catchphrase-02` passes
  688 recorded steps, 91 native calls, and 432 assertions. All 27 messages open
  through the actual request and initializer, which performs real cartridge DMA
  and speaker binding. Thirty insertions cover two distinct ten-character defaults,
  custom input, and a null request clearing a previously assigned client. Complete
  messages/headers, cursors, both full actors/animals, window/message/stack/module
  guards, and checkpoint restoration pass. FlashRAM remains blank, the Pak
  unchanged, and shutdown is graceful. This is not ordinary NPC traversal,
  final page rendering, save/travel validation, or hardware acceptance.
- `build/resident-catchphrase-pilot/animal-forest-halfwidth.z64` has SHA-256
  `63dc82e931bfe78ffc08fcc55559b466de9aa38a592af7d375893e663f5c470f`;
  its verified round-trip UPS has SHA-256
  `11c17f784ce68b16308a45074147c1b0e5cf2bbc2fe83191d735e56e94ecc46d`.
  The candidate file contains 10,542 edits, including 9,269 reference main
  candidates and 28 original main drafts. All previous 10,515 edits are unchanged.
  The original main-bank audit leaves 2,455 records without candidates, including
  1,524 with Japanese static text. There are 1,388 reference-layout warning
  records. Rejections comprise 1,800 unconfirmed identities, 570 control-signature
  differences, 80 unavailable-field references, and six expansion overflows.
  Reports remain local in `build/resident-catchphrase-candidates/` and
  `build/resident-catchphrase-coverage/`. Font/runtime/save structures and optional
  generation settings remain unchanged. Final candidate review is still required.

### Native festivals and ordinary resident date preparation

- Added original drafts `119C`, `27C0`, `11AC`, and `180B` for the N64 carp
  streamers and moon-viewing events. Complete native commands and arguments,
  actor requests, pauses/pages, choice IDs, branches, and terminators remain
  unchanged. The existing eating/refusal responses `27E8/27E9` fit the native
  carp joke and remain unchanged. These are drafts, not final reviewed text.
- Added the optional `--english-dialogue-dates` patch for the ordinary resident
  overlay. Three native year/month/day preparation calls use the existing
  English formatters within the unchanged ten-byte fields. The leap-month branch
  uses a complete ten-byte resident literal and removes only its obsolete HI/LO
  relocations. Six instructions and two relocation entries change; overlay,
  BSS, field, save, and resident reservation sizes are unchanged. Native calendar
  conversion and schedules remain intact. Full source/module/literal guards and
  exact installed-file dependencies protect the dated drafts. Basic candidate
  builds explicitly withhold dependent drafts without the option.
- The native table covers 2000–2032; dates outside that table and failed-conversion
  handling remain separate audit items. Birthday `34/35` insert item fields,
  not the moon-viewing free fields `3C/3D`, and are not claimed fixed here.
- Independent resident builds match SHA-256
  `bc3ea5e77daba273146d4ea6a858b4e5e4b604ae14b5b20e9db9d5dca5f14f22`.
  Linked size remains 22,720 bytes with 1,856 free; public function/storage
  addresses remain unchanged. Module-bound creator and generation-test artifacts
  are rebuilt. The first host regression finds a host-only nonterminated-string
  warning and two stale generated artifact bindings. An explicit ten-character
  initializer and refreshed artifacts resolve them; MIPS output is unchanged.
  The corrected 423-test suite passes in 196.205 seconds at
  `build/tests-dialogue-dates-full-02.log`. The basic-candidate compatibility fix
  also passes nine focused date tests, including two new selection tests.
  The final complete suite passes all 425 tests in 175.706 seconds at
  `build/tests-dialogue-dates-full-03.log`. The basic non-module candidate set
  and ROM also build successfully at `build/native-festival-basic-candidates/`
  and `build/native-festival-basic-pilot/`, withholding only the two dated drafts.
  The full candidate set regenerates unchanged with explicit date support.
  The NPC letter-show scenario generator verifies the exact combined overlay
  and prepares all nine window cases; those windows are not rerun in this batch.
- `build/smoke-native-festival-01` passes 442 steps, 102 native calls, and
  184 assertions. The real cartridge overlay loader performs relocation and
  clears BSS. Fifty-three preparations cover years, all months/days, and bounds;
  thirteen native conversions cover both moon dates in 2000, 2001, 2004, 2026,
  2030, and 2032, plus the 2001 leap month. Six full message loads and eight
  actual insertions cover all four drafts and different years. Complete saves,
  RTC restoration, other fields, heap/stack/module guards, allocation release,
  checkpoint restoration, blank FlashRAM, unchanged Pak, and graceful shutdown
  pass. This is not ordinary seasonal selection or hardware acceptance.
- `build/native-festival-pilot/animal-forest-halfwidth.z64` has SHA-256
  `88fa0d72f415661660d1b00ee9f4023beb010f42715edb323e15b392167dd3d7`;
  its verified round-trip UPS has SHA-256
  `367ca386877eedb42c6068f15e048da63bc1e00b3fc684e942fed6f1c8bc088d`.
  Overlay SHA-256 is `512686b2e4d74e6b1fead4c72e2eab09ac17ab406361c67449a34903963eb3c8`;
  relocation SHA-256 is `8f1a312b27e72fcc3be0f01110d6e76fc17e5e8529f7270120cb486648de597d`.
  `build/smoke-festival-full-01` passes all ten independently checked four-MiB
  train-to-town tests across 188 steps, including module-memory guards.
- The full candidate file contains 10,546 edits: 9,269 reference main candidates
  and 32 original main drafts, with all 460 choices unchanged. All previous
  10,542 edits remain unchanged. The native main-bank audit leaves 2,451 records
  without candidates, including 1,520 with Japanese static text. Reference
  rejections comprise 1,800 unconfirmed identities, 570 control-signature
  differences, 76 unavailable-field references, and six expansion overflows.
  The 1,388 reference-layout warnings are unchanged. Reports remain local in
  `build/native-festival-candidates/` and `build/native-festival-coverage/`.
  Optional generation settings and approved font assets/metrics are unchanged.
  Normal seasonal gameplay and final draft review remain for the combined
  gameplay and human-playthrough passes.

### Native seasonal conversations and related advice

- Added 21 original drafts in `translations/n64-seasonal-conversations.json`:
  six shrine/queue conversations, eight moon-viewing conversations, five
  spring/winter conversations, and the fullness/travel-stock responses.
  All complete native commands and arguments are preserved, including the slow
  New Year's proverb recital. The first focused check catches two omitted
  one-frame pauses in that draft; both are restored before building/testing.
- The complete spring exchange `1F6B/1F77/1F78` retains choices `011E/0128`
  (`Maybe...` / `That's not true!`), both branches, and native quest requests
  `0C/5/0003` and `0C/5/0067`. The GameCube spring-training/groundhog exchange
  is not imported. `1EB7` keeps inviter field `26`, not player field `1A`.
  Other native topics retain the shrine, dumpling offerings, rice-cake rabbit,
  returning insects, winter fishing/neighbours, and other towns' shop stock.
- Three new host tests check all original hashes, complete ordered controls,
  expansion limits, layout using the approved advances, spring action order,
  quest values, and inviter identity. The complete suite passes all 428 tests
  in 176.758 seconds at `build/tests-native-seasonal-full-01.log`.
- `build/smoke-native-seasonal-01` passes all 21 complete cartridge message
  loads in one fresh silent four-MiB process: 114 recorded steps, 21 native
  calls, and 65 assertions. Full messages/headers, adjacent/module guards,
  restored stack/checkpoint, blank FlashRAM, and graceful shutdown pass.
  This tests text loading, not shrine/seasonal actor progression, travel,
  final presentation, ordinary saving, or hardware compatibility. Runtime code
  and module bindings are unchanged, so no repeated train or mail-window batch
  is performed for these content additions.
- `build/native-seasonal-pilot/animal-forest-halfwidth.z64` has SHA-256
  `823753ec45c6f646f6b0849d3ddd5f880b98b0f4f81be486891fda54dae4e715`;
  its verified round-trip UPS has SHA-256
  `ab59c4c718a83b7de676a6f4148055d601307d63bd243aeb2784acb0fd7b7c42`.
  The candidate file contains 10,567 edits: 9,269 reference main candidates
  and 53 original main drafts. All previous 10,546 edits and all 460 choice
  labels remain unchanged. The main-bank audit leaves 2,430 records without
  candidates, including 1,499 with Japanese static text. Reference rejections
  comprise 1,797 unconfirmed identities, 559 control-signature differences,
  69 unavailable-field references, and six expansion overflows. The 1,388
  reference-layout warnings are unchanged; original-draft presentation is
  tracked separately. Reports stay in `build/native-seasonal-candidates/` and
  `build/native-seasonal-coverage/`.
  Comparing every extracted DMA file with the festival build finds changes
  only in main text, its pointer table, and the DMA directory's expected size
  and physical-address rows. All code, overlays, font data, and wider resources
  are unchanged; bytes outside the DMA rows in its container are also retained.
- The remaining moon references `1EA2/1EDD/1EE7` and secret-spot `1F09` have
  broadly matching meaning but different actor controls. Their next audit
  should retain matching English reference text under a scoped native-control
  review. The GameCube `aNPC_check_manpu_demoCode` reads NPC0 slot zero for
  animation selection; this alone is not proof of N64 values or consumer
  bounds and does not authorize relaxing the current command guard.

## 2026-09-07: resident expressions and complete late-night introduction

- Audited native NPC0 slot-zero animation selection in shared overlay `008681F0`
  and its six 42-entry primary/secondary tables. Added eighteen individual
  source/reference/output-bound approvals for complete GameCube introductions,
  moon conversations, a secret spot, dusk-road fear, the heat challenge, and an
  interrupted home visit. Other actor requests, fields, gameplay controls, and
  buffer limits remain guarded. The adapter's ordinary defaults are unchanged;
  the independent builder rejects modified approved text. A wider 255-record
  expression-only mismatch pool is a review queue, not blanket approval.
- Extracted the existing strict native relocation model as a shared helper.
  This fully verified NPC overlay uses two explicit source constants: an
  indexed item-table base and the exclusive BSS end. Ordinary mail callers keep
  their original outside-pointer rejection. Host checks cover two relocation
  bases; actual native loading independently matches the full relocated file
  and zeroed BSS. No production loader or animation code changes.
- `build/smoke-resident-animation-01/` passes 213 native selection cases,
  eighteen complete cartridge loads, and 88 native expression dispatches:
  322 calls, 654 assertions, and 1,616 recorded steps. Whole actor/order outputs,
  saved data, allocation/stack/module guards, restored code/order pointer,
  heap release, checkpoint restoration, and blank FlashRAM pass. The private
  test overlay records calls at the animation-initializer boundary; rendered
  poses and normal resident conversation are explicitly not tested.
  Its ROM hash is
  `3658860fe57f4e63eb188e43028a157eb58701cd3791790797d4415bef3d9d5e`.
- The user asked whether the long late-night introduction could gain pages.
  Implemented complete `04F7 → 083E` using the existing sequence framework.
  The original English record is 798 bytes, with a conservative expanded bound
  of 1,174. Split only its existing wait/newline/page-clear span `[480,485)`
  after the clock joke; resulting bounds are 773 and 419. Preserve all English
  wording, clock reads, pauses, manual lines, remaining page boundaries, native
  actor argument tuples, and final end. No truncation or buffer increase.
  This resolves a build-time capacity rejection, not a reproduced crash.
- Source-hash-bound reserve `083E` has no incoming native message target. The
  pinned executable-section scan finds no matching arithmetic/comparison/
  logical immediate; the only aligned data halfword belongs to the arctangent
  table. The group requires the resident module. AM/PM derives only from an
  available native hour field and a preceding hour in the same replacement
  record, never previous-record state. Basic generation finishes with 10,320
  edits and withholds the complete runtime-dependent group. Partial/manual
  installation without the verified runtime fails.
- `build/smoke-late-intro-01/` passes both complete native cartridge loads,
  the continuation target, both phases of continuing/final termination, buffer
  and module guards, and checkpoint restoration: seven calls, fifteen
  assertions, and forty recorded steps. Normal conversation, rendered clock
  insertion, final layout, ordinary saving, and hardware validation remain.
- All sixteen sequence tests pass. The initial animation host batch passed
  435 complete-suite tests; after the sequence/runtime and independent builder
  checks, `build/tests-late-intro-full-01.log` passes all 439 tests in 183.228
  seconds. Tests include portable native-model/sanitizer checks and local-input
  retail/reference coverage. No repeated train or mail-window batch is needed:
  all production code, runtime bindings, font data/metrics, and saved layouts
  remain unchanged.
- Final build `build/late-intro-pilot/animal-forest-halfwidth.z64` has SHA-256
  `75af44a629c16bd9aa971056c079f417000522d8480eb2bf2dab00feb6b1c84b`;
  its verified round-trip UPS has SHA-256
  `679fb8c2fbe7334488ed67ad13384580104c10a6a8f978e97fd0a8990b402bbf`.
  It contains 10,587 edits: 9,289 reference main candidates, 53 original main
  drafts, and all 460 choice candidates. All previous 10,567 edits remain
  identical. The twenty added main-bank records represent nineteen complete
  English conversations and one continuation slot. Comparing all extracted
  DMA files finds changes only in main text, its pointer table, and the DMA
  directory container. The eighteen animation-test payloads are also unchanged
  in this final ROM; their isolated native proof belongs to the earlier hash
  above, while the continuation test uses this final ROM.
- `build/late-intro-coverage/` records 9,342 main candidates and 2,410 records
  without candidates: 1,479 Japanese static records, nine exact placeholders,
  919 without static text, one Latin record, and two number/symbol records.
  Ten command-only records have dynamic insertions. The reference queue has
  1,796 unconfirmed identities, 540 control-signature mismatches, 69 missing
  fields, and six expansion overflows. Its 1,390 conservative layout warnings
  remain for review without automatic reflow. Continue bounded expression/
  field/topic review and page-boundary splitting where applicable; fishing
  advice `2008` needs native-content review before approval. Full gameplay,
  saves, the later human playthrough, and release/stretch work remain active.

## 2026-09-07: seventy resident and clothing-errand records

- Reviewed and added 65 complete GameCube reference approvals under the existing
  resident-animation contract. Forty cover moving/home/reunion greetings,
  weather, friendship, NPC rumours, furniture rewards/sale, roof colour,
  guessing, collecting, and eyesight. Twenty-five cover clothes-delivery
  requests/reminders, recipients trying on clothes, and failed-delivery returns.
  Each independently binds the original source, complete supplied English
  reference, and final output, retaining every non-expression actor request,
  native field availability, gameplay command order, and expansion guard.
- All wording, manual lines/pages, emphasis, and pauses remain. Four records
  (`0156/0158/2373/2580`) remove only the existing redundant pre-field
  CUTARTICLE command; full English source hashes are checked before adaptation.
  No article text or other English wording is dropped. Native expression codes
  stay inside the already-verified standing-expression set. Special-actor
  Gracie/Booker/Redd/Jingle/Gulliver records are withheld for their own caller
  review, even where the broad signature check appears compatible.
- Added five original drafts to the native seasonal/advice file. `2008` keeps
  all seven fishing pages, including finding shadows, casting where fish can
  see the float, correct reeling timing, and discovering the trick. The English
  reference lacks the last two native instructions. `252D` keeps winter flowers
  rather than the unrelated English weeding complaint. `26F4/26F5` keep White
  Day and March 14, not Groundhog Day/February 2. `26FD` keeps May carp streamers
  and rice cakes in oak leaves, not the autumn Harvest Festival.
  All five preserve every native command and argument exactly and have no
  conservative layout warning. Their expanded bounds are 704, 287, 254, 176,
  and 169 bytes; none requires a split or buffer change. White Day wording
  explicitly describes buying reciprocal gifts, not returning received items.
- `build/tests-resident-conversations-full-01.log` passes all 440 tests in
  181.607 seconds. The final native-draft check passes all four tests, including
  complete command/source identity, layout, native fishing/holiday meanings,
  and the existing spring choice/quest mapping. The final eight-test animation
  check verifies all 83 approved complete references and exactly the four
  declared article adaptations. Logs stay in ignored `build/`.
- `build/smoke-resident-conversations-01/` passes all seventy complete native
  cartridge loads in one fresh four-MiB process: seventy calls, 212 assertions,
  and 359 recorded steps. Complete message headers/text, adjacent/module
  guards, checkpoint restoration, blank FlashRAM, and graceful shutdown pass.
  No expression-selector, train, or mail-window batch is repeated because
  all production code and runtime bindings are unchanged. Normal clothing
  handoff/try-on/return, sale/painting actions, prepared-field display, final
  wording/layout, ordinary saving, and hardware acceptance remain unverified.
- Final ROM `build/resident-conversations-pilot/animal-forest-halfwidth.z64`
  has SHA-256
  `d91e7bba012d28102ed0457e8adb62420a2ad574de49bd4ca2bd769bcee71e83`;
  its verified round-trip UPS has SHA-256
  `1988d69289bb89fee5cd4b2b6b148b73b8743be7f37aeb7c7228e7b26744bc09`.
  Comparing every extracted DMA file with the late-introduction build finds
  changes only in main text, its pointer table, and the DMA directory rows.
  All code, overlays, fonts, resource files, and the directory container's
  non-directory prefix remain unchanged. All previous 10,587 candidate edits,
  including the complete late-night split and all 460 choices, remain identical.
- The candidate file contains 10,657 edits: 9,354 reference main candidates and
  58 original main drafts. The main bank has 9,412 candidates and 2,340 records
  without candidates, including 1,409 with Japanese static text. The other
  classifications remain nine exact placeholders, 919 without static text,
  one Latin record, two number/symbol records, and ten dynamic-only records.
  The reference queue has 1,796 unconfirmed identities, 470 control-signature
  differences, 69 unavailable fields, and six expansion overflows. Its 1,403
  conservative layout warnings remain for later review without reflow.
  Reports are in `build/resident-conversations-candidates/` and
  `build/resident-conversations-coverage/`. Continue individual early parcel/
  favour conversation review and the broader field/topic/overflow queue;
  gameplay, saves, human playthrough, release, and stretch work remain active.

## 2026-09-07: fifty-seven parcel, town-advice, and native event records

- The status-only interruption changed no project state. Resumed the pending
  parcel batch from the authoritative worktree and completed its original
  drafts, verification, and durable checkpoint. The complete translation goal
  remains active; this batch is progress, not project completion.
- Added the read-only `tools/resident_review_queue.py` with five synthetic tests.
  It verifies the native ROM/consumer and complete reference hashes, excludes
  existing candidates and incompatible commands/fields/values/capacity, and
  emits explicitly unapproved comparison rows. It does not write translation
  approvals or install text. A full-hash mismatch in `14FD` was traced to
  reference re-encoding uncertainty; that record is withheld rather than
  accepted by partial wording. Reports retain complete local comparison text
  under ignored `build/`, not committed extracted assets.
- The initial queue contained 164 comparisons. Individually reviewed 49 matching
  resident references: parcels and borrowed items for moved-away owners,
  cancelled searches, refusal/disappointment, pocket capacity, four-player town
  sharing, fruit, Nook's business, selling, mail/boards, friendship, exercise,
  New Year's Eve, Redd's value warning, snowmen, gardens, and deferred/successful
  rewards. Each full source/reference/output hash is bound independently.
  The complete ID/context list is in `specs/PARCELS_TOWN_ADVICE.md`; detailed
  per-record evidence is in `translations/reference_matches.json`.
- The resident-expression permission now has 132 complete approvals. The 49
  references retain all supplied English wording, lines, pages, emphasis, and
  pauses. Exactly `0212`, `0240`, and `0246` remove the existing redundant
  pre-field `CUTARTICLE`, giving seven such adaptations across all approvals.
  Other actor requests, fields, quest/choice/branch commands, and buffer guards
  remain enforced. Special actors are not granted this permission.
- Added eight original drafts in `translations/n64-town-advice.json`.
  `0B8D` retains White Day return gifts, and `0B96` retains May carp streamers
  and the verb-choice joke. `0BA8` retains Thirteenth Night and the annually
  converted lunar ninth-month day 13 in fields `3E/3F`. `0BC9` retains black-bass
  size and the hint not to show catches immediately, not GameCube weight wording.
  `0F35` retains rain, `0F42` yellow-green leftover paint, and `0FA9` the player's
  slightly dissatisfied town rating. `1082` retains Nook's 498,000-Bell final
  renovation, instalments, no further house growth, and the debt obligation;
  the 398,000-Bell English reference is unsuitable.
- All original commands and arguments remain exact except one colour length
  in `1082`, seven to eleven for the complete term `post office`. Its focused
  test admits only that precise change. All twelve Nook pages, original waits,
  pauses, expression requests, and final end remain. Original draft bounds are
  314, 400, 486, 609, 308, 138, 321, and 703 bytes, respectively.
  No split, truncation, buffer increase, or new runtime patch is needed.
- The first layout check flagged the generic ten-fullwidth-cell bounds for
  both free date fields and a prefixed town name. Moved the town-name prefix
  to the preceding English line within its existing page. The date warnings
  remain visible; substituting the longest English month/day proves the guarded
  values fit. The date draft requires the existing complete ordinary-dialogue
  date patch. Its ninth-month day-13 preparation is covered by existing native
  conversion tests; this batch does not claim new rendered date-insertion tests.
  Basic generation completes with 10,108 edits, withholds all three dependent
  moon-viewing drafts, and includes the other seven town-advice drafts.
- `build/tests-parcel-advice-full-01.log` passes all 451 tests in 190.909 seconds.
  The focused runs also pass six original-draft tests, eight animation approval
  tests covering all 132 references, and five read-only queue tests.
- `build/smoke-parcel-advice-01/` passes all 57 new complete cartridge loads in
  one fresh silent four-MiB process: 57 calls, 173 assertions, and 294 recorded
  steps. Complete headers/text, adjacent/module guards, checkpoint restoration,
  blank 131,072-byte FlashRAM, and graceful shutdown pass. No unchanged train,
  expression-selector, or mail test batch is repeated. This does not execute
  ordinary parcels, searches, rewards, painting, seasonal conversations, debt
  repayment, saving, or hardware play.
- The final ROM `build/parcel-advice-pilot/animal-forest-halfwidth.z64` has SHA-256
  `975f9e08554faaaef08a201fc6cb67fae35eea696340384ab44a926c5d450bf1`.
  Its UPS has SHA-256
  `2ee23f1dea971a06f9b7c123c232e90723bb8d6448778d701d9939134b873606`.
  The builder verifies the complete patch round trip. All previous 10,657 edits
  remain identical. Independent comparison of every extracted DMA file finds
  changes only in main text, its pointer table, and the directory rows; the
  directory container's other bytes remain unchanged. All code, overlays,
  fonts, metrics, resident runtime, and resources retain their prior contents.
- Coverage is 10,714 total edits, including 9,403 reference main candidates and
  66 original main drafts: 9,469 main candidates and 2,283 without candidates.
  The latter include 1,352 with Japanese static text, nine placeholders, 919
  without static text, one Latin record, and two number/symbol records. Ten
  command-only records contain dynamic insertions. The reference queue contains
  1,796 unconfirmed identities, 413 control-signature differences, 69 missing
  fields, and six overflows. Its 1,410 reference-layout warnings remain for
  review without automatic reflow. The regenerated expression-difference queue
  contains 107 unapproved comparisons. Reports are in
  `build/parcel-advice-candidates/`, `build/parcel-advice-coverage/`, and
  `build/parcel-advice-review/`. Continue these and broader text/runtime work;
  normal gameplay, saves, final review, patch-only release, and stretch goals
  remain in scope.

## 2026-09-07: ninety-three community conversations and event details

- Verified the previous goal turn as progress: commit `775bb0b` contains the
  completed 57-message parcel/advice batch, its tests, source evidence, and
  updated queue. Continued from a clean matching private-repository checkpoint.
- Reviewed the remaining 107 expression-difference comparisons in full.
  Approved 75 matching standing-resident references with complete independent
  source/reference/output hashes. Topics cover introductions, trades, gifts,
  reward/game outcomes, fishing, Gracie/Redd/Katrina, weather, reading, letters,
  bee stings, turnips, and matching seasonal remarks. The complete context/ID
  inventory is in `specs/COMMUNITY_CONVERSATIONS.md`; each approval records its
  individual semantic evidence in `translations/reference_matches.json`.
  The permission now covers 207 records and still changes no native consumers.
- All 75 references preserve their complete supplied English wording, manual
  lines, pages, emphasis, and pauses. Nine redundant `CUTARTICLE` commands are
  removed through the existing adapter in seven records: `15F6`, `15FF`,
  `16CC`, `16CE`, `1869` (two), `18DE`, and `2C94` (two). Across the project,
  fourteen approved records use this adaptation. No English word is removed.
  Non-expression actor requests, fields, gameplay commands, capacity, and full
  hashes remain guarded; no combined permission is introduced.
- Checked connected native context before approving ambiguous responses.
  `18A3` selects `18B0` through its third option `00A2`, whose existing English
  label is `Orange`; the response concerns the letter's impression, not a roof
  colour. Native `186F` supplies fruit field `34` and recommends planting it,
  while `1870` describes catching the wanted creature, confirming `1869`'s
  fruit-for-creature exchange. Installed parent `207A` and sibling `2771`
  use the same English girls/fluffy-snow joke as `2772`.
  Trade, zodiac, outfit, weight, fishing, and game-result decisions remain
  native. The 1,000-Bell carpet and dynamic price/payment/item fields remain.
- Added eighteen source-hashed originals in
  `translations/n64-community-conversations.json`. White Day and Valentine's
  records retain giving chocolates, reciprocal gifts, cookies, the white-
  chocolate misunderstanding, and March 14. `17FB/1D43` retain the Children's
  Day/Doll Festival/May contrast. `1808` keeps next month's fireworks, not
  July 4. `2811` retains the 6th/7th and remembered 5th, the shrine plaza,
  and the miso-soup comparison. `1689` retains both traditional fireworks
  calls and asking the player's father what they mean.
- `11F3` keeps fish/insects in the player's room without food or tank supplies;
  it does not invent the GameCube museum/Blathers donation feature. `1084`
  keeps Nook's mock sculptor fee, self-made monument, no charge, and thanks
  for the player's custom. All seven native pages remain; Nook receives no
  resident-expression permission. `2837` keeps the countdown invitation and
  finishing year-end cleaning early rather than replacing the ending with
  next-day sports viewing. `27D2` keeps the bitten-moon/Thirteenth Night joke.
- Every original command and argument remains exact. Initial focused validation
  caught a misplaced name/pause in `1084` and a player-field/pause order in
  `2837`; corrected the English placement without changing native controls.
  Final conservative expansion bounds, in draft-file order, are
  `450 237 352 390 130 236 311 164 225 161 192 122 340 300 272 399 490 360`.
  No truncation, split, formatting exception, larger buffer, or runtime patch
  is needed. The original drafts remain marked for final wording/layout review.
- Moon-viewing `180C/2825` retain the annually converted date in fields `3C/3D`
  and require the complete ordinary-dialogue date patch. Both generic free-
  field layout warnings stay visible; the longest English month/day values
  fit with the approved advances. Existing native eighth-month day-15
  preparation tests apply to the unchanged date code; this batch does not
  claim new ordinary seasonal selection or rendered insertion checks.
  Basic candidate generation completes with 10,124 edits, admits the sixteen
  unconditional drafts, and withholds all five date-dependent drafts.
- `build/tests-community-conversations-full-01.log` passes all 457 tests in
  186.203 seconds. Focused checks also pass six original-community tests and
  all eight animation tests covering 207 references and exactly fourteen
  article-adapted records. Complete native controls, source identity, layout,
  meanings, dependency selection, and independent builder guards pass.
- `build/smoke-community-conversations-01/` passes all 93 new complete cartridge
  loads in one fresh silent four-MiB process: 93 calls, 281 assertions, and
  474 recorded steps. Full headers/text, adjacent/module guards, checkpoint
  restoration, blank 131,072-byte FlashRAM, and graceful shutdown pass.
  No unchanged train, expression-selector, or mail batch is repeated.
  Ordinary trades/payouts, letter replies, moving, bee escape, seasons, poses,
  saving, and original hardware remain gameplay/playthrough acceptance work.
- Final ROM `build/community-conversations-pilot/animal-forest-halfwidth.z64`
  has SHA-256
  `e1bc1d345c503f1e9eb429154649644bbea20389c5a49182e6e3f541bc147033`;
  its independently verified UPS round trip has patch SHA-256
  `579a6be7c03a7afc79ce503fefae66f88794044e3ccde5d99c16c3531b0038ae`.
  All previous 10,714 candidate edits remain identical. A comparison of every
  extracted DMA file finds changes only in main text, its pointer table, and
  the DMA directory rows; the directory container's other bytes are unchanged.
  All executable code, overlays, fonts, spacing, runtime, and resources remain.
- The candidate file contains 10,807 edits: 9,478 reference main candidates
  plus 84 original main drafts, giving 9,562 main candidates. The 2,190 main
  records without candidates include 1,259 with Japanese static text, nine
  placeholders, 919 without static text, one Latin record, and two number/
  symbol records. Ten command-only records contain dynamic insertions.
  The rejection queue has 1,794 unconfirmed identities, 322 control-signature
  differences, 69 missing fields, and six overflows. There are 1,424 conservative
  reference-layout warnings, 41 confirmed native aliases, and 70 alias conflicts.
  These counts do not establish final translation or gameplay review.
- Regenerated review output in `build/community-conversations-review/` contains
  fourteen comparisons: Rover `0467`, Gracie `0723`, Booker `0785`, Redd `0789`,
  Jingle `07AA`, Phyllis `08B0/08B2`, sleeping resident `0D3F`, title-menu
  `14A2/14D9`, and Gulliver `2403/240A/240B/240D`. Their actor/state consumers
  need separate review. Reports and coverage are in
  `build/community-conversations-candidates/` and
  `build/community-conversations-coverage/`. The broader identity/field/control/
  overflow queue, general strings and other destinations, normal gameplay,
  saves, final review, patch-only release, and stretch work remain active.

## 2026-09-07 — Native-context references, travel, and sports dates

- Revalidated the worktree at `4dab47c` and resumed the pending identity-review
  tooling. Fixed its legitimate original-fallback/reference-rejection collision
  for `09C7` without allowing ordinary stale collisions or stale source hashes.
- Added read-only `tools/identity_review_queue.py` and seven tests. It exposes
  complete comparisons under the unchanged policy ladder without installable
  translation fields or approvals. The initial pool contains 73 records out of
  1,794 unconfirmed references. All 73 receive individual native/topic review;
  same command compatibility alone does not establish matching meaning.
- Added `complete_reference` source/reference/output bindings and eight tests.
  Explicit decoded-text spans must match exact ordered positions, cannot
  overlap, and preserve the combined newline/non-colour-command sequence.
  Only local colour counts may change. Generator and builder independently
  check complete payloads; all existing field, action, flow, and buffer guards
  still apply. Combined special permissions are rejected.
- Added 64 individual bindings: twelve retain the complete reference unchanged;
  52 use bounded native-context wording changes. They cover shrine menus,
  blossoms, sports/exercise, New Year's visits, cartridge/Pak messages,
  greetings, game advice, Resetti, Disk System, and development labels. Exact
  IDs, native/reference hashes, local spans, final hashes, and review notes are
  in `translations/reference_matches.json`; the contract is documented in
  `specs/NATIVE_CONTEXT_REFERENCES.md`.
- Preserved the native shrine/plaza, July 25th and 6:00 exercise schedule,
  April 20th spring sports where stated, January 1st visits, native menu/quiz
  branches, and native Pak connection instructions. The twelve deletion
  notices retain all actual native actions and exact successors; the English
  power/removal warning refers to the cartridge Game Pak. These messages are
  loaded as data for testing, not executed as deletion actions.
- `2360` uses native Booker/Tom Nook instead of absent Blathers/mayor in its
  reference aside. `23E6` retains full enlarged English emphasis and original
  special-actor/shake/mode/branch commands under existing layout checks. Neither
  gets a standing-resident expression exception. `0670` and `08BF` retain two
  explicit reference typos for the final wording pass.
- Added `18CA` under the existing `map_x_to_r` controller contract. Copper's
  item `251D` and native action arguments stay exact, including the existing
  adapter's restoration of `0A:02:0001` from reference `0000`. All English
  wording except X/R and all presentation commands remain.
- Added eight original drafts in `translations/n64-native-context.json`:
  `0852 085C 0962 0BAA 11CD 2711 27D5 285C`. These retain actual Controller
  Pak travel/return rules, private-letter advice, October's second Monday
  Sports Day, the former October 10th date, the 9:00 a.m. start, and Nook's
  loan/enlargement reminder. The incompatible GC two-card travel, September/
  equinox, skiing, and mayor-gift topics are not imported.
- All native original commands and arguments remain exact except five tested
  sets of named colour-count corrections. Initial layout checking identified
  two five-line draft pages; corrected their original English line divisions
  without changing any native command. Final expansion bounds in file order:
  `650 694 473 620 292 316 331 206`. Generic town-width warnings remain; a
  separate six-fullwidth-cell native-town limit check passes every draft.
- Basic candidate generation completes with 10,196 edits and admits 72 of the
  73 additions. `16A5` correctly remains withheld for unsupported `75` without
  the complete runtime. All eight native-context drafts are available; the
  existing five converted-date drafts remain withheld without their patch.
- All 477 tests pass in 205.285 seconds in
  `build/tests-native-context-full-01.log`, including the 20 new queue, binding,
  and native-context tests. Focused runs also pass all seven queue tests,
  eight binding tests, and five native-draft tests.
- `build/smoke-native-context-01/` passes all 73 complete cartridge-loader calls
  with 221 assertions over 374 recorded steps. Full headers/text, adjacent and
  module guards, checkpoint restoration, graceful shutdown, disabled audio,
  no Expansion Pak, and blank 131,072-byte FlashRAM are verified. This is a
  fresh isolated four-MiB run. It does not execute deletion actions, travel,
  normal saving, seasonal selection, map handoffs, or Resetti animation.
  No unchanged train, mail, or resident-selector batch is repeated.
- Final ROM `build/native-context-pilot/animal-forest-halfwidth.z64` has SHA-256
  `98f735c4e907929cb24c29f4671421eb6d4a96599d709e4151cbe43128a709e5`.
  UPS SHA-256 is
  `5da21e7d0081e2f4e3b48c6944370c99fff71bb404167dc7ec2c6d5625afc5a4`;
  applying it to the verified original reconstructs the complete new ROM.
  All previous 10,807 candidate edits are identical. Every DMA file is
  compared: changes are confined to main text `02000000`, pointers `00CF9000`,
  and the DMA directory rows. The directory container's other bytes, all code,
  fonts, overlays, runtime, resources, and save layouts remain unchanged.
- The candidate file contains 10,880 edits: 9,543 reference main candidates
  and 92 original main drafts give 9,635 main candidates. The 2,117 unfilled
  main records include 1,186 with Japanese static text, nine placeholders,
  919 without static text, one Latin record, and two number/symbol records.
  Ten command-only records have dynamic insertions. The reference queue has
  1,721 unconfirmed identities, 322 control differences, 69 missing fields,
  and six overflows. There are 1,435 conservative reference-layout warnings,
  41 native aliases, and 68 alias conflicts. These are candidate counts, not
  final review or whole-game acceptance.
- The updated read-only same-ID comparison pool is empty. Its unresolved
  unconfirmed records are routed as 1,512 without visible same-ID English,
  102 requiring fields, 38 with control differences, eight overflows,
  36 native non-static records, 24 glyph failures, and one encoding/hash
  uncertainty. The separate fourteen-expression pool remains unapproved.
  Next work remains cross-ID/native-only matching, field/control/overflow
  batches, other string/name/mail destinations, normal gameplay and saves,
  final wording/layout, patch-only release, and artwork/keyboard stretch work.

## 2026-09-07 — Native Pak storage and carp/fireworks dialogue

- Added 26 original post-office/Pak drafts and 25 carp/fireworks drafts in
  `translations/n64-pak-storage-dialogue.json` and
  `translations/n64-carp-fireworks.json`. Fifty fill missing messages; `0BC4`
  deliberately corrects an existing English candidate with the wrong topic.
  All other 10,879 previous edits remain unchanged. The precise message lists,
  retained meanings, and test boundaries are in `specs/PAK_FESTIVAL_DIALOGUE.md`.
- The legacy `08E7/08E8` confuses an absent Pak with unreadable/corrupt storage;
  several later errors are bare terminators. The new drafts distinguish absent
  hardware, read failure, free-byte capacity, note-directory slots, removal,
  repair confirmation/progress/success/failure, and checking. Data-loss warnings
  precede the original repair choices. The service menus keep three choices,
  both native `1BE7` storage targets, and no GC-only fourth action. Phyllis's
  grey inner voice and all native repair/continuation requests remain.
- The only changed control arguments are exact colour counts from nine glyphs
  to fourteen for `Controller Pak`. Every other original command and argument
  stays exact. Final Pak expansion bounds in draft-file order are
  `106 115 181 280 184 244 122 128 167 170 189 251 263 273 149 147
  131 122 91 96 198 227 165 180 114 112`. All fit without layout warnings.
- Carp drafts preserve the father/mother complaint, waterfall symbolism,
  storage-space remarks, inedible streamers, hungry Tango/Dango confusion, and
  backbone joke. `0B98` retains its tunnel-game choices and both branches;
  corrected `0BC4` restores entering the tail, appearing from the mouth, and
  the grown-up joke while retaining native quest request `0C:05:0066`.
  Existing `0BC3`, fireworks replies `182F/1830`, and Pak continuations
  `08E9/08EA` are reviewed and left unchanged.
- Fireworks drafts preserve August, weekly Saturdays, 7:00 p.m., and the pond
  wherever native text states them. Native `2823` explicitly describes viewing
  from the shrine plaza; that distinction remains. All festival commands and
  arguments are exact. Focused layout validation caught an overwide new line
  in `119E`; shortened that original draft line without changing any command.
  Generic town-width warnings in `27C2/2816` stay visible. Separate checks using
  the native six-fullwidth-cell town limit pass every draft; no reflow or
  warning suppression is introduced.
- All eight focused tests pass. The complete suite passes 485 tests in
  198.850 seconds in `build/tests-pak-festivals-full-01.log`. Basic candidate
  generation completes with 10,246 edits and all 51 new/corrected drafts;
  the five existing date-dependent drafts remain appropriately withheld.
- `build/smoke-pak-festivals-01/` passes 56 complete cartridge-loader calls,
  170 assertions, and 289 recorded steps in a fresh silent four-MiB process.
  The run includes every edited record and the five connected unchanged
  replies above. Complete headers/text, adjacent/module guards, checkpoint
  restoration, graceful shutdown, and blank 131,072-byte FlashRAM pass.
  Both test save-write permissions are false. These calls only load text;
  they do not execute repair, deletion, storage menus, seasonal selection,
  normal actions, normal saves, or real-console tests. No unchanged train,
  resident-selector, or mail batch is repeated.
- Final ROM `build/pak-festivals-pilot/animal-forest-halfwidth.z64` SHA-256 is
  `3705072e0d6ce916d7ec812fedaf02fb22f18989d3c44c99077695bad1fc6b85`.
  UPS SHA-256 is
  `7d86d9589d9203b02d5266fd4586414814cbeb60c043db4bf41fe0c1faf9e9df`;
  applying it to the verified original reconstructs the complete new ROM.
  Comparison of every extracted DMA file against the native-context pilot
  finds changes only in main text `02000000`, pointers `00CF9000`, and DMA
  directory rows. The directory container's other bytes, executable code,
  overlays, fonts, runtime resources, and save structures remain unchanged.
- The candidate file contains 10,930 edits: 9,542 reference main candidates
  plus 143 original main drafts give 9,685 main candidates. The 2,067 unfilled
  records comprise 1,136 Japanese static records, nine placeholders, 919
  without static text, one Latin record, and two number/symbol records.
  Ten command-only records contain dynamic insertions. The 2,068 reference
  rejections contain 1,673 unconfirmed identities, 320 control differences,
  69 missing fields, and six overflows. There are 1,435 conservative reference
  layout warnings, 41 aliases, and 68 alias conflicts. None of these counts
  establishes final semantic review, reachability, or gameplay acceptance.
- Regenerated both read-only review queues against the new candidate file.
  The same-ID comparison pool remains empty, with 1,466 lacking visible
  same-ID English, 102 requiring fields, 36 control differences, eight
  overflows, 36 native non-static records, 24 glyph failures, one encoding/hash
  uncertainty, and the separately classified original fallback. The expression
  pool still contains fourteen unapproved special-context messages. Reports
  are in `build/pak-festivals-{identity,expression}-review/`; coverage is in
  `build/pak-festivals-coverage/`. Native-only/cross-ID content, control/field
  work, wider destinations, normal gameplay/save validation, final review,
  release preparation, and both stretch goals remain active.

## 2026-09-07 — Complete overlong phone, furniture, and letter conversations

- Revalidated the pending Pak/festival work and its terminal test reports,
  updated living documentation, and committed/pushed `0e26d7a`. Confirmed a
  clean worktree, matching remote main, and private repository visibility.
  Continued with complete overlong references rather than abbreviating them.
- Added five exact sequence approvals covering ten new records:
  `047C → 0486 → 046F`, `08F4 → 0921`, `08F8 → 2B05`, `08FA → 2B06`, and
  `0910 → 0A26`. The last `046F` is an existing external destination, not a
  reused slot. Topics are Rover's repeat phone call, lazy/cranky/snooty
  furniture advice, and cranky letter-sharing advice. All 10,930 previous
  candidate edits remain unchanged. Contract: `specs/LONG_ADVICE_SEQUENCES.md`.
- Full conservative expansion bounds are 1,049, 1,031, 1,259, 1,053, and
  1,079 bytes. Part bounds are respectively `155/912`, `535/514`, `623/654`,
  `667/404`, and `541/556`. The replaced existing wait/newline/page-clear spans
  are `[132,137)`, `[452,457)`, `[540,545)`, `[584,589)`, and `[458,463)`.
  All complete English wording, manual lines, remaining pages, pauses, and
  native field/actor/flow meaning remain. No buffer enlargement is needed.
- Rover's `06/07` phone-mode pair stays wholly in the second record, followed
  by its original `0E046F` and `01`. Furniture explanations retain complete
  hold-A push/pull/rotate and tap-A dresser/radio instructions, gift context,
  decorating remarks, and work/life advice. `08F8` includes all pages after
  the legacy's first linked part; this project does not use legacy slot `0914`.
- The explicit Boolean sequence-member article flag permits only the existing
  redundant `74`-before-string adaptation. `08FA` removes one such command
  immediately before its already-native item field `31`. The full unmodified
  reference hash is checked before adaptation, all slices must agree, the
  entire adapted reference is covered, and each final output hash is guarded.
  Strengthened complete reference reconstruction checks also apply to unsliced
  records. No unknown opcode, new field, or arbitrary deletion is accepted.
- `0910` keeps `75` immediately with its following catchphrase in part two.
  Auditing treats this existing one-shot capitalization as presentation only
  with the resident runtime. Its entire group requires that runtime; unrelated
  protected/range/flow controls gain no permission. Basic generation has
  10,254 edits, adds the other eight records, and retains every earlier basic
  edit. Both `0910/0A26` are withheld without the runtime, as are existing
  gated sequences and the five date-dependent drafts.
- The five selected native slots contain source-bound reserve text and only
  a final `00`. Whole-bank message target scanning finds no incoming script
  branches. A separate pinned executable/data scan finds no matching arithmetic,
  comparison, or logical immediate and no aligned non-executable halfword for
  any selected slot. Tests repeat these exact checks. This is slot-specific
  evidence, not a general indirect-flow or unreachable-record proof.
- Added nine focused tests covering complete reconstruction, capacity, native
  fields/phone mode, basic/runtime selection, malformed or stale article
  approvals, unrelated-command rejection, slot scans, and batched checkpoint
  structure. The first existing-sequence test run exposed only the two expected
  total-count assertions; updated those from `22/20` to `32/28`. All nine
  focused tests pass in 5.058 seconds. The complete suite passes 494 tests in
  201.225 seconds in `build/tests-long-advice-full-01.log`.
- Extended `tools/sequence_test_scenario.py` to accept repeated `--sequence`
  values and retain every group's checks within one checkpoint. The fresh
  silent four-MiB run in `build/smoke-long-advice-01/` passes ten complete
  cartridge loads, five internal links, Rover's existing external link, and
  both termination phases: 36 native calls, 70 assertions, and 169 recorded
  steps. Complete headers/text, adjacent/module guards, checkpoint restoration,
  graceful shutdown, disabled audio, and blank 131,072-byte FlashRAM pass.
  Both test write permissions are false. No actual phone animation, normal
  actor traversal, gift/handoff, mail interaction, saving, or hardware test is
  claimed. No unchanged train, mail, or resident-selector batch is repeated.
- Final ROM `build/long-advice-pilot/animal-forest-halfwidth.z64` SHA-256 is
  `1e3a6651f2034d1401973a3fc985a7dd06e7e95dccb69a45f925927f091a2984`.
  UPS SHA-256 is
  `835024c12fac6a8c8b49c45247d3b99ecbd1f089bf7ac861b3ae2ecd4d1010fa`;
  applying it to the verified original reconstructs the complete ROM. Comparing
  all extracted DMA files against the Pak/festival pilot confines changes to
  main text `02000000`, pointers `00CF9000`, and DMA directory rows. All other
  directory-container bytes, code, fonts, overlays, runtime resources, and
  saved structures remain unchanged.
- The new candidate file contains 10,940 edits: 9,552 reference main records
  plus 143 original drafts give 9,695 main candidates. The 2,057 unfilled
  native records comprise 1,126 with Japanese static text, nine placeholders,
  919 without static text, one Latin record, and two numeric/symbol records.
  Ten command-only records have dynamic insertions. Five filled slots are
  continuations, not five additional original conversations. Reference
  rejections total 2,058: 1,667 unconfirmed, 320 control differences, 69 missing
  fields, and two direct overflows. Layout warnings total 1,437; the added
  `0486` town-width and `2B06` item-width warnings remain unsuppressed for polish.
  There are 41 aliases and 65 conflicts. Candidate counts are not final review.
- Regenerated coverage and both review queues in `build/long-advice-*`.
  The unconfirmed same-ID comparison pool remains empty, with 1,461 lacking
  visible same-ID English, 102 needing fields, 36 control differences, seven
  overflows, 36 non-static records, 24 glyph failures, one encoding/hash
  uncertainty, and the separately tracked original fallback. Fourteen special-
  context expression comparisons remain unapproved. The two direct overflow
  records are native numeric test loop `0B14` and Resetti `2511`, whose special
  `58:08` ending needs a separate continuation audit. Broader native/cross-ID
  content, fields/controls, destinations, normal gameplay/save validation,
  final review, patch-only release, and image/keyboard stretch goals remain.

## 2026-09-07 — Native service menus, travel conditions, and save dialogue

- Revalidated clean `24e34c2` and continued the bulk native-content work. Added
  `translations/n64-service-save-dialogue.json` with 47 original drafts: ten
  post-office records, four home-gyroid records, fifteen station/Pak records,
  and eighteen six-personality save-question/acknowledgement records. The
  default generator includes the file. No existing candidate is replaced.
  Scope and exact message lists are in `specs/SERVICE_SAVE_DIALOGUE.md`.
- Preserved the separate three- and four-service post-office menus and every
  original choice index/target. The GameCube e-Reader action is not imported.
  Native `08DE` keeps storage target `1BE7`, not the legacy's `1BE8` change.
  `08B2` keeps the native debt-payment option and its complete longer greeting.
  `08D3/08D4` keep amount fields `25/26` and the original `04/19/01` hand-back
  boundary rather than importing the GC `55` command.
- Added native-complete Phyllis `08B0/08B2` without any special-actor expression
  permission. Her queue-full response retains four grey inner remarks, asking
  Pete for an extra delivery, the refusal, and farewell. Every original native
  expression, voice command, and pause remains. These fill two records from
  the previously unapproved fourteen-expression comparison pool.
- Home-gyroid menus keep native Revise/Store an item/Save/Never mind choices
  and their actual `0927/0927/092D/0926` targets. The proceeds acknowledgement
  retains its sound. `0932` is translated as native saving, not the unrelated
  GameCube door menu. Existing connected gyroid candidates fit native topics
  and remain unchanged. Diagnostic `092F/0930/0931` and blank `0933` are not
  given GameCube gameplay actions and remain in coverage/flow review.
- Station drafts correct the native conditions without modifying any action:
  refusal/acceptance of erasing the named existing traveller, free bytes versus
  note slots, organisation/refusal, player/town saving, damaged-Pak repair,
  declined/successful/failed repair, removal, boarding requirements, and write
  failure. The legacy confuses several of these conditions. In particular,
  `0954` incorrectly says repair succeeded after refusal, `0955` describes a
  save instead of completed repair, `0956` describes formatting instead of a
  repair retry, and `0967` describes changed town data instead of write failure.
  The original error/repair branches and `094B` continuations remain intact.
- All six native question/quit/continue triples in `2B09..2B1A` retain choices
  `01AE/01AF`, exact successors, power-off warnings before the save request,
  the wait before completion, expressions, and final `00`. Farewell and
  continued-play wording remain distinct. No GC card-location or save-error
  dialogue is imported into these same-numbered native records.
- Complete native-command comparison permits only 30 exact colour-count
  corrections: fifteen Controller Pak spans, fourteen town-data spans, and
  one station span. All other commands and arguments are exact. Twenty-three
  drafts use the existing layout policy for those counts; 24 use `exact`.
  No new runtime permission, code, buffer, font, or saved-format change occurs.
  Initial layout checks identified a five-line payment page and one overwide
  Phyllis aside; adjusted only original English wording/line divisions without
  changing any command. The two generic payment amount-field width warnings
  remain visible; actual amount preparation/rendering remains unverified.
- Final expansion bounds in draft-file order are
  `94 94 180 180 276 281 97 112 130 114 149 138 169 172 212 123 89
  293 189 258 157 149 121 155 187 186 174 64 225 241 60 218 222 56
  216 242 56 209 228 58 222 243 64 220 242 452 186`.
  All fit the unchanged limit. Nine focused tests pass in 0.244 seconds.
  The complete suite passes 503 tests in 200.909 seconds in
  `build/tests-service-save-full-01.log`.
- Basic generation completes with 10,301 edits and every new draft. All
  earlier basic edits remain identical; existing runtime/date gates still
  apply. The full candidate file contains 10,987 edits and retains all
  previous 10,940 edits unchanged.
- `build/smoke-service-save-01/` passes all 64 complete cartridge-loader calls
  with 194 assertions across 329 recorded steps: all 47 drafts plus seventeen
  connected unchanged messages. Complete headers/text, adjacent/module guards,
  checkpoint restoration, and graceful shutdown pass. The fresh four-MiB
  process has disabled audio, no seed saves, both test write permissions false,
  and blank 131,072-byte FlashRAM. The only injected function is `8009E558`.
  This test does not execute menu selection, payment, repair, data management,
  normal saving, actor actions, or original-hardware checks. No unchanged
  train, mail, or resident-selector batch is repeated.
- Final ROM `build/service-save-pilot/animal-forest-halfwidth.z64` SHA-256 is
  `bb5a04efc85d70ccfb22cbc663b49f5604a1ff2301f65472d17d63967e10ac61`.
  UPS SHA-256 is
  `0199e8a54aa97163ecfeec0dffa94567db4932c1e659c51ca058a8a1c5e1c35c`;
  applying it to the verified original reconstructs the complete new ROM.
  Comparing every extracted DMA file against the long-advice pilot finds
  changes only in main text `02000000`, pointers `00CF9000`, and DMA directory
  rows. Other directory-container bytes, all executable code, overlays, fonts,
  runtime resources, and save structures remain unchanged.
- Coverage now has 9,552 reference main candidates plus 190 original drafts,
  giving 9,742 main candidates. The 2,010 unfilled records include 1,079 with
  Japanese static text, nine placeholders, 919 without static text, one Latin
  record, and two number/symbol records. Ten command-only records contain
  dynamic insertions. The 2,011 reference rejections contain 1,634 unconfirmed
  identities, 306 control differences, 69 missing fields, and two overflows.
  There are 1,437 reference-layout warnings, 41 aliases, and 65 conflicts.
  Original-draft amount warnings remain separately tracked; none of these
  counts establishes complete review, reachability, or gameplay acceptance.
- Regenerated coverage and both review queues under `build/service-save-*`.
  The unconfirmed same-ID pool remains empty, routing 1,461 without visible
  same-ID English, 74 requiring fields, 31 control differences, seven overflows,
  36 native non-static records, 24 glyph failures, one encoding/hash uncertainty,
  and the separately classified original fallback. The expression queue now
  contains twelve special-context records; Phyllis's two originals remove her
  entries without broadening expression permissions. Broader content and
  field/control work, other destinations, normal gameplay/saves, final review,
  patch-only release, and both stretch goals remain active. The legacy audit
  now records verified static message mismatches, not reproduced crash fixes.

## 2026-09-07 — Native seasonal questions, dates, and connected replies

- Added `translations/n64-seasonal-topics.json` with 29 complete original
  drafts: 26 missing conversations and three corrections to existing reference
  replies. Added eight focused tests, the default candidate input, and
  `specs/SEASONAL_TOPICS.md`. Every native command and argument remains exact;
  no expression permission, gameplay request, field, page, pause, choice,
  branch, or terminator is added, removed, or reordered.
- Translated the two moon-viewing events and their nearly-full versus full
  moon distinction, the samurai-era lunar-calendar explanation, and the
  complete preference-for-the-sun joke. Six converted second-moon date drafts
  (`11AE 11AF 180E 270F 2826 2827`) require the existing guarded ordinary-date
  patch. The pond gathering at 6 p.m. remains. No calendar code, RTC value,
  event schedule, or conversion table changes.
- Also covered native Sunday/June fishing questions, morning aerobics and
  rain cancellation, second-Monday-in-October Sports Day, ball tosses, shrine
  blossom viewing, matsutake scarcity, countdown jokes, and Christmas gifts.
  Ten questions retain their complete native choice/reply order. The four
  paired NPC0 row-two/row-eight request sequences remain, including `0002`
  on row eight for the counted-down numbers in `27E3`.
- Corrected `0BC5` to the native fish-size comparison against fish caught so
  far, without the reference end-of-day prize claim. Corrected `27EE/27EF`
  from meteor showers/summer to pond moon viewing, an autumn evening, lunar
  month eight/day 15, dumplings, and asking someone else for the date.
  Current-month `1E` and native quest requests stay unchanged. Seventeen
  connected existing replies remain exact, including approved `27F0` mushroom
  wordplay, native `11CD` Sports Day details, and the `2847` small aside.
  Shared `2833` choice-label wording remains a contextual polish item.
- The final draft layouts retain seven conservative date-width warning
  records: the six converted-date messages and current-month reply `27EE`.
  Independent host layout checks substitute all twelve English months and
  31 ordinal days, checking 372 combinations for each of those seven drafts.
  All fit without reducing other dynamic-field bounds or suppressing generic
  warnings. This checks width, not native runtime insertion or seasonal
  selection. Every draft fits the unchanged 1,024-byte expansion limit.
  A first draft's unsupported semicolon and five-line fishing page were
  corrected before the final build, without changing native commands.
- Eight focused tests pass in 0.621 seconds. The complete suite passes
  511 tests in 202.944 seconds in `build/tests-seasonal-topics-full-01.log`.
  Basic generation has 10,321 edits: twenty newly filled entries and all
  three reply corrections, with six new date drafts correctly withheld.
  The full candidate file has 11,013 edits: 26 newly filled entries and the
  three corrections. All other 10,984 earlier edits remain identical; no
  earlier candidate disappears from either build.
- `build/smoke-seasonal-topics-01/` passes 46 complete native cartridge loads,
  140 assertions, and 239 recorded steps: all 29 drafts plus seventeen
  connected unchanged replies. Complete headers/text, adjacent/module guards,
  restored checkpoint, and graceful shutdown pass. The process is silent,
  fresh, and four-MiB, with no seed saves and both test save-write permissions
  false. FlashRAM remains 131,072 erased bytes. The only injected function
  is `8009E558`; no choice, actor-request dispatch, event, prize award,
  date insertion, save action, or hardware gameplay is executed. The existing
  train, mail, resident selector, and calendar-native batches are not repeated.
- Scenario SHA-256 is
  `bb8fcad93d0b01724c7e9d775a130f691feb62050b4dfcb1e867dae1dad7a2ae`.
  ROM `build/seasonal-topics-pilot/animal-forest-halfwidth.z64` SHA-256 is
  `f319afaa06827f7962b922becabc124106a67ad2fef6001508543a77ac15532c`.
  UPS SHA-256 is
  `87d635f9781b17139cf19843f340ceb3d1ecb3b3717a7625c34c791a6ebb239c`;
  applying it to the verified original reconstructs the complete ROM.
  Every extracted DMA file was compared with the service/save pilot: only
  main text `02000000`, pointers `00CF9000`, and DMA directory rows differ.
  Other directory-container bytes, executable code, fonts, overlays, runtime
  resources, and saved structures remain unchanged.
- Main coverage is 9,549 reference candidates plus 219 original drafts,
  giving 9,768 candidates. The 1,984 unfilled records include 1,053 with
  Japanese static text, nine placeholders, 919 without static text, one Latin
  record, and two number/symbol records. Ten command-only records contain
  dynamic insertions. Reference rejections number 1,985, including 1,632
  unconfirmed identities, 293 control differences, 58 missing fields, and
  two overflows. There are 1,436 reference-layout warnings, 41 aliases, and
  65 conflicts. The original fallback fills one reference rejection.
- Regenerated coverage and review queues under `build/seasonal-topics-*`.
  The unconfirmed same-ID comparison pool is empty: 1,461 lack visible
  same-ID English, 73 need fields, 31 differ in controls, seven overflow,
  36 are native non-static records, 24 fail glyph encoding, one needs
  encoding/hash review, and one has an original fallback. The twelve
  special-context expression records remain unapproved. These counts do
  not establish reviewed translation, unreachable records, or gameplay
  acceptance. Remaining content, other text destinations, ordinary events,
  dynamic rendering, normal saving, final review, patch-only release, and
  both stretch goals remain active.
- Audited the three-hour progress report against the repository after the
  user challenged the repeated rough percentage. At the 15:14 checkpoint
  `11685fb`, main candidates numbered 9,342; the committed service/save
  checkpoint has 9,742, and this batch has 9,768. The interval therefore
  added 400 committed candidates and 26 pending this checkpoint, not merely
  the last 26-message batch. The repeated overall estimate had no measured
  basis for the claimed less-than-one-point change. Chat reporting now
  distinguishes actual candidate changes from unmeasured overall estimates.

## 2026-09-07 — Startup travel and Controller Pak warning translation

- Added `translations/n64-startup-pak.json` with 35 original drafts across the
  six native startup speakers: six capacity warnings, five write errors, six
  duplicate-return confirmations, six accepted-copy notices, six cancellations,
  and six mid-operation removal errors. The sixth write error `14DB` already
  has suitable English and remains unchanged. Added the default candidate input,
  eight focused tests, and `specs/STARTUP_PAK_DIALOGUE.md`.
- Capacity messages retain the native START/reset data-deletion instructions,
  removal of an unused Pak, A-button acknowledgement, and six actual start
  targets. No same-ID GameCube rumble menu is imported. Write errors describe
  writing, not an added read failure. All original `05` formatting controls
  remain, without borrowing GameCube card-slot fields.
- All six duplicate-return prompts retain both field-26 insertions and warn
  that the earlier returned player's record will be erased before `5E` and
  choices `0066/003D`. Both successors and request `09/9/0001` stay exact.
  Accepted copies name Controller Pak as the source and cartridge as the
  destination; power/removal warnings remain before `59:04` and `09/9/0001`.
  All six post-transfer continuations remain. Cancelled returns instead ask
  for Pak removal and an A press before the native start prompt.
- Mid-operation removal keeps each native explanation, including concern for
  the precious record in `1440`, losing track of progress in `1468`, the extra
  catchphrase in `1490`, and no extra initial pause in `14E0`. These messages
  do not become GameCube missing-town-card errors. They keep return-to-title,
  reinsertion, and restart instructions, not a new runtime recovery routine.
- All commands are exact except 101 highlight counts: 59 Controller Pak,
  eighteen controller, six START button, twelve A Button, and six cartridge
  spans. The six N64 spans stay unchanged. Tests check the complete command
  stream with only these substitutions and each full following term. Initial
  original-draft line-width findings were resolved by splitting only those
  draft lines; all 35 final layouts have no warning, and every expansion fits
  the unchanged 1,024-byte buffer. No font metric or GameCube line is changed.
- Eight focused tests pass in 0.228 seconds. The complete suite passes
  519 tests in 200.333 seconds in `build/tests-startup-pak-full-01.log`.
  Full generation has 11,048 edits and basic generation has 10,356. Every
  new draft is present in both; all 11,013 and 10,321 earlier edits respectively
  remain identical. No optional runtime requirement or approval is added.
- `build/smoke-startup-pak-01/` passes 48 complete cartridge loads, 146
  assertions, and 249 recorded steps. It includes all 35 drafts and thirteen
  unchanged messages: six start prompts, six post-transfer continuations,
  and `14DB`. Complete headers/text, adjacent/module guards, restored
  checkpoint, and graceful shutdown pass. The fresh four-MiB process has
  audio disabled, no seed saves, and both test save-write permissions false.
  Its 131,072-byte FlashRAM stays erased. The only injected function is
  `8009E558`; no erasure, transfer, real confirmation/cancellation, title-menu
  traversal, warning rendering, saving, or original-hardware test is performed.
- Scenario SHA-256 is
  `b57a34866b0270078ad37cf78a2a20a7683214ffc0a938619b83fddf1ed5f8eb`.
  ROM `build/startup-pak-pilot/animal-forest-halfwidth.z64` SHA-256 is
  `0a880b8701776e0553c1b6c99851e3a754659bde188ad7ff14f198dd5e51cb0f`.
  UPS SHA-256 is
  `0e748d78717c02eff2e48bae3536cb81804c9795102051b9aa7b6cafe5b190af`;
  applying it to the verified original reconstructs the complete ROM.
  Comparing every extracted DMA file against the seasonal-topics pilot shows
  only main text `02000000`, pointers `00CF9000`, and DMA directory rows change.
  Other directory-container bytes, executable code, overlays, fonts, runtime
  resources, and saved formats remain unchanged.
- Coverage has 9,549 reference candidates plus 254 original drafts, giving
  9,803 main candidates. The 1,949 unfilled records include 1,018 with Japanese
  static text, nine placeholders, 919 without static text, one Latin record,
  and two number/symbol records. Ten command-only records contain dynamic
  insertions. The 1,950 reference rejections comprise 1,608 unconfirmed IDs,
  293 control differences, 47 missing-field records, and two overflows. The
  original fallback fills one rejection. Reference layout warnings stay at
  1,436, with 41 aliases and 65 conflicts.
- Regenerated coverage and both queues in `build/startup-pak-*`. The
  unconfirmed same-ID pool is empty, with 1,461 lacking visible same-ID
  English, 49 requiring fields, 31 control differences, seven overflows,
  36 native non-static entries, 24 glyph failures, one encoding/hash review,
  and one original fallback. Twelve special-context expression records remain
  unapproved, including title-menu `14A2/14D9`. Missing startup greetings,
  preparation and menu variants, broader text destinations, ordinary storage
  and gameplay, full review, patch-only release, and both stretch goals remain.

## 2026-09-07 — Complete native startup preparations and menu variants

- Added `translations/n64-startup-greetings.json` with fifty original drafts,
  the default candidate input, eight focused tests, and
  `specs/STARTUP_GREETINGS.md`. Six variants each cover remembered players,
  new faces, returning travellers, visitors, and continued use of the record
  retained during travel. Eleven menus, six clock acknowledgements, and three
  distinct warning/cancellation/identity records complete this batch.
- All eighteen ordinary preparations retain their two native `05` commands,
  the power-off warning before `59:04`/`09:9:0001`, wait, full completion
  dialogue, and final `00`. They are not replaced with GameCube linked
  preparations. The lazy speaker's grey muted aside in `1454`, the repeated
  name in `147C`, and the snooty speaker's final remarks remain.
- Returning travellers copy from Controller Pak to cartridge and keep their
  six native post-wait continuations. Visitors keep separate preparation
  paths and continuations. Both groups retain all four warning-format
  commands and power/removal warnings. Native field order remains, including
  town before player in `145A` and no town field in `14AA/14D2`. Only twelve
  hardware highlight counts change, for six Controller Pak and six cartridge
  terms. `1480` keeps its one-character highlight after the name, using an
  English exclamation mark. The other 44 drafts use exact native controls.
- Six first menus retain Sound settings, Other things, and cancellation,
  with native choices `0070/01B3/0029`. No rumble option or fourth branch is
  added. Five further menus retain demolish-house/rebuild-town/clock/cancel
  order `0072/0073/0071/0029`; existing `143A` remains. All targets and
  `09:9:0003` requests stay exact. Six clock acknowledgements retain their
  continuations without adding the GameCube `5B` command.
- `1437` retains the away-player/items/money warning before its original
  choices and `1438/1439` branches, with `09:9:0007`. `14A2` cancels town
  rebuilding, expresses relief at not disappearing, and returns to `1494`.
  `14D9` retains the identity retry and `09:9:0006`. Neither title speaker
  receives standing-resident expression permissions.
- All fifty complete source hashes and command streams pass. An initially
  overwide original first-meeting line was shortened without changing any
  source command or dropping meaning. Seventeen generic town-name width
  warnings remain. Independently substituting the native six-fullwidth-cell
  town limit makes all fifty draft layouts fit, with every other field at
  its conservative bound. No font, generic limit, or GameCube line is changed.
  All expansions fit the unchanged 1,024-byte buffer.
- Eight focused tests pass in 0.241 seconds. The complete suite passes
  527 tests in 210.441 seconds in `build/tests-startup-greetings-full-01.log`.
  Full generation contains 11,098 edits, retaining all earlier 11,048 edits;
  basic generation contains 10,406 edits, retaining all earlier 10,356.
  Every new draft is present and no existing candidate changes.
- All 53 unique outgoing targets have candidates. The native batch tests
  every new record and 42 unchanged connected candidates in one scenario.
  `build/smoke-startup-greetings-01/` passes 92 complete loader calls,
  278 assertions, and 469 recorded steps. Complete headers/text, adjacent
  and module guards, restored checkpoint, and graceful shutdown pass.
  The fresh four-MiB process has audio disabled, no seeded saves, and both
  test write permissions false; FlashRAM remains 131,072 erased bytes.
  Only `8009E558` is injected. No ordinary startup, selection, preparation,
  erasure, transfer, date insertion, save action, or hardware test is executed.
- Scenario SHA-256 is
  `619e689faa35b353806ddd173c87c4649e648f749d1eed96e8ffb188535947e4`.
  ROM `build/startup-greetings-pilot/animal-forest-halfwidth.z64` SHA-256 is
  `c8e0a92a452c07b63ba396cda7a8a22096027c3586e655b4c8e321003e0eccf2`.
  UPS SHA-256 is
  `69e34fb940d287d8ddf6d7056c0c6db06f9e0edaad490751b226474d9871417e`;
  applying it to the verified original reconstructs the complete ROM.
  Comparing all extracted DMA files with the startup/Pak pilot shows only
  main text `02000000`, pointers `00CF9000`, and DMA directory rows differ.
  Other directory-container bytes, executable code, overlays, runtime
  resources, fonts, and saved layouts remain unchanged.
- Main coverage is 9,549 reference candidates plus 304 original drafts,
  giving 9,853 candidates. The 1,899 unfilled records include 968 with Japanese
  static text, nine placeholders, 919 without static text, one Latin record,
  and two number/symbol records. Ten command-only records have dynamic
  insertions. Reference rejections number 1,900: 1,578 unconfirmed identities,
  273 control differences, 47 missing-field records, and two overflows.
  The original fallback fills one rejection. There are 1,436 reference layout
  warnings, 41 aliases, and 65 conflicts; none proves complete review.
- Regenerated coverage and queues under `build/startup-greetings-*`. The
  unconfirmed same-ID pool is empty: 1,461 lack visible same-ID English,
  33 need fields, seventeen differ in controls, seven overflow, 36 have no
  native static text, 24 fail glyph encoding, one needs encoding/hash review,
  and one has an original fallback. The expression queue has ten unapproved
  records; title-menu `14A2/14D9` leave it through native originals, not new
  expression permissions.
- The native range `13F2..14E1` now has only six unfilled Japanese-static
  records: `13F2/141A/1442/146A/1492/14BA`. Their complete GameCube references
  add unavailable storage field `28` and its colour/possessive clause while
  reordering the date and adding AM/PM `76`. Existing complete-reference
  wording spans deliberately forbid deleting non-colour controls. The next
  step must preserve GameCube calendar/line/pause intent and omit only the
  unavailable device clause with complete source/output checks. Original
  draft selection also needs a module-command gate: it currently appends
  originals directly, whereas the full builder independently verifies runtime
  hooks and rejects unsupported tokens. No unsafe clock candidate is installed.
  Broader translation, other text destinations, ordinary gameplay/storage,
  final review, hardware acceptance, patch-only release, and stretch goals
  remain active.

## 2026-09-07 — Complete opening clock references and draft runtime selection

- Added six complete-reference approvals for `13F2/141A/1442/146A/1492/14BA`.
  Native sources already supply catchphrase, town, year/month/day/hour/minute;
  GameCube storage-location field `28` is absent. Each approval removes only
  that exact highlighted device/possessive clause, retaining `in` and every
  surrounding English word, space, punctuation mark, newline, page, wait,
  pause, calendar order, and successor. AM/PM remains after the hour field.
  Native successors are `13F4/141C/1444/146C/1494/14BC`. No actor, expression,
  available-field, gameplay, buffer, font, or saved-format permission is added.
- Extended the complete-reference schema with a strict boolean
  `omit_startup_storage_location`, limited to those six same-ID records and
  one fixed before/after span each. Full native/reference/output hashes,
  original decoded offsets, required native fields, no native storage field,
  exactly one reference storage field, and unchanged remaining delivery are
  enforced. The independent builder retains its complete-output hash check.
  The original sixty-four wording-only references retain their exact delivery
  tests and fifty-two changed-span count. Added `specs/STARTUP_CLOCKS.md`.
- Shared the existing six implemented extension descriptors between runtime
  command-table construction and original-draft selection. Drafts using actual
  `62/67/72/73/75/76` tokens are withheld without the resident runtime; native
  arguments and glyphs are not mistaken for commands. Unsupported/wrong-size
  extensions fail. Ordinary resident-date requirements remain independent.
  This changes host selection only, not production MIPS code or capabilities.
- All eleven focused tests pass in 1.470 seconds in
  `build/tests-startup-clocks-focused-01.log`. They include every complete retail
  reference and continuation, runtime gating, invalid flags/IDs/spans, duplicate
  storage fields, changed source/output hashes, and independent-builder rejection
  for all six altered payloads and all six missing-runtime attempts. The full
  run passes 537 tests in 205.724 seconds in
  `build/tests-startup-clocks-full-01.log`; that run was started before the extra
  builder-rejection method was added, which is covered by the focused run.
  All eight existing reference-content tests and nine ordinary-date tests pass.
- Full generation contains 11,104 edits, six more than the startup-greetings
  checkpoint. Every earlier edit is identical. Basic generation retains all
  10,406 previous edits and withholds all six new references. The six conservative
  expansion bounds are `373 361 377 396 343 371`; all fit the unchanged limit.
  Each has generic field-width warnings, increasing the reference warning-bearing
  record count from 1,436 to 1,442. No warning is hidden and no line is reflowed.
- `build/smoke-startup-clocks-01/` passes twelve complete cartridge-loader calls,
  38 assertions, and 69 recorded steps: the six greetings plus their six unchanged
  next messages. Complete headers/text, adjacent/module guards, checkpoint
  restoration, and graceful shutdown pass. The fresh four-MiB process is silent,
  has no seed saves, and has both test save-write permissions false. FlashRAM is
  131,072 blank bytes and the Pak is 32,768 blank bytes. The only injected call
  target is `8009E558`. This is not startup selection, live clock insertion,
  normal saving, final rendered presentation, or hardware validation.
- Scenario `build/startup-clocks-scenario.json` SHA-256 is
  `3a821c2f3eda82c0f843d010e9a23262e535cdc01b86cb12d9f15a800ecbc631`.
  ROM `build/startup-clocks-pilot/animal-forest-halfwidth.z64` SHA-256 is
  `5b6a48a30acf578dc07eaf4b93cbd14a7ca8b9e0a3693439b68678a2fd24d885`.
  UPS SHA-256 is
  `f96d48296fed65fadfead4a01f0b6dc7e93817a12f7cde1ee20a6305786afbb9`.
  Applying the UPS to the verified retail ROM reconstructs the complete build.
  Comparing every extracted DMA file against the previous pilot changes only
  main text `02000000`, pointers `00CF9000`, and DMA directory rows in `00019D40`.
  All directory-container bytes outside the table, code, fonts, overlays,
  resident resources, save structures, and other text banks remain unchanged.
- Main coverage is 9,859 candidates: 9,555 reference-based and 304 original
  drafts. Of 1,893 records without candidates, 962 contain Japanese static text,
  nine are placeholders, 919 contain no static text, one is Latin, and two are
  number/symbol records; ten command-only records have dynamic fields. The 1,894
  reference rejections are 1,572 unconfirmed identities, 273 control differences,
  47 missing fields, and two overflows; one rejection has an original fallback.
  There are 41 aliases and 65 conflicts. No Japanese static text remains without
  a candidate in the inspected startup range `13F2..14E1`.
- Regenerated coverage and both review queues. The unconfirmed same-ID comparison
  pool remains empty, with 1,461 lacking visible same-ID English, 27 requiring
  fields, seventeen control differences, seven overflows, 36 native non-static
  records, 24 glyph failures, one encoding/hash review, and one fallback. The
  ten special-context expression comparisons remain unchanged and unapproved.
  Inspected further missing native topics: `087B/1506` describe moving through
  player travel; `2A43` describes winter flowers; `2BC3/2BC5/2BC7/2BC9` are native
  introductions with no previous-town field. Those remain queued, alongside
  broader content, other text destinations, normal gameplay/saves, complete
  review, hardware acceptance, patch-only release, and both stretch goals.

## 2026-09-07 — Native resident topics and complete cross-ID introductions

- Filled 22 missing main messages: eighteen original drafts in
  `translations/n64-resident-gaps.json` and four complete GameCube references.
  Added default draft input, eight focused tests, and `specs/RESIDENT_GAPS.md`.
  Native topics include complete letter/gift instructions, both bulletin boards,
  moving through player travel, errands, umbrella embarrassment, the colour
  game, inventory capacity, train delays, unnamed-person advice, New Year,
  bedtime, and seasonal flowers. No incompatible GameCube actions or actor
  fields are substituted. The final GameCube introductions are
  `2BC3 → 2DD1`, `2BC5 → 2DD3`, `2BC7 → 2DD5`, and `2BC9 → 2DD7`.
- Initially drafted all 22 from Japanese. Full native-record comparison then
  identified the four introduction references, so replaced those four drafts
  before committing. Their complete original/reference/output hashes are bound,
  all GameCube wording and delivery stays exact, and the original NPC0 requests
  and names match. No new runtime permission or schema extension is needed.
  The initial all-draft build/test outputs under `build/resident-gaps-*` are
  superseded by the final `build/resident-topics-*` artifacts below.
- All original commands remain exact except seven highlight lengths in the
  letter/board instructions and a single AM/PM insertion after the native hour
  in `2311`. The three affected drafts use `reference_layout`, independently
  checked against the full native command sequence; fifteen use `exact`.
  Native choices `00DC/00ED → 29A8/29A9` and `0044/003D → 213C/213D` remain.
  Failed-errand request `09:5:006B`, gift `0C:3:0001`, colour-game `0C:5:0003`,
  delay preparation `0C:9:0002` with field `32`, and special ending `58:32`
  remain. No RTC minute is substituted for a train-delay value.
- All eight focused tests pass in 0.340 seconds in
  `build/tests-resident-topics-focused-01.log`; the complete final regression
  passes 546 tests in 195.053 seconds in `build/tests-resident-topics-full-01.log`.
  The shared complete-reference tests now cover 68 unchanged-delivery approvals,
  with the original 52 wording-span adaptations unchanged; the six separate
  clock storage omissions retain their dedicated tests.
  Corrected an initial five-line original page in `02BB` without changing any
  command. Five original drafts retain generic field-width warnings:
  `0850/1506/1C82/2311/23E2`. Checks with six fullwidth town cells, all twelve
  hours and both meridiems, and a ten-digit delay value fit the draft lines.
  Generic bounds remain unchanged; no GC line or pause is reflowed.
- The final full file has 11,126 edits, 22 more than the opening-clock checkpoint.
  All earlier edits are identical. Basic generation retains all 10,406 earlier
  edits and adds 21, giving 10,427; only the new bedtime draft requires the
  resident module and remains withheld. No ordinary-dialogue date patch is
  required by these drafts. All messages fit the unchanged expansion limit.
- `build/smoke-resident-topics-01/` passes 31 complete loader calls, 95 assertions,
  and 164 recorded steps. The nine unchanged connected messages are
  `213C/213D/213E/213F/2140/2141/2142/29A8/29A9`; all outgoing targets in this
  recursively inspected dialogue set have candidates. Complete headers/text,
  adjacent/module guards, checkpoint restoration, and graceful shutdown pass.
  This fresh four-MiB run is silent, has no seed saves, disables both save-write
  permissions, and retains blank FlashRAM and Pak files. The only injected
  function is `8009E558`. The test does not execute choices, errands, gifts,
  moving, letter delivery, bedtime/New Year events, normal saving, or hardware.
- Scenario `build/resident-topics-scenario.json` SHA-256 is
  `031eca6cf3aa8da3e73e7e1e33c5baad93bf65323cbed9d2c17ed065678c6886`.
  ROM `build/resident-topics-pilot/animal-forest-halfwidth.z64` SHA-256 is
  `bcb9ee54b8d23977c64eda0163eb3da130b01d02c49d9677ced55b34fdd9a83e`.
  UPS SHA-256 is
  `6d47e0100527491ed51445288973f72b477134334f5881bed4041e0b68494288`.
  Applying the UPS to verified retail input reconstructs the complete ROM.
  Comparing every extracted DMA file against the opening-clock build changes
  only main text, its pointers, and DMA directory rows. Other directory-container
  bytes, all code, fonts, overlays, runtime resources, and save structures remain.
- Main coverage is 9,881 candidates: 9,559 reference-based and 322 originals.
  Of 1,871 unfilled records, 940 are classified as Japanese static text, nine
  as placeholders, 919 as non-static, one as Latin, and two as number/symbol
  records; ten command-only records have dynamic fields. Reference rejections
  total 1,872: 1,572 unconfirmed identities, 273 control differences, 25 missing
  fields, and two overflows; one rejection receives an original fallback.
  Reference layout warnings remain at 1,442, aliases at 41, and conflicts drop
  to 61. Coverage and both read-only review queues are regenerated; the empty
  same-ID comparison pool and ten unapproved expression comparisons are unchanged.
- Inspected all remaining alias conflicts: three train-demo reserved labels and
  58 exact `よび` reserved labels account for all 61. The same reserved source
  has ten existing candidates, including door/sleep signs and the GameCube-only
  Game Boy Advance instruction at `2B42`. The classifier recognises `ダミー`,
  not these reserved labels. Added a next-action caller/source/import audit to
  the durable queue; do not treat candidate agreement, placeholder text, or
  missing references as reachability or semantic approval. Broader translation,
  normal gameplay/saves, complete review, hardware, release, and stretch goals
  remain active.

## 2026-09-07 — Complete native reserve-label audit and guarded English labels

- Revalidated the pending placeholder work against `3c2beea` and the actual
  source/candidate files. The percentage-explanation turn did not implement new
  translation work; this continuation completed the pending importer guard,
  fallback, classification, tests, build, and native verification.
- `tools/placeholder_text.py` recognises complete native development labels,
  not words merely containing `よび`. The verified inventory contains 360:
  48 dummy, 207 fixed reserve, ten train-demo reserve, and 95 numbered reserve
  records. Unknown data/glyphs remain review items. The shared importer/builder
  guard rejects unrelated English dialogue or changed commands in these slots.
- Fourteen slots already belong to approved complete sequences and remain
  excluded from label fallback, including runtime-disabled groups. All 32
  sequence payloads remain unchanged and pass their complete source/reference/
  output and control checks. No new continuation slot is allocated.
- Preserved 55 complete valid reference labels and their metadata, including
  the event `extra` aliases and compact `Dummy7`. Original label fallback runs
  after reference and alias validation. Its 291 drafts add 283 missing labels
  and correct eight unrelated GC imports: `07DA`, `2AFF..2B04`, and `2B42`.
  These native sources say only `よび`, not shop hours, sleep signs, or Game Boy
  Advance dock instructions. Every other existing candidate remains identical.
- All 346 unallocated labels fit the current font and capacity without layout
  warnings. The 63 numbered normal/peppy labels retain their leading expression
  reset; nine dummy and two trash-reserve records retain continuing end `01`.
  An initial new test expected only nine continuing labels; inspection showed
  native `19C3/19C4` also end in `01`. Corrected the test expectation, not the
  retained native commands.
- Added `tools/audit_placeholders.py` with per-record hashes, source categories,
  native script references, sequence allocations, and independent candidate
  validation. Auditing the previous checkpoint gives 55 valid English labels,
  fourteen approved continuation members, 283 missing labels, and eight invalid
  candidates. The new full audit gives 346 valid English labels and fourteen
  approved members, with none missing or invalid. The basic audit preserves
  twelve enabled continuation members and leaves the two runtime-disabled
  members uninstalled instead of replacing them with labels.
- All 360 labels have no incoming original message-script targets under the
  `0E..15` argument scan. A separate executable/data scan for the eight corrected
  IDs finds one instruction-immediate lead (`boot:8002E658`, word `24042B00`)
  and 24 aligned data-halfword leads. These numerical matches are not established
  message callers. No exhaustive reachability or free-slot claim is made.
- Full generation in `build/placeholder-candidates/` contains 11,409 edits:
  9,551 reference main-bank candidates, 322 original dialogue drafts, and 291
  original label drafts give 10,164 main candidates. The 1,588 unfilled native
  records contain 666 Japanese-static-text records, 919 command-only/non-static
  records, one Latin record, and two symbol/number records. Ten non-static
  records contain dynamic fields. Generator rejections total 1,589: 1,290
  unconfirmed identities, 273 control differences, 24 missing fields, and two
  overflows; one rejection still receives the existing original fallback.
  Alias count remains 41, unresolved alias conflicts become zero, and reference
  warning-bearing records remain 1,442. Label translation is not new gameplay
  conversation coverage. Basic generation contains 10,710 edits, with exactly
  the same 283 additions and eight corrections and no other changed edit.
- `build/tests-placeholder-full-01.log` passes all 557 regression tests in
  207.648 seconds, including eleven new placeholder/audit tests and independent
  builder rejection of every unrelated sign. The subsequent reporting-only
  volume addition passes all seven focused coverage tests in
  `build/tests-placeholder-coverage-01.log`. The full suite is not described as
  rerun after that reporting-only addition.
- `build/smoke-placeholder-01/` passes 52 actual cartridge-loader calls and all
  158 assertions over 269 recorded steps. The sample covers all 31 generated
  label families, every corrected slot, both boundaries of each numbered reset
  range, and all eleven continuing-ending labels. It calls only the native
  loader at `8009E558`; complete headers/text, adjacent/module guards, checkpoint
  restoration, and graceful shutdown pass. Four-MiB memory, disabled audio,
  no seed saves, and both storage-write permissions false are recorded.
  FlashRAM and Pak remain completely blank, with hashes
  `b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260`
  and `ab2a6e04fd3ceb36594f1216c888a1b8bd0a3ba0a94f715a7c7601e98c49ec51`.
- Final pilot: `build/placeholder-pilot/animal-forest-halfwidth.z64`, SHA-256
  `b097cf8e15ca8ababadd548d2faed38634bba7f65af4bfce90fa666b445bc409`.
  UPS SHA-256:
  `bbd307df37d24f77c7f5b113978f134afead7b8c25cd10a8b909d843dcd4bae9`.
  Scenario `build/placeholder-scenario.json`, SHA-256
  `7ac12344549d40efd10d23fd8ecf6d59a89aba9c83a7bf19950d2984630fca61`.
  Candidate file SHA-256:
  `d5a68906ec7732a9fb094d47477e7e2b26d0d6fb85e4f3f2231fe3f801c84432`.
  The UPS reconstructs the complete ROM from the verified original. Comparing
  all extracted DMA contents with the resident-topic pilot changes only message
  bank `02000000`, pointer table `00CF9000`, and the directory container
  `00019D40`; that container is unchanged outside the directory range. Code,
  fonts/metrics, resident resources, and saved structures remain unchanged.
- Refreshed both read-only review queues. The same-ID pool has no new compatible
  unconfirmed candidate; its excluded routes are 1,214 with no visible same-ID
  English, ten missing-field cases, twelve control cases, seven overflows,
  36 native non-static records, ten unsupported-glyph cases, one encoding/hash
  uncertainty, and the existing original fallback. Ten unapproved expression
  comparisons remain in `build/placeholder-expression-review/queue.jsonl`.
- At the user's explicit request, measured text volume across all 29 native
  banks: 603,067 covered source characters out of 746,978 non-whitespace visible
  characters in Japanese-static-text records, reported once as 80.7 percent.
  This weights each translated native ID by its original text length, not its
  English length, and excludes reserve labels, commands, and already-Latin or
  symbol-only sources. It includes 101 English punctuation/dynamic-response
  candidates covering 397 source characters, principally letter-header commas;
  requiring a Latin letter in every English fragment would wrongly omit those
  installed replacements. `text_coverage.py` now records the definition and
  aggregate/per-bank values. Separate partially integrated runtime resources
  receive no extra credit; embedded UI/image text is outside this inventory.
  The measurement is candidate coverage, not final review or overall completion.
- Continue the 666 untranslated Japanese-static-text records, broader native
  field/control matching, all-bank destinations, normal gameplay/saves, review,
  and stretch goals. The first missing gameplay/context candidates include
  `02BD/02CC`, gyroid records `0382..038B`, and several introductions and
  charm-state responses. Early `0001..0012` diagnostics retain separate control/
  capacity concerns and must not be used to displace gameplay-content work.

## 2026-09-07 — Complete gyroid/resident-state dialogue and police explanations

- Previous goal turn made progress: committed/pushed `31aedfa`, completed the
  reserve-label audit, and recorded repeatable all-bank text-volume measurement.
  Revalidated a clean local/remote checkpoint before this content batch.
- Added 21 native-complete drafts in `translations/n64-gyroid-charm-dialogue.json`:
  failed-errand replies `02BD/02CC`, all ten earlier gyroid messages `0382..038B`,
  and resident-state responses `0761/0763/0767/0768/076A/076B/076C/076E/0770`.
  Every complete native command and argument remains exact. Both builds include
  all drafts without new runtime requirements or weakened reference permissions.
- The two favour responses retain native NPC0 slot-five requests `006B/0065`,
  catchphrases, and the original expressions. The gyroid range retains its
  distinct acknowledgement/acceptance/thanks/refusal meanings, three-choice
  owner menu, two-choice visitor menu, and original `0385 → 0386` owner-message
  continuation. No later save choice, house submenu, or new branch is added.
  The saving notice retains the power-off warning, blue/red colours, full
  pause/page order, and continuing ending. Its same-ID English references are
  empty, not translations or evidence of native reachability.
- All nine resident-state records retain command `41`, complete native endings,
  and all existing actor requests. Six complete native second halves are not
  replaced by the GameCube's partial records and `3057..3062` targets beyond
  the native bank. Three records retain the original final row-two/row-eight
  requests. Both two-character shout highlights remain exact over English
  exclamation marks; no font or expression-consumer change is made.
- Added two complete GameCube police explanations with existing hash-bound
  native-choice approvals. `0777` keeps the twenty-item limit, oldest-first
  disposal, prompt collection, and the supplied jokes; `0778` keeps claiming
  lost property, local lack of punishment, and Copper's concern about his role.
  All wording, lines, pages, pauses, and emphasis remain. Only each six-byte
  choice command changes to native `16:002F:000B`; outgoing targets remain
  `0778/077C` and `0779/077C`. Their complete bounds are 833 and 747 bytes.
  There are now 24 native-choice approvals, including the unchanged 22 shop
  records. Builder validation independently rejects changed full payloads.
- Every native draft fits. In file order, conservative expanded bounds are
  150, 141, 82, 51, 57, 171, 64, 50, 54, 99, 175, 81, 213, 276, 212, 205,
  209, 188, 241, 129, and 247 bytes. Only `0385` retains a generic width
  warning (`page_1_line_1_width_816`) for its embedded owner-message field.
  Static surrounding text fits; real custom-owner wrapping has its separate
  tested implementation and is not proved by substituting a short sample.
- `build/tests-gyroid-charm-focused-01.log` passes seven tests in 0.478 seconds.
  An initial test incorrectly expected the reference adapter's audit metadata
  to be empty; its payload was already unchanged. The final test requires exact
  payload preservation and permits only the existing retained-delivery/format
  report entries. No production adaptation was changed for that expectation.
  `build/tests-gyroid-charm-full-01.log` passes all 567 tests in 212.637 seconds,
  including the full repeatable-volume reporting checks and all 24 choices.
- Full generation produces 11,432 edits: 9,553 reference main-bank candidates,
  343 original dialogue drafts, and 291 original label drafts give 10,187 main
  candidates. All previous 11,409 edits remain identical. Basic generation
  produces 10,733 edits, with the same 23 additions and no changed earlier edit.
  The final main audit leaves 1,565 native records without candidates: 643 with
  Japanese static text, 919 without static text, one Latin record, and two
  symbol/number records. Ten non-static records contain dynamic fields.
  Generator rejections total 1,566: 1,280 unconfirmed identities, 260 control
  differences, 24 missing fields, and two overflows; one receives the existing
  original fallback. Reference width-warning records remain 1,442, aliases 41,
  and alias conflicts zero. Volume coverage gains 1,318 source characters,
  reaching 604,385 of the unchanged 746,978-character denominator; no unsolicited
  percentage is reported to the user.
- `build/smoke-gyroid-charm-01/` passes 33 complete native cartridge loads and
  all 101 assertions across 174 recorded steps. The batch includes all 23 new
  messages and ten unchanged connected responses:
  `0760/0762/0764/0765/0766/0769/076D/076F/0779/077C`. Complete loaded headers
  and text, adjacent/module guards, checkpoint restoration, and graceful
  shutdown pass. Only loader `8009E558` is called; the test does not execute
  charm state changes, saving, police choices, item claims, or gyroid actions.
  The fresh four-MiB run has no save seeds, audio disabled, and both storage-write
  permissions false. Isolated FlashRAM/Pak remain blank with hashes
  `b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260`
  and `ab2a6e04fd3ceb36594f1216c888a1b8bd0a3ba0a94f715a7c7601e98c49ec51`.
- Final ROM `build/gyroid-charm-pilot/animal-forest-halfwidth.z64`, SHA-256
  `4cc9932855c35839e28640b2973a85edf6890a0ad683f7223f6d94c5ac81d88b`.
  UPS SHA-256:
  `6db4eaa5c2f9a2ffd1b9a1f39b50e33292bf741236dbce49be1819da817967cf`.
  Scenario `build/gyroid-charm-scenario.json`, SHA-256
  `82fac7d2bb531dd1f0b01cc20d97234b42adcca9409e9727ed5d765e58ce606e`.
  Candidate file SHA-256:
  `281ffdec0f5317762d70ddeb5bde2c12664084accffe13afe9d402d41778276f`.
  UPS application reconstructs the complete ROM from the verified original.
  Against the placeholder pilot, all extracted DMA contents remain unchanged
  except main text `02000000`, its pointers `00CF9000`, and directory container
  `00019D40`. The container remains unchanged outside directory bytes. All
  code, fonts, metrics, runtime resources, and saved structures are unchanged.
- Both read-only review queues are regenerated. The same-ID pool is still
  empty under current compatibility rules; missing visible same-ID references
  drop to 1,204. The other routes remain ten missing-field cases, twelve control
  cases, seven overflows, 36 non-static records, ten glyph failures, one encoding/
  hash uncertainty, and the original fallback. The ten unapproved expression
  comparisons remain; no special-actor permission is assumed from resident tests.
- Native `077E` still needs its take-an-item question instead of the GC ownership
  question. `04D2/04FA` retain queued semicolon-glyph support for complete reference
  text, rather than unnecessary rewritten introductions. The missing `1C00`
  range includes letter-message fragments needing complete source-field and
  donor review. Broader text, runtime destinations, normal gameplay/saves,
  complete review, hardware, release preparation, and stretch goals remain active.

## 2026-09-07 — Complete cross-bank letter-message fragments

- Revalidated the clean `ba3ca96` checkpoint after the requested one-time text
  measurement. The status-only turn did not advance implementation. Continued
  the missing letter-message audit and built a separate, restricted reference
  path rather than weakening the ordinary cross-bank rejection.
- Main dialogue `1BFF..1C3E/1C53..1C5E` contains 76 Japanese fragments with empty
  same-ID GameCube main references. Explicit counterparts are native/English
  `maila:0020..003F`, `mailb:0020..003F`, and `mailc:0034..003F`. Sixty-six
  Japanese bodies equal their native mail counterparts after removing only
  final `7F00` and outer spaces/newlines. Eight individually bound variants
  preserve the same ordered fields: `1C01/1C07/1C22/1C29/1C2C/1C2E/1C33/1C3A`.
  Their differences are greeting grammar, a malformed particle, internal
  whitespace, or a spelling/punctuation error, not missing gameplay content.
- Added `tools/reference_mail_fragments.py` and 74 explicit approvals containing
  native dialogue, native donor, complete English, and final encoded hashes.
  Each donor agrees completely with the legacy English extraction. The final
  text is the whole GameCube fragment plus the native final ending. No English
  space, manual line, word, or field changes. Both generator and independent
  builder reject stale sources/references, changed output, missing ending,
  unsupported glyphs, non-field commands, and unavailable fields. Registered
  validation cannot be bypassed by deleting edit provenance. The ordinary
  resolver still rejects cross-bank matches, and these records do not become
  implicit alias donors or inherit sequence/actor/field exceptions.
- Added two original native-complete drafts in `n64-letter-fragments.json`.
  `1C18` keeps native writer field `24`, not the donor's unavailable `25`;
  `1C1D` retains its greeting, home-loan question, and joking qualification.
  Both preserve every original command and fit without width warnings.
  Complete English reference bounds are at most 136 bytes and require no
  resident extension. Eight reference records retain generic field-width
  warnings: `1C02/1C07/1C11/1C27/1C29/1C38/1C39/1C3A`. No reflow is performed.
- Added ten focused tests covering all native mappings/full English outputs,
  schema and duplicate rejection, source/reference/legacy mutations, strict
  internal-whitespace comparison, explicit variations, unsupported controls,
  added fields, independent builder checks without provenance, and both drafts.
  `tests-letter-fragments-focused-01.log` passes ten tests in 0.563 seconds.
  `tests-letter-fragments-full-01.log` passes all 577 tests in 213.571 seconds
  on the initial 75-message batch. A broader exact-fragment scan then identified
  adjacent `1BFF`, the only additional missing match under this rule. Its
  complete `maila:0020` source/reference was added, and the final focused run
  `tests-letter-fragments-focused-02.log` passes all ten tests in 0.543 seconds,
  covering all 74 references and both drafts. No production logic changed
  between the full-suite run and this final data/test-expectation addition.
- Initial `smoke-letter-fragments-01/` passes all 75 loads, 227 assertions, and
  384 recorded steps. Final `smoke-letter-fragments-02/` passes all 76 complete
  cartridge loads, 230 assertions, and 389 steps. Only native loader `8009E558`
  is called. Complete headers/text, adjacent/module guards, restored checkpoint,
  and graceful shutdown pass. Both runs use fresh four-MiB state, no save seeds,
  audio disabled, and FlashRAM/Pak write permissions false. Final isolated
  FlashRAM/Pak remain blank with hashes
  `b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260`
  and `ab2a6e04fd3ceb36594f1216c888a1b8bd0a3ba0a94f715a7c7601e98c49ec51`.
- Final full generation produces 11,508 edits, with all previous 11,432 edits
  unchanged. The 10,263 main candidates comprise 9,627 reference candidates,
  345 original dialogue drafts, and 291 original label drafts. Basic generation
  produces 10,809 edits and includes every addition without changing earlier
  edits. Main records without candidates number 1,489: 567 Japanese static,
  919 non-static, one Latin, and two symbol/numeric records. Ten non-static
  records contain dynamic insertions and still need caller/control review.
  The generator rejects 1,490 main records, including one existing original
  fallback: 1,204 unconfirmed identities, 260 control differences, 24 missing
  fields, and two overflows. Reference warning-bearing records number 1,450;
  aliases remain 41 and conflicts zero. Source-volume coverage gains 2,008
  characters, reaching 606,393 of the unchanged 746,978-character denominator.
- Final ROM `build/letter-fragments-pilot/animal-forest-halfwidth.z64`, SHA-256
  `be6edf6404b67795056863c213bca39b2b9ffcb4b829b015f0a5096cbf5e6a71`.
  UPS SHA-256:
  `a4041a43f0e933eb4a9fcbb7400ac7ccb6178b22c3408ab68d3e0124ee0a1f17`.
  Candidate SHA-256:
  `2af70e2a05ab789768079af078bc5535190d46c879def1b9f4b034762ed1890a`.
  Scenario SHA-256:
  `272c1608786faf5860ab975d7eea3fd91f3ba5bf71eae8d638de53e4628d0b7c`.
  UPS application reconstructs the complete ROM from the verified original.
  Against the gyroid pilot, only main text `02000000`, pointer data `00CF9000`,
  and directory container `00019D40` differ among extracted DMA files. The
  directory container is unchanged outside its table. Runtime/code/font/name/
  mail resources and saved structures remain unchanged.
- Regenerated coverage and both read-only review queues. The same-ID comparison
  pool remains empty under current rules, with 1,128 absent visible references,
  ten field cases, twelve control cases, seven overflows, 36 non-static cases,
  ten glyph failures, one reference-encoding/hash uncertainty, and one original
  fallback. Ten unapproved expression comparisons remain. Final wording work
  explicitly includes the duplicated pronoun in `1C06` and missing verb in
  `1C2C`, both present in the supplied complete English donor. No final semantic,
  normal-caller, dynamic-field, mail-delivery, save, or hardware approval is
  inferred from this loader batch. Separate remaining dialogue, runtime,
  generation/editor integration, public patch preparation, and stretch goals
  remain active. The font-atlas-edge investigation remains paused.

## 2026-09-07 — Complete native menus and connected answer corrections

- Reviewed 154 same-ID/legacy-agreeing menu references whose complete English
  passes ordinary checks after substitution of the original native menu.
  Approved 135 complete references, bringing native-choice approvals to 159.
  Nineteen mechanically compatible donors were withheld for changed native
  questions, topics, dates, labels, or field preparation. Five receive original
  drafts; fourteen remain explicitly queued in `specs/NATIVE_MENUS.md`.
  Local source/reference hashes and comparison routing are retained in
  `build/native-menu-review.json`. No control-signature match was treated as
  sufficient semantic approval.
- Complete reference wording, manual lines/pages, emphasis, and pauses remain.
  Every approval binds the full native/reference source, one menu offset/span,
  exact original native command, and complete output hash. The host choice
  parser recognises reference-only `74`, retaining it until the existing
  direct-pre-field article adaptation. Native runtime descriptors remain
  unchanged, and unrelated `74` use is still rejected. No extra actor/field,
  gameplay, or buffer permission was added.
- Added `translations/n64-native-menus.json`: five missing native questions,
  five corrected existing replies, and eight shared labels. The original
  questions preserve Booker's take-home meaning, burying/forgetting advice,
  yesterday's bath, the actual third-answer M eye chart, and an affordable
  price. Event replies `0AE5/1212/1218/1219` retain native fireworks,
  April/October Sports Fairs, and two moon viewings. Connected-reply inspection
  also found `1783` incorrectly referring to a mint and THIS morning after
  the bath-yesterday question. Its original draft retains the general native
  denial/forgetfulness and unchanged failure route. All ten dialogue drafts
  preserve every native command/argument and fit the ordinary message buffer.
  Only `077E/29B0` retain explicit-formatting warnings.
- Eight shared labels retain their native meanings: `002F` Tell me!, `0036`
  Again!, `00BF` Moon Viewing, `00C1` Christmas Eve, `00F8` Play it!, `0103`
  Somewhat., `011F` Won't warm you!, and `0130` It's fine!. Their decoded native
  main-bank occurrences total 66. All fit sixteen bytes; the full pilot retains
  the existing twenty-byte implementation. The Circle/X labels remain unchanged
  because 35 menus across 33 records share them between quizzes and shape games.
  Context-specific truth labels and ambiguous none/pear or agreement/refusal
  choices remain required, not globally replaced.
- Added seven retail-input tests covering all 135 complete adaptations, exact
  flow/presentation, builder mutation rejection without provenance, all ten
  native drafts, connected replies, actual answer indices, all eight label
  hashes/capacities/use counts, and the shared Circle/X constraint. The choice
  adapter adds one reference-article test. Initial `tests-native-menus-full-01.log`
  passes 585 tests in 208.798 seconds. After the connected `1783` correction,
  `tests-native-menus-focused-02.log` passes seven tests in 1.787 seconds, and
  `tests-native-menus-full-02.log` passes all 585 tests in 214.401 seconds.
- Extended `tools/shop_menu_test_scenario.py` with repeatable explicit
  `--message-id` selection. All referenced choice labels are derived from the
  actual selected command streams; default selection still includes all
  native-choice approvals. Full built payloads are checked before generation.
  `build/native-menus-scenario.log` records every selected ID: 145 new/corrected
  dialogue records, 23 unchanged connected records, and 126 actual labels,
  including all eight label corrections. The scenario hash is
  `fabeaa8c60f26eff3445587fa63ae069e2be6a53ea9c0e1b2a8b4759324e6b22`.
- `build/smoke-native-menus-01/` passes all 168 native message loads at
  `8009E558` and 126 native label loads at `80065D90`: 294 calls, 632 memory
  assertions, and 1,353 recorded steps. Complete headers/text/labels, padding,
  adjacent/module guards, checkpoint restoration, and graceful shutdown pass.
  The run uses fresh four-MiB state, no save seeds, disabled audio, and both
  FlashRAM/Pak write permissions false. Actual isolated saves remain blank:
  FlashRAM `b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260`,
  Pak `ab2a6e04fd3ceb36594f1216c888a1b8bd0a3ba0a94f715a7c7601e98c49ec51`.
  These loads do not execute item claims, quiz answers, trades, events, ordinary
  menu progression, normal saving, or hardware tests.
- Final full generation contains 11,648 edits, with 140 additions and exactly
  thirteen deliberate changes to the previous 11,508 edits: the five connected
  replies and eight labels above. No earlier entry is removed or otherwise
  changed. The 10,403 main candidates comprise 9,757 reference candidates,
  355 original dialogue drafts, and 291 original development-label drafts.
  All 460 choices are present: 451 references and nine original labels.
  Every candidate main/choice entry was compared with its complete built-bank
  payload: all 10,403 messages and 460 labels match.
- Basic generation contains 10,954 edits, adding 139 dialogue entries and six
  choice entries to its previous 10,809, with seven existing entries deliberately
  corrected and no removals. It admits 134 new reference approvals and all
  eighteen original edits; `0A0A` is withheld without command `62`. Candidate
  generation is not proof of a retail-capacity build: original labels beyond
  ten bytes still require the English choice runtime.
- Main records without candidates number 1,349: 427 Japanese-static,
  919 non-static, one Latin, and two symbol/numeric records. Ten non-static
  records contain dynamic insertions; all retain caller/control review.
  The reference/label generator rejects 1,350 records, including one original
  fallback: 1,204 unconfirmed identities, 120 control differences, 24 missing
  fields, and two direct overflows. Reference warning-bearing records number
  1,469; aliases remain 41, with zero conflicts. Source-volume coverage gains
  6,116 characters, reaching 612,509 of the unchanged 746,978-character
  denominator. This is replacement coverage, not semantic, gameplay, or project
  completion. The requested one-time text measurement uses this definition.
- Final ROM `build/native-menus-pilot/animal-forest-halfwidth.z64`, SHA-256
  `d974f891820e91fcf496b666990a45a32f5b8900da1345f1db46748857d02cb3`.
  UPS SHA-256:
  `c4a807ab441fc1bf22d44e2eda0c0d8f0953d0bbac36340675d657eb99dcf33e`.
  Candidate SHA-256:
  `88ef5a64189c71a909dcd26db169d37020a21e46284c4cc3f696b14d4d282710`.
  UPS application reconstructs the complete ROM from the verified original.
  Against the letter-fragment pilot, only extracted main text `02000000`,
  choices `02400000`, their pointers `00CF9000/00D06000`, and directory
  container `00019D40` differ. The directory container is unchanged outside
  its table; code, font, runtime/name/mail resources, and saved structures
  remain unchanged.
- Regenerated final-hash coverage and both read-only review queues under
  `build/native-menus-*`. The current-rule unconfirmed same-ID pool remains
  empty, with 1,128 absent visible references and the separate field, control,
  overflow, glyph, non-static, and encoding cases retained. Ten unapproved
  expression comparisons remain. Main work continues with missing native
  dialogue, contextual choices, remaining field/actor controls, name/string/mail
  integration, review, saves, and patch-only release preparation, followed by
  the image and keyboard stretch goals. Original hardware and human playthrough
  remain unverified. The font-atlas-edge investigation remains paused.

## 2026-09-07 — Context-dependent English answers and connected replies

- Added nineteen complete-payload approvals in `translations/contextual_choices.json`.
  Fourteen quiz questions use their complete English truth/affirmation labels,
  while unrelated Circle/X shape games retain their existing labels. Five
  further contexts distinguish no interest from pear, trade acceptance from
  refusal, move/stay requests, qualified excitement, and musical knowledge.
  Eighteen menus use the complete supplied English answer pairing; `1FAE`
  retains the native moderate second answer through the existing Somewhat.
  label. All twelve destination-label records remain unchanged.
- Added `tools/contextual_choices.py` and independent importer/builder checks.
  Each mapping requires its native-menu parent approval, complete native/base/
  final hashes, exact menu offset and commands, and every destination label's
  source and complete English hashes. Only existing label IDs may change;
  answer count, index, branches, surrounding wording, lines, pages, and timing
  remain. The builder reverses the exact display menu for every existing
  independent guard, then writes the approved final text. Missing label edits
  withhold generator candidates; mutations fail. No generic control exception,
  native descriptor, new label, buffer, runtime hook, font, or save change is made.
- Added five complete native-menu reference approvals, bringing their total to
  164: `136E/1868/1CE0/1FAE/20CA`. Four original connected replies fill
  `186E/187B/1880/1CE3`. These keep every native command and argument, including
  three emphatic item repetitions, the equal two-way `187B/1880` continuation,
  the distinct refusal routes back to `186E` or onward to `1872`, and the moving
  conversation's complete memories/farewell without a new reference-only menu.
  Their conservative bounds are 358, 144, 144, and 433 bytes; all fit without
  layout warnings. Ordinary trade, moving, quest, and friendship actions remain
  unverified by this content and isolated-call batch.
- Added ten focused tests covering schema, parent/payload/label bindings,
  mutations, exact reversibility, dependency withholding, actual retail cases,
  native branch preservation, unchanged shape contexts, all four drafts, and
  native even-pixel width rounding. The initial nine tests pass in 0.982 seconds;
  after the width-fixture correction, all ten pass in 0.941 seconds. Full suite
  `build/tests-contextual-choices-full-01.log` passes 594 tests in 213.657 seconds.
  The final `build/tests-contextual-choices-full-02.log` passes all 595 tests in
  224.932 seconds.
- Added `tools/contextual_choice_test_scenario.py`. Forty unique message checks
  cover all nineteen menus, four new replies, sixteen unchanged connected
  replies, and one unchanged four-choice shape game. Actual cartridge loading,
  label loading, row setting, width, selection, insertion, and conditional
  dispatch run together. All 42 selection cases retain complete labels and
  indices; all 38 contextual cases reach the original conditional destinations,
  including inverted source branch-command order. Shape-game random outcomes
  and ordinary player interaction are not executed or claimed.
- Two initial native runs exposed test-fixture errors, not production changes.
  Run `smoke-contextual-choices-01` passed a scratch window with zero selected
  length to insertion while selecting into the global choice object. The
  corrected insertion parent is `80142410`. Run `-02` expected 87 pixels for
  an odd-width label, while the retail helper returns 88. Actual instructions
  `8009031C..80090328` round odd totals upward; the pinned GameCube source lacks
  this final step. The fixture and its portable regression now model the retail
  rule. The production ROM and approved glyph advances stayed unchanged through
  both corrections.
- Final `build/smoke-contextual-choices-03/` passes 302 native calls and 484
  memory assertions over 1,195 recorded steps, restores `test.bs1`, and shuts
  down gracefully. Scenario SHA-256:
  `47874aa5a514c045d430fe463da62c207b1f91689d314424c31253fdf1f17b92`.
  The run has four MiB, no seeds, disabled audio, and both save-write permissions
  false. FlashRAM remains
  `b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260`;
  Pak remains `ab2a6e04fd3ceb36594f1216c888a1b8bd0a3ba0a94f715a7c7601e98c49ec51`.
- Full generation contains 11,657 edits: nine additions, fourteen deliberate
  menu-only changes, no removals, and no unrelated changes. Main candidates
  number 10,412: 9,762 references, 359 original dialogue drafts, and 291 original
  development labels. All 460 choices remain unchanged. The rejected reference
  pool is 1,341: 1,204 unconfirmed identities, 111 control differences, 24 field
  differences, and two direct overflows; one has an original fallback. The
  final 1,340 missing main records comprise 418 Japanese-static, 919 non-static,
  one Latin, and two symbol/numeric records. Ten non-static records contain
  dynamic fields. Reference warnings remain 1,469; aliases remain 41 with no
  conflicts. Review queues are regenerated against the final candidate hash.
- Basic generation contains 10,947 edits. It adds six messages, changes one
  existing mapping, and withholds thirteen previously admitted quiz candidates
  whose required complete English labels are unavailable at basic capacity.
  Three additional new reference mappings are also withheld, giving sixteen
  explicit contextual dependency failures; three mappings remain admitted.
  This is deliberate dependency enforcement, not truncation or a full-pilot
  content loss. Basic generation alone still does not establish that original
  label drafts beyond ten bytes fit an unmodified retail choice buffer.
- ROM `build/contextual-choices-pilot/animal-forest-halfwidth.z64` SHA-256:
  `1dc097f7b3e3cef99950caf90891f44a68af2c42d385a379e5962231bc6648b4`.
  UPS SHA-256:
  `9b53cfecbb3b08115f98186267f8c98e15639432e082c189bb2c9aa4e03bf582`.
  Candidate SHA-256:
  `34b931bb337230801dcf6022baa422606ea9f0ac1012a36f936bd804ebabb20a`.
  UPS application reconstructs the complete ROM. All 10,412 main and 460
  choice payloads match the candidates; a subsequent read-only measurement
  additionally compares every one of the 11,657 ordinary edits against its
  actual built-bank entry. Only extracted main text `02000000`, its pointers
  `00CF9000`, and the DMA directory container `00019D40` differ from the preceding
  pilot. The container is unchanged outside its table; code, fonts, runtime,
  choice/name/mail resources, and saved structures remain unchanged.
- The explicitly requested one-time measurement recalculates 613,016 covered
  source characters out of 746,978, adding 507 under the unchanged definition.
  The original, candidate, and built-ROM hashes match their reports. This is
  installed replacement coverage across 29 banks, not full semantic review,
  gameplay approval, or a complete denominator for embedded UI/image text and
  separate runtime resources. No overall project-completion claim is made.
- Nine mechanically compatible menu comparisons and separate `1C6F` remain
  withheld for native questions, dates, artwork, field preparation, and meal
  jokes. Further native dialogue, contextual labels, general strings/names/mail,
  special controls, gameplay, saves, review, patch-only release, and stretch
  goals remain active. Early `00C0..00D2` contains real resident return/greeting
  prose; the broader early range must not be declared unused from debug-looking
  neighbours. No reachability or hardware evidence is inferred. The font-atlas
  edge investigation stays paused.

## 2026-09-07 — Complete native return greetings

- Continued from the pushed contextual-menu checkpoint `50ae5d8`, with a clean
  tracked worktree and the private remote verified. The preceding measurement
  supplied new evidence that all 11,657 ordinary edits were present in the
  actual ROM; it did not claim completion. This turn records the completed
  contextual batch, then adds another content batch rather than repeating its
  native selection test.
- Added 35 original dialogue drafts in `translations/n64-return-greetings.json`
  for `00B0..00D2`. All native and legacy sources retain Japanese; every supplied
  same-ID GameCube entry contains only `7F00`. An independent native-prose
  comparison ignoring whitespace and commands finds no identical second native
  record for any of the 35. These remain native-specific drafts, not invented
  reference matches or unreachable-code claims.
- The complete translations retain the different friendly, energetic, sleepy,
  gruff, and teasing voices; month/week absences; concern about illness; furniture
  and decorating reminders; hot-spring wishes; debt-collector and raining-spears
  jokes; late-night remarks; and each reassurance or reprimand. Every native
  command/argument, per-page field sequence, catchphrase repetition, wait/clear,
  total/per-page newline count, and continuing `01` ending remains exact. No
  actor, action, field permission, reference layout, runtime, font, or save
  format is changed.
- Added `specs/RETURN_GREETINGS.md` and seven regression tests. Tests cover
  complete source/control/ending equality, encoding, page/line/field structure,
  month-versus-week identity, repeated catchphrases, native topics, empty donor
  slots, absent exact native aliases, basic/full selection, and conservative
  bounds/layout. The full expansion bounds range from 101 to 344 bytes. All
  35 drafts fit without layout warnings using the unchanged conservative field
  widths; no one-digit absence assumption is needed. Native-only lines were
  adjusted within the original pages before building to fit those full bounds.
- Focused `build/tests-return-greetings-focused-01.log` passes seven tests in
  0.766 seconds. After the final wording adjustment, the complete
  `build/tests-return-greetings-full-01.log` passes all 602 tests in 220.135 seconds,
  including all seven new tests. Candidate generation, building, artifact
  validation, and the native batch complete without a failed run.
- Full generation contains 11,692 edits, adding exactly the 35 new messages
  without changing or removing any of the preceding 11,657. Main candidates
  total 10,447: 9,762 references, 394 original dialogue drafts, and 291 original
  development labels. All 460 choices remain unchanged. Basic generation adds
  the same 35 entries without changing/removing any of its preceding 10,947,
  reaching 10,982. The contextual-label dependencies retain their previous gates.
- The generator rejects 1,306 main records: 1,169 unconfirmed identities, 111
  control differences, 24 field differences, and two direct overflows. One
  receives an original fallback, leaving 1,305 final gaps: 383 Japanese-static,
  919 non-static, one Latin, and two symbol/numeric entries. Ten non-static
  records have dynamic fields. Reference warnings remain 1,469, aliases 41,
  and conflicts zero. Source-volume coverage gains 2,779 characters to 615,795
  of the unchanged 746,978-character denominator. No new percentage or overall
  completion claim is made.
- Reused the existing explicit-ID cartridge-load scenario for all 35 new
  messages. `build/smoke-return-greetings-01/` passes 35 calls at `8009E558`,
  107 assertions, and 184 recorded steps. Full headers/text, adjacent/module
  guards, restored `test.bs1`, and graceful shutdown pass. Scenario SHA-256:
  `d4aab5d201585c43bc882da3df3928707729da87541c9b4ac5a5c47c41c5c99b`.
  The four-MiB run has no seeds, disabled audio, and both save-write permissions
  false. FlashRAM remains
  `b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260`;
  Pak remains `ab2a6e04fd3ceb36594f1216c888a1b8bd0a3ba0a94f715a7c7601e98c49ec51`.
  No ordinary greeting selection, field preparation, actor action, or saving is
  executed by these calls.
- ROM `build/return-greetings-pilot/animal-forest-halfwidth.z64` SHA-256:
  `4d7af4ec1b57aa0b72a59322abd3b04919751c26e40a3a17e82f3fbeae2941e1`.
  UPS SHA-256:
  `9b9cbeae8f7f78067a651b4a6d302fe95b9bd74c827089301d67a1351455859a`.
  Candidate SHA-256:
  `83d8522462dc9948a805c445d649b6fb41eec3332de6ff5542c8b39f2c633b2e`.
  UPS application reconstructs the complete ROM from the verified original.
  All 11,692 ordinary edits match their complete actual built-bank entries.
  Only extracted `02000000`, `00CF9000`, and DMA directory container `00019D40`
  differ from the contextual-choice pilot. The container is unchanged outside
  its table; every code/font/runtime/name/mail/choice resource remains unchanged.
- Regenerated final-hash coverage and both review queues under
  `build/return-greetings-*`. The current-rule unconfirmed same-ID pool remains
  empty, with 1,093 absent visible references and the separate field, control,
  overflow, glyph, non-static, and encoding cases retained. Ten unapproved
  special-expression comparisons remain. The adjacent `00A3..00AF` native
  month-return conversations and broader earlier greetings/test messages remain
  available content work. Normal caller selection, live fields, complete wording
  and presentation review, save/hardware acceptance, general strings/names/mail,
  patch-only release, and the image/keyboard stretch goals remain active.
  The font-atlas-edge investigation stays paused.

## 2026-09-07 — Native daily, move, repeat, and month-return greetings

- The preceding goal turn made progress: the contextual-menu checkpoint and
  35 return greetings were committed and pushed, with full artifact, regression,
  and bounded native evidence. This batch starts from clean `9e16e2e` and
  continues the still-missing native greeting block instead of repeating the
  preceding cartridge-load or selection scenarios.
- Added 85 complete original drafts in `translations/n64-daily-greetings.json`
  for `005B..00AF`: 24 recent-move conversations, 24 daily greetings, 24 repeat
  greetings, and thirteen month-return conversations. All 85 original and legacy
  sources agree in Japanese, all same-ID GameCube slots contain only termination,
  and none had a prior candidate. No reference identity or unreachable-code
  status is invented. Together with the preceding return batch, `005B..00D2`
  now has 120 complete English drafts.
- Preserved every original command/argument, field occurrence and per-page
  sequence, wait/clear, total/per-page newline count, and continuing `01` ending.
  Old/current town fields remain distinct; repeated names and catchphrases are
  retained. Native topics include incomplete unpacking, old-friend visits,
  secret moves, starting over, daytime/evening and sleep distinctions, snacks,
  furniture, gruff reprimands, drinking too much the previous night, and the
  three-kilogram remark. Final native wording review retains the nightlife
  meaning in `00A6` as party animal. No GameCube reference text is reflowed.
- Added `specs/DAILY_GREETINGS.md` and eight focused tests. The tests cover all
  original source/control/page/field/ending checks, complete encoding and bounds,
  both runtime selections, source/legacy agreement, empty English donor slots,
  all native topic groups, old/current town distinction, repeated fields, and
  the more-than-months qualifier in `00AF`. The initial focused run passes all
  eight tests in 0.531 seconds. After the final `00A6` wording adjustment,
  `build/tests-daily-greetings-full-01.log` passes all 610 regression tests in
  287.729 seconds, including all eight daily-greeting tests. Generation, building,
  artifact validation, and the native batch complete without a failed run.
- All conservative expansion bounds fit, from 36 to 370 bytes. Original lines
  are arranged within the unchanged native pages to retain complete numeric
  and old-town fields. Six generic current-town warnings remain for
  `0062/0065/0067/006D/0070/0071`. The existing native `2F` consumer uses a
  six-byte current-town name; `m_land.h` also defines `LAND_NAME_SIZE` as six.
  All 85 layouts fit when substituting six fullwidth cells only for `2F`, with
  every other field retaining its conservative bound. Global capacity/width
  validation is unchanged, and the warnings remain explicit for presentation
  review. This is not proof of live old-town/month field preparation.
- Full generation contains 11,777 edits, adding exactly these 85 messages with
  no changes or removals among the preceding 11,692. Main candidates number
  10,532: 9,762 references, 479 original dialogue drafts, and 291 original
  development labels. All 460 choices remain unchanged. Basic generation adds
  the same 85 records to its previous 10,982, reaching 11,067 with no earlier
  change or removal. Existing contextual-label and runtime gates stay intact.
- The reference/label generator rejects 1,221 main records: 1,084 unconfirmed
  identities, 111 control differences, 24 field differences, and two direct
  overflows. One has an original fallback, leaving 1,220 final gaps: 298 Japanese
  static-text, 919 non-static, one Latin, and two symbol/numeric records. Ten
  non-static records have dynamic fields; all retain caller/control review.
  Reference warning records remain 1,469, aliases 41, and conflicts zero.
  Source-volume coverage gains 4,559 characters, reaching 620,354 of the unchanged
  746,978-character denominator. This remains installed replacement coverage,
  not complete semantic review, live gameplay, or an all-assets denominator.
- `build/smoke-daily-greetings-01/` passes all 85 complete new messages through
  native cartridge loader `8009E558`: 257 assertions and 434 recorded steps.
  Complete headers/text, adjacent/module guards, restored `test.bs1`, and graceful
  shutdown pass. Scenario SHA-256:
  `710b47bbbb51ecb28aa46f5486f5a1b98995eae4f2f024bd66eff6f520661d94`.
  The run has four MiB, no seeds, disabled audio, and both save-write permissions
  false. FlashRAM remains
  `b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260`;
  Pak remains `ab2a6e04fd3ceb36594f1216c888a1b8bd0a3ba0a94f715a7c7601e98c49ec51`.
  It does not run ordinary greeting selection, actor actions, field preparation,
  moving, or saving. No earlier native batch is rerun.
- ROM `build/daily-greetings-pilot/animal-forest-halfwidth.z64` SHA-256:
  `f651a8cad9496f458430273578b55119cb9abbf73ee84629095ed74e627dcd4b`.
  UPS SHA-256:
  `996d63dbc4c7806242ff59d08ae8f6269b66a56b41338582230bd382307655f8`.
  Candidate SHA-256:
  `32d4b28012e28278d66b0d6d1342cba382bb133e379b16cb16001d2168c6eb47`.
  UPS application reconstructs the complete ROM from the verified original;
  all 11,777 ordinary edits match their actual complete built-bank entries.
  Extracted changes are confined to main text `02000000`, its pointers `00CF9000`,
  and DMA directory container `00019D40`. The container is unchanged outside
  its directory table; all code, fonts, runtime/name/mail/choice resources, and
  saved layouts remain unchanged.
- Regenerated final-hash coverage and both review queues under
  `build/daily-greetings-*`. The current-rule unconfirmed same-ID pool remains
  empty; absent visible same-ID references decrease to 1,008. Ten unapproved
  special-expression comparisons and all distinct field/control/overflow/glyph
  cases remain. The next early content block is `0013..005A` introductions and
  reunions, with the separate `0001..0012` development/control samples retained
  as a different audit. Normal caller selection, full wording/presentation,
  general strings/names/mail, control support, gameplay/save/hardware acceptance,
  patch-only release, and image/keyboard stretch goals remain active. The
  font-atlas-edge investigation stays paused.

### 2026-09-07 — Complete native introductions and reunions

- Added 72 original drafts in `translations/n64-reunion-greetings.json` for
  `0013..005A`: 24 introductions, 24 long-absence reunions, and 24 short-absence
  reunions. All supplied same-ID GameCube slots contain only termination, every
  legacy/native Japanese pair agrees, and no identical visible native duplicate
  exists after commands/whitespace are removed. No English donor, reference
  permission, or unused-record status is invented.
- Preserved every original command and argument, field occurrence/order/page,
  wait, clear, page count, and continuing `01` ending. Only `002C` page zero
  changes its five lines to four by combining the interrupted greeting and
  surprise; all questions, names, meaning, and pauses remain. Month/week fields,
  literal more-than-one-month remarks, repeated names/catchphrases, delayed
  recognition, native jokes, and qualified friendship invitations remain.
  The blue/gunjou joke uses navy blue as an original English colour escalation.
  No actual GameCube reference is reflowed.
- Added `specs/REUNION_GREETINGS.md` and ten focused tests for selection in both
  runtime modes, source/control/ending/encoding/bounds, page and field sequences,
  the one line-count exception, distinct units and fields, repetitions, native
  topics, and supplied-source provenance. The focused run passes ten tests in
  0.645 seconds. After a test-expression cleanup, the final full regression run
  `build/tests-reunion-greetings-full-01.log` passes all 620 tests in 287.234
  seconds, including the ten final reunion checks. No failed test, generation,
  build, or cartridge run occurs in this batch.
- All complete conservative expansion bounds fit at 148–620 bytes. Original
  English line placement retains complete meanings and full absence/old-town
  field bounds. Nine generic current-town width-warning records remain:
  `0034/0045/0046/0049/004E/0050/0057/0059/005A`. Every draft fits when only
  current-town `2F` is substituted with the verified six fullwidth cells; every
  other field retains its conservative estimate. No global validator is
  narrowed. These host checks do not establish live field preparation.
- Full generation adds exactly 72 messages to 11,777, reaching 11,849 with no
  earlier changes or removals. Main candidates number 10,604: 9,762 references,
  551 original dialogue drafts, and 291 original development-label drafts.
  All 460 choices remain unchanged. Basic generation adds the same 72 to its
  previous 11,067, reaching 11,139 with all earlier edits unchanged. The complete
  `0013..00D2` range now has 192 English drafts, not completed gameplay review.
- Reference/label rejections number 1,149: 1,012 unconfirmed identities, 111
  control differences, 24 field differences, and two overflows. One has an
  original fallback, leaving 1,148 main gaps: 226 Japanese-static-text, 919
  non-static, one Latin, and two number/symbol records. Ten non-static records
  contain dynamic fields, with caller/control review retained. Reference warning
  records remain 1,469, complete-native aliases 41, and conflicts zero.
  Source-volume replacement coverage gains 8,762 characters, reaching 629,116
  of the unchanged 746,978-character denominator. This is not semantic review,
  gameplay acceptance, or an all-assets denominator.
- `build/smoke-reunion-greetings-01/` passes all 72 complete cartridge message
  loads through native `8009E558`, with 218 assertions and 369 recorded steps.
  Full headers/text, adjacent/module guards, restored `test.bs1`, and graceful
  shutdown pass. Scenario SHA-256:
  `060b4a1f6c2900fef57f94b211eac0cf344134d7513905f0cddb7cb8929d7d08`.
  The run has four MiB, no seeds, disabled audio, and both save-write permissions
  false. FlashRAM remains
  `b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260`;
  Pak remains `ab2a6e04fd3ceb36594f1216c888a1b8bd0a3ba0a94f715a7c7601e98c49ec51`.
  It does not execute actual introduction/reunion selection, live field
  preparation, moving, ordinary saving, or hardware behaviour.
- ROM `build/reunion-greetings-pilot/animal-forest-halfwidth.z64` SHA-256:
  `11c72c4fa4ff88df90d8ffc8a64c21c447416613e6feaffbb9df122ce2de3d2e`.
  UPS SHA-256:
  `77139c80afae970c7aacdf051fd0d9a7172b2c862a8a9aac48b4b6e44a7535c8`.
  Candidate SHA-256:
  `a3879d2436722f45746dd888d0ec9e86ddc0e403a4c54e10391796277b329b80`.
  UPS application reconstructs the complete verified ROM; all 11,849 ordinary
  edits match their complete actual built-bank entries. Against the daily build,
  extracted changes are only main text `02000000`, its pointers `00CF9000`, and
  DMA directory container `00019D40`. The container is unchanged outside the
  directory table; all other code, fonts, runtime/name/mail/choice resources,
  and saved layouts remain unchanged.
- Regenerated final-hash coverage and both read-only queues under
  `build/reunion-greetings-*`. Current-rule unconfirmed same-ID review remains
  empty; no-visible-same-ID references decrease to 936. The ten unapproved
  special-expression comparisons and distinct field/control/overflow/glyph
  cases remain. The private remote is verified before checkpoint publication.
- Read all eighteen `0001..0012` native samples and supplied same-ID references
  for the next audit. These mix real personality descriptions (`0007/0008`)
  with branching state, colour, position/scale, voice, and syllable timing
  tests. Native `0004` is 694 stored bytes but already has a 1,314-byte
  conservative expansion bound; `000F/0010` terminate through timed-close `58`.
  Do not translate these as generic labels or discard their controls. Keep
  this separate audit alongside broader remaining dialogue, not ahead of all
  other content. Full wording/presentation review, live callers/fields, general
  strings/names/mail, runtime controls, normal gameplay/save/hardware acceptance,
  patch-only release, and image/keyboard stretch goals remain active. The
  font-atlas-edge investigation remains paused.

## 2026-09-07 — Native moving, game-launch, and diagnostic text

- Continued from clean pushed checkpoint `9493c80`. The subsequent one-time
  measurement supplied fresh evidence that all 11,937 current edits are present
  in the actual built ROM; it was progress by new verification, not a new
  implementation batch or a project-completion claim. The pending build,
  coverage, and full-suite handles were collected with terminal success rather
  than restarted. No live prior build or test handle remains.
- Added eight complete originals in `n64-moving-conversations.json` for
  `0FA5..0FA8`, `0FAC`, and `2862..2864`. The native satisfaction question
  retains choices `0103/0104` and replies `0FA8/0FA9`; the unchanged reply comes
  from `n64-town-advice.json`. Five moving remarks retain final `00` with no new
  GameCube-only moving questions or quest actions. Tom Nook's expansion dream
  is retained instead of the unrelated same-ID furniture question. Every
  original command/argument, field occurrence/order/page, wait, and ending
  remains. Bounds are 281–531 bytes. Only `0FA5/2862` have generic `2F` warnings;
  all eight layouts fit six fullwidth current-town cells with every other field
  estimate unchanged. No actual GameCube reference is reflowed.
- Added seven complete NES launch prompts `2B6B..2B71` with the exact supplied
  GameCube furniture names `036A..0370`: Clu Clu Land, Balloon Fight, Donkey Kong,
  DK Jr MATH, Pinball, Tennis, and Golf. Native Japanese titles are individually
  checked; same-ID English main records contain unrelated Memory Card errors.
  All choices, conditional `17B5` links, and continuing endings remain. Only the
  title and question-mark colour lengths change. Bounds are 57–66 bytes with
  no layout warnings. Existing `17B5` and choice labels remain unchanged.
- Added all 99 complete exact native diagnostics: 28 rumour-pattern, 68
  script-bug, and three gyroid debug notices. This fills 73 missing records
  and corrects 26 existing partial imports at `2720..2739` that omitted Script
  bug and the printed number. `2956` keeps its literal `10581`, not inferred
  decimal ID `10582`. The gyroid notices retain `2351/2352/2353`, the debug-report
  request, native By Eguchi credit, page transition, and no imported save action.
  All commands are exact; bounds are 35–113 bytes without layout warnings.
  Explicit diagnostic metadata separates these from original dialogue drafts.
- Added the independent `native_diagnostics.py` source recogniser and complete
  replacement guard to shared candidate/build validation. It rejects partial
  labels, changed numbers, changed controls, and unrelated menus under all
  ordinary policies. Sequence-policy declarations still require the separate
  complete hash-bound approval. Exact source matching rejects false positives,
  unknown tokens, and unexpected native control structure. The coverage label
  catalog and denominator remain unchanged; the 26 corrected English-looking
  labels receive no additional source-volume credit.
- Added twelve focused tests. The initial focused run had one fixture-path
  error looking for `0FA9` in the contextual-replies file; the correct existing
  draft is in the town-advice file. Corrected only that test lookup. Final
  `build/tests-native-misc-focused-02.log` passes twelve tests in 0.849 seconds;
  `build/tests-native-misc-full-01.log` passes all 632 in 281.315 seconds.
- Full generation adds exactly 88 missing records and corrects exactly the
  26 diagnostic labels; every other prior edit remains unchanged. It contains
  11,937 edits and 10,692 main candidates: 9,736 reference candidates, 566
  original dialogue drafts, 291 development labels, and 99 diagnostics. All
  460 choices remain unchanged. Basic generation has the same exact changes
  and reaches 11,227. Every new/corrected candidate matches its versioned draft.
  No runtime/date gate or ordinary bank-count contract is weakened.
- Reference rejection totals 1,061: 935 unconfirmed identities, 100 control
  differences, 24 missing-field records, and two direct overflows. One original
  fallback leaves 1,060 final main gaps: 138 Japanese-static, 919 non-static,
  one Latin, and two symbol/numeric records. Ten non-static entries contain
  fields; no reachability is inferred. Reference warning records remain 1,469,
  native aliases 41, and conflicts zero. Regenerated both final-hash review
  queues; current-rule same-ID eligibility remains zero, no-visible-reference
  entries are 866, and the ten special-expression cases remain unapproved.
- ROM `build/native-misc-pilot/animal-forest-halfwidth.z64` SHA-256:
  `ab38396566ff8f35c356f1dfde6e880caea092f61d8c7154ef8dc214788c0dfe`.
  UPS SHA-256:
  `df82782d1e1d934010bd63791d86635019f65ac2384d1c809db9b0f68fa5d5a7`.
  Candidate SHA-256:
  `561dca1c28cb5c277b1d7528b1f471332c0d3c557b044aca6024b598299162c6`.
  Fresh source/candidate/build hashes and every one of the 11,937 complete
  actual built-bank entries pass. The existing text-volume definition counts
  631,270 installed source characters of the unchanged 746,978 denominator,
  adding 2,154. Embedded UI/images and incompletely integrated separate
  resources remain outside this measurement; no new unsolicited percentage
  or semantic/gameplay completion claim is made.
- UPS application reconstructs the complete ROM. Against the reunion pilot,
  only extracted main text `02000000`, pointers `00CF9000`, and DMA directory
  container `00019D40` differ. The container is unchanged outside its table;
  every other code, font, runtime, name, mail, and choice resource is unchanged.
- `build/smoke-native-misc-01/` passes all 114 new/corrected message loads plus
  unchanged `0FA9/17B5`: 116 calls at `8009E558`, 350 assertions, and 589 steps.
  Complete headers/text, adjacent/module guards, restored `test.bs1`, and
  graceful shutdown pass. Scenario SHA-256:
  `15e75574f2f1ca43d8c42bcbd24d48858bff0ac9956614efdd072a5a236d6f63`.
  The four-MiB run has no seeds, disabled audio, and both save-write permissions
  false. FlashRAM remains
  `b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260`;
  Pak remains `ab2a6e04fd3ceb36594f1216c888a1b8bd0a3ba0a94f715a7c7601e98c49ec51`.
  These calls do not execute ordinary moving selections, actual game launch or
  quit, script-bug conditions, live field preparation, or saving.
- Read all four native travel explanations `0848/0866/0870/087A` and their
  complete supplied references for the next content batch. The English disc
  adds second-Memory-Card and destination-town-data rules that differ from the
  native Controller Pak instructions. Preserve all native advice and bulletin-
  board details; add a guarded existing-page split if complete English needs it.
  No travel draft or new sequence contract is implemented in this checkpoint.
  All remaining dialogue/runtime, general strings/names/mail, full review,
  ordinary gameplay/saves, hardware acceptance, patch-only release, and image/
  keyboard stretch goals remain active. The font-edge investigation stays paused.

## 2026-09-08 — Complete native travel advice and original-text page splits

- Continued after committing and pushing the moving/game-launch/diagnostic
  batch as `90eda2c`. The tracked tree was clean, the repo was private, and
  local HEAD, origin/main, and the actual remote branch all matched. That
  batch and its native verification are completed progress; the full project
  remains active. No subagents, desktop renders, audio, or existing saves were
  used. All build/native handles from that batch were collected successfully.
- Added complete native travel translations for `0848/0866/0870/087A`.
  Their supplied GameCube references explain second-Memory-Card and destination-
  town-data rules, which differ from the original Controller Pak instructions.
  Native `0848` retains reciprocal visiting, boredom, station/train/Pak advice,
  the reminder, other-town bulletin-board writing, later readers, writing for
  that audience, and the home board's equivalent use. The other personalities
  retain jock adventure/romance, cranky invitations and broadening one's world,
  and the snooty frog-in-a-well/country-bumpkin exchange. These are original
  drafts, not new GameCube identities or substitutes for glyph-blocked matches.
- All native commands/arguments, fields/order/page, actor values, pauses, and
  final endings remain except explicit colour-span lengths. The jock's coloured
  two-character call and `04` without `02` inside the station advice remain.
  An in-memory first draft of `0866` omitted one pause; the full native command
  comparison caught it, and it was restored before the versioned draft and
  all test/build runs. The ordinary expansion bounds are 861, 695, and 828.
  Generic `2F` warnings remain on `0848/0866/087A`; all four full layouts fit
  six fullwidth current-town cells without narrowing any other estimate.
- Complete original `0848` is 818 stored bytes with a 1,134-byte expansion bound.
  Added `native_normal_travel_advice`, `0848 → 0A27`, using `[0,460)` and
  `[465,818)` of that complete draft. The existing `[460,465)` wait/newline/clear
  precedes bulletin-board advice. Its replacement is exactly one native
  continuation boundary; the final part retains `00`. Bounds are 663 and 489;
  parts store 467 and 353 bytes. No words, pauses, other pages, or fields are
  removed. Full draft SHA-256:
  `9404a5afb7ae8c6f438cf4966487f5f4aa96c171ee34b104e944e1fe5a6fedd0`.
- Extended the existing sequence framework with explicit `native_original`
  provenance and an embedded complete original draft/hash. Added
  `tools/native_sequences.py`: independent source-kind/schema checks, complete
  native command comparison, and exact indexed original/replacement colour
  commands. Only a nonzero final length byte may change. Native originals
  cannot add actor-source or article-removal permissions. The independent ROM
  builder also reconstructs every full original slice, in addition to existing
  source/part hashes, membership, incoming branches, flow, and capacity checks.
  Re-hashing an incomplete part cannot discard original wording; re-hashing
  all English text cannot silently change native controls. Existing GameCube
  groups retain their complete payloads and original permissions.
- Native `0A27` is the exact letter-show reserve, with source SHA-256
  `90d32ead3827a2e2920a43565ba4e28cd4db7e82eeedf7005ad201fd6b8e4d1f`.
  It has no native message-script incoming target and no arithmetic/comparison/
  logical/load-upper immediate or aligned non-executable halfword in the pinned
  code-section scan. Other inspected reserve numbers had unrelated data hits
  and were not used. This is slot-specific evidence, not exhaustive indirect
  reachability proof. The placeholder audit now accounts for fifteen allocated
  native label slots and 345 unallocated ones; source classification is unchanged.
- Added twelve tests: seven portable native-sequence guard tests and five retail
  content/layout/source/slot tests. Focused
  `build/tests-native-travel-focused-01.log` passes all twelve in 2.344 seconds.
  The initial existing sequence run passed fifteen tests and failed one stale
  basic-mode count expecting 28 instead of 30 members. Updated explicit basic/
  full counts to 30/34 and reserve accounting to include `0A27`. Final
  `build/tests-native-travel-full-01.log` passes all 644 in 292.926 seconds.
  This final suite includes the final original-provenance metadata and every
  existing reference/placeholder guard; no test exclusions are added.
- Both final generation modes add exactly four roots and change only `0A27`
  from its old English reserve label into the guarded continuation. All other
  edits remain identical. Full generation reaches 11,941 edits and 10,696 main
  candidates: 9,736 references, 570 original dialogue drafts, one original-
  dialogue continuation, 290 development-label drafts, and 99 diagnostics.
  All 460 choices remain unchanged. Basic ten-byte-capacity generation reaches
  11,231. A redundant sixteen-byte-choice generation was started after misreading
  the basic comparison flags; its reports are retained separately in
  `build/native-travel-sixteen-candidates/`. The final basic comparison was
  regenerated with the actual baseline's no-runtime flags and passes the exact
  four-addition/one-allocation check. No ROM used that redundant candidate set.
- Reference rejection totals 1,057: 931 unconfirmed identities, 100 control
  differences, 24 missing-field records, and two direct overflows. One original
  fallback leaves 1,056 final gaps: 134 Japanese-static, 919 non-static, one
  Latin, and two symbol/numeric entries. Ten non-static entries contain fields;
  no reachability is inferred. Warning-bearing manifest records total 1,470,
  including the new original sequence's generic town warning; native aliases
  remain 41 with no conflicts. Final-hash review queues have zero current-rule
  same-ID admissions and the same ten unapproved special-expression cases.
- ROM `build/native-travel-pilot/animal-forest-halfwidth.z64` SHA-256:
  `b19f2ce726bfbdb59e23f14386603bdb9e4ccd36d119159213c578e5a3419d8b`.
  UPS SHA-256:
  `43c70bb98f075f78e8b7f3cda153bff05b874f06253e2d00326f4e048f74489f`.
  Candidate SHA-256:
  `a565b47eb3b56ded388998350c8519ec0340d12334b4bb0dfda96b4db5a2a44e`.
  Source, candidate, and built hashes pass; all 11,941 complete installed bank
  payloads match. UPS application reconstructs the entire ROM. Against the
  preceding pilot, only extracted `02000000`, `00CF9000`, and DMA directory
  container `00019D40` differ. The container is unchanged outside its table;
  every other code/font/runtime/name/mail/choice resource is unchanged.
  Measured source volume increases by 1,090 to 632,360 of the unchanged 746,978
  characters. The reused placeholder earns no source-volume credit; no new
  percentage, semantic-review, or project-completion claim is made.
- `build/smoke-native-travel-01/` passes all five complete cartridge loads,
  the internal link assignment, and both continuing/final termination phases:
  ten calls, 25 assertions, and 56 recorded steps. Its scenario combines the
  existing sequence generator and explicit-ID loader generator within one
  identical checkpoint setup/restoration, with both restored scratch checks.
  Scenario SHA-256:
  `3361caeb9858dd6c8d101bd4083aa599964fbd88d991219a67a2a074e0f6d03e`.
  Complete headers/text, adjacent/module guards, restored `test.bs1`, and
  graceful shutdown pass. The four-MiB run has no seeds, disabled audio, and
  both save-write permissions false. FlashRAM remains
  `b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260`;
  Pak remains `ab2a6e04fd3ceb36594f1216c888a1b8bd0a3ba0a94f715a7c7601e98c49ec51`.
  No ordinary conversation, actual travel, board posting, or saving is executed.
- Remaining main text/control/field/glyph work, general strings and full name/
  mail destinations, final wording/presentation review, ordinary gameplay/save
  acceptance, hardware validation, patch-only release, and image/keyboard stretch
  goals remain active. The font-atlas-edge investigation stays paused. The
  original-sequence contract is available for further genuinely native-specific
  overlong text; it is not permission to replace compatible English references
  or reuse arbitrary message slots.

## 2026-09-08 — Complete furniture-name identity approvals

- Continued the uncommitted item-name batch from `b8370d0`. The intervening
  user-requested measurement independently verified all 12,153 installed edits;
  it did not implement another translation batch. The full project remains
  active, including all text, destination integration, review, available normal
  gameplay/save tests, release preparation, and image/keyboard stretch goals.
- Added 179 explicit native-to-GameCube furniture-name identities in
  `translations/item_reference_matches.json`. Each records the Japanese name,
  exact ten-byte source hash, English reference ID, full sixteen-byte hash,
  and review explanation. All four native rotation fields must agree. This
  covers unambiguous object and series names in the first 300 groups; ambiguous
  artwork/species/figurine identities and dropped unused prefixes remain
  unapproved. The review does not establish artwork identity or reachability.
- Added `tools/item_matches.py` and shared the approval map across ordinary
  candidate generation and wider resources. ROM and resource builders also
  independently verify the complete approved value, actual target source,
  all rotations, provenance, and any native placed-object conversion. Removing
  metadata, shortening/re-hashing English, using a different reference, or
  changing the donor/conversion cannot bypass these checks. Unapproved legacy
  matches and all existing English candidates remain unchanged.
- All 179 names fit sixteen bytes, adding 716 slots. Fifty-three fit ten bytes,
  adding 212 slots without changing native capacities. The other 126 new names
  remain complete in the wider resource and withheld from native ten-byte fields.
  Full/basic generation reaches 12,153/11,443 ordinary edits, respectively.
  Ordinary item names occupy 443 slots from 160 distinct reference IDs, including
  376 furniture slots. The wide resource contains 1,365 slots from 461 reference
  IDs, including 1,204 furniture slots. All previous full/basic/wide candidates
  remain identical; only these explicitly approved furniture slots are added.
- `build/tests-item-identities-full-01.log` passes all 653 tests in 270.698
  seconds. The nine initial identity checks cover schema, complete source and
  reference values, strict metadata types, capacity, aliases, all retail approval
  hashes/rotations, excluded names, and independent builder/resource rejection.
  Added two test-scenario composition checks after that full suite began;
  `build/tests-item-identities-focused-02.log` passes all eleven final focused
  tests in 1.155 seconds. Do not describe this as a 655-test full-suite run.
- The combined scenario generator joins native ten-byte and wide sixteen-byte
  bodies inside one identical setup/restoration, retaining all name and guard
  checks. Its first invocation stopped before starting an emulator because the
  default compiler module report lacks the ROM's NPC creator configuration.
  The configured `build/item-identities-pilot/runtime-module.json` supplies the
  correct independent approval; no guard or production code was changed.
  The failed invocation remains in `build/item-identities-scenario.log`; the
  corrected invocation is `build/item-identities-scenario-02.log`.
- ROM `build/item-identities-pilot/animal-forest-halfwidth.z64` SHA-256:
  `5b33a20b617d022e31c575d311d7742c3bae0518e9371ea7f1d7251a93e79a67`.
  UPS SHA-256:
  `98d867d049d40c2940a42720e82f964f1403d17951f2842bcdd9f30d5d115368`.
  Candidate SHA-256:
  `0f77a61c23280fc719e19ae03b26b919fc6351b51f5cc29159e534b9403011a5`.
  Wide resource SHA-256:
  `b12e5a7463840ab65a513bc2232c07d375cb8d4fe955dedea04a0a6d57786b91`.
  All actual installed edits match, and UPS application reconstructs the entire
  ROM. The cartridge wide resource equals both `names.bin` and independently
  reconstructed complete entries. The resource stays 72,736 bytes, with its
  original header, 4,544 entries, and sixteen-byte stride.
- The read-only artifact audit initially expected a DMA-directory change along
  with the two name files; actual comparison proved that only `010F4000` and
  `02A00000` differ from the travel pilot. The corrected exact-two-file assertion
  passes. The DMA directory, code, main text, choice/name/mail resources other
  than these item files, fonts, module, and saves remain unchanged. The ROM stays
  32 MiB. Source-volume replacement coverage increases by 1,196 characters to
  633,556 of the unchanged 746,978-character denominator; separately loaded names
  receive no additional coverage credit.
- Final-candidate identity and expression queues remain unchanged in scope:
  no currently admissible same-ID references and ten unapproved special-actor
  expression cases. Main candidates stay at 10,696, with 134 Japanese-static
  gaps, 919 non-static gaps, one Latin gap, and two symbol/numeric gaps. All 460
  choices remain unchanged. These counts do not imply completed wording review,
  normal item display, every wider destination, saving, or hardware validation.
- The first combined emulator run, `build/smoke-item-identities-01/`, stopped at
  its 370-second process limit with a debugger connection reset. It records
  606 calls and 596 passing memory assertions but no checkpoint restoration;
  it is incomplete, not a successful batch or an established game crash.
  No failed text assertion precedes the stop. The same complete scenario was
  run once with a 600-second allowance in `build/smoke-item-identities-02/`.
  That process exits successfully: 757 calls, 749 memory assertions, 545 expected
  return values, and 2,271 recorded steps. All 461 wide reference representatives,
  every new ten-byte rotation slot, boundary/capacity/header cases, unaligned
  destinations, guards, full checkpoint restoration, and graceful shutdown pass.
  The run uses no seeds, no audio, four MiB, and neither save-write permission.
  FlashRAM remains `b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260`;
  Pak remains `ab2a6e04fd3ceb36594f1216c888a1b8bd0a3ba0a94f715a7c7601e98c49ec51`.
  Scenario SHA-256:
  `a37e4160ef4ffdf301209a7343d4d46ad6ee1f3f729ad7d68acf1ff25eec43c0`.
  Each recorded address/argument, expected return, memory assertion, and restored
  stack was independently compared with the complete scenario after termination.

## 2026-09-08 — Native startup errors and final combined checkpoint

- While the item-name batch ran, translated cartridge-clock failure `09CC` and
  corrupted-town notice `09D1` in `translations/n64-startup-errors.json` and
  integrated both into default full/basic generation. The GameCube texts refer
  to its console clock or Memory Card insertion/erasure choices; those are not
  the native instructions. The drafts preserve the native hardware meaning,
  every command and argument, pauses, pages, choices, branches, and terminators,
  except the exact Instruction Booklet colour length `0C → 13`.
- The clock warning keeps `00E7/00E8` and `09CD/09CF`, including the choice to
  wait and try later. The town-data notice retains `09:09:0001` and normal `00`,
  not the legacy's `09D7` continuation or a GameCube erasure menu. No recovery,
  clock, save, font, actor, or buffer code changes. Complete stored/expanded
  lengths are 345/361 and 162/178 bytes, with no layout warnings.
- All five focused checks pass in 0.271 seconds in
  `build/tests-startup-errors-focused-01.log`. The final combined full-suite run,
  `build/tests-startup-errors-full-01.log`, passes all 660 tests in 256.628
  seconds, including the final eleven item tests and five new startup tests.
- Full/basic generation adds only these two records and leaves every prior
  candidate unchanged: 12,155/11,445 ordinary edits. The main bank contains
  10,698 candidates: 9,736 references, 572 original dialogue drafts, one original
  continuation, 290 development labels, and 99 diagnostic labels. Main reference
  rejection totals 1,055: 929 unconfirmed identities, 100 control differences,
  24 missing-field records, and two direct overflows. One original fallback
  leaves 1,054 final gaps: 132 Japanese-static, 919 non-static, one Latin, and two
  symbol/numeric. Ten non-static records contain insertions; no reachability is
  inferred. Warning-bearing records stay 1,470; aliases stay 41 with no conflicts.
  Identity review has zero current-rule admissions and the expression queue has
  ten unapproved cases. Final reports use `build/startup-errors-*` paths.
- ROM `build/startup-errors-pilot/animal-forest-halfwidth.z64` SHA-256:
  `f1d0985dd4911cf01b452e8742967b9a1fbf938a1816db0225aec760e03b159f`.
  UPS SHA-256:
  `e097539c4228f5495e07455a4a4cd7f3476cba77dcd86592a961bf5bfe102f1c`.
  Candidate SHA-256:
  `3866c07d4e6267aab431ea40296b0cac752dceee2e647a72d7c6df6746e28d17`.
  All 12,155 installed edits, source/candidate/build hashes, and whole-ROM UPS
  reconstruction pass. Only `02000000`, `00CF9000`, and the DMA directory container
  differ from the item-name pilot; the container is unchanged outside its table.
  An initial read-only check used the wrong list order for that exact set;
  the corrected unordered comparison passes. Every name resource, code, font,
  other table, and saved structure remains unchanged. Source-volume coverage
  gains 221 characters to 633,777 of the unchanged 746,978-character denominator.
  The user's subsequent one-time measurement used this verified final ROM.
- `build/smoke-startup-errors-01/` passes all five complete cartridge loads for
  `09CC/09D1/09CD/09CE/09CF`: seventeen memory assertions and 34 recorded steps,
  complete headers/text, both adjacent guards, the module guard, restored
  `test.bs1`, and graceful shutdown. All five expected return values pass.
  Scenario SHA-256:
  `64a642d44b9bf1142e28105c50daa79181e9b082fc0f7e72c9e53197ce2c54f6`.
  The four-MiB process is silent, has no seeds, and has both save-write permissions
  disabled. Blank FlashRAM/Pak hashes match the item-name batch. This loads text
  only; ordinary error selection, live date input, clock recovery, saving, final
  wording, and hardware still require their own acceptance evidence.
- The previous goal work is progress: implemented and built two startup errors,
  completed item-name validation, and verified the final installed artifacts.
  The user's follow-up makes the title screen the image-pass priority. Recorded
  that priority without removing other Japanese text-bearing images or moving
  stretch work ahead of the main port. All broader completion-queue requirements
  remain active, and font-atlas-edge investigation remains paused.

## 2026-09-08 — Complete references with original resident mood effects

- Added nineteen individually reviewed `complete_reference.native_mood`
  approvals and `tools/reference_mood.py`. Each restores the complete original
  `09:02:0001` mood plus `09:08:0001/0002` duration pair at its corresponding
  English page, retaining all supplied words, newlines, pages, pauses, and fields.
  `1FAD` needs the fourth English page clear, not the third native page clear;
  its final victory claim supplies the semantic match. `263C` retains duration
  two. Only `2067` removes two already-supported redundant article controls.
- Verified native mood reader `80976588..80976604` and setter
  `80978800..80978874` against the actual cartridge overlay. These commands
  change resident mood and its duration, not merely facial expression. The
  reader consumes only NPC0 row-four slots two/eight; the setter uses animal
  `51E` and actor `804`, with duration scaling and the existing cap. Generation
  and installation require the unchanged pinned overlay, relocations, core
  getter/setter, parser, and dispatch. No production actor or saved-layout changes.
- The rule checks exact pairs/offsets, native/reference page starts, absence of
  duplicate mood orders, complete actor order before normal adaptation, and
  native/reference/final hashes. Wrong-page insertion cannot be hidden by the
  ordinary demo-argument adapter. Mid-page cases and changed-topic `2773` remain
  withheld; no new field, expression, gameplay, or random-branch permission.
  Contract and consumer evidence are in `specs/NATIVE_MOOD_REFERENCES.md`.
- Eleven focused checks pass in `build/tests-native-mood-focused-04.log`
  (2.131 seconds). The new positive builder test initially omitted the original
  code replacement required by the existing relocation API, causing a fixture
  `KeyError`; the corrected fixture supplies that code. The initial full suite
  recorded that one fixture error. The final full run,
  `build/tests-native-mood-full-02.log`, passes all 671 tests in 222.352 seconds.
  No production workaround is introduced for the fixture error.
- Full/basic generation adds exactly the nineteen approvals, preserves every
  earlier candidate, and produces 12,174/11,464 ordinary edits. Main candidates
  total 10,717, including 9,755 references. Original draft counts remain unchanged.
  Main rejections are 1,036: 929 unconfirmed, 81 control differences, 24 field
  differences, and two direct overflows. One original fallback leaves 1,035
  final gaps: 113 Japanese-static, 919 non-static, one Latin, and two symbols.
  Ten non-static records have fields; no reachability is inferred. Warning
  records total 1,471, with no automatic reflow. Aliases remain 41, conflicts zero.
  Fresh identity/expression queues have zero current-rule admissions and ten
  unapproved special contexts. Reports are under `build/native-mood-*`.
- ROM `build/native-mood-pilot/animal-forest-halfwidth.z64` SHA-256:
  `c5b1f9414fa1a0c727b08b327b4a6226d33a550730d9891cf97e8ce120ea752d`.
  UPS SHA-256:
  `220094fbbc29ff571efd7ed4a506d744948d8e8d2414ff41347662e33ea6fe00`.
  Candidate SHA-256:
  `62053eaa67bb0bc1d3dbcbacdc7592483c3174c88b5ffd2674182b4481c78645`.
  All 12,174 installed payloads, source/build hashes, and whole-ROM UPS
  reconstruction pass. Only `02000000`, `00CF9000`, and DMA container `00019D40`
  change relative to the startup-error pilot. The container remains unchanged
  outside the DMA table. An initial read-only audit assumed the wrong container
  ID; the exact actual-file audit passes in `native-mood-artifact-audit-02.log`.
  Fonts, code, choices, item/name/mail resources, and saved structures remain
  unchanged. Covered source volume gains 1,136 characters to 634,913 of the
  unchanged 746,978-character denominator; this is not project completion.
- Extended the existing native actor-request scenario with `--native-mood`.
  The original twenty-five-request scenario is independently compared with the
  committed implementation and remains identical. The new batch loads every
  complete approved message, dispatches both original mood orders, and checks
  cumulative row-four changes, all other rows, cursors, and adjacent/module
  guards. `build/smoke-native-mood-01/` passes 57 calls, 57 expected returns,
  140 memory assertions, and 283 recorded steps, with one restored checkpoint
  and graceful shutdown. Each call/argument/return and every complete read is
  independently compared with the scenario in `native-mood-native-audit.log`.
  Scenario SHA-256:
  `510d4ea19b85c8336f79c01f3d9e6831225f61849a85aab3eeee9d506287ff95`.
  The isolated four-MiB run has no seeds, audio, or save-write permissions.
  FlashRAM remains `b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260`;
  Pak remains `ab2a6e04fd3ceb36594f1216c888a1b8bd0a3ba0a94f715a7c7601e98c49ec51`.
  This establishes cartridge loading and order dispatch, not normal resident
  mood/timer progression, rendered conversations, saving, or hardware acceptance.

## 2026-09-08 — Shifted item-name identities and carried spelling variants

- Reviewed and added 308 furniture-name approvals outside the first 300 groups:
  138 individually matched shared indices and 170 explicit cross-index matches.
  English table insertions shift selected insect/fish/umbrella/later-furniture
  groups by 8/16/24/44 entries. Those differences are recorded per approval,
  not installed as a blanket index rule. Complete native names, source hashes,
  all four rotations, supplied English names/hashes, and families are checked.
  Japanese queen/king, tail/torso, and right/left-wing words select correct
  English parts where the legacy wording swaps them. Unreviewed gyroids,
  changed species/designs, native game slots, and filler remain withheld.
- The initial 308-name resource adds 1,232 furniture slots and 114 exact-source
  ordinary aliases; 324 furniture slots and eleven aliases fit ten bytes.
  All previous candidates remain unchanged. Full/basic generation contains
  12,509/11,799 ordinary edits; the initial wide resource has 2,711 slots and
  769 reference IDs. The first eleven focused checks pass, followed by fourteen
  checks including shifted blocks, withheld cases, and actual placed conversion.
  The initial full suite passes all 674 tests in 224.795 seconds.
- The independent converted-name audit catches two genuine display gaps:
  placed `ゆきぐにニット` versus carried `ゆきぐになニット`, and placed `くまのふく`
  versus carried `クマのふく`. The exact-source alias guard correctly leaves those
  carried fields native. Added independent ordinary approvals `item_24:006D/0078`
  for complete winter sweater and bear shirt references, with their actual
  native/English hashes. No general kana or particle normalisation is added.
  Both fit sixteen bytes; only bear shirt fits ten. The final audit proves that
  every selected wide name remains complete after actual native conversion.
- The final registry contains 489 approvals: 487 furniture and two ordinary.
  The batch adds 1,348 wide slots and 336 ordinary edits. Final full/basic
  generation contains 12,510/11,800 edits. Native item storage has 779 slots from
  242 reference IDs, including 700 furniture slots from 175 identities. The wide
  resource has 2,713 slots from 771 reference IDs, including 2,436 furniture
  slots from 609 identities. Counts distinguish references, rotations, aliases,
  and storage capacities; longer names are never abbreviated.
- The final fifteen focused checks pass in 1.112 seconds in
  `build/tests-mapped-items-focused-03.log`. The complete final suite passes
  all 675 tests in 226.977 seconds in `build/tests-mapped-items-full-02.log`.
  All main dialogue and choices remain unchanged: 10,717 main candidates,
  113 Japanese-static gaps, and the same rejection/warning/alias counts as the
  mood checkpoint. Fresh final identity/expression queues retain zero
  current-rule admissions and ten unapproved special contexts. Source-volume
  coverage gains 1,865 characters to 636,778 of the same 746,978 denominator.
- Final ROM `build/mapped-items-final-pilot/animal-forest-halfwidth.z64` SHA-256:
  `041abc6ba98c662c48078848b5d882e3e201b681009992887ae1f95f7bb37871`.
  UPS SHA-256:
  `26c8bf9927ff56a12960802078a6e2e585d8f34e26d610a582d329290e8cb0ef`.
  Candidate SHA-256:
  `a8663840811a20f3549f365130984e0ab9de834844789018ffe6206e0551e048`.
  Wide-resource SHA-256:
  `12325054543aa6a610fe4525f915a8ea563e40cd2d5cb2d570edafed6db208b5`.
  `build/mapped-items-final-artifact-audit.log` verifies all 12,510 installed
  payloads, whole-ROM UPS application, full resource reconstruction, and all
  2,713 converted full-name expectations. Only `010F4000` and `02A00000` differ
  from the mood pilot; every DMA entry, code/font/message/name/mail resource
  outside those two files, and saved structure remains unchanged.
- An initial combined 1,185-call fixture was generated. The runner rejects
  a requested 900-second allowance before launching because its existing limit
  is 600 seconds. Kept that safety limit and split the checks into separate
  wider and original-width batches. No game failure is implied by this preflight
  rejection. `build/smoke-mapped-items-wide-01/` passes 850 calls/expected returns,
  842 memory assertions, and 2,550 steps. `build/smoke-mapped-items-native-01/`
  passes all 335 new original-width loads, 337 memory assertions, and 1,014 steps.
  The native void-return path is checked by complete output/guards, not an
  invented expected return. Both processes restore their checkpoints and shut
  down gracefully.
- The final clothing refinement changes only the carried bear-shirt ten-byte
  field and two sixteen-byte fields. All other bytes tested by the two larger
  runs remain unchanged. `build/smoke-mapped-items-spelling-01/` checks the final
  ROM through four full-width carried/placed loads and ten native-width loads,
  covering both carried items and all four placed rotations: fourteen calls,
  four expected-return checks, sixteen memory assertions, and 51 steps. Exact
  complete English wide names, the deliberately unexpanded winter ten-byte
  fallback, guards, restored state, and graceful shutdown pass. No additional
  full-size emulator rerun is needed for these three explicitly checked fields.
- `build/mapped-items-native-results-audit.log` independently compares every
  call/address/argument, applicable return, complete read, restored stack, and
  checkpoint with all three scenarios. Scenario SHA-256 values:
  wide `a65fb2e92ee6518ce41904396fce89c870d3c4affaf3eb56b9ed70564034c1b6`;
  native `5ee3f6a91f4e61d61fa5a1db538ed407769acc7bc8b31eff7498675b5856a8fe`;
  spelling `92dc9bd801b7106d0953da912de5ec80fd9ee703625b969ada3905e1b59cbd2a`.
  All three runs are silent, four MiB, have no seeds, and disable both save-write
  permissions. FlashRAM remains
  `b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260`;
  Pak remains `ab2a6e04fd3ceb36594f1216c888a1b8bd0a3ba0a94f715a7c7601e98c49ec51`.
  Normal inventory/catalogue/catch/gift display, every wider destination, final
  wording/design identity, saving, and hardware remain separate acceptance work.

## 2026-09-08 — Title-screen source route

- While item checks ran, located the supplied English title's three animated
  letter groups, four background pieces, trademark, and two separate Press
  Start tiles in the local decompilation/model/symbol inventory. Verified the
  complete supplied REL hash and the 60,600-byte title-related data region.
  Also verified the native logo overlay and relocation files. Scoped local
  palette/letter names repeat, so a first-symbol-name lookup is insufficient.
  `specs/TITLE_ASSETS.md` records exact source/destination locations, hashes,
  source-described formats, and remaining implementation/acceptance checks.
- This is source discovery, not a title replacement, asset conversion, or
  native drawing verification. No image or font changes. The main logo is
  animated textured geometry, not the separate Press Start image. Preserve
  native title/menu, clock, save-data, and player-selection transitions during
  the later drawing integration. Title artwork remains first in the image pass;
  broader main-port work and all other completion requirements remain active.

## 2026-09-08 — Complete English mood effects at phrase boundaries

- Added complete reference approvals `203A/262B/2637/264B/266B`. Their original
  mood/timer pairs occur after quest preparation, at a mid-page phrase, or
  immediately before the final newline/end. Each semantic position is reviewed
  against the complete native and English text. Four rules require the exact
  following original `09:00:000E` expression; `266B` requires only the original
  final newline and normal `00` ending after the pair. Source/reference/final
  hashes and complete actor order remain mandatory. Unanchored page rules stay
  strict, and no English word, line, page, pause, field, or command is changed.
- Two added unit tests cover phrase and final-ending anchors, incorrect positions,
  changed/missing expressions, extra text, and alternate terminators. The first
  thirteen-test run preceded saving the five registry entries and correctly
  failed their presence assertion; all other checks passed. After the complete
  approvals are installed, `build/tests-mood-phrases-reference-01.log` passes all
  96 reference-group tests in 17.323 seconds, including thirteen mood tests and
  independent builder/source-consumer checks. Seven text-coverage tests pass
  in 0.002 seconds. No production runtime/C code changes, so the unchanged
  components retain the 675-test full-suite checkpoint rather than another
  full C regression for this import-only batch.
- Both generation modes add exactly the five messages and preserve every prior
  edit: 12,515 full and 11,805 basic. Main candidates total 10,722, including
  9,760 references. Rejections total 1,031: 929 unconfirmed, 76 control,
  24 fields, and two direct overflows. One fallback leaves 1,030 final gaps:
  108 Japanese-static, 919 non-static, one Latin, and two symbol/numeric. Ten
  non-static records have insertions; no reachability is inferred. Warning
  records total 1,472, aliases remain 41, and conflicts remain zero. Fresh
  identity/expression queues retain zero current-rule admissions and ten
  unapproved special contexts. Source volume gains 277 characters to 637,055
  of the unchanged 746,978-character denominator.
- ROM `build/mood-phrases-pilot/animal-forest-halfwidth.z64` SHA-256:
  `25301e4aec42c8aa7edb1e43c4fc406b4b25db77c94e614530b443ea79872c92`.
  UPS SHA-256:
  `152ee654d30f1cbd76fee179b62e5bd3881360cc2d66955be9fe42f9bf8d87a9`.
  Candidate SHA-256:
  `fe660331b69cae1374d4927079014db4cf52f58e39a82efaf114eeb0510b11d0`.
  `build/mood-phrases-artifact-audit.log` verifies all 12,515 installed edits,
  source/build hashes, and complete UPS reconstruction. Only main text,
  its pointer table, and the DMA directory container differ from the final
  mapped-item pilot. The container is unchanged outside its table. Every item,
  name, mail, font, runtime, and saved structure remains unchanged.
- `build/smoke-mood-phrases-01/` passes the complete combined twenty-four-message
  batch: 24 cartridge loads, 48 native mood/timer dispatches, 72 expected-return
  checks, 175 memory assertions, and 353 steps. Complete text, exact cumulative
  order tables, cursor advances, adjacent/module guards, stack restoration,
  checkpoint restoration, and graceful shutdown pass. The independent audit
  compares every call/argument/return and complete memory read with the scenario.
  Scenario SHA-256:
  `6ee50d80148ad552297362e69aace0fbc2453eaa823b759c7f969cf970d22788`.
  The isolated run is silent, four MiB, has no seeds, and disables both save-write
  permissions. FlashRAM and Pak retain the same blank hashes as the mapped-item
  runs. This checks native loading and order dispatch, not ordinary mood/timer
  progression, rendered conversations, saving, or original hardware. Those and
  changed-topic `2773` remain in the completion queue.

Generated assets, logs, screenshots, ROMs, patches, and reference text remain
local under ignored `build/` and `local/` paths. Current status belongs in
`PROGRESS.md`; this file records completed work and test observations.

## 2026-09-08 — Complete renovation invoice and original room choices

- Added `nook_first_renovation_invoice`, preserving all supplied English `107E`
  with only the native 49,800-Bell amount in place of 148,000. The complete
  corrected record is 1,023 stored/1,039 expanded bytes. Its existing page
  transition immediately after the bill becomes `107E → 083F`; resulting
  expanded bounds are 574 and 483 bytes. Dry-rot, mammal-strike, payment,
  debt-character, and farewell wording, manual lines, and pauses remain intact.
- Added the narrow `native_price` sequence approval. It checks a complete numeric
  reference span, the full corrected reference hash, exact native numeric text,
  unchanged commands/newlines, complete slice coverage, and final payload hashes.
  It cannot combine with native-original or article-removal adaptations. The
  independent builder checks the native price as well as all source/output hashes.
  Native `083F` has no incoming script branch or matching executable immediate.
  Its sole non-executable aligned halfword match is inside libultra's sine table
  at `8003C644`, not a dialogue pointer.
- Added complete original `107F/1081` drafts for repayment, the expensive further
  enlargement, refusal, and roof-colour choice. The GameCube basement action is
  not native. Every source command and argument remains exact, including `5E`,
  both agreement branches, all four roof branches, and continuing termination.
  Expanded bounds are 421 and 322 bytes; both layouts pass without warnings.
- Eight focused tests pass in 2.214 seconds
  (`build/tests-nook-renovation-prices-03.log`). All 96 reference checks pass in
  19.018 seconds, eleven placeholder checks in 13.907 seconds, and seven coverage
  checks in 0.002 seconds. Early attempts exposed only a test error-message case
  expectation and stale aggregate sequence counts; those fixtures were corrected,
  and their full groups passed. Runtime/C code is unchanged and retains its
  675-test full-suite checkpoint; no new full-suite run is claimed.
- Full/basic candidates now contain 12,518/11,808 ordinary edits. Three previously
  missing records gain text; `083F` changes from its reserve label to the complete
  invoice continuation. All other candidates remain unchanged. Main coverage is
  10,725 records: 9,762 references, 574 original dialogue drafts, one original
  continuation, 289 development labels, and 99 diagnostics. All 460 choices
  remain. The remaining main set is 1,027: 105 Japanese-static records, 919
  nonstatic records, one Latin record, and two symbol records. Ten nonstatic
  records have dynamic insertions; none is labelled unreachable. The reference
  queue has 926 unconfirmed identities, 76 control differences, 24 missing-field
  records, and two direct overflows, with one original fallback. Fresh identity
  review admits no additional records under existing rules; the ten special
  expression contexts stay unapproved. Layout warnings remain 1,472. Covered
  source weight is 637,486/746,978 characters, not an overall completion claim.
- `build/nook-renovation-pilot/` ROM SHA-256:
  `80cff2f8cff769b9aae7d1f65184092196b838f272c7011625cbeebe4dc05f4b`.
  UPS SHA-256:
  `05da1b249d952a5ed2b977643f83489c3c8417311ff5cd6de12eb1b1a405d5fc`.
  Candidate SHA-256:
  `d45f11c5f8ec3ecf1790840a55a7a8964f5da5a5fc7195ea275a3daec7106aea`.
  `build/nook-renovation-artifact-audit.log` checks every installed payload,
  source/build hashes, the complete UPS reconstruction, and candidate differences.
  Only `02000000`, `00CF9000`, and the DMA-directory container `00019D40`
  differ from the mood-phrase pilot; the container is unchanged outside its
  table. Runtime, font, all item/name/mail resources, and saved layouts remain.
- `build/smoke-nook-renovation-01/` passes all four actual cartridge loads,
  invoice continuation and both termination phases, both agreement outcomes,
  and all four roof-branch selections. The complete run has 33 calls with exact
  expected returns, 51 memory assertions, and 142 steps. The independent audit
  verifies every call/argument/return, restored stack, and complete expected read.
  Guards, checkpoint restoration, and graceful shutdown pass. The run is silent,
  four MiB, has no seeds, and disables both save-write flags; cartridge/Pak hashes
  remain blank. Scenario SHA-256:
  `176e7ffb74444cdb23682120094043945f9dac70f01be0d1b0fa12b26762497c`.
  This is injected native-handler validation, not ordinary repayment, roof-menu
  input, rendered progression, saving, or original-hardware proof.
- Updated the current progress, queue, and sequence/renovation specifications.
  Title artwork remains the first image priority after the main port; its source
  route is recorded, but no replacement is installed. Broader dialogue, remaining
  destinations, gameplay/save validation, image/keyboard work, final review, and
  patch-only release acceptance remain required.

## 2026-09-08 — Complete native topics, connected replies, and combined validation

- Added ten original drafts in `translations/n64-topic-gaps.json`: `0B69`,
  `11FC`, `1D47`, `2006`, `2018`, `204B`, `246C`, `25E6`, `25EB`, and `25FD`.
  Nine fill missing messages; `25FD` replaces an existing incompatible reference
  reply. The native sign claim, train-dependent moving, seasonal romance, net
  technique, shovel-hole warning, positive item-attachment question, ocean
  row-six quiz, and complete meal-greeting jokes retain original actions and
  answer order. The native map/sign artwork and seasonal selector are not
  claimed inspected or translated; no explicit September or F-row label is
  invented. Expanded bounds in file order are
  `117 340 153 209 361 267 106 211 228 235` bytes.
- Kept the complete shouts Let's eat! and Thanks for the meal!, with ten and
  twenty English characters respectively, original RGB `E1 1E D7`, and native
  `54 2D` scale before every character, including spaces and punctuation. Only
  exact colour counts and per-character scale repetitions change. Every other
  native command remains exact. Both full scaled phrases fit the approved glyph
  widths. The initial test caught a nineteen-versus-twenty character colour count;
  that draft was corrected before the successful build. Eight drafts have no
  warning; the two shouts retain explicit-formatting review warnings.
- Added two explicit `native_original` contextual-choice approvals. `0B69`
  displays `0025/0026`; `246C` displays `0025/0051`. Native answer indices and
  success/failure destinations remain. Canonical original payloads must retain
  every source command and argument; original approvals cannot collide with
  reference parents. Source/canonical/display hashes, unique menu offsets, exact
  menu bytes, and complete label dependencies remain bound in both generator and
  builder. Shared Circle/X labels are unchanged. The registry contains twenty-one
  mappings: nineteen references and two originals. Basic generation retains three
  mappings and withholds eighteen whose complete labels are unavailable.
- Corrected candidate-report accounting for original contextual drafts. Their
  existing original-draft count remains; reference counters change only for
  existing reference manifests. Withholding an original removes its draft count,
  not unrelated reference credit. Original edits without an explicit policy use
  the established `exact` default. Initial generation attempts exposed the
  missing-policy assumption and original-report path before a ROM was built;
  dedicated tests cover both successful and withheld original accounting.
- Added complete GC `2773` after reviewing native `207A` and all three connected
  replies. Already installed GC `207A/2771/2772` consistently use the girls and
  fluffy-snow joke, so mixing in an original snow-makeup ending would break the
  English conversation. `2773` retains every English word, line, page, pause,
  field, actor order, and ending. The native mood-one/duration-one pair is restored
  at the final page's matching `0A`, binding native offset 64 and reference offset
  192. Its expanded bound is 281 bytes. The registry now has twenty-five mood
  approvals: twenty page anchors and five phrase anchors. No new runtime policy
  or blanket changed-topic approval is introduced.
- Added `tools/topic_gap_test_scenario.py` to combine the contextual-answer,
  complete-message, and mood fixtures into one checkpoint. All body assertions
  and guards remain. Composition requires matching setup/restore structure and
  rejects differing restore bytes, including partially overlapping windows and
  declared-length mismatches. Only one final restore runs. Nine topic tests pass
  in 0.567 seconds (`build/tests-topic-gaps-native-05.log`); twelve contextual
  tests pass in 0.941 seconds (`build/tests-topic-gaps-context-02.log`); 96 reference
  tests, including thirteen mood checks, pass in 18.291 seconds
  (`build/tests-topic-gaps-reference-01.log`); seven native-menu checks pass in
  1.986 seconds and seven coverage checks in 0.003 seconds. These are 131 focused
  tests, not a new full-suite claim. Runtime/C code retains the 675-test checkpoint
  in `build/tests-mapped-items-full-02.log`.
- Successful full/basic candidates are in `build/topic-gaps-ready-candidates/`
  and `build/topic-gaps-ready-basic-candidates/`, with 12,528/11,816 ordinary
  edits. Only ten absent main IDs are added; only existing `25FD` changes.
  Main coverage is 10,735: 9,762 references, 584 original dialogue drafts, one
  original continuation, 289 development labels, and 99 diagnostics. All 460
  choices remain unchanged. The 1,017 gaps comprise 95 Japanese-static records,
  919 nonstatic records, one Latin record, and two symbol records. Ten nonstatic
  records have dynamic insertions; none is deemed unreachable. Main rejections
  total 1,018: 926 unconfirmed, 66 control differences, 24 missing fields, and
  two overflows; one receives an original fallback. Fresh identity review admits
  zero records under existing rules; ten special expression contexts remain
  unapproved. Reference/label-manifest warnings remain 1,472, separately from
  the two original shout warnings. Covered source weight is 638,075/746,978,
  not a semantic-review, gameplay, or project-completion claim.
- `build/topic-gaps-pilot/animal-forest-halfwidth.z64` SHA-256:
  `b7d5ecb7b4a78f71df8ddd0f18108763d780409a9adb7473e82825423b612179`.
  UPS SHA-256:
  `757fa3c145b97bd11a14e0ea40a513da8e9e85b1f91c72d9a1e5d0a5c63bbfbf`.
  Candidate SHA-256:
  `fbb0989fa59604098382cb8d5236b3ed374cd334806979cc5b6f41a332c641d1`.
  `build/topic-gaps-artifact-audit.log` checks all 12,528 actual ROM payloads,
  source/build/candidate/patch hashes, original-context accounting, and complete
  UPS reconstruction. Relative to the renovation pilot, only `00019D40`,
  `00CF9000`, and `02000000` differ. The DMA container is unchanged outside its
  table. All runtime/font/name/item/mail resources and saved layouts remain.
- `build/smoke-topic-gaps-01/` passes 1,754 recorded steps: 423 native calls,
  309 explicit return assertions, and 763 memory assertions. Coverage includes
  107 actual cartridge message loads, all 46 selected-label/insertion cases,
  all 42 contextual branch cases, and all 25 mood messages/50 order dispatches.
  Shape selection is checked without executing or claiming its random outcomes.
  `build/topic-gaps-native-audit.log` independently verifies every call/address/
  argument, each declared expected return, restored stacks, and complete memory
  reads. Regenerating the strengthened fixture reproduces the executed scenario.
  Scenario SHA-256:
  `d3eed654b998c2a27e09f4e5a21083f94f4a8b281c6d201eca04f67912be59ed`.
  Guards, the single checkpoint restore, and graceful shutdown pass. The isolated
  run is silent, four MiB, has no seeds, and disables both save-write flags.
  FlashRAM SHA-256 remains
  `b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260`;
  Pak SHA-256 remains
  `ab2a6e04fd3ceb36594f1216c888a1b8bd0a3ba0a94f715a7c7601e98c49ec51`.
- Recorded the full contracts and current queue. Remaining native-menu cases are
  `088B/2586` birthday fields and `246D` old-calendar preparation, with separate
  `1C6F` letter-reaction/label work. Native disassembly locates the calendar-order body at
  `80920F20`: request value one converts current RTC month/day using `800D6218`
  through `8091EBB8` into free fields 15/16, distinct from the earlier reminder
  callers. This is a next-step source finding, not a new runtime approval or test.
  Ordinary topic/answer actions, rewards, shout rendering, calendar selection,
  saves, final wording, artwork, hardware, and patch-only release remain. The
  title screen is the first image priority; no title replacement is installed.

## 2026-09-08 — Complete old-calendar quiz and required English date preparation

- Audited actual native quiz `246D`, its `0C 07 0001` request, the complete
  ordinary overlay, dispatcher `809215E4`, and table `80921D88`. Entry seven
  selects `80920F20`. Manager type/value are 16-bit fields `1AC/1AE`. Value one
  converts the two moon-viewing dates into free fields 11/12 and 13/14, then
  current RTC month/day into 15/16 through `800D6218` and `8091EBB8`. The current
  day/month/year addresses are `80136FBF/80136FC1/80136FC2`; `3B/3C` insert free
  fields 15/16. This is distinct from the earlier reminder caller's fields and
  from birthday item slots. Exact instruction/body/table hashes and source words
  are recorded in the date spec and tests.
- Added complete English reference `246D`, canonical native-menu approval, and
  contextual `0025/0051` answers. All native requests and answer branches remain:
  affirmative reaches `2472`, negative reaches `2476`. The displayed payload
  equals the complete supplied GameCube reference, including every word, manual
  newline, page, pause, field, and ending. It is 81 stored/157 conservatively
  expanded bytes. The generic free-field warning remains; a separate 403-case
  complete-layout audit covers every month, leap month, and ordinal day. Every
  complete layout fits; the widest actual date line is 88 pixels, leap month 10th.
  No text is shortened and no font, runtime code, or saved structure changes.
- Added reviewed-reference support for the existing `ordinary_dialogue_dates`
  requirement. The generator withholds the reference when the complete English
  date patch is unavailable and carries its requirement when enabled. The builder
  consults the identity approval independently of candidate metadata; omitting
  the list or supplying an empty list cannot remove the dependency. Both complete
  overlay/relocation files and the resident module/literal remain mandatory.
  Unknown, duplicate, malformed, empty explicit reference requirements, and
  non-message reference requirements fail. Original-draft behaviour remains.
- Expanded the owned-heap native fixture to execute the actual quiz request and
  relocated demo dispatcher. It checks the complete quest request table, manager,
  twenty free fields, current clock, message, and actual `3B/3C` insertions. Six
  current dates cover 2000-02-05, 2001-05-23's native leap-month start,
  2004-02-29, 2026-09-08, 2030-08-15, and 2032-12-31. Independent native
  conversions supply expected values; values zero and two leave all fields
  unchanged. The fixture restores the actor-order pointer and complete RTC block,
  retains saved game and code, guards its allocation and stack, and frees the
  allocation before one checkpoint restore. It does not simulate ordinary quest
  polling or claim quiz rewards.
- Added `calendar_quiz_test_scenario.py` to combine all date and contextual-answer
  checks in one checkpoint. Thirteen focused date/dependency tests pass in
  0.645 seconds (`build/tests-calendar-quiz-dates-01.log`), all 96 reference tests
  pass in 17.768 seconds, and the complete 700-test suite passes in 226.242 seconds
  (`build/tests-calendar-quiz-full-01.log`). The full suite includes current native
  topics, contextual choices, date dependencies, and unchanged portable/runtime C.
- `build/calendar-quiz-candidates/` adds exactly one ordinary edit to 12,529;
  every earlier candidate remains unchanged. Basic output remains exactly the
  same 11,816 edits and records the quiz's missing-date requirement. Full main
  coverage is 10,736: 9,763 references, 584 original dialogue drafts, one original
  continuation, 289 development labels, and 99 diagnostics. All 460 choice texts
  remain. The 1,016 gaps comprise 94 Japanese-static, 919 nonstatic, one Latin,
  and two symbol records; ten nonstatic records have dynamic insertions and none
  is deemed unreachable. Main rejections are 926 unconfirmed, 65 control
  differences, 24 missing-field records, and two overflows, with one original
  fallback. Reference/label warnings total 1,473, plus the two separately recorded
  original shout warnings. Source weight is 638,100/746,978 characters. The full
  native-menu registry contains 165 approvals; contextual mappings total 22,
  with twenty complete references and two originals. Basic generation retains
  three, withholding eighteen for complete labels and one for date preparation.
- `build/calendar-quiz-pilot/animal-forest-halfwidth.z64` SHA-256:
  `ed738e2e59c0f93b25faebcd568f79cef0acf07da74fe09c1311a3640a73a8c6`.
  UPS SHA-256:
  `6cad8e919472aa15bc8b7033bd9dc1326bd8f187e21e0119f257dc644546df23`.
  Candidate SHA-256:
  `cbf8b3aa7ba0e34653cc2e2dcae235ede423ce33864d4a4d61f02671acc12184`.
  `build/calendar-quiz-artifact-audit.log` verifies every installed payload,
  complete source/build/patch hashes, UPS reconstruction, exact prior-candidate
  and basic retention, and the full displayed reference. Only `00019D40`,
  `02000000`, and `00CF9000` differ from the topic pilot; the DMA container remains
  unchanged outside its table. All runtime/font/name/item/mail resources remain.
- `build/smoke-calendar-quiz-01/` passes 2,039 recorded steps: 496 calls,
  294 explicit expected-return checks, and 822 memory assertions. There are
  78 actual cartridge message loads. The date group covers 53 preparations,
  thirteen earlier conversions, eighteen direct quiz conversions, six actual
  quiz requests/dispatches, two no-op orders, twelve date-message loads, and
  twenty date insertions. The contextual group covers 43 messages, all 48 answer
  selections/insertions, and 44 actual contextual branches; shape random outcomes
  are not executed. The single checkpoint restore, complete clock/saved-game
  retention, allocation freeing, guards, restored stacks, and silent graceful
  shutdown pass. Four MiB, no seeds, both save-write flags disabled; FlashRAM/Pak
  retain the same blank hashes as the topic run.
- `build/calendar-quiz-native-audit-02.log` independently checks all explicit
  scenario call arguments, declared return values, complete memory assertions,
  saved hashes, and regenerated fixture identity. The first audit compared Python
  tuples with decoded JSON lists and failed only its final fixture comparison;
  normalising through JSON fixes that audit without changing the run or code.
  Scenario SHA-256:
  `6bde62a8b49c36b42f2fbafcfad83b9f9d9f98f8d35be1b6f2d98a713d3dc54d`.
  Layout evidence is `build/calendar-quiz-layout-audit.log`. No emulator rerun was
  needed. Normal conversations, request polling, calendar selection, actual
  rewards, out-of-table dates, rendering, saves, hardware, and final review remain.
- Updated the current progress, queue, date, menu, and dependency contracts.
  Birthday `088B/2586` and letter reaction `1C6F` remain among the next native
  content tasks. The title screen remains the first image priority after the main
  port, with no installed replacement. The complete project goal remains active.

## 2026-09-08 — Full birthday names/dates and connected English answers

- Continued from private checkpoint `101c95762156f1c6364ddba010743a0fae943132`.
  Verified the complete native birthday preparer at `80921324..80921464`,
  its boundary table, dispatch table, player pointer/month/day, both random
  draws, and ten-byte native item mirrors. The body hash is
  `770b3dbb0270671fe82acf1804887c667dd60e4c1ebd6f07c95b95be35a05440`.
  The complete pointer/jump/branch audit finds exactly one entry reference,
  ordinary-overlay offset `0045D4`, and no external interior references.
  Source definitions retain their recorded pins. GameCube repeat-avoidance state
  is not present in the native helper and is not imported.
- Added `runtime/birthday.c`: full common English names for all twelve animals
  and Western signs, full month names, and ordinal days. Existing sixteen-byte
  message-item rows retain Sagittarius in full while preserving all fifty
  native compatibility bytes and every saved structure. Exactly two native RNG
  draws remain in their original order. The native first-ceiling/minus-three
  constellation calculation retains all byte-valued invalid-date behaviour;
  English display fallback remains separate. Null player consumes no RNG and
  changes no fields. No general-string bank or unrelated destination is widened.
- Extended the guarded ordinary-date patch with one entry jump and delay-slot
  nop. Eight words now change; the original file/BSS sizes, native dispatcher,
  and 550 remaining relocations are retained. Both birthday entry words have no
  relocation. Every one of the 33 native `0C 09 0004` messages owns the complete
  installed-patch dependency independently of identity/candidate metadata. The
  generator withholds unsupported references and prevents alias fallback from
  bypassing that requirement. Omitted or empty metadata cannot remove it.
- Installed complete English `088B/2586` and corrected the acknowledgement in
  existing `088A/088C`. All supplied words, manual newlines, pages, and pauses
  remain. You know it! acknowledges the birthday at `0889`; You're wrong!
  returns to `088A`. Shared greeting `0041` stays unchanged. The deliberately
  random Western sign in `2586` retains confidence, modesty, and incorrect-sign
  answers at `259D/259E/259F`, including friendship values `005/003/069`.
  The native-menu registry has 167 approvals. The contextual registry has 26:
  22 adapted references, two complete unchanged-menu references, and two original
  quizzes. The explicit unchanged-menu kind binds the entire unadapted reference
  and forbids a fictitious native-menu adaptation; default behaviour stays strict.
- Added complete native-original letter question `1C6F` with both original
  answers and every command preserved. Funny! reaches `1C70`; Like a star!
  reaches `1C71`. The GameCube-only third answer is not added: native `1C72`
  contains only the normal end command. This is a draft, not a reviewed reference
  or a normal letter-show gameplay claim.
- Host checks exercise the real wider setter/reader across all 144 random pool
  pairs, all 65,536 byte-valued date pairs, all retail month/day combinations,
  display fallbacks, complete names, first-row publication before the second
  draw, saved-player retention, and adjacent guards. Source/table/entry mutations,
  all 33 dependencies without metadata, missing entry-hook rejection, complete
  reference controls/branches, and the original letter question are checked.
  The full 714-test run passes in 268.581 seconds at
  `build/tests-birthday-full-02.log`. The first full run found two stale test
  expectations: the empty record was incorrectly asserted as literal zero
  instead of `7F00`, and the menu-approval count still expected 165 instead of
  167. Both test expectations were corrected; no ROM change was needed.
- Independent pinned-Docker modules agree: 23,488 linked bytes, 1,088 bytes free,
  the unchanged 32 KiB reservation, and module SHA-256
  `9f1f730f13d0a2a78bc2bbcfc570a5fa2249976cbe253edd6a22274eb95a6460`.
  Birthday stack use is 64 bytes; both local helpers use zero additional stack.
  Rebuilt module-bound NPC capture/creator and generation-probe artifacts;
  independent creator code/relocation also match. Earlier ignored default-module
  and imported-overlay artifacts were moved to explicit calendar-quiz backup
  directories before refreshing defaults. No source ROM, old pilot, or user save
  was replaced.
- `build/birthday-final-candidates/` has 12,532 ordinary edits: three additions,
  only existing `088A/088C` payloads changed, and 29 earlier payloads receive
  metadata-only dependencies. Main coverage is 10,739: 9,765 references, 585
  original dialogue drafts, one original continuation, 289 development labels,
  and 99 diagnostics. All 460 choice texts, 178 villager-name slots, and 779
  ordinary item slots remain. The 1,013 gaps comprise 91 Japanese-static,
  919 nonstatic, one Latin, and two symbol records. Ten nonstatic entries have
  dynamic fields; none is deemed unreachable. Main rejections are 926
  unconfirmed identities, 62 control differences, 24 missing fields, and two
  overflows, with one original fallback. Reference/label warnings total 1,475,
  plus the two separate original shout warnings. Source weight is
  638,255/746,978; main source weight is 627,923/637,761. These are coverage
  measurements, not completed semantic review or total project completion.
- Basic generation is 11,789 edits. It adds `1C6F` and withdraws 28 previously
  admitted birthday references that lacked actual English field preparation;
  five other birthday requests were already withheld. Every retained basic
  payload is unchanged. Full generation includes all 33. The basic contextual
  output retains three mappings; eighteen lack complete labels and five require
  birthday/calendar preparation. Withholding a misleading basic candidate is
  not a removal from the full translation pilot.
- `build/birthday-final-pilot/animal-forest-halfwidth.z64` SHA-256:
  `87f1c48893c48b94efe2380a150bcc2b3f7c3a6cc3a762035ef98fc5097d9062`.
  UPS SHA-256:
  `4039b2a6b83b66406f54539deacd4fdb68a6e4b45baf61a75c1b96d9cbb6653f`.
  Candidate SHA-256:
  `349e8796694880524a4ebb3529d6ea6d834c5913d1409991eb025b23e3a0aa57`.
  `build/birthday-final-artifact-audit-02.log` checks all 12,532 installed
  payloads, full UPS reconstruction, all earlier payload changes, dependency
  coverage, both unchanged font atlases, and independent module/creator/ROM/patch
  equality. Only DMA container `00019D40`, code `00675720`, board `007908A0`,
  ordinary overlay `00815B70`, Pelly `008A6C10`, main data/table, module, and NPC
  creator change. Board/Pelly changes are their guarded resident-address bindings.
  The initial audit's expected file set omitted those two shifted bindings;
  the corrected audit verifies them without rebuilding the ROM.
- `build/smoke-birthday-dates-02/` passes 4,083 steps, 913 native calls,
  274 scenario-declared expected returns, 1,588 memory assertions, and 150
  cartridge message loads. Birthday coverage includes both sides of all twelve
  constellation boundaries, both complete random pools, 48 independent native
  RNG calls, 57 complete question/message loads, all 33 related conversations,
  190 full field insertions, and null-player rejection. The all-message batch
  uses complete Sagittarius in both Western fields. It leaves the earlier food
  field in `0872` and later lucky-colour field in `29F9` untouched. The complete
  manager, saved player, RNG, clock, saved game, code, and heap/stack/module
  guards remain; both owned allocations are freed before one checkpoint restore.
  The ordinary date/calendar group also passes all 53 preparations, thirteen
  earlier conversions, eighteen direct quiz conversions, six current-date
  requests, two no-op orders, twelve date-message loads, and twenty insertions.
  All 54 contextual messages, 57 selections/insertions, and 53 branches pass.
  Scenario SHA-256:
  `4bf56831839d5fbdbdfd0b86f7a9dc2511758e2b5dfa9147848c3be65e32c697`.
- `build/smoke-birthday-arrival-mail-02/` passes the fresh four-MiB English
  keyboard/train-to-town scenario and then the real cartridge NPC creator:
  1,947 steps, 245 native calls, and 546 memory assertions. All 48 original
  metadata/RNG comparisons, eight successive letters, and eight rejections pass.
  Zero creator/resource bytes are debugger-uploaded. Complete reconstruction,
  original metadata, names/words, capitalization, heap release, saved-game
  retention, guards, and the final town checkpoint restore pass. The post-scenario
  SHA-256 is `b0ef875ebecafa529b7515193ec40d6e2a463449d74e354aec3f02e31a2a8805`.
  Actual letter delivery is not exercised or enabled by this evidence.
- Both successful runs have no seeded saves or checkpoints, disable audio and
  both save-write flags, restore one checkpoint, and shut down gracefully.
  FlashRAM remains `b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260`;
  Pak remains `ab2a6e04fd3ceb36594f1216c888a1b8bd0a3ba0a94f715a7c7601e98c49ec51`.
  `build/birthday-final-native-audit.log` independently verifies all declared
  call arguments/returns, complete plain reads, every custom assertion/hash,
  restored stacks, recorded save hashes, and regenerated scenario identity.
- Initial emulator batches were cut off by the declared timeouts without a
  failed text/memory assertion: approximately 610 seconds for the combined native
  batch and 308 seconds for the 300-second journey. The bounded runner ceiling
  is now 1,200 seconds, with the same forty-second default; successful runs use
  900 seconds. Mail tests execute after town creation, not from an unpopulated
  title checkpoint. An initial 900-second request was rejected before launch by
  the old CLI ceiling. Four read-only CLI boundary checks and seven scenario
  tests pass after the ceiling change. No timing/layout or production-ROM change
  was made to accommodate a test timeout.
- Updated the birthday, date, choice, menu, building, progress, and queue records.
  Reviewed the next storage, raffle, offering, and twin-speaker gaps while the
  emulator batches ran. Normal gameplay/save validation, remaining main text and
  general/name/mail destinations, final wording/presentation, image replacements,
  hardware, and patch-only release remain. The title screen stays the first
  image priority; no replacement is installed. The complete project goal remains
  active.

## 2026-09-08 — Complete native storage, raffle, and offering messages

- Added six complete original drafts: `0A0B/10D9/10DA/10DB/112C/10E1`.
  Storage keeps its original Remove / Never mind... / Swap order. All three
  prize announcements retain complete item fields, prize ranks, native Nook
  expressions, and every pause. The offering question retains give/refuse and
  `112D/112E`, without importing the GameCube wishing-well name. No new
  special-actor command permission is introduced.
- The raffle greeting retains all four native twin-speaker pairs and complete
  English echoes. Only the four colour-span lengths and repeated per-character
  scale commands change, under the existing source-bound layout policy.
  RGB `198CDC`, eight-pixel line anchors, 26/32 scale, original pauses, and every
  other native command remain. The explicit-formatting warning is retained for
  rendered-layout review; no font change is made.
- Five focused tests pass in 0.203 seconds at
  `build/tests-storage-raffle-01.log`; all 96 reference tests pass in 17.997
  seconds at `build/tests-storage-raffle-reference-01.log`. Complete native
  controls, source hashes, all English echoes, menus/branches/prizes, and bounds
  pass. Expanded bounds in draft-file order are 98/166/146/175/86/312 bytes.
  All six are available in both basic and full generation. The unchanged
  runtime retains the independently recorded 714-test birthday checkpoint;
  this content batch does not claim a new full-suite run.
- Full generation has 12,538 ordinary edits; basic generation has 11,795.
  Every earlier full/basic edit object remains unchanged. Main coverage is
  10,745: 9,765 references, 591 original dialogue drafts, one original
  continuation, 289 development labels, and 99 diagnostics. The 1,007 gaps
  comprise 85 Japanese-static, 919 nonstatic, one Latin, and two symbol records.
  Ten nonstatic records contain dynamic fields; none is deemed unreachable.
  Reference rejections are 925 unconfirmed identities, 57 control differences,
  24 missing fields, and two overflows, with one original fallback. All 460
  choices, 178 ordinary villager names, and 779 ordinary item slots remain.
  Reference/label warnings remain 1,475; original formatting warnings are
  separate, including the new complete echo. Source weight is 638,459/746,978;
  main source weight is 628,127/637,761. These are candidate measurements,
  not semantic or whole-project completion claims.
- Pilot: `build/storage-raffle-pilot/animal-forest-halfwidth.z64`.
  ROM SHA-256:
  `234e6e3a066826c7976f4e84d8eb1bac04b97c779e4988a13c3a19b72c4aff78`.
  UPS SHA-256:
  `e3e9cbfdf10ba3e0b8e88cb961a3b9bf61e54696392e029a91be2121d29e3a60`.
  Candidate SHA-256:
  `fd0f72c63e9172882cf4e6cb5f6949997a0a3167aec0c830df8027b67474f8bf`.
  `build/storage-raffle-artifact-audit.log` confirms all 12,538 installed
  payloads, source/build/candidate hashes, unchanged earlier candidates, and
  complete UPS reconstruction. Only DMA container `00019D40`, main data
  `02000000`, and pointer table `00CF9000` change from the birthday pilot.
  The DMA container is unchanged outside its table. All runtime/name/item/mail
  resources and both font atlases are unchanged.
- `build/smoke-storage-raffle-01/` passes 88 steps, seventeen native calls,
  eleven declared expected returns, and 41 memory assertions. All six drafts,
  connected messages `0A0A/0A0C/0A0D/112D/112E`, and six menu labels load
  completely from the cartridge. `build/storage-raffle-native-audit.log`
  independently verifies regenerated scenario identity, every call argument,
  expected return, complete read, guards, single checkpoint restoration,
  silent graceful shutdown, and blank isolated FlashRAM/Pak. Scenario SHA-256:
  `479fe0ad693741bbdf75d4ed967862f3751dd855fb2d02591965442d6cc16fae`.
  The four-MiB run uses no seeded saves or checkpoints and disables both
  save-write flags. No storage swap, prize delivery, offering deduction,
  ordinary twin rendering, or original-hardware acceptance is claimed.
- Updated the current progress, queue, and implementation contract. Main
  content/destination integration and normal gameplay remain active. The title
  screen remains the main image priority after the main port. The complete
  translation goal remains active.

## 2026-09-08 — Complete native service replies and preserve random responses

- Added four complete GameCube references for `263E/2646/2650/26C5` with one
  individually reviewed `complete_reference.native_random` rule each. The
  English three-entry branch duplicates one destination; the native two-entry
  command remains exact. Source/reference offsets, complete command bytes,
  identical destination sets, unique spans, and complete source/reference/output
  hashes are mandatory. Every other gameplay command `08..19` must agree before
  the ordinary adapter. Other adaptation permissions cannot combine. The builder
  rejects modified complete payloads independently of edit metadata. All English
  words, newlines, pages, waits, emphasis, and pauses remain. No runtime change.
- Reviewed all eight connected random replies, including praise versus louder
  retries, sleepy bedtime acceptance, and the sunshine-boy denial/training joke.
  The four expanded bounds are 58/58/59/127. Native `2769`, with a different
  third destination, is deliberately outside the same-destination-set rule.
  `14FD` passes N64 content validation but the supplied GameCube plus glyph does
  not reproduce its original hash through the current native encoder; that
  reference remains withheld for source-encoding work, not paraphrased away.
  `17B1` still has the GameCube-only cancellation command and remains withheld.
- Added fifteen complete native-specific drafts in
  `translations/n64-connected-services.json`: `1722/172A/1737/1889/1CD7/1D27/
  2065/2077/23DC/2769/2798/2CD0/1502/1D3D/28EE`. They retain the complete twin
  sale/order/apology/disposal exchanges; Gracie outfit advice; moving-away
  remembrance; gift-refusal self-loop; catchphrase replacement/reassurance;
  rain-colour paint; brown-paint aside; suspense lead-in; forced sale; repayment
  and advice reactions; and the complete mock-shopkeeper sale/item reveal.
  Native-only meanings and actions are not replaced by different GameCube ones.
- Every native command/argument remains exact except three complete English
  twin echo colour/scale spans under the existing layout policy. All ten echoes
  retain RGB `198CDC`, eight-pixel anchors, and original 26/32 scale before
  every character. Native pair counts remain 2/5/3. The three explicit-formatting
  warnings remain for the polish pass; the other twelve drafts have no layout
  warning. Native-original line placement avoids overlong dynamic-field lines;
  no GameCube reference is reflowed. Bounds in file order are
  215/600/336/395/309/276/192/285/369/118/62/194/275/282/571.
- Moving keeps two answers and `1CD8/1CD9`; native `1CDA` is empty. Gift refusal
  returns to `2065`; alternative native `2068` is empty. Catchphrase answers keep
  `2774/2775`. Brown paint retains native `276A/276B/276C`, including the
  original too-flashy branch rather than GameCube `276D`. Shared labels stay
  unchanged. No extra GameCube quest request, persistent mood, absent catchphrase
  field, new branch, or new action is installed.
- Five focused draft tests pass in 0.209 seconds at
  `build/tests-connected-services-01.log`. All 104 reference tests pass in
  19.029 seconds at `build/tests-connected-services-reference-01.log`, including
  eight new random-reference checks. The content-only wording suite explicitly
  excludes the new random-rule category, whose complete-reference and native-flow
  retention have their own tests. The unchanged production runtime retains the
  full 714-test birthday checkpoint; no new full-suite run is claimed.
- Full generation has 12,557 ordinary edits; basic generation has 11,814.
  All nineteen new records appear in both. Every earlier full/basic edit object
  is unchanged. Main coverage is 10,764: 9,769 references, 606 original dialogue
  drafts, one original continuation, 289 development labels, and 99 diagnostics.
  The 988 gaps comprise 66 Japanese-static, 919 nonstatic, one Latin, and two
  symbol records. Ten nonstatic records have dynamic fields; none is deemed
  unreachable. Reference rejections are 924 unconfirmed identities, forty
  control differences, 23 missing fields, and two overflows, with one original
  fallback. Reference/label layout warnings stay 1,475; original echo warnings
  are separate. All 460 choices, 178 ordinary villager names, and 779 ordinary
  item slots remain. Source weight is 639,612/746,978; main source weight is
  629,280/637,761. These are candidate measurements, not completed review.
- Pilot: `build/connected-services-pilot/animal-forest-halfwidth.z64`.
  ROM SHA-256:
  `0f3777d64a6594224c2150259834378e437cf978e882c8ae3688158a80d35d02`.
  UPS SHA-256:
  `9fad302395751e09bf8318479335a73daed61c9c5364440bbc2de09d08a652ed`.
  Candidate SHA-256:
  `58a9dd78125fc2f0796e1deaf7e935db5c61fcf29d3c14d43c376205e68ac672`.
  `build/connected-services-artifact-audit.log` verifies all 12,557 actual
  payloads, complete UPS reconstruction, all earlier full/basic edits, and
  unchanged font atlases. Only `00019D40`, `02000000`, and `00CF9000` DMA files
  change from the storage/raffle pilot; the container changes only its table.
  Runtime, names, items, mail resources, font metrics, and saved formats remain.
- `build/smoke-connected-services-01/` passes 276 steps, 57 native calls,
  39 declared expected returns, and 137 memory assertions. The nineteen new
  messages and twenty directly connected replies load completely, plus eighteen
  menu labels. `build/connected-services-native-audit.log` independently
  regenerates the scenario and checks every address, argument, return, restored
  stack, complete memory read, guard, single checkpoint restoration, and silent
  graceful shutdown. Scenario SHA-256:
  `bb1b95f6e19cad56bb3c7d8b87c8512e6f336d4cba085e5ab0eeab9748fea080`.
  The four-MiB run has no seeded saves/checkpoints, disables both save-write
  flags, and retains blank FlashRAM/Pak. These are text loads, not executed
  random selections, gifts, trades, friendship changes, catchphrase entry,
  ordinary saving, rendered twin echoes, or original-hardware validation.
- Current progress, queue, reference-choice boundaries, and both new contracts
  are updated. Remaining main dialogue, general/name/mail destinations, normal
  gameplay, final semantic/presentation review, original hardware, and patch-only
  release remain. The title screen stays the first image priority. The complete
  project goal remains active.

## 2026-09-08 — Preserve the complete English plus-glyph controller tip

- Resolved the source-encoding rejection for `14FD` without changing a font.
  The supplied GameCube raw message has 254 bytes and stores its plus at offset
  112 as `B4`. The pinned English decoder identifies that character as +. The
  existing native encoder/font uses `5C` for +. Direct raw-data/decoded-reference
  comparison confirms this is the only difference between the complete English
  and native encodings. GameCube `5C` is a different symbol; raw code copying
  would be incorrect.
- An explicit `complete_reference.gamecube_plus_offsets` rule reconstructs
  exactly the approved English glyph bytes solely for original-reference hash
  verification. Offsets must identify complete native plus text tokens, never
  command arguments or other glyphs. Empty/duplicate/unsorted/malformed offsets,
  stale full hashes, and combined adaptations fail. The installed payload keeps
  the ordinary native encoding, with independent complete-output verification.
  No general glyph substitution, unsupported-punctuation workaround, or font
  investigation is introduced.
- Complete NES advice retains + Control Pad and Control Stick, the two original
  expressions, catchphrase, every English word, manual line/page, emphasis, and
  pause. Its native output hash is
  `d4d43dd7e725ea39d8fd2eeaf8171fdd04b19461e1a6d0e80d901af96682b01d`;
  original English hash is
  `477a33ac04951016bf03873c51cc0a555b21633d9182e3b48e75b693b897d453`.
  Stored/expanded bounds are 254/300 bytes, valid in basic and full output.
- All 109 reference tests pass in 18.534 seconds at
  `build/tests-reference-plus-01.log`, including five new source-encoding checks
  and the existing complete-content retail check covering this new approval.
  The actual extracted English data and pinned decoder are checked, not just
  a synthetic reconstructed fixture. No unchanged native batch is rerun for this
  host-only encoding change; a dedicated `14FD` cartridge load is explicitly
  queued with the next content batch. The existing 39-message/18-label native
  checkpoint and full 714-test runtime checkpoint remain their own evidence,
  not a claim that this specific conversation has been played.
- `build/reference-plus-candidates/` has 12,558 ordinary edits; basic output has
  11,815. Only `14FD` is added and every earlier full/basic edit object remains
  unchanged. Main coverage is 10,765: 9,770 references, 606 original dialogue
  drafts, one original continuation, 289 development labels, and 99 diagnostics.
  The 987 gaps include 65 Japanese-static, 919 nonstatic, one Latin, and two
  symbol records; ten nonstatic records contain dynamic fields. Rejections are
  923 unconfirmed identities, forty control differences, 23 missing fields,
  and two overflows, with one original fallback. Source weight is
  639,709/746,978; main source weight is 629,377/637,761. These remain candidate
  measurements, not semantic or project completion.
- Pilot: `build/reference-plus-pilot/animal-forest-halfwidth.z64`.
  ROM SHA-256:
  `b4f88b4df100c8cb949a7b7bbdc4911ce525fe3aef3a5877490f9568f6e97839`.
  UPS SHA-256:
  `f916234078f467a36b8c352d8a85477cf4bcb41f91b359b44196eb9ecf43806e`.
  Candidate SHA-256:
  `09bcb8764061e8a7d3ebe4b3dd0199a16108ff95041b88bc3aad2d18aad08d6e`.
  `build/reference-plus-artifact-audit.log` verifies all 12,558 actual installed
  payloads, source/candidate/build hashes, complete UPS reconstruction, and
  unchanged earlier full/basic edits. Only DMA files `00019D40`, `02000000`,
  and `00CF9000` change; the container differs only in its table. Both font
  atlases and every runtime/name/item/mail resource remain unchanged.
- Updated the source-encoding contract, progress, and next-batch queue. Main
  translation/integration, normal gameplay, final review, title-first images,
  the GameCube-style keyboard, original hardware, and patch-only release remain.
  The complete project goal stays active.

## 2026-09-08 — Complete eleven special-actor conversations

- Imported eleven complete supplied English conversations: Gracie `0723`, Redd
  `0789/078D`, Jingle `07AA`, sound settings `09C8`, Gulliver
  `2401/2402/2403/240B`, and Rover `2ACF/2ADD`. Every word, manual line,
  emphasis, and pause remains. Redd's complaint and two Gulliver stories use
  existing English wait/newline/page-clear boundaries at `[523,528)`,
  `[635,640)`, and `[668,673)`. Their full expanded lengths exceed the buffer;
  fourteen complete parts fit without shortening text or expanding runtime RAM.
- Bound the exact native reserve slots `2B02/2B03/2B07`, each with source hash
  `b2c0b6f9facf02630f093fd1b6a5a6e47d722ecadd50e6c82fae305db4821e2c`.
  Complete native-script and pinned executable/data-section scans find no
  incoming target, relevant executable immediate, or aligned data halfword.
  `2B08` has data matches and was not used; nearby save-menu records were
  untouched. These three previously translated reserve labels intentionally
  become continuations; every other earlier full/basic edit object is unchanged.
- Strengthened independent sequence validation: only speaker-zero expression
  requests may repeat, move, or disappear with English presentation. All other
  actor requests retain exact native order and multiplicity. Every earlier
  approved group passes without payload changes. New tests reject duplicated,
  dropped, and reordered mood/duration and quest requests. All new expression
  tuples already occur in their own native root, with no extra actor approvals.
  Sound menu indices/actions, external `072A/09CA` links, and Gulliver's final
  `01` endings remain native. The test does not change sound settings or play audio.
- Five focused tests pass in 8.143 seconds, 110 reference tests in 26.098 seconds,
  and nine long-advice tests in 5.821 seconds, in the three
  `build/tests-special-actors-*-02.log`/`build/tests-special-actors-02.log` files.
  The first reference run exposed two stale aggregate-count expectations
  (`36/32` rather than `50/46`); those fixtures were updated for the fourteen
  approved parts, and the complete relevant suites passed. No production
  runtime or font changes were needed, and the unchanged 714-test full-runtime
  checkpoint is separate evidence rather than a newly rerun suite.
- `build/smoke-special-actors-01/` passes 278 recorded steps: 59 native calls,
  51 checked returns, eighteen complete message loads, eight choice labels,
  and 109 memory assertions. This includes all fourteen sequence parts,
  the queued complete `14FD` plus-glyph tip, sound labels, and connected
  `072A/09CA` messages. The independent audit regenerates the exact scenario
  and checks every call/argument/return, restored stack, complete read/guard,
  continuation and ending phase, one restored checkpoint, silent graceful
  shutdown, and blank isolated FlashRAM/Pak. Four-MiB mode has no seeded saves
  and both save-write permissions disabled. Scenario SHA-256:
  `34ccbf1b06d7ea38f689e6a03c4e8ea940679cca8321f25368deb119b74c3b8c`.
  This is not ordinary special-actor traversal, gift/service execution,
  sound-setting UI, rendered expressions, normal saving, or hardware acceptance.
- Full/basic generation has 12,569/11,826 edits. Main coverage is 10,776:
  9,784 references, 606 original dialogue drafts, one original continuation,
  286 development labels, and 99 diagnostics. The 976 gaps include 54
  Japanese-static, 919 nonstatic, one Latin, and two symbol records; ten
  nonstatic records insert dynamic fields. Rejections are 918 unconfirmed,
  34 control differences, 23 missing fields, and two overflows, with one
  original fallback. Source weight is 642,350/746,978, main 632,018/637,761.
  The 1,478 reference/label layout warnings remain review tasks; no automatic
  reflow is performed. These are candidate measurements, not project completion.
- Pilot: `build/special-actors-pilot/animal-forest-halfwidth.z64`.
  ROM SHA-256:
  `9ce34b89eb67c03581357b1a7e6334b3edb7c8a2dee974f8cc92e2764da1856e`.
  UPS SHA-256:
  `93a9439a874b38c0c883c3f63daf89bf88f0ed3a36d5a6942d06be1f86737acb`.
  Candidate SHA-256:
  `40f07b36fcb5831aaa2f367e589dea6e19c33475d20a8c8996d946b4fd112661`.
  `build/special-actors-artifact-audit.log` verifies every installed payload,
  source/candidate/build hashes, UPS reconstruction, and exact old/new candidate
  differences. Only DMA files `00019D40`, `02000000`, and `00CF9000` change;
  the container differs only in its table. Both font atlases and all runtime,
  name, item, and mail resources remain unchanged. The first audit asserted the
  wrong label-policy name; inspection confirmed original `exact`/`reserved`
  metadata, the assertion was corrected, and the full audit passed.
- Updated the current progress, queue, and sequence contracts. Remaining main
  dialogue, general/name/mail destinations, normal gameplay, final review,
  title-first image replacements, GameCube-style keyboard, original hardware,
  and patch-only release remain. The full project goal stays active.

## 2026-09-08 — Complete five character-context references

- Imported complete `0785/240A/240D/2AC9/2AD4`: Booker's lost-property explanation,
  Gulliver's weekly falls and sea tales, and Rover's seat refusal and money/arrival
  encouragement. Native `0786/240E/2AD2/2ACD` respectively supply only the explicitly
  listed same-character expressions. The full English localisation, every manual
  line/page, emphasis, pause, native non-expression request, field, and ending
  remains. No continuation allocation, runtime/font change, or new adaptation is
  needed. `2AC9` retains name-entry request `09/09/0001`, command `55`, and end `01`.
  Expanded bounds are 211, 479, 487, 237, and 444 bytes.
- Five focused tests pass in 11.126 seconds, 110 reference tests in 28.653 seconds,
  and all five earlier special-actor tests in 8.188 seconds. Logs are
  `build/tests-contextual-actors-{01,reference-01,special-01}.log`.
  The focused checks reject missing/stale expression support, extra actor
  requests, and modified reference wording; full/basic imports are identical.
- `build/smoke-contextual-actors-01/` passes 79 steps, fifteen native calls/returns,
  five complete cartridge loads, both ending phases, and 27 memory assertions.
  `build/contextual-actors-native-audit.log` independently regenerates all actions
  and checks exact calls/arguments/returns, restored stacks, full reads/guards,
  one restored checkpoint, silent graceful shutdown, and blank FlashRAM/Pak.
  No seeded saves or save-write permissions are used. Scenario SHA-256:
  `7f6f91ab691ce6b216af283d6c4f797ad104789e47dbb6e8c349574583c9fbfb`.
  Actual name-entry progression, expressions, collection, and actor traversal
  are not established by injected loader/terminator calls.
- Full/basic candidates: 12,574/11,831. Main: 10,781, comprising 9,789 references,
  606 original dialogue drafts, one original continuation, 286 development labels,
  and 99 diagnostics. Remaining main records: 971, including 49 Japanese-static,
  919 nonstatic, one Latin, and two symbol-only records. Ten nonstatic records
  insert fields; reachability remains unestablished. Rejections: 918 unconfirmed,
  29 control differences, 23 missing fields, and two overflows, with one original
  fallback. Reference/label layout warnings: 1,480. Source weight:
  642,786/746,978; main 632,454/637,761. These remain candidate measurements.
- Pilot: `build/contextual-actors-pilot/animal-forest-halfwidth.z64`.
  ROM SHA-256:
  `6d780f7deddccaf9e6e6498e70bebcb9771785cbac8a769ade8d88747c2ac040`.
  UPS SHA-256:
  `0ccaac657ea4764a5fa798eae343925aadc0000648e9f9b3565f229c5bfcf6c0`.
  Candidate SHA-256:
  `00cb11bd464da9092a6caad00a3678c8685c0649ebfdd3060b8672ad8d18b841`.
  The independent artifact audit checks all 12,574 installed payloads, input/build
  hashes, UPS reconstruction, only the five added IDs, and every earlier full/basic
  edit unchanged. Only `00019D40/02000000/00CF9000` DMA files change; the first
  differs only in its table. Runtime, both font atlases, and other resources match.
- Current progress, queue, and reference contracts are updated. Remaining main
  controls/fields/long scripts, test text, general/name/mail integration, normal
  play, final review, title-first images, GameCube-style keyboard, hardware, and
  patch-only release remain. The complete project goal stays active.

## 2026-09-08 — Complete both long train phone calls with native skip behaviour

- Imported all English content for `2AD0 → 07DA` and `2ADE → 2B1B`. Original
  full bounds are 1,235/1,259 bytes. Existing English wait/newline/page-clear
  spans `[460,465)` and `[471,476)` become native continuing-message boundaries;
  parts fit at 513/740 and 494/783 bytes. Every word, line, other page break,
  voice control, grey/small-text formatting, pause, player/town field, and final
  `00` remains. Both generic reserve records have the pinned common label hash
  and no native script, relevant code-immediate, or aligned data references.
- The previously implemented `72/73` protected-pacing pair stays entirely in
  each first part. Sequence validation now permits balanced same-part spans with
  the verified resident runtime and rejects unmatched, nested, cross-part, or
  runtime-less spans. Native controls remain ordered. No runtime rebuild, buffer
  expansion, font change, or save-format change is needed.
- Confirmed that `06/07` enable/disable cancellation, not phone mode. Corrected
  the living long-advice spec. Native message change `8009E658` resets loaded
  cursor/line positions and timer but retains cancellation-enabled word `2C0`.
  Native normal-page setup `800A04E4` clears only active cancellation `2BC`;
  final `07` clears both. This permits the reviewed page split inside the
  skippable section without changing the protected opening or later skip state.
- Five focused tests pass in 1.895 seconds, ten advice/pacing tests in 4.805
  seconds, 110 reference tests in 29.198 seconds, and ten special/contextual-actor
  tests in 20.026 seconds. Logs: `build/tests-train-phone-01.log` and the
  `build/tests-train-phone-{long-advice,reference,special}-01.log` files. Tests
  check full reference reconstruction, cuts, capacities, runtime requirements,
  partial/stale/payload rejection, exact voice/cancellation operations, reserve
  scans, and pinned native loader/reset/cancellation code. The unchanged
  full-runtime suite retains its separate 714-test checkpoint.
- `build/smoke-train-phone-01/` passes 211 steps: 42 calls, 38 expected returns,
  eight direct loads, four actual native message changes, four normal-page setup
  calls, and 104 memory assertions. Both active-cancel states retain enabled
  cancellation across each real loaded continuation. Protected flags, final
  reset, complete buffers, cursor resets, timer, adjacent/module guards, restored
  stacks/checkpoint, silent graceful shutdown, and blank FlashRAM/Pak pass.
  The independent native audit regenerates all actions and checks every recorded
  address, argument, return, and complete read. Scenario SHA-256:
  `8236b8cd0fdea33bcd956948ade4af40db909d2f7d0d3b633085846d1318e64b`.
  Normal train actor traversal and actual controller timing remain unverified.
- Full/basic output has 12,576/11,829 edits. Full adds two roots and converts
  two reserve-label candidates to continuations. Basic omits both runtime-only
  sequences and their two allocated labels; all other earlier candidates remain
  unchanged. The first artifact audit assumed basic retained those labels;
  candidate inspection showed the generator's all-member withholding, and the
  corrected exact-difference audit passes. No source/tool behaviour was relaxed.
  Main coverage: 10,783 = 9,793 references + 606 original dialogue drafts + one
  original continuation + 284 development labels + 99 diagnostics. Remaining:
  969, including 47 Japanese-static, 919 nonstatic, one Latin, and two symbol
  records. Rejections: 916 unconfirmed, 29 control differences, 23 missing fields,
  and two overflows, with one original fallback. Layout warnings: 1,484.
  Source weight: 643,251/746,978; main 632,919/637,761. These are candidate counts.
- Pilot: `build/train-phone-pilot/animal-forest-halfwidth.z64`.
  ROM SHA-256:
  `930db1592acce9dc8bd1e447a10897ed163fac915e9d2e8e827b0229b33e6079`.
  UPS SHA-256:
  `74af4d9672e704595f157cb351929a2d25a01046644b092708879ce4ee079930`.
  Candidate SHA-256:
  `3e4965a6d26f45a3f99f25a235345561d566537e5b2434d2ea671e0432ac464f`.
  The artifact audit verifies all 12,576 installed payloads, source/build hashes,
  UPS reconstruction, and exact full/basic candidate differences. Only DMA files
  `00019D40/02000000/00CF9000` change, with the first differing only in its table.
  Runtime, fonts, other resources, and saved layouts remain unchanged.
- Updated progress, queue, and sequence contracts. Remaining main dialogue,
  controls/fields, test text, general/name/mail destinations, normal gameplay,
  semantic/presentation review, title-first images, GameCube-style keyboard,
  original hardware, and patch-only release remain. The full goal stays active.

## 2026-09-08 — Complete nine native menu and dialogue follow-ups

- Added complete original drafts for `0467/0970/09D0/0D3F/0F10/10B7/10B8/10BE/17B1`.
  They retain the native seat-refusal/name request, full two-line fortune chant,
  50-Bell question, sound retry, entire sleeping apology about Daddy's turnips,
  snowfall observation, distinct music-player menus, and NES prompt/instructions.
  All controls remain exact except two NES highlight lengths. No GameCube-only
  menu, cancellation command, waking expression, or random continuation is added.
  Expanded bounds are 113, 226, 69, 493, 207, 100, 143, 143, and 62 bytes;
  approved font metrics report no layout warnings for these drafts.
- Five focused tests pass in 0.213 seconds, 110 reference tests in 34.659 seconds,
  and seven native-menu tests in 2.123 seconds. Logs are
  `build/tests-menu-followups-{01,reference-01,native-menus-01}.log`.
  The separate unchanged full-runtime checkpoint remains 714 passing tests.
- `build/smoke-menu-followups-01/` passes 193 steps, 41 native calls, twenty
  declared returns, twenty full messages, 21 choice labels, and 83 memory checks.
  Eleven connected fortune/sound/music/NES replies are included. Independent
  regeneration verifies every call/address/argument/return, complete read,
  guard, restored stack/checkpoint, silent four-MiB shutdown, and blank isolated
  FlashRAM/Pak. No save seeds or write permissions are used. Scenario SHA-256:
  `f9e525f529d56969fd527b55b07ea3593ab7031eb0c7f2e29eab71329227b2d0`.
  Normal item/music/fortune/NES actions, name entry, sleeping animation, and
  weather conversations remain gameplay checks, not claims from injected calls.
- Full/basic output has 12,585/11,838 edits. Only the nine new IDs are added;
  all earlier complete edit objects remain unchanged and no reserve is allocated.
  Main coverage: 10,792 = 9,793 references + 615 original dialogue drafts + one
  original continuation + 284 development labels + 99 diagnostics. The 960 gaps
  comprise 38 Japanese-static, 919 nonstatic, one Latin, and two symbol records.
  Ten nonstatic records contain dynamic insertions; reachability remains open.
  Rejections: 915 unconfirmed, 21 control differences, 23 missing fields, and two
  overflows, with one original fallback. Reference/label warnings remain 1,484.
  Candidate source weight: 643,605/746,978; main 633,273/637,761.
- Pilot: `build/menu-followups-pilot/animal-forest-halfwidth.z64`.
  ROM SHA-256:
  `36d2809c538c22aceb3faa75721ad7917a608285a5fbc1bfdd9b577d4cb8692b`.
  UPS SHA-256:
  `274ac58c29d3510e5559ab39616d587bbb02532e9e3ee1d8205e6a418e0db557`.
  Candidate SHA-256:
  `971a4f67e2384870ceb21acae5fa1b1cf419d58d301e2346784a36080273e0d6`.
  The independent artifact audit verifies every installed payload, source/build
  hash, complete UPS reconstruction, and exact full/basic differences. Only
  `00019D40/00CF9000/02000000` DMA files differ; the first changes only its table.
  Runtime, both font atlases, all other resources, and save layouts are unchanged.
- Recorded the native `0970` second-answer route back to itself for ordinary
  decline/cancellation review; did not silently replace it with the GameCube
  branch. Identified shared size labels in clothing `1772` and all three number
  games `2D01/2D06/2D0B`; scoped numeric labels remain required for all three,
  including the two already translated candidates. Progress, queue, and the new
  menu-follow-up spec track these limits. Main translation/integration, gameplay,
  semantic/presentation review, title-first images, keyboard, hardware, and
  patch-only release remain. The complete project goal stays active.

## 2026-09-08 — Complete Resetti and Gulliver cue/timed-ending scripts

- Imported six full English scripts: `1B3B`, `1B41`, `2362`, `23E8`, `2511`,
  and `23FF`. They retain the Reset Alarm lecture, bathing farewell, relaxed-play
  lecture, one-sock story, complete mock-reset threat, and Gulliver's roughhousing,
  swimming, video-game, rescue, and treasure story. No wording is shortened.
  Existing page gaps `[619,624)`, `[511,516)`, and `[555,560)` split the three
  long scripts into reserves `2B42/2B43/2B46`. Bounds are 896; 610; 672/580;
  842; 564/523; and 578/487. All three reserves have the generic-label source
  hash and no pinned native script, relevant code-immediate, or aligned data
  references. Nearby slots with data hits were not allocated.
- Added explicit complete-reference sound-cue and timed-ending permissions to
  sequence validation. Native `59` is a sound trigger, not an idempotent state
  setter. Four approvals retain full English cue placement/count: native/English
  counts 9/10, 5/6, 9/8, and 6/7. Only native `05/06` repetitions may differ,
  within identical actor/action intervals; comparison does not remove installed
  cues. Both native and English tables map those indices to `0427/0428`.
  All other sound/music commands, fields, and native actions remain guarded.
- Explicit `5808` endings remain only in the final `1B41/2511` parts. Both native
  parser phases remain unchanged. The retail end timer is `(8-1)*2+1 = 15`,
  unlike the GameCube source's doubled shift result of 29. Native instructions,
  parser, dispatcher, and sound table are pinned in host tests. No production
  timer, runtime, font, music operation, reset action, or save format changes.
  Gulliver's additional expression `0F` is bound only to his own native `240E`.
- Eight focused tests pass in 6.795 seconds; 110 reference tests in 33.144 seconds;
  ten earlier special-actor tests in 19.927 seconds; and five train-phone tests
  in 2.054 seconds. Logs are `build/tests-resetti-gulliver-02.log` and
  `build/tests-resetti-gulliver-{reference-02,special-01,phone-01}.log`.
  The first reference run failed only two catalogue-count fixtures (59/51);
  the new nine sequence parts require 68/60. Updating those expected counts
  resolves both failures without weakening validation. The separate unchanged
  full-runtime checkpoint remains 714 passing tests.
- `build/smoke-resetti-gulliver-01/` passes 309 steps, 68 native calls/returns,
  nine full cartridge loads, 35 sound-cue dispatches, both timed endings, and
  143 memory assertions. Both ending timers equal 15. Independent regeneration
  checks every call/address/argument/return, full read/guard, restored stack and
  checkpoint, silent four-MiB execution, graceful shutdown, and blank isolated
  FlashRAM/Pak. No save seeds or write permissions are used. Scenario SHA-256:
  `e92d7a1222c4a35da98086fe602285c16d9c8914d5697ce965ff09fe68e6d7d3`.
  These injected calls do not establish ordinary encounters, apology entry,
  mock-reset scene, treasure delivery, audible presentation, or hardware.
- Full/basic candidates: 12,591/11,844. Main: 10,798 = 9,802 references + 615
  original dialogue drafts + one original continuation + 281 development labels
  + 99 diagnostics. Remaining: 954 = 32 Japanese-static + 919 nonstatic + one
  Latin + two symbol records; ten nonstatic records contain dynamic insertions.
  Rejections: 913 unconfirmed, eighteen control differences, 23 missing fields,
  and one overflow, with one original fallback. Layout warnings: 1,488.
  Candidate source weight: 644,939/746,978; main 634,607/637,761.
- Pilot: `build/resetti-gulliver-pilot/animal-forest-halfwidth.z64`.
  ROM SHA-256:
  `58dfb1a1035ee865d0056db738dee98fe09fdc2e0ba32bb2909a72b3a204ba3e`.
  UPS SHA-256:
  `2e2e07afe16b3af615b79286e7b380c15ceae347eadaee6e99ad906b0170e886`.
  Candidate SHA-256:
  `0bc33d0dc5bda084985e250e221158806eb7930b291d0c2bcd78dc2d588f57f7`.
  The artifact audit verifies all 12,591 installed payloads, source/build hashes,
  full UPS reconstruction, only six added IDs and three reserve conversions,
  and every earlier other full/basic edit unchanged. Only DMA files
  `00019D40/00CF9000/02000000` differ; the first differs only in its table.
  Runtime, fonts, and all other resource files match the menu-follow-up pilot.
- Updated progress, queue, and sequence contracts. Remaining main commands,
  fields, glyphs, test text, general/name/mail destinations, ordinary gameplay,
  semantic/presentation review, title-first graphics, GameCube-style keyboard,
  hardware, and patch-only release remain. The complete project goal stays active.

## 2026-09-08 — Complete native special-dialogue follow-ups and sale mood

- Added complete native-original drafts `23EB/23FE/2513`: the repeat-this-phrase
  prompt, full Gulliver waking/wave/fall/rescue/thanks/gift story, and no-resetting
  warning. All native commands and arguments remain exact, including input `55`,
  the ten-byte coloured free-string field, pauses, expressions, choice order,
  acceptance `2514`, and fallback `2515/2516/2516`. No GameCube-only date field,
  expression, or `2517` random destination is introduced. Bounds are 145/823/108,
  with no approved-font layout warnings. Existing answers remain `Got it!`/`No
  way!` and sale answers `Sure!`/`Sorry!`; no shared label is changed.
- Imported complete GameCube `203C`, including its part-time fish-scrubber joke,
  money surprise, and 1,000-Bell sale. Restored the exact native mood-one/duration-
  zero pair between initial quest `0C/02/0003` and expression `09/00/0002`.
  The new anchor requires those exact initial commands and accepts only duration
  zero; other anchors cannot use zero. Full source/reference/output hashes and
  complete actor order remain enforced. Every English word, page, and pause
  remains; only redundant article suppression before the native item field is
  removed. Its 445-byte bound fits. One conservative money-width warning remains.
- Five focused tests pass in 0.200 seconds, fourteen mood tests in 1.385 seconds,
  all 111 reference tests in 33.932 seconds, and nine topic/batching tests in
  1.023 seconds. Logs are `build/tests-special-followups-02.log` and
  `build/tests-special-followups-{mood-01,reference-01,batching-01}.log`.
  The first focused run caught an outdated 824-byte expected bound after a draft
  wording edit; the actual complete payload is 823. Only the expected bound and
  specification were corrected. The separate full-runtime checkpoint remains
  714 passing tests; no runtime code changes are introduced.
- `build/smoke-special-followups-01/` passes 469 recorded steps: forty complete
  cartridge loads, four choice labels, 52 native mood/timer order dispatches,
  96 total calls, 92 declared returns, and 237 memory assertions. The 468-action
  combined scenario checks fourteen selected messages, including ten connected
  replies, plus all 26 mood approvals. Independent regeneration checks every
  call/address/argument/return, read, fixture write, guard, restored stack, and
  checkpoint. Four-MiB execution, disabled audio, graceful shutdown, and blank
  isolated FlashRAM/Pak pass, with no seed or save-write permission. Scenario
  SHA-256: `3b371b05af0862eca0c737ed35b423bb5d20bbb5d042c66b95059f15cbe180e4`.
  Ordinary sale/payment, apology entry/retry/matching, rescue/gift, and reset
  progression remain separate gameplay requirements.
- Audited the native Majin3 apology preparer, target comparison, rude-reply scan,
  and retail length table. The native table at `809B572C` is
  `6,16,25,30,31,-1`, different from the GameCube. Fourteen of sixteen ten-byte
  targets already have complete candidates; `048E/0491` need sun/skull glyphs.
  Only one of 32 rude-reply strings has a candidate; complete English storage
  and the matching-length contract must change together. Recorded the concrete
  keyboard/caller work without paraphrasing phrases or claiming prompt translation
  completes the editor. No apology detector or target bank is changed here.
- Full/basic candidates: 12,595/11,848. Main: 10,802 = 9,803 references + 618
  original dialogue drafts + one original continuation + 281 development labels
  + 99 diagnostics. Remaining: 950 = 28 Japanese-static + 919 nonstatic + one
  Latin + two symbol records; ten nonstatic records contain dynamic insertions.
  Rejections: 912 unconfirmed, fifteen control differences, 23 missing fields,
  and one overflow, with one original fallback. Reference/label layout warnings:
  1,489. Candidate source weight: 645,388/746,978; main 635,056/637,761.
- Pilot: `build/special-followups-pilot/animal-forest-halfwidth.z64`.
  ROM SHA-256:
  `308c7ce2ac780c86c80e5ab9eadc9963b7d3dad378cffe6791d92b7afc485005`.
  UPS SHA-256:
  `fba2ddd6b2ebd70f4b92359380bd6611604a24989c09801479f9739e5605cfac`.
  Candidate SHA-256:
  `87ad1a974a2f4c69a9174a9dc39dab97cc95741f3b02c68277accb6365e474f0`.
  The artifact audit verifies all 12,595 installed payloads, complete source/build
  hashes and UPS reconstruction, only four added IDs, no reserve conversion, and
  all earlier full/basic edits unchanged. Only DMA `00019D40/00CF9000/02000000`
  differs; the first differs only in its table. All runtime/font/name/item/mail
  resources match the Resetti/Gulliver pilot.
- Updated progress, queue, and the mood/special-follow-up contracts; removed the
  stale `2511` overflow item now covered by the complete timed-ending sequence.
  Remaining main text/fields/glyphs, general/name/mail integration, semantic and
  gameplay review, title-first images, GameCube-style keyboard, hardware, and
  patch-only release remain. The complete project goal stays active.

## 2026-09-08 — Separate English glyph resource and native drawing foundation

- Added exact-source extraction for semicolon, slash, sun, snowman, and skull.
  The supplied GameCube font is 8×8-block-tiled I4, not native linear I4; the
  converter checks the complete executable/font/symbol hashes and decoder
  agreement before extracting cells. Semicolon/slash use the existing resize
  algorithm with advances 3/6; symbols retain complete source pixels and width
  twelve. The 1,600-byte separate resource leaves every native font cell intact.
  Proposed pairs are `80D0/80AE/80A7/80AB/80BA`; all unlisted tags remain unknown.
  Resource: `build/extended-glyphs/glyphs.bin`, SHA-256
  `30dddc658038fea1a4abc359121e1e4fa110edac5f5757ad6001703eff8aae7e`.
- Added bounded portable selection/measurement, resource binding, nested draw
  context, and native rectangle/polygon/texture adapters. Every six-argument
  texture-loader frame value is retained. An independent native instruction/
  pointer audit over 1,838 executable segments finds no external interior
  references into the four replaced entry regions. This is not an exhaustive
  indirect-caller proof. No production hook or import permission is enabled.
- Compiled 1,384 bytes with the pinned VR4300 Docker toolchain. The image has
  1,356 text bytes, twenty read-only/alignment bytes, and eight state bytes.
  The relocator checks internal jumps and signed high/low pairs, including
  native load/store low halves, with explicit type/order/bounds/source failures.
  Independent `build/extended-font-probe-repeat/` compilation matches the whole
  binary, report, and relocation inventory. Code SHA-256:
  `3aa77cc5ea55e6a79df760852f25e306cd0460e98f46e4b4533416268718b07e`.
  Relocation-list SHA-256:
  `67b32f53c2a10fb1426f430a239e03780a34217aef6f8e63fd004cdead4fa36e`.
- Eight focused tests pass in 0.809 seconds (`build/tests-extended-glyphs-03.log`),
  including address/undefined-behaviour sanitizers, all 256 second-byte values,
  exact source pixels, all 29 native-bank tag census, relocation errors and
  signed-low boundaries, and fixture ownership/restoration. Five unchanged
  reader-probe tests pass in 0.007 seconds. The separate full-runtime checkpoint
  remains 714 passing tests; no production runtime source changes are made.
- The first native attempt stopped before executing new code: ordinary runner
  calls reject boot routines and code in reserved test scratch. The final test
  uses the existing verified-code interface and a real native allocation; no
  call restriction is weakened. The relocation build also initially rejected
  direct load/store low halves, then gained explicit checked support for those
  actual compiler instructions. Both failures remain recorded in ignored logs.
- `build/smoke-extended-font-02/` passes 593 recorded steps and 574 generated
  native fixture actions: 113 calls, 67 declared returns, 286 memory assertions,
  and 185 writes. The native allocator supplies 8 KiB at `802DDCE0`; relocated
  code starts at `802DDCF0`, hash
  `46fb9105b8fa2459a92e8b2443aa80df7d9b50fbb0e0c1fc3f2cf0e34c987bbb`.
  All 26 mixed-token sentence draws pass through the actual rectangle/polygon
  functions, with complete display-list/vertex, width, token-index, context,
  resource, and guard assertions. Eight tag-helper boundary cases also pass.
  Actual message-cursor/reveal timing remains untested and unhooked.
- Independent regeneration checks every executed call/address/argument/declared
  return, memory read, fixture write, native thread/stack, and restored hook.
  Entire native font, width table, live save payload, and immutable code remain
  intact. Hooks are restored/flushed before freeing the allocation, then the
  whole checkpoint is restored. Four-MiB execution, disabled audio, graceful
  shutdown, and blank isolated FlashRAM/Pak pass, without seeds or write opt-in.
  No generated display list is submitted to the GPU. Audit summary:
  `build/extended-font-native-audit.json`. Scenario SHA-256:
  `8cb6dbb40acf4d848da323e3436d975c1045cff42e463e8f74cafbbc5873904e`.
  Runner SHA-256:
  `8f056906154f04e7fb319835f1145f772c2cdb754bd9314522671ca241506b91`.
- Added the extended-glyph contract and concrete cartridge/reveal/import/input
  follow-ups. The production ROM/UPS/candidates retain their complete previous
  hashes and counts: 12,595 full edits, 11,848 basic edits, and 28 remaining
  Japanese-static main records. This prototype does not add translated records,
  solve apology input, approve saved two-byte text, or resume atlas-edge work.
  Main follow-ups include the six compatible punctuation/symbol references,
  general strings, remaining mail glyphs/callers, semantic review, and normal
  gameplay. Title-first graphics, GameCube-style keyboard, hardware checks, and
  patch-only release remain. The complete project goal stays active.
