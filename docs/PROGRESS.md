# Current progress

## Active development

**V3 optional content imports** are the active goal on `v3/optional-imports`.
The [V3 specification](../specs/V3_OPTIONAL_IMPORTS.md) covers individual villager
and item selections, select all, the import-free option, and follow-on e/e+
sources. The [foundation checkpoint](checkpoints/V3_IMPORT_FOUNDATION.md) records
the verified donor inventory and six passing focused tests. Twenty donor-only
villager identities are identified. The [villager artwork batch](checkpoints/V3_VILLAGER_ART.md)
converts Punchy and Cheri's complete body/palette and facial frames into native
objects, verifies their shared models/skeletons, and passes nine focused checks.
The [additive asset loader](checkpoints/V3_ASSET_LOADER.md) installs their texture
banks alongside all 410 original banks without ordinary heap growth. Five focused
checks, actual native object-DMA checks, and the no-Expansion-Pak path pass.
The [native draw adapter](checkpoints/V3_NPC_DRAW.md) installs both pilot rows in
both NPC overlays, reserves stable actor IDs, and preserves full donor voice IDs
without enlarging actors. Seven focused host/cartridge checks pass. A native
boot exposed a DMA alignment defect, now corrected; the corrected build reaches
the game frame loop without a fault and loads its complete checked blob. The
deeper native draw/tail fixture passes in the combined
[audio batch](checkpoints/V3_VILLAGER_AUDIO.md). That batch installs both donor
melodies, verifies their complete shared instrument/sample dependencies, and
widens the native audio paths without low-byte identity collisions. Five focused
checks and actual native playback-entry/sequence/port checks pass, with no
physical audio playback. The [villager text batch](checkpoints/V3_VILLAGER_TEXT.md)
installs shared full-name/phrase readers, native six-byte compatibility names,
default reset, and borrowable four-byte V3 phrase references. Five focused checks
and actual native name/phrase insertion, reset, setter, original/special fallback,
and guard checks pass. The new references require V3 despite unchanged saved
field widths. The [initial-default batch](checkpoints/V3_VILLAGER_DEFAULTS.md)
connects Cheri's personality, verified yellow bar shirt, catchphrase reference,
and hometown through all three native initialization entries. Both pilot
personality lookups, native/test fallbacks, and actual clothing DMA pass native
checks; six focused tests also pass. Punchy's cherry shirt has no exact native
artwork match and needs a proper clothing import before his initialization is
enabled. Selection, remaining ID-bounded readers, and gameplay/save/profile paths remain;
the [static furniture batch](checkpoints/V3_FURNITURE_ART.md) converts Cheri's
haz-mat barrel and oil drum house dependencies into complete native objects.
Seven focused checks pass, including every texel, vertex, and triangle in the
actual donor conversion and compiled N64 lists. The
[furniture loader](checkpoints/V3_FURNITURE_RUNTIME.md) adds stable item identities,
resident profiles, expanded native table readers, and model-bank loading/cleanup.
Five focused checks and 86 native steps pass, including both imported models,
original furniture allocation/DMA, bank reuse/release, guards, and checkpoint
restore. The [shared item-reader batch](checkpoints/V3_FURNITURE_ITEMS.md) installs
both complete English names, leaf classification, donor price values, and 1×1
footprint readers. Four focused checks and 73 native steps pass, including
disabled-profile rejection and all five original-item fallbacks. The
[room-integration batch](checkpoints/V3_FURNITURE_ROOM.md) connects all 21 reviewed
room range checks, both index conversions, and four field-type scans. Four
focused checks and 151 native steps pass, including 125 full-register and
branch-delay cases across the 27 installed detours. The
[shared field-grid batch](checkpoints/V3_FURNITURE_FIELDS.md) connects both native
room-grid builders and donor-backed shop eligibility. Four focused checks and
56 native steps pass, including complete mixed-layer maps, cross-layer indices,
retained rotations, disabled imports, original shop fallbacks, and guards. The
[menu-dispatch batch](checkpoints/V3_FURNITURE_MENU.md) connects furniture action
menus, held-item destinations, and room-placement dispatch. Three focused checks
and 77 native steps pass, including complete action/hand decisions, all four field
contexts, wrapped/quest restrictions, and full-register checks. The
[inventory icon batch](checkpoints/V3_FURNITURE_ICON.md) connects the independent
leaf reader. Three focused checks and 59 native steps pass, including full-register
preservation, actual parent relocation, six descriptor selections, and complete
native drawing commands matching the original leaf for both imports. The
[ground-item batch](checkpoints/V3_FURNITURE_GROUND.md) connects both drop-flag
paths and ground-descriptor selection. Three focused checks and 57 native steps
pass, including full-register/branch cases, native furniture flags, and the
complete descriptor function. The [pocket-search batch](checkpoints/V3_FURNITURE_POCKETS.md)
connects both shared furniture searches; four focused checks and 51 native steps
pass, including 28 complete query calls and original-type fallbacks. Ordinary
acquisition/persistence and Punchy's animated speed
bag remain work. No V3 villager is playable or
enabled in the patcher yet. Both complete ordinary-villager and furniture pilots
remain required. The [save-codec foundation](checkpoints/V3_SAVE_CODEC.md)
implements checked import profiles, payload/extension CRC binding, legacy
decoding, and four imported-item catalogues. Six focused checks and 76 native
steps pass, including complete encoding against an independent reference and
profile/corruption rejection. The [FlashRAM runtime](checkpoints/V3_FLASH_RUNTIME.md)
connects actual saving/loading, separate runtime state, and the English
incompatibility warning. Six focused checks, synchronous writing, a 141-step
two-bank writer, and a 54-step fresh-process reader pass. Both native load entries
restore the imported pocket IDs and catalogue/profile data without using the
unnamed native RAM tail. A normal cold boot with missing imports displays the
complete warning, stops without a CPU fault, and preserves both save banks.
The [collection adapter](checkpoints/V3_COLLECTION.md) connects native pocket
acquisition/collection and resident clearing to the saved imported catalogues.
Four focused tests and a 177-step native acquisition/two-bank save check pass,
including present/quest conditions, original collection, rotation sharing,
separate player ownership, and temporary/resident clearing. A 54-step fresh
process restores the complete acquired payload and catalogue/profile. The
[catalogue adapter](checkpoints/V3_CATALOGUE.md) adds collected-item rows, complete
English names, model previews, selection, prices, and completion. Four focused
tests and 70 native steps pass, including both complete model DMAs, all 438 rows,
and original preview fallback within the existing menu allocation. Ordinary
order/payment, placement persistence, and Controller Pak profile transport
remain work. The [shop adapter](checkpoints/V3_SHOPS.md) adds the pilots to native
ordinary goods lists and category queries while preserving town rarity and RNG.
Four focused tests pass; the native stock-selection and pocket-acquisition
prefix passes. The [shop interaction adapter](checkpoints/V3_SHOP_INTERACTIONS.md)
connects twenty furniture decisions across all five shopkeepers without actor
or save growth. Three focused tests and 148 native steps pass, including both
complete imported-order deliveries/readbacks and pending-order clearing. The
independent [shop-floor adapter](checkpoints/V3_SHOP_FLOOR.md) connects reserve
points, floor-item selection, and sold-removal classification. Three focused
tests and 63 native steps pass, including complete reserve/grid selections and
all changed branch/delay semantics. Ordinary payment/model removal
and the full item lifecycle remain work. The [HRA adapter](checkpoints/V3_HRA.md)
connects all twenty range and twenty index decisions, expanded theme groups,
actual donor scoring properties, and missing-item recommendations. Three focused
tests pass. Eighty-six native register windows pass on the retained detour code;
the corrected current scoring tail passes 46 steps, including complete group
initialization, five recommendations, three point calculations, and a safe
one-past-table marker. The [feng shui adapter](checkpoints/V3_FENG_SHUI.md) adds
actual donor colours while retaining native point weights. Three focused checks
and the first 45-step native run pass, including five complete item evaluations,
three complete room evaluations, disabled/unknown exclusion, and guards.
The [ordinary lifecycle batch](checkpoints/V3_ITEM_LIFECYCLE.md) fixes a room-drop
index alias and three inlined inverse-ID conversions. The current barrel renders
correctly when placed and returns to the pocket with its complete imported ID
through normal B pickup; all original items stay intact. Both items are explicitly
fixture-seeded for this check, not purchased. Seven focused host checks and 25
native instruction windows pass across the fixes; the ordinary corrected
interaction passes 24 recorded steps.
The [house batch](checkpoints/V3_VILLAGER_HOUSES.md) installs Cheri's complete
mapped house, including both imported barrels and K.K. Samba. Her wallpaper and
flooring are exact existing native matches, and every original house is retained.
Five focused checks pass. The current combined selection batch's corrected
42-step house tail passes native house initialization, appended foreground DMA,
all 498 sparse pointers, both imported layer transfers, and guards. Complete
scene allocation and ordinary visits remain unverified. Move-ins stay disabled.
Current experimental ROM:
`build/v3-clothing-resources-01/animal-forest-v3-asset-loader.z64`, SHA-256
`48140ace682f65c7bc9961dc0cf786075222e021e4d8cbba67af24170a4bce3b`.
The [secondary reader batch](checkpoints/V3_VILLAGER_READERS.md) connects map,
inventory, address-list, letter-header, conversation-identity, and generated-mail
names. Six focused checks pass, including full imported names, native alias
retention, disabled/ambiguous-name rejection, both loading checksums, and the
unchanged import-free cartridge. The corrected 101-step native check passes both
generated-name/alias readers and four complete display paths with original and
imported identities, current-owner relocation, disabled-name rejection, and guards.
The [town-selection adapter](checkpoints/V3_VILLAGER_SELECTION.md) expands unseen
counts, history reset, and both initial/subsequent population selection. Six
focused checks pass. Native execution passes all four entries, including two
complete six-villager populations, original RNG/shuffle correspondence, Cheri's
fixed identity, disabled/resident exclusion, history preservation, and guards.
Import move-in flags remain off until ordinary gameplay integration is ready.
The [house-gift adapter](checkpoints/V3_VILLAGER_REWARDS.md) connects imported
furniture to the native reward selector, retaining original exclusions and RNG.
Four focused tests and the initial 45-step native run pass, including both
actual Cheri-room imported gifts through complete list storage and retrieval,
rotations, disabled imports, room boundaries, and guards. Ordinary gifting
conversations remain part of gameplay integration.
The [umbrella review](../specs/V3_VILLAGER_UMBRELLAS.md) verifies both already
installed defaults and their complete matching native artwork: 2,048 pixels,
56 vertices, and 33 material-bound triangles per umbrella. Two focused checks
pass. No ROM change is needed; ordinary rain animation remains a gameplay check.
The [ordinary Cheri gameplay check](checkpoints/V3_CHERI_GAMEPLAY.md) identifies
and fixes an acre-entry crash in both NPC-specific object streaming loaders.
They now use the expanded object table while keeping native reserved buffers
and DMA lifetimes. Three focused checks pass. The corrected current cold boot
and twenty-one-step gameplay run cross the acre normally, load Cheri, observe
her movement, and reach her English introduction with the correct name, outfit,
and catchphrase. Fault pointers remain zero and guards intact. The disposable
town explicitly seeds Cheri; this is not natural move-in or save/restart evidence.
The greeting reaches the normal three-option menu, and a thirty-four-step
continuation completes a multi-page chat with both full catchphrase insertions.
The [clothing resource foundation](checkpoints/V3_CLOTHING.md) installs Punchy's
actual cherry-shirt texture/palette under a separate identity and connects the
shared indexed reader. Four focused tests and the initial thirty-four-step
native run pass, including complete native/imported garment transfers and
rejection/guard checks. All original clothing is retained. The NPC-specific
clothing, wearing/item, and clothing save-registry consumers remain work;
Punchy's defaults stay disabled.
These changes do not change the existing experimental V3 save format or
profile rules; V3 saves still must not be loaded by V2. Ordinary acquisition/
payment, placed-item rotation/persistence, remaining native readers,
and the complete villager remain work.
No import is enabled for players yet.
V3 development continues on GitHub. The web patcher stays V2 until the user
has tested V3 and explicitly approved the switch.

## Stable V2 deliverable

The current cartridge is **V2-11** at
`build/v2-keyboard-fit-11/Animal Forest English V2.z64`.
The [compact keyboard layout](../specs/KEYBOARD_V2_LAYOUT.md) uses a key-only
grey tray with separate attached N64-style shoulders and grips, native coloured
buttons, and the animated N64 stick. Case-alteration/order combination hints
are hidden; their shortcuts remain active. R Space sits above the keys, Z Page
below, and the C-button section above A/B. Antialiased rounded shells replace
coarse edges and the bright top stripes. The Cursor shell is narrower and
further left; Page/Done sit lower within a shorter shell. Eight focused cartridge
checks and
ordinary in-game appearance/input checks pass. The suffix fits the existing
8-KiB reservation without pool growth. The
[fit checkpoint](checkpoints/KEYBOARD_V2_FIT.md) records exact outputs,
the native pass, browser reconstruction, and hardware-testing limits.

The cartridge retains the V2-08 museum/credits corrections. It displays the faraway
museum as `Museum` in the recipient list and removes invisible trailing-space
drawing from the credits. This resolves the identified font-buffer overflow
behind the reported screen freezes while K.K. Dirge audio continues.
All sixteen credits pages fit the real command limit in the native emulator
check: at most 1,295 of 1,792 commands, versus 2,054 for the reproduced untrimmed
page. Visible geometry, complete text, fades, guards, and saved data pass.
The [ordinary performance check](checkpoints/KK_ORDINARY_PERFORMANCE.md) also
passes: a copied town after 8 p.m. Saturday reaches K.K. through normal controls,
declines a request, and completes K.K. Western through the return to dialogue.
Continuous analysis of 156 seconds finds no frozen game-picture interval of
0.5 seconds or longer. The user reports improved appearance; exhaustive hardware
and all-song testing are not claimed.
Save formats are unchanged; compatibility with V2-10 is expected both ways
without migration. Existing builds and saves remain preserved.
The README introduces the current V2
translation to public readers, with patching instructions, hardware requirements,
credits, and bug reporting rather than private V1/RC handoffs.

The existing `TheDiscordian/doubutsu-no-mori-english` repository contains the
complete website, reviewed patch recipe, and GitHub Pages workflow. Pages is
configured for Actions. The repository is public, and main-branch pushes validate
and deploy the website; no rename or separate repo is needed.
The publication address is
`https://thediscordian.github.io/doubutsu-no-mori-english/`.
The [publication checkpoint](checkpoints/PAGES_PREPARATION.md) records the
bounded history review, exact deployment package, and focused verification.
Only the reviewed website files are deployed, never ROMs or saves.

The local portal uses the user's [YouTube trailer](https://www.youtube.com/watch?v=UloFru4K4Q8)
through a click-to-load, sound-enabled embed and a direct viewing link. The
53.9-MB MP4 copy is preserved outside the served site, and fresh exports omit
it. Four focused checks and three-width browser integration checks pass;
the [checkpoint](checkpoints/PORTAL_YOUTUBE.md) records playback limits.

The [YouTube upload resources](promotion/YOUTUBE.md) include a title-screen-led
thumbnail, unlisted and release descriptions, a suggested title, and an optional
pinned comment. Copy and image verification are recorded in the
[production checkpoint](checkpoints/YOUTUBE_RESOURCES.md). The current thumbnail
uses clean, flat lettering over the retained green background and title scene,
addressing the user's font feedback. The handoff contains one upload-ready file,
not multiple export sizes. The user accepts the revised thumbnail.
The upload copy includes the planned public patcher address,
`https://thediscordian.github.io/doubutsu-no-mori-english/`.
The published trailer remains unchanged.

The [local browser patcher](WEB_PORTAL.md) is running at
**http://127.0.0.1:8073/**. It builds the current V2-11 from the original N64 ROM
and actual English GC donor data inside the browser, without uploads. The
corrected output includes the reported map `むら` omission. The
[combined checkpoint](checkpoints/MAP_SUFFIX_AND_PORTAL.md) records four
cartridge checks, eleven JavaScript checks, real browser-output verification,
and static-hosting preparation. The current museum/credits correction preserves
the map and keyboard fixes.
The [visitor-copy pass](checkpoints/PORTAL_VISITOR_COPY.md) uses **Animal Crossing
N64** branding, removes private release/version prose, and adds six explicit
input MD5 references to the FAQ. The live browser download uses that public-facing
name.

V2's N64-inspired keyboard is implemented in
`build/v2-keyboard-fit-11/Animal Forest English V2.z64` on the preserved
V1 Final baseline. It adds grey shading, native N64 button artwork and pressed
feedback, and an eight-direction left-side stick graphic. The complete input/editor prefix,
key positions, glyph metrics, sound code, and saved formats are retained.
The keyboard compensates for horizontal font-projection shrink so letters
remain centred across the bubbles. Cursor/C-button positions and A/L/R labels
are adjusted left; A/B/L/R lettering depresses with the button art.
The suffix uses all 8,192 reserved bytes; no pool allocation changes.
Eight focused layout checks pass on this build; the decoder and direction-helper
evidence remain applicable to the unchanged implementations.

The [feedback record](checkpoints/KEYBOARD_V2_FEEDBACK.md) records
ordinary V2-06 captures of all eight stick directions, neutral return,
uppercase/lowercase/symbols, and all ten pictured buttons. A short same-build
checkpoint continuation finishes the final guard/fault checks after correcting
a test assumption about the caret and trailing spaces. No old build is replayed.
The [ordinary work record](checkpoints/KEYBOARD_V2_ORDINARY.md) preserves earlier
entry, space, caret, deletion, and Start-confirmation evidence. Other keyboard
callers and hardware acceptance of the new corrections remain playtest limits.
V1 Final remains unchanged. Expected V1 Final ↔ V2 save compatibility needs no migration,
but those particular loading directions are not independently executed.

The [private offline V2 package](checkpoints/V2_PRIVATE_PACKAGE.md) is complete
at `build/v2-private-bundle/V2-Development-patch.zip`. Three package checks and
its archived standalone patcher pass; the patcher recreates the exact current
`v2-keyboard-05` ROM from the original Japanese input, not the current correction
build. The package contains offline guides,
credits, source/compatibility records, and checksums, but no ROM or save. This
does not change the cartridge or claim additional gameplay/hardware acceptance.

The [released trailer](checkpoints/TRAILER_TOWN_REVISION.md) is rendered and
visually reviewed at `build/trailer-cut-05/Animal Forest English - Trailer.mp4`.
The 66.5-second 1080p edit follows the native opening music through the English
title, K.K., Fae's single keyboard sequence, Rover's reaction, the town map,
Nook's Cranny and catalogue, a bridge crossing, the post office and loan screen,
inventory, and notice board. Seven focused production checks pass on the current
edit, along with full video/audio decode and the recorded visual inspection of
all four timeline sheets, all 15 transition strips, and selected full-size frames. Final audio
measures −18.06 LUFS / −1.26 dBTP. No listening audition through physical outputs
occurs during production checks. The user has published the trailer and requests
that it remain unchanged; the new map correction belongs only in the ROM.

## Human acceptance

The user confirms all reported bugs are fixed and ordinary save → restart →
reload works across many reloads of the same save. All V1-01 through V1-23
findings are human-accepted, including visual/editor fixes and existing-town
loading. [The acceptance record](checkpoints/V1_HUMAN_ACCEPTANCE.md) also covers
the reported v0 corrections. These checks are complete; do not repeat the
exhausted save harness or keep reported appearance fixes open. Source-identified
menu labels and genuinely untested areas retain their own limits.

## Builds

The [V1 Final handoff](checkpoints/V1_FINAL_PACKAGE.md) is ready locally:
`build/v1-final/Animal Forest English V1 Final.z64`, with patch-only archive
`build/v1-final/V1-Final-patch.zip`. It contains all tracked V1-01 through V1-29
implementations. Three new package checks and the bundled standalone patcher
pass; no older build, game code, or accepted gameplay case is re-tested. RC8
save compatibility is expected both ways without migration, not independently
executed. Expansion Pak, 128-KiB FlashRAM, and RTC are required. Existing RCs
and saves remain intact. Public publication/redistribution decisions remain
separate; this is not exhaustive gameplay or hardware certification.

The [main-program diagnostic batch](checkpoints/MAIN_DIAGNOSTIC_TEXT.md) applies
V1-29: eleven generation stages, the Famicom index label, and an unused reserve
literal. All thirteen fit their existing slots without changed instructions,
pointers, allocations, or saved formats. Four focused checks, the clean committed
construction from RC8, and complete UPS reconstruction pass. The development
ROM is `build/main-diagnostic-text-01/animal-forest-diagnostic-text.z64`.
`make complete` includes this final data-only step; the composed 109-stage
command is not rerun end to end. The diagnostic stage is included in `V1 Final`.
No old build or gameplay test is repeated.

The [current-build integration](checkpoints/CURRENT_V1_REBUILD.md) connects the
nineteen correction stages after the artwork/title baseline, including the new
scene-menu text. `make complete` invokes this suffix inside its isolated source
checkout. Six focused orchestration checks, the committed nineteen-stage run,
and the completed-run check pass. `build/v1-current-01/final/` contains the ROM
and UPS matching the independently built scene-menu candidate. No full historical
replay is queued; the composed 108-stage command has not been executed end to end.
Old builds are not re-tested. This does not change game content or reopen
accepted gameplay tests.

The [development scene-menu batch](checkpoints/SCENE_MENU_TEXT.md) implements
V1-28: 76 Japanese scene, loading, and setting strings in the native selector.
Six focused checks pass, plus the targeted unsupported-control rejection check.
Complete text uses existing storage, all 101 reader pointers retain relocation,
and only one scene-list X origin changes beyond text/pointers. Native actions,
initialization, allocations, and saved data remain unchanged. The clean committed
construction and full UPS reconstruction pass at
`build/scene-menu-text-01/animal-forest-scene-text.z64`; the checkpoint records
exact hashes. The batch is included in the named RC8 handoff. This is
source-identified text, not an accepted user defect being reopened.

The RC4 catalogue/repayment findings V1-21 through V1-23 have
[implemented corrections](checkpoints/RC4_MENU_LABEL_FIXES.md): exact GC Bells
artwork, complete `Not for Sale`, and centred `Your Loan` / `OK`. Five focused
checks and both native price-adapter routes pass. Font arguments are captured in
the native check; screen appearance is separately human-accepted. The committed
rebuild, two package checks, and archived standalone patcher pass. Prices,
transactions, save formats, and previous fixes are retained.

The [menu-text follow-up](checkpoints/MENU_TEXT_FOLLOWUP.md) corrects two more
source-identified omissions: the town-tune confirmation's complete GC
`Are you sure?` / `Yes` / `No`, and the N64-only `Erase a Pak note` instruction.
Eight focused checks, both committed construction stages, three package checks,
and standalone patch application pass. The combined development ROM is
`build/menu-text-followup-01/animal-forest-menu-followup.z64`.
It retains all RC5 fixes and introduces no allocation, relocation, transaction,
or save-format changes. Both corrections are included in the named RC6 handoff;
ordinary appearance remains pending.

The [title-warning follow-up](checkpoints/TITLE_WARNING_TEXT.md) implements
V1-26: complete English for the native missing-controller warning and retained
erase-save menu label. Four focused checks pass, including actual Expansion Pak
relocation, centred complete lines, unchanged controller/menu actions, retention
of every other resource, and UPS reconstruction. The clean committed build is
`build/title-warning-text-01/animal-forest-title-warning.z64`; its exact hashes
are recorded in the checkpoint. This correction is included in the named RC7
handoff. No save format, artwork, or allocation changes;
native rendering and hardware appearance remain unverified.

The [gamestate-menu follow-up](checkpoints/GAMESTATE_MENU_TEXT.md) implements
V1-27: nine complete labels in the separate native player-selection/save-menu
gamestates. Six focused checks pass for original text, longer display copies,
stack/field boundaries, relocated pointers, unchanged metadata/actions, and
complete cartridge/UPS retention. The committed combined development build is
`build/gamestate-menu-text-01/animal-forest-gamestate-text.z64`; its build and
patch reconstruction pass. No allocations or saved formats change. These labels
follow the title-warning stage and are included in the named RC7.
Ordinary accessibility and hardware appearance remain unverified; no save
operation is executed to test their wording.

**RC3 town-loading memory failure corrected in V1RC4 (V1-20).**
The supplied RC2 save reproduces RC3's out-of-memory crash and loads successfully
after the complete bordered font moves to its own Expansion Pak region. The
corrected town has 25,216 bytes free, with intact memory guards and no faulted
thread. Controller movement and clean unsupported-memory stopping also pass.
Eight focused implementation checks, three package checks, a committed rebuild,
and the archived standalone patcher pass. The same candidate includes the
ordinary-space marker fix (V1-19). Cross-version
save compatibility is preferred, not mandatory; loading evidence and unchanged
saved formats are distinct. The original save remains preserved locally.

The [source-bound gyroid interaction](checkpoints/RC4_GYROID_INTERACTION.md)
opens the ordinary English menu and reaches Save & Quit / Save & Continue.
The actual native talking limit is 43 units; the earlier route stops outside it.
The retained active-menu checkpoint avoids repeated navigation. The confirmation
driver stops before confirming a save, and its corrected continuation remains
unexecuted at the setup retry limit. Ordinary saving and restart/reload are
separately human-confirmed; this incomplete automation is not an open save gate.
Original and isolated seed-save checksums pass; emulator checkpoints are not
game saves. Preserve the [earlier attempt](checkpoints/RC4_ORDINARY_SAVE_ATTEMPT.md)
as separate evidence rather than rerunning either completed setup batch.

The preserved preceding private playtest is **V1RC8**, with local ROM
`build/v1rc8/Animal Forest English V1RC8.z64` and patch-only archive
`build/v1rc8/V1RC8-patch.zip`. The cartridge matches the completed current V1
build and retains every RC7 fix, adding all 76 scene-menu translations.
Three package checks pass in 0.443 seconds, and the archived standalone
patcher recreates the exact current ROM. The ten-file ZIP includes offline
application/source guides and bug-report notes, closing the private-guide-link
dependency. The [package checkpoint](checkpoints/V1RC8_PACKAGE.md) records
hashes and committed sources. RC7 save compatibility is expected in both
directions, with no migration; these particular loading directions are not
independently tested. Ordinary save/restart/reload and all reported fixes have
prior human acceptance, retained separately from RC8's new menu-label changes.
An Expansion Pak is required. Earlier RCs and the user's saves are preserved.
The [bug list](V1_PLAYTEST_BUGS.md) separates implementation from hardware
acceptance; this is not a completed public release or hardware-certified build.

The retained RC4 [supplementary patch archive](checkpoints/V1RC4_PACKAGE_DOCS.md) fixes a
source-guide link in the ZIP and passes standalone patch application. It produces
the identical RC4 ROM; the original handoff and compatibility notes stay intact.

V1-17's [font-edge correction](checkpoints/FONT_POLYGON_EDGES.md) has four
passing focused tests and controlled native drawing/guard checks. V1-18's
[transition correction](checkpoints/TRANSITION_EDGES.md) has three passing
focused tests and native reproduction/correction checks for all three closed
shapes and the centre open/midpoint states. The original two-row top gap is
reproduced; corrected closed shapes leave no exposed framebuffer pixels.
Both findings are human-accepted on original hardware.

Retained V1RC2 corrections include the complete GC `I'm new` player option, separate shop `Bells`
unit, and PM texture-edge clamping. Four focused text/HUD tests pass; their
[checkpoint](checkpoints/RC1_TEXT_HUD_FIX.md) records bindings and limits.
The [keyboard follow-up](checkpoints/KEYBOARD_RC1_FIX.md) corrects corner
directions/placement, contains hints, centres key-label ink, and combines all
supported symbols into one page. Six focused tests and the controlled native
drawing check pass (five calls/thirty assertions), preserving save data, memory
guards, and accepted sound code. The full prior editor and font pixels remain.

The separately built [hiring-notice correction](checkpoints/SHOP_HIRING_NOTICE.md)
at `build/v1-shop-notice-fix-03/animal-forest-title-preview.z64` follows V1RC1.
It omits the Japanese Nook 'n' Go placard as in English GC, changing only its
two-triangle command. Four focused checks and complete patch reconstruction
pass. This correction is also included in V1RC2.

Installed corrections cover Press Start pixels, proportional mail/notice editing,
navigation sound calls, Camera/Your Bells images, AM/PM placement, date slashes,
town-tune labels/OK, inventory money sizing, letter prompts/defaults/recipient
display, and the GC-style shaded keyboard background. The recipient reader
supports all 216 villager identities; Limberg is the reported example, not a
hard-coded exception. Player names and saved identities remain unchanged.

Focused source/ROM/patch checks pass for each batch. The pixel editor has
passing native call/guard evidence. Letter UI checks verify representative
recipient names and native prompt/default handling with saved data and guards
retained. The corrected background has complete controlled native drawing and
guard evidence; the reported ordinary appearance is human-accepted. See the
[letter](checkpoints/V1_LETTER_UI_FIXES.md) and
[keyboard](checkpoints/KEYBOARD_RC1_FIX.md) checkpoints. The older RC1 background
probe remains a separate partial result, not retroactively passed evidence.

Remaining work prioritises concrete human playtest defects. The
[full regression](checkpoints/V1RC1_REGRESSION.md) finishes with 25 failures and
75 errors across 2,103 tests, primarily rejecting historical fixtures or older
accounting expectations. A scoped title-metadata correction and independent
binary comparison pass. The [core runtime fixture follow-up](checkpoints/RUNTIME_FIXTURE_FOLLOWUP.md)
closes five historical errors, with passing evidence for 69 selected checks
across eight test files and unchanged source/provenance guards. The suite as a
whole is not passed. The [letter/shared-word fixture follow-up](checkpoints/MAIL_RUNTIME_FIXTURE_FOLLOWUP.md)
closes seven further historical errors with passing evidence for 51 selected
checks, retaining resource/source guards and the native herabuna correction.
The [system-letter/glyph follow-up](checkpoints/SYSTEM_LETTER_FIXTURE_FOLLOWUP.md)
closes twelve further historical errors with 33 passing focused checks and six
fresh source-built creator variants. The playable ROM and saves are unchanged.
The [receipt/probe fixture follow-up](checkpoints/MAIL_RECEIPT_PROBE_FIXTURES.md)
closes four further errors and the word-profile/date-target assertion failures
with 18 passing focused checks. It adds a positive matching-profile check,
a fresh generation-only test build, and current date-installation fixtures,
without changing the playable cartridge.
The [postal/museum follow-up](checkpoints/POSTAL_MUSEUM_FIXTURE_FOLLOWUP.md)
closes ten further historical errors with twenty passing checks. Complete
English contents and delivery patches are checked on the corrected base;
earlier native results remain bound to their actual archived cartridges.
Two fresh creator variants pass current source checks. No playable ROM or
save data changes.
The [Snowman follow-up](checkpoints/SNOWMAN_FIXTURE_FOLLOWUP.md) closes five
further errors with eleven passing checks. It reuses the matching source-built
actor, reconstructs the entire corrected base through the installer, and keeps
the historical interrupted/edge-only native runs distinct. The
[renovation/event/fortune follow-up](checkpoints/LETTER_ACTOR_FIXTURE_FOLLOWUP.md)
closes six further errors with sixteen passing checks. Early installer stages
use current source-bound dependencies; separate checks retain the final readers,
accented event actor, and payment safeguards. No playable build changes.
The [date/fortune/glyph fixture follow-up](checkpoints/DATE_FORTUNE_GLYPH_FIXTURES.md)
closes four further errors with six passing checks. Current module selection and
an isolated date installation retain complete text, font capability, source,
capacity, and transactional rejection checks. No playable ROM or save changes.
The [native-item fixture follow-up](checkpoints/NATIVE_ITEM_FIXTURE_FOLLOWUP.md)
closes one further historical error with two passing checks. It retains strict
rejection of obsolete imports, verifies archived retention separately, and
matches the full current RC4 item-name resource, N64-specific names, rotations,
aliases, and short fields against source-bound construction. No text changes.
Historical fixture repair is not a remaining V1 task unless a concrete current
failure makes an affected check relevant. Do not re-test old builds. Counter
maintenance stays deferred. Reported letter/editor and screen defects
are human-accepted. Broader untested gameplay cannot block the
build that enables it; confirmed game crashes or data corruption must be fixed.

The retained artwork-only reference package is
`build/releases/v1-artwork-playtest-05.zip`, with local ROM
`build/title-civic-interior-combined-01/animal-forest-title-preview.z64`.
It does not include these human-playtest corrections. Its patcher/reconstruction
tests pass, and the
[package checkpoint](checkpoints/V1_PLAYTEST_PACKAGE.md) records hashes,
source revisions, contents, and limitations. It is not a public release or
original-hardware certification.

The package includes the
[GC-style festival stall](checkpoints/STALL_ARTWORK.md), using one shared mesh
and a reflected second placement inside the original allocation. Three focused
tests, the title combination, and the full combined counter pass. A
[controlled native graphics preview](checkpoints/EVENT_ARTWORK_PREVIEW.md)
renders both placements and the fortune table with intact memory guards and
restored checkpoint. The visible surfaces are inspected; the stall preview's
lowest edge is clipped by its framing. Ordinary
stall appearance, lighting, both placements, and event acceptance remain.

The [shop-interior batch](checkpoints/SHOP_INTERIOR_ARTWORK.md) installs seven
exact GC English sign textures across the ordinary, raffle-day, and upstairs
Nookington rooms. Five focused checks, title combination, and the full counter
pass. Every unrelated resource, native room vertex, drawing command, saved
layout, and shop rule remains unchanged. Ordinary room appearance remains
playtest work; the tiny original information-notice wording remains an explicit
transcription gap, not an uninstalled English image.

The [civic-interior batch](checkpoints/CIVIC_INTERIOR_ARTWORK.md) installs the
exact English GC wanted/recruitment posters and postal MAIL bag in two native
rooms. Five focused checks, seventeen counter unit tests, the complete combined
counter, title combination, and patch packaging pass. The three images fit
existing native slots with no palette, geometry, command, gameplay, or save
changes. Ordinary room appearance remains playtest work.

The corrected four-MiB v0 remains at
`build/v0-hardware-fixes-02/animal-forest-halfwidth.z64`. Both complete Nook
conversation fixes and the Shrine wording are retained in every current build.
See [the hardware-bug checkpoint](checkpoints/V0_HARDWARE_BUGS.md).
Existing ROMs, packages, and the user's saves remain untouched.

The [post-v0 rebuild command](checkpoints/V1_REBUILD.md) recreates all 28 artwork,
screen, keyboard, and title stages without retained intermediate artwork ROMs
or precompiled overlay directories. The complete 28-stage public-image execution
passes and matches package `05`'s ROM/UPS and approved title-report profile.
The [isolated base recipe](checkpoints/V0_REBUILD.md) also passes all sixty-one
stages from an empty build directory, regenerating corrected v0 from clean source
checkouts and the three supplied inputs. Its final ROM/UPS/report exactly match
corrected v0.
The retained complete source-to-v1 run passes all twenty-six package-`03` stages
inside that clean checkout. See the
[combined rebuild evidence](checkpoints/V1_REBUILD.md).

The [published compiler setup and complete clean rebuild](checkpoints/PORTABLE_TOOLCHAIN.md)
also pass all 87 package-`03` stages with exact final ROM/UPS matches. Build reports retain
the actual public image identity; separate comparison fingerprints preserve
compatibility with the older approvals. Building no longer depends on the local
development Docker image. Source inputs remain local and separately licensed.

## Implemented scope

The combined candidates include proportional Latin rendering, English dialogue
and its integrated name/letter/editor consumers, the English animated title,
and GameCube-style keyboard with native N64 controls and saved capacities.
Screen work covers map, inventory, clock, collections, catalogue, bulletin board,
town tune, birthday, Controller Pak, editor confirmation, warning windows,
mail/repayment, and gyroid service responses.

Building/event artwork includes seasonal shops, Nookington's main and doorway
signs and clearance banners, police exterior/interior signs/posters, the postal
MAIL bag, Redd's summer sign, SOLD OUT,
both dump signs, fishing props, the fortune table, countdown units, and the
shared stall. Native shrine identity, event rules, and saved
formats remain. The [V1 Final notes](V1_FINAL.md) describe the current packaged
build; [remaining artwork](ARTWORK_REMAINDER.md) records artwork work and
neutral texture sets already inspected.

The [additional structure inspection](checkpoints/NEUTRAL_STRUCTURE_ARTWORK.md)
finds no readable Japanese wording in the selected train, vacant-lot-sign,
Katrina-tent, and Gracie-car textures. The region warning is already English.
Their native artwork is retained and verified in both relevant cartridge copies;
this is review progress, not newly applied English text.

The [house artwork review](checkpoints/HOUSE_ARTWORK_REVIEW.md) also retains the
native walls, roofs, doors, and decorative oval plaques. The inspected English
GC plaques retain the same central decoration. Both native cartridge copies,
season/type selection, and copyright artwork are checked; this is completed
scoped inspection, not newly translated text.

The [regional review and source-matching inventory](checkpoints/REGIONAL_ARTWORK_REVIEW.md)
resolve the island-cottage donor as GC-only and confirm that the native gloom
effect and three shop drapes contain no Japanese wording. Their native assets
remain unchanged. A read-only matching tool now links supported N64 material
candidates to named GC texels and records unmatched candidates and excluded
formats/readers. It helps target remaining inspection; it does not grant text
credit or claim complete artwork coverage. No replacement ROM is needed for
this review-only work; the combined playtest-fix build remains the current candidate.

## Remaining work and evidence limits

Neutral tools, room surfaces, effects, and fish/insect artwork remain unchanged
unless actual lettering or a concrete defect is identified. Their broad review
is not a V1 completion task. All tracked V1-01 through V1-29 findings have
implementations, including the later diagnostic stage in the final assembled
deliverable. Remaining broad playtesting is distinct from unfinished translation
code and does not block the build that enables that testing.

The [household review](checkpoints/HOUSEHOLD_ARTWORK_REVIEW.md) closes 28 further
selected images through direct inspection and exact visible-colour matches to
English GC. The current RC8 retains their complete native owners. New CI8
inspection support resolves the blue tabletop with its 256-entry palette;
three synthetic decoder checks pass. The igloo detail's actual material/vertices
also resolve the wrong-donor lead; preserve its native food-surface pattern.
No text is newly applied and no ROM changes in this review. Do not
repeat this group or claim that it reviews every image in the game.

The [prop/shadow/effect review](checkpoints/PROP_EFFECT_ARTWORK_REVIEW.md)
inspects 34 additional native images and the matching English GC umbrella
decoration. These designs remain native; no newly applied text or changed ROM
is claimed. Native/GC I8 inspection support and three focused decoder tests
resolve six previously unsupported gradient-mask views. The
[dynamic-palette follow-up](checkpoints/DYNAMIC_PROP_ARTWORK_REVIEW.md) resolves
the four deferred player/effect images: all inspected views are non-text, native
palette selection is bound, and the effect palette agrees with a retained RC4
town state. Their textures/materials/palette sources remain unchanged in RC4.

The [player-house/winter-windmill review](checkpoints/PLAYER_HOUSE_WINDMILL_REVIEW.md)
closes seven further non-text atlases. Selected palettes, complete textures,
and material ranges remain native in both RC4 building-resource copies.

The [home-mailbox review](checkpoints/HOME_MAILBOX_ARTWORK_REVIEW.md) closes
sixteen static/animated seasonal textures. Their visible colours and markings
already match the English GC donor. The complete object and actor remain native
in RC4; this is review progress, not newly applied English or gameplay acceptance.

The [additional room/item review](checkpoints/ROOM_ITEM_ARTWORK_REVIEW.md)
inspects 48 images: one hiring notice is corrected separately, and 47 neutral
images remain native. This includes seventeen selected Katrina-interior images;
it is scoped review evidence, not a claim that every game image is reviewed.

Use [the completion queue](WORK_QUEUE.md). Lucky-bag Japanese decoration is
intentionally retained at the user's request, matching the English GC donor.
It is not an outstanding translation task or new English credit. The stall
adaptation still needs ordinary appearance acceptance. Other unreviewed game images
are not declared complete by the scoped seasonal-prop inspection.

The [matching detail review](checkpoints/MATCHED_DETAIL_ARTWORK_REVIEW.md)
closes 35 further selected room/prop images. Their visible pixels already match
English GC, and all selected material sequences and visible pixels are retained
in RC4. No readable Japanese wording is identified; small donor-retained marks
receive no invented transcription. This is review progress, not newly applied
English text, a changed ROM, or ordinary scene acceptance.

The embedded warning drawing probe remains incomplete after its permitted setup
retry; do not repeat that setup batch. Birthday and gyroid controlled drawing,
title/START/low-memory, and corrected keyboard input have passing native evidence
on the exact builds/checkpoints documented in their records. Retention checks
preserve unchanged implementations; they do not turn that evidence into a fresh
ordinary playthrough of a newer ROM.

Ordinary save/restart/reload and all reported fixes are human-accepted. Broader
unreported tutorial/transaction cases, travel, events, and other untested
hardware workflows remain playtest work. Confirmed crashes, save damage, and
memory corruption must be fixed; test-infrastructure limits do not waive them.
Preserve GameCube wording, intentional line/page breaks, and timing during polish.
Public release still needs provenance review and explicit release approval.
The [scoped provenance review](checkpoints/RELEASE_PROVENANCE_REVIEW.md)
checks the private archive's exact contents/checksums and distinguishes legacy
identity corroboration from actual GC/project payload sources. Source notices
retain upstream exclusions and legacy utility authorship. The
[release-preparation checklist](RELEASE_PREPARATION.md) separates packaging,
redistribution review, public documentation access, and release approval; it
does not grant permission or change the playable build.

## Translation measurement

Percentage-tool maintenance is deferred at the user's request. Use existing
inventory when it helps find untranslated text, not as a separate progress-tool
project. The shared counter is `python3 tools/translation_progress.py`; its
candidate selector misses the correction recipes and named release candidates. Do not report an
older cartridge's result as current. The combined approximation counts installed
English against inventoried Japanese source characters across dialogue, names,
letters, and interface/artwork text. Do not report the bank-only diagnostic as
whole-game progress, reuse an old figure, or mix testing effort into replacement
coverage.

[Counting rules](../specs/TRANSLATION_PROGRESS.md) retain explicit inventory
limits, including the tiny untranscribed stall labels. The installed stall model
is verified even though those labels receive no invented character weight.
Generated reports and the per-record ledger live in `build/translation-progress/`.

## Detailed records

Exact implementation and test results live in [checkpoints](checkpoints/),
[specifications](../specs/), and the preserved
[implementation record](PROGRESS_RECORD.md) and [queue record](WORK_QUEUE_RECORD.md).
Build-specific historical instructions in those records do not override this
current state or the [bounded testing policy](V0_PLAN.md).
