# Sources and provenance

| Source | Purpose | Distribution policy |
| --- | --- | --- |
| User-supplied Japanese N64 ROM | Build input and original text | Local only |
| User-supplied AFProjectDistro.zip | Legacy patch, tools, and reverse-engineering notes | Local only pending explicit licence review |
| https://github.com/zeldaret/af | N64 decompilation and symbol reference | Pinned submodule; preserve upstream terms |
| User-supplied GAFE01 revision 0 GameCube CISO | English script and matching reference | Local extraction; no full disc distribution |
| https://github.com/ACreTeam/ac-decomp | GameCube structures, symbols, and character/command tables | CC0; pinned local reference |
| https://github.com/dolphin-emu/dolphin | CISO sparse-block format reference | Format research only; no copied implementation |
| https://github.com/ares-emulator/ares | Silent emulator validation and debugger protocol | Source research; executable remains separately installed |

## Pins

- N64 decompilation: `4ddba04604ee7b4c4cfc0b64f8ee4d094bb385be`.
- GameCube decompilation: `09ca8e8b5b24e6ab44047ee980cf0088ad7ecb4c`.
- Local MIPS toolchain image: `sha256:281fbf9b787994c0d9454a5d8bdcaba5e23407d53f2206c75ebdc97b09d29915`
  (`doom-n64:tc`, GCC 14.2.0). The image is a local dependency, not a published
  registry artifact; the pure-Python ROM builder does not require it.
  [Toolchain identity](TOOLCHAIN.md) records inspected executable versions/hashes
  and the remaining clean public-container setup work.
- AFProjectDistro archive SHA-256:
  `d0f7e708fa2453c9f06714d9d39b1265e02f4878d330dcea99c85c52123838ed`.
- Legacy UPS SHA-256:
  `ae4d50632e9d9bcf19ccc0f9672afd3aed592784e62c7b6422526da86d74e1da`.

## Reference assessment

Cuyler36's Animal Crossing Text Editor provides useful GameCube format research.
The local e+ translation repository from ColinGamez is not an authoritative text
source: the inspected implementation uses guessed glyph mappings, skips
overlength replacements, and contains only a small substitution set. It is not
used to build this translation. The supplied English disc and pinned
decompilations provide stronger evidence for extraction and matching.

The legacy distribution already contains variable-width work, but its notes
describe an unfinished, buggy patch. Its item-name extraction offsets do not
all match the supplied patched ROM; item candidates from those offsets must not
be imported without additional verification. Furniture names also use four
rotation slots per item in retail, while the legacy lookup collapses rotations.

Extracted Nintendo text, textures, and executable binaries are generated locally.
Original code in this repository is MIT licensed; that does not grant rights to
third-party material. Translation reuse requires a recorded source and review.

The N64 decompilation's README explicitly excludes `lib/ultralib` and its other
listed subrepositories from the root licence. The GBI/MBI headers used for native
command compilation carry their own notices. Keep that distinction in source
packages; the root CC0 declaration is not blanket permission for every dependency.
The supplied legacy notes identify Zoinkity and invite script work, but the
inspected distribution has no general licence file. Do not replace its notices
with this project's MIT licence or treat that invitation as completed release
review. The legacy archive and bundled executable utilities remain local.
