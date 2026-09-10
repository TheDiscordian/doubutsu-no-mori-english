# Inventory Bells-digit sizing

The combined intermediate cartridge is
`build/v1-inventory-money-fix-01/animal-forest-title-preview.z64`.
SHA-256: `5f777165ad4cf77ad18ccab6c7cf5ab1e73901093e3ffa9a7453911f0e5a4573`.
UPS: `6c87fae89a3d9015d1dd48e70d21db5c8d5e72d332082e301c43607298b3e528`.
It retains all preceding title/editor/HUD/notice/tune corrections and requires
an Expansion Pak. Original-hardware appearance rechecking remains pending.

The inventory money caller already uses individual 12-pixel digit slots.
Narrowed five-column glyphs at native 0.75 scale occupy only 3.75 pixels.
Four checked, non-relocated instructions now draw these digits at X scale
1.25 and move their origins right by 1.5 pixels. Each digit occupies 6.25 pixels
inside its original slot. Height, colours, total slot spacing, money arithmetic,
leading zeros, font, and all other text readers remain unchanged.

Three focused checks pass in 8.555 seconds. A small evaluator checks the actual
patched straight-line MIPS argument instructions, including unchanged RGBA and
Y scale; every digit fits all five slots using the installed atlas; the complete
ROM/UPS and every unrelated resource/relocation remain intact. This establishes
the correction's bounded data flow, not original-hardware visual acceptance.
