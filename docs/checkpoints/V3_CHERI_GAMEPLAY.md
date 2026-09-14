# V3 ordinary Cheri gameplay checkpoint

## Scope and fixture

Target the current ABI-26 cartridge at
`build/v3-villager-rewards-01/animal-forest-v3-asset-loader.z64`.
Check ordinary town loading, full NPC construction/rendering, English dialogue,
and her actual mapped room. Follow with imported identity/house persistence.
Reuse completed component evidence; do not replay historical candidates.

The ignored `build/v3-cheri-gameplay-seed-01` seed is derived from the preserved
source town, SHA-256
`d489736e39abc7eff1c5b5085bf52e679186f2882a0247339e11603799b80b60`.
Only the disposable seed substitutes Cheri into the known slot-3 peppy resident's
location and existing interaction state. It changes actor/name identity, default
phrase, starting shirt, appearance history, and V3 profile/checksums in both
banks. Source town files remain untouched. The ROM itself remains additive and
has no original villager substitution. This fixture is not a natural move-in
test, newly generated town, or proof of move-in eligibility.

The independent checked V3 packer binds the seed to the installed profile;
catalogues start empty. The retained isolated daytime RTC is copied without
changing the host clock. Emulator execution is silent on a private X display.
Use the existing arrival/navigation scenarios and matching-current-ROM emulator
checkpoints for continuation, never cross-ROM checkpoints.

## Testing boundary

Allow one initial attempt plus one justified setup retry. Cap new harness work
at thirty minutes for this implementation batch; record unresolved navigation
or setup results and continue other implementation. Actual crashes, save damage,
or memory corruption require diagnosis and correction. Ordinary game save/reload
is distinct from emulator checkpoint restoration. Record outcomes without
claiming untested move-in, rain, mail, or hardware behaviour.

Both V2 patchers and source saves remain unchanged.

## Arrival

`build/v3-cheri-gameplay-arrival-01` completes the first ordinary cold boot and
character-selection arrival in twelve recorded steps. The translated town loads
normally from the independently packed V3 fixture, with no CPU fault or damaged
translation guard. The player stands outside the house at `(2128, 152, 1488)`.
No villager is loaded in this initial acre, so this does not establish Cheri's
construction or drawing. The disposable save changes through the game's normal
arrival processing; source files remain intact.

The snapshot reader's native-only 216-ID diagnostic limit is extended to admit
only installed V3 metadata identities 218–237. Test IDs and missing imports are
still rejected. This is test-reader maintenance needed to observe Cheri, not a
change to the game's ID handling. Continue using the matching-ROM checkpoint
for map inspection and ordinary controller navigation toward her house.

`build/v3-cheri-gameplay-map-01` confirms Cheri's complete loaded identity,
personality, and native house-list entry at `(3000, 160, 2200)`. The map opens
normally. In `build/v3-cheri-gameplay-approach-01`, the player catches the side
of a player house while moving east, so the subsequent southward movement ends
in the neighbouring resident's acre at `(2381, 160, 2142)`, not Cheri's acre.
The helper correctly reports that Cheri is not loaded. This is a documented
navigation shortfall, not evidence of an imported actor failure. The one
corrected approach uses the current checkpoint and walks around the houses;
the successful arrival/map prefix is not replayed.

## Confirmed acre-entry crash

`build/v3-cheri-gameplay-approach-02` reaches `(2548.57, 160, 2142)` approaching
the next acre, then the game thread faults: `8003CE34 = 80145630`. Cheri is not
yet a loaded visible actor. The existing native resident unloads during the
transition. The frozen view and failed fault assertion establish an actual
game defect, not another navigation/setup shortfall. This blocks an imported
gameplay handoff. The next focused run reproduces only the eastward boundary
crossing and records the faulted thread's registers and a diagnostic checkpoint.
No further navigation retry is queued; crash diagnosis/fixing is the active work.

## Streaming diagnosis and fix

The exact fault is the native DMA assertion, not an arbitrary CPU fault:
`fault_AddHungupAndCrashImpl` stops at `80029AF4`, with the diagnostic
`DMA ERROR: ../m_scene.c 613` and source `0000000`, destination `8034CD00`,
size `0`. `build/v3-cheri-acre-fault-01`, `build/v3-cheri-fault-stack-01`, and
`build/v3-cheri-fault-objects-01` retain the crashed checkpoint and read-only
thread/stack/object evidence. These are diagnostic captures, not passing gameplay.

Object status 37 at `80232D64` holds pending bank `-426`, Cheri's texture bank,
but has zero VROM and size. It is a reserved NPC texture slot, below the normal
streaming arena's first dynamic status 61. The shared scene allocator is not
the writer: NPC-specific functions `8097FDF0` and `809A0378` directly read the
old 410-entry table at `8010DDD0`. The appended bank falls beyond that table.

Both NPC functions now load `80461000`, the checked table containing every
original entry plus the imported banks. Only the table-address instruction pair
changes in each function. Complete source hashes, expected instructions, and
absence of relocations are checked before patching. Existing reserved buffers,
size caps, asynchronous DMA, and release/reuse are retained. No crash assertion
is disabled and no heap is enlarged.

`build/v3-npc-streaming-01/animal-forest-v3-asset-loader.z64`, configuration
ABI 27, SHA-256 `a9dd8d6ef851bf3141b32f84544d53058a0a8a5d41ab217b5992d518e1815b37`,
is the corrected current experimental cartridge. All three focused tests pass
in 1.137 seconds: both complete function guards, relocation of each owner,
rejected changed inputs, installed table/configuration, unchanged dependencies,
UPS reconstruction, and the unchanged import-free V2 path. Resident code/data
apart from the configuration revision remain unchanged; V3 save profiles and
the fixture's packed save remain identical.

The first gameplay invocation uses the checkpoint option against a cartridge-
save-only seed, and the runner rejects it before launching the emulator. The
corrected invocation uses `--seed-save` in a fresh output directory,
`build/v3-cheri-streaming-gameplay-02`. It cold-boots the corrected ROM; no
cross-ROM emulator checkpoint is used.

The corrected run completes twenty-one recorded steps and exits normally. The
player crosses the failing boundary and reaches `(2755.90, 160, 2142)`.
Cheri becomes a normal live `E0EA` actor at `80287930`, walks around the acre,
and responds to ordinary controller input. The navigation helper reaches an
active conversation after ten movement steps. Message `0515` contains the
English introduction, the player's existing name, and her `tralala` catchphrase.
The private capture visibly confirms the red cub model/facial artwork, yellow
bar shirt, English Cheri nameplate, and complete first dialogue page.

Both fault-pointer reads after streaming/conversation are zero; the translation
guard is intact. The recorded emulator checkpoint has SHA-256
`0a298bfc8bdc08550ecd936b1a213ac445c8c3e2cd8bebb5824207393caffbbe`.
This closes the reproduced acre-entry crash and establishes ordinary initial
construction/movement/conversation for the imported actor. It does not yet
establish a completed greeting, ordinary house visit, natural move-in,
rain/umbrella behaviour, or a game save/restart cycle.

`build/v3-cheri-greeting-choice-01` continues the same-ROM checkpoint, advances
the greeting through five ordinary A presses, and reaches Cheri's normal
three-option menu: `Can I help you?`, `Care to chat?`, and `Whoops, sorry!`.
Twenty-two recorded steps complete without a fault. The English follow-on
message `02A9` retains `tralala`. This establishes completion of the greeting
through the ordinary conversation menu; the next bounded continuation selects
the chat option.

`build/v3-cheri-chat-01` checks the actual menu strings/cursor, selects
`Care to chat?`, and completes the ordinary multi-page fruit conversation
`084B`. The full message expands from 598 to 608 encoded bytes as both live
catchphrase references resolve to `tralala`; the town name appears normally.
Nine A presses finish the conversation, with `loaded = 0`. All thirty-four
recorded steps complete, the game thread remains unfaulted, and the translation
guard remains intact. The conversation checkpoint is retained for later
ordinary gameplay/persistence work; no further chat replay is queued.
