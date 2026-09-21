# Sources and provenance

Per-text authorship and source identities live in the single
[`translations/provenance.json`](../translations/provenance.json) catalogue.
The [catalogue guide](TEXT_PROVENANCE.md) explains assistant-authored entries,
human review, coverage limits, and additional languages. This page credits the
project's input resources; it is not a second per-text attribution list.

| Source | Purpose | Distribution policy |
| --- | --- | --- |
| User-supplied Japanese N64 ROM | Build input and original text | Local only |
| User-supplied AFProjectDistro.zip | Legacy patch for text-identity corroboration, and reverse-engineering notes | Archive, patch, extracted resources, and bundled utilities stay local; no general licence established |
| https://github.com/zeldaret/af | N64 decompilation and symbol reference | Pinned submodule; preserve upstream terms |
| User-supplied GAFE01 revision 0 GameCube CISO | English script and matching reference | Local extraction; no full disc distribution |
| https://github.com/ACreTeam/ac-decomp | GameCube structures, symbols, character/command tables, and password algorithm/reference checks | CC0; pinned local reference |
| https://github.com/dolphin-emu/dolphin | CISO sparse-block format reference | Format research only; no copied implementation |
| https://github.com/ares-emulator/ares | Silent emulator validation and debugger protocol | Source research; executable remains separately installed |

## Pins

- N64 decompilation: `4ddba04604ee7b4c4cfc0b64f8ee4d094bb385be`.
- GameCube decompilation: `09ca8e8b5b24e6ab44047ee980cf0088ad7ecb4c`.
- Default MIPS toolchain: `ghcr.io/dragonminded/libdragon@sha256:b68e8dfd393f76ba69c1ba62da6b42dcda8b5b52eaa8fb96adc5aab7865a2d40`
  (published Linux amd64 image, GCC 14.2.0). The explicit `AF_TOOLCHAIN=legacy`
  alternative is local image
  `sha256:281fbf9b787994c0d9454a5d8bdcaba5e23407d53f2206c75ebdc97b09d29915`.
  [Toolchain identity and setup](TOOLCHAIN.md) record verified executable hashes,
  actual report provenance, and the complete-build verification status.
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

The legacy-patched ROM is a reference, not this translation's base cartridge.
The clean recipe applies the old UPS only to a separate local inspection copy.
The inspected dialogue, name, item, and shared-word builders obtain English
payloads from the supplied GC references or source-bound project translations;
legacy agreement corroborates identity. Complete mail catalogues come from the
verified GC banks. An identity match does not transfer authorship to the legacy
patch, and it does not remove the dependency on that local reference. Preserve
these distinctions when describing reused text or changing the build inputs.

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

Credit Zoinkity for the supplied patch and reverse-engineering notes. Those
notes separately identify byuu's UPS patcher, _Demo_'s Zextract, Shevious's Yaz0
utilities, and Obsidian's macetII. These bundled programs are not included in
this project's patch archive; the standalone Python patcher is project tooling.
Acknowledging the programs is not a licence grant or a claim that they are
required build dependencies.

Patch archives, source-repository publication, and redistribution of local input
archives are separate decisions. A patch contains game-derived changes even
when it contains no full ROM or loose textures. The MIT tooling licence, CC0
decompilation notices, and successful patch reconstruction do not establish
permission to distribute Nintendo content or third-party translation work.
Keep the repository and playtest private until the outstanding release review
and approval are resolved.
