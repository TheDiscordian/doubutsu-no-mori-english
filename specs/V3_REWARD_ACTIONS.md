# V3 shared golden-tool reward actions

## Registered behaviour

The shared `--refresh-runtime --player-actions` stage follows reward persistence.
It registers all twelve non-null donor callbacks for action indices 118, 119,
and 120 in the existing 121-entry native action tables. Every original action,
the imported fan action 109, all byte metadata, and every unrelated callback
remain unchanged. Other unfinished imported actions stay null.

| Action | Source role | Registered implementation |
| --- | --- | --- |
| 118 | Golden-item celebration, including the submenu route | Shared setup, main, persistent settlement, submenu request, and native net-reset callback |
| 119 | Event-requested golden-item celebration | The same setup/main/settlement and native net-reset callback |
| 120 | Golden-axe delay after the reward conversation | Source waiting setup/main and native net-reset callback; no settlement or submenu callback |

Source tables are resolved again from complete donor consumers and relocations.
Each installed pointer must match the prior source symbol/hash, occupy an
originally disabled slot, and have a known complete implementation. Null source
callbacks remain null. The existing relocation-aware dispatcher resolves native
linked pointers against the actual loaded player owner and accepts resident
import callbacks. No native owner or relocation resource changes in this stage.

## Requests and timing

`af_v3_reward_request(game, action, type, priority)` preserves the native request
permission and priority checks. Only after acceptance does it request the action
and write the four-byte type at actor offset `D58`. Types are axe/net/rod/shovel
0–3; action 120 carries no type and leaves that field unchanged. Null games,
unsupported actions/types, and a missing actor are rejected without a request.

The public event helper requests action 119 at priority 34. The axe-wait helper
requests action 120 at priority 33. The registered submenu callback requests
action 118, shovel type three, at priority 31. These source priorities are not
replaced with arbitrary values to force a request through.

The axe wait resets the transient timer at `D10`, uses native WAIT1 and the
actual held-item upper motion/part mask, and selects the requested action through
native Base setup. It preserves the donor's WAIT1 continuation predicate:
no current morph, matching lower/upper motions, and a compatible part mask retain
both current frames with zero morph; otherwise it starts at frame one with morph
minus five. Native Base1 lacks that optimization, so the adapter supplies it
explicitly before calling the original animation initializer.

The main callback retains reinput, combined animation, lean recovery, normal
face, standing correction, type-one background checks, and held-item updates.
The source delay is 320 updates at animation speed 0.5. Native speed is 1.0;
the timer advances by two through 160 updates, then requests the axe celebration
on the following update. A rejected request is retried without restarting the
delay or skipping native request rules. The waiting action itself does not
award an item, mark a trophy, play the celebration fanfare, or set completion.

## Storage and bindings

The 308-byte request group occupies `804B24E0..804B2613`, after the unchanged
message controller ending at `804B24DC` and before bobber artwork at `804B2800`.
Its entry points are request `804B24E0`, event `804B25E0`, axe wait `804B25F0`,
and submenu `804B2600`.

The 668-byte waiting group occupies `804B3C90..804B3F2B`, after the unchanged
reward controller ending at `804B3C8C` and before the icon guard at `804B3FF0`.
Setup is `804B3C90`; main is `804B3DD0`. Linker bounds and full module/zero-space
checks protect both neighbouring resources. No resource, module, heap,
permanent reservation, save format, or selected profile grows.

Complete source request/wait/continuation functions and every direct native API
are bound by hashes. The two action-bound consumers outside the player need no
new hook: all three donor event-position values are zero, matching the native
out-of-range result, and the equipment-change callback still returns only
`-1`, `7`, `8`, `9`, or `10`. The unrelated native resource-size bound is retained.

## Verification and remaining integration

The [checkpoint](../docs/checkpoints/V3_FURNITURE_PIPELINE.md#shared-reward-action-registration)
records the exact cartridge and results. Host sanitizers exercise accepted and
rejected requests, untouched actor bytes, source priorities, all wait-continuation
branches, the complete delay, rejected-request retry, and null arguments.
Cartridge checks bind source/native APIs and all twelve callbacks, retain other
data/resources and disabled actions, and verify optional composition and UPS.

The native component check uses the actual registered setup/main dispatchers,
with no temporary callback slots. It covers both celebration variants, real
priority rejection, sampled wait boundaries, actual wait-to-celebration-to-idle
transitions, and the saved active-player celebration bits. It simulates the
message-completed phase; it does not establish a player reading/dismissing every
message or a complete reward conversation. Isolated test-only request trampolines
reach cartridge-loaded code. Live state and the emulator checkpoint are restored.

Ordinary acquisition still requires the source collection-completion event
director/NPC support, perfect-town reward conversation, and gold-tree growth/drop
route. Additional shovel pickup/submenu consumers must request the new action
where the source does. These are required gameplay integration, not replaced
with shop stock or arbitrary letters. The four golden-tool choices remain
disabled. This stage adds no English text; existing source credits remain in
the single provenance catalogue. Format-3 save/profile restrictions continue
unchanged; both served V2 patchers and the main lock remain untouched.
