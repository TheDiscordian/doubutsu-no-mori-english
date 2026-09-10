# Source artwork matching inventory

`tools/artwork_matches.py` is a read-only review aid, not a translation counter
or an automatic graphics installer. It identifies material candidates in the
verified native cartridge and exact texel matches in named English GC sources.
Its output helps select remaining images for direct inspection. A match alone
does not establish English wording, palette equivalence, active runtime use,
or original-hardware appearance. Unmatched does not mean Japanese.

Require the exact original ROM, decoded supplied REL, and pinned symbol map.
Resolve actual same-module `.data` relocations for GC Dolphin texture commands
inside named model objects. Bind each selected texture range to a named source
object with sufficient storage. Decode complete GC tile blocks only. Scope the
first inventory to CI4, CI8, I4, I8, and IA8; record unsupported formats and
unresolved sources without treating them as reviewed.

Find candidate native texture loads followed by a supported render-tile setup
and tile dimensions within the same short RDP command sequence. Accept segment
6 pointers only within the containing file-backed DMA owner. This intentionally
does not resolve cross-object segments, dynamic material construction, segmented
suballocations, vertices, palettes, or complete display-list reachability.
Malformed, out-of-bounds, unsupported, and otherwise unresolved candidates are
reported rather than silently promoted to matches.

Match format, dimensions, and complete row-major texel bytes. Deduplicate native
image identities by owner-relative texture address, format, and dimensions;
record every candidate command and matching named GC image. CI matches compare
indices, not visible colours. Ignore no source glyphs, award no translation
credit, and make no statement of complete whole-game inventory.

Write a new ignored JSON report with input hashes, counts, explicit limitations,
and reproducible candidate addresses. Never modify cartridges, generated patches,
saved data, source checkouts, or earlier reports. Tests cover tiled conversion,
material parsing, invalid bounds/segments, named source binding, deduplication,
and the real-source inventory's known English/native civic and shop assets.
