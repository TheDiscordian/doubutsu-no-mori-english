# Town-tune control labels

Port the supplied English Play, Erase, and OK images. Retain the original N64
Z/R/Start controls, animated button images, notes, tune handling, and saved melody.
The source file at VROM `00AD1000` is 48,336 bytes, SHA-256
`a1644c0082cf2ae0cafc5a9d21290838a55863f2a787ec285ec3b3b6bd99ece6`.

Play and Erase are 64×16 IA8 in both games. Their native destinations are
`00AD77C8` and `00AD7C48`; donors are `.data:004A2500` and `.data:004A2900`.
The actual source-model texture commands at `004A40B8` and `004A4098` bind their
REL pointers and dimensions. Preserve every untiled pixel's intensity/alpha,
with the native nibble order. Native 64×16 quads and loads remain unchanged.

The finish label at `00AD53C8` is native 64×16 I4. Replace it with the complete
32×16 GameCube OK image at `.data:004A4980`, bound by model `004A9310`, and clear
the unused trailing 256 bytes. A source-compiled 56-byte load at `00AD5118`
selects 32×16 I4 with clamp addressing. The quad at `00AD4650` retains its
native centre (105, -56.5), Z, flags, colours, and 0.9375 display scale: X becomes
90..120, Y remains -49..-64, and U becomes 0..1024. Preserve winding and all
other native geometry. The label stays centred in the original finish control.

Only three texture regions, one load block, and one quad change. Their original
allocations and TMEM bounds suffice; no CPU code or saved format changes.
Focused tests bind actual donor pointers, complete converted pixels, the
independently compiled native load, unchanged surrounding resources, strict
installed keyboard/notice ownership, and patch reconstruction. Ordinary
appearance/input acceptance is not inferred from these data-only checks.
