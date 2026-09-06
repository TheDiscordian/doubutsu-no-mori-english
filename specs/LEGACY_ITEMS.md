# Legacy item-reference extraction

## Authority

Use the supplied patched ROM's actual code and tables, not the archived offset
notes. The supported legacy main-code SHA-256 is
`f5ec79a742ac3555b99c8c8588f950a4e98bb0e8f81b5382c73556d7f8bed742`.
Unknown loader code fails extraction. This is read-only reference recovery; no
legacy executable code is copied into the translation runtime.

`8009E3E4` selects item groups `20..2F` through sixteen table pointers at
`8009E418`, sixteen counts at `8009E458`, and sixteen data pointers at `8009E468`.
`8009E3B4` handles furniture: it masks the low twelve item bits and shifts right
by two, then uses table VROM `010F4C50`, data VROM `010F84A4`, and count 947.
The common lookup at `800C3E54` uses cumulative end offsets and a strict
index-less-than-count check. Each offset table has a following zero terminator.

All tables/data reside in VROM `010F4000..010FF19F`. Extraction verifies code
identity, ordered/nonoverlapping table and data spans, counts, cumulative offsets,
terminators, and unchanged reconstruction. Unused capacity remains preserved.

## Native identity mapping

Native ordinary item names use the same group/low-byte index. Native furniture
names instead store four identical ten-byte strings for each rotation group.
There are 947 complete groups and a final filler slot. The legacy and GameCube
furniture lookups both divide the low twelve item bits by four. Inventory records
the legacy donor ID explicitly, and the native filler receives no invented donor.

Correct extraction does not establish a GameCube match. The legacy uses different
wording for many items, and some names are misplaced. For example, its first two
music labels are exchanged relative to the native Japanese names and GameCube
reference. Plants also have different GameCube indexing after added entries.
Candidate import still needs per-entry identity and complete capacity checks;
case-only naming differences may be considered separately from wording changes.

## Acceptance

Tests cover every legacy bank's unchanged reconstruction, actual loader-derived
data positions, counts, corrupt code/table rejection, and all 947 native furniture
rotation groups. These references are local-only generated data, not approved
translation edits or a claim that the legacy runtime is stable.
