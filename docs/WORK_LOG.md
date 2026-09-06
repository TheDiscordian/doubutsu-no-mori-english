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

Generated assets, logs, screenshots, ROMs, patches, and reference text remain
local under ignored `build/` and `local/` paths. Current status belongs in
`PROGRESS.md`; this file records completed work and test observations.
