# V3 nineteen-villager body components

## Artifact

`build/v3-islander-bodies-01/` contains 35 files totalling 143,792 bytes:
nineteen textures (98,400 bytes), Pigleg's separate model (7,360 bytes), and
fifteen required accessory objects (38,032 bytes). Manifest SHA-256:
`aaf1cdbf4ce0fb0510d50912fa4cb7cbbbd0047e4d75f834b8e9014288c0777f`.
Every output's hash, donor identity, native template, source bindings, and
unassigned runtime bank are recorded in the ignored manifest.

The fifteen additional bodies are Maelle, O'Hare, Bliss, Drift, Bud, Boomer,
Elina, Flash, Flossie, Annalise, Plucky, Faith, Rowan, June, and Ankha.
Punchy, Cheri, Pigleg, and Dobie retain their existing converted outputs.
Yodel is explicitly excluded: the shared gorilla geometry is not equivalent.
His already-converted bag does not remove that model requirement.

Construction:

```sh
python3 tools/v3_villager_art.py --all-supported \
  --accessories build/v3-accessory-art-03 \
  --output build/v3-islander-bodies-01
```

The first complete construction succeeds. The source compiler is not rerun for
unchanged accessories: their entire source-bound manifest and each object hash
are pinned. An edited receipt or changed object cannot supply a dependency.
Outputs stay ignored; no ROM, extracted asset, or save is committed.

## Conversion details

Thirteen additional species layouts use actual donor/native draw fields and
material commands. Ducks and lions store mouths before eyes. The five additional
mouthless species retain all eight eye frames and null mouth pointers. Chicken's
remaining 64 atlas bytes are zero padding. Palette, every facial frame, and every
body tile retain their actual donor values; another villager's shirt is never
copied into a new body.

The larger donor arrays include extra mirrored/clamped edge rows. Their complete
704-byte content regenerates exactly from the retained source rows before any
reduction to native tile height is accepted. A distinct pixel in an extension
fails conversion. Read-only UV inspection finds the expected tile-edge ranges;
it is not a GPU rendering comparison.

The shared-mesh check resolves partial vertex-cache updates and matrix loads
through both games' complete joint display lists. It checks 3,766 ordered faces
for the fifteen new bodies, including their material/texture bindings. The first
development comparison rejects cyclic corner permutations; direct inspection
shows equivalent winding, and the corrected check accepts cyclic rotations only.
Reversed winding, missing vertices, unknown pointers, and changed bindings fail.
All nineteen bodies verify 6,954 vertices and their actual skeleton records;
Pigleg's separately converted coordinates retain their existing special check.

## Verification and limits

Nineteen focused tests pass in 58.595 seconds in
`build/v3-islander-bodies-tests-01.log`. The tests cover all 42,496 source body pixels, all 117,760 expression pixels,
palettes, complete converted dependencies, partial-cache bounds, edge-row
reconstruction/rejection, and unchanged pilot outputs. Python compilation and
`git diff --check` also pass. The website and workflow diff against the stable
main branch is empty.

This is component conversion, not runtime installation or a playable release.
No emulator, historical cartridge, hardware, or ordinary save is executed in
this batch. The current ABI-50 cartridge, its save profile, both stable V2
patchers, and the trailer stay unchanged.

## Next work

The [Yodel conversion and twenty-body bundle](V3_GORILLA_ART.md) supply his
actual gorilla geometry. Assign stable additive model/texture
storage, implement the verified accessory joint attachment and cleanup, and
connect the remaining voices, English/default data, houses, town-compatible
behaviour, and persistence. Do not enable a villager just because its body and
accessory components exist. User testing and explicit approval remain required
before switching either web patcher to V3.
