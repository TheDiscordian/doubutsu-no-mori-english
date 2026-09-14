# V3 umbrella review checkpoint

`build/v3-villager-umbrella-review-01/report.json` verifies the current ABI-26
reward cartridge, SHA-256
`07ce3743aac471e6672d78b3fcb55bc02d76b88d0df4b3806e7e265e1ab63a03`.
Cheri's existing umbrella 3 and Punchy's existing umbrella 13 match their donor
defaults, both native constructor consumers, and complete native held assets.
The [specification](../../specs/V3_VILLAGER_UMBRELLAS.md) records the verified
textures, palettes, geometry, material assignments, and field routing.
Two focused tests pass. No cartridge, executable, asset, or save change is needed.

An attempted umbrella build at `build/v3-villager-umbrellas-01` stops at its
own source guard before generating a ROM. It expects the donor draw fallback
to be zero based on a source comment, but the actual installed bytes are already
3 and 13. The proposed patch and ABI bump are removed; the existing source and
current cartridge remain. The review now verifies actual installed values and
does not manufacture a fix for the already-correct data. No native test is
replayed for unchanged code. Ordinary rain animation remains an explicit
gameplay check.
