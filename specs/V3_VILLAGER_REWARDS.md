# V3 villager house gifts

The native house-gift selector at `800AB8A0` scans only type-1 furniture.
Both passes need to include enabled imported type-3 furniture, otherwise the
imported barrels in Cheri's complete house cannot become her furniture reward.

The bounded replacement occupies `80463A00..80463FFF`, after the installed
selection code and before the villager reader. The installer checks the entire
native selector and retained exclusion filter before replacing its entry.
The native caller, stored reward field, and gift retrieval remain unchanged.

The original 10-by-10 scan, 16-cell row stride, count-then-select ordering, one
random draw, native exclusions, and full item ID with rotation remain intact.
Original type-1 items still use `mNpc_CheckSelectFurniture`; imported type-3
items require their enabled resident furniture profile. Empty/missing layers,
out-of-range layer indices, and unknown/disabled imports cannot produce gifts.
No heap, actor, or saved layout grows.

## Verification scope

Check mixed original/imported rooms, native excluded categories, scan boundaries,
rotations, disabled/unknown imports, and the no-candidate/no-RNG case. One combined
native check targets the installed selector and its ordinary list-population and
retrieval callers, including Cheri's actual main layer. Preserve the live RNG,
resident profile flags, NPC list, and animal records, and restore the emulator
checkpoint. This does not claim an ordinary gift conversation or acquisition.
New test construction/debugging remains bounded to 30 minutes for this batch.

Move-in eligibility remains disabled. Both V2 web patchers remain unchanged.
