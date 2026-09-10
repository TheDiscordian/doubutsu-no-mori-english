# Additional room and item artwork review

Direct inspection of 48 decoded images finds one Japanese hiring notice and
47 images without readable Japanese wording. The notice is handled in the
[separate correction](SHOP_HIRING_NOTICE.md). This is a bounded artwork review,
not a whole-game coverage claim or ordinary scene validation.

All reviewed owners are compared directly with V1RC1 before inspection and
retain their native contents in that cartridge. The existing texture decoder
uses the native palettes selected by the adjacent material commands. No art is
redrawn or generated. Local decoded views are under `build/artwork-inspection/`.
The existing `artwork-matches-01.json` supplies texture addresses and dimensions;
an unmatched GC search result is not treated as Japanese wording.

## Katrina tent interior

Owner `012B2000`, 25,232 bytes, SHA-256
`884a173a1449f1b0cae9a2dcb3ed9b2ef7326514760026d0f29d38d17395506b`,
contains the tent interior. The supplied GC symbols identify the corresponding
`rom_uranai_*` room family. Seventeen selected images are directly inspected:

| Native texture offsets within owner | Palette offsets | Visible content |
| --- | --- | --- |
| `2408` | `2308` | Circular patterned floor with celestial motifs |
| `2C08`, `3208`, `3608` | `2328` | Patterned wall fabric |
| `3A08`, `3A88` | `2348` | Table fabric |
| `3B08` | `2368` | Blue vase |
| `4608` | `2388` | Decorated stand |
| `4808`, `4888` | `23A8` | Red cloth |
| `4908` | `23C8` | Patterned furnishing |
| `4B08`, `4E08` | `23E8` | Card ornament and round golden decorations |
| `3E08`, `4208`, `5E88`, `5A88` | None | Smoke, flame, and orb/effect imagery |

Offsets are relative to `012B2000`; for example palette `2308` is `012B4308`.
The image filenames are `room-012Bxxxx.png`, using their absolute addresses.
No reliable Japanese wording is found in these images. Retain them. Two other
shadow candidates already match named GC texels in the existing inventory;
they are not counted among these seventeen newly inspected images.

## Other room and item textures

The filenames are `remainder-<absolute texture VROM>.png`. All following images
are decoded with their bound native CI4 palettes and inspected directly:

| Texture VROMs | Finding |
| --- | --- |
| `013B8EF8` | Readable Japanese hiring notice; separate correction applies GC omission |
| `013BCFF0` | Red-and-white raffle drapes/rosettes; retain |
| `013EC798`, `013ED600`, `013EDDD0`, `013EDED0`, `013EDD50` | Clock-face, pendulum, case, and ornament textures; retain |
| `013EEA68`, `013EE3E8`, `013EE5E8`, `013EE768` | Animal-shaped clock face and hands; retain |
| `013EF618`, `013EF598`, `013F0088`, `013EFE88`, `013EFD88` | Clock dials, hands, and cases; retain |
| `014275F0`, `01428240`, `014292F0` | Furniture surfaces, drawers, and patterned fabric; retain |
| `0142A6D0`, `0142B720`, `0142F458` | Stereo and wooden furniture surfaces; retain |
| `0142C6A8`, `0142D450` | Plant/pot and furniture/shaded ornament textures; retain |
| `0179F450`, `0179F2D0`, `0179FCB8`, `0179F9B8`, `0179F838`, `017A0390`, `017A0090` | Blue mechanical/radial surface details, no readable wording; retain |

These 31 images include the one hiring notice. The other thirty receive no
English replacement or translation credit. Unreviewed images, dynamic readers,
and formats outside the matching inventory remain in scope. No percentage is
computed or reported for this artwork review.
