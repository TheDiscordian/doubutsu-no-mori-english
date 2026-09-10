# Bulletin-board control artwork

Replace four Japanese texture labels with the supplied English GameCube labels:
latest entry, entry 1, Quit, and Write. Keep the native N64 button/arrow images,
button handling, notice data, animations, and all saved fields.

The original asset file is VROM `00ABA000`, 52,896 bytes, SHA-256
`9b21110f4a2cbbdaae0fcfed2c1c1ebb3f929dc0af9ac756e5716543d9f86d38`.
The four labels occupy `0858..1857`, a contiguous 4,096-byte region. Their source
formats are row-major native IA8 and tiled GameCube IA8. Untile and exchange the
intensity/alpha nibbles; preserve every intensity and alpha value.

| English label | GC data offset | Size | New native offset | Native load |
| --- | --- | --- | --- | --- |
| latest entry | `004C3A20` | 80×16 | `0858` | `0610` |
| entry 1 | `004C3F20` | 64×16 | `0D58` | `05C0` |
| Quit | `004C4320` | 32×16 | `1158` | `0680` |
| Write | `004C4520` | 64×16 | `1458` | `06F0` |

The first three labels share their original 3,072-byte allocation: 1,280 + 1,024
+ 512 = 2,816 bytes, leaving 256 transparent bytes. Write retains its original
1,024-byte position. No texture is shortened, compressed visually, or moved
outside the loaded asset file. Four source-bound native texture loads each fit
their existing 56-byte instruction block and remain below the 4-KiB TMEM limit.

Use the source's 0.875 display scale: native label heights remain 14 units,
and widths become 70/56/28/56 units. The two bottom hints use GC horizontal label
positions (`-128..-58` and `-13..43`) at the native Y coordinates. Each retains
its original N64 arrow immediately to its left: `-142..-128` and `-27..-13`.
Quit and Write keep their native button-associated left/top positions. Preserve
all vertex flags, colours, winding, Z coordinates, and icon pixels. Do not import
GameCube controller symbols or change native input behaviour.

Source bindings check the actual REL texture-pointer fixups and dimensions,
the original asset hash, the four native load/quad references, every quad's
source coordinates, and the sole readers of the moved textures. Focused tests
cover exact pixel/alpha conversion, independently compiled native GBI, bounded
label/icon layout, complete prior-resource retention, and UPS reconstruction.
Unchanged notice CPU/storage code reuses its existing evidence. Ordinary screen
appearance and navigation are separate acceptance work, not inferred from an
installed texture.
