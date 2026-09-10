# Base translation reproduction

## Current state

The [isolated recipe](../../specs/V0_REBUILD.md) passes all sixty-one source/resource,
compiler, integration, and finishing stages from an empty build directory.
`build/v0-rebuilt-02` clones clean source revision
`04539bd1daa310ae5c98e4a41f93e001cd3d88f9`, the pinned N64 and GC reference sources,
and read-only copies of the verified native ROM, legacy reference patch, and GC
disc. It uses no retained generated resource, compiled overlay, or translation ROM.

The 805 build-source hashes remain unchanged. Fresh extraction, candidate
generation, compilation, complete integration, accent/residual/classic-letter
finishing, and both first-job corrections complete in 378.255 seconds of stage
work. The successful boundary after forty-eight stages resumes with checked
input/source identities and every previously generated output hash.

Final output is `source/build/v0-hardware-fixes-02/` below that run directory.
ROM SHA-256 is
`b93a54b8804f262e1c05e7dabcd6aac4f5b47d637c69d94264f058c12dbdbd35`;
UPS SHA-256 is
`378400869b2b4965f6a5641a23c861fbc5a1d0b98e445ab43d88a6a548cbc3ea`;
canonical build-report SHA-256 is
`5fe4d9b4731470dd9f095f88165133fc629622d6478d9e0b6dd86e65742606a0`.
All match the supplied corrected v0. The final standalone UPS reconstruction
check also passes.

Recipe SHA-256 is
`05fb86759b300a45b8b79cb1f57a32b32c0677d3a5d4c8b7a555195cbcf2b4d0`;
`inputs.json` SHA-256 is
`9366885f187eaaa95cbc8b633914b2604f11a681153f68fa98f79acd48a390a2`;
`result-61.json` SHA-256 is
`4f2133a81e62edcd9603b6b6e230c09d31ece0c4f77627a0bc07ede29e567642`.
Seven focused orchestration tests pass in 0.005 seconds, including refusal of
changed recipes, completed outputs, redirected outputs, and incorrect final ROMs.

## Executed resource batch

`build/v0-rebuilt-01` starts from clean source revision `3c71d45`. All seventeen
resource stages pass from an empty build directory. The generated item names,
character names, catchphrases, NPC reply words, and exact name aliases match the
retained resources. Fresh resident and world-font compilation also pass.

Candidate generation then rejects the recipe's world-font argument because
that profile requires an installed item resource. Candidate preparation does
not install world items. The recipe compiles the complete mail-glyph-only font
for candidate validation and retains the world font for actual integration.
No production validator is weakened. This is an orchestration dependency error,
not a game failure. The rejected run and log remain intact; the corrected recipe
uses a new output directory.

No passing gameplay evidence is repeated for unchanged code. The current
playtest, earlier artifacts, and the user's saves remain untouched. Portable
public compiler setup and redistribution review remain separate preparation.
