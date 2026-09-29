# Current progress

## Stable V2 publication

V2-14 at `build/v2-dresser-14/Animal Forest English V2.z64` fixes B-button
cancellation at dressers and retains the official `Animal Crossing` credits
title and English `Museum` letter headers. Both patchers target this build. The
publication hold applies only to experimental V3, not stable V2 fixes.

Three dresser checks, eight cartridge/packaging checks, and 29 silent native
assertions pass. A current Chromium download using the real CISO and N64 inputs
matches V2-14. The trailer and poster remain unchanged. See the
[publication checkpoint](checkpoints/V2_14_DRESSER.md) for hashes and limits.
V2 saved formats and fossil processing are unchanged; compatibility with V2-11
and V2-12 is expected in both directions without migration. A fresh hardware
playthrough and save cycle are not claimed. The earlier museum rendering-fixture
comparison remains incomplete; its name-resolution and relocation evidence is
retained, not replayed.

The current imported V3 includes the dresser, credits, and museum corrections.
Its empty-selection baseline returns V2-14. This does not change the main V3
lock or publish experimental V3.

## Active development

The current development proposal is ABI 369 / format 19 at
`build/v3-carried-selection-03/build-lock.json`. Orange paper, exercise cards,
knife and fork, coconut, cedar saplings, and spirits have independent selections
through the shared offline/browser composers, bringing the development catalogue
to 213 options. State variants stay with their parent; the sign board stays off.
Card/cutlery choices activate their installed holiday providers without requiring
diaries. Spirits independently activate the quest service and Wisp's actual
character allocation. Existing art, code, and saves are not reconstructed or
overwritten. Eleven composition profiles and complete resource-preservation
checks pass. Silent native boot verifies the actual carried/event masks, Wisp
allocation/service flags, packet guard, and absence of faults; ordinary gameplay
and native save/reload remain unverified. The remaining V3 item identities are
the four golden tools; continue their shared behaviour/reward/acquisition paths.
Carried-family saves require the selected families and cannot load in builds
without their admission, including ABI 368. Four-sheet saves require pack mode.
See [the selection checkpoint](checkpoints/V3_CARRIED_SELECTION.md).

The shared stationery implementation has a global `paper-quantities` choice:
N64 single sheets or GameCube four-sheet packs, across all original/imported
styles and creation routes. N64 is the default. Preparation at
`build/v3-paper-quantities-prepared-10/` contains the 6,304-byte shared
reader/action/supply/catalogue module, 12,304-byte format-18/wire-5 save adapter,
and complete letter/catalogue owners. Its checked resident extension is
`807B4000..807BB000`; existing catalogue, food, and spirit code is not overwritten.
Native singles, orange states, and the native grab bags retain their IDs.
Focused sanitized checks pass for both modes, invalid-mode rejection, all 65
styles/quantities, split/merge/consumption, price/icon/name/ownership readers,
independent original-paper support, and conservative saved-mode binding.
Installed native hooks connect random creation, style-aware exclusions, shop
category, and catalogue order identities. Background-only selection retains
its canonical style IDs. Catalogue previews retain native artwork/DMA while
pricing the actual quantity; order identities carry that quantity to Nook's
quote and pending delivery, without changing mail-transfer semantics.
MIPS compilation and complete owner preservation/relocation checks pass. The
actual format-18 compressed save transaction passes in both modes with native
I/O doubled: partial quantities in all four players' saved pockets, migration
from formats 14–17, retained diary/console/card state, older-reader rejection,
and pack-mode incompatibility rejection before state publication or writes.
The complete policy is installed in ABI 367 at
`build/v3-paper-quantities-installed-08/build-lock.json`. All three shop-floor
consumers, five shop counters, loose-item drawing, and first-job creation/display
use the shared policy without changing quantities during transfers. Public
reader/catalogue/save exports redirect to the new code. The existing quest
startup packet grows to 61,440 bytes; the startup table stays at 22 descriptors.
Eight browser/offline profiles pass, including four-sheet mode with no content
imports and exact V2-14 for an empty/default selection. Ordinary native gameplay
and save/reload remain unverified. Pack-mode saves reject single-sheet mode
rather than discard quantities.

The current native boot check exposed and fixes an incorrect physical-ROM read
in the shared scenery and tree-effect loaders. A bounded physical/virtual DMA
adapter preserves all prepared artwork and existing public entries. The current
ROM boots without a fault and loads the complete stationery module. Routing,
bounds, and allocator reclamation checks pass. Only a recorded obsolete DMA
copy is reclaimed in the new output, with both historical hashes and its live
replacement checked; source ROMs remain intact. Detailed native paper-fixture
results live under `build/v3-paper-quantities-native-03/`. The fixture's initial
allocation and its one corrected-allocator retry both return null before any
paper calls. No native paper gameplay result is claimed; the setup retry budget
is spent. Continue the remaining connected consumers instead of repeating it.

Wisp's complete actor is installed from `build/v3-carried-npc-connected-13/` with all
retained participant/motion records, its official text, walk-only schedule,
weed counts, roof-colour writes, item mapping, and guarded handovers. All 22
reward lists retain 998 candidates; 1,000 destination mappings include the two
source fallback items. Disabled imports are filtered before either reward
selection branch. Every paper reward binds to the installed global quantity
provider. The complete two-layer first-encounter sound and disappearance sound retain their
donor programs, instruments, samples, timing, and priorities through the shared
audio converter. One unused cross-group priority slot supports the latter without
changing any existing sound. Click-voice mode has both a native predicate hook
and message-initialization reset; the original selector retains silent mode.

The deferred weed reward covers the saved town at outdoor field renewal,
suppresses regrowth during that renewal, and retains the source notification
deferral. Its pending bit survives hunt-date cleanup and player deletion.
Installed format-19/wire-6 storage is 12,592 bytes at `807BB000`; the complete
37,616-byte NPC/service module links at `807BF000..807C82F0`, including BSS and
guard. Its descriptor and guarded actor pool end at `807C8D70`. There are no
unresolved actor services. The shared registry redirects retain all prior
participants; Wisp's two complete character banks use `04800000/04804000`, outside
the expanded audio reservation. The native transfer reader supports all ten banks.
Focused sanitized world/voice checks, current source/audio retention checks,
fourteen shared sound-parser/allocation checks, and the format-19 save transaction
in both paper modes pass. Native I/O is doubled in the save test; forward
migration from formats 14–18 and older-reader rejection are covered.
Successful-save/travel cleanup stages spirit removal in write buffers and only
clears live pockets after full success. Native error paths that also return `1`
do not count as success; allocation, FlashRAM, and Controller Pak failures retain
live items. Automatic player-load/reset-guard saves keep spirits. The departure
writer accepts native private snapshots by complete identity and retains imported
fish/insect records. Sanitized transaction/transfer checks and complete cartridge
resource, hook, relocation, startup-CRC, and patch-reconstruction checks pass.
The audio append moves three complete tree-art pages through their checked table;
every art byte and old sound remains. Eight current browser/offline profiles agree,
including pack-only and exact V2-14 for an empty/default selection.
The conversation host fixture has
not executed successfully; its two setup attempts are recorded as incomplete,
and no further attempt is spent on that fixture in this batch.
The retained ABI-368 / format-19 provider boot passes at `build/v3-carried-npc-boot-01/`,
including the six-character registry, ten-bank directory, final packet guard,
and absence of a faulted thread. Wisp interaction and native save/travel remain
unverified; no hardware result is claimed. Format-19 saves cannot be read by
format-18-or-earlier builds, and pack-mode saves still need pack mode. Existing
ROMs, saves, and both deployed V2 patchers are unchanged. Independent selections
are connected in the current proposal above; keep gameplay verification explicit.
Able Sisters (including its custom-design system), the Museum building, and comparable large features
belong to V4. Unfinished design code is isolated on `v4/deferred-custom-designs`
at `baded8ca`; its checkpoint there records prepared resources and the unresolved
save-fixture failure. None of that code is installed in the active V3 build.
Design-dependent imports remain deferred, not complete. Ordinary item behaviours
and fish/insect/fossil imports remain V3 work.

The active work is the importing pipelines: extraction, conversion, bulk
installation, and working item behaviours, including item-specific behaviours.
There is no blanket postponement of item-specific work. Acquisition systems
remain separate. The [execution order](WORK_QUEUE.md#execution-order) governs task
selection; pending rewards must not displace unfinished conversion categories.
The code-entry keyboard is parked, incomplete source work. Its attempted build
stops on resource preservation before producing a ROM; it is not installed.

Complete gold/palm/cedar banks are installed in all four seasonal renderers.
The shared importer reuses every prepared model, palette, growth/death/stump
appearance, coconut, and Christmas light. Drawing tables have 139/140 entries;
all four appended actor index arrays and the temporary stack grow together.
Native matrix nodes and Christmas-light state remain in place. The shared
12,596-byte runtime occupies the checked 20-KiB reservation at
`8077B000..80780000`, outside the carried/save packet. Additional active-scene
memory is 72,512 bytes, or 73,936 in Xmas, including the larger actor.

The complete seasonal banks share identical 4-KiB pages: 250,832 cartridge bytes
reconstruct 422,288 bytes without dropping artwork. Each reconstructed bank keeps
its full CRC and pointer validation. Storage uses checked zero space outside live
resources. Existing planting, daily, world, player, insect, and camera callers
are rebound together; the insect shake notification remains intact. The refresh
route can reuse these banks and allocations for subsequent behaviour changes.

Growth/death, fruit regeneration, mixed-family neighbours, thinning, hidden
contents, collision/digging, shaking/cutting, player targeting, camera limits,
field clearing, and the original on-tree insect habitat now share the complete
gold/palm/cedar rules. Palms use the coastal acre row; cedars use each cell's
actual terrain height. Cedar planting and all four seasonal throw previews
retain native placement, animation, consumption, and flower handling.
Coconut eating uses both complete resident drawing lists through nine-entry
food tables; original foods and turnips retain their native artwork and animation.
The 72-byte food tables use existing padding, with no added allocation.

Six focused tree checks pass for sanitized family behaviour, source/native
bindings, allocation, relocation, page loading, startup, and refresh reuse.
Three focused food checks pass for complete tables, retained native code,
relocation, source rejection, packet bounds, startup checksums, and patch
reconstruction. Browser/offline outputs agree for seven current profiles;
empty selection remains V2-14. These are not native rendering/gameplay or
hardware results. Independent admission still keeps palm/cedar unavailable.
Retain the complete resources at
`build/v3-carried-trees-prepared-02/` and the
[tree-family contract](../specs/V3_SCENERY.md#palm-and-cedar-dependencies).

The complete tree-effect family is installed through one shared conversion and
runtime path: fourteen seasonal tables, 63 skeletons, 105 motions, 122 models,
eleven sprites, and all 42 palette frames. The native tree actor and all four
player shake/axe callers use these resources. Two additive particle profiles
preserve the original shrub/snow effects and all nine existing imported effects.
Source timing runs at two donor ticks per native update; joint workspaces have
room for the root plus every joint, with double-buffered matrices retained.

The guarded `80780000..807AC000` reservation adds 180,224 resident bytes. A
32-KiB code/configuration packet loads at startup; 36 complete art pages share
35 checked physical blocks and load before tree-actor construction. The full
resource CRC is checked before use. The shared cartridge allocator merges
overlapping mappings and protects pending owners before finding free gaps.
No live resource, original artwork, or save field is replaced to make room.
The native actor/controller allowance increases by 184 bytes; the replaced
native actor no longer allocates its separate seasonal art heap.

Eleven focused conversion, MIPS linkage, sanitized page-reader, allocation,
owner/relocation, profile-retention, startup, and patch checks pass. The current
cartridge agrees across seven browser/offline profiles, including exact empty
V2-14. The 21-packet bootstrap occupies 656 of its 688 reserved bytes. Native
effect rendering/gameplay and hardware remain unverified. Continue the same
carried-item task with the remaining sign-board/spirit consumers and independent
admission; do not reconvert the tree artwork or replay unchanged checks.

The shared creature importer includes the complete spirit field behaviour:
all fifteen donor functions, both full billboard models, four animation entries,
native lighting, held animation, escape, and light cleanup on scene teardown.
The existing insect controller/buffers are reused. Code, artwork, and the three
expanded 41-entry tables fit checked padding inside the tree startup packet;
the original tree code/page directory and all forty preceding insect entries
remain intact. This adds no resident allocation or startup descriptor.

The connected capture path merges into a non-full spirit stack before using an
empty pocket. Release removes one spirit, retains the rest, and requests the
native release animation. Indoor menus prohibit cage placement; protected and
unrelated items retain their native handlers. Five complete official GameCube
catch messages and the donor's empty sixth record retain their wording, line
breaks, colours, and pauses, with credits in the single source catalogue.
The shared text allocator slides an index inside existing text-owned space when
a bank grows, avoiding a needless large relocation. Capture/menu code and
inventory policy occupy 1,872 bytes of existing carried padding and add no RAM
or saved fields.

Focused source, sanitized lifecycle/drawing/interaction, current cartridge,
relocation, complete text retention, 21 startup CRC, and patch checks pass.
Seven current browser/offline profiles agree; empty selection remains V2-14.
These are not native gameplay or hardware results. Actual Wisp event ownership,
sign-board designs/placement, and independent
carried selections remain unfinished; all seven family readiness bits stay off.

Six native inventory routes enforce the source spirit and sign-board rules:
spirits cannot be sold, entrusted, gifted, or submitted for a quest; they remain
eligible for release during a full-pocket exchange. Sign boards cannot use that
exchange route. Protected conditions, empty storage slots, card/cutlery rules,
and native fish-water checks stay in the preceding complete filters. Mailing
already rejects the insect category and retains its original function/callers.
The shared interaction refresh reuses the existing allocation, artwork, dialogue,
and saved format. Focused sanitized interaction and current cartridge checks,
all 21 startup CRCs, UPS reconstruction, and seven browser/offline profiles pass.

The shared character importer prepares Wisp's complete translucent model and
expressions in `build/v3-carried-wisp-art-01/`: 6,688 model bytes, 4,128 texture
bytes, 26 joints, and 186 triangles. All 48 actor functions and four event-manager
functions compile for VR4300 in `build/v3-carried-event-prepared-03/`, retaining
the complete conversations, rewards, fade/movement logic, acre selection, and
cleanup. Native state/rendering accesses are explicit unresolved services, not
successful placeholders. These prepared resources are not installed or playable.
Continue by binding their scheduling, persistence, placement/spawning, native
NPC services, official dialogue, and reward providers; reuse the prepared art.

The shared carried-item importer installs the remaining seven parent families
and all 26 states together, with readiness and selection still off. Its checked
`build/v3-carried-batch-prepared-05/` resources supply fourteen pocket icons,
seven handover/police models, full orange-paper background/lines, official names,
and source prices without graphics recompilation. Fixed additive IDs preserve
all native paper and flower identities. Name/type/price/display/pocket/icon
readers delegate unrelated items through the existing reader chain. Cedar has
its own ground category, distinct from diaries; spirits do not acquire an
invented dropped-cage model.

The native letter window has the additional complete orange-paper models and
official text colour, preserving all 64 original styles and the existing editor.
Its shared constructor normalizes all four imported quantities to one paper
style; physical graphics pointers avoid overwriting the native DMA buffer.
The shared seasonal bitmap, startup, and enlarged menu allocations are connected.
The shared inventory path includes multi-sheet menus, one-at-a-time pickup,
paper/spirit merging with overflow retained in hand, and one-sheet consumption
only on confirmed letter creation. Native hand movement, ticket handling,
protected-item conditions, and original paper remain intact. All existing menu
words and cancellation positions are reused; four additional menus share one
handler. The action code fits its installed reservation.
All seven carried families have saved-profile requirements in the existing
48-byte card extension. Four independent paper-ownership bytes share that owned
allocation without changing native save arrays or card-stamp offsets. Native
collection calls and the catalogue use this ownership; orange paper has one
four-sheet catalogue entry and both complete preview models. All 64 original
styles, native editor resources, and unrelated catalogue pages remain intact.
Thirty public save entries redirect to the complete format-16 adapter. Missing
required families reject loading before changing live town or output state;
format-14/15 migration retains card stamps, diary pages, and console records.

Focused sanitized save/collection/catalogue checks, current cartridge/resource
bindings, all twenty startup checksums, allocation bounds, patch reconstruction,
and seven browser/offline comparisons pass. Existing reader/stack/letter/ground
checks remain retained for unchanged code and artwork. These are not native
rendering or gameplay/save verification. Remaining item-specific field behaviours
and independent selection remain the same connected task. See
[the carried-item contract](../specs/V3_CARRIED_ITEMS.md).

The actual acre-entry manager dispatches selected quest spirits through Wisp's
five assigned acres and the complete shared habitat/group-creation path.
Unbound, stopped, errored, disabled, or unrelated-acre quests retain the installed
ordinary insect manager and its N64/GameCube population choice. Wild occupancy,
colonies, field rank, candy/trash suppression, native positioning, creation
failure, and the donor's countdown lake relocation are preserved. Ordinary
calendar decoding still rejects spirit type 40.

The 4,496-byte spawning code occupies the retained 8-KiB prefix at
`807AC000..807AE000` of the expanded quest packet. Existing tree/page directories,
all artwork, and insect program buffers are unchanged. The shared startup loads
22 packets using 676 of its 688 reserved bytes. Focused sanitized quest-state,
five-acre, countdown, and unchanged ordinary-population checks pass, along with
the actual cartridge caller/resource checks, all startup CRCs, patch
reconstruction, and seven browser/offline profiles. These are not native
gameplay or hardware results. The missing Wisp owner still leaves the quest
inactive; all seven carried readiness/selection bits remain zero.

Wisp's source hunt calendar and native event-state services are installed in the
same guarded quest packet as spirit spawning. The donor's two-to-four-day
rescheduling, seven-day eligibility, year/leap handling, and midnight-to-4am
window use additive native event 115 without renumbering existing events.
The complete 44-byte common record occupies owned memory and follows the
lifetime of a native common-area marker; the real daily status supplies the
spirit field bridge. Saved quest flags use native area 54. The town-wide hunt
date uses two owned bytes in the existing 48-byte extension, not native padding.

The 12,032-byte save adapter and 7,168-byte combined quest-state/manager module
occupy the existing 32-KiB quest startup packet. All 22 startup descriptors still
fit in 676 bytes.
Thirty-six public storage/profile entries redirect to format 17 / card wire 4;
compatible format-14/15/16 records migrate forward, retaining diary pages,
console data, stamps, and paper ownership. Two obsolete event startup copies
with verified live replacements provide cartridge space in the new output only.
All current artwork, tree/spirit code, and other physical resources are retained.

Three focused checks pass for sanitized source dates and event-state lifetime,
actual save transactions with native I/O doubled, current code/caller/resource
bindings, all startup CRCs, and patch reconstruction. Browser/offline composition
agrees for seven profiles, including exact empty V2-14. Native gameplay,
save/reload, and hardware remain unverified. Wisp's NPC,
dialogue, and complete reward/save-travel cleanup services are still required: availability
and all carried readiness/selection bits remain zero.

The complete Wisp source manager connects the five unique spirit acres,
same-player/date hunt restoration, returned-spirit state, native acre entry,
culling, and event-end cleanup of normal-condition spirit pockets. Protected
items remain untouched. Its additive event-control row retains all 73 existing
controls and adds only 32 on-demand bytes. Shared placement uses Wisp's actual
five-tile edge margin and source seed. Its result comes from native placement
storage, independently of the source's debug pointer. NPC identity reservations
are fixed and inactive: `D0CD`, profile `F0`, banks 456/457.

The source-manager host check and 108 complete donor-search comparisons pass,
along with current owner/relocation/resource checks, 22 startup CRCs, patch
reconstruction, and seven browser/offline profiles. The resident allocation,
format-17 save code, all artwork, and original controls are retained. The NPC
is not registered or playable; no native gameplay or hardware result is claimed.

The current proposal is ABI 368 at
`build/v3-carried-npc-installed-08/build-lock.json`, ROM SHA-256
`b0e1c41ad0af74c499be9dc5d34e0a6594421baf3d7a830f3cb54b0d9ef9a6b0`.
It contains 207 independently selectable development imports, including all
sixteen diary styles, all nine fish, and eight insects. Another 100 furniture
profiles await acquisition. The main lock and both stable V2-14 deployments
remain unchanged; these are experimental source and local artifacts.

Diary selection connects the carried/cover records, metadata, saved bits,
catalogue/scoring rows, five special-character allocation flags, participant
registry, and fishing/Harvest providers. All 83 actual event dependencies resolve
through installed providers; collision-only positions remain in layouts without
requiring nonexistent actors. One data-driven activation group serves both
composers. Unrelated imports retain original events. Explicit N64/GameCube
calendar and tournament-measurement choices have actual installed bindings.
Unselected gifts retain complete official conversations without false rewards.

The ordinary and exercise conversation paths support profiles without selected
holiday gifts. Actual Tortimer conversations still record attendance, using
existing official standalone dialogue without promising excluded items or
writing a trophy receipt. Selected gifts retain their complete source handover;
the summer exercise-card conversation requires selected cards and its radio
prize. The shared checked gift map includes the aerobics radio, which is outside
the ordinary 28-event reward table. All 66 mapped identities use actual installed
profile/metadata checks, including the carried diary IDs.

The connected 20,240-byte world/card module uses 52 checked redirects and one
shared exercise context. Existing artwork, animations, and actors remain intact.
The unchanged 64,064-byte festival code prefix shares a 105,904-byte startup
packet with carried resources and the save adapter; twenty descriptors still
fit the 676-byte bootstrap. Current resource hashes, redirects,
all startup spans/checksums, source batches, and patch reconstruction pass.
Focused source/sanitized-host checks cover disabled gifts, actual attendance,
visitor isolation, selected handovers, and official greeting field requirements.
Current browser/offline empty, all-supported, unrelated, one-diary, all-diaries,
calendar-only, and tournament-only outputs agree. Empty is exactly V2-14;
unrelated selections disable imported events. A single-diary/GameCube-calendar
offline build also reconstructs its patch and updates its complete receipts.
Current physical resources, all twenty startup transfers/CRCs, source batches,
and source hashes pass. Native diary UI/save and activated festival gameplay
remain unverified. The exhausted native fixture stays closed. The remaining
importing work is the carried-object/stationery group and any unfinished golden
tool behaviour; acquisition and the required gold-tree work follow primary imports.
Saved format 17 migrates compatible earlier saves forward. V2 and
format-16-or-earlier V3 cannot load new saves. Removing required imports,
including any carried family or selected diary style, rejects loading. Preserve
backups; ordinary native save/reload remains unverified.

The complete moon/meteor effect family is installed: moon reflection, meteor
emitter, moving trail, and sparkle. Complete source lifecycles, native drawing,
scrolling, actor attention, and 60-to-30-Hz timing share one 16,400-byte guarded
packet. All original effects and the four imported room effects are retained.
The shared model converter handles the family's complete mixed-intensity
textures and 256-pixel scrolling. The effect loader validates room and sky
callbacks against their actual separate code ranges. The nineteen-packet startup
fits its existing reservation; the large holiday packet and saved format stay
unchanged. Focused source/sanitized-host, current-cartridge, and browser/offline
composition checks pass. These effects are bound to the dedicated dispatcher;
holiday participants/controllers and calendar admission remain unfinished.
No native fixture is restarted, and these checks do not establish in-game
rendering or make diaries selectable.

The shared race, tug-of-war, and New Year participant module is installed in the
current proposal, using `build/v3-diary-category-work-01/participants-prepared-26/`.
All three controllers, five resident roles, and the rope compile together from
245 complete donor functions. The preparation includes 279 official messages,
two choices, offering payment, matched motions, the full prayer motion, tools,
and native effect/sound mappings. The complete deforming rope and shadow use
the shared model converter. Fixed identities, ordinary NPC allocation, guarded
callbacks, and deferred identity cleanup share one registry. A sanitized host
check and 23 shared conversion checks pass; native gameplay remains unverified.
The complete town-selection/placement reader family and both NPC spawning
routes have installed hooks, preserving original/camper dispatch and the global
prayer-animation chain. Native resident selection/refill algorithms and verified
red/blue uniforms are reused. Collision includes the unspawned fifth New Year
queue position without inventing a fifth actor. The complete offering coin,
both palettes/models, and both sound programmes use the shared importers.
The linked 51,872-byte module and original sky prefix share one 68,272-byte
startup packet, retaining the nineteen-entry bootstrap and holiday/fishing
packet. All 21 hooks, dialogue, source coin profile, both sound programmes,
and full artwork are installed together. A native NPC-manager guard handles
failed event storage allocation without losing initial/refill semantics or
dereferencing a null pointer. Text storage moves only the 50,976-byte message
index; verified obsolete audio storage is reused instead of adding copies.
The offering trajectory targets the actual native shrine box, using the loaded
shrine's position and both seasonal meshes. Source vertical motion, palettes,
sounds, and fade are retained; the water splash is removed from the solid box.
Sanitized trajectory checks pass across four elevations and twenty launch angles.
The participant name/profile/effect resolver is installed in the shared event
dispatcher, with admission still off. Source/host placement and unchanged
profile-loader evidence is retained. Native execution remains unverified.

The shared character converter and bank installer handle the New Year attendant
and Halloween costume together. Their complete models/textures are installed
in fixed banks 450–453, retaining ordinary Tortimer's 448/449. Clamped
non-power-of-two textures, fixed faces without expression textures, primitive
colours, and lossless shared drawing commands use the common converter. Both
models retain every face and texel; the larger model fits the original buffer
without cropping. The refreshed renderer is bound in both native NPC owners.
Current-ROM checks verify all six banks, transfer entries, renderer calls,
participant bindings, and unchanged actor admission/save profile. Focused
conversion and sanitized drawing checks pass. The inherited participant-stage
test does not complete against the later art-only stage because its original
stage files/relocation receipt are absent; its accepted earlier evidence is not
claimed as a fresh pass. The current private browser export
`special-art-browser-02/` matches offline output for empty, all-supported, and
both mixed profiles; cancellation and unknown selections are rejected correctly.
No native fixture is restarted.

The costume has installed allocation, callbacks, full voice, placement identity,
and both spawn bindings through the same complete holiday controller as ordinary
Tortimer. The variant batch appends refreshed shared movement/world modules and
a guarded actor slot to the existing startup packet (91,664 bytes total).
All 45 public entries retain their original addresses through checked redirects;
ordinary resident/camper/participant spawning remains in the fallback chain.
The shared physical allocator grows the owned packet into verified adjacent
free space, retaining the original ROM. Current-ROM callbacks, redirects, pool
guards, spawn hooks, packet hashes, and inactive selection flags pass structural
checks. Existing sanitized movement and world checks pass using current code
and current installed item records. Native execution remains unverified; the
latest private browser pass above covers the preceding art-only build, not this
new lifecycle addition. Do not replay it until the connected batch is ready.

The shrine attendant's complete English fortune actor is installed under its
additive identity, including payment/refund, letter generation, save/destruction,
and mapped New Year cleanup. The original native actor remains unchanged.
All three special identities have official GameCube names and metadata through
shared readers; both spawn callers use the registry rather than per-name hooks.
Current-ROM reader/startup checks and existing allocation/rendering host checks
pass. Native execution is unverified. The combined packet is 102,352 bytes;
the same nineteen startup descriptors and saved format remain in use.

The complete exercise actor/card family is installed from
`build/v3-diary-category-work-01/exercise-prepared-16/`: 34 actor functions,
17 card functions, number formatting, 20 matched motions, and 158 individually
credited official messages. Real inventory, attendance, radio, clock, card
handover, and player exercise controls are connected. One shared registry serves
Copper, four resident roles, and Tortimer while retaining existing participants.
Copper's complete artwork occupies banks 454/455; Tortimer reuses 448/449.
The 35,424-byte code module and two guarded special-actor slots share the same
nineteenth startup entry in a 143,136-byte packet. All 82 registry/save redirects,
current physical resources, changed packets, player hooks, startup CRC, and
inactive admission pass structural checks. Native execution remains unverified.

The shared carried-event controls cover all thirteen card states and Harvest
cutlery: Grab/Throw Away/Quit, confirmation, native shrink/deletion, mailing
restrictions, and eight inventory filters. Both added warnings and the action
labels retain official wording, credited in the single source catalogue.
The native menu tables retain all 45 existing action rows and 16 warning rows;
their extensions and both allocation owners pass relocation-preservation checks.
The 1,728-byte controls and 10,256-byte save adapter share the existing nineteenth
startup entry, in a 155,136-byte packet. The 27 save redirects preserve existing
entry addresses, card state, and scratch allocation.

Experimental saves use format 15. The existing 48-byte card record also records
required card/cutlery support, checked before loading into a reduced profile.
Compatible older saves have a forward migration path; V2 and format-14-or-earlier
V3 cannot load new saves. Preserve backups. Current-ROM hooks, packet bounds,
startup CRC, and inactive gates pass. Six provenance checks and the two existing
compression/fishing-storage host checks pass; they do not execute the new
format-15 path. Native menu execution and format-15 save/reload remain unverified.
The shared calendar implementation connects both N64 and GameCube dates to
live scheduling, diary labels, and real saved attendance. N64-only celebrations
remain, and GC-only holidays supplement either setting. Corresponding original
controllers are excluded when imported owners take responsibility; ordinary
native status readers observe the imported event. No actor save-area layouts
are aliased. Browsing the adjacent years preserves Gregorian dates without
reading outside the lunar table. The added code and guard occupy 12,768 bytes,
with a 492-byte diary context inside its existing reservation. The combined
event packet is 167,904 bytes; startup still has nineteen entries, and format 15
is unchanged. Current physical-resource/startup checks and compilation pass.
The existing connected calendar/attendance host check passes the changed
scheduler's donor route; native execution and the alternative route are not
claimed. The setting remains unexposed while actor admission is unfinished.
The remaining five ordinary festival families are installed together from
`festivals-prepared-04/`: ten complete cherry-blossom, moon/meteor, countdown,
ball-toss, and Harvest actor implementations. All 558 official English messages
are mapped, including 125 timed endings. Complete encoded equality and existing
official credits allow reuse of 372 installed records; 186 additional records
have credits in the same provenance catalogue. No wording, page breaks, or
timing is shortened to fit storage.

One 22-owner registry supplies all old and new participants through 68 checked
public-entry redirects. Native head movement, clocks, resident names, tools,
effects, and sound calls are bound. Three complete additional motions retain
their curves and eye/mouth/feeling programmes, with ordinary hand/mouth bank
release preserved. The native animation entry retains the existing fallback.
The 43,824-byte festival packet loads separately beside the 167,904-byte prefix
at contiguous RAM addresses. Compact startup descriptors fit all twenty packets
in 676 bytes inside the existing 688-byte reservation. One verified obsolete
102,352-byte packet is reclaimed only in the new output image; original files
and saves remain untouched. No save-format or profile change is introduced.

Ten shared keyframe checks, six provenance checks, and the existing sanitized
startup check pass. Current-ROM verification covers all physical resources,
twenty packet CRCs, 68 redirects, native motion hook/unchanged relocations, actor
bounds, packet guards, and inactive admission. The builder reconstructs the ROM
from its UPS patch. These are not native gameplay or hardware results.
Continue complete actor/service admission in this same category, then expose
the setting and diary selection. Do not restart the
exhausted native fixture or new-harness budget. No diary is selectable, and both
stable V2-14 patcher deployments remain unchanged.

All fourteen dedicated event owners have live manager callbacks through the
shared dispatcher and existing common state. Their 85 identity requirements
come from every source layout variant and actual profile/effect calls. Missing
participants, controllers, or effects reject the entire callback before scene
mutation; the calendar stays inactive until those providers are implemented.
A failed transition also rejects correctly instead of treating `-1` as success.
Focused source/host and current-cartridge checks pass, as does current browser/
offline empty, mixed, and all-191 composition. The native fixture budget remains
exhausted; these checks do not claim in-game event execution or playable diaries.

The complete eighteen-decoration event batch has installed constructors,
initialization, movement, destruction, drawing, and collision. The generator
follows all eleven source owners' complete local controller calls, including
countdown coordination, Harvest fork handling, radio effects, and fishing-record
logic. Shared native setup uses the existing structure pool; descriptor and
cleanup hooks preserve the NPC/balloon/campsite/original actor chains. Additive
names `5F00..5F11` and profiles `CE..D8` are fixed independently of selections.
The source controllers retain native actor layout and deletion semantics.

The guarded holiday packet is 272 KiB. Its existing startup descriptor loads the
10,952-byte lifecycle module and 1,536 bytes of owned state/profiles alongside the
retained renderer, collision routines, binding directory, and complete artwork.
No graphics are reconverted. Ordinary/scripted acre-transition predicates have
native bindings; the absent boat-boarding transition is not sent to a native
enum with a different meaning.

All eighteen decorations have foreground bindings. Matching native markers
retain their existing meaning, including the basket/fishing shared marker;
Groundhog and Harvest use separate `F300/F301` identities. Checked native field,
item-category, and drawing consumers preserve these as temporary markers.
The radio uses the existing native musical-note effect. Shared movement executes
two source steps per N64 update, preserving the donor's 60-Hz counters and
animation speed on the 30-Hz engine. Countdown digit flips also advance twice,
with one geometry submission and no state advance for rejected draws.

The installer refreshes this shared module within its existing physical/RAM
reservation. It validates the predecessor, rebinds the four owner hooks, retains
the original fallback chain and complete artwork, and updates startup CRC.
No new packet allocation or saved-format change is needed for a refresh.

The shared carried-item importer also contains all thirteen exercise-card states
and the Harvest knife and fork. Source-derived official names, zero-price rules,
two complete models, two pocket icons, and the name/type/price/placement readers
are installed together. The generic converter accepts carried parent records
from their actual donor category tables; existing equipment preparation is
retained. One additive category installer binds both new categories to the
existing police/handover tables and all four seasonal ground owners. It appends
complete descriptor banks without moving scenery or existing artwork. The
loaded holiday packet does not grow. All fourteen names have official-disc
attribution in the single provenance catalogue.

Harvest pickup is connected to the actual ordinary-item search, native table
animation, inventory insertion, and source controller's delayed removal. The
counter advances only after the requested pocket contains the fork. A full
inventory uses the native refusal animation and official GameCube message,
credited in the single provenance catalogue. All four seasonal renderers use
the actual tabletop collision height. The shared packet retains its allocation;
the 1,152-byte adapter fits inside its existing reservation.

The item readiness mask is zero. Exercise-card menus, event activation, and
profile/save admission remain unfinished; no event item becomes selectable or
playable from these installed connections alone. The current cartridge check
covers all six changed player/seasonal calls, relocation removal, original
fallbacks, text/bounds, provider pointers, startup CRC, retained packet resources,
and unchanged save/profile data. Empty/mixed/all-191 browser/offline outputs agree.
Existing carried-item resource checks are retained, not replayed. No native
fixture is restarted, and pickup gameplay has not been executed.

The complete five-record fishing core and save integration are installed. The
15,488-byte module includes the donor's holder, size, date, sorting, and finalising
rules. A separate 176-byte record block preserves full eight-character identities
without changing diary/page offsets. All 28 original/direct storage entry points
reach the new code; player deletion, capacity checks, migration, and town changes
include the records. Controller refreshes preserve this appended module and both
packet references. The native event/name/size/record providers and complete
official fishing dialogue are installed in the current proposal. The tournament
host's eight affected calls and the imported stall's clip lifecycle are connected.
Winner-mail creation and delivery are connected. The measurement binding is
installed; calendar choice and event activation remain unfinished.

The 13,808-byte provider/host/mail module uses the existing fishing code reservation. It
converts native event records explicitly, preserves complete eight-character
record names, formats both units, and retains records when a provider fails.
All forty donor fish messages and their complete conversation branches form
74 installed messages and seven choices, retaining official pages and timing.
The single provenance catalogue credits each message, choice, and unit label.
The maximum expanded message is 995 bytes within the 1,024-byte buffer.

The text bank grows by 29,456 bytes into a verified unloaded duplicate of the
holiday packet. Startup descriptors distinguish virtual from physical addresses;
the loaded combined packet stays intact. Controller and text-reader core edits
are merged, and the connected Harvest pickup resolver is relinked while its
public entries stay fixed. No artwork is reconverted or old ROM file overwritten.
The sanitized provider check and current-cartridge service/text/startup/retention
check pass; empty/mixed/all-191 browser/offline outputs agree. Unchanged storage
and source-lifecycle evidence is retained. Fishing service admission remains
closed, and this does not establish native tournament gameplay.

The native host retains its original dialogue/demo/handover state machine.
The imported clip maps all donor fish while keeping native herabuna `2301`
distinct from brook trout `2328`; the native path remains the fallback when the
imported stall is absent. Actual winner assignment captures the complete record.
Removing the imported stall restores the previous native clip without clearing
another owner's replacement. The accepted V2 alias table resolves legacy winner
names, and display-only recovery preserves their original saved keys.
The expanded sanitized host check and current-cartridge eight-call/relocation/
alias/startup check pass. Empty/mixed/all-191 browser/offline outputs agree.
Native gameplay is not newly executed; the fixture budget remains exhausted.

Tournament winner mail uses all four official weekly templates from the existing
English catalogue and its twelve existing provenance entries. Both complete
donor reward lists map 103 candidates, including nineteen optional imports, to
their actual native identities. Selection prefers uncollected furniture and
filters disabled imports. Native notice completion attempts delivery independently
of the stall's lifetime; an accepted home/post-office delivery acknowledges its
record, while full/rejected queues, unavailable memory, or failed text generation
retain it. The saved letter contains a complete validated English snapshot and
prize, using ordinary mailbox storage. No new saved format or packet is needed.
The expanded sanitized host check uses the real catalogue reader/formatter and
record codec, with only native I/O doubled. All four letters, both delivery
routes, rejection/retry, and duplicate prevention pass. The current-cartridge
connection/retention check and empty/mixed/all-191 browser/offline outputs pass.
The native delivery hook remains behind fishing service admission; installation
does not claim an active tournament or hardware verification.

Tournament measurements use the shared behaviour-choice framework: N64
centimetres or GameCube inches. An existing event or pending winner retains its
stored units; a new choice applies only to an empty event with no pending
records. The saved format and packet allocation are unchanged. The sanitized
selection/retention check and current-cartridge binding/checksum check pass.
The definition stays unavailable in the selector until tournament actors and
mail delivery are admitted together; it is not a nonfunctional selectable toggle.
The separate donor announcement/speech handover is installed in the same packet.
The 6,096-byte combined module preserves all fourteen original demo identities and adds
alternate announcement 14 and speech 15. Its 23 native connections include
request priority, saved announcement/resume, speech readers, shrine/interpolated
camera return, and actual return-door acceptance. A rejected return retains the
announcement for retry. The original callback tables and unrelated code remain
unchanged; no new allocation or saved format is needed.
The focused sanitized host sequence and current-cartridge hooks/bounds/retention
check pass, as does current empty/mixed/all-191 browser/offline composition.
The same module contains live signed-acre/pool-shape readers, the existing
console-request gate, and relocated native room tempo/gyroid capture. Return
state is committed only after scene acceptance. A focused sanitized check
passes with native I/O doubled; source comparison confirms that all three
mainland climate states retain the N64 mainland result. The current-cartridge
check and empty/mixed/all-191 browser/offline comparison pass. Native gameplay
is not claimed. The 7,584-byte transition module binds these providers to the
actual expanded event-status directory and existing eighteen-decoration resolver.
All fifteen original N64 layouts retain their native collision reader and
priority relative to the source layouts; both native moon events and the null
Halloween layout keep their meanings. Focused source/host/current-cartridge and
browser/offline checks pass. Remaining actor and effect services,
and calendar selection/admission remain unfinished. The separate Groundhog ceremony is outside
those scheduled owners; its prepared controller stays inactive and does not
block diary attendance.
Reuse completed fishing and demo paths; do not restart native fixtures.

Two sanitized host checks, the current-cartridge/storage/startup check, and a
current-packet controller-refresh check pass. Empty/mixed/all-191 browser/offline
outputs agree. Native I/O is doubled; no native gameplay or FlashRAM execution is
claimed. **New experimental saves use format 13. Compatible older saves migrate
forward, but V2 and format-12-or-earlier V3 cannot load newly written saves.**
Existing saves and both deployed patchers are untouched.

The right fireworks stall uses the checked seven-entry projection bound. The
renderer retains both donor shadow passes, independently selected digit textures,
scrolling, joint colours, and frame-phase updates. Fishing-record/text consumers,
Harvest profile/save admission, and event activation remain unfinished.
Fishing/Harvest service admission remains closed; live event activation remains
disconnected for the whole batch. Installed controllers do not make these events
or diaries playable, and native gameplay/rendering have not been verified.

The retained lifecycle/owner/startup check passes on its recorded input build. It covers all
eighteen records, eleven profiles, source-controller references, four exact native
hook changes, all foreground identities, native marker consumers, the source
draw-state tail, retained resources, and unchanged save/profile data. Private
browser/offline empty, mixed, and all-191 compositions agree. Unchanged conversion
and renderer evidence is retained, not replayed.
No native fixture or old build is executed. The
[decoration contract](../specs/V3_DIARIES.md#shared-event-decoration-resources)
records the actual source/native layout differences and the next connected owner.

The shared hourly event path connects the donor sports-ending rules, original
N64/camper activation and cleanup, and persistent transient sports state. Both
native reset callers initialize that state to `-1`; scene changes do not reset
it. Dedicated owners have a shared-state entry instead of callback-local copies.
The complete 6,592-byte collision/escape/fade module is installed unchanged from
its prepared output. Its 16-KiB packet extension has checked startup transfer,
CRC, instruction-cache invalidation, and retained prefix resources. The transition
retains its original 48-KiB prefix inside the expanded holiday packet; no saved
field or format changes.

Two focused source/host/current-cartridge checks pass, including the actual
reset instructions, donor sports comparison, native cleanup, and startup
descriptor. Empty, mixed, and all-supported browser/offline compositions agree.
Native I/O and unfinished services are doubles; no in-game execution or newly
playable diary is claimed. The scene/gate/climate/rhythm providers, alternate
announcement lifecycle, and live owner dispatch are installed. Remaining work
is participant/controller/effect behaviours and calendar choice/admission. See the
[transition contract](../specs/V3_DIARIES.md#shared-transition-and-native-scene-bridge).
Selection profiles are unchanged; the current format-13 compatibility boundary
is stated above. Native reload is not newly verified. Existing saves/builds and
the native test budget are preserved.

The complete dedicated-owner code, native primitive adapter, and all shared
event layouts are installed in the existing holiday packet. The placement
adapter uses the checked `8010EF90` game-context pointer; its shared owner and
saved-state lifecycle are relinked together while retaining public entry
addresses. Sports callbacks reach the existing native acre-transition lock,
including its unchanged player consumers. The event-announcement initializer
uses the full donor mapping and preserves native door/camera/timer setup.
Twenty-eight announcements reuse installed English; four additional official
messages have individual source credits. Reviewed shrine wording is retained.

Five focused checks pass: source/host announcement comparison, connected
cartridge/startup bindings, shared native-pointer guards, complete owner/layout
host dispatch, and current browser/offline empty/mixed/all-supported composition.
Native I/O is doubled in the host checks. No native fixture is restarted.
No diary becomes selectable: participant/controller/effect identities and
behaviours, costume/exercise actors, and calendar behaviour choice remain required.
The [shared owner contract](../specs/V3_DIARIES.md#reserved-layouts-and-dedicated-owners)
records the connected work. Saved format/profile and resident allocation are
unchanged; gameplay and hardware verification remain open.

The same diary category now has the connected holiday conversation, movement,
calendar, and reward kernels installed with the actual native player/inventory/
trophy bindings. All 65 donor reward candidates map to their installed records;
diaries resolve to carried IDs rather than cover furniture, and the bottled ship
uses its reserved additive identity. Both selection fields must be enabled.
Actual handover calls the existing native insertion/collection path and only
then marks the active resident's trophy. Visitors cannot write resident state;
pointer/slot mismatches, full pockets, and stale selections reject delivery.
The native lifecycle bridge calls these services. The event scheduler and shared
owner lifecycle also reside in the existing packet: 49 source schedule rows,
44 owner records, live RUN/SHOW priority, and source cleanup selection. Calendar
planning, shrine/wandering/costume placement requests, event start/stop, and acre
entry/exit are connected through the shared owner interface. Native daily storage
and its readers are expanded together to 64 rows and 80 manager references. The
camper retains its own event and uses the same expanded directory. The manager's
capacity check precedes its write, fixing the original delay-slot overrun.
All 44 donor owners have fixed additive IDs, with a transactional native insertion
bridge and live status/cleanup mapping. The native manager's 73-row directory
retains all 29 native/camper controls and connects all 21 shared shrine/wandering
owners to actual field, reservation, terrain, spawn, and culling services.
The donor search order, shrine margins, and nearby height checks are preserved.
Separate imported keep flags reset with native common state without extending
an unknown native array. Dedicated callbacks explicitly reject while unfinished;
Halloween does not substitute ordinary Tortimer for its costume actor.
NPC event/field observations, actual shrine lookup, mapped race-position reading,
and cleanup are installed. The outdoor clip is checked against its live relocated
owner before binding; imported New Year cleanup uses a separate reserved Miko
profile and cannot remove native Miko. That imported actor remains unimplemented.
Placement reads the shrine at manager offsets `22C/230`, not the pool at `214/218`.
The event-world provider supplies actual saved Town Day, source harvest dates,
and lighthouse vacation state. The complete prepared NPC lifecycle links against
the installed motion, dialogue, world, observation, and date/state services.
The native calendar caller uses the real date/state provider, preserving camper
scheduling, the working-player gate, and native cleanup/hourly dispatch. All four
NPC profile callbacks reach the linked lifecycle. Its actor stays inactive:
event-specific actors, the calendar behaviour choice, and the separate exercise/
card conversation remain required. Installed code is not
a claim that Tortimer or any diary is playable.

The shared holiday state occupies the versioned diary header without moving any
calendar or page. Current saves preserve the full town, four players' console
progress, and all 48 pages. Compatible old saves migrate forward, including
formats eleven and twelve; earlier readers cannot load new format-13 saves. Existing
ROMs/saves and both stable patchers remain untouched. A sanitized connected host
check covers actual edit/preflight, save/reload, migration, rejection by the old
reader, date/quest state, and the calendar caller through actual planning/native
directory code. The current cartridge check verifies all 25 stable-entry
redirects, the native caller and four profile callbacks, retained NPC resources,
and the eighteenth startup packet.
Browser/offline empty, mixed, and all-191 compositions agree. Native diary/holiday
gameplay, FlashRAM execution, and hardware remain unverified.

Three current focused checks pass: all 44 mapped observation/cleanup paths and
clip/resource rejection; 54 comparisons with complete donor search functions,
the corrected native landmark decoder, and all 21 shared owners; and current
packet/linker/relocation/resource retention. Host checks use address/undefined
sanitizers; native shrine, save-record, actor-search, terrain, and spawn calls are
doubles, not native execution. The unchanged common-reset instruction check is
retained rather than replayed. Current browser/offline empty, mixed,
and all-191 compositions agree. No native fixture is restarted. The connected
path remains the same unfinished diary-category task, not a new release.

Three retained directory checks pass: installed readers and relocation/
resource retention; sanitized all-owner admission, capacity rejection, status,
and cleanup; and execution of the changed MIPS capacity branch with delay-slot
handling.
The 1,360-byte bridge, 256-byte identity map, and expanded temporary storage use
the existing packet. Profile bits are unchanged; the saved holiday state uses
format twelve as described above. Preserve existing saves. No native fixture is restarted,
and native diary gameplay, ordinary save/reload, and hardware remain unverified.

Retained event checks cover sanitized calendar boundaries,
all 28 priority/cleanup comparisons against the complete donor functions,
placement/culling failure handling, and scheduled owner → accepted conversation →
attendance → guarded reward delivery. Placement and event I/O are host doubles.
The source event kernel remains unchanged: its 3,824-byte code and 812-byte
source packet use existing reserved RAM. The state extension retains these
components, profile identities, and all sixteen inactive diary selections.
No native fixture is attempted.

One connected sanitized host check passes all 65 candidates and 128 handovers,
four-player trophy isolation, visitors, repeat delivery, full/stale inventory,
and resource gates. Retained world cartridge/manifest checks and browser/offline empty,
mixed, and all-191 compositions pass. The exact appended-choice resource hashes
and reader changes repair the stale choice-bank manifest without weakening the
build guards. No native fixture is repeated, no new style is selectable, and
these results do not establish native diary gameplay or save/reload.

The active diary category has a source-bound calendar → read → edit → finish →
privacy controller for all sixteen styles and all 48 monthly pages. Capacity
admission covers the page and lock together; rejection keeps the draft and old
saved contents. The actual surface A-tap adapter resolves the resident from the
house owner ID and preserves native furniture handling when no selected diary
is present. The shared carried model is converted, and official prompts plus
project safety messages have per-text provenance. Preparation is
`build/v3-diary-category-work-01/prepared-05/`; the linked MIPS save/calendar/menu
core is 22,544 bytes. The calendar matches the donor C in focused host comparisons.
The adapter and controller pass a combined sanitized host check across all styles,
all player access modes, navigation, privacy, and rejected edits. These are not
ordinary native gameplay results.

The shared screen packet retains all twelve calendar/diary month labels, 31 day
numbers, year digits, backgrounds, paper, controls, and prompt graphics. Preparation
is `build/v3-diary-category-work-01/screen-04/`: 144,240 bytes, 148 shared resources,
and 141 native drawing/loading lists. All 118 texture resources have individual
official-source credits in the single provenance catalogue. The native drawing
functions and full-page keyboard adapter compile for VR4300. The focused keyboard
check covers proportional rows, full pages, Rewrite, ownership, and unchanged
ordinary keyboard dispatch. The screen conversion checks complete resource/load
bounds, caller tables, and rejection of missing state. The screens and hooks are
installed in the experimental cartridge, but not visually verified.

The shared native menu owner is linked at
`build/v3-diary-category-work-01/ui-06/`. It connects opening, calendar/read views,
scrolling, the actual keyboard child, first-A answer reveal, Rewrite, privacy,
capacity rejection, closing, and session cleanup. The paper and text share the
same scrolling position; the cursor uses proportional glyph positions. The
keyboard adapter retains blinking and character alteration. The linked UI and
native entry/calendar adapter occupy 18,416 bytes, with 2,240 bytes of screen state
and 488 bytes of native context. Installed HBOARD and keyboard
hooks add 1,600 bytes to the native menu arena and preserve unrelated existing
code/graphics at two relocation addresses. Three focused source/compiler/host
checks pass, including the connected interaction with rejected and accepted
commits. Native UI execution and visual verification remain pending.

The native entry resolves all sixteen selected styles, actual house/player
identity, owner birthdays, real RTC dates, current proportional glyph widths,
and the full-town save preflight. Its separate 48,048-byte candidate buffer at
`806D4000` cannot overlap the save compressor's workspace. The calendar uses the
checked N64 holiday schedule and lunar conversion, with bounds protecting the
adjacent browsing years. Twenty labels have source credits, including seventeen
official-source labels and three reusing explicitly assistant-authored N64 text.
The installed play-day hook retains the native title/player-select/demo gates and
live-player result. Actual event-participation callbacks remain unbound.

Four focused checks pass: current linked packets/hooks, the combined native-data
entry/calendar host check, and retained donor-calendar comparison. The host check
covers 420 months, lunar boundaries, all style bits, separate owner birthdays,
overlapping holidays, and guarded preflight. The converted screen/carried artwork
is reused. These are host/compiler results, not installed native gameplay.

The shared builder installs diary menus, room/visit hooks, three guarded resident
packets, and format-eleven storage together. Its sixteen-packet startup occupies
600 of 688 reserved bytes. Both stable save exports and direct calls from the
insect runtime reach diary-aware storage, preserving canonical-codec bodies and
existing artwork. Three focused checks pass for the current cartridge, including
native menu relocation, unchanged surrounding code/resources, packet checksums,
and sanitized startup failure gates. They do not establish native UI/save execution.

All sixteen diary styles have additive carried identities (`2B10..2B1F`) and
installed shared names, prices, categories, placement/pickup conversion, collection
record/check routing, and pocket icons. The original native `2B00` remains intact.
The room A-tap predicate uses those destination IDs. Official name credits live
in the single provenance catalogue. The 16-KiB guarded packet reuses the complete
carried model; ground, police storage, and handover use its category artwork.
Expanded seasonal descriptor banks follow the retained scenery allocations,
without changing scenery code, resource contents, or bank addresses. Startup
loads sixteen checked packets in 600 of 688 reserved bytes.

Four focused checks pass for the current carried cartridge and sanitized host
readers/startup/ground tables. The connected menu/surface host check passes for
all sixteen additive IDs. Existing creature reader validation recognises the
outer diary hooks and retains the original reader bodies. The complete menu
capacity check includes the diary arena reservation. These are build/host results,
not native diary gameplay, save/reload, or hardware verification.

All sixteen distinct covers are installed together for loose-room drawing and
catalogue previews, using the existing converted artwork. The 35,616 artwork
bytes are stored once in the expanded Shop_Goods owner; its loaded room copy
rebases resource pointers, while catalogue DMA retains segment-six pointers.
The original 34 room rows, native BSS, DMA indices, rotation exports, and unrelated
resources remain intact. The complete owner is 41,424 bytes, with 1,648 bytes of
room adapter code inside the existing diary reservation.

The shared catalogue includes donor ordering, special framing, and parent prices
for all sixteen styles. Source-derived HRA/feng-shui metadata is installed. The
400-byte diary clutter adapter exempts a selected diary on a table, while
retaining the donor's floor penalty and other item handling. The catalogue's
menu allowance grows by 256 bytes; retained diary/clothing/model allocations
are checked together. No profile is enabled by these changes.

Four focused checks pass for the connected room-art and catalogue steps:
complete current resources/profiles/relocation, all-style rotation and resource
rebasing under sanitizers, actual catalogue/scoring/CRC/allocation bindings, and
sanitized framing/prices/selection/clutter behaviour. These checks do not prove
native rendering, ordinary diary use, save/reload, or hardware compatibility.

The installed diary bindings connect every carried parent to its cover, single
save-profile bit, catalogue ordering, and scoring. Browser and offline composition
agree for empty, mixed, and all-supported selections on ABI 316. Prepared diaries
remain unavailable, including under select all; inactive catalogue/scoring rows
are removed from composed builds. The shared save/profile host check uses real
carried readers, selected-style resolution, canonical codec, and format-eleven
storage. It preserves independent ownership and pages for four players and
rejects a missing style without changing live/save data. Two focused Python
checks and eleven browser-engine checks pass. Native graphics and FlashRAM
execution are not established by these host/device-double checks.

The shared save adapter retains the complete town, console progress, calendars,
and pages within the existing two FlashRAM banks. Actual participation callers,
ready-choice activation, and connected native UI/save verification remain in the same
[diary consumer map](../specs/V3_DIARIES.md). No diary choices are enabled yet.
New format-eleven saves require this or a newer compatible build; earlier V3
and V2 cannot load them. Both deployments remain V2-14, and the user's saves
are untouched.

The current diary native check stops before opening a menu. Both permitted
setup attempts are terminal: the general allocation returns zero, and the
corrected title-context arena has no free space. All four resident packets match
the current ROM and its initial fault pointer is zero. Menu/editor/save execution
remains unverified; the [recorded result](checkpoints/V3_DIARY_NATIVE.md) keeps
those limits explicit without another title-fixture retry.

The shared Tortimer conversation source connects all 28 holiday branches to
calendar attendance and guarded reward delivery. First/repeat/claimed visits,
visitors, full pockets, vacation callbacks/dates, and duplicate handover handling
are implemented together. Four focused host checks pass, including the complete
donor conversation comparison and the donor calendar query comparison. The
VR4300 controller compiles with explicit diary/reward/library link dependencies.
The controller is not linked into an active actor: Tortimer's event owner,
live world/reward bindings, cleanup, and exercise-card route remain necessary.
The complete official dialogue group and native transport are installed in the
current proposal: 347 messages, four choices, all 31 ordinal dates, and 29 event
labels, with 411 per-text credits in the single provenance catalogue. Branch IDs
are remapped together; wording, manual lines/pages, pauses, and demo orders are
retained. Two donor dash glyphs use the halfwidth hyphen, explicitly credited.
The largest expanded message is 867 bytes within the existing 1,024-byte buffer.
The native transport uses actual continuation, turn/camera, listen/start, complete
16-byte item/event fields, and PUTAWAY handover orders. No inventory award is
duplicated in the transport. Source/cartridge checks, sanitized connected
conversation/reward/transport checks for all 28 events, and browser/offline
composition pass. Native conversations remain unverified; no diary is enabled.

Tortimer's complete model and expressions are converted within the existing NPC
buffers, with no discarded source pixels. The shared per-material texture path
retains geometry, face choices, wrapping, and render state, and keeps the native
4-KiB preload inside its bank. The native drawing adapter preserves ordinary
NPC/accessory handling and restores graphics segments. Six focused checks pass,
including current owner hooks and sanitized expression/bounds handling; the
adapter compiles for VR4300. These components are installed through the shared
registry and resource loader; native rendering is unverified.
The [actor connection notes](../specs/V3_DIARIES.md#tortimer-artwork-and-native-actor-connection)
identify the remaining lifecycle, event scheduling, and message/demo
consumers. Diary choices remain inactive; saves and V2 deployments are untouched.

The full fifteen-state Tortimer movement controller connects to the existing
conversation, diary attendance, and guarded delivery code. A combined host check
compares the complete donor think file and exercises request → conversation →
attendance → delivery → resumed movement. The native lifecycle bridge supplies
the checked N64 callbacks, actor fields, requests, and real demo-end/delivery
signals. Both VR4300 objects are prepared at
`build/v3-diary-category-work-01/tortimer-dialogue-02/actor/`, not linked or installed.
They call the installed motion and English dialogue exports. Timed pauses
consume elapsed 60 Hz ticks rather than doubling in duration at native 30 Hz.
The remaining services are the event owner, live world/reward data, cleanup,
and separate exercise/card integration.
The actor needs 2,612 bytes; the ordinary NPC pool rejects sizes above 2,400,
so it uses a separate guarded pool instead of growing the original nine slots.
Diaries remain unavailable, and no native gameplay is claimed.

The shared actor installation connects descriptor/allocation/free, complete
drawing in both NPC owners, full voice 281, and model/texture banks 448/449.
The 64-KiB resident packet holds two 2,612-byte actors in guarded 2,656-byte slots,
3,984 bytes of linked dispatch/drawing/loading code, and the complete 912-byte
cane motion. Its lifecycle callbacks and readiness flags remain unset until the
event/conversation providers are connected. Allocation rejects inactive records;
cleanup preserves the native actor body and original NPC slots.

The complete 13,584 artwork bytes use checked external physical-ROM storage and
virtual banks `03FE0000`/`03FE4000`, keeping existing item storage intact. The
ordinary DMA worker handles both sync/async object loads and retains its message
notifications; its hook activates only after the resident packet passes startup
verification. Audio DMA is unchanged. The seventeen-packet startup uses 644 of
688 reserved bytes. Object capacity and the startup header agree at 450.

Four focused build/host checks pass, covering complete resources/hooks/startup,
allocation/free/guards, transfer bounds/failures, and original fallbacks. Ten
shared keyframe checks pass, including all cane channels and its complete timing
record. The current browser/offline comparison passes empty, mixed, and all 191
supported choices while keeping all diaries inactive. No native fixture is run.
The saved format/profile is unchanged from the preceding diary proposal; native
save compatibility is not newly tested. Format-eleven backward incompatibility
with V2 and earlier V3 remains. The next work is the same actor-provider connection,
not another allocation or artwork conversion pass.

The installed shared motion adapter occupies 2,016 bytes inside the existing
actor-code reservation. It preserves the native main/face animation and bank
ownership, then initializes the complete cane channel and retains the donor's
arm/mouth joint selection. Native wait/clap motions match all donor channels and
controls. Walking keeps native collision/path/interruption handling while using
the donor's walking-only probabilities and block-edge initialization. Ordinary
NPCs use the original functions. No art, actor slots, saved format, or profile
changes are required.

Focused sanitized checks compare walking decisions and timer states with the
actual donor C, including pause boundaries; they also cover cane arguments,
block edges, and ordinary fallbacks. Installed hooks, relocations, trampoline,
retained resources/guards, and current browser/offline composition pass. The
controller and lifecycle bridge compile with the new bindings. These checks do
not establish native animation, gameplay, or hardware behaviour. Diary choices
remain unavailable until the event/conversation/exercise path is connected.

Both source artwork variants, school desk and bus stop, are installed through
the ordinary shared importer. Complete original-N64 profile/model comparison
establishes different geometry, with the original items retained. The 7,840
converted bytes, official names and prices, B/C stock, catalogue/scoring, saved
profile bits, and independent browser choices are connected. Source/build checks
and five browser/offline profiles pass. The save codec, resident furniture loader,
and palette runtime are unchanged; ordinary gameplay and saving with these items
remain unverified. Profiles lacking the selected variants are incompatible with
saves that use them. Preserve backups.

The shared representation catalogue identifies sixteen saved-design forms and
nine museum placeholders rather than treating them as fixed missing furniture.
Their complete source consumers bind inventory, scan, and browser review data.
Three focused tests cover classification, malformed-source rejection, and shared
consumer behaviour. The custom-design editor/saved-pattern feature belongs to
V4 and does not block V3 imports. See
[the representation contract](../specs/V3_ROOM_REPRESENTATIONS.md).

The complete clothing category is installed together. All eight distinct donor
appearances use shared loading, official names/prices, player/NPC outfit readers,
reversible mannequins, catalogue/scoring, real stock seasons, save-profile bits,
and browser/offline selection. The native puzzling shirt remains alongside its
optional donor variant; the G logo shirt appears in summer stock only.
The converter accounts for all 255 named donor garments, including 247 existing
native appearances, and reuses `build/v3-clothing-category-work-01/prepared-02/`.
Mannequins are representations of their carried garments, not separate choices.

Three focused current-build tests pass: complete resource/stock/profile/hook/UPS
checks, five matching browser/offline selections, and sanitized readers covering
all eight garments, mannequin DMA in every rotation, all stock groups/months,
and twelve-packet startup including failed transfers/checksums. A real composed
summer-shirt build also succeeds. The shared startup uses 504 of 688 bytes,
including its new descriptor table; clothing adds 4 KiB of reserved resident
memory and 128 bytes to the actual catalogue menu allocation. Saved format nine
is unchanged. Profiles missing selected garments/mannequins reject those saves;
preserve backups. Ordinary gameplay, shop purchases, save/reload, and hardware
remain unverified. See [the clothing contract](../specs/V3_CLOTHING_IMPORTS.md).

One silent native run at `build/v3-clothing-category-work-01/native-01/` passes
80 records and 50 assertions. It exercises the current cartridge's startup and
actual clothing DMA for all eight imports plus an original N64 garment,
disabled-record rejection, saved-state preservation, guards, and checkpoint
restoration without a CPU fault. It does not establish ordinary gameplay or
save/reload. Clothing reader tests remain retained rather than repeated while
the diary category is implemented.

The complete insect category is installed together: six full donor programs,
calendar/habitat/group spawning, collision, the ground ant colony, field sounds
and water/mud effects, player rock/dig/tree events, mosquito responses, both full
player motions, bounded face timelines, official dialogue, and persistent seasons.
Its controller retains native actor sizes and extends allocation, graphics
reload, movement, drawing, and cleanup to nine slots with independent code buffers.
The N64 population choice keeps two wild insects and its proximity exclusion;
GameCube uses eight wild insects and source groups. Both have a separate release
slot. The choice is connected to the same private browser/offline composition
rules as individual insect inclusion, parent/display identities, scoring, and
saved-profile bits. Empty/default selections still produce stable V2-14.

The 96,880-byte insect runtime/guard packet is allocated in reserved Expansion Pak
RAM and stored in checked physical ROM space. Shared startup verifies complete
transfer/checksum/cache ordering before entering the game. The common importer
moves the complete regenerated catalogue/shop owners outside the nearly full
item-data area and retains 8,592
bytes of checked reusable padding. Existing artwork, names, console resources,
and both native/imported species identities are preserved.

Current cartridge/resource/planner checks pass, as do six matching browser/offline
profiles: empty, select all, all insects in either mode, one insect, and population
changes without imported items. Focused sanitized checks cover both population
limits, independent buffers, releases, profile rejection, all eight behaviour
programs, the changed controller adapter, and the expanded startup chain.
The earlier save/migration, audio, player, colony, and graphics checks remain
retained evidence; they are not repeated as new native tests.

This build writes format-nine compressed saves (canonical eight, registry five).
Valid older saves migrate forward; V2 and earlier V3 builds cannot load its new
saves. Preserve backups. Native scene-bank capacity, ordinary creature gameplay,
save/reload, and hardware remain unverified. The fish constructor timeout and
sound-scheduler disconnection remain unresolved, not waived or labelled harmless.
The creature path still requires those native consumers and fixes for any real
defects found, without restarting exhausted fixtures. This is an experimental
development build, not a playtest handoff or deployment approval. See the
[insect contract](../specs/V3_CREATURE_ITEMS.md#added-insect-behaviour-programs).

Four additional paintings use the ordinary shared importer: full models, original
shop/event lists, catalogue, scoring, official names, and fixed additive IDs.
The shared native-profile stage also installs 49 complete objects independently
of acquisition: direct models, seating/beds, constant model sequences, flowers,
and palette-fading building models. These retain 183,408 artwork bytes; 48 models
reuse prepared conversions and one compiles through the common batch compiler.
No new per-item installer, callback code, resident reservation, or saved format
is introduced. All names have official-donor credits in the single catalogue.
See the [bulk-profile checkpoint](checkpoints/V3_BUILTIN_PROFILES.md).

The complete console image/save/disk/room integration is installed. A silent
54-record native scenario at `build/v3-console-combined-native-01/` verifies
Clu Clu Land D and Wario's Woods execution and title rendering, native Reset
with required RAM retained, and native cleanup with no CPU fault. Disk work RAM
advances between observations. Reset requests use test-only menu writes; cleanup
uses the actual native return request and stops before loading an uninitialized
town. Ordinary room entry/world return, user-controlled play, save/reload with
these games, audible quality, and hardware remain unverified. The checked code
and resources are retained in the current proposal, so this evidence does not
require replay for the data-only model stages.
See the [console checkpoint](checkpoints/V3_CONSOLE_ROOM.md).

The shared converter prepares 17 complete creature displays: sixteen animated
rigs and the three-layer static ant. All 78,544 bytes, 96 joints, full motion
arrays, and three sound-callback dependencies are retained. Actual source
placement/pickup functions establish carried-parent identities and official
names. These are not seventeen playable imports. All sixteen animated objects
(74,672 bytes) and the shared embedded-rig callback are installed. Nine fish
and eight insect profiles participate in private composition through their
installed field behaviours and spawning.
The shared native dispatch preserves creature animation in placement/removal
states 6 and 13 while retaining other furniture's callback exclusions. Sanitized
category checks and current cartridge/resource/UPS checks pass; ordinary native
creature gameplay is not claimed. The dispatch adds no allocation or save change.
Complete frog, mole-cricket, and mosquito sound programs and three instruments
are installed through the shared importer, including the original pitch bend and
envelopes. Wave data grows by 69,824 bytes and the audio heap by 1,024 bytes.
Two current resource/planner checks and the focused bend-parser check pass.
Native creature-sound scheduling and callbacks are installed, with the complete
17-entry sound/delay tables, all five added programs, and original per-instance
timing. The 68-byte arrays use an existing startup-loaded reservation; the two
additional programs need no new instruments, waveform data, or heap growth.
Three current resource/guard/planner checks and the sanitized callback check pass.
The bounded native attempt disconnects before assertions, so native execution
is inconclusive, not passed. Existing creature sounds and saved formats are
retained; no audible test is performed.
All seventeen room profiles are installed, including the complete static ant.
One shared adapter connects fixed carried identities, official names, prices,
categories, placement, and pickup, with brook trout at `2328` and native herabuna
preserved at `2301`. The ordinary category pipeline reuses all seventeen prepared
models without graphics compilation. Three focused tests pass, including two
sanitized C fixtures, installed-resource/hooks/UPS checks, and all/empty optional
composition. The 3,840-byte reader packet adds no save change; the shared startup
fits its existing reservation. Fish per-species composition is connected to the
carried and displayed forms, saved profile, and packet checksums. Added insect
field behaviours remain required; native connected-path execution remains unverified. See the
[creature checkpoint](checkpoints/V3_CREATURE_PROFILES.md).

The carried/field graphics category is prepared at
`build/v3-creature-field-prepared-01/`: all seventeen species, 59 frame references,
43 distinct models, and 25,504 bytes. One batch compiler invocation handles the
whole category. Shared conversion now retains separate frame vertex arrays and
the insects' environment-alpha fading. Six focused checks pass, including full
resource/frame bounds and unchanged reuse of the existing room artwork. These
field graphics are installed through one checked physical-ROM loader and shared
resident tables, with native actor/buffer sizes retained. Fish capture/release
mapping preserves rubbish, coastal salmon, and herabuna. The added insects use
source held/world poses, and release shadows include safe XXL entries. The
[creature contract](../specs/V3_CREATURE_ITEMS.md#connected-native-field-stage)
owns layout and verification details. Two focused tests pass, including sanitized
loading/transforms/startup, all resources/relocations, shared planning, UPS, and
all/empty composition. Native execution verifies all nine added fish transfers
and segment bases through the actual field loader. The constructor-window check
times out; its cause is unresolved, and later checks do not execute. Insect
transfers, ordinary gameplay, and GPU rendering remain unverified.

The shared fish world stage connects all nine size/search/bite records to the
river and coastal owners, including XXL river parameters/effects. Added coastal
fish have donor-sized approach/nibble speed, distance, wait count, backing speed,
shadow scale, bobber correction, rubbish selection, and splash/ripple parameters.
Constructor dispatch selects the coastal owner for the added sea species.
Capture-to-release creation maps real carried IDs, keeping rubbish separate from
the added fish. Original fish values and golden-rod hooks are retained. A transient
origin byte retains imported behaviour if a hooked fish becomes rubbish.
The code and tables occupy existing field-packet padding: no new ROM resource,
resident allocation, actor growth, or save change. Two focused host tests cover
the readers, source arrays, relocation, preservation, planning, and optional
composition. The constructor timeout is not classified as a game or harness bug;
do not loop on the exhausted native fixture or claim the new hooks passed it.
The connected fish task includes an installed world packet containing complete
donor calendars, seasonal blending, weighted selection, spawn-position scanning,
and shared native-bound terrain checks. Brook trout and native herabuna have
separate records. Six coastal callbacks connect donor patrol/wait/escape code
with preserved original-function fallbacks. The GameCube calendar now reaches
the native spawn-manager entry, terrain selection, and native fish creation.
The town's season/transition fields persist alongside independent collection
records and profile bits for all seventeen additions. The N64 alternative adds
selected donor fish while retaining the complete native manager for original
species. Its 100-weight native opportunity competes with actual donor seasonal
weights; source mode uses the complete donor population and saved seasonal blend.
The private offline/browser composers expose population and imported coastal
movement settings separately from item selection. Both default to N64 and bind
to real runtime alternatives; receipts record the resolved values. No deployed
patcher is changed.
Native catch recording, prospective final-catch checks, and completion dialogue
include all selected additions without aliasing original 32-bit records.
All seventeen complete pocket icons retain their two donor palettes. The 9,792
artwork bytes and 152-byte descriptor table use existing world/save packet
padding, with no new RAM or ROM allocation. Original icons, tool/gift paths,
native herabuna, and existing model assets remain intact. Collection drawing,
navigation, and names cover all 41 fish and 40 insects in a nine-by-five grid.
All seventeen complete official catch messages retain line/page breaks, timing,
and effects, with source credits in the single catalogue. The 880-byte UI reader
and 240-byte table fit the existing world packet. The complete English text
region moves into verified unused ROM space because its original end is occupied;
no existing owner, artwork, or save layout is overwritten.

Three UI/text checks pass on ABI 301, covering every collection identity and
catch-message route, complete official bank preservation, hooks/relocations,
patch reconstruction, and optional composition. ABI 302 retains those complete
resources and consumers. Three current behaviour checks pass, including five
matching browser/offline profiles, both runtime settings, empty/default V2,
nested checksums, invalid values, and retained save/assets. An actual offline
behaviour-only build also completes. New native execution or visual acceptance
is not claimed. All nine fish have fixed, independently selectable source
identities. Brook trout retains its separate N64 identity and native herabuna
is preserved. Three selection checks cover current actual parent/display tables,
four-player catch/save readers, rejection of a missing saved species, and six
matching browser/offline profiles. These checks do not establish native gameplay.

The shared passport adapter connects added catch records to visiting players
and restores them to the matching resident on return. A versioned, checksummed
48-byte record uses native passport padding without resizing private data,
animals, letters, or the Controller Pak note. A separate 28-byte visitor record
prevents writes to another resident's collection. The current cartridge adds
one 4-KiB world-packet extension; existing artwork and save codecs are retained.
Three current checks pass for installed hooks/packet/UPS preservation, six
browser/offline compositions, and sanitized travel across all seventeen identities
and four residents. Incompatible profiles, corrupt records, wrong identities,
and device errors reject; legacy returns preserve existing resident catches.
Complete donor house-rating and feng shui records use the existing shared
converter and native category mappings. Nine selected fish have installed
ratings alongside all eight added insects. Disabled creatures leave
rating-group searches through the same offline/browser selection writes.
No model, sound, saved layout, or resident allocation changes for scoring.
Native travel and other imports' catalogue/console transport remain unfinished
or unverified. This is not complete V3 travel support or a playtest handoff.

Three changed-path checks pass for both population modes, all seventeen native
catch/collection readers across four players, completion timing, disabled/foreign
record handling, all dual-palette icons, installed code/hooks, retained assets,
UPS reconstruction, and all/empty optional composition. The unchanged format-seven
save codec retains its forward-migration, deletion, capacity, and pre-write
rejection evidence; it is not rebuilt or replayed for these consumer changes.
The shared world/save
packet uses 48 KiB; the working save state includes 32 added creature bytes without actor growth.
This build writes format-7 compressed saves with canonical format six. Valid
older saves migrate forward, preserving existing collections and console data;
V2 and older V3 builds cannot read its new saves. Preserve backups. These host
and cartridge checks do not establish native execution or ordinary save/reload;
the constructor timeout and scheduler disconnect remain unresolved. Continue the
fish gameplay/save verification and classify those failures without restarting
the exhausted native fixture. Continue the eight insects' shared behaviour/spawn
programs using their installed resources. Do not replay old builds or recompile
unchanged artwork. Passport travel requires compatible V3 creature profiles;
V2 and older V3 readers do not understand its extension. Preserve Pak backups too.

Continue with creature parent/native integration and the remaining legacy
clothing and collectible fossil representations, not deferred V4 custom designs, resource reconversion
or obsolete test attempts. Complete genuine conversion/behaviour gaps.
The two worksheet-mapped school-desk/bus-stop
records require identity/artwork correspondence review, not automatic duplicate
IDs. Then complete the actual acquisition routes and gold-tree work, and
assemble a private combined playtest build.

The retained native console lifecycle is installed in ABI 278 at
`build/v3-console-emulator-native-01/build-lock.json`, ROM SHA-256
`5a714a18c3d6037f07bd9664bae456fcf85cd7ba290aebfe35370e42aea41ad1`.
Six checked native calls connect complete iNES image loading, expanded graphics,
initialization, frame/reset, and cleanup to independent player progress. Three
focused checks pass, including sanitized host-adapter execution for all eleven
additional iNES games, retained resources/relocations, and four private browser
compositions. Native CPU/graphics/audio are stubbed in the host check; native
gameplay is not claimed. See the [lifecycle checkpoint](checkpoints/V3_CONSOLE_EMULATOR.md).

The retained image-reader installation has its evidence in ABI 277.
All nineteen complete images use a separately tracked 770,144-byte ROM pool,
6,336-byte metadata, and a 1-KiB streaming input buffer. Six-packet startup,
resource preservation, physical allocation, and four private compositions pass.
Native ROM reads reproduce a complete iNES image and complete QD image with
guards and saved state intact; the scenario fails afterwards in fixture cleanup,
so full scenario success is not claimed. The helper is corrected without another
replay. See the
[streaming checkpoint](checkpoints/V3_CONSOLE_IMAGES.md).

The console converter prepares the full nineteen-game category and a shared
3,988-byte MIPS save engine at `build/v3-console-games-prepared-06/`. All sixty
recipes execute against four independent player saves. The full and streamed
representations pass 90,001 actual-donor/safety assertions for first/repeat play,
score restoration/reset, battery/disk capture, and Zelda checksums. Current source and
prepared-resource checks also pass. The donor needs 6,528 player-save bytes,
not one shared 1,623-byte payload. A common 3,368-byte lossless encoder/decoder
prepares the complete canonical bank and console bytes inside one 64-KiB
format-five bank, retaining the backup bank. Capacity is checked before output
writes; oversized input rejects safely. Sanitized checks and an independent
decoder pass; dense synthetic storage retains 5,151 spare bytes. This is not a
universal capacity claim. Native storage is installed in ABI 276 at
`build/v3-console-storage-native-04/build-lock.json`, ROM SHA-256
`f876fc31541db21297e6c5b27f62af790e32ea33850d700f15f3cdd1291f070f`.
It retains complete canonical town data and four independent console records,
with checked startup, non-mutating bank probes, decoded commit, migration, and
per-player clearing. Four focused host/cartridge/composition checks pass,
including 85,426 sanitized adapter assertions and all ten startup failure paths.
Actual native synchronous and asynchronous two-bank writing, followed by both
native load routes in a fresh process, pass. Room launch/return, real heap
capacity, native gameplay verification, and QD emulation remain work.
Format-five saves require this or a newer compatible build, and cannot be loaded
by V2 or format-one/two/three/four V3. Preserve backups before any handoff. See the
[console checkpoint](checkpoints/V3_CONSOLE_PERSISTENCE.md) and
[storage checkpoint](checkpoints/V3_CONSOLE_STORAGE.md).

The exercise integration retained by the current proposal is ABI 275 at
`build/v3-player-exercise-imports-01/player-exercise-native/build-lock.json`, ROM SHA-256
`a940dab0ff14f5fc0e0bed23c78d5500c874da7a9f269e89e321c0106453e205`.
The shared importer installs the complete exercise action: all 18 gestures,
chaining/exit, C-button input, source eligibility, both camera readers, real native
audio tempo/counters, and existing movement/collision/face/item updates. Two
gesture/animation steps run per native update; physics runs once. All twelve
complete motions and the existing radio music/artwork are reused unchanged.
Checked startup loads 4,192 packet bytes into an unused 8-KiB reservation.
The player actor grows by 48 transient bytes, with explicit constructor reset;
the scene arena is 610,736 bytes. Saved format 4 and 162 choices are unchanged.
Five focused checks pass, including 256 actual-donor eligibility comparisons,
all 18 host-adapter gesture/animation/exit paths under sanitizers, preload failure
handling, installed resources/hooks, and four private browser/offline compositions.
Native execution, ordinary appearance/synthesis, a new save cycle, and hardware
remain unverified. Continue console launch/storage importing work. See the
[native exercise checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#installed-native-player-exercise).

The radio's room-music lifecycle is installed through the ordinary importer.
All 5,152 prepared artwork bytes are reused. Source-equivalent music reservation,
radio/stereo exclusivity, constructor/destructor handling, source-rate note
emission, and rotated drawing are connected. The source track and four complete
instrument/sample bindings reuse native audio with the native volume mix.
Five focused checks pass, including 289 actual-donor lifecycle comparisons,
relocated owner hooks, preserved existing resources/saves, and four private
browser/offline compositions. This is not native execution or hardware evidence.
Room code uses 27,856 of 32,768 bytes; bootstrap uses 1,182 of 1,536.

The radio remains unavailable because its original reward route remains
acquisition work. Its indoor exercise interaction is installed and recognized
by the shared eligibility reader. Continue console launch/storage importing work. See the
[radio lifecycle checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#installed-radio-room-music-lifecycle).

The shared converter prepares the complete aerobics radio and treasure chest
together: 13,824 bytes, 174 triangles, all textures/palettes, nested model parts,
six chest joints, both distinct 51-frame motions, and three scrolling layers.
The ordinary importer installs the chest's complete native behaviour, including
room/contact readers, both mapped multi-instrument sounds, continuous sound,
destruction, and saved-state capture. Its retained implementation evidence is ABI 271 at
`build/v3-dual-motion-imports-01/profile-runtime/build-lock.json`, SHA-256
`a93384de48092aa3180f484602bc4fb57b0e0037635dbec6c8a4fc03025343e3`.
Installed-resource and four private browser/offline composition checks pass;
162 choices and saved format 4 are retained. The chest's island acquisition is
still pending, so it remains unavailable in the selector. The prepared core's
donor comparisons are retained, not relabelled as full native execution. A new
dispatch fixture stops at its two setup attempts before C execution; do not loop
on it. Native gameplay/rendering/synthesis, saving with this item, and hardware
remain unverified. See the
[installed chest checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#installed-dual-motion-lifecycle).

The ordinary category importer installs crab stew's combined reversible animation,
delayed fire textures, translucent joint, randomized steam, and complete audio.
All three models, 62 triangles, four joints, motion channels, and five on/off frame
entries are retained in 4,384 reused bytes. Its actual winter-camper route,
non-orderable catalogue entry, scoring, official name, and optional profile are
connected. Five focused checks pass: complete resources/planning, 8,008 donor
lifecycle comparisons and 4,000 host draw frames under sanitizers, installed
dependencies, four browser/offline selections, and the affected shared reversible
core. Native execution, ordinary rendering/audio synthesis, a save cycle with
this item, and hardware remain unverified. See the
[combined-effect checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#installed-combined-reversible-material-and-effects).
Continue console launch/storage importing behaviours.

The ordinary category importer installs the complete matryoshka: eleven joints,
five models, 85 triangles, and all 46-frame motion channels in 4,512 reused bytes.
Idle-only reversal, complete sound, destruction, native switch capture, actual
Gulliver rewards, catalogue/scoring, and official English provenance are connected.
Larger joint work fits unused matrix slots without growing the actor or saves.
Ten focused checks pass, including 1,440 sanitized move/draw updates, all eleven
bootstrap entries, complete installed resources, retained imports, and four
private browser/offline compositions. The existing 4,324 donor lifecycle
comparisons remain applicable to the unchanged core. Native gameplay/drawing,
audio synthesis, ordinary saving with this item, and hardware remain unverified.
See the [installed reversible checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#installed-reversible-lifecycle-and-save-capture).
Acquisition-only work must not displace the remaining importing behaviours.

The shared importer installs combined skeleton/timed-material behaviour for the
hamster cage: all five models and 61 triangles, seven joints, the complete motion,
both texture frames, and positioned loop audio. Its actual lottery availability,
catalogue ordering, scoring, official English name, and optional profile bit are
connected. Five focused checks pass, including 600 sanitized host motion/draw
frames, complete installed resources, retained dependencies, UPS reconstruction,
and four private browser/offline selections. Native execution, ordinary drawing
and audio synthesis, a save cycle with this item, and hardware remain unverified.
See the [combined-animation checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#installed-combined-skeleton-and-material-animation).

The shared material importer installs the harvest TV's complete switched-screen
lifecycle: both models and all 37 triangles, four timed on-frame entries plus the
off image, complete positioned loop and both clicks, and native start-disabled
placement. The audio converter retains the source lead-in rest and correct
envelope alignment for odd-address programmes. Thirteen focused checks pass,
including host draw/sound dispatch, complete donor asset comparison, installed
dependencies, unchanged saved data/profile bits, and private browser composition.
The profile stays inactive pending the actual Harvest reward route. Native
execution, ordinary GPU appearance/audio synthesis, and hardware remain
unverified. See the
[switched-screen checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#installed-switched-texture-lifecycle).

The shared importer installs both complete house/manor models and their selected
roof/light lifecycle. All 9,344 artwork bytes and 93 triangles are reused. The
native room identity or preview player's actual assigned home selects among all
twelve roof colours; colour ordering is checked against both games' exterior
palettes. Lights use the shared fade renderer and frame-owned palette storage.
Both complete profiles remain inactive pending their actual HRA reward route.
Seven focused checks cover 4,800 host-rendered frames, all colours/homes/previews,
native dependency guards, complete installed resources, and private browser
composition. Native execution and GPU/hardware appearance remain unverified.
Continue remaining model/behaviour and console categories; do not divert into
reward acquisition. See the
[roof-lifecycle checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#installed-selected-roof-palette-lifecycle).

The shared moving-table core is converted and cross-compiled alongside the
compass needle: all six footprints, four carried slots, mixed furniture/loose
items, relative transforms, parent readers, drawing arguments, and final
placement/angle restoration. The carrying comparison runs 90 donor cases and
1,890 move/draw frames under sanitizers. Source and native dependency guards
also pass, as do the affected needle and joint-source checks: seven focused
tests in total. No historical emulator fixture is replayed.

The loose-item dependency is installed in ABI 244: both native drawing paths,
the donor's category rotation flags, transient angle-grid lifetime, and successful
drop clearing. The existing startup chain loads and checks the resident code
before native actors run. Four focused checks cover 768 donor angle comparisons,
all 34 native categories, startup failures, installed hooks/relocations, retained
resources, UPS reconstruction, and four browser/offline selections. Native bridge
execution and GPU appearance remain unverified. See the
[loose-item checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#installed-loose-item-rotation).

The moving-table owner hooks and compass lifecycle are installed. Twelve guarded
owner replacements connect carrying, parent-relative drawing, and final item
restoration. The ordinary importer reuses the complete 3,008-byte compass model
and enables its actual Gulliver route, non-orderable catalogue entry, scoring,
official English name, and optional save-profile bit. Five focused checks pass
for source/dependency guards, the combined carrying/needle dispatcher under
sanitizers, complete installed resources, UPS reconstruction, and four
browser/offline selections. The needle retains its 19,232 donor comparisons.
Native bridge execution, ordinary gameplay, and GPU/hardware appearance remain
unverified. See the [needle checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#installed-parent-sensitive-needle).

The shared importer installs complete lighthouse, moon, and snowcone lifecycles
in one category batch, reusing all prepared artwork. Motion, clock rotation,
translucent joint redraws, scrolling, and full required sounds are connected.
Three focused source/integration/composition checks pass, alongside the retained
9,600-frame host sanitizer check. The native run passes 99 assertions for the
lighthouse/moon before a debugger interruption; the retry encounters an
unsupported debugger command. Native snowcone execution and full ordinary/GPU
appearance remain unverified. The profiles stay inactive pending actual
acquisition. The compass uses the same dispatcher with installed parent support. See the
[joint-lifecycle checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#installed-switched-joint-lifecycles).

The checked proposal is ABI 267 at
`build/v3-effect-rig-imports-01/cartridge/build-lock.json`, with 162
development choices and unchanged format-four saved data. The complete
10,448-byte snowboard remains imported through the ordinary pipeline,
including all 259 triangles, thirteen textures, and actual winter-camper route.
Shared room banks and catalogue model buffers hold 12,288 bytes. The extension
uses reserved Expansion Pak memory plus 6 KiB of submenu memory without changing
saved formats. Four focused tests and 31 native capacity assertions pass,
including complete first/last-bank DMA and the native preview allocation loop.
Full room/catalogue construction and GPU/hardware appearance are not claimed.
See the [capacity checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#complete-model-bank-capacity).

The shared console-game converter prepares all nineteen full donor games,
sixty ordered persistence operations, original and converted metadata, and
twenty source-derived launch bindings. Six focused checks pass. The twelve
additional game payloads are retained; the leftover disk-system Zelda furniture
has no corresponding payload in this donor. Native launch, larger-game memory,
and persistent storage remain unfinished, so none is enabled. Actual native
mapper callbacks are identified without claiming execution. See the
[console checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#complete-console-game-dependencies).

The shared fixed/indexed material converter prepares all fourteen console
models, 68,320 bytes total, in one compiler run. It retains each source cartridge
texture/palette, complete selector tables, and all geometry. Four focused source
and compiled-artwork checks pass. Twelve new supplied games need their launch
lifecycle; one unused disk-system model also lacks a game payload. Profiles
remain unavailable. Super Tortimer is
drawing-only in the donor, not a missing game implementation. This preparation
does not change the cartridge or either deployment. See the
[constant-material checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#bulk-fixed-and-indexed-material-sequences).

Scrolling-material imports automatically prepare
complete artwork, install any required loop audio, and bind finished profiles.
Beach table retains its complete body, translucent glass, and moving bubbles;
its island acquisition remains unfinished, so its complete profile stays inactive.
The existing native renderer handles all three model lists without new code.
Four focused checks pass, including complete compiled artwork, the shared renderer
under sanitizers, retained resources, and four browser/offline compositions.
See the [scrolling checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#automatic-scrolling-category-imports).

The ordinary importer installs chowder's complete
three-part model, two-frame texture animation, periodic steam, complete five-note
sound loop, both envelopes, instrument, and sample. Actual winter-camper
acquisition is enabled without substituting shop stock. Shared material/audio
categories perform the conversion and installation; no dedicated item installer
is added. Focused source/sanitizer checks, full installed-resource verification,
patch reconstruction, and four browser/offline selections pass. The saved format
is unchanged. Native particle execution, GPU appearance, and synthesis remain
unverified. See the [material checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#installed-timed-textures-and-periodic-materials).

The ordinary importer also connects periodic steam and
directional projectiles, complete loop/trigger audio, and additive native effect
profiles. All four steam textures, both material variants, and the complete
projectile model remain. Both furniture models are reused without compilation.
Barbecue uses its actual B-stock/category, catalogue ordering, and scoring.
Cannon's complete behaviour remains inactive pending its actual acquisition.

The complete effect graphics bank is relocated to VROM `03FC0000`, with its
native reader rebound and original prefix preserved. Six focused checks pass,
including sanitized emitters, complete installed resources, patch reconstruction,
and four browser/offline compositions. Native owner loading/relocation, six
graphics allocations, and public clip registration pass. The bounded native run
stops before particle execution because the title-scene fixture obtains seven
programme slots while its assertion expects twelve. Native lifecycles/rendering
remain unverified; no further setup retry is queued for this batch. See the
[particle checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#installed-steam-and-room-projectiles).

The retained shared static-interaction importer installs
the piggy bank's one-Bell deduction and the ukulele's native town-tune callback.
It reuses both complete models and preserves all 71 original font instruments
while adding the full ukulele instrument/sample and nineteen-note programme.
The callback recognizer covers all sixteen donor musical-instrument callbacks.
Post-office and island acquisition still keep these two completed profiles
inactive; acquisition remains phase 2.

Seven focused checks pass, including four browser/offline compositions and
sanitized wallet/position-update checks. The first native attempt passes 60
internal assertions across 103 recorded steps, executing the installed shared
callback and actual native room melody dispatcher. Audio calls are captured;
ordinary synthesis, interaction, and hardware are not newly verified. See the
[static-interaction checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#installed-static-interactions-and-town-tune-instruments).

The retained material importer installs starman's
complete constructor, positioned loop, same-item switch coordination, and player
colour update/draw hooks. Its complete instrument and 46,900-byte sample are
retained. A separate 256-byte transient reservation preserves native actor and
saved-field sizes. The shared dispatcher starts the item off, honours transition
states, and restores scene fog after the player skeleton without discarding
graphics allocations. Starman remains unavailable because its actual Mario
reward route is unfinished; acquisition stays in phase 2.

Six focused checks pass, including 480 donor timing ticks under sanitizers,
complete installed bindings, retained data, and four browser/offline compositions.
The bounded native check passes 36 assertions after one fixture allocation
correction. It executes the installed bridges, material callbacks, and native
fog writer; skeleton and sound calls are captured. Ordinary in-room player
appearance, synthesis, and hardware remain unverified. See the
[colour lifecycle checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#installed-exclusive-player-colour-lifecycle).

Mouth of Truth's complete timed reaction and shared N64 motor connection remain
installed through the ordinary importer. Its complete 3,968-byte artwork, official name, Gulliver
reward route, catalogue non-orderability, and scoring are retained.

The guarded controller hook uses the actual shared-packet CRC and retrace entry.
The complete donor waveform bank and independent motor state preserve start,
stop, communication retries, and stopping during suspended gameplay or pre-NMI.
The source surprise request persists until the player accepts it. One explicit
1-KiB reservation holds transient state; saved formats and actor sizes do not grow.

Focused sanitizer checks compare 2,850 frames with the donor evaluator and
exercise the actual material dispatch. The native run passes 63 internal
assertions for the installed bridge, cold-load guard, full model transfer,
constructors, player-request arguments, complete countdown/envelope timing,
saved-state preservation, and bounds. Its captured player callback and
disconnected accessory do not establish ordinary player animation, actual
motor transfers, or physical Rumble Pak behaviour. See the
[installed reaction checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#installed-timed-material-reactions).

The retained candle integration is ABI 220 at
`build/v3-material-lifecycle-imports-02/build-lock.json`, with 154 development choices.
The ordinary category importer plans complete material renderers, required audio,
and implemented lifecycle profiles together, skipping installed dependencies.
Festive candle is enabled through its actual donor stock/category, catalogue,
scoring, and selection, reusing its complete 4,448-byte animated object.

The source-checked invalid-index initializer uses private native actor storage;
the source's larger actor offset is never written into the N64 instance. The
existing checked constructor bootstrap dispatches material and rig callbacks.
No extra bootstrap, allocation, or saved field is required. Full-source move and
destructor checks retain the candle's inert callbacks. Completed imports no
longer retain stale pending-resource entries in generated reports.

Three source/planner checks and three current-cartridge/material checks pass,
including sanitized construction/rendering and four browser/offline selections.
The focused native run passes 22 internal assertions for the actual constructor,
room/catalogue aliases, complete model DMA, independent instances, packet/cache,
save-state preservation, and bounds. Its one setup retry uses the existing
main-RAM entry-bridge approach. The final report correction produces the identical
tested ROM; unchanged animation/effect/rolling/contact evidence is retained.
See [the checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#automatic-material-lifecycle-import).

Judge's bell retains its complete endpoint-hit behaviour, both sounds, and
conditional effect binding. Its native particle lifetime still needs a properly
allocated graphics fixture with the next changed effect batch; the previous
fixture omitted that allocation. Do not repeat the passed bell checks.

Room code uses 18,688 of 32,768 bytes; bootstrap uses 1,509 of 1,536 bytes.
Scroll code has 4 bytes spare, audio has 768 conservative bytes spare, and
the import reservation has 1,009,936 bytes spare. Live synthesis, GPU appearance,
ordinary gameplay/save/restart, and original hardware are not newly verified.

Saved format 4 is unchanged. A save using an added item requires its selected
import in the receiving build; preserve backups and equal-or-larger profiles.
Format-4 saves cannot load in V2 or format-1/2/3 V3 builds. Translation-only output
remains the pinned V2-12 ROM. The main lock and both stable deployments remain
unchanged. Continue remaining model, material, animation, and behaviour
conversion, including remaining material lifecycles, rigged creatures, and
model-bank capacity. Steam, projectiles, and stone coin's rolling lifecycle are
installed; ordinary gameplay acceptance remains separate.
The code-entry frontend remains parked.

The retained password-engine component is ABI 197 at
`build/v3-password-runtime-05/build-lock.json`. The shared password codec,
eligibility rules, and 128-import destination map are linked into a checked
32-KiB demand-loaded packet. The 6,764-byte engine reads actual selection flags
and calls the native continuous RNG. A 306-byte loader fits existing equipment
padding; startup resets its cache, with no increase to startup code or ordinary
heap allocations. Missing and disabled imports do not resolve.

Four focused host checks cover source/data bindings, complete retained resources,
loader failure/cache ordering under sanitizers, and browser/offline none/all/
individual composition. Native execution remains incomplete after two fixture
setup failures; the corrected proof alignment is queued with frontend testing,
not replayed in this batch. The new loader's startup bytes, zero cache, footer,
and original RNG instructions pass the reached native checks. No decoder,
keyboard, or gift-handover execution is claimed.

Nook's input/dialogue and animated handover, native saved-name conversion,
and reviewed existing-item/display correspondence remain phase-2 work. Retain
the verified codec and policy results. Keep its destination map aligned with
newly installed imports before completing the frontend. See the
[runtime checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#linked-password-engine-and-native-bindings).

The retained scoring proposal is ABI 196 at
`build/v3-birth-scoring-runtime-02/build-lock.json`. The shared importer maps all
38 donor birth categories into 27 native scoring counters, preserving every
existing native weight and actual acquisition rule. Four new values cover the
remaining categories, including Harvest's exact 1,177 points. No per-item
scoring exceptions or wider metadata fields are required.

Three focused host checks pass, including real donor-row integration through
the ordinary installer and rejection on an older evaluator. The first silent
native attempt passes 83 assertions across 17 cases: complete counters/products,
new values, native lottery points, mixed/null layers, full surface indices, stack
boundaries, relocation, and saved-state preservation. The report-only final
refresh produces the identical tested ROM; unchanged theme checks are retained.
The scoring owner grows 112 bytes, with no extra fixed allocation. Saved format
4, profiles, artwork, and 148 choices are unchanged. Delivery and remaining
behaviours still gate imports. Neither deployment nor the main lock changes.
See the [base-point checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-complete-donor-base-points).

The shared theme proposal is ABI 195 at
`build/v3-theme-scoring-runtime-02/build-lock.json`. Shared HRA theme storage
supports all 60 donor categories with three inert padding rows for the native
unrolled loops. Harvest retains its base-series rules; Mario retains its theme
rules. Both use their actual additive floor/wall pairs and official English
names in the complete score-letter lookup. The first 55 native definitions,
all installed furniture metadata, and native base-point weights are preserved.

Three focused host checks pass, including complete owner reconstruction,
relocation bounds, text provenance, and browser/offline none/all/single output.
The focused native run passes complete scoring loading/relocation, group assignment,
both new category rules, loop termination, English key lookup, and saved-state
preservation after one fixture correction for byte-sized category counts.
Ordinary score-letter generation and hardware are not newly verified.
There are still 148 experimental
choices and 27 inactive profiles: theme support does not substitute for delivery
or the remaining new birth-point categories. Saved format 4 and selection
profiles are unchanged. Neither stable deployment nor the main lock changes.
See the [theme checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-complete-donor-themes).

The shared movement proposal is ABI 194 at
`build/v3-room-movement-imports-01/cartridge/build-lock.json`. The shared room
movement-sound dispatcher implements both source categories, with complete
directional rolling/dragging and grass-dependent pushing sounds. The normal
bulk importer enables lawn mower through its actual event-item stock and
catalogue reordering, reusing its complete graphics and contact callbacks.
There are 148 experimental choices and 27 inactive profiles. Stone-coin sound
support does not enable its unfinished model/behaviour category.

Four focused host checks pass, including sanitized runtime execution, complete
audio/program/instrument rebinding, and four browser/offline ROM comparisons.
A silent native first attempt passes 62 internal assertions through the complete
movement-owner function, real lazy loader, and installed dispatch. Audio call
arguments are recorded; actual synthesis/listening, ordinary room use, and
hardware are not newly verified. Unchanged alpha/rendering evidence is retained.
No additional fixed memory is reserved. Audio has 288 conservative bytes spare.

Saved format 4 is unchanged, but selecting the mower adds its required profile
bit: builds or selections without that import cannot load such saves. Preserve
backups; ordinary cross-version reload is not established by these checks.
The main lock and both stable website deployments are unchanged. See the
[movement checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-room-movement-sounds-and-ordinary-import).

The retained contact proposal is ABI 191 at
`build/v3-contact-floor-runtime-04/build-lock.json`. Shared contact/floor alpha
callbacks are installed without additional memory or saved fields. Complete
source/artwork bindings map backyard lawn to new floor 74 and retain native
meadow 48; native plank floor 26 is untouched. A focused silent emulator run
passes the installed callbacks, native easing, complete actor-write boundaries,
saved-state preservation, and guards. Ordinary room use and hardware remain
unverified. This retained proposal has alpha callbacks but no room-owner
movement sounds; the current proposal above supplies the complete sound binding.

Existing import choices and resources are unchanged. Furniture validation now
follows the expanded floor-sound table while checking all original entries and
complete switch-click programs. No website deployment or main lock changes.
See the [contact checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#installed-contact-and-floor-lifecycles).

The retained surface-selection proposal is ABI 190 at
`build/v3-surface-selection-runtime-02/build-lock.json`. The private selector
offers 147 installed development choices, including three floors and three
wallpapers. Individual/all composition updates real enabled metadata, packs
catalogue rows/counts, and exports independent 64-byte surface profiles. Two
checked read-only CRC words allow selection without changing instructions.
No allocation or saved format grows. Format-4 saves still cannot load in V2 or
format-1/2/3 V3; preserve backups and retain every selected import.

Five focused checks pass, including four complete browser/offline ROM comparisons
and sanitized startup failure paths. Ten browser-engine unit checks pass across
the base run and added surface case. A composed two-surface build passes native
cold startup after one fixture correction for the existing scenery cache word.
A focused silent Chromium worker reconstructs the same ROM from the two supplied
games, verifies the profile/warning, and checks floor/wall category controls.
The temporary verification server is stopped. The private export is
`build/v3-surface-browser-01/`; neither stable website deployment changes.
See the [selection checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-surface-optional-selection).

Shared native stock lists
include the six additive surfaces through their actual A/C and event categories.
The complete native picker and membership query filter disabled imports before
selection, retaining original goods, RNG, and rarity. HomePage/Mario and Harvest
surfaces remain outside these lists, awaiting their real delivery categories.
The helper occupies existing reserved memory; temporary goods allocations grow
80 bytes each. Three focused host checks pass. A native run passes after one
fixture correction to initialize rarity settings in its disposable blank town.
Ordinary purchases/event delivery and hardware are not established.
See the [stock checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-surface-stock).

The retained audio proposal is ABI 188 at
`build/v3-surface-audio-runtime-01/build-lock.json`. Player/NPC floor footsteps
and furniture dragging use independent full-index tables. Complete donor
programs, instruments, samples, and all eight walking/running variants are
matched. Existing floor mappings stay unchanged. Eight unused native grass
programs are connected through reserved sound slots; only the lawn drag program
needs new sequence data. No instrument or waveform is added.

The sequence grows 176 bytes. A checked 1-KiB permanent-audio increase leaves
896 bytes of conservative capacity; session pools remain unchanged. Three
focused host checks pass after one expected-value rounding correction. Native
execution passes 58 internal assertions after one fixture correction for the
original sequence's self-modifying dispatch operands. Actual loaded sequence,
audio pools, player/NPC/drag calls, priorities, saved state, and guards pass.
No listening, synthesis, ordinary room playthrough, or hardware acceptance is
claimed. See the [audio checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-surface-audio).

All ten additive surfaces
use their exact donor HRA base values, while all original surface values remain
native. Western, Backyard, and Boxing themes reference the new matching pairs.
The complete native base evaluator retains furniture accumulation and bounds
full surface indices before reading independent resident tables. No owner,
packet, or saved-state allocation grows. Full Harvest and Mario furniture theme
categories remain incomplete; surface base values do not establish those bonuses.

Three focused host checks pass. A silent native first attempt passes 36 internal
assertions through the complete evaluator and existing theme scorer, including
original values, all added values, invalid indices, retained furniture points,
partial/complete theme bonuses, restored state, and guards. Ordinary score
letters, save/restart, and hardware execution are not tested by this fixture.
Unchanged menu/application/save checks are retained, not replayed. See the
[scoring checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-surface-scoring).

The catalogue's floor/wall
lists connect to independent surface ownership through one 144-byte helper.
Original entries, debug behaviour, complete English names, and completion flags
remain intact. Lists and helper fit the existing surface packet; menu memory,
relocation size, artwork, saved format, and selectable choices do not grow.
Shared catalogue rebuilds preserve these readers and the surface previews.

Three focused checks pass across the implementation and corrected receipt:
actual C under memory-safety sanitizers, checked relocation at three addresses,
retained rebuild hooks, unchanged resources/profiles, exact empty/all composition,
and UPS reconstruction. A silent native run passes 42 assertions on its first
attempt, including the actual catalogue loader/initializer, collected surface
lists, full names, completion flags, and complete native inventory action bodies.
The inventory already exchanges full surface IDs; no new pocket format is needed.
Its fixture stubs UI index/close callbacks, not the pocket/room-queue exchange.
No ordinary UI playthrough, GPU appearance, hardware acceptance, physical audio,
or explicit FlashRAM writes are claimed. Unchanged application/save tests are
retained, not replayed.

Format-4 saves require a compatible newer build; V2 and format-1/2/3 V3 builds
cannot load them. Preserve backups. Private exports carry this warning. There
are 147 choices and 27 inactive furniture profiles; four Mario/Harvest surfaces
remain disabled pending genuine delivery routes. Next connect those shared
acquisition/theme categories and the prepared contact/floor lifecycles. The stable
patcher and main lock remain unchanged. See the
[surface-menu checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-surface-catalogue-and-inventory-exchange).

All ten surfaces retain shared texture, name, price, category, and room-change
readers. Selected surfaces queue until the menu closes, then use native texture
swaps and full-byte home fields. The full floor getter retains selected IDs and
special-scene/campsite behaviour. Disabled imports reject before reservation.
The unchanged application code retains its 34-assertion native evidence in the
[room-application checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-surface-room-application-and-identity);
it is not replayed for the separate save-category extension.

The shared room-surface pipeline prepares all ten donor-only floors/wallpapers
in `build/v3-room-surfaces-prepared-02/`: 61,760 bytes with complete palettes,
tiles, official names, price/catalogue records, acquisition lists, and floor-sound
selectors. Complete artwork matching retains 124 existing player surfaces and
all eight shop-surface mappings. Stable new indices 73–77 preserve original
player/shop content and special-room sound IDs; the paired floors/walls share
indices for scoring. Names are credited in the single provenance catalogue.

Four focused conversion/metadata/cache checks pass. Every added palette and
texel is checked through independent tile addressing; malformed resources and
changed caches reject. Preparation itself changes no choices, saved layouts,
main lock, or served website content. The room/shop installation is described
above; remaining acquisition/theme categories and
ordinary persistence remain required. See the
[surface specification](../specs/V3_ROOM_SURFACES.md).

Shared contact/floor lifecycle preparation is available through the ordinary
pipeline's `lifecycle` representation. Complete source callbacks, easing
constants, contact helpers, six native consumer/owner functions, and complete
floor artwork are checked. The shared native callback compiles to 3,612 bytes
within the existing 4-KiB scroll-code reservation; four focused host/source
checks pass, including memory-safety sanitizers. It is prepared, not installed
in a cartridge, and native execution remains unverified.

The mower exposes an actual additive floor dependency: GameCube backyard lawn
at index 26 is not N64 old plank floor at index 26. Daisy meadow at index 48
matches completely. The importer refuses the numerical alias and keeps the
mower unavailable until the missing floor has its own additive runtime support.
Next extend the general room-surface pipeline to preserve existing floors while
adding donor-only identities, then bind the prepared contact category. Do not
reconvert the mower's completed graphics. See the
[contact/floor checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-contact-and-floor-lifecycle-preparation).

Shared native fresh-placement handling applies the source start-disabled flag to imported
items while preserving original-item defaults. Loaded switches and gyroid paths
remain native. A twenty-byte owner patch calls the existing shared behaviour
reservation; the complete helper is 280 bytes with no additional RAM or heap.

The ordinary bulk importer now enables sprinkler through actual donor C stock,
with catalogue reordering, complete artwork, source switch fades/clicks/looping
sound, and unchanged persistent identity. Its existing 4,672-byte object is
reused; no graphics or audio is rebuilt. Merlion, Manekin Pis, and fireplace
retain their completed shared callbacks and genuine gift/trade routes.

Three focused checks pass for the changed helper under memory-safety sanitizers,
complete owner/source/profile bindings and asset retention, plus four matching
browser/offline selections. A bounded native check passes 21 assertions using
the complete installed initializer copied into an isolated small arena. It
executes the fresh-placement path and confirms the installed fade constructor
consumes the off state, with guards, saved state, checkpoint restoration, and
clean exit. One setup correction resolves a test-only blob/RAM-offset mismatch.
Unchanged rendering/fade/audio tests are retained rather than replayed. Ordinary
room interaction, synthesis, appearance, and hardware acceptance remain separate.
See the [placement checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-start-disabled-placement-and-import).

There are 141 experimental choices and 27 inactive profiles. Saved format 3 is
unchanged; saves selecting an addition require that ID in the target build and
profile. Older builds without the sprinkler cannot load profiles selecting it.
Empty/all selections reproduce the exact translation-only baseline/current
proposal. The main lock and both stable website deployments remain unchanged.
Next complete remaining contact/floor, material, acquisition, and rigged-material
categories. Required gold-tree effects and golden-shovel acquisition follow
primary imports.

The retained draw-only proposal is ABI 174 at
`build/v3-draw-only-scrolling-imports-01/cartridge/build-lock.json`. Shared
draw-only lifecycle checks connect the well model and backyard pool to ordinary
profiles without new artwork, runtime code, or memory reservations. The pool
also passes the normal donor event-item acquisition, catalogue, price, name, and
scoring checks, so it is an optional experimental import. The well model remains
inactive pending acquisition support. Five other scrolling lifecycles and the
previous material dependencies remain explicitly pending.

Four focused checks pass, including unchanged resource/runtime storage,
source-lifecycle rejection, retained staged/active profiles, saved selection
changes, UPS reconstruction, and matching browser/offline outputs for four
profiles. The 137 experimental choices comprise 20 villagers, 90 furnishings,
24 equipment parents, and three shirts; 27 ordinary profiles remain inactive.
No native/GPU/ordinary-gameplay verification is added by this batch. Saved format
3 is unchanged, but a profile containing the pool requires a build/profile that
includes it; older builds lacking the pool cannot load such a save. The stable
website and main lock remain unchanged. See the
[draw-only profile checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-draw-only-scroll-profiles-and-imports).

Continue the remaining shared lifecycle/acquisition and rigged-material
categories. The mower's contact/floor-driven grass update, switch-driven fades,
and looping sounds remain real dependencies. Gold-tree completion follows
primary importing.

The retained shared renderer is ABI 172 at
`build/v3-scrolling-materials-runtime-04/build-lock.json`. All seven scrolling
objects use one renderer, including the pool's three layers/native colour
registers and the mower's scaled grass alpha in room and preview contexts.
Both new objects reuse complete prepared artwork; five existing objects keep
their original storage. No RAM reservation grows. Five focused checks pass,
including actual renderer C under memory-safety sanitizers, complete installed
resources, malformed-input rejection, and unchanged save-profile/composition
behaviour. One existing test fixture required a correction before its focused
retry passed. Native execution, GPU appearance, and ordinary gameplay remain
unverified. The 136 choices and 26 staged profiles are unchanged. See the
[extended-renderer checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-layered-scroll-renderer).

The complete no-op lifecycle category is connected above. Remaining
lifecycle/acquisition categories still require implementation.

The shared scrolling converter also prepares complete backyard pool and lawn
mower artwork. `build/v3-scrolling-materials-prepared-03/` contains seven objects
(38,336 bytes): two newly compiled together, five reused without compilation.
EVW animation tables and the common parameterised scrolling helper feed the
same graphics pipeline. All pool layers, water rates, debug colour dependencies,
and the mower's scaled actor alpha remain explicit. Four focused resource checks
pass, including complete graphics comparisons and rejection of unsupported
runtime installation. Names are credited to the official donor in the single
provenance catalogue. Native drawing support is installed above; lifecycle and
profile/acquisition integration remain required before playable imports. The
resource preparation itself changes no cartridge or saved profile. See the
[EVW/parameter-scroll checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-evw-and-parameter-scroll-resources).

The retained initial scrolling renderer is ABI 171 at
`build/v3-scrolling-materials-runtime-02/build-lock.json`. The shared renderer
installs all five complete prepared scrolling objects, with separate opaque and
translucent draws, both texture layers, frame-owned commands, and mapped colour
inputs. An 8-KiB extension fits between existing room code and furniture banks;
the original room packet, model pool, and ordinary heap stay unchanged. Four
current-build checks pass, including address/undefined-behaviour sanitizer
execution, installed resource/dispatch checks, and retained saves/composition.
Native execution and GPU appearance remain unverified. Lifecycle and acquisition
remain unfinished, so these five objects have no ordinary profiles or choices.
The 136 choices, 26 staged profiles, saved format 3, main lock, and stable website
are unchanged. See the
[scrolling-renderer checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-scrolling-material-renderer).

The shared scrolling-material category prepares five complete objects at
`build/v3-scrolling-materials-prepared-02/`: Merlion, Manekin Pis, well model,
fireplace, and sprinkler, totalling 28,112 bytes. One compiler batch produces
their graphics; the final receipt reuses all five objects without compilation.
The common converter preserves both texture layers, padded eight-pixel texture
rows, opaque/translucent model order, scroll rates, and external colour state.
Four focused checks pass. Runtime drawing and additive destination reservations
are installed above; lifecycle and acquisition remain required and these
resources are not selectable.
Names are credited to the official donor in the single provenance catalogue.
No cartridge or served website changes. See the
[scrolling-material checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-scrolling-material-resource-preparation).

The material/trigger profile integration is retained from ABI 170 at
`build/v3-material-trigger-profiles-02/build-lock.json`. The shared profile
importer stages coin, ? block, and fire flower with their complete material/sound
callbacks, official names, prices, and ordinary records. All graphics and runtime
bytes are reused in place. Three focused current-build checks pass; metadata now
reaches the missing source acquisition route. The other three material objects
retain explicit incomplete lifecycle dependencies. There are 26 staged profiles;
none of this batch is enabled for selection. The 136 existing choices, allocations,
saved format/profile, main lock, and both served patchers are unchanged. See the
[profile checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-material-trigger-profile-integration).

The shared incremental-audio integration is retained from ABI 169 at
`build/v3-material-trigger-runtime-04/build-lock.json`. Shared audio installation
accepts incremental batches, preserves previous sound identities and complete
instruments/samples, and connects the existing switch-trigger callback to coin,
? block, and fire flower's installed material renderer. Their three full sound
programs/instruments are installed alongside the five previous sound objects.
All 82 instruments fit the existing audio allocation, with 352 bytes of
conservative permanent headroom. Ordinary profiles are staged above; acquisition
remains pending, and this batch does not add selectable choices.

The shared allocator relocates the complete wave archive into verified empty
cartridge space when an in-place append encounters occupied or unclaimed data.
All six headers and the native base load follow the new location; external wave
resources and the old allocation remain intact. Four current-build checks pass.
The first silent native run passes 75 records and 50 assertions, including
complete instrument/sample relocation, one new and one retained real sample
transfer, guards, checkpoint restoration, and clean exit. Ordinary interaction,
GPU appearance, listening, and hardware are not claimed verified. See the
[incremental-audio checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#incremental-shared-furniture-audio).
The 136 choices, saved format 3, main lock, and both served V2 patchers are unchanged.
Continue primary profiles/acquisition before required gold-tree completion.

The shared material-renderer integration is retained from ABI 168 at
`build/v3-material-frames-runtime-02/build-lock.json`. One shared material renderer
and all six complete frame-bank objects are installed, reusing the 17,104-byte
prepared batch without recompiling artwork. Palette cycles, animated textures,
room/preview timing, switch gating, and actor-state faces share bounded records.
The code and tables fit the existing room packet; no resident allocation grows.
Four current-build checks pass, including sanitizer execution of the renderer,
complete frame order, malformed-input rejection, and unchanged existing choices,
profiles, saves, and translation-only output. Native execution and GPU appearance
remain unverified. Coin, ? block, and fire flower's trigger lifecycles are
connected above; the other three lifecycles and all six acquisition routes remain
pending, so none of these objects is selectable. See the
[renderer checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-material-frame-renderer).
The 136 existing choices, 26 rigs, 23 staged profiles, saved format 3, main lock,
and both served V2 patchers are preserved. Continue primary category/acquisition
work before required gold-tree effects and full golden-shovel acquisition.

The shared material-frame converter prepares complete artwork for six more
objects: coin, ? block, starman, fire flower, festive candle, and Mouth of Truth.
`build/v3-material-frames-prepared-01/` contains 17,104 bytes compiled in one
container. Every texture/palette frame, repeated frame-table entry, and source
draw order is retained, along with explicit pending timing/interaction callbacks.
Four focused checks pass, including independent complete graphics comparisons,
cache reuse, changed-dependency rejection, and refusal to install unfinished
behaviour. Names use credited official source text. This preparation changes no
ROM, choice, save, or served patcher. See the
[material-frame checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-material-frame-resource-preparation).

The shared clock integration is retained from ABI 167 at
`build/v3-shared-fixed-clock-profiles-01/build-lock.json`. The shared clock
runtime serves both fixed and indexed source bindings. Harvest clock's complete
model, animation, live hands, inactive ordinary profile, official name, and price
are installed. Its 3,744-byte object is reused without an artwork compiler; the
runtime code and resident allocations are unchanged. There are 26 room rigs and
23 staged furniture profiles. Three current-build checks pass. Acquisition remains
pending, and the selectable count stays 136. See the
[clock integration checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-fixed-and-indexed-clock-integration).

The static-profile resource path prepares complete models even when a move-only
callback still needs porting. `build/v3-static-callback-resources-prepared-01/`
contains piggy bank, ukulele, barbecue, and cannon: 17,168 bytes, compiled together
in one container. Three focused checks pass. Move code, interaction fields, and
spawned effects remain explicit pending dependencies; metadata and native-profile
construction refuse to enable these resources. No cartridge, choice, save, or
served-patcher changes result from this preparation. See the
[static-callback checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-static-callback-resource-preparation).

The shared importer also prepares complete fixed keyframe rigs independently of
unfinished gameplay callbacks. `build/v3-fixed-keyframe-rigs-prepared-01/`
contains tiger bobblehead, stone coin, harvest clock, and judge's bell: 15,776
bytes of complete models, skeletons, and motions compiled in one container.
Three focused checks pass, covering complete graphics/keyframe data, changed
resource bindings, cache reuse, and refusal to enable unfinished behaviour.
Stop/repeat initialization, clock joints, and pending move/destroy code remain
explicit. Harvest clock's lifecycle and profile are integrated above; the other
three remain prepared only. These are not four new playable imports. See the
[fixed-rig checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-fixed-keyframe-resource-preparation).

Shared IA16 texture conversion and two translucent material formulas preserve all source
pixels, alpha, geometry, and draw states. The complete tissue and bottled ship
artwork is prepared, while the Moai statue is integrated through the ordinary
importer and existing Gulliver reward category. The prepared batch compiles
three models and reuses five; native storage adds the 4,048-byte Moai object
without another resident allocation. See the
[material checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-ia16-and-translucent-materials).

The shared importer separates
donor IDs/indices from stable N64 destinations throughout artwork reuse, names,
prices, placement, sound categories, scoring, catalogue, acquisition, and optional
selection. Eight complete legacy Gulliver souvenirs are installed through that
pipeline, using 33,760 bytes of prepared artwork and no new resident allocation.
There are 136 experimental choices: 20 villagers, 89 furnishings, 24 equipment
parents, and three shirts. Four golden tools remain disabled.

Eight focused checks pass for the material batch: three format checks, two
complete-art/source checks, and three current-cartridge mapping checks. Four
browser/offline composition profiles agree, including retained assets/allocations,
stable identity rejection, and exact empty/all output.
The bounded native check reaches startup/table assertions but cannot allocate its
temporary owner arena at the title screen, even after one size correction.
That allocation limit is retained, not retried for the material batch.
Changed-item native readers/acquisition and ordinary gameplay remain unverified;
do not replay the same setup. See the
[mapped-identity checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-source-to-destination-mapping).
Save format 3 is unchanged, but saves using the new items require their selected
destinations and cannot be loaded by older builds. Neither served patcher nor
the main ABI-109 lock changes. Continue primary category/acquisition work before
required gold-tree effects and golden-shovel acquisition.

The bulk scan includes unresolved legacy `1xxx` donor records rather than
silently omitting them. `build/v3-legacy-static-prepared-01/` contains twelve
complete static objects (46,272 bytes), compiled in one container with the
existing converter. Two focused checks pass, including complete graphics
comparisons, source names, alias/dummy classification, and refusal of unfinished
imports. Official name sources are in the single provenance catalogue.
Eight ordinary souvenirs have reviewed additive destinations; the four paintings,
chocolates, tissue, and bottled ship remain pending identity/acquisition work. Same-numbered N64
items are not overwritten. See the
[legacy checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#legacy-donor-discovery-and-bulk-artwork).

The primary acquisition pipeline prepares all 28 source holiday selectors and
65 gift candidates at `build/v3-holiday-rewards-prepared-02/`, plus a relocatable
N64 selection/handover kernel. Three focused source and sanitizer checks pass.
The shared kernel handles optional variant selection, independent player
receipts, duplicate rejection, and full-pocket failure without consuming a
reward. This is prepared code/data, not an installed NPC or acquisition route;
holiday preparation adds no selectable choices. Next connect donor identity
resolution, Tortimer's actor/calendar/dialogue, and actual delivery callbacks.
Legacy `1xxx` donor records are included in primary discovery. The holiday
program's bottled ship `1FC0` still has no reviewed native identity or additive
destination. Its complete artwork is prepared; holiday acquisition remains open.
See the [holiday checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-holiday-reward-preparation).

The retained ABI-163 staging at
`build/v3-shared-room-profiles-02/build-lock.json` connects
all fifteen clocks, both storage rigs, and five sound objects to ordinary
profiles, official names, and prices. It reuses all seventeen rig assets and
adds 12,352 bytes of complete sound models, with no additional resident memory.
The current import reservation has 1,981,712 free bytes. Both record flags and saved
selection bits remain off, preventing unfinished items from entering gameplay.

The ordinary bulk importer validates these installed lifecycle bindings and can
reuse staged records/assets when their acquisition categories are implemented.
All 22 now reach the actual acquisition checks instead of stopping on missing
lifecycle code. Four focused host/cartridge tests pass, including full/empty
composition and unchanged existing records/resources. The silent native check
passes 112 assertions, covering disabled registration and three category
representatives' names, prices, sizes, complete model transfers, and guards.
See the [profile checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-ordinary-profile-staging).
Those 22 staged records add no experimental choices; their acquisition and
catalogue/scoring activation remain incomplete. Ordinary gameplay and hardware
checks are not claimed complete.

The retained ABI 162 audio evidence covers all five complete
furniture sound programs, instruments, and samples installed with one shared
move callback. Sound priorities are preserved; the callback supplies the donor's
single-instance rule missing from the N64 engine. Audio memory grows by 2 KiB,
with 864 bytes of conservative spare capacity.

Seven focused audio checks and the shared sanitizer check pass; the three
current-cartridge checks and affected sanitizer check also pass on the corrected
build. The silent native run passes 61 assertions, including all program/font
loading, two actual positioned-trigger/sample-transfer representatives, duplicate
suppression, guards, restored checkpoint, and clean exit. Ordinary furniture
interaction, acquisition, listening, and hardware remain unverified. No choices,
saved formats, main lock, or served patchers change. Continue shared category
integration and acquisition, then required gold-tree completion. See the
[audio runtime checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-furniture-trigger-audio-runtime).

The next bulk-import check follows the installed sound tables/font locations and
verifies complete original chair instruments instead of requiring their old
addresses. Its focused positive/negative check passes. This is an importer-only
change; it neither changes the current ROM nor calls for another emulator run.

The installed clock category retains its passing component evidence from the
25-record ABI-161 packet. The current room engine serves 26 records: eight
balloons, two storage rigs, and sixteen clocks. Clock/storage ordinary profiles are staged, and acquisition remains
required. Resources alone do not make them selectable. No additional resident
memory or saved format is needed for this batch.

Four focused host/cartridge checks pass. The silent focused native run passes
153 assertions, including the corrected final-string DMA boundary, three complete
clock rig representatives, live hand angles, guards, state restoration, and clean
exit. Earlier passing relocated-text checks are retained without replaying them.
Ordinary acquisition, room gameplay, GPU appearance, and hardware remain unverified.
Continue shared conversion/integration and acquisition categories. The main ABI-109
lock and both served patchers remain unchanged. Required gold-tree leaf/cut effects
and full golden-shovel acquisition follow the primary importing work. See the
[storage/clock checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#bulk-storage-and-complete-clock-installation).

The shared open/close category prepares both Harvest storage objects, retaining
complete models, skeletons, animations, source interaction flags, and opening
limits. Two converter checks pass; the shared runtime above supplies their
lifecycle. Ordinary profiles are staged; acquisition remains required. The additional
fixed rigs described above are prepared separately; three still need their
actual runtime behaviours. Continue shared integration before required gold-tree work.
See the [storage checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#openclose-storage-category).

The shared sound category reuses complete prepared artwork and audio from
`build/v3-switch-sound-prepared-01/` and `build/v3-furniture-trigger-audio-02/`.
The installed audio retains all 74 previous instruments and adds five complete
donor instruments, preserving repeated notes, envelopes, tuning, and samples.
Ordinary profiles are staged; acquisition still needs connecting before these
five objects become selectable.

All fifteen station models have complete prepared artwork, skeletons, and motions
through the shared indexed-clock category at `build/v3-indexed-clock-rigs-prepared-01/`.
One compiler container handles the whole batch. Source clock-hand rules and live
time dependencies are recorded explicitly; complete resources and the shared clock
runtime and inactive ordinary profiles are installed in the current proposal.
Acquisition remains pending. Three retained converter checks pass, including
complete graphics/motion comparisons and refusal to enable unfinished records.
See the [clock-rig checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#indexed-looping-clock-rigs).

The primary importing pipeline compiles missing furniture artwork in one batch
and reuses verified prepared objects while regenerating current eligibility and
metadata. `build/v3-bulk-prepared-02/` contains 95 complete prepared objects:
93 reused and two newly compiled constant-palette trophy variants. Acquisition
gaps remain explicit; preparation adds no selectable items or ROM changes.
The current cartridge proposal is identified above. Continue shared conversion and
acquisition categories before returning to required gold-tree completion. See
the [bulk checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#bulk-compilation-and-prepared-reuse).

The retained planting-sparkle evidence is from ABI 158 at
`build/v3-shared-tree-sparkle-02/build-lock.json`. All four seasonal planting
callbacks add the donor's gold-sapling sparkle at its actual source position.
The existing N64 effect, planting timing, foreground arguments, and callback
cleanup remain intact. Nine focused checks pass. Native checks cover all four
seasonal consumers; the focused retry closes a fixture-only timing expectation,
verifies original effect setup, and passes guards, restoration, and clean exit.
No ordinary planting, GPU appearance, or hardware claim is made. Code occupies
9,788 of the existing 12,288 bytes, with no added allocation, save field, or choice.
Primary import pipelines and bulk category coverage take priority. Afterwards,
finish gold-tree leaf/cut effects and ordinary acquisition; these remain required
V3 work, and golden choices remain disabled meanwhile. See the
[planting checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-planting-sparkle).

Shared field clearing and both
insect-habitat consumers include selected gold trees while preserving the N64's
four-cell entrance layout, original habitats, and bee-tree exclusion. Seven
focused checks pass. The first silent native check passes 106 records and 69
assertions, including the actual entrance routine, complete loaded insect owner,
three real candidate selections, guards, restored state/checkpoint, and clean
exit. No insect actor is created; ordinary spawning/acquisition and hardware
remain unverified. The 9,296-byte packet fits the existing 12-KiB reservation.
No owner allocation, artwork, saved format, choice, main lock, or patcher changes.
Reuse these components. Golden choices stay disabled until their ordinary routes work. See the
[field checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-field-clearing-and-insect-habitats).

The final axe predicate accepts
selected gold stumps, preserving their real identity through the existing
height and foreground-update path. All four seasonal conversation-camera
callbacks include the donor's medium/large/full gold-tree descriptors. Native
fallbacks and descriptor identities remain intact. Five focused host/cartridge
checks pass. The 8,824-byte packet fits its existing 12-KiB reservation; owner
sizes, allocations, saves, choices, the main lock, and both patchers are unchanged.
The first silent native run passes 172 records and 88 assertions, including
the actual felling branch/commit arguments, loaded seasonal callbacks, guards,
restored state/checkpoint, and clean exit. It injects the stump result and stops
before terrain/foreground mutation; full ordinary felling/effects and acquisition
remain unverified. Reuse these completed components.
See the [checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-final-felling-and-conversation-camera).

Shared player tree queries remain installed, verified in ABI 155 at
`build/v3-shared-tree-player-02/build-lock.json`. They
connect axe targeting, nearby-tree selection, shovel reactions, shaking/touch
sound eligibility, and bee checks. Eleven native call sites use one lazy-loading
gate, preserving real foreground identities, native targeting, and bee timing.
Four focused host/cartridge checks pass. All eleven native query sites and
register preservation pass in the initial partial run; its final fixture guard
overlaps a result recorder. The corrected, focused consumer retry passes 67
records and 52 assertions, including actual bee and axe routines, guards, restored
state/checkpoint, and clean exit. Drop/cut callbacks are fixture stubs; these
results do not prove ordinary acquisition or hardware behaviour. Reuse them.

The packet occupies 8,544 bytes within the existing 12-KiB reservation. The
364-byte player gate reuses a replaced inline predicate; owner sizes, allocations,
saves, choices, the main lock, and both patchers remain unchanged. Final stump
acceptance and seasonal camera checks are connected. Next connect complete
source gold-tree leaf/cut effects. Planting sparkle and field/insect consumers are
connected. The native and donor stump-height lookups already agree and remain
unchanged. Golden choices stay
disabled. See the [checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-player-tree-queries).

Shared seasonal shake/drop and axe-hit initialization remain installed, verified
in ABI 154 at `build/v3-shared-tree-interactions-04/build-lock.json`. Complete donor records
add the shovel, Bells, furniture, and bees while retaining native landing, luck,
furniture selection, bee handling, and original tree records. All nine seasonal
cut-initialization calls are connected, including winter's extra path. Four
focused host/cartridge checks pass. Native verification is partial: 28 assertions
pass before a test-recorder overlap, after an initial oversized fixture allocation.
The overlap is corrected but not rerun within this batch's retry limit. The native
result is not a complete pass; see the checkpoint for the precise tested scope.
The packet occupies 8,232 bytes in a 12-KiB reservation, adding 4 KiB of fixed
space without changing assets, owner sizes, saves, or choices. Player eligibility
and bee timing are connected; final felling, effects, and remaining field/insect
consumers still precede ordinary acquisition. Golden choices stay disabled.
See the [checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-seasonal-tree-interactions).

Shared tree collision, shovel-removal, and NPC-walkability queries remain installed,
verified in ABI 153 at `build/v3-shared-tree-world-02/build-lock.json`. The adapter uses
native terrain and complete collision geometry while preserving real foreground
identities and caller exclusions. Four focused checks pass. The first silent
native run passes 132 records and 118 assertions, including all twelve solid gold
states, actual core dispatch/lazy loading, removal/walkability, native fallbacks,
guards, restored state/checkpoint, and clean exit. This is component verification,
not an ordinary interaction or hardware test. The packet occupies 7,516 bytes
within the existing 8-KiB reservation; no allocation, save field, or choice changes.
The seasonal drop/cut-count stage is installed; full player interactions and
planting effects remain. Golden choices stay disabled.
See the [checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-tree-world-queries).

Shared hidden tree contents remain installed, verified in ABI 152 at
`build/v3-shared-tree-contents-01/build-lock.json`. Spent gold trees participate
in native daily bee, furniture, and Bell recording/refilling without changing
ordinary trees, spawn limits, or saved formats. Four focused checks pass. The
first silent native run passes 75 records and 50 assertions: the real schedulers
populate a temporary mixed grove, preserve families and shovel-bearing trees,
avoid duplicate refills, and restore the complete world/RNG/profile/checkpoint.
The packet is 6,812 bytes within the existing 8-KiB reservation; no allocation
grows in that stage. World queries and seasonal drop/cut-count consumers are
connected; player interaction and planting effects remain. Golden choices remain disabled. See the
[checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-hidden-tree-contents).

Shared daily tree growth remains installed. The actual daily owner connects
gold-tree growth/death, mixed native/imported neighbours across acre boundaries,
sapling recording/counting, and source-priority overcrowding removal. Native
functions and imported-house protections remain intact. Four focused checks
pass; the first silent native component run passes 97 records and 75 assertions,
with restored state/checkpoint and clean exit. It executes daily-entry loading
and isolated-acre consumers, not
a full live-town renewal or hardware test. The shared code reservation adds 4 KiB;
assets, owner sizes, saves, and all 128 choices remain unchanged. Next connect
player interaction and planting effects. World collision, seasonal drop/cut counts,
and hidden-content replenishment are connected. Golden choices stay disabled. See the
[checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-daily-tree-growth).

Shared planting and tree-state rules remain installed. Shovel burial in a shining hole
uses the donor's gold-sapling conversion in all four seasonal owners. Core
growth/stump queries use complete donor tables for selected gold trees and retain
the original routines for native families. The code loads safely before any
seasonal actor exists and fits the existing reservations: no added RAM, scene
allocation, saved fields, or choices. Four focused checks pass. The first silent
native component run passes 150 records and 100 assertions, including lazy loading,
all four burial helpers, native fallbacks, guards, restored state/checkpoint, and
clean exit. It is not a full planting interaction, daily-growth, or hardware test.
Daily growth, neighbour/death rules, thinning, and collision are connected;
seasonal drops/cut counts are connected, while full player interaction and planting effects remain. Golden choices remain
disabled. See the [checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-planting-and-tree-state-runtime).

The proposal retains shared seasonal scenery. All fourteen gold-tree foreground
states use complete owner-local models, positions, descriptors, palettes, and
shadow dependencies. Each loaded season adds 32,864 bytes; an 8,192-byte fixed
reservation holds shared code. Verified retired cartridge storage avoids growing
the import blob or equipment module. Original scenery, held categories, actor
sizes, and saved/profile formats remain unchanged.

Four focused host/cartridge checks pass. The first silent native component run
passes 237 records and 122 assertions, including all four seasonal loads, all
56 selected type records, safe unselected/native fallbacks, actual body drawing,
memory guards, restored state/checkpoint, and clean exit. This is not GPU
appearance, ordinary acquisition, or hardware proof. Reuse the prepared assets
and this evidence. Full player interactions and planting effects remain;
the selected seasonal shovel-drop consumer is installed. Golden choices stay disabled.
The main lock and both served patchers remain unchanged. See the
[scenery specification](../specs/V3_SCENERY.md) and
[checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-seasonal-scenery-runtime).

The current explicit ABI-157 proposal retains the complete balloon integration.
All eight balloons are
connected through the shared parent-category installer: official names/prices,
complete pocket icons, held/inventory animation, source acquisition records,
collection/catalogue, animated room profiles, indoor conversion, and inverse
pickup. The local composer has 128 experimental choices, including 24 equipment
parents. These are not a public or hardware-ready handoff.

The complete separate flying-balloon actor is installed for all eight shapes,
with private model/motion banks, donor flight/hide behaviour, reflection drawing,
and actual selected-profile player creation. Existing native actors and resources
remain intact. Its code fits existing reserved space; selected profiles add
8,336 bytes of transient scene allocation including the player's pointer slot.
Four host/cartridge checks pass. Native components cover all eight resource
banks, two representative drawers, movement/hiding, and memory guards. The
focused current-build selection check passes 41 records and 26 assertions,
including restored state/checkpoint and clean exit. Interrupted full fixtures
are not claimed as passes; the checkpoint records corrections and reused evidence.
Release/look, inventory exchange, and fall/get-up consumers are installed.
The release action retains source positions, poses, head tracking, disappearance
and timing rules, native fish/insect behaviour, and deferred rewards. Missing
actors cannot consume a held balloon. Five focused host/cartridge checks pass.
Native release/fall and exchange checks pass, with preserved/restored live data,
memory guards, checkpoint restoration, and clean exits. The ordinary outdoor
`Let Go` menu is installed for all eight shapes, retaining indoor placement,
present/quest priority, the native pocket setter, and all 44 existing menu rows.
Four focused host/cartridge checks pass, including relocation, allocation,
optional composition, and no-loss rejection. The silent native menu check passes
92 records and 59 assertions, including actual cursor/A dispatch, pocket
replacement, return-tag initialization, the flight queue, state/checkpoint
restoration, fault/memory guards, and clean exit. Its final close callback is a
test stub; full ordinary gameplay and appearance remain unverified.
The menu needs 384 additional transient bytes; saved formats, choices, the main
lock, and both served patchers remain unchanged. Gameplay/hardware verification
and source acquisition remain; the four golden-tool choices stay disabled.
See the [menu checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-ordinary-balloon-menu).
See the [consumer checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-balloon-release-exchange-and-fall)
and the
[flight checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-flying-balloon-actor).

Shared inventory exchange carries the golden-shovel reward condition through
normal drop, empty hand, burying, and fish/insect/balloon release. Three existing
transient unions hold the deferred flag; ordinary requests clear it, rejected
requests do not overwrite it, and actual native setup/animation precedes the
reward. Two code groups fit unused ground/event reservations without module,
save, or allocation growth. Two sanitizer and three cartridge/composition checks
pass. The first silent native run passes 142 records and 92 assertions, covering
the actual loaded tag's empty/fish/insect branches, all four installed callbacks,
request clearing/rejection, setup, sampled release timing, guards, restored state/
checkpoint, and clean exit. Its menu-close callback is a test stub; bury setup
uses item zero, and release setup uses an existing actor. Ordinary world
placement/release and hardware remain unverified. The ordinary balloon menu is
installed; next implement source acquisition events. Golden choices remain disabled. See the
[exchange checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-reward-inventory-exchange).

All four non-exchange collection tails share the installed reward-completion
adapter: pickup, jump pickup, furniture pickup, and shovel put-away. The source
priority ordering, early returns, and full-pocket branches remain intact. One
424-byte code group fits existing space, with no save/profile/allocation change.
One sanitizer and three cartridge/composition checks pass. The first silent
native run passes 141 records and 102 assertions, including actual relocated
collection entries, first/repeated/unselected items, rejected requests, all four
players' completion queries, original exchange requests, guards, restored state/
checkpoint, and clean exit. These are component calls, not ordinary acquisition
or a hardware playthrough. The exchange stage connects normal/bury/fish/insect
endings; the ordinary balloon menu is installed, while source scene/NPC/tree acquisition remains required.
Golden-tool choices remain disabled. See
the [collection checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-reward-collection-consumers).

The shared reward-action category registers all twelve source callbacks for
both golden-tool celebrations and the golden-axe waiting action. Requests retain
native permissions and donor priorities; the axe wait preserves idle animation
continuity and source timing. The 308-byte request group and 668-byte wait group
fit existing unused space. No save, profile, resource, or allocation grows.
One sanitizer and three cartridge/composition checks pass. The first silent
native run passes 73 records and 53 assertions, including actual registered
setup/main transitions, priority rejection, the axe-wait handoff, persistent
settlement, unchanged code, guards, restored state/checkpoint, and clean exit.
It simulates the message-completed phase and samples the delay boundaries;
ordinary acquisition, full conversations, and hardware remain unverified.
The collection stage connects non-exchange pickup/put-away. Source scene/NPC/tree
acquisition and balloon-release consumers remain required.
The four golden-tool choices remain disabled. See the
[action checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-reward-action-registration).

Shared reward persistence and the celebration settlement callback are installed.
Format 3 appends 48 bytes for four players' distinct trophy and celebration
flags, retaining all existing selection and catalogue offsets. Valid NAFJ and
format-1/2 banks migrate with the new flags clear; older format-1/2 V3 builds
cannot load format-3 saves. Matching/equal-or-larger import profiles remain
required, and imported saves must not be loaded in V2. Preserve backups.
The 912-byte runtime allocation, codec, and helpers fit existing owned ranges;
no permanent reservation grows. Five focused host/cartridge checks and one
export-warning check pass. The
first silent native run passes 67 records and 50 assertions, including migration,
complete encoding, actual commit/settlement/player deletion, retained guards,
restored state/checkpoint, and clean exit. This is component verification, not
an ordinary save/restart or hardware test. The action stage connects registration
and request routes; source scene/NPC/tree acquisition remains required. The four
golden-tool choices remain disabled. See the
[persistence checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-reward-persistence).

The shared golden-tool celebration setup and per-frame controller connect the
installed motions, held-item handling, facial animation, and message phase.
All four source fanfare selections use complete existing native sequences and
fonts; all 60 referenced samples match the donor. The 1,036-byte callback group
fits unused icon-reservation space without moving resources or changing saves.
One sanitizer and three cartridge/composition checks pass. The silent native
retry passes 46 records and 34 assertions, including real animation setup and
one frame, fanfare requests, native segment behaviour, unchanged saved data,
restored state/checkpoint, and clean exit. The first run also verifies all four
fanfare request/delete pairs before its incorrect segment-retention assertion.
No actual game-code defect is found: the unchanged native animation combiner
leaves the lower bank selected in segment six. Reward actions are registered;
ordinary acquisition events remain unimplemented, so the four golden-tool
choices remain disabled. See the
[control checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-reward-controls-and-fanfares).

The shared golden-tool message phase imports all four complete official messages
and preserves their wording, pages, colours, and commands. A 604-byte callback
group fits unused space between the inventory-bobber helper and artwork. Native
timing retains the donor delay; the continuation lock remains until animation
completion, and the controller waits for the report to close. All four source
credits are in the single provenance catalogue. No save, profile, import-blob,
or resident allocation grows. One sanitizer and four cartridge/composition
checks pass. The first silent native run passes 115 records and 98 assertions,
including full message loads, phase transitions, guards, unchanged saved data,
restored checkpoint, and clean exit. The fixture temporarily routes an unused
callback slot; ordinary reward events are not yet connected. The action stage
connects registration and request routes; source acquisition is next. The four golden
tools remain disabled. See the
[message checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-reward-messages).

The shared player-animation category includes both complete golden-tool reward
motions and source eye/mouth timelines for all installed player motions. The
53-frame celebration motions fit the existing 3,848-byte banks. A 200-byte reader,
1,272-byte table, and 213 bytes of deduplicated complete face timelines fit the
existing 72-KiB module. Checked retired-resource storage limits ROM-blob growth
to 3,072 bytes; native tables, existing resources, and saved formats remain.
One sanitizer check and four cartridge/composition checks pass. The first silent
native run passes 165 records and 123 assertions, including both full transfers,
30 actual native facial frames, segment restoration, guards, restored checkpoint,
and clean exit. Skeletal playback and ordinary reward events are not established
by that component check. Golden-tool choices remain disabled pending ordinary
acquisition. See the
[reward-motion checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-reward-motions-and-player-faces).

Both wrapped-item name readers use the official GameCube `present` label with
their original ten- and sixteen-byte output limits. Selected aliases share the
existing present name; disabled aliases leave the output untouched. Four source
credits live in the single provenance catalogue. The 184-byte adapter and
712-byte shared reader fit existing reservations without changing saved data,
choices, or resource allocations. One sanitizer check and four cartridge checks
pass; the first silent native check passes 101 records and 60 assertions,
including both actual readers, bounded unaligned writes, original-item fallback,
zero gift prices, memory guards, restored checkpoint, and clean exit.
Ordinary reward acquisition and hardware remain open. See the
[name-reader checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-wrapped-gift-names).

Shared wrapped-gift transport connects all four golden-tool identities through
native pocket insertion, exchange-hand initialization, and field exchange. Pockets
contain the actual tool plus its wrapped condition; disabled aliases are rejected.
The category reader uses existing present artwork without indexing beyond the
native miscellaneous table. The module occupies 72 KiB, preserving prior resource
addresses. The shared installer stores changed compressed overlays in checked
unused cartridge space without consuming the bounded import-object region.

One sanitizer check and four cartridge/composition checks pass. The first silent
native run passes 308 records and 202 assertions, including four-player pocket
handling, full/unselected rejection, 14 relocated menu-hook windows, live register
and memory guards, restored state, and clean exit. The private browser worker
matches offline empty/all/mixed/equipment outputs; its export stays unserved.
These are component checks, not ordinary reward acquisition or hardware tests.
Golden-tool choices remain disabled pending acquisition and reward demos.
The field setters preserve full item halfwords, and the save codec preserves
the original payload; neither needs an extra item-ID filter. Ordinary wrapped
exchange/save gameplay remains unverified. See the
[wrapped-gift checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-wrapped-gift-transport).

All four golden-tool parents have official names/prices, complete pocket icons,
collection bindings, and catalogue models through the shared category installer.
Their active-tool selectors retain native actions rather than passive-item rules.
The four new icons occupy their checked 4-KiB extension, with all old resource
addresses retained. Acquisition and reward demos remain
unfinished, so these four choices and their catalogue completion counts stay
disabled. The existing 128 choices and saved profile are unchanged.

One sanitizer check and four cartridge/composition checks pass. The first silent
native run passes 182 records and 117 assertions, covering all four complete
catalogue transfers, English readers, active-tool selection, ten pocket-icon
cases, register/memory guards, restored state, and clean exit. It temporarily
selects the pending tools in isolated fixture data; it does not establish
ordinary acquisition, appearance, or hardware. The private browser worker
matches offline empty/all/mixed/equipment profiles from both supplied games;
the export stays unserved. See the
[parent checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-golden-tool-parent-category).

All four golden-tool inventory previews use their complete installed models and
motions through shared source-derived records. The rod includes its separate
960-byte donor bobber, retaining its native-format palette/texture data. A
56-byte pointer helper preserves the original rod, transforms, and graphics
allocation. Existing previews, the 64-KiB module, saved formats, and 128 choices
remain unchanged; no golden-tool option is enabled. Four focused checks pass.
The silent native retry passes 132 records and 116 assertions, covering actual
loading/animation/draw dispatch, complete joint/accessory lists, ordinary-bobber
fallback, live registers, guards, checkpoint restoration, and clean exit.
Ordinary inventory/gameplay and GPU/hardware appearance remain unverified.
See the [preview checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-golden-tool-inventory-previews).

The shared tool-input adapter connects all four active tool families to the
native input predicates while retaining their real kinds and existing scene/
profile rules. Pickup and tree shaking also recognise imported passive items
correctly; umbrella-spin behaviour stays separate. The 132-byte adapter fits
the existing code reservation without moving any prior callback or constant.
Four focused checks pass. The silent native check passes 128 records and 106
assertions across the six real controller functions, original/golden-family
kinds, pressed/held inputs, rejection paths, guards, state restoration, and clean
exit. Extended kinds use temporary fixture data, not enabled golden-tool choices.

Shared action setup connects the thirteen imported net/rod animations to their
native action requests, preserves the actual equipment kind, and retains the
rod's bobber during animation changes. The original net/rod drawers match the
complete source skeletons and stay unchanged. The 688-byte adapter uses existing
unused code space; no asset, selection, saved format, or allocation grows.
Four focused checks pass. The first silent native check passes 128 records and
102 assertions, including actual model/motion loading, complete drawing commands,
original-tool setup, rod movement speed, bobber lifetime, guards, restored
checkpoint, and clean exit. GPU appearance and ordinary gameplay are not proven.

The four remaining net request/transition checks use the shared family reader,
and fall/get-up setup preserves imported net identity with the proper stopped
animations. Non-net tools retain their default recovery motions and repeat mode.
Four focused checks pass; the first silent native run passes 255 records and
218 assertions, covering actual requested actions/priorities, slip input exits,
hidden/unselected rejection, recovery loading, guards, checkpoint restore, and
clean exit. Complete ordinary gameplay and appearance remain unverified.

Golden-net capture uses the donor's 21/60 radius/span, while original and
ordinary imported nets retain 15/50. Native collision math, requested-radius
endpoint tolerance, candidate ordering, and forced-capture priority remain.
Four focused checks pass; the first silent native run passes 244 records and
179 assertions across 53 collision cases, bounds, immutable actor/save state,
restored selectors, checkpoint restore, and clean exit. The 184-byte helper fits
existing space without allocation/save changes. These are isolated component
checks, not ordinary golden-net gameplay or hardware. See the
[capture checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-golden-net-capture).

Golden-rod response is connected in both fish behaviours. Detection angles and
bite windows use the source golden values with native timing; normal fishing,
detection distance, fish identities, and existing state updates remain. Four
focused cartridge checks pass. The first silent native run passes 190 records
and 142 assertions, including 82 actual angle windows, 32 complete bite setups,
unselected rejection, guards, retained state, checkpoint restore, and clean exit.
The 248-byte suffix uses existing resident space; the shared builder relocates
the compressed fish owner and adds 8,816 ROM bytes. No saved/profile/actor format
changes. These component checks do not prove ordinary fishing or hardware.
See the [rod checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-golden-rod-response).

Golden-shovel digging uses the actual player's cached kind and retains native
foreground/hole/buried-item processing. A new eligible position gives the donor's
10% chance of 100 Bells; ordinary digs also update the previous-position state.
The shared module grows to 64 KiB using checked retired sequence storage, with
all prior code and state addresses retained. One sanitizer check and four
cartridge/composition checks pass. The first silent native run passes 186 records
and 174 assertions across 29 cases, real hook/argument passing, native RNG, state,
guards, checkpoint restore, and clean exit. Most cases inject the native digging
result to isolate the new suffix; one negative-position case executes the complete
native cancellation path. This does not establish ordinary terrain digging.
See the [shovel checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-golden-shovel-digging).

The golden-axe durability audit finds no extra wear adapter is needed: the
donor golden identity remains unchanged, and the retained native axe request/
action path does not wear equipment. This is source/cartridge evidence, not
ordinary gameplay. Next complete shared tool acquisition and reward demos.
The donor's balloon-loss-on-get-up path also remains an explicit shared behaviour
dependency; it is not implemented by the net recovery adapter. Keep tool choices
disabled. Continue from the current lock and retain completed evidence. See the
[transition checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-net-transitions-and-tool-recovery),
[motion checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-tool-animation-setup) and
[tool-control checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-tool-input-predicates).

The shared installer repairs actual room-footprint metadata, permits the native
eight-byte graphics alignment, and combines catalogue/icon owner edits without
losing the catalogue's final 16 bytes. Twelve focused checks pass; the current
combined native check passes 216 records and 151 assertions. The source models,
128 choices, fixed identities, and saved formats are
retained. The current checks cover complete catalogue loading, all 24 parent
conversions/order, representative animated previews/icons, register/memory guards,
retained saves, restored checkpoint, and clean exit.

The unserved private export `build/v3-room-parent-browser-01/` remains ABI 127,
not the repaired cartridge. Its actual worker/composition checks remain evidence
for unchanged browser code; it is not the current playtest output. Both served
V2 patchers and the main lock remain unchanged.

The isolated two-balloon profile visibly renders the placed red balloon and
returns its parent item through normal pickup. Ordinary Save & Quit completes,
and both actual FlashRAM banks match independent format-2 reconstruction. A
fresh process restores the saved room form and visibly renders it. That run's
additional pickup assertion fails, so post-reload pickup remains unresolved;
the full scenario is not a pass. Exact results and limits are recorded in the
[gameplay checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-room-gameplay-repairs).
Reuse the unchanged equip/put-away evidence; a seeded pocket does not establish
ordinary acquisition. Continue shared net/rod/golden-tool actions. Broad gameplay,
other category interactions, and original hardware remain unverified.

All eight balloon inventory
previews use their source idle animation and reflected drawing. Existing fan and
pinwheel records, timing, resources, selections, and saved formats are retained.
Three focused checks pass. The first silent native run passes 141 records,
including 103 component assertions and four final fault/memory checks, covering
four representative balloon/pinwheel previews and checkpoint restoration.
GPU appearance, ordinary inventory interaction, and hardware remain unverified.

The shared converter prepares all eight complete room-balloon models, skeletons,
and animations at `build/v3-indexed-room-rigs-prepared-01/`. The category needs
44,400 ROM bytes; each object fits the existing room bank. Four new category
checks, four shared pipeline checks, and seventeen affected held/keyframe checks
pass. No cartridge or selectable choice is added by asset preparation.

Existing choices remain; eight balloon choices are added. Format-2 saves and
exact V2-12 empty output are retained. Saves using the new imports require a
matching or larger profile; older profiles lacking them reject those saves.
Do not load imported saves in V2, and do not treat removing imports as migration.
See the [inventory checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-balloon-inventory-previews).
The [parent checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-animated-room-parent-category)
records integration, exact hashes, and remaining ordinary-gameplay checks.

The retained ABI-124 proposal at `build/v3-balloon-actions-02/` installs shared
balloon setup, hand-motion tracking, sway/spring animation, and reflected drawing.
The player owns 48 additional transient bytes; no saved field is changed.
The shared equipment module is 60 KiB. An adjacent audio sequence moves intact
through its actual native header, making room without changing any sound data.

Five focused checks pass. The first silent native run passes 148 records and
96 assertions, covering two complete balloon rigs, two retained pinwheel rigs,
actual initialization/hand tracking/animation/drawing commands, matrix and memory
guards, saved-state retention, checkpoint restoration, and clean exit. This is
component execution, not GPU appearance, ordinary gameplay, or hardware proof.

Use the ABI-136 lock above for continued work. Reuse the
passing eight-vector player/inventory allocation evidence. The main lock and
both patchers stay unchanged. See the
[balloon-action checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-balloon-actions).

The explicit ABI-122 proposal at `build/v3-rig-capacity-03/` installs all twenty
complete animated equipment rigs through shared category discovery. Both outdoor
model/animation banks hold 7,168 bytes; the player has eight-vector joint and morph
arrays in an enlarged transient allocation. It retains the 120 experimental
choices, complete existing imports, format-2 saves, and exact V2-12 no-import
output. Resource availability does not enable balloon or net/rod gameplay.

Six focused checks pass. The silent native check passes 116 records/93
assertions: alternating complete models/animations, actual player initialization,
small and maximum-size joint/morph playback, old-array retention, guards, saved
state retention, checkpoint restore, and clean exit. Ordinary gameplay and
hardware are not established. The inventory proposal above retains these bank
changes; next connect source-correct balloon previews and remaining
parent consumers.
The main lock and both served patchers stay unchanged. See the
[capacity checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-rig-capacity-and-resource-extension).

The shared graphics converter prepares all twenty animated equipment rigs,
including the twelve remaining balloon/net/rod roots in
`build/v3-held-matrix-prepared-02/`. Complete joint-matrix commands, partial
vertex-cache loads, and IA8 intensity/alpha conversion preserve articulated
geometry and transparency. The new bundle contains 46,976 bytes, 1,219 vertices,
and 850 triangles; existing pinwheel assets are retained without recompilation.
Thirty-five focused checks pass, including complete donor/native comparisons,
matrix ownership, material stride/format, and installed-resource retention.

The complete assets are installed by the explicit capacity proposal above,
not exposed as twelve newly playable imports. Balloon inventory work
and remaining consumers are still required; net/rod gameplay integration also
remains open. Conversion and installation retain separate checked category
contracts. See the
[graphics checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-joint-matrix-and-ia8-conversion).

The explicit ABI-121 proposal at `build/v3-held-category-02/` connects all
eight pinwheels through shared parent discovery, names/prices, pocket artwork,
collection, catalogue, and individual offline/browser selections. It retains
all eight fans and their fixed identities. There are 120 experimental choices:
20 villagers, 81 furniture items, three shirts, and 16 equipment parents.
The refresh consumes complete prepared assets and source-category records;
it adds no per-item installer, runtime action code, or resident allocation.

Six focused current-cartridge/composition/save-codec checks pass. The native
catalogue check passes 128 records/86 assertions, including source ordering,
all 16 ownership entries, representative English names/prices/model transfers,
disabled-item hiding, original umbrella retention, guards, and restored state.
The corrected native purchase fixture passes actual 680-Bell transactions,
ownership recording, shortage/full-pocket rejection, handover requests, and
original-ware retention. Both runs restore their checkpoints and exit cleanly.
The actual browser worker matches offline empty/all/mixed/equipment outputs
using both supplied games. Its unserved export is
`build/v3-held-category-browser-01/`; neither served patcher changes.

Continue from `build/v3-shared-tool-controls-02/build-lock.json` explicitly. Retain
passing animation, sound, and inventory evidence for unchanged implementations.
The 60-KiB equipment module, 15,584-byte inventory bank, and format-2 save layout
retain their current ownership; outdoor banks hold 7,168 bytes each. Pinwheel profile bits require a
matching or larger profile; older builds lacking them reject these saves.
Imported V3 saves remain unsuitable for V2. Empty selection returns exact V2-12.

Ordinary equipped-pinwheel gameplay, acquisition, persistence, listening, and
hardware remain unverified. All four seasonal setter-copy routines have passing
complete-return component evidence on this cartridge. The prior stack mismatch
depends on stopping at an internal return instruction; it is not reproduced
across the complete epilogue. The overall focused run remains partial because
of a final guard-expectation typo, and full seasonal rendering/gameplay remains
open. No cartridge change is needed for the tested copy operation. See the
[diagnosis](checkpoints/V3_FURNITURE_PIPELINE.md#seasonal-setter-copy-diagnosis) and
[category checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-parent-category-expansion).

The current ABI-116 two-fan profile has an isolated festival-night fixture with
no seeded item or ownership. Normal town entry, original inventory, the festival
vendor/visitors, and stall scene loading are observed. The generic NPC approach
stops at the counter before opening dialogue, so an ordinary purchase, payment,
handover, and earned ownership are not established. The usable pre-interaction
checkpoint is `build/v3-festival-near-stall-01/`. The navigation batch's setup
retry is spent; do not replay it. Continue shared animated-held native integration
and remaining acquisition implementation, retaining the ordinary transaction and
catalogue-delivery checks as open. See the
[festival checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#ordinary-festival-acquisition-setup).

The explicit ABI-116 proposal in `build/v3-translation-headers-02/` includes
the Museum-header correction in both reading and editing, and fixes the ordinary
reader's missed imported-villager bound. It preserves all 112 experimental
choices, selected profiles, saved formats, acquisition code, and artwork. Empty
selection returns exact corrected V2-12 through both composition paths.
The native component check passes complete cartridge-loaded overlay relocation,
Museum/player/original/imported/fallback names, saved-data retention, guards,
and checkpoint restoration. Seventeen focused checks pass; fourteen browser/
offline composition profiles match. The actual silent browser worker reconstructs
matching empty, all-installed, mixed, and equipment outputs from both supplied
games. Ordinary letter appearance and hardware remain
unverified; the older rendering fixture is not relabelled as passed.

The current ABI-121 proposal retains these translation changes. Ordinary
acquisition and order/delivery remain open; continue
shared category implementation without replaying exhausted navigation batches.
Both served patchers remain unchanged. See the
[translation checkpoint](checkpoints/MUSEUM_LETTER_HEADERS.md#v3-integration).

The two-fan ABI-115 profile has ordinary inventory/equip, put-away, ground-drop,
and same-profile game-save/restart/load evidence for parent `2255`. The English
`plum fan` name, icon, miniature/outdoor held model, and dropped artwork display.
`build/v3-equipment-save-01/` completes gyroid Save & Quit; both actual FlashRAM
banks match independent format-2 re-encoding. A fresh process in
`build/v3-equipment-reload-01/` restores the equipped parent, all expected
pockets, and its collection bit. Fault and resident/equipment/save-state guards
pass. These scenarios use normal buttons and read-only observations, never
live-memory edits. The source save remains untouched.

Pickup remains unverified: the house forces the dropped item away from the
player, and the bounded navigation retry stops about 21 units from it before
issuing pickup. The corrected limit/radius is unexecuted; do not replay that
failed setup. Ten focused observation/navigation checks pass. Next pursue
ordinary reward acquisition/catalogue delivery, retaining the seasonal rendering
and gameplay checks as open. The main
lock stays ABI 109; this evidence is for one copied town/profile, not every
parent, cross-profile migration, or hardware. See the
[persistence checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#ordinary-equipment-put-away-drop-and-persistence).

The proposed ABI 115 in `build/v3-held-selection-02/` connects individual
equipment choices through the shared offline/browser composers. Its 112
experimental choices include eight fan parents; catalogue representations are
not extra choices. Selected umbrella rows/counts follow the parents, while
empty selection retains exact V2-11. The private Equipment filter supports
individual and group selection. The full reference enables eight profile bits;
gameplay code, artwork, saved format, and allocations remain unchanged.

Nineteen focused checks pass across the combined run and corrected codec fixture;
nine JavaScript checks pass. Browser/offline ROM equality covers fourteen
representative profiles. Actual silent-browser downloads match for a two-fan
subset, mixed villager/item selection, and no imports. The complete interface
check remains partial: a later same-file invalidation assertion failed, and
the corrected genuine-input-change fixture is unexecuted. Preserve these
successful downloads instead of replaying the full setup. The prior catalogue's
104-record/70-assertion native result applies to unchanged runtime code.

Next complete ordinary
acquisition, pickup, and order/delivery gameplay on the current selected build.
Use the ABI-121 proposal lock; the main lock remains ABI 109. Do not hand over
this proposal as validated. Saves containing fan selections require those bits;
older profiles reject them. Codec acceptance of equal/superset profiles is tested,
but ordinary cross-build reload and hardware are not. Both served V2 patchers
remain unchanged. See the [selection specification](../specs/V3_OPTIONAL_COMPOSITION.md#shared-equipment-selections)
and [checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-held-parent-selections).

The proposed ABI 112 in `build/v3-event-menu-06/` connects the shared fireworks
stock to an explicit original/imported-wares selector, English item pages,
native pocket/payment checks, actual insertion/debit, and handover requests.
Original merchandise and unlimited-fruit behaviour remain intact; imported
categories use finite, selected-only stock. The equipment module is 52 KiB,
and the vendor gains four transient bytes without changing saved formats.

Four focused checks and twelve optional-composition tests pass. The corrected
silent native run passes 178 records with 73 assertions, including loaded-owner
callbacks, both routes, full names, full-pocket/short-money rejection, actual
pocket insertion and payment, single-sale consumption, handover requests,
sold-out retention, memory guards, and restored globals/checkpoint. Ordinary
conversation, rendered animation, catalogue ownership, and save/reload are not
established by this component check.

Four source-tracked messages correct the original route's merchandise/prices
and provide its route question; all 12,007 existing messages remain unchanged.
Official GameCube introductions remain on the matching imported route. The
single provenance catalogue credits every adaptation and new label. All
handheld choices remain absent from the served patchers. The current explicit
proposal connects collection/catalogue and optional selection; ordinary gameplay
is still required. Reuse the installed shared consumers and prepared models.
The main lock stays ABI 109 pending combined gameplay verification. See the
[checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-event-menu-and-transactions).

The proposed ABI 110 at `build/v3-ground-categories-02/` implements the shared
seasonal ground adapter: all four renderers, their complete category tables,
loaded-owner constructors, appended actor indices, expanded setter stacks,
and twelve furniture-type windows. The global category reader preserves its
original fallback without recursion. The module is 44 KiB; no artwork is
reconverted, and no handheld choice or saved format changes.

Six focused tests and twelve composition tests pass. Native startup, selected/
disabled/original categories, the complete cherry owner/table, four constructor
index pointers/counts, and local-array clearing pass. The setter-copy window
has a breakpoint-dependent continuation/stack assertion, classified by the
current complete-return checks above. Remaining seasonal execution,
drawing, final guards, and checkpoint restoration are not established. The
main lock remains ABI 109; do not hand over the proposed build as validated.
See the [checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-seasonal-ground-runtime).

Current ABI 109 at `build/v3-category-runtime-03/` installs the nine complete
equipment category graphics, shared police/handover tables, and selected-parent
category lookup. Native categories remain unchanged; added categories use
`27 + donor category`, so fans use native category 70. Police start arrays,
stack storage, actor allocation, matrix-list offsets, and drawing bounds expand
together. The shared equipment module is 40 KiB; police actors grow by 88 bytes.

Five focused tests and twelve current-composition tests pass. The first silent
native run passes 63 records with 44 assertions: complete startup resources,
selected/disabled categories, both loaded owners, all 70 police start indices,
257 matrix nodes, original/imported police drawing, five handover windows,
guards, and restored profile/checkpoint. This is component execution, not GPU
appearance, ordinary acquisition, or save/reload verification. See the
[checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-police-and-handover-runtime).

The proposed adapter connects all four seasonal consumers and the global
item-type wrapper. Current ABI 121 supplies shared acquisition, collection,
catalogue, and optional selections for fans and pinwheels. Full seasonal
rendering and ordinary gameplay remain open; both served patchers stay unchanged.

The retained ABI 108 integration connects the inventory
screen's separate equipment selector, all eight shape/animation/draw tables,
and owner-relative callbacks through shared source-derived records. All eight
fans reuse their complete installed models and holding poses. Original tools
and the empty-item sentinel remain intact. The equipment module is 28 KiB;
ordinary model/animation banks and saved formats are unchanged. No fan profile
bit or browser choice is enabled.

Four focused checks and twelve current composition checks pass. The silent
native run passes 104 records with 79 assertions: loaded-owner relocation,
selected/disabled kinds, complete model/pose transfers, actual imported and
original axe/shovel draw dispatch, all pocket-icon control cases, memory guards,
and restored profile/checkpoint. Ordinary inventory appearance, full construction,
equip/put-away gameplay, persistence, and hardware remain unverified. See the
[checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-inventory-equipment-previews).

Source fan category 43 is distinct
from the donor menu's ID-derived tool category two; do not use it as an unchecked
native menu index. The fan profile includes the shared category, collection,
catalogue, and composition adapters described above. Ordinary acquisition,
pickup, and ordering/delivery remain work. The corrected-header proposal includes
the Museum fix; both served V2 patchers stay unchanged.

The shared category converter prepares all nine ground/police/handover artwork
categories used by 43 extra equipment parent/state records in
`build/v3-item-category-art-02/`. Complete textures, palettes, vertices, and
separate material/geometry lists occupy 7,344 bytes. Seven focused checks pass,
including every texel/colour/vertex/triangle, all six source-owner relationships,
source mutation rejection, matrix-safe list splitting, and unchanged ordinary
model emission. The police/handover adapter installs these assets as described
above; seasonal ground integration remains. They are not 43 new playable items. See the
[checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-ground-and-handover-artwork).

ABI 104 registers fan action 109's complete setup/main/net-reset group and its
four ordinary input polls through the shared importer. A complete core-bound
audit preserves unrelated native limits and umbrella repeat behaviour. Native
release/repeat handling retains events crossed in one update or at the animation
wrap. Action code occupies 1,944 bytes without allocation growth.

Four focused checks pass in 5.692 seconds, including host sanitizers, source/
relocation guards, and patch reconstruction. The corrected silent native run
passes 60 records with 37 passing assertions: real action dispatch, complete
swing, release to movement, guards, and restored live actor/animation banks and
checkpoint. It fixes an actual skipped-release bug found by the initial run,
not a test-setup failure. Held-A repeat and idle-after-wrap have host evidence;
ordinary equipped-fan use and full scene rendering remain unverified. Twelve
current composition checks pass, including exact no-import V2, all-import ABI
104, dependencies, sparse profiles, and the real save codec. See the
[checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-fan-action-activation).

The shared converter handles all 27 player action tables and both held-item
main/draw tables. All 105 native actions and 21 native held categories remain
intact. Fan category 23 draws complete static held models; balloon/pinwheel
categories use their installed rig callbacks. Fan action 109 and reward actions
118–120 are registered; twelve unfinished actions remain disabled. The native dispatch
resolves the currently loaded player owner. The
[held-draw evidence](checkpoints/V3_FURNITURE_PIPELINE.md#shared-held-item-dispatch)
and [sound evidence](checkpoints/V3_FURNITURE_PIPELINE.md#shared-sound-programs-and-per-frame-actions)
remain applicable to unchanged dependencies. The fan's complete source pitch
sweep, envelope, and sample are retained without enlarging the audio heap.

The complete 24-KiB module transfer is checksum-bound; startup remains 952 of
992 bytes. Models, motions, actor sizes, animation banks, saved format 2, and
104 choices remain unchanged. No fan is offered as a selectable import yet.
Next integrate inventory categories/acquisition
and context-correct catalogue/persistence. Do not
repeat passing component checks or create per-item scripts. Original-hardware
testing and ordinary equipped-fan gameplay remain pending.

All six equipment-kind lookups use one source-derived
record format: holding pose, item routine, shape, equipment motion, tumble, and
get-up. The 79 donor kinds retain stable indices without changing original tools.
All twelve installed player motions fit the original banks. The complete
transition motions retain their source timing and 5,744 ROM bytes. Their prior
focused/native evidence remains applicable; the current native run also checks
representative transfers, masks, and original/extended kind lookups.

Fourteen held models and sixteen equipment animations retain their complete
31,584 bytes and the passing shared-loader evidence. There are no new selectable
items yet: native kind selection, actual actions/controllers, rig buffers,
inventory/acquisition, and optional profiles still need integration. Combined
model/animation size is checked for all nineteen installed static item/state
resource pairs; unsupported rigs remain explicit dependencies.
See the [checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#shared-equipment-kind-readers).

The shared handheld pipeline prepares a complete 7,760-byte motion bundle:
sixteen equipment animations, six constant player poses, fan idle, and fan
swing. Twenty skeleton descriptions retain actual joint/model dependencies;
their geometry and player integration remain separate work. Complete source
selectors connect all 79 equipment identities/states to their real holding
animations. The shared keyframe format preserves every constant, frame, value,
velocity, hierarchy, and relocated pointer without resampling. Fourteen focused
checks pass across the initial run and one corrected mutation fixture. The
player and equipment motions use the shared loaders above. Continue native
player ownership and action/animation binding using these
resources. See the [checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#held-motion-dependencies).

The [shared handheld adapter](../specs/V3_HANDHELD_ITEMS.md) discovers all 79
donor equipment IDs/states and prepares fourteen actual held models in one
batch: eight fans, ordinary/golden shovels, and four axe appearances. The
25,888-byte batch retains 334 vertices and 244 triangles through the existing
complete furniture graphics converter. Nineteen item/state records share these
fourteen roots. Animated equipment and separate umbrella owners retain their
missing dependencies; no static substitutes or selectable imports are created.
Eleven focused checks pass, including complete artwork and unchanged current
furniture output from the shared compiler. The full donor inventory carries the
same equipment dependencies without duplicate identities. Native player actions,
model ownership, readers, acquisition, catalogue, and profile integration remain
work; resource installation alone does not enable them. Saves and both patchers
remain unchanged. See the
[checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md#actual-held-model-batch).

The shared importer distinguishes ordinary room drops from catalogue/collection
representations using all four actual donor calls and three complete consumer
implementations. Tools, golden tools, fans, pinwheels, and diaries retain their
parent IDs when dropped indoors; worn axes retain wear. Eight balloon aliases
use their display IDs in both contexts. Generated records expose the actual
output IDs for every input/context, preventing an unconditional furniture
conversion from being mistaken for faithful parent-item support. Eight focused
checks pass; full donor inventory and current furniture scan regenerate
successfully. This is importer integration evidence, not new gameplay or new
selectable items. The development ROM, saved format, and both patchers remain
unchanged. Continue actual parent readers/actions/acquisition and context-correct
catalogue integration using the prepared models.

The shared native room-alias adapter uses generated parent/display records for
conversion, pickup, names, prices, ownership, footprints, and garment lookup.
All three installed garments use this path without adding new item choices.
Shared runtime updates run through the existing importer with
`--refresh-runtime`; artwork, resource allocations, saved identities, and
profile bits remain unchanged. Twenty focused host/cartridge/composition checks
pass. The corrected current native run passes 187 records with 177 assertions,
including all rotations, English names, prices, native footprints, independent
selection rejection, original fallbacks, restored state, and guards. See the
[checkpoint](checkpoints/V3_FURNITURE_PIPELINE.md).

Current development uses ABI 106 at
`build/v3-held-parent-readers-01/animal-forest-v3-asset-loader.z64`, pinned by
`config/v3-import-build.json`. The 104 choices and saved format 2 are unchanged.
Same-profile compatibility with ABI 104/105 is expected in both directions; this
batch does not claim another ordinary save/restart or hardware playthrough.
The 48 additional donor aliases still need native parent support and integration;
prepared artwork alone is not a completed import. Both served patchers remain V2.

The [indexed model-sequence category](checkpoints/V3_FURNITURE_PIPELINE.md)
automatically converts all 24 fan, pinwheel, and tool display models in one batch:
46,832 bytes, 852 vertices, and 566 triangles. Complete source verification
preserves 44 original model parts across 26 native lists, including both fishing
rods' translucent layers. Material and geometry lists retain their actual order;
no per-item script or runtime callback is added. Parent-item and room-conversion
dependencies remain explicit, so these are prepared assets, not new selectable
imports. Converter/installer revision 9 supplies these prepared assets without
enabling unfinished parent items or changing either served patcher.

The shared [room-alias discovery](checkpoints/V3_FURNITURE_PIPELINE.md)
connects 48 room-display models to parent items across balloons, diaries, fans,
pinwheels, ordinary tools, and golden tools. Complete donor placement/pickup and
index functions supply the ranges; the seven worn-axe states also map to their
actual single parent. The full donor catalogue, furniture scan, prepared-asset
records, and browser review data consume this relationship. Forty-four aliases
occur in the `3xxx` furniture queue. They cannot install as unrelated furniture;
their missing parent/room support and separate artwork gaps remain explicit.
Room-alias discovery itself changes no cartridge code or saves.
Both served V2 patchers remain unchanged.

The [constant model-sequence category](checkpoints/V3_FURNITURE_PIPELINE.md)
installs Lady Liberty and the tanabata palm automatically, including all 11,152
artwork bytes, 248 vertices, and 179 triangles. Complete draw-only callback
verification supplies ordered model links to the normal native renderer;
there is no new runtime callback, per-item installer, or memory reservation.
Official names, Gulliver/event acquisition, catalogue, scoring, and optional
selection use the shared pipeline. Automatic additions total 42.

The installed constant-model-sequence batch retains its passing ABI-95 evidence
at `build/v3-furniture-static-sequence-runtime-01/`. Its suite passes 59 checks;
one scoring-alias test is inapplicable to this batch. The first silent native
run passes 124 records and 85 assertions, including complete model DMA,
source framing, selected-only rewards, event stock, ownership, restoration,
and guards. Ordinary appearance, interaction, full catalogue construction,
save/restart, and hardware acceptance remain open. Saved format 2 is unchanged;
saves containing these identities must not load earlier builds or V2.

The [shared palette-fade category](checkpoints/V3_FURNITURE_PIPELINE.md)
discovers and converts eight complete building models in one batch: 29,664
artwork bytes, 555 vertices, and 346 triangles. Complete callback-code and
dependency checks identify the shared behaviour without an item allowlist.
Generated layouts retain every model layer, both palettes, and the light fade.
One native implementation also handles the existing tent's unchanged artwork
within its existing memory reservation. The igloo installs automatically through
the supported winter-camping reward route; the other seven retain actual missing
acquisition routes.

The palette-fade checkpoint preserves its passing native callback evidence;
that installed code is unchanged in the current cartridge. Sanitizers cover all eight prepared
objects and the retained tent. The corrected eight-MiB native run passes 190
records with 114 assertions, including both callback layouts, full model DMA,
palette lifetime, seasonal rewards, acquisition/ownership, and guards.
Ordinary model appearance, interactions, full catalogue construction, and
save/restart remain unverified. Saved format 2 is unchanged, but saves containing
the new identity must not load older builds or V2. Both served patchers stay V2.

The [private browser interface](checkpoints/V3_BROWSER_INTERFACE.md) supplies
search, individual/category/all/clear choices, disclosed villager requirements,
save warnings, and ROM/profile downloads. Its 101 choices come from installed
records, with 164 unavailable furniture entries and actual reasons generated by
the shared pipeline. The interface downloads the selected Punchy/snow-bunny build
with the exact offline hash, including the required shirt and speed bag. Initial
selection, dependency removal, category controls, review reasons, cancellation,
and discarded late results pass. Later invalidation/layout checks remain
unexecuted after two classified test-setup failures; the checkpoint preserves
the stopping points instead of claiming a complete interface pass.

Nine synthetic browser tests and four current-build Python tests pass, including
eleven browser/offline equivalent selections and complete/disjoint review data.
The [underlying composer](checkpoints/V3_BROWSER_COMPOSITION.md) retains its
recorded no-import/all/subset worker results. The page binds the worker to the
exact displayed plan hash. Exports remain unserved; both V2 sites are unchanged.
Browser-native graphics conversion, full donor classification, and gameplay
acceptance remain unfinished. The interface work itself changes no runtime or save format.

The [automatic furniture pipeline](checkpoints/V3_FURNITURE_PIPELINE.md) supplies
forty-two additional items through source-discovered records and shared graphics,
metadata, acquisition, catalogue, scoring, and profile installation. No per-item
installer, graphics description, or native scenario is needed. Converter/installer
revision 9 includes winter-camping rewards, shared winter/summer selection,
data-driven palette callbacks, constant model sequences, and parent-item alias
classification/indexed model sequences. No item-specific browser entry is required.

The development cartridge uses source-derived canonical reward records
for camping and Gulliver. No summer-item array is maintained in the runtime.
The 948-byte shared reader preserves exclusions, small-list duplicate allowance,
and safe exhausted-profile fallback. Winter retains the donor's 10% special-list
roll, summer its 20% roll, and both the subsequent house-gift chance. Winter with
no selected imports retains the unchanged original native trade body. Camping
and Gulliver items stay non-orderable, not ordinary shop stock. The trade suffix
uses 1,152 bytes within its existing 1,344-byte allocation. Official names remain
credited in the single text-source catalogue. Scoring-only category aliases keep
the donor's 412-point weights without changing actual acquisition. No permanent
RAM reservation or saved format grows; existing models and identities remain unchanged.

The offline composer contains 104 installed development options: 81 furniture,
three shirts, and twenty villagers. The generated browser plan consumes that same
lock. The recorded private interface export above remains the 101-choice export;
it is not a served V3 site or a claim of fresh interface testing on ABI 95.

The shared CI4/I4/RGBA16 and constant indexed-palette converters retain every
supported material/model layer and reject unsupported effects rather than dropping
them. Fifty-four additional non-placeholder models pass artwork preparation but
retain acquisition, identity, or gameplay dependencies: 13 unidentified routes,
12 Tortimer gifts, six harvest items, five island items, two native-identity
reviews, and sixteen diary aliases needing parent gameplay and room conversion.
Prepared-only output cannot pass installation; donor dummy profiles
remain explicit missing-artwork records. Continue shared acquisition and animated
callback categories using the bulk-prepared assets.

The [school-desk batch](checkpoints/V3_SCHOOL_DESKS.md) installs complete lefty,
righty, and teacher's desks in ABI 84, with official names, prices, A/B stock,
catalogue entries, native scoring, and independent selection. All 218 vertices,
96 triangles, seat flags, and material settings remain. Twenty cartridge/
composition checks pass. The first native run passes 88 records with 74
assertions, covering complete owner loading, names, prices, model DMA, rotated
footprints, stock membership, catalogue eligibility, acquisition, saved ownership,
restoration, and guards. Ordinary sitting, room appearance, and save/restart
remain unverified. Their shared seating-sound reader is installed and checked
in the current cartridge above. Both served patchers remain V2. No permanent
memory or saved format grows.

The [ordinary summer-town check](checkpoints/V3_CAMPSITE_GAMEPLAY.md) cold-boots
ABI 83 with the current profile and unchanged copied-town content. The game
activates event 70 and places the tent on a vacant lot without fixture-seeded
camper, tent, or rewards. Arrival and two bounded approaches retain clean
fault/save/translation guards. River navigation prevents reaching the tent;
no further navigation retry is queued. Ordinary actor construction, entry,
conversations, rewards, and persistence remain open. Continue remaining native
readers and donor implementation; neither patcher changes.

The [timed tent lamp](checkpoints/V3_TENT_LAMP.md) installs the donor model,
dawn/dusk fade, room-light transitions, drawing, and cleanup in ABI 83. The
complete original native effect controller remains. Lamp code uses existing
reserved memory; a live model needs 3,280 heap bytes, released by the destructor.
Nineteen focused/composition tests pass. The first silent native run completes
65 records with 36 passing assertions, including the full owner load/relocation,
all four actual callbacks, model DMA, draw commands, complete native environment
update, room colours, cleanup, restoration, and guards. Ordinary tent entry,
GPU appearance, conversations, and persistence remain unverified. No saved
formats, text resources, or patchers change.

The [campsite environment adapter](checkpoints/V3_CAMPSITE_ENVIRONMENT.md)
connects the donor's actual footstep sound and room-light parameters in ABI 82.
Its complete sound program, instrument, and sample match existing native audio;
the transient floor selector shares that sound without replacing any flooring.
The 156-byte adapter fits existing reserved memory. Eighteen focused/composition
checks pass. The corrected silent native run passes 39 records and 29 assertions,
including the actual field store, player/NPC sound readers, full five-argument
light getters, original-room fallbacks, restoration, and guards. The first run
also passes the new floor getter. Ordinary walking and tent gameplay remain
unverified; the timed lamp has the separate current evidence above.

The [camper trade adapter](checkpoints/V3_CAMPER_TRADE.md) connects full-ID pocket
selection, summer last-gift exclusion, and selected camping rewards in ABI 81.
It preserves the donor's 20% tent-list roll, subsequent 10% house-gift roll,
small-list duplicate rule, and carpet/wall list fallback. The 1,344-byte suffix
uses the existing conversation allocation; saved formats and resident heaps do
not grow. Eighteen focused/composition checks pass. The corrected silent native
run passes 55 records and 37 assertions, including two selected-only rewards,
three complete trade preparation calls, both gift hooks, constructor reset,
the complete greeting initializer/return, restoration, and guards. Four pocket
cases also pass in the initial run. Complete conversations and acquisition
animations are not established by these checks.

The [official credits correction](checkpoints/OFFICIAL_CREDITS_TITLE.md) uses
the supplied English GameCube title, `Animal Crossing`, rather than the manual
literal-title draft. The [single text-source catalogue](TEXT_PROVENANCE.md)
records per-text authorship and source evidence, including assistant-authored
passages and explicit remaining provenance coverage. No served patcher changes.

The [summer greeting adapter](checkpoints/V3_CAMPER_GREETING.md) connects first
and repeat introductions, donor item/Bell eligibility, and transient last-gift
tracking in ABI 80. Its 512-byte suffix fits the existing shared conversation
buffer; saved formats and permanent allocations do not grow. Seventeen current
focused/composition checks pass. Actual native owner loading, all six personality
introductions, English message reads, repeat bases, and thirteen eligibility
cases pass. A later caller-dispatch breakpoint times out despite the expected
message result. That intermediate stop remains unexplained; the current trade
check passes the complete unchanged greeting initializer/return, native gift/reset
execution, and final guards. Complete conversations still require verification.

The unchanged [complete summer text adapter](checkpoints/V3_CAMPER_TEXT.md) appends all 253
donor messages and 49 choices in ABI 79, retaining every existing English record.
All branches, choices, wording, page breaks, timing, and expressions are preserved;
eight duplicate donor trade requests map to their verified native handler.
The largest expanded message bound is 827 of 1,024 bytes. Seventeen current
focused/composition tests pass. The corrected native run passes 74 records,
23 calls, and 54 assertions, including complete old/new reads and continuation.
Its unchanged loader evidence applies to the final eight-byte command adaptation;
ordinary conversations and reward execution remain unverified.

The unchanged [camper NPC/quest adapter](checkpoints/V3_CAMPER_QUEST.md) binds both native
NPC controllers to the donor's shared camper profile and installs first/repeat
quest routing in ABI 78. The summer greeting-session flag changes at first talk
start; winter and ordinary conversations leave it alone. The helper uses 112
checked unused resident bytes without growing any RAM allocation or saved format.
Seventeen focused/composition tests pass. The corrected silent native run passes
68 records, five calls, and 55 assertions, including all three complete owner
loads/relocations and twelve changed instruction windows. Full NPC construction,
complete conversations, and rewards remain work; the current greeting adapter
supplies summer-specific selection with the native limits described above.

The unchanged [camper move-in guard](checkpoints/V3_CAMPER_MOVEIN.md) prevents the saved
summer visitor from simultaneously becoming a resident, through either normal
growth or an inbound villager transfer. ABI 77 adds 252 bytes in checked unused
resident space, preserving the native selection rules and all allocations.
Fifteen focused/composition checks pass. The first silent native run passes
48 records, 22 calls, and 25 assertions, including actual appearance-history
reset, the complete candidate set, full native transfer refusal without town or
incoming-Animal mutation, and restored eligibility after event-record release.

The unchanged [summer event manager](checkpoints/V3_CAMPSITE_MANAGER.md) connects the
calendar, saved camper selection, independent visitor registration, and native
tent placement/removal in ABI 76. All 28 original event controls and the complete
English letter manager remain. Failed placement/removal preserves the pending
event state for retry; the engine's error flag would otherwise abort the event.
Indoor starts register the same camper without requiring an outdoor field.
Its retained focused checks and corrected silent native test pass
79 records, 42 calls, and 51 assertions, including real selection, registration,
dispatcher retries, nine-cell placement, and removal with lot restoration.
The loaded manager grows by 1,920 bytes; permanent reservations, heap limits,
actor instance size, DMA file count, and saved formats stay unchanged.

Current full integration:
`build/v3-furniture-intensity-runtime-01/animal-forest-v3-asset-loader.z64`, SHA-256
`ad194977b9083764c0efe8636614ba45d69b9370d6322514e2fd0b24aff2c1e3`.
The offline composer retains 93 experimental choices and exact all/empty
full/V2 output. Continue
remaining masked readers and combined ordinary
construction, entry/exit, conversation handover, and persistence checks. Those
gameplay paths remain unverified. GitHub development source is allowed; neither
served patcher changes until the user
tests V3 and explicitly approves the switch. This is not a complete-import
playtest handoff. Imported saves require matching/superset profiles and must
not be loaded in V2.

The unchanged [tent placement adapter](checkpoints/V3_CAMPSITE_PLACEMENT.md)
retains its passing native building-class, register/delay, lot-restoration, and
expanded cleanup-list evidence. Both consumers handle the added ID explicitly,
avoiding an out-of-bounds read into function-pointer data. No older cartridge
is re-tested or counted as current-build verification.

The retained [independent camper](checkpoints/V3_CAMPER.md) installs complete visitor
Animal ownership, optional-roster/default/outfit registration, current-player
memory reconstruction, and native NPC-info attachment in ABI 74. No town slot,
heap growth, or model bank is used. Fifteen current focused/composition checks
pass. The corrected native run passes 144 records with no failed assertions,
including actual native/imported defaults, English names, masked draw records,
alias capacity/selection checks, greeting memory, and complete native save/town
list preservation. The native greeting-memory alignment is explicitly handled.
These are native RAM/reader checks, not full NPC construction or persistence.

Its unchanged ownership/default/name/attachment code retains that recorded native
evidence; the manager batch does not re-test the older cartridge.

The installed [native summer calendar](checkpoints/V3_CAMPSITE_CALENDAR.md)
retains its independent expanded index and all original event types/schedules.
Its unchanged code retains passing native calendar/status/event-save-area
evidence; that earlier RAM check is not re-labelled as save/restart persistence.

The [additive tent exterior](checkpoints/V3_CAMPSITE_EXTERIOR.md) installs its
complete actor callbacks, independent identity, native loader binding, full
exterior/shadow assets, collision, doors, daylight fade, and cleanup in ABI 72.
The original igloo and all native descriptors remain. Code and metadata fit the
existing resident reservation; each live tent needs 7,776 heap bytes. Sixteen
focused/composition checks pass. Partial native execution confirms complete
controller relocation, setup registration, descriptor selection, and pool
initialization. The combined probe stops at a field-background allocation bound
before constructing the tent; that unresolved result is not a gameplay pass.

Exterior checkpoint:
`build/v3-campsite-exterior-runtime-01/animal-forest-v3-asset-loader.z64`, SHA-256
`61d9bec4ac698420f20df7a062b13d8bf3619989fc78b357245d6ade4589abdf`.
The ten-item subset is `build/v3-optional-campsite-exterior-01/`. The offline
composer retains all 59 experimental options and exact all/empty full/V2 output.
The current manager supplies event binding and saved camper identity. Continue
ordinary English conversations, reward handovers, and timed scene lighting. Native actor construction,
ordinary entry/exit, GPU appearance, and persistence still need verification.
Neither web patcher changes; this is not a complete-import playtest handoff.
Saved format 2 and selected identities are unchanged. Imported saves require
matching/superset profiles and must not be loaded in V2.

The [campsite scene loader](checkpoints/V3_CAMPSITE_SCENE.md) installs native
scene 35, a complete extended field directory, all four scenery objects, and
checked resident callbacks in ABI 71. All 35 original scene/field records remain;
the complete 19,872-byte room uses the existing background allocation. Fifteen
focused/composition tests pass. The corrected silent native run passes 57
records, 24 calls, and 30 assertions: full real field construction, collision,
exits, camper placement, model DMA, gameplay-overlay relocation, and guards.
The resident package adds 8 KiB; normal heaps and furniture banks do not grow.

Scene-loader checkpoint:
`build/v3-campsite-runtime-03/animal-forest-v3-asset-loader.z64`, SHA-256
`fc8a8682c58f61841f23996bacccf2daa98eefda2c6f9e65aa4e472713834ea9`.
The ten-camping-item subset is `build/v3-optional-campsite-01/`. All 59
experimental options compose offline; all/empty output is exact full/V2.
Neither served patcher changes. This is not a complete-import playtest handoff.
Continue ordinary summer-event integration, camper conversations,
reward handovers, and timed scene lighting.
Ordinary scene entry, acquisition, GPU appearance, persistence, and hardware
acceptance are not established by the field-constructor test. Saved format 2
and selected identities are unchanged; imported saves require matching/superset
profiles and must not be loaded in V2.

The [summer campsite scenery](checkpoints/V3_CAMPSITE_ART.md) retains all 527
vertices and 369 triangles across exterior, projected shadow, interior, and
separate scene lantern. Its five conversion checks cover the interior's mixed
CI4/I4 materials and the lantern's simultaneous textures/palette banks.
The collectible lantern and sleeping bag correctly have no extra interaction;
the animated lantern belongs to this separate scene.

The [complete fire runtime](checkpoints/V3_FIRE_RUNTIME.md) installs campfire and
bonfire with full rigs, camera-facing flames, two scrolling textures, positional
sound, English metadata, catalogue/scoring, and selected dependencies in ABI 70.
The bonfire has its true four-cell footprint. Twenty-one focused checks pass;
the current silent native run passes 110 records, 24 calls, and 90 assertions,
including actual full model DMA, native rig/draw execution, unaligned graphics
arenas, placement readers, restoration, and guards. The offline composer has
59 experimental options with exact all/empty full/V2 output. No additional
resident, model-bank, normal heap, or menu allocation is required.

Fire runtime checkpoint:
`build/v3-fire-runtime-02/animal-forest-v3-asset-loader.z64`, SHA-256
`e2a8ddfb41b7ad7d111cf666dc4b4706046d6edff1fe88968e925603a9345ad5`.
Its two-fire subset is `build/v3-optional-fires-02/`.
Continue summer-camper acquisition, then
other donor content and ordinary gameplay/persistence. GPU appearance and
original-hardware acceptance remain unverified. Both served patchers remain V2;
this is not a complete-import playtest handoff. Saves using either fire require
a matching/superset import profile; no save-structure change is introduced.

The retained [fire-sound runtime](checkpoints/V3_FIRE_SOUND_RUNTIME.md) installs both
complete two-layer sounds and their missing samples, retaining all current
sounds. Its five cartridge checks, twelve composition checks, and initial
74-record native run pass. Actual allocation, all six waveform headers,
complete 74-instrument font relocation, both new sample transfers, native level
start/stop, and final guards pass. Audio reserves 1 KiB more; session/cache
capacity stays intact, and the permanent pool has 256 bytes spare. The fires'
graphics/interaction callbacks and item installation are supplied by the current
integration above. Both served patchers remain V2.

The [tent-model loader repair](checkpoints/V3_TENT_MODEL_LOADER.md) enables actual
ROM DMA for the complete callback-owned tent. Fifteen focused tests pass; the
first native run passes 36 records, eight calls, and 24 assertions, including
complete upper-memory model DMA, rotated bank reuse, invalid-profile rejection,
and restoration. The expanded helper uses 1,760 of its reserved 2,048 bytes.
ABI, saved format/profile, allocations, and all content remain unchanged.

The [tent-model runtime](checkpoints/V3_TENT_MODEL_RUNTIME.md) installs its complete
model and light callbacks, English name/price, one-cell profile, non-orderable
catalogue entry, HRA/feng shui, and optional saved dependency in ABI 69. Seventeen
focused integration/composition tests pass. The first native run passes all
17 calls and 48 assertions: installed callbacks, independent light fades, complete
four-part draw commands, submitted palette lifetime, native item readers, guards,
and checkpoint restoration. No extra resident RAM, model banks, or normal heap
allocation is needed. The offline composer has 57 experimental options, with
exact all/empty full/V2 output and deterministic individual selection.

Sound-only integration checkpoint:
`build/v3-fire-sound-runtime-01/animal-forest-v3-asset-loader.z64`, SHA-256
`f3d055a74c2172029755b6be39e84b29658a17e83ef599a4f2fe6453570cb48f`.
Its tent-only subset is `build/v3-optional-fire-audio-01/`.
Ordinary light interaction, rendering, acquisition, and persistence are not yet
verified. Both served patchers remain V2; this is not a complete-import playtest
handoff. The selected-import dependency set changes, not the save format; a town
saved with tent selected must not be loaded by a profile lacking that import.

The [remaining camping assets](checkpoints/V3_CAMPING_ACTORS.md) are complete:
campfire, bonfire, and tent model, including both moving flame textures, full
fire rigs, and both tent-light palettes. All 18,320 native asset bytes fit the
existing model banks. The bonfire's true four-cell item reader is implemented
and compiles to 1,020 bytes within the existing code reservation. Twenty-one
focused checks pass, including sanitised shared readers and full source/asset
checks. Both complete fire actors and their individual offline options are
installed by the current runtime above. Summer-camper acquisition for all ten
rewards remains work. Both served patchers remain V2.

The [camping integration](checkpoints/V3_CAMPING_ITEMS.md) installs seven complete
objects: kayak, backpack, lantern, cooler, mountain bike, sleeping bag, and propane
stove. English names/prices, one/two-cell profiles, catalogue framing and
non-orderability, safe HRA points, feng shui, and selected dependencies are in
ABI 68. No further resident RAM, heap, model-bank, or menu allocation is needed.
Twenty-nine focused checks pass. The first native run passes all 28 item-reader
calls and 37 memory assertions, including complete loaded rows and intact guards.
These seven entries retain deterministic individual selection in the current
offline composer.

The donor's collectible lantern and sleeping bag are correctly non-interactive:
their profiles have no callbacks or contact/interaction flags. The separate
`ef_tent_lamp` scene effect is not the collectible lantern. The complete pinned
profiles and installed scalar fields agree; no extra furniture behaviour is
required. Summer-camper acquisition, ordinary
placement/rendering/persistence, and the remaining donor content are unfinished.
The seven rewards are not substituted into ordinary shop stock. Both served
patchers remain V2; this is not a complete-import playtest handoff.

The [import-storage expansion](checkpoints/V3_IMPORT_STORAGE.md) supplies
1,847,280 bytes of free import storage without adding to the full DMA directory.
English choices retain their contents and IDs at a new virtual address. Fixed
profile/item slots remove the need to relocate tables for every content batch.
ABI 67 adds 114,704 resident bytes without increasing the normal heaps or model
pool. Seventeen focused checks and the first actual native run pass: 23 calls,
48 memory assertions, all installed static pointers, relocated English choices,
and intact guards. The offline composer retains all 49 experimental options,
exact all/empty outputs, and deterministic individual selections.
Storage checkpoint:
`build/v3-import-storage-02/animal-forest-v3-asset-loader.z64`, SHA-256
`f12da1a8575403ab74ded685e916bf082b5c1d53e6b73c0ae74c0fe87d282ade`.
The subset is `build/v3-optional-storage-01/`. Both served patchers remain V2.
Camping uses these fixed slots and a scoring-only category mapping; acquisition,
remaining content, and gameplay/persistence integration continue. This is not a
complete-import handoff; spare slots are not implemented items.

The [full-sized Western batch](checkpoints/V3_WESTERN_LARGE_ITEMS.md) installs
watering trough, covered wagon, and storefront, completing the ten-item Western
theme. Complete models, two-cell footprints, true stock routes, catalogue framing,
English readers, scoring, and selected dependencies are installed in ABI 66.
The checked package adds 8 KiB; the existing menu and model-bank allocations stay.
Twenty-eight focused checks and the initial 88-record native run pass, including
all three items' four rotations and retained three-shirt readers. Ordinary
placement, rendering, acquisition, and persistence remain unverified.
Full-sized Western checkpoint:
`build/v3-western-large-runtime-01/animal-forest-v3-asset-loader.z64`, SHA-256
`5c51f80525a253e889a38b4ed4730df7e21b9a5e63a80917f0406b512faaebfe`.
The offline composer has 49 experimental options, exact all/empty outputs, and
a generated trough/wagon/red-aloha subset at `build/v3-optional-western-large-01/`.
Expanded import storage supplies the headroom for further donor families.
Both served patchers remain V2. This is not a
complete-import playtest handoff; remaining donor content and gameplay continue.

The [Western runtime](checkpoints/V3_WESTERN_RUNTIME.md) installs seven complete
furnishings with English names/prices, catalogue entries, ordinary/event stock,
scoring, and saved dependencies. Dedicated Expansion Pak banks hold 9,216 bytes
each without ordinary heap growth. Fifteen focused integration/composer checks
pass. Native item readers, event acquisition, catalogue rules, and Western
scoring pass; bank verification is partial after two permitted setup attempts.
Actual 100-bank allocation and dummy DMA are established. Paired upper-memory
model DMA and executed teardown remain unverified; no complete bank-lifetime
pass is claimed. Western checkpoint:
`build/v3-western-runtime-02/animal-forest-v3-asset-loader.z64`, ABI 65, SHA-256
`e9285a7d301b466b32eb4af022b5dc7ffaa555b3f1de93cffdb86bc838daa858`.
The offline composer has 46 experimental options and exact all/empty outputs.
The two-event-item subset is `build/v3-optional-western-01/`. Both web patchers
remain V2. Ordinary gameplay/persistence, remaining donor families, and the
bank tail continue; this is not a complete-import handoff.

The [garden runtime and composer](checkpoints/V3_GARDEN_RUNTIME.md) install six
complete models, English names/prices, catalogue entries, scoring, stock, and
selected save dependencies. Four focused integration checks and the initial
187-record native run pass. The gnome is acquired through native lottery
selection; mailbox reward delivery remains unfinished. The 452-entry furniture
catalogue and complete 248-entry clothing catalogue fit the existing menu RAM.
The garden artifact is `build/v3-garden-runtime-02/animal-forest-v3-asset-loader.z64`,
ABI 64, SHA-256 `436c5cec2aeb1d9f34d1fb71217ec62a6ef232d91573e0112d7055c65345f1d0`.
Nine composer checks pass across 39 experimental options. Unselected HRA records
are excluded from theme requirements and recommendations; all/empty outputs
retain the exact full/V2 cartridges. Its subset is `build/v3-optional-garden-01/`.
Its initial 35-record native scoring check passes, including selected-only theme
counts/completion, actual reward points, saved-state restoration, and guards.
Neither served patcher changes. Ordinary gameplay/persistence and remaining donor
families continue; this is not a complete-import handoff.

The [reward-category scoring adapter](checkpoints/V3_HRA_BIRTH.md) extends the
actual HRA counter arrays to 23 categories, preventing post-office category 19
from overwriting its output pointer. Three focused checks and the initial
82-record native run pass, including complete counters/products, all four new
categories, mixed/null layers, and guards. All native point values stay intact.
This prerequisite remains in the current Western integration. It uses
96 additional on-demand bytes without additional permanent RAM. Post-office
reward delivery remains work.

The [garden batch](checkpoints/V3_GARDEN_ITEMS.md) converts six more complete
decorations: birdhouse, bird feeder, both flamingos, mailbox, and garden gnome.
Six new focused checks and ten shared parser/profile checks pass. Models retain
all 406 vertices, 251 triangles, and 24,448 texels, including tall clamped textures
and explicit mirrored materials. Acquisition metadata preserves lottery and
post-office rewards. The runtime batch supplies installation and backyard scoring;
the separate reward-category adapter supplies its safe counter prerequisite.

The [aloha scoring correction](checkpoints/V3_ALOHA_SCORING.md) supplies both
imported displays' actual clothing properties instead of inactive HRA records.
Three focused checks and a corrected 52-record native run pass, including full
grouping, native clothing points, disabled exclusion, and array-end guards.
It changes two data words with no RAM, saved-profile/format, or ABI change.
Its corrected metadata remains in the current ABI-64 integration above.
Neither served web patcher changes.

The [construction catalogue integration](checkpoints/V3_CONSTRUCTION_CATALOGUE.md)
installs all seven new items into ordinary stock, the catalogue, and room scoring.
The actual category storage grows to 753 slots: 446 furniture and 248 clothing
rows retain their full names and independent pages. The initial native catalogue
run passes 103 records; the B/C stock and pocket-acquisition run passes 36.
The shared menu reserves another 6,144 bytes; the cartridge remains 64 MiB with
an Expansion Pak required. Its code and allocations remain in the current
integration above.
The local optional composer connects the package-resident furniture rows/CRC.
Ordinary acquisition/placement/persistence remain. Both web patchers remain V2.

The [construction runtime](checkpoints/V3_CONSTRUCTION_RUNTIME.md) installs
seven more complete furniture models, fixed profiles, English names/prices,
placement readers, and selected save-profile bits in ABI 61 without more RAM.
Four focused checks and the initial 145-record native run pass, including all
seven item readers, paired detour-sign/saw-horse model loading, original-item
fallbacks, cleanup, and guards. The actual C codec rejects new-profile saves in
older profiles without writes. The capacity-expanded integration supplies its
catalogue and stock/scoring tables. No complete-import handoff is claimed.

The [local optional composer](checkpoints/V3_OPTIONAL_CONSTRUCTION.md) now
supports individual experimental selections across the twenty installed
villagers and nineteen logical items. It derives required house furnishings and
outfits from installed content, preserves fixed IDs, and exports the selected
save profile. Seven focused checks pass: reordered selections produce identical
cartridges, select-all reproduces the full integration build, and an empty
selection reproduces stable V2-11. The O'Hare/detour-sign/saw-horse subset passes
its initial 122-record native run: selected/excluded readers, package CRC,
438-row furniture and 246-row clothing catalogues, correct subset completion,
model loading, names, saved-state retention, and final guards. Its local build
is `build/v3-optional-construction-02/`, with the two corrected HRA words and
unchanged catalogue/selector code. Seven composer checks pass on this source;
the native subset evidence covers the unchanged consumers. Neither served patcher changes.
This does not certify unfinished gameplay or
claim that all donor items are converted.

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
checks; six focused tests also pass. The complete variant supplies Punchy's
separate imported cherry shirt and passes his native initializers, as recorded
in the combined house/default checkpoint. Ordinary gameplay/save paths remain;
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
`build/v3-house-markers-01/animal-forest-v3-asset-loader.z64`, ABI 60, SHA-256
`55a715831671c989aa465fbf6d04c49caa975a761105ffa1f3acecd10ac7b8cf`.
The [separate house markers](checkpoints/V3_HOUSE_MARKERS.md) prevent imported
houses from sharing original player-house/building markers. Three focused tests
pass, including compiled instructions over all 16-bit inputs and the complete
cartridge/patch. The ROM is 64 MiB; RAM remains 8 MiB, with no extra allocation.
The corrected native run enters Punchy's actual room, retains one player and
intact guards, and draws Punchy inside. The matching-state continuation verifies
the normal outdoor house ID is restored and all 65 scene-heap nodes are valid,
with 358,528 bytes free. The corrected side approach and ordinary A presses
advance Punchy's English home dialogue, insert his full catchphrase, and reach
the three live English choices. Ordinary exit returns outdoors, reconstructs the
correct house/marker, and retains one player plus a valid arena with 40,608 bytes
free. Natural arrivals and ordinary villager persistence remain distinct from
those passing checks.
The [islander gameplay check](checkpoints/V3_ISLANDER_GAMEPLAY.md) adds a
profile-checked disposable fixture for any fixed imported villager. Maelle's
current copied town loads her identity, outfit, house, and complete interior
with 359,248 bytes free. Her ordinary schedule takes her outdoors; the native
away-resident handling explains her inactive indoor position. Outdoor speech
remains unverified after two bounded setup attempts, with exact checkpoints
retained. The first read-only sample observation passes its final guards but
does not start speech or validate any new instruments. Continue independent
implementation instead of repeating that navigation setup.
This is an implementation artifact, not an accepted playtest handoff. Native
default and house-layer checks pass; ordinary house/move-in and villager
persistence checks remain open, as detailed below.
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
The [complete town adaptation](checkpoints/V3_TOWN_RESIDENTS.md) enables all
twenty fixed identities in the experimental integration cartridge, with separate
town modes, selected-profile/outfit checks, and unchanged donor roles. Six
focused tests pass. Native counts/exclusions pass, and the corrected 90-record /
56-assertion tail verifies full Maelle resident creation, two complete starting
populations, all six daily schedules, event overrides, and guards. Ordinary
arrivals, visits, and persistence remain incomplete; neither patcher enables V3.
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
rejection/guard checks. All original clothing is retained. The
[NPC clothing adapter](checkpoints/V3_NPC_CLOTHING.md) connects both owners'
foreground/queued resource readers and full shirt-ID checks. Four focused tests
pass, and native execution confirms the first complete foreground loop with
original, imported, and invalid clothing. Queued completion and the second
owner remain unverified after the bounded allocation/timing setup attempts.
The [player clothing adapter](checkpoints/V3_PLAYER_CLOTHING.md) connects both
startup readers and clothes changes while retaining native double buffering.
Three focused tests and the initial 47-step native run pass: complete original/
imported artwork, four registered banks, both buffer changes, unknown/missing
handling, restored globals, and guards. The
[clothing save extension](checkpoints/V3_CLOTHING_SAVE.md) adds independent
clothing profile/ownership records and preserves format-1 furniture ownership
during migration. Five focused checks, four current non-clothing codec host
checks, and the corrected 52-step native run pass, including complete startup/
encoding/decoding, ownership separation, player clearing, and guards. Remaining
gameplay consumers need integration. Punchy's defaults are connected in the
complete house/default variant; move-in eligibility stays disabled. The
[shared clothing item readers](checkpoints/V3_CLOTHING_ITEMS.md) connect the
complete English name, category, and donor price, preserving native garment
footprint rejection. The current host/cartridge tests and corrected 60-record
native run pass, including selected-profile rejection, retained original clothes
and furniture, complete code retention, and guards. The
[clothing collection adapter](checkpoints/V3_CLOTHING_COLLECTION.md) connects
native pocket acquisition to independent per-player saved ownership. Current
host/cartridge checks and the initial 62-record native run pass, including all
four residents, present/quest timing, full IDs, original/furniture retention,
disabled/adjacent-item rejection, player clearing, restored records, and guards.
The [clothing menu routing](checkpoints/V3_CLOTHING_MENU.md) adds checked clothing
classification and three hand/cursor/animation decisions. The host/cartridge
checks and initial 62-record native run pass, including six full-register
windows, complete eligibility/destination/action functions, retained present/
quest menus, full identities, code retention, and guards. Drop/display,
shop/catalogue, and gameplay persistence remain work.
The [player animation fix](checkpoints/V3_CLOTHING_WEAR.md) replaces its old
256-shirt index restriction with the checked full imported index. Host/
cartridge checks and the initial 33-record native instruction-window check
pass, retaining other registers, native/invalid fallbacks, classification,
artwork, save code, and guards. Ordinary copied-town cold boot, inventory,
grabbing, wearing, and outdoor rendering pass. The full imported identity is
retained, and the original shirt returns to its pocket. Actual gyroid Save &
Quit, return to title, and a fresh-process reload pass, restoring both clothing
fields, all expected pockets, ownership, and complete active garment artwork.
The [clothing shop category](checkpoints/V3_CLOTHING_SHOPS.md) now recognises
the selected garment through the checked shared item reader. Two focused tests
and the initial 23-record native run pass, retaining original/furniture
categories, complete resources, save code, profile, and guards. The
[clothing stock adapter](checkpoints/V3_CLOTHING_STOCK.md) adds the selected
shirt to A's all-season list with native B/C seasons, town rarity, and one RNG
draw retained. Two focused tests and the initial 65-record native run pass:
seven actual stock selections, six rarity queries, full-ID pocket acquisition,
independent ownership, restored records, and guards. The
[shop mannequin adapter](checkpoints/V3_SHOP_MANNEQUIN.md) widens all six
count/search windows while retaining the native actor, model, and buffers.
The focused cartridge check and corrected 56-record native run pass: full
owner relocation, original/imported/disabled/sold counting and placement,
both complete texture-loading loops, restored globals, and guards. The
[clothing shop-floor adapter](checkpoints/V3_CLOTHING_SHOP_FLOOR.md) connects
separate reserve, selection, and sale decisions. Its cartridge check and
initial 61-record native run pass, including twelve complete reserve/selection
calls, full native sale reporting, the real bare-mannequin callback, foreground
clearing, retained other stock, exact sales-total changes, and restored guards.
The [bounded ordinary-shop check](checkpoints/V3_CLOTHING_SHOP_GAMEPLAY.md)
confirms cold boot retains the seeded imported stock without pre-awarding a
pocket item or ownership. Purchase remains unverified: both door approaches
leave the player outside the shop, with guards and fault checks passing.
Navigation retries stop for this batch; catalogue/home display is next.
The [expanded furniture tables](checkpoints/V3_FURNITURE_TABLES.md) provide 2,051
profile/bank entries in guarded Expansion Pak memory, retaining all eight public
helper addresses, existing items, native heaps, and saved formats. Two focused
tests and the initial 91-record current native run pass: both imported models,
original profile/model allocation, bank reuse/release, complete cleanup, and
new guards. The [clothing display adapter](checkpoints/V3_CLOTHING_DISPLAY.md)
installs stable mannequin identity `3AFC`, the original N64 model/draw callbacks,
and checked full-index garment loading without larger buffers. Three focused
tests and the corrected 116-record native run pass, including all four rotations,
complete artwork/model transfers, native draw commands, cleanup, and guards.
The [display readers](checkpoints/V3_DISPLAY_ITEM_READERS.md) connect the full
English name, price, placed category, native mannequin footprint, and canonical
clothing ownership for all four rotations. Both scoring tables contain 2,051
source-verified rows within existing allocation limits. Two focused checks and
complete native item-reader/collection exercises pass. The
[global conversion batch](checkpoints/V3_DISPLAY_CONVERSION.md) connects
`34BF` to mannequin `3AFC` and all rotations back to the pocket garment,
preserving every native conversion body. Two focused checks and the initial
157-step native run pass, including complete conversions, full HRA grouping/
points, feng shui item/room scoring, guards, and checkpoint restoration.
This closes the pending scoring tail. The initial 22-record ordinary copied-town
run also passes house entry, inventory Drop, mannequin bank allocation, and
B pickup returning the full `34BF` identity with the bank released. All other
pockets, conditions, worn clothing, and guards remain intact. The pocket item
is fixture-seeded, not purchased. The
[clothing catalogue](checkpoints/V3_CLOTHING_CATALOGUE.md) adds the owned shirt
after all 245 native clothing rows, with its full English name, native mannequin,
clothing presentation, price eligibility, and canonical ordering identity.
Two focused tests and the initial 71-step native run pass: all 246 rows,
selection, the complete 4,128-byte model/artwork transfer, original retention,
disabled dependencies, restored state, and guards. The shared menu uses 274,176
of its existing 274,560 bytes. The
[placed-clothing persistence check](checkpoints/V3_DISPLAY_PERSISTENCE.md)
establishes ordinary gyroid Save & Quit, independent validation of both complete
FlashRAM banks, fresh-process restoration of the complete room and ownership,
and B pickup returning `34BF` with its model bank released. Other inventory
fields stay intact. The final scenario stops on a wrong expected guard constant;
the observed save guard is correct, the expectation is fixed, and the remaining
tail is not claimed passed. Ordinary rotation remains unverified after the two
bounded approaches. Do not repeat that navigation batch.
The mannequin's additional profile dependency accepts the preceding profile in the focused
decoder check, but older profiles reject new saves. Keep save backups; this is
not an ordinary cross-build reload result.
Ordinary confirmation/player payment, catalogue ordering/delivery, and remaining
buy/sell integration remain work. The separate outdoor Drop checkpoint is
retained; outdoor pickup remains unverified after timed movement overshoots.
Home placement, same-build persistence, and pickup have the evidence above.
The clothing variant writes format 2 and must not be loaded by older format-1
V3 builds or V2. Back up existing saves. Ordinary acquisition/
payment, rotation, other imported items' placed persistence, remaining native
readers, and the complete villager remain work. Continue villager integration
and Punchy's animated speed-bag dependency before another navigation batch.
The [speed-bag converter](checkpoints/V3_SPEED_BAG_ART.md) supplies Punchy's
complete two-part animated model: all textures, geometry, three animation tracks,
and native two-joint headers fit in 3,728 bytes of a 5,120-byte bank. Six focused
conversion checks and the five retained static-parser host checks pass. The
separate [callback batch](checkpoints/V3_SPEED_BAG_CALLBACKS.md) implements the
constructor, hit/retrigger logic, and native skeleton drawing in 472 bytes.
Five focused checks and the corrected 103-record native run pass: complete
poses, hit/retrigger/stop timing, native state-based sound dispatch, both matrix
banks' drawing commands, and memory/save guards. The complete hit-sound program,
instrument, envelopes, loop, predictor book, and 11,062-byte sample are converted;
five audio checks pass. The [sound installer](checkpoints/V3_SPEED_BAG_SOUND.md)
adds the real hit through the original native audio loader and preserves all
original audio. The complete villager audio installation below leaves 32 bytes
of conservative permanent-heap spare capacity.
Four focused checks and the corrected build's first 58-step native run pass,
including actual trigger/retrigger, completed imported-sample transfers, and
guards. Native testing found and fixed an unaligned envelope read. PCM/listening
verification, ordinary gameplay, and GPU appearance remain work.
The [animated runtime installation](checkpoints/V3_SPEED_BAG_RUNTIME.md) adds the
production callbacks and positional sound adapter, complete native profile/model
loader, fixed item `3350`, and full English metadata. A two-MiB virtual-ROM
reservation supplies room for further imports without increasing resident RAM;
all original directory indices and public item-reader entries remain fixed.
Four focused checks and the corrected 204-step native run pass, including actual
installed construction, hit animation, positional sound, full model loading,
English metadata, original/clothing retention, and cleanup/guards.
The [boxing HRA adapter](checkpoints/V3_SPEED_BAG_HRA.md) installs actual series
58 and safely expands native definitions, names, and completion masks to 59
entries. Four focused checks and the first 68-record native run pass, including
complete grouping, all four scoring loops, points, disabled-item rejection,
no false matching-surface bonus, and preserved storage/guards. The HRA image
uses 31,296 of its 32,768-byte bound without permanent RAM growth.
The [gameplay connections](checkpoints/V3_SPEED_BAG_GAMEPLAY.md) add the boxing
score-letter name, donor-order catalogue entry, group-A stock, neutral feng shui
properties, and selected save dependency. The combined native run passes 149
records / 103 assertions, including four complete English letters and restored
text, actual stock selection/acquisition, all 439 catalogue rows, full English
names, and animated preview construction. All seven current host checks and
the enabled build's 12-record cold-boot check pass. The private build enables the speed
bag with these dependencies; ordinary purchase, placed interaction/persistence,
final GPU appearance, and Punchy's house remain work. No V3 import is selectable
in either web patcher. The new profile requires speed-bag support: older builds
without that dependency reject its saves, although the format remains version 2.
V3 development continues on GitHub on `v3/optional-imports`. Both the local and
public web patchers stay V2 until the user has tested V3 and explicitly approved
the switch; publishing development source does not grant patcher approval.

The [Punchy house/default batch](checkpoints/V3_PUNCHY_HOUSE.md) installs his
complete mapped room, original furniture rotations, K.K. Love Song, matching
native surfaces, and actual `34BF` starting shirt. The complete foreground
moves to a checked reservation, retaining all original rows and DMA identities.
Default/selection code fits existing resident gaps without permanent RAM growth.
All seven focused checks pass, including sanitized default/clothing code,
dependency rejection, full source conversion, and patch reconstruction.
The full native arithmetic block produces the correct 436 records without the
synthetic window's internal breakpoint. The failed window diagnostics remain
recorded; their exact emulator entry/resume mechanism is not established.
Native defaults pass 81 records / 44 assertions, including all six initializers,
full names/catchphrases, actual garment transfers, and dependency rejection.
The native house tail passes 48 records / 29 assertions, including all four
imported layers and complete original/pilot house initialization.
The [ordinary Punchy check](checkpoints/V3_PUNCHY_GAMEPLAY.md) cold-boots a
disposable town, retains his full identity and imported outfit, and loads his
actor while crossing the acre. House entry remains unverified after the bounded
door approaches. Move-in eligibility stays disabled. Profile/format are unchanged from ABI 49; ordinary
cross-build loading is not newly verified. Both patchers remain V2.

The [additional islander artwork](checkpoints/V3_ISLANDER_ART.md) converts
Pigleg's complete pig textures and separate donor-coordinate model, plus Dobie's
complete mouthless wolf textures with a matching native rig. Thirteen focused
tests pass, retaining exact Punchy/Cheri outputs and all original game assets.
These components are not installed or selectable. Fixed model-bank assignment,
islander town behaviour and runtime dependencies remain
work; the current ABI-50 ROM and both V2 patchers are unchanged.

The [accessory batch](checkpoints/V3_ACCESSORY_ART.md) converts all sixteen
islander accessories into complete native objects: actual hats, flowers, bags,
leis, and cobra, with their verified consumer/joint bindings. Fifteen focused
checks pass, including every source pixel, vertex, and compiled triangle plus
retained furniture/speed-bag behaviour. Runtime attachment is pending; no
accessory or islander is enabled by this asset batch.

The [complete body-component bundle](checkpoints/V3_GORILLA_ART.md) converts
all twenty donor-only villagers, with all sixteen required accessory
objects included. Thirteen additional species layouts preserve complete facial
frames and source pixels, including verified mirrored/clamped edge extensions.
Shared meshes retain every ordered face, vertex binding, and joint matrix.
Yodel's separate complete model preserves all 429 donor vertices and 284
triangles, fitting the native NPC model buffer with 128 bytes spare.
Twenty-six focused conversion checks pass. The
[complete-asset loader](checkpoints/V3_COMPLETE_VILLAGER_ASSETS.md) installs all
38 objects in fixed banks, relocates growth permissions safely, and preserves
every original bank and audio DMA location. Seven focused checks and the
93-record / 59-assertion native run pass, including actual model/texture/accessory
loads and both initial populations. That loader retains the original startup
reservation and cartridge size. The
[attachment runtime](checkpoints/V3_ACCESSORY_RUNTIME.md) installs all twenty
draw records and attaches all sixteen accessories in both NPC owners, using
49,152 additional resident bytes without actor/save or ordinary-heap growth.
Seven focused tests pass. Partial native execution passes 28 assertions,
including both joint transforms, actual drawing commands, native fallback, and
buffer handling. The complete audio batch closes the remaining accessory
null/guard tail with 37 passing assertions; ordinary GPU appearance is not
established. Text/defaults, houses, town behaviour, and persistence still require work.
All move-in flags stay off; both V2 patchers are unchanged.

The [complete audio bundle](checkpoints/V3_COMPLETE_VILLAGER_AUDIO.md) supplies
all twenty additional villagers' full melody fragments and the four missing
instruments, retaining all 83 original instruments. The 9,376-byte melody set
retains every track and note. The compact font shares an identical original
envelope, limiting font/wave growth to 592/7,584 bytes without dropping sound data.
The [complete audio installation](checkpoints/V3_COMPLETE_AUDIO_RUNTIME.md)
installs all twenty sources and both expanded resources in ABI 53. Fourteen
focused tests pass. Native checks pass startup, complete font relocation,
physical sample addresses, melody copying, full-ID handling, and audio-heap
bounds. The package grows by 12,288 resident bytes; ordinary heaps and saved
formats remain unchanged. Both bounded playback attempts fail to observe a
completed sample transfer for the four new instruments, so their playback and
the final post-audio guards remain unresolved. This is not a confirmed fixture
failure or a playable-import claim. Continue text/defaults, houses, and town
behaviour; inspect note-layer progress and sample requests in the next meaningful
combined native check. Both V2 patchers remain unchanged.

The [complete villager text](checkpoints/V3_COMPLETE_VILLAGER_TEXT.md) installs
all twenty names, full catchphrases, personality values, and donor-default
references without changing reader code or increasing memory allocations.
Six focused checks pass, including all installed rows through sanitized text/mail
readers and actual save-codec subset acceptance and missing-profile rejection.
The initial native run passes 168 records / 90 assertions: O'Hare, Flossie,
Annalise, and Plucky's complete text, real dialogue insertions, phrase reset and
borrowing, unchanged save state, guards, and checkpoint restoration.
The [aloha outfit runtime](checkpoints/V3_ALOHA_OUTFITS.md) supplies both actual
shirts (`341A`, `341B`), shared resource/name/type/price readers, independent
clothing profile bits, and all eighteen islander outfit initialisers. Seven
focused checks and the corrected 109-record / 55-assertion native run pass.
The native boot defect caused by a compiled caller's live register is fixed
with checked preserving bridges; single-record name/price assumptions are fixed
as well. All original garments and unrelated data remain intact. The explicit
town policy enables selection in the experimental cartridge; ordinary move-ins
and persistence remain work. Aloha ordinary acquisition remains work.
Earlier builds missing these garments reject new saves; the saved format is
unchanged, but ordinary cross-build loading remains unverified. The audio playback
issue remains recorded, and both web patchers stay V2.

The [islander arrival houses](checkpoints/V3_ISLANDER_HOUSES.md) supply all
eighteen authentic sparse rooms, including each starting furnishing, its position,
and exact matching native wall/floor artwork. The separate furnished island
gift layouts are not substituted for arrival rooms. All twenty imported house
records and forty fixed layers are installed, with original/pilot data retained.
Five focused checks and the initial 57-record / 35-assertion native run pass,
including complete appended DMA, all sparse pointers, native and representative
house initialization, complete layer transfers, guards, and checkpoint restoration.
The cartridge stays 32 MiB, original audio/file positions remain intact, and the
scene foreground allocation grows by 18,648 bytes. Ordinary house entry and the
complete scene's larger allocation remain unverified. Ordinary move-ins,
villager persistence, aloha ordinary acquisition, and new-instrument
playback remain work. ABI 56 retains ABI 55's exact save profile and formats;
ordinary cross-build reload is not newly verified. Both patchers remain V2.

The [complete garment displays](checkpoints/V3_ALOHA_DISPLAY.md) connect all three
imported shirts to fixed mannequins, full canonical readers, four-rotation
conversion, ownership, catalogue selection, and complete preview loading. All 245
native clothing rows remain in order, with three imports appended. Six focused
tests pass across two invocations. The first native run passes 120 records /
67 assertions, including full transfers, independent dependency removal, retained
originals, state restoration, and guards. The catalogue uses 64 additional bytes
of its existing menu reservation, leaving 320 bytes; no allocation grows. Both
aloha shirts retain zero donor prices and stay out of general shop stock.
The profile adds their two display dependencies: the actual codec accepts ABI 57
saves in ABI 58 and rejects the reverse without source/output writes. Ordinary
cross-build reload remains unverified. Ordinary acquisition, placement/persistence,
temporary house-marker handling, house entry, and new-instrument playback remain open.

The [outdoor-house fix](checkpoints/V3_HOUSE_EXTERIOR.md) corrects a confirmed
animation fault: the old structure selector creates a second player for an
unrecognised imported house. Six bounded instruction edits connect all twenty
actual house IDs to structure, door, NPC, and daily-growth consumers. Two focused
tests pass. The first corrected native run loads Punchy's real house, retains one
player, passes the previous fault point, and passes nine fault/guard assertions.
Its final house-entry assertion fails (`FFFF` owner), so complete entry is not
claimed. A separate temporary-marker collision with existing buildings requires
an additive mapping before house interactions are complete. Save profile/format
and memory allocations are unchanged from ABI 58; ordinary reload is not newly
verified. Both patchers remain V2.

## Stable V2 deliverable

The served patchers' current cartridge is **V2-11** at
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
