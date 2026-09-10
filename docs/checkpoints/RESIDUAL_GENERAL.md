# Complete general-string bank

## Installed result

`build/residual-general-pilot/animal-forest-halfwidth.{z64,ups}` finishes every
Japanese-bearing record in the 1,562-entry general-string bank. The batch supplies
140 complete values, changing 127 rows and retaining thirteen existing matches.
Full GameCube fortune phrases, birthday animals/signs, trash labels, shop names,
test text, and usable catchphrases retain exact wording. Original unused phrases
replace donor placeholders; compact compatibility-date labels fit old small
helpers without changing active full English date formatting.

- ROM SHA-256: `8fece2aad3ee8c050ff1ed93c7403dd89e2f2428fdc7b0e9aae659df2731f7c6`.
- UPS SHA-256: `b7658ba06027a868ab84c9e781f8d2fe2ce16c1a66d3bf0dc25bc66fb1a6a31f`.
- Rebuild: `python3 tools/residual_general.py` with its exact retained-name predecessor.

Only general-string data, offsets, and cartridge repacking metadata change. All
runtime images, full names, accents, font pixels, letter catalogues, timing,
selectors, and saved fields remain unchanged. The cartridge stays 32 MiB with
the same four-MiB runtime configuration.

## Verification and accounting

All three focused checks and fourteen counter regressions pass. They cover all
140 complete values and sources, rejection of edited manifests, exact retained
bank rows, full fortune/birthday/seasonal consumers, all five shop quantity
selectors and their native capacities, complete cartridge/resource/index
retention, and UPS reconstruction. No new native harness is needed for unchanged
code. Ordinary progression and normal save/restart remain combined v0 checks.

The counter verifies exact source-bound intentional omissions for thirty Japanese
quantity suffixes. Those empty English values are already installed; newly
recognizing them is an accounting correction, not a new ROM translation. The
batch newly replaces 724 source characters and corrects credit for sixty existing
omissions. Combined accounting verifies 750,175 replaced source characters out
of the unchanged 751,284, with no uncredited Japanese-bearing general-string row.

## Next implementation

Finish the 23 remaining classic letter variants and eleven command-only letter
components. The classic IDs are `0000/0001`, `004D`, `0053..0056`, `0058..005B`,
`00BF`, `00C0..00C4`, `0182/0183`, and `0186..0189`. Complete English references
already exist for eighteen variants, but unused catalogue presence alone does
not establish an installed generation path. Five reserve bodies retain the
Japanese bytes even in the English donor; translate their meaning as reserve
text rather than copying the donor decoder's unrelated symbols. Preserve frozen
catalogue interpretations and the 122-byte saved envelope.

The remaining two six-byte NPC tail slots and ten-byte furniture tail slot are
zero-filled structural storage, not phrases to overwrite with filler English.
Keep them untouched. After text implementation, use the bounded combined v0
gameplay/menu/editor/mail/board/save checks and patch-only playtest handoff.
