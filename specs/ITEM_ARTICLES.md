# Complete-name item articles

The treasure creator uses the same native item conversion and full-name index as
`af_load_item_name`. The selected article entry must match the CRC32 of the exact
sixteen-byte name returned by that loader. A missing translation, stale name, or
invalid item prevents publication. Clues that do not mention the item do not
require name/article lookup.

## Source binding

`tools/item_articles.py` verifies the Japanese ROM, reconstructs the approved item
names, and checks the supplied GameCube REL and symbol map. Each donor-backed name
must equal its exact sixteen-byte English reference field. Its article comes from
the corresponding `ftrArt` or `itemArt_*` entry. This preserves metadata associated
with that approved name, without guessing by spelling. Native placed-item
conversion chooses which installed field is actually used; GameCube furniture
indices are reference identities, not native item IDs.

| Input | SHA-256 |
| --- | --- |
| Supplied decoded GAFE01 REL | `29306a927eee861b073c571408393f99cb384048684eee4bff3d219725429837` |
| Supplied REL symbol map | `e5267b989d235655c51885bd2a660b3e8c2cbd46d60b2b3c46166d337c7bca87` |
| Original approved name profile | `69e7bf2e099e652463deecd3a1416f09774c9b4b4810bfc3cfd104956eff4add` |
| Original immutable article profile | `639aaeb04f49e5c5e06daaae7c395bd4691fb68f3ec0d3ddd018e0946e04686d` |
| Expanded approved name profile | `e64c6e93659af310860458964ef02690f3cc1d5914e896070a004b453ea47bcd` |
| Expanded immutable article profile | `eee68e48d3a6f5e68cfc23288c2776402a46958a37206477cc4f72e1b2d5c4c1` |

The 22 native-specific identities use sixteen explicit wording approvals in
`translations/n64-item-articles.json`. Repeated console names share a grammar
approval while retaining each native identity and complete-name provenance.
Every original name requires an approval. A changed name resource requires a
fresh complete article build/audit and an updated immutable profile approval;
changing a generated manifest's self-reported hash is insufficient.

## Format and ownership

The 8,576-byte resource contains:

| Offset | Meaning |
| --- | --- |
| `0..15` | BE32 magic `41464941`, version one, 1,703 entries, five-byte stride |
| `16..47` | SHA-256 of the complete approved name resource |
| `48..8562` | Entries: article byte followed by BE32 complete-name CRC32 |
| `8563..8575` | Zero alignment padding |

The first 756 entries follow ordinary category fields. The final 947 entries each
represent four identical furniture rotations. The builder rejects unequal fields
or unequal approval presence within a rotation group. Articles `0..4` mean no
article, `a`, `an`, `the`, and `some`. Marker `255` with CRC zero is unavailable.
The original profile covers 3,563 translated fields and rejects the remaining
981; the expanded profile covers 4,397 and rejects the remaining 147. These
are name-resource counts, not a separate overall translation percentage.

`overlays/mail_generation/item_article.c` validates the original 16-bit item ID,
calls native conversion at `800BF10C`, uses resident `af_item_name_index`, and
checks the selected complete-name CRC. The resource lives only in the on-demand
creator. The loader's approved whole-image CRC binds it before execution. The
installer requires the matching full-name DMA resource and enabled configuration.

The complete seasonal creator is 58,144 bytes with 848 relocation bytes and an unchanged
5,344-byte workspace. No permanent resident or saved memory is added. Tests cover
the entire 16-bit item-ID domain, changed name bytes, exact metadata, invalid
inputs, and configuration mismatches, including sanitizer execution. The complete
installed creator must declare the exact hash returned by verification of its
embedded article bytes; the installer and installed-ROM verifier compare that
identity to the actual enabled name resource. Accepting either name profile
without checking which article table is installed is forbidden.

The expanded creator retains all original code and relocations; only its article
data and configured whole-image CRC change. The original profile may retain the
pinned original generator provenance, hash
`c913ac8565b1dcdc6d4dbd0a7bf8d7229653cf409d0473271df7e478bae666ca`,
while every compiled source and immutable resource remains checked. New profiles
cannot claim that old generator. Controlled native treasure ownership, undo,
publication, and complete reading have evidence in the
[treasure checkpoint](../docs/checkpoints/NOTICEBOARD_TREASURE.md); current normal
gameplay, newly translated item publication, save/reload, and hardware acceptance
remain required.
