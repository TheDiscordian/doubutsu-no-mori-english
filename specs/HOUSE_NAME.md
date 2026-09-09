# Complete villager house-sign names

## Scope and ownership

`ovl_Nameplate` at VROM `00956630`, RAM `80A963C0`, displays message `1369`
when a villager's house sign is examined. The original actor has an eight-byte
name temporary but publishes only six bytes. Its 512-byte image, 64-byte
relocation, zero BSS, actor metadata at `80102130`, and allocation remain.

The position-to-name lookup at `800ACF84..800AD084` has exactly one direct native
caller, `80A9640C`, and no aligned literal references. A pinned executable-range
audit rejects another caller or external references into the affected code.
The lookup's success call at `800AD050` uses the already verified identity bridge
`800BB708` to produce eight display bytes. The six-byte saved-name API itself
remains unchanged. World-coordinate conversion, all fifteen resident searches,
free-slot checks, and home block/unit comparisons retain their native code.

## Existing-buffer preparation

The `28`-byte actor stack frame saves its return address at `14`. The name is
at `1C..24`; the later window colour occupies `24..28`. All offsets are
hexadecimal. The replacement setup at `80A963E8..80A96414` initializes exactly
eight name bytes to spaces before the unchanged lookup. A failed position
conversion or no matching occupied home therefore displays a blank name instead
of stack contents. A successful lookup uses the complete name or fresh padded
native fallback supplied by the shared bridge.

The setup replaces redundant compiler-generated argument stores, using `t6`
for the actor and `t0` for the space word. It supplies the same destination and
three position words in `a0..a3`; the native lookup stores its own argument
homes. No value from the removed outgoing stores is read after that call.
The setter length at `80A9642C` becomes eight. Message ID, field zero, window
colour, hidden speaker label, camera, listening state, timing, and all remaining
actor instructions stay unchanged. The GC reference also publishes eight name
bytes for this same message; no English wording or line layout is changed.

## Verification scope

Verify source identity, exclusive caller, exact preparation assembly, destination
and position arguments, unchanged frames, colour, lookup branches, relocation,
atomic installation guards, previous translation retention, and UPS reconstruction.
Reuse the recorded native identity-bridge and complete-field evidence: neither
shared helper changes. Ordinary house-sign interaction and save/restart join the
combined v0 smoke; no exhaustive per-house emulator matrix is required.
