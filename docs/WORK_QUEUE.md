# Completion queue

## Active: V3 optional GameCube imports

Use the [automatic furniture pipeline](../specs/V3_FURNITURE_PIPELINE.md) for
new furniture. Twenty-five additional complete assets and their shared runtime
records are installed. ABI 89 adds hammock and weight bench through one
single-bed category and the existing native controls, without new gameplay code.
Catalogue framing uses
donor-table records for all installed furniture, replacing per-item overrides.
Thirty-five focused pipeline/composition checks pass; one optional prepared-assets
check is not requested. The first current native run passes, including bed
positioning in all four rotations. The full source/verification record is in
[the checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md). The composer has 87
installed development options; neither patcher changes.

Extend shared categories instead of writing another per-item/family installer.
The constant identity-indexed model/palette category prepares all nine flower
variants in one command, retaining their full 19,152 bytes, 555 vertices, and 288
triangles. They are not installed: the shared `ftr_listEventPresentChumon`
acquisition/catalogue route must cover those flowers, two tree models, and weed
model together. Actual source tracing identifies Tortimer's Groundhog Day,
Founder's Day, Cherry Blossom Festival, and Nature Day gifts. The N64 lacks that
actor; the shared event/calendar/conversation and per-player trophy route needs
implementation. Prepared-only output cannot pass the installer. Keep that shared
dependency explicit and continue graphics/contact/callback categories instead of
blocking bulk imports on it. Useful callback groups include fifteen clocked
station models, eight palette-animated
buildings, and tool/fan/pinwheel selectors; preserve their actual effects.
Beach chair and harvest bed pass shared bed/model discovery, but retain
their island and harvest acquisition dependencies instead of substitute shop stock.
Sixteen diary display models still need diary identity/gameplay/acquisition.
Complete model conversion without required behaviour is not a completed import.
Full catalogue construction, ordinary GPU appearance, interactions, and
save/restart remain for the gameplay pass. Saved format 2 is unchanged, but saves
using the two ABI-89 additions must not be loaded in older builds or V2.

Current integration:
`build/v3-furniture-bed-runtime-02/animal-forest-v3-asset-loader.z64`, pinned
by `config/v3-import-build.json` for both the pipeline and offline composer.

The [school desks](checkpoints/V3_SCHOOL_DESKS.md) are installed in ABI 84 with
complete artwork, native metadata/readers, stock, catalogue/scoring, profile
bits, and official text attribution. Twenty cartridge/composition tests and the
first 88-record native run pass, including all rotated footprints, actual model
DMA, stock membership, catalogue eligibility, acquisition, and saved ownership.
Ordinary sitting, appearance, and save/restart remain for the gameplay pass.
Continue shared import categories and remaining native readers; do not
replay passed unchanged paths. The current shared sound reader covers the desks;
ordinary sitting remains unverified. Both patchers stay V2.

The desk prerequisite image is
`build/v3-school-desks-runtime-01/animal-forest-v3-asset-loader.z64`; the
[lamp checkpoint](checkpoints/V3_TENT_LAMP.md) records ABI-83 complete native
creation, dawn/dusk movement, drawing, environment updates, and cleanup.
Floor-sound routing, selected rewards, and full-ID pocket selection retain
their passing evidence. Continue remaining masked readers and ordinary camper construction/
conversations. Maintain text credits
in the single `translations/provenance.json` catalogue; its own coverage queue
tracks the remaining attribution work without a duplicate review list.

The [ordinary summer-town check](checkpoints/V3_CAMPSITE_GAMEPLAY.md) passes
cold boot and natural event/tent placement. Both bounded navigation approaches
stop at the river without reaching the tent; do not repeat this navigation
batch. Actor construction, scene entry, conversations, rewards, and persistence
remain unverified. Continue native-reader and donor-content implementation.
Private captures also show `0:05 pm` around noon; inspect the clock formatter
in a later concrete rendering fix. No patcher update is authorised by that finding.

The [V3 specification](../specs/V3_OPTIONAL_IMPORTS.md) governs new work on
`v3/optional-imports`. The goal is additive, optional villager/item content from
GAFE01 revision 0, selected individually or together in the browser patcher,
with later e/e+ donor support investigated separately.

- [x] Establish source-verified donor inventory, identities, scope, and save policy.
  [Foundation evidence](checkpoints/V3_IMPORT_FOUNDATION.md): six tests and actual
  donor extraction pass; 20 donor-only villager identities are identified.
- [ ] Trace ordinary donor-only villager assets and implement one complete pilot
  through rendering, text, house/move-in, conversations, and saved identity.
  [Punchy/Cheri artwork conversion](checkpoints/V3_VILLAGER_ART.md) and shared
  model/skeleton checks are complete. The [additive asset loader](checkpoints/V3_ASSET_LOADER.md)
  and native object-DMA checks pass for both texture banks, with all original
  banks preserved. The [native draw adapter](checkpoints/V3_NPC_DRAW.md) installs
  both overlay routes and full voice-ID transport. Seven host/cartridge checks
  pass; cold boot passes after an alignment fix. The
  [audio batch](checkpoints/V3_VILLAGER_AUDIO.md) installs both donor melodies and
  widened audio paths, verifies shared instrument/sample data, and passes five
  focused checks plus combined native audio and both-overlay draw/tail probing.
  The [text batch](checkpoints/V3_VILLAGER_TEXT.md) adds shared full-name/phrase
  readers, six-byte compatibility names, default reset, and borrowable V3 phrase
  references. Five focused tests and the combined native reader/insertion/reset
  check pass. The [initial-default batch](checkpoints/V3_VILLAGER_DEFAULTS.md)
  connects Cheri's verified starting outfit/defaults and both personalities;
  six focused checks and native initialization/clothing-DMA checks pass.
  The [house batch](checkpoints/V3_VILLAGER_HOUSES.md) installs Cheri's complete
  mapped house layers, existing matching room surfaces, and K.K. Samba, retaining
  every original house. Five focused tests and the corrected current 42-step
  native house check pass, including complete initialization, appended DMA,
  sparse pointers, both layer transfers, and guards. Ordinary house visits
  remain unverified; move-ins stay disabled.
  The [secondary readers](checkpoints/V3_VILLAGER_READERS.md) connect map,
  inventory, letter/address, conversation identity, and generated-letter names.
  Six focused checks and the corrected 101-step native check pass, including
  both generated-name/alias entries, four complete display paths, and guards.
  The [town-selection adapter](checkpoints/V3_VILLAGER_SELECTION.md) connects
  unseen counts, history reset, initial population, and subsequent move-ins
  with independent candidate/shuffle storage. Six focused checks and all four
  native entries pass, including two complete starting populations and Cheri's
  fixed ID under a temporary test flag. Default import eligibility remains off.
  The [house-gift adapter](checkpoints/V3_VILLAGER_REWARDS.md) includes imported
  furniture in native reward selection. Four focused tests and the initial
  45-step native run pass, including both actual-room barrel gifts through
  complete selection, list storage, and identity-based retrieval.
  The [umbrella review](../specs/V3_VILLAGER_UMBRELLAS.md) confirms both installed
  defaults, native consumers, and full donor/native artwork correspondence.
  Two focused checks pass without changing the cartridge.
  The [ordinary Cheri gameplay check](checkpoints/V3_CHERI_GAMEPLAY.md) fixes the
  separate NPC streaming-table readers in both overlays. Three focused checks
  and a twenty-one-step current cold-boot/gameplay run pass: acre crossing,
  ordinary Cheri construction/movement, and her English introduction with the
  correct name, outfit, and catchphrase. The town seeds Cheri explicitly;
  natural move-in and ordinary save/restart remain unverified.
  Next: remaining native reader review and ordinary gameplay/
  save integration. Punchy's complete variant uses the additive cherry-shirt
  import, never the different native shirt with the same item number.
  The [clothing resource foundation](checkpoints/V3_CLOTHING.md) installs the
  actual new shirt and shared indexed reader. Four focused checks and the
  initial thirty-four-step native test pass. The
  [NPC clothing adapter](checkpoints/V3_NPC_CLOTHING.md) connects both owners'
  full shirt-ID checks and foreground/queued loaders. Four focused checks and
  the first native foreground loop pass; queued completion and the second
  owner remain unverified after bounded setup attempts. The
  [player clothing adapter](checkpoints/V3_PLAYER_CLOTHING.md) connects startup
  and clothes-changing resources. Three focused tests and the initial 47-step
  native double-buffer/registration/guard run pass. The
  [clothing save extension](checkpoints/V3_CLOTHING_SAVE.md) installs independent
  selected/owned clothing records and format-1 migration. Five focused checks,
  four current non-clothing codec host checks, and the corrected 52-step native
  run pass. The [shared clothing item readers](checkpoints/V3_CLOTHING_ITEMS.md)
  connect the full English name, native category, and donor price. Current host/
  cartridge checks and the corrected 60-record native run pass, including
  original/furniture retention and missing-profile rejection. The
  [clothing collection adapter](checkpoints/V3_CLOTHING_COLLECTION.md) connects
  actual pocket acquisition to per-player saved ownership. Focused checks and
  the initial 62-record native run pass, including present/quest timing,
  separate clothing/furniture bits, player clearing, and guards. The
  [clothing menu routing](checkpoints/V3_CLOTHING_MENU.md) connects classification
  and three extra hand/cursor/animation decisions. Host/cartridge checks and the
  initial 62-record native run pass, covering six full-register windows and
  complete eligibility/destination/action functions. The
  [player animation fix](checkpoints/V3_CLOTHING_WEAR.md) preserves full imported
  shirt indices at the texture-change frame. Host/cartridge checks and the
  initial 33-record native instruction-window run pass. Ordinary copied-town
  cold boot, inventory, grab/wear, and outdoor rendering pass, retaining full
  imported clothing identity and returning the original shirt to its pocket.
  Actual gyroid Save & Quit and fresh-process reload pass, restoring clothing,
  pockets, ownership, and complete active artwork. Next connect remaining
  renderer/shop consumers and dropped/displayed garment gameplay; retain the
  missing NPC queued evidence for combined gameplay. Punchy's complete variant
  connects his actual outfit through the checked shared reader.
  The [shop category reader](checkpoints/V3_CLOTHING_SHOPS.md) recognises selected
  clothing with retained original/furniture handling. Two focused tests and the
  initial 23-record native run pass. The
  [stock adapter](checkpoints/V3_CLOTHING_STOCK.md) installs selected cherry shirt
  in A's all-season list. Two focused tests and the initial 65-record native
  run pass, including seven stock choices, six town-rarity queries, actual
  full-ID acquisition, independent ownership, restored state, and guards.
  The [shop mannequin adapter](checkpoints/V3_SHOP_MANNEQUIN.md) connects all six
  count/search decisions. Its cartridge check and corrected 56-record native
  run pass, including full original/imported/disabled/sold counting and search,
  both complete texture-loading loops, native relocation, and guards.
  The [clothing shop-floor adapter](checkpoints/V3_CLOTHING_SHOP_FLOOR.md)
  connects the three separate placement/selection/sale decisions. Its cartridge
  check and initial 61-record native run pass, including full sale reporting,
  actual bare-mannequin callback, foreground clearing, exact sales-total update,
  retained other stock, and guards. The [ordinary-shop check](checkpoints/V3_CLOTHING_SHOP_GAMEPLAY.md)
  retains imported stock through cold boot without pre-awarding ownership.
  Purchase remains unverified after two unsuccessful door approaches; stop
  navigation retries for this batch and continue catalogue/home representation.
  The [expanded furniture tables](checkpoints/V3_FURNITURE_TABLES.md) raise
  transient capacity to 2,051 without native heap or save growth. Two focused
  tests and the initial 91-record native run pass, including both imported
  models, original allocation/loading, full cleanup, and new guards. The
  [clothing display adapter](checkpoints/V3_CLOTHING_DISPLAY.md) installs stable
  mannequin identity `3AFC`, the original native callbacks/model, and selected
  full-index clothing loading within existing buffers. Three focused checks
  and the corrected 116-record native run pass, including all four rotations,
  complete transfers, draw commands, cleanup, and guards. The
  [display readers](checkpoints/V3_DISPLAY_ITEM_READERS.md) connect canonical
  names/prices, placed category, native footprint, and clothing ownership.
  Both scoring tables contain 2,051 verified rows within existing limits.
  Two focused checks and complete native item-reader/collection exercises pass.
  The [global conversion batch](checkpoints/V3_DISPLAY_CONVERSION.md) connects
  the pocket/mannequin identities and preserves all native conversion bodies.
  Two focused checks and the initial 157-step native run pass, including the
  full HRA/feng shui scoring tail, four orientations, and guards.
  The initial 22-record ordinary run passes copied-town cold boot, house entry,
  Drop, mannequin bank allocation, and B pickup retaining full `34BF` and
  releasing the bank. Other pockets, clothing, and guards stay intact; the
  garment is fixture-seeded, not purchased. The
  [clothing catalogue](checkpoints/V3_CLOTHING_CATALOGUE.md) installs the owned
  shirt after all 245 native entries, retaining their original order. Two
  focused checks and the initial 71-step native run pass: complete lists/names,
  selection, actual artwork/model loading, price/presentation, missing-dependency
  exclusion, restored state, and guards. The menu fits its existing reservation
  with 384 bytes spare. The
  [placed-clothing persistence check](checkpoints/V3_DISPLAY_PERSISTENCE.md)
  establishes ordinary Save & Quit, both complete independently validated save
  banks, fresh-process room/ownership restoration, and B pickup with the correct
  full identity and model-bank release. Its final scenario expectation is
  corrected to the observed intact save guard; the subsequent unexecuted tail
  is not claimed passed. Rotation remains unverified after the bounded two
  approaches. Next: remaining villager integration and Punchy's animated speed
  bag; retain ordinary rotation and transactions for the combined gameplay pass.
  The display profile bit means older profiles
  reject new saves; preserve backups and distinguish the passing codec check
  from untested ordinary cross-build loading.
  Ordinary catalogue ordering/payment and buy/sell remain. The separate outdoor
  Drop checkpoint is retained with pickup unverified after movement overshoots;
  do not confuse that pending outdoor case with the passing home pickup.
- [ ] Review native/donor item identities and implement one complete simple
  furniture pilot through acquisition, inventory, placement, and persistence.
  The [static furniture batch](checkpoints/V3_FURNITURE_ART.md) converts both
  haz-mat barrel and oil drum models/textures for Cheri's house and passes seven
  focused checks. The [native loader batch](checkpoints/V3_FURNITURE_RUNTIME.md)
  installs stable IDs, resident profiles, expanded readers, and native model-bank
  selection/reuse/release. Five focused checks and 86 native steps pass, including
  original furniture allocation/DMA and cleanup. The
  [shared item readers](checkpoints/V3_FURNITURE_ITEMS.md) add complete names,
  item category, donor price values, and placement footprints; four focused
  tests and 73 native steps pass. The
  [room integration](checkpoints/V3_FURNITURE_ROOM.md) connects 21 upper bounds,
  two index conversions, and four local field-type scans; four focused checks
  and 151 native steps pass. The
  [shared field-grid batch](checkpoints/V3_FURNITURE_FIELDS.md) connects both native
  room-grid builders and shop eligibility; four focused checks and 56 native
  steps pass. The [menu batch](checkpoints/V3_FURNITURE_MENU.md) connects action
  menus, held-item destinations, and room-placement dispatch; three focused
  checks and 77 native steps pass. The [inventory icon batch](checkpoints/V3_FURNITURE_ICON.md)
  connects the independent leaf reader; three focused checks and 59 native steps
  pass, including full native drawing-command comparisons. The
  [ground-item batch](checkpoints/V3_FURNITURE_GROUND.md) connects both drop-flag
  paths and ground-descriptor selection; three focused checks and 57 native steps
  pass. The [pocket-search batch](checkpoints/V3_FURNITURE_POCKETS.md) connects both
  shared furniture queries; four focused checks and 51 native steps pass.
  The [collection adapter](checkpoints/V3_COLLECTION.md) connects native
  acquisition/collection and resident clearing to saved imported ownership.
  Four focused tests, a 177-step native collection/two-bank save check, and a
  54-step fresh-process load pass.
  The [catalogue adapter](checkpoints/V3_CATALOGUE.md) adds collected rows, complete
  names, both model previews, selection, prices, and completion. Four focused
  tests and 70 native steps pass, including all 438 rows and original fallback
  within the existing menu allocation.
  The [shop adapter](checkpoints/V3_SHOPS.md) adds native ordinary-stock lists
  and category queries without changing town rarity/RNG. Four focused tests
  pass, along with native stock selection and pocket acquisition. The
  [shop interaction adapter](checkpoints/V3_SHOP_INTERACTIONS.md) connects twenty
  furniture decisions across all five actors. Three focused tests and 148 native
  steps pass, including complete deliveries/readbacks for both imports and
  pending-order clearing; the earlier delivery-tail uncertainty is closed.
  The [shop-floor adapter](checkpoints/V3_SHOP_FLOOR.md) connects reserve points,
  item selection, and sold-removal classification. Three focused tests and 63
  native steps pass, including native complete reserve/grid selection and
  retained branch-delay entry paths.
  The [HRA adapter](checkpoints/V3_HRA.md) adds actual donor properties, all range/
  index consumers, native theme grouping, and correct missing-item IDs. Three
  focused checks pass, with 86 native register windows and a corrected 46-step
  scoring tail covering groups, recommendations, points, and boundary safety.
  The [feng shui adapter](checkpoints/V3_FENG_SHUI.md) connects actual donor
  colours and retains native balance. Three focused checks and the first
  45-step native run pass, including eight complete item/room evaluations.
  The [ordinary lifecycle batch](checkpoints/V3_ITEM_LIFECYCLE.md) fixes the
  room-drop index and three inlined inverse-ID conversions. The current barrel
  now places with its correct model and returns to its pocket with the correct
  imported ID through normal B pickup. Seven host checks and 25 changed native
  instruction windows pass across the two fixes; original items remain intact.
  Next: ordinary acquisition/payment, rotation/persistence, and the remaining
  villager integration. No complete item is enabled yet.
  The [speed-bag asset converter](checkpoints/V3_SPEED_BAG_ART.md) supplies the
  complete two-part model, all eight textures, and the two-joint/three-track
  animation in 3,728 bytes. Six focused checks and five retained static-parser
  host checks pass. The [callback batch](checkpoints/V3_SPEED_BAG_CALLBACKS.md)
  implements all three native callbacks, with five focused checks and the
  corrected 103-record native run passing actual interpolation, first hit,
  retrigger/stop timing, sound eligibility, and drawing in both matrix banks.
  The full donor hit sound is converted with five passing audio checks.
  The [sound installer](checkpoints/V3_SPEED_BAG_SOUND.md) adds the actual
  sequence/font/wave data without replacing native resources or enlarging the
  audio heap. Four focused checks and the corrected build's first 58-step native
  run pass, including real trigger/retrigger and completed sample transfers.
  The native envelope-alignment defect is fixed; PCM/listening remains unverified.
  The [animated runtime installation](checkpoints/V3_SPEED_BAG_RUNTIME.md) adds
  the production callbacks, positional sound, profile/model loading, fixed
  item/index, and English metadata. Four focused checks and the corrected
  204-step native run pass, including installed construction/hit/positional
  sound, model loading, English metadata, retention, and cleanup. Storage now uses
  a checked two-MiB VROM interval without RAM growth or directory-index changes.
  The [boxing HRA adapter](checkpoints/V3_SPEED_BAG_HRA.md) expands native series
  storage to 59 entries with the actual donor series 58 and unchanged scoring
  formulas. Four focused checks and the first 68-record native run pass,
  including all four scoring loops, real group/point data, disabled-item
  rejection, original storage retention, and guards. The
  [gameplay connections](checkpoints/V3_SPEED_BAG_GAMEPLAY.md) add complete boxing
  score letters, catalogue/group-A acquisition, actual neutral feng shui data,
  and the selected save dependency. The combined 149-record native run passes
  stock selection, pocket ownership, four complete letters/readbacks, all 439
  catalogue rows, and animated preview construction. The item is enabled in
  the private build; its seven host checks and 12-record cold-boot check pass.
  Neither web patcher exposes V3 options.
  The [Punchy house/default batch](checkpoints/V3_PUNCHY_HOUSE.md) installs his
  room and actual starting shirt, relocates the complete foreground without
  overwriting adjacent files, and passes all seven focused checks. The complete
  native arithmetic block produces 436 records without the internal breakpoint;
  preserve the separate failed window diagnostics and their recorded limits.
  Native defaults pass 81 records / 44 assertions, and the native house tail
  passes 48 records / 29 assertions across all four imported layers. The
  [ordinary Punchy check](checkpoints/V3_PUNCHY_GAMEPLAY.md) loads his full
  identity/outfit and actor through copied-town cold boot and acre crossing.
  House entry remains unverified after bounded approaches; do not repeat that
  navigation batch. Keep move-ins disabled. Continue remaining donor conversion
  and speed-bag interaction/persistence work; complete ordinary house/move-in
  and villager persistence remain required for a playable handoff.
  GPU/hardware acceptance, ordinary purchase, and villager persistence remain open.
- [ ] Expand native tables/readers safely and assign subset-independent IDs.
  Object-bank slots 410–429 are assigned by verified English-donor index;
  registry version 1 reserves villager actor indices 218–237, preserving native
  tests and special characters. Furniture registry version 1 assigns the two
  reviewed static pilots; saved-identity/shared item readers remain work.
  Preserve special-character draw records; do not truncate the GC draw record
  or voice IDs into the smaller native fields.
- [ ] Batch remaining English-donor villagers/items and their actual behaviours;
  adapt islanders explicitly instead of pretending the island engine is present.
  The [camping integration](checkpoints/V3_CAMPING_ITEMS.md) installs seven complete
  static models and their English names/prices, one/two-cell profiles, catalogue
  framing and non-orderability, HRA/feng shui, and selected dependencies in ABI 68.
  Twenty-nine focused checks pass. The initial native run passes 28 calls and
  37 memory assertions, including all seven loaded profiles and item readers.
  No additional resident RAM is needed. The [three callback-owned camping assets](checkpoints/V3_CAMPING_ACTORS.md)
  are converted completely, and the bonfire's true four-cell item reader compiles
  within the existing reservation. Twenty-one focused checks pass. The
  [tent runtime](checkpoints/V3_TENT_MODEL_RUNTIME.md) installs complete callbacks,
  English metadata, non-orderable catalogue entry, scoring, and saved dependency
  in ABI 69. Seventeen focused tests and the first native run pass, including
  17 calls, 48 assertions, independent fades, complete draw commands, palette
  lifetime, item readers, and guards. Fifty-seven options compose offline;
  all/empty retain exact full/V2 outputs. The
  [tent DMA repair](checkpoints/V3_TENT_MODEL_LOADER.md) admits only the reviewed
  tent identity/vtable through the complete-object loader. Fifteen focused tests
  and the initial native 36-record run pass actual model DMA, rotated bank reuse,
  rejection, and restoration. Content, ABI, saves, and allocations stay unchanged.
  The [fire-audio converter](checkpoints/V3_FIRE_AUDIO.md) retains both complete
  two-layer programs, appends their actual samples/instruments, and preserves
  current native/speed-bag resources. Seven checks pass. The
  [sound runtime](checkpoints/V3_FIRE_SOUND_RUNTIME.md) installs both loop IDs
  with a coordinated 1-KiB allocation increase and safe whole-wave relocation.
  Five cartridge checks, twelve current composition checks, and the initial
  74-record native run pass actual allocation, complete font/header relocation,
  both new samples, start/stop, restoration, and guards. Permanent capacity has
  256 bytes spare; session/cache capacity is unchanged. The
  [complete fire runtime](checkpoints/V3_FIRE_RUNTIME.md) installs both full
  rig/billboard/scroll and positional sound callbacks, item profiles/readers,
  English metadata, four-cell bonfire, catalogue/scoring, and saved dependencies
  in ABI 70. Twenty-one focused checks pass; the current initial native run
  passes 110 records, 24 calls, and 90 assertions, including real model DMA,
  actual rig/draw execution, unaligned arenas, item readers, and guards.
  Fifty-nine options compose offline; all/empty retain exact full/V2 output.
  Continue summer-camper acquisition, then
  other donor content and ordinary gameplay/persistence. The ten installed Tent
  rewards do not enter normal shop stock. Neither served patcher changes.
  The collectible lantern and sleeping bag retain the donor's null callbacks
  and contact/interaction flags. The animated lantern is a separate scene
  effect; do not invent lighting or sleep interactions for these furniture items.
  The [complete campsite scenery](checkpoints/V3_CAMPSITE_ART.md) supplies native
  exterior, projected shadow, interior, and scene-lantern assets with all source
  geometry/materials retained. Five focused checks pass. The 19,872-byte interior
  uses scene storage, not a furniture bank. The
  [scene-loader integration](checkpoints/V3_CAMPSITE_SCENE.md) installs all four
  assets, native scene 35, the complete 36-record field directory, collision,
  exits, and camper placement in ABI 71. Fifteen focused/composition checks and
  the corrected 57-record native run pass, including complete field construction,
  actual interior DMA, relocated gameplay code, cleanup, and guards. Resident
  RAM adds 8 KiB without normal heap or model-bank growth. The scene checkpoint is
  `build/v3-campsite-runtime-03/`; its ten-item subset is
  `build/v3-optional-campsite-01/`. Both served patchers remain V2.
  The [additive exterior](checkpoints/V3_CAMPSITE_EXTERIOR.md) installs the complete
  tent callbacks and loader binding in ABI 72 without more permanent RAM. The
  actor retains the fixed native pool stride and owns 7,776 bytes of full artwork
  and guard storage. Sixteen focused/composition tests pass. Actual controller
  relocation, setup registration, descriptor selection, and pool initialization
  pass; native construction/drawing/cleanup remain unverified after the combined
  probe's field-background allocation bound fails. The failure is unresolved,
  not waived as a fixture problem. The exterior checkpoint build is
  `build/v3-campsite-exterior-runtime-01/`; its camping subset is
  `build/v3-optional-campsite-exterior-01/`. Neither patcher changes.
  The [native calendar](checkpoints/V3_CAMPSITE_CALENDAR.md) installs the event
  index/readers and calendar hooks in ABI 73, preserving native holidays and
  capacity. Fifteen current focused/composition tests and the corrected native
  112-record/63-call/55-assertion check pass. Native weekly-date encoding is
  adapted explicitly. Event-save-area checks use RAM, not FlashRAM persistence.
  The [independent camper](checkpoints/V3_CAMPER.md) supplies the complete visitor
  Animal, optional-roster/default/outfit registration, current-player memory
  reconstruction, and native NPC-info attachment in ABI 74. It uses no town
  slot, extra heap, or model bank. Fifteen current focused/composition checks
  and the corrected 144-record native run pass. Real native/imported defaults,
  English names, masked draw records, alias limits, greeting memory, and complete
  native save/town-list preservation are checked. Full NPC construction and
  ordinary persistence remain unverified. The native memory array is at Animal
  offset `10`, not the inaccurate source comment's `0C`.
  The [event manager](checkpoints/V3_CAMPSITE_MANAGER.md) binds real selection,
  registration, placement/removal, and retries, retaining all original events
  and the current English letter owner. Its 79-record native check passes.
  The [move-in guard](checkpoints/V3_CAMPER_MOVEIN.md) excludes the saved camper
  from both native growth and inbound transfers; its 48-record native check passes.
  The [NPC/quest adapter](checkpoints/V3_CAMPER_QUEST.md) binds both camper-profile
  readers and first/repeat quest state. Seventeen focused/composition checks and
  the corrected 68-record/55-assertion native instruction-window check pass.
  Full NPC construction remains unverified. The [summer text adapter](checkpoints/V3_CAMPER_TEXT.md)
  appends all 253 messages and 49 choices, retaining the original English banks,
  complete wording/timing, stable branches, and equivalent native trade operations.
  Seventeen focused/composition checks pass. Its corrected native loader and
  continuation check passes 74 records, 23 calls, and 54 assertions; ordinary
  conversation/reward execution is not established.
  The [summer greeting adapter](checkpoints/V3_CAMPER_GREETING.md) installs first/
  repeat selection, donor item/Bell conditions, and transient last-gift tracking.
  Seventeen current focused/composition checks pass; native full-owner loads,
  six personalities and nineteen repeat/eligibility cases pass. The later
  dispatch-window stop times out with the expected message in return registers.
  That intermediate stop remains unexplained. The [trade adapter](checkpoints/V3_CAMPER_TRADE.md)
  passes the complete unchanged greeting initializer/return in the current ROM,
  both native gift/reset hooks, restoration, and final guards. It installs actual
  full-ID pocket selection, last-gift exclusion, and profile-filtered camping
  rewards, preserving donor probabilities, small-list duplicate rules, and later
  carpet/wall fallback. Eighteen focused/composition checks pass. The corrected
  native run passes 55 records and 37 assertions, including three complete trade
  preparation calls and two selected-only camping rewards. Four pocket cases
  pass in the initial run; its bad fixture identity is corrected without a ROM
  change or replaying those cases. Ordinary conversations remain unverified.
  The [environment adapter](checkpoints/V3_CAMPSITE_ENVIRONMENT.md) connects
  actual native player/NPC floor-sound routing and donor room-light parameters.
  Eighteen focused/composition checks pass; the corrected native run passes
  39 records and 29 assertions. The [timed lamp](checkpoints/V3_TENT_LAMP.md)
  installs the full lifecycle, donor model fade, point/diffuse/room colours,
  and cleanup without permanent memory growth. Nineteen focused/composition
  tests pass; the first native run completes 65 records and 36 assertions,
  including all four callbacks and the complete native environment update.
  Current full build: `build/v3-tent-lamp-runtime-02/`; camping subset:
  `build/v3-optional-tent-lamp-01/`. Both patchers remain V2.
  Continue remaining masked readers, ordinary NPC construction, conversation
  handover, and ordinary scene lighting as specified in
  [V3_CAMPSITE](../specs/V3_CAMPSITE.md). Natural entry, reward handover, GPU
  appearance, and persistence are not yet verified.
  Current catalogue suffix headroom is 160 bytes; the menu pool has 256 bytes
  spare. The furniture helper has 220 bytes spare. Further content must respect
  those bounds or expand the relevant allocation before installation.
  The [expanded import storage](checkpoints/V3_IMPORT_STORAGE.md) preserves the
  full 3,389-entry DMA directory and relocates the unchanged English choice bank.
  ABI 67 provides 1,847,280 bytes of free import storage and fixed
  metadata slots, with 114,704 more resident bytes and no ordinary heap growth.
  The corrected preflight and first actual native run pass 84 records, including
  all installed static pointers, shared readers, relocated choices, and guards.
  Camping uses a checked scoring-only mapping from category 37 to the native
  equivalent 412-point weight; its actual reward route remains a separate task.
  The [full-sized Western integration](checkpoints/V3_WESTERN_LARGE_ITEMS.md)
  installs the remaining three Western furnishings, bringing the theme to ten
  complete models with true two-cell footprints and explicit catalogue framing.
  ABI 66 relocates/expands the checked package by 8 KiB while preserving save
  code, public item entries, and existing menu/model allocations. Twenty-eight
  focused checks and the first 88-record native run pass. Forty-nine options
  compose individually; all/empty retain exact full/V2 outputs. Expanded import
  storage supplies the headroom and canonical metadata slots for further batches.
  Continue ordinary placement/rendering/acquisition/persistence, mailbox
  behaviours, and remaining villagers/items. Neither served patcher changes.
  The [Western runtime](checkpoints/V3_WESTERN_RUNTIME.md) installs seven complete
  models, English readers, true stock/catalogue/scoring, and saved dependencies
  in ABI 65. Dedicated 9,216-byte Expansion Pak banks fit the saddle fence without
  ordinary heap growth. Fifteen focused checks pass, and the offline composer
  contains 46 options. Native readers, event selection/ownership, catalogue rules,
  and Western scoring pass. Native 100-bank allocation is established, but two
  fixture mistakes exhaust this batch's setup attempts. Both are classified and
  corrected; paired model DMA, executed teardown, and the final restore tail remain
  unverified. Do not repeat that setup batch. Continue donor families and ordinary
  gameplay; retain the bank tail for a later meaningful integration check.
  Retain full catalogue/menu allocation checks before further additions. Both event rewards
  keep their actual route. No web update.
  The [construction batch](checkpoints/V3_CONSTRUCTION_ITEMS.md) converts seven
  complete static models and verifies names/prices, 1×1 profiles, ordinary B/C
  stock membership, and native scoring metadata. Five new asset checks, seven
  shared converter checks, and four metadata/table checks pass. All seven models
  fit existing banks; 28 construction-theme items fit the 32-bit completion mask.
  The [runtime batch](checkpoints/V3_CONSTRUCTION_RUNTIME.md) installs all seven
  complete objects, fixed profiles, shared item readers, and saved-profile bits.
  Four focused checks and the first 145-record native run pass, including all
  seven names/prices, two model banks, original fallback, cleanup, and guards.
  The [catalogue integration](checkpoints/V3_CONSTRUCTION_CATALOGUE.md) installs
  the 446-row furniture table in actual 753-slot pages, retaining all 248 clothing
  rows, full names, and preview buffers. It installs verified B/C stock and scoring
  metadata. Four focused tests, 103 native catalogue records, and 36 native stock/
  pocket-acquisition records pass. Its menu reservation grows by 6,144 bytes;
  the Expansion Pak requirement and 64-MiB cartridge size remain unchanged.
  The [33-entry optional composer](checkpoints/V3_OPTIONAL_CONSTRUCTION.md)
  connects package-resident enable words and both CRCs, with selected catalogue
  packing and iteration/completion counts. Seven focused checks and the first
  122-record native subset check pass, including non-prefix item/shirt choices.
  The [aloha scoring correction](checkpoints/V3_ALOHA_SCORING.md) installs both
  actual clothing records. Three focused checks and the corrected 52-record
  native run pass, including complete grouping/points and end guards. Seven
  composer checks pass against that source without another menu replay.
  Ordinary acquisition/placement/persistence remain incomplete; neither web
  patcher changes.
  The [six-item garden batch](checkpoints/V3_GARDEN_ITEMS.md) converts complete
  artwork and verifies names, prices, real acquisition lists, and scoring flags.
  Six new focused checks and ten shared parser/profile checks pass. The
  [garden runtime](checkpoints/V3_GARDEN_RUNTIME.md) installs all six complete
  profiles/models, shared readers, backyard series/name, ordinary/lottery stock,
  complete catalogue/scoring, saved dependencies, and individual composition.
  Four focused integration checks and the initial 187-record native run pass;
  nine composer checks pass across 39 options. The gnome reaches actual native
  lottery selection and pocket ownership. Unselected furniture is excluded from
  HRA theme counts/recommendations. Next: faithful post-office reward delivery,
  ordinary acquisition/placement/persistence, and the remaining donor families.
  The local two-item subset's initial 35-record native scoring check passes:
  one selected backyard member, no unselected boxing members, complete counters,
  actual reward points, saved-state restoration, and guards.
  The [reward-source review](checkpoints/V3_POST_OFFICE_REWARD_REVIEW.md) binds
  mailbox template `0248`, balance 100,000,000, flag `10`, and successful-mail-only
  acknowledgement. Establish actual native account/save equivalents before
  adapting this route; donor private-data offsets are not native fields.
  The original/current Pelly status function and native submenu set lack the
  donor banking route. Faithful delivery requires deposit/withdrawal, preserved
  loan payment/account eligibility, and reviewed per-player balance/reward
  persistence; do not substitute lifetime earnings or reuse unknown fields.
  The [reward-category adapter](checkpoints/V3_HRA_BIRTH.md)
  supplies safe counters and weights through category 22. Three focused checks
  and the initial 82-record native run pass. Require this ABI-63 prerequisite
  before mailbox scoring; its reward acquisition remains uninstalled.
  [Pigleg/Dobie artwork](checkpoints/V3_ISLANDER_ART.md) converts both complete
  texture formats and Pigleg's separate donor-coordinate model. Thirteen focused
  tests pass with unchanged pilot outputs. Connect stable model/texture banks,
  voices, text/defaults/houses, and town behaviour before move-in eligibility.
  The [accessory batch](checkpoints/V3_ACCESSORY_ART.md) supplies all sixteen
  complete accessory models with actual consumer/joint bindings; fifteen
  focused checks pass. The [complete body bundle](checkpoints/V3_GORILLA_ART.md)
  converts twenty villagers with all sixteen required accessory objects,
  complete expressions, verified edge extensions, and verified mesh/joint bindings.
  Yodel's complete donor model fits the native buffer with 128 bytes spare;
  26 focused checks pass. Retain all complete accessory objects and source-bound
  conversion checks.
  Use Yodel's converted skeleton at `06002770`, not the native gorilla pointer.
  The [complete-asset loader](checkpoints/V3_COMPLETE_VILLAGER_ASSETS.md) assigns
  all 38 objects to fixed banks 410–447 and moves growth permissions to
  `80461E80`. Seven focused tests and the 93-record / 59-assertion native run
  pass, including real object DMA, both custom models, accessories, bank bounds,
  and both starting populations. All original banks/audio locations remain;
  move-in flags stay off. The
  [attachment runtime](checkpoints/V3_ACCESSORY_RUNTIME.md) installs all twenty
  draw records and attaches all sixteen accessories in both owners, with shared
  storage and frame-local matrices. Seven focused tests pass; partial native
  execution verifies head/torso transforms, commands, fallback, and buffer limits.
  The complete audio batch closes the final accessory null/guard tail with
  37 passing assertions, without replaying the passing transform cases.
  Continue text/defaults, houses, town behaviour, ordinary appearance, and persistence
  before enabling new town inhabitants.
  The [complete audio bundle](checkpoints/V3_COMPLETE_VILLAGER_AUDIO.md) supplies
  all twenty melodies and four additional instruments, with all 83 native
  instruments retained. The [complete audio runtime](checkpoints/V3_COMPLETE_AUDIO_RUNTIME.md)
  installs the source table/storage and expanded bank/wave resources in ABI 53.
  Fourteen focused tests pass, as do native startup, complete font relocation,
  physical headers, melody copies, full-ID handling, and allocation bounds.
  New-instrument sample playback and final post-audio guards remain unresolved
  after two bounded attempts. Do not start a third setup attempt in this batch
  or classify the missing playback evidence as a proven fixture problem.
  Continue full text/defaults, houses, and town behaviour. In the next meaningful
  combined native check, inspect note-layer progress and actual sample requests
  without replaying the passing font/attachment checks. Move-in flags stay off.
  The [complete text installation](checkpoints/V3_COMPLETE_VILLAGER_TEXT.md)
  supplies all twenty names, catchphrases, personality values, and source-default
  references in ABI 54. Six focused checks and the initial 168-record /
  90-assertion native run pass, including full-length dialogue insertion,
  borrowed phrases, aliases, profile loading, retained save state, and guards.
  The [aloha outfit runtime](checkpoints/V3_ALOHA_OUTFITS.md) installs both actual
  garments, all eighteen applied outfits, checked shared readers, and independent
  saved clothing dependencies. Seven focused checks and the corrected native
  run's 109 records / 55 assertions pass. Register-preserving bridges fix the
  confirmed native boot defect; actual selected records supply names and prices.
  The [arrival-house batch](checkpoints/V3_ISLANDER_HOUSES.md) installs all eighteen
  authentic initial rooms, matching native surfaces, and reviewed furnishings.
  Five focused checks and the initial 57-record / 35-assertion native run pass,
  including all forty imported layer transfers into the pointer table and three
  representative full rooms. Ordinary visits and complete scene allocation remain
  unverified. The separate island gift layouts are not imported as initial rooms.
  The [complete town policy](checkpoints/V3_TOWN_RESIDENTS.md) enables all twenty
  fixed identities in the experimental cartridge while preserving donor roles.
  Six focused checks pass, as do native roster counts/exclusions and the corrected
  90-record / 56-assertion resident/schedule tail. Maelle's full native creation,
  both starting populations, six personality schedules, event overrides, and
  guards pass. This is not ordinary elapsed-day arrival or save/restart evidence.
  The [complete garment displays](checkpoints/V3_ALOHA_DISPLAY.md) connect all
  three shirts to fixed display identities, canonical readers, full conversion,
  ownership, and the 248-row clothing catalogue. Six focused tests pass, and the
  first native run passes 120 records / 67 assertions covering complete transfers,
  names/prices, selection, independent dependencies, original retention, and guards.
  No memory allocation grows; the existing menu reservation has 320 bytes spare.
  Actual codec tests accept the preceding profile and reject new-profile saves in
  older builds without writes. Ordinary cross-build reload is not newly verified.
  Next connect faithful aloha acquisition and finish ordinary move-ins, house
  visits, conversations, and persistence. The
  [outdoor-house diagnosis/fix](checkpoints/V3_HOUSE_EXTERIOR.md) identifies an
  actual CPU address fault: unrecognised new houses construct a second player.
  Six instruction changes cover all twenty actual house IDs. Two focused tests
  pass; the corrected native run constructs a real house, retains one player,
  and passes the prior fault point and nine fault/guard assertions. Final entry
  remains incomplete. The [separate marker adapter](checkpoints/V3_HOUSE_MARKERS.md)
  assigns `F200..F213` without moving original buildings, connects the three
  native consumers, and passes three focused cartridge/compiled-code tests.
  The cartridge grows to 64 MiB without additional RAM allocation. Native
  Punchy-house entry, normal-marker restoration, and valid complete interior
  arena allocation pass, with one player and intact guards. His normal English
  conversation and ordinary exit also pass, restoring the outdoor house/marker
  and a valid 69-node arena. Continue ordinary villager persistence; keep the
  new-instrument playback issue open, and do not replay passing catalogue tests.
  The [islander gameplay check](checkpoints/V3_ISLANDER_GAMEPLAY.md) loads Maelle's
  complete house and ordinary away schedule without a room-allocation defect.
  Her outdoor conversation remains unverified after two bounded setup attempts;
  preserve the matching checkpoint and continue independent implementation.
  The no-dialogue sample observation passes final guards but proves no imported
  instrument playback. Do not repeat its navigation prefix.
  Do not replay passing text/default checks. Older builds lacking dependencies reject new saves;
  retain separate test saves and compatibility warnings.
  The other species' mouthless, reordered-expression, larger-body,
  and repeated-edge layouts are implemented; retain their source-bound checks.
- [ ] Implement deterministic optional composition, dependencies, profile
  receipts, and save/profile compatibility handling.
  The [local composer](checkpoints/V3_OPTIONAL_COMPOSITION.md) resolves the
  twenty installed villagers and six logical items into fixed-ID selections,
  required house/outfit dependencies, and complete save profiles. Six focused
  checks pass, including native enable-field changes, exact all/empty outputs,
  selection-order independence, and actual codec subset/superset handling.
  The first 42-record native run passes all nineteen selected/excluded item,
  name, and personality-count returns plus fifteen memory assertions, preserving
  save state and final guards. Local artifact: `build/v3-optional-profile-02/`.
  Browser conversion/composition remains separate and unserved.
  The [save-codec foundation](checkpoints/V3_SAVE_CODEC.md) implements checked
  profiles, payload/extension binding, legacy decoding, and four imported-item
  catalogues. Six focused tests and 76 native steps pass. The
  [FlashRAM runtime](checkpoints/V3_FLASH_RUNTIME.md) now connects actual
  saving/loading, separate state, and an English incompatibility warning.
  Six focused tests, synchronous writing, a 141-step two-bank writer, a
  54-step fresh-process reader, and the cold-boot warning pass. Both native
  load entries preserve imported IDs/catalogue state and the original RAM tail;
  the warning preserves both stored banks. Native collection/clearing now
  populates the saved ownership, and the catalogue menu consumes it. Ordinary
  gameplay persistence and Controller Pak profile transport remain work.
  Include imported default-phrase references borrowed by original villagers;
  checking imported actor IDs alone cannot detect every saved dependency.
- [ ] Add searchable per-entry/category/select-all controls to the web patcher;
  verify actual browser output and the unchanged import-free path.
- [ ] Complete bounded combined checks and provide a V3 hardware-playtest build.
- [ ] Obtain the user's V3 testing feedback and explicit approval before changing
  the web patcher. Continue version-tracking V3 development on GitHub meanwhile.
- [ ] Verify e/e+ editions, inputs, formats, additional identities, and capacity;
  implement donor adapters when their required source data is available.

Keep public/local V2 patchers and the trailer unchanged while V3 is experimental.
Do not maintain the old translation-percentage tool or re-test old builds as
part of this work. No import is complete merely because it has a name record.

## Compact N64 keyboard presentation

The [key-only tray and attached N64-style sections](../specs/KEYBOARD_V2_LAYOUT.md)
are complete in **V2-11**, at `build/v2-keyboard-fit-11/`.
The Cursor shell is eight pixels narrower and four pixels left, with its
contents re-centred. Page/Done and their icons sit four pixels lower inside
a 30-pixel-high shell. Only position/size tables change from V2-10.
R Space and Z Page exchange places, as do the A/B and C-button groups.
Analytic antialiased corners give the grey shells smooth edges without the
bright top stripes. Eight cartridge checks and one ordinary native input and
appearance pass verify the changes; existing memory allocation is retained.
N64 button colours/shapes, animated stick and held-button feedback, complete
editor/input behaviour, and museum/credits fixes remain intact. Only the
visible case-alteration/order combo hints are removed, not their shortcuts.
The [fit checkpoint](checkpoints/KEYBOARD_V2_FIT.md) owns exact evidence
and remaining hardware/other-caller acceptance; no implementation is pending.

## Current V2 corrections

**V2-11** retains the faraway museum recipient label and the credits
drawing-buffer correction. The [focused verification](checkpoints/V2_PERFORMANCE_FIXES.md)
passes on V2-08's unchanged resources, including all sixteen credits pages, sampled
fades, unchanged geometry, and native museum/villager/player identity handling.
The [ordinary K.K. Western performance](checkpoints/KK_ORDINARY_PERFORMANCE.md)
also completes, with no measured frozen interval of at least 0.5 seconds across
the recorded 156-second sequence. No all-song or exhaustive hardware test is
claimed. No save migration is required; do not reopen accepted V1 save tests.

## Publication

The existing development repository contains the complete website and reviewed
patch data. The repository is public; GitHub Pages validates and deploys
main-branch pushes through Actions. Keep the repository
name. The [publication guide](WEB_PORTAL.md) describes the automatic workflow
and matching YouTube description URL. Do not change repository visibility or
edit the released trailer.

## Local browser patcher and map correction

The [portal](WEB_PORTAL.md) is running at **http://127.0.0.1:8073/**, serving
`build/web-portal-06/site`. Browser-only patching of both verified game inputs
produces current V2-11. The [map correction](../specs/MAP_TOWN_SUFFIX_FIX.md)
omits the independent Japanese `むら` image beside the town name without save,
code, allocation, or unrelated-art changes. The released trailer is untouched.
Implementation and focused verification are complete; user portal feedback,
and new hardware findings guide further work.
Do not change repository visibility or publish game inputs.

## Released trailer

The local portal uses the user's YouTube upload `UloFru4K4Q8`, loading only on
Play with sound requested. Its redundant MP4 export is preserved outside the
served folder; the original trailer remains unchanged. The integration and
verification are recorded in [the YouTube checkpoint](checkpoints/PORTAL_YOUTUBE.md).

The [YouTube upload resources](promotion/YOUTUBE.md) include a revised thumbnail,
a suggested title, unlisted/release descriptions, and an optional pinned comment.
The thumbnail uses flat, regular lettering and the retained green background;
handoffs contain one upload image, and the user accepts the revision. The user's
YouTube upload is linked in the portal. Release copy includes the patcher address,
`https://thediscordian.github.io/doubutsu-no-mori-english/`.
This resource work does not edit the trailer.

The [released trailer](checkpoints/TRAILER_TOWN_REVISION.md) is preserved at
`build/trailer-cut-05/Animal Forest English - Trailer.mp4` and visually reviewed.
It uses the native opening music, one name-entry keyboard sequence, translated
storefronts and interiors, and the map, catalogue, loan, inventory, and notice-board
screens. Opening and closing identifiers are the only added captions. Production checks and
full decode pass. The user has released the video; do not edit or re-render it.
No further trailer production is queued, and no physical audio playback occurs.
The [V2 hardware feedback batch](checkpoints/KEYBOARD_V2_FEEDBACK.md) is
implemented in `build/v2-keyboard-06`: directional stick tilt, visibly held
buttons, keyboard-wide horizontal glyph alignment, and leftward label/control
adjustments. Six focused checks and the bounded current-build native check
pass within the documented limits. The user has not yet accepted these fixes
on hardware; that does not block private trailer production.

## V2 keyboard

The [N64-inspired keyboard](../specs/KEYBOARD_V2.md) is implemented on V1 Final:
grey shading, native N64 button icons and pressed feedback, and a left-side
stick graphic. The accepted key layout, sounds, proportional editor, controls,
and saved capacities remain intact. The current development ROM is
`build/v2-keyboard-fit-11/Animal Forest English V2.z64`, retaining the
map-suffix correction and adding the compact N64-style layout.

The [fit record](checkpoints/KEYBOARD_V2_FIT.md) owns current checks,
exact artifacts, and limits. The [ordinary work record](checkpoints/KEYBOARD_V2_ORDINARY.md)
retains the earlier accepted editor evidence. Do not repeat resolved setup work.

Remaining V2 game work is concrete playtest feedback, including other keyboard
callers and hardware acceptance of the corrections. No known V2 game change
is awaiting implementation. This does not reopen V1 save testing or
block the available development build. Do not invent further RCs, public
packages, or speculative artwork tasks while awaiting findings. Keep V1 Final
unchanged. Publish only the reviewed website files, not local game inputs.

The [private offline V2 handoff](checkpoints/V2_PRIVATE_PACKAGE.md) is complete
at `build/v2-private-bundle/V2-Development-patch.zip` targets `v2-keyboard-05`;
use the current ROM/adjacent UPS for the feedback corrections. Its three package checks
and bundled standalone patcher pass. No further packaging is queued without
a concrete cartridge or documentation correction; preserve this handoff and
do not use packaging as a substitute for the remaining human acceptance.

## V1 Final

All tracked findings V1-01 through V1-29 have implementations. The
[human acceptance record](checkpoints/V1_HUMAN_ACCEPTANCE.md) closes every
reported V1-01 through V1-23 issue, the reported v0 corrections, and repeated
ordinary save/restart/reload. Do not reopen those accepted cases.

The complete development ROM is
`build/main-diagnostic-text-01/animal-forest-diagnostic-text.z64`. It retains
all RC8 content and adds the [thirteen diagnostic literals](checkpoints/MAIN_DIAGNOSTIC_TEXT.md).
That stage has passing focused checks, committed construction, and full UPS
reconstruction. No known tracked V1 finding awaits implementation.

The [V1 Final handoff](checkpoints/V1_FINAL_PACKAGE.md) is complete at
`build/v1-final/Animal Forest English V1 Final.z64`, with patch-only archive
`build/v1-final/V1-Final-patch.zip`. Three new package checks pass, and its own
standalone patcher recreates the complete final ROM. Preserve these results;
do not create more RCs, repackage without a change, or repeat final verification.
Existing RC artifacts and saves remain intact. Public publication approval and
the recorded redistribution decisions remain separate from the local handoff.

The [requirements audit](checkpoints/V1_FINAL_REQUIREMENTS_AUDIT.md) confirms
the implemented and packaged scope, separates retained evidence from fresh
execution, and records the remaining whole-game-review/publication limits.
It identifies no unapplied tracked V1 finding and does not queue more testing,
neutral-artwork inspection, or repackaging. Public publication needs the user's
direction; new concrete playtest findings can justify further V1 changes.

## Work that can change V1

- Fix concrete new text, layout, artwork, or gameplay defects when identified.
  Crashes, save damage, memory corruption, and blocked progression take priority.
- Preserve GameCube wording, intentional line/page breaks, and timing. Do not
  reflow dialogue broadly or redesign the accepted keyboard during finalisation.
- Keep the final package self-contained: offline patch instructions, sources,
  compiler/source guide, manifest, checksums, save/memory requirements, and
  explicit known limits. The source-build guide points to the final diagnostic
  suffix output, not the older correction-only directory.

Neutral tools, room surfaces, effects, and fish/insect artwork stay unchanged
unless actual lettering or a concrete translation defect is identified.
Broad inspection of those assets is not V1 work and does not delay the final
release. Preserve [completed artwork findings](ARTWORK_REMAINDER.md) without
repeating them. Lucky-bag Japanese decoration intentionally matches English GC
and the user's explicit choice; the shrine remains the native shrine.

## Verification boundaries

Use existing passing source/native evidence for unchanged code and resources.
Do not re-test old builds, launch the full historical construction chain, repair
old test fixtures, resume exhausted harnesses, or maintain the percentage tool
without a concrete current need. Preserve the actual historical full-suite
result; do not claim it passed.

The 61-stage base, 28-stage artwork, nineteen-stage correction, and final
data-only suffix have recorded construction evidence. The composed 109-stage
command is not presented as a newly executed end-to-end run. Package checks
target only the final artifact and its bundled patcher.

Source-identified V1-24 through V1-29 labels retain their recorded verification
limits. Do not enable debug controls, create a town, spawn items, delete Pak
data, or invoke save operations merely to inspect wording. Prior human
acceptance is not fresh execution of these additional labels.

Broader seasonal/event/travel/Pak combinations, individual dialogue layouts,
and ordinary appearance of both adapted festival-stall placements remain
human-playtest work. The controlled stall preview already passes. These
untested cases are not automatically passed, but they do not block the build
that enables further testing. The [validation record](VALIDATION.md) and
[bounded policy](V0_PLAN.md) preserve the evidence and safety requirements.

## Public publication

The source repository remains private. The [release checklist](RELEASE_PREPARATION.md)
and [provenance review](checkpoints/RELEASE_PROVENANCE_REVIEW.md) distinguish
technical readiness from redistribution rights.

- Preserve third-party attribution, licence exclusions, and actual input roles.
  Tooling licences and patch checks do not grant Nintendo-content permissions.
- Obtain the user's public-publication approval and resolve the recorded
  redistribution review before a public upload or repository visibility change.
- Publish only the approved patch package and accompanying documentation/hashes,
  never ROMs, input archives, extracted assets, saves, or emulator checkpoints.

## V2

The [N64-inspired keyboard](../specs/KEYBOARD_V2.md) is the active work. Its
grey N64-controller background, matching button art, and left
control-stick image must preserve V1's accepted sounds, key positioning,
proportional editing, N64 controls, and saved capacities.

## Evidence

Current artifacts are in [progress](PROGRESS.md). Exact implementation and
verification results are retained in [checkpoints](checkpoints/),
[the implementation record](PROGRESS_RECORD.md), and
[the queue record](WORK_QUEUE_RECORD.md). Historical instructions in those
records do not direct completed work to be repeated.
