# Catalogue navigation artwork

Replace Japanese はじめ/さいご with the supplied GameCube top/bottom images.
Native catalogue overlay VROM `007A28F0` contains its asset start/end pair
`00B2A000/00B35930` at offset `9890`. The asset is 47,408 bytes, SHA-256
`73aa49c3e550ca30ea5f09f222f0dac6f05189b2d7e5bbe90410f61a2354038a`.

Top uses source `.data:003E4E60`, a 32×16 IA8 image bound by the actual REL
texture command at `003E5AD0`. Bottom uses `003E5060`, 64×16 IA8, bound by
`003E5AB0`. Both belong to `clg_win_cbT_model` in `clg_hyouji.c`.
Untile each complete image and exchange IA8 nibbles without changing alpha or
intensity. Native destinations are `00B2A9B8` and `00B2ADB8`, each with 1,024
bytes available. Clear the unused 512 bytes after the narrower top image.

Replace the 56-byte native loads at asset offsets `0768` and `0718` with
independently compiled 32×16/64×16 IA8 clamp loads. The native top quad at `0600`
retains its left/top position (18, -79), height 14, and 0.875 display scale;
its right edge becomes 46 and U becomes 0..1024. Bottom retains its complete
native quad at `05C0`, X 68..124 and Y -79..-93. Preserve every other vertex
field, winding, arrow/button image, and display-list command.

The native arrow beside top occupies X 4..18; the bottom arrow occupies 54..68.
Both remain unchanged, with eight units separating the top label and the next
arrow. Do not import the GC C-stick diagram or reposition native controls.
Item names, prices, ordering, navigation CPU code, allocations, and saved data
remain unchanged. Checks bind source pixels, readers, compiled loads, original
geometry, complete retained cartridge resources, and patch reconstruction.
Ordinary catalogue appearance/navigation remains separate playtest acceptance.
