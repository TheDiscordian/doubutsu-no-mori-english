# V3 Punchy copied-town gameplay

## Inputs and fixture boundary

The current artifact is ABI 50:
`build/v3-punchy-house-02/animal-forest-v3-asset-loader.z64`, SHA-256
`55cb90c0cc9eac32aa6e180051f1791072cfa6dd5ba1c6b8a72a413f6211e060`.
The fixture tool reads the preserved source town with SHA-256
`d489736e39abc7eff1c5b5085bf52e679186f2882a0247339e11603799b80b60`
without changing it. Only the disposable copy substitutes Punchy into slot 3
at the existing acre-4/3 home. This is not a ROM roster replacement or natural
move-in. The fixture explicitly seeds the at-home flag, so it is not schedule
verification either.

Both banks contain actor `E0ED`, name index 237, lazy personality 2, default
phrase reference `FEF3ED20`, actual cherry shirt `34BF`, appearance history,
and the current format-2 profile. Ownership starts empty. The isolated RTC is
midday on September 10; the host clock and source RTC are untouched.
`build/v3-punchy-town-seed-01/fixture.json` records every resident-field edit.
Its FlashRAM SHA-256 is
`ccd650661d413a0fb9d3f5051627586fc47f1620d2bba1089ccd5a585e2819e0`.

Two focused fixture tests pass. They verify both complete banks through the
actual C format-2 reader, restrict payload differences to declared fields,
checksums/signature/history, preserve all other residents and inventory, and
reject unknown source data or missing installed dependencies. This verifies
fixture construction, not an ordinary game save.

## Cold boot and acre crossing

`build/v3-punchy-town-arrival-01/` completes the current cold boot and controller
route: 16 recorded results, four guard/fault assertions, and graceful shutdown.
The full imported identity, personality, and home survive loading. Acre crossing
constructs actor `E0ED` at `3020,160,2220`, with the installed native update
function and draw flag. Player position reaches `2838.77,160,2142`.
No CPU fault is recorded, and translation/save guards remain intact.
Snapshots do not establish final garment appearance or completed dialogue.

## Bounded house approach

`build/v3-punchy-visit-01/` does not test movement: the scenario incorrectly
presses F7, which is frame advance, after the runner already loads the matching
checkpoint. Captures show the emulator paused. The setup correction removes
that key; the original run remains unaccepted, despite its passing guard reads.

`build/v3-punchy-visit-02/` resumes the same current checkpoint and executes
ordinary controls. The player encounters a tree/rock beside the destination;
the approach reaches `2823.13,160,2183.13`, then the northward leg ends at
`2824.61,160,1902`, outside the house. The final actor list is empty because the
player leaves the acre. All three fault/guard checks pass and shutdown is clean.
The house is not entered, no dialogue is reached, and no game save is confirmed.
Private captures document the obstruction. No physical audio is emitted.

The initial attempt and justified setup retry are complete. Preserve both
checkpoints and results; stop this navigation batch. Continue remaining donor
conversion and item integration. A future combined gameplay check still needs
house entry, complete foreground scene allocation, conversation, move-in, and
ordinary saved-identity persistence. Do not mark these passed from component
checks or copied-state loading. Both web patchers stay V2 pending user testing
and explicit approval; GitHub development source remains permitted.
