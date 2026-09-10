# Base translation reproduction

## Current state

The [isolated recipe](../../specs/V0_REBUILD.md) contains sixty-one source/resource,
compiler, integration, and finishing stages. Its full clean-checkout execution
is in progress; the recipe is not yet a verified replacement for the retained-base
instructions.

The first bounded run regenerates resources through `item-articles` in a fresh
directory. Continuation compiles the resident module and required overlay
variants, assembles the full integration, and applies the accent, residual,
classic-letter, and hardware corrections. The final cartridge/report/patch
must match corrected v0 before this checkpoint can claim complete reproduction.

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
