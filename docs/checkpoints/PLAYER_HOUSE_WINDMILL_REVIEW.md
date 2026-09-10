# Player-house and winter-windmill texture review

Seven selected unmatched native texture candidates contain roof, wall, door,
window, wood, and sail surfaces without readable Japanese wording. Preserve
them. This closes these candidates without applying text or changing the ROM.
The 22 resident-house textures in the separate [house review](HOUSE_ARTWORK_REVIEW.md)
are not repeated or included in this count.

## Sources and selected views

The original ROM is verified before decoding. Candidate addresses, dimensions,
and material loads come from `build/artwork-matches-01.json`, SHA-256
`424fb279c90e7ac27a30ecbdf6c578b58cdfaeb3cd8549148a2d866816ad276f`.
All selected images are CI4, 128×32, in owner `00D5E000`.

The pinned asset YAML, SHA-256
`ee29259e9dd1b389e8f2beddebc7b42bd74d25a78e9b55dfeeb1567d351e7009`,
binds the player-house atlases to `obj_[sw]_myhome[12]_t1_tex_txt` and their
seasonal palettes. The asset symbol file, SHA-256
`f8a2ef74a8bc78f8898e8a194da595e47e528c8d4205f0840a4c1ee3c88ac62a`,
binds the three winter-windmill textures and palette. All eight selected
materials load `FD100000 08000000` forty-eight bytes before the texture command.
These views use each family's `a` palette; other colour variants are not
individually inspected or claimed tested.

| Texture VROM | Palette VROM | Texture-load VROM | Finding |
| --- | --- | --- | --- |
| `00D9C4C8` | `00D5B648` | `00D9B0E0` | First player-house roof, door, and window |
| `00D9EDB8` | `00D5B648` | `00D9D9B0` | Second player-house roof, timber, and wall |
| `00DA3FA0` | `00D5B7C8` | `00DA2BB8` | Snow-covered first player-house surfaces |
| `00DA6850` | `00D5B7C8` | `00DA5448` | Snow-covered second player-house surfaces |
| `00DEF1F8` | `00D5C288` | `00DEF140` | Windmill sail, hub, and wood |
| `00DEF9F8` | `00D5C288` | `00DEF090` | Windmill roof, snow, and wall |
| `00DF01F8` | `00D5C288` | `00DEEF20`, `00DEEFB8` | Windmill door, wall, and wood |

Seven PNGs are directly inspected in `build/player-house-windmill-review-01/`.
Use the existing decoder and a fresh destination to reproduce a selected view:

```sh
python3 tools/texture_preview.py --address D9C4C8 --palette D5B648 --width 128 --height 32 --format ci4 --scale 4 --output build/player-house-windmill-review-new/00D9C4C8.png
```

## Retention and limits

The checked V1RC4 SHA-256 is
`5930435f588947df35313ae9cc2ea301af9fc7e68d59a7d8e13a48741d4f3067`.
All seven complete textures and all eight 112-byte material ranges (48 bytes
before the load through 64 bytes after its address) match the original in both
the `00D5E000` owner and the streamed `03D00000` copy. All three complete
inspection palettes match the original as well. No gameplay, drawing code,
saved data, geometry, package, or asset source changes result from this review.

This is direct texture inspection, not a fresh native scene test or hardware
acceptance. It does not close every artwork candidate. The raw matching report
also retains old image storage after some model replacements; unchanged source
texels alone do not establish that the current model still draws that image.
Check current readers before classifying such storage as untranslated.
