# Shared flying-balloon actor

## Source and identity

`tools/v3_balloon_actor.py` installs the complete flying actor shared by all
eight balloon parents `2244..224B`. The source is the supplied GAFE01-r0
`ac_balloon.c`, complete REL text `000A3B2C..000A42F0`, and `Balloon_Profile`
at data `00012788`. Their complete bytes and relocations are bound in the build
receipt. The existing converted held resources `40..47`, idle motion `48`, and
gathered motion `49` supply the actual models and animation, without reconversion.

Additive actor `CB` uses native background category four, corresponding to donor
category five, keep bank three, and source flags `30`. The existing descriptor
selector handles every other ID, including the additive tent `CA`. Native
`C9` remains the no-demo sentinel. No original actor descriptor or gift-balloon
code/artwork is repurposed; the native gift balloon is a different mechanic.

## Lifetime and memory

The original player constructor's `Player_actor_ct_other_func1` call goes through
a wrapper that calls the complete original function, then creates one flying
actor if any balloon is selected. The player stores its pointer at `13A0`.
The allocation grows from `13A0` to `13B0`; native zero-initialization clears the
new storage. No-selection profiles create no flying actor. Allocation failure
leaves the pointer null and changes no inventory item.

The actor owns `2080` bytes. The source layout through `478` retains its
112-byte native keyframe, eight work and morph vectors, two banks of four
matrices, modes, angles, frame, speed, and position. Its `ready` field prevents
drawing incomplete resources. At `480` begins a private 5,728-byte model bank;
at `1AE0` begins a private 1,440-byte animation bank. Neither aliases the player's
held-item banks. Native scene teardown owns the actor and its embedded storage;
there is no separate heap buffer to leak. The additional scene allocation is
8,336 bytes including the player's sixteen-byte extension, when balloons are
selected. Existing heap limits and permanent reservations are unchanged.

Code occupies `804AC300..804ACBDC` (exclusive end), inside the verified unused
category-art suffix. The mutable descriptor and profile occupy
`804AEA40..804AEAA0`. Bounds protect complete category artwork, deferred reward
code, event records, and the existing module guards. The descriptor's native
loaded-instance counter is intentionally mutable; startup checksum validation
occurs before actors are created.

## Behaviour and rendering

Hidden actors follow the current player. A selected release request records the
source shape, orientation, lean, position, animation frame, and speed. Invalid
shape indices retain the source's first-shape fallback while preserving the
requested type. A null actor or unselected parent rejects the request without
changing the actor.

Flight setup transfers the full model, evaluates the source gathered/idle pose
at the requested frame with zero speed, then switches to idle at frame one,
speed `0.5`, and morph `-5`. Failed transfers leave the actor hidden and not
ready. Resource loading uses the native **VROM** reader at `800B1650`, not the
distinct origin-offset reader at `800B1614`, and rejects out-of-range transfers.
The installed pointer/size/VROM hooks are checked against their actual helpers.

Each native update executes two donor substeps. Each substep advances animation,
smooths pitch/roll/lean with the source `1-sqrt(0.5)` rule and `50/5` limits,
applies half gravity, calls the native environment function, and integrates
half velocity plus native collision displacement. This preserves the donor's
60-Hz movement instead of approximating it with a doubled end-frame step.
More than 200 units above the player requests hiding on the next substep.

Drawing retains the source transform order, two-frame matrix ownership,
reflection/light setup, and all four skeletal display lists. The complete native
materials use AA/CVG_X_ALPHA, matching the installed held-balloon adaptation;
GX-only texture-edge opcodes must not enter an N64 display list. CPU segment six
is separately bound for animation and model consumers and restored after calls.
Opaque/translucent display-list segments are restored after drawing. The drawer
checks arena capacity before emitting anything and balances the matrix stack.

## Release, exchange, and fall consumers

`tools/v3_balloon_release.py` is the next shared `--player-actions` stage. It
binds the complete donor release/get-up groups, submenu setter, exchange, and
equipment setter to the checked native APIs. All eight shapes share one action;
there are no per-item scripts or new choices. The native fish/insect setup,
tracking, and deferred reward implementation remain the fallback.

Request type two uses native action 81 and its actual permission/priority checks.
Invalid/unselected shapes, missing owned actors, and a foreign existing-actor
pointer reject without changing requested state. Successful requests preserve
the deferred reward flag at `D70`; setup transfers it to `D20`.
The registered submenu and setup callback slots for action 81 select the new
shared implementation, with ordinary native fish/insect paths delegated.

New flight uses the donor's exact position offsets, player yaw, frame `-1`, and
speed seven. Existing flight is reused without resetting its pose. The native
held-item, body-animation, and base-action setup still run, at native speed one.
Head tracking uses the balloon's position plus fifty vertical units, native
distance/angle readers, donor yaw/pitch limits, and two donor smoothing substeps.
The first thirty native updates track the actor. Thereafter the head returns to
neutral, but release still waits while flight is active or a mode is pending.
Completion requires both forty-two native updates and a true continuation result.
It then requests ordinary wait or the deferred golden-shovel celebration.

The actual get-up item callback transfers the current right-hand position,
gathered animation frame, combined pitch, yaw, and lean into the owned actor.
Only an accepted flight request clears equipment; no actor or an unselected
shape retains the held item. The donor title-demo exception retains the saved
equipment. Other tools delegate to the complete existing shared recovery helper.
The completed get-up animation requests action 81 at source priority thirty,
reusing the already flying actor; ordinary get-up retains settlement and wait.

The exchange callback uses the converted outgoing item identity and queues
selected balloons through this same action. It does not place a room model on
the ground. Failed queueing uses the existing warning path without closing the
menu. Successful queueing retains the source close/sound sequence and deferred
reward condition. No new item is awarded by this adapter.

The release/queue group occupies `804B1100..804B1778`; the public queue entry is
`804B1680`. Head tracking occupies `804AEAA0..804AEDD4`, and fall/get-up occupies
`804ACBE0..804ACE08`. The extended exchange uses `804AD650..804AD9B4`.
All ranges fit checked existing reservations. Continuation and fallen-shape
state use player words `13A4` and `13A8`; the player stays `13B0` bytes, and
neither scene allocations nor saved formats grow. The native Look call loses
its one internal relocation. Other original callbacks, instructions, and
relocations remain apart from the explicit get-up and completion entry jumps.

## Ordinary inventory menu

The shared installer appends menu type 44 with `Grab`, `Let Go`, and `Quit`.
Source `mTG_tag_word_fly` at REL data `00082A50` supplies the official sixteen-byte
label, credited once as `v3/ui/balloon/let-go` in `translations/provenance.json`.
`mTG_field_balloon` binds the source choices and `mTG_fly_proc` binds the handler.
Grab and Quit reuse the complete existing translated objects and callbacks.

All eight selected parents use this menu outdoors. The wrapper preserves native
room-placement type 12 indoors and restricted type eight elsewhere. Present and
quest conditions retain the complete original selector, including the existing
furniture-import hook. Unselected and unrelated items also retain that selector.
The live field byte is `80136EA1`, derived from the native selector's actual
address-loading instructions; it is not the saved town-data base at `80126EA0`.

The handler uses the native table-position reader and guards the fifteen-slot
pocket range and item condition. Public queue entry `804B1680` validates the
selected shape and owned actor before consumption. A rejected queue uses the
native warning without changing pockets or closing the menu. Success records
the selected slot/item and calls the existing pocket setter, retaining its
wrapped-import hook. Ordinary release empties that slot; native exchange mode
replaces it with the current hand item. The original return-tag initializer,
close callback, and sound request remain. Flight/fall/reward code is not copied.

The 680-byte resident menu group occupies `804AFBF0..804AFE98`, inside the unused
held-collection suffix. The module, scene actor, save state, and selection profile
do not grow. The complete 44-row native table is copied and extended to 45 rows
at `8087A070`; all sixteen native table references, including mutable money-menu
rows, point to the extended table. Every original row and pointer relocation
is retained. The new resident callback must not receive an overlay relocation.
The wrapper replaces the selector's single call at `80875834` and removes only
that call's internal relocation.

The tag owner grows from 44,384 to 44,784 bytes and its relocation resource from
3,568 to 3,760 bytes. The parent allocation descriptor and rounded shared-menu
reservation grow by 384 bytes. The shared owner-tail storage accepts only these
two explicitly sized/hash-bound resized owners. It retains their logical DMA
identities and rejects unknown resize requests or occupied cartridge space.

Ordinary menu interaction, full gameplay flight, GPU appearance, and original
hardware remain unverified. Focused native component results do not close these.

The four golden-tool choices remain disabled. Saved format three, selected
profile requirements, and existing incompatibility warnings remain unchanged.
Neither served V2 patcher nor the main V3 lock is switched. Native component
results and limits belong in the [menu checkpoint](../docs/checkpoints/V3_FURNITURE_PIPELINE.md#shared-ordinary-balloon-menu)
and [release checkpoint](../docs/checkpoints/V3_FURNITURE_PIPELINE.md#shared-balloon-release-exchange-and-fall).
