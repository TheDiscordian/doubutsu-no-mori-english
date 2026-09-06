# Current progress

## Active work

Inspect the supplied AFProjectDistro archive and original ROM. Establish a
reproducible extraction/build pipeline, map the text format and renderer, and
compare the original and legacy patched resources.

## Complete

- Workspace and repository rules established.
- Existing Docker N64 toolchain and archive utilities located.
- N64 decompilation located at `zeldaret/af`.

## Remaining

- Verify source hashes and recover the legacy patch reproducibly.
- Pin upstream reference code and document its relationship to the ROM.
- Extract and round-trip text banks, preserving control codes.
- Implement and test halfwidth rendering.
- Audit text coverage, crashes, menu constraints, and save compatibility.
- Extract English GameCube references if supplied and match them conservatively.
- Translate and review all remaining text and graphics.
- Complete silent emulator regressions and an original hardware test matrix.
- Prepare a patch-only public release after validation and provenance review.

## Release status

No release candidate exists. Original hardware validation is outstanding.
