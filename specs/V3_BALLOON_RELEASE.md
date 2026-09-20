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

## Required consumers

The actor and its player lifetime are installed. Ordinary balloon release,
exchange release, and loss during a fall are **not yet connected**. Continue
through the shared release category, retaining native fish/insect behaviour:

- Balloon release setup uses the owned actor, source position/angle/frame rules,
  and optional existing actor pointer.
- Balloon look/head tracking returns the source continuation result; completion
  waits for both the native time boundary and that result. Preserve the deferred
  golden-shovel reward flag and original request permissions.
- Fall/get-up transfers the actual hand position, gathered frame, and balloon
  angles before clearing the equipped item. A missing actor must not lose the
  item. The get-up transition uses the source balloon release continuation.
- Ordinary and inventory-exchange actions release the correct selected shape;
  dropping its room representation is not equivalent to flight.

The four golden-tool choices remain disabled. Saved format three, selected
profile requirements, and existing incompatibility warnings remain unchanged.
Neither served V2 patcher nor the main V3 lock is switched. Native component
results and limits belong in the [checkpoint](../docs/checkpoints/V3_FURNITURE_PIPELINE.md#shared-flying-balloon-actor).
