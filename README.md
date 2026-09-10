# Doubutsu no Mori English 🌲

English translation framework for the Japanese Nintendo 64 release of
**Doubutsu no Mori**, targeting original hardware.

This project is under development. It is not a complete translation or a
hardware-validated release. See [progress](docs/PROGRESS.md) for verified results
and remaining work, and [sources](docs/SOURCES.md) for third-party provenance.

The [current combined playtest](docs/V1_TITLE_PLAYTEST.md) includes the English
title, GameCube-style keyboard, translated screen/building artwork, and embedded
menu responses, along with the main English text and progression fixes. It
requires an Expansion Pak. The [patch-only bundle](docs/V1_PATCH_PLAYTEST.md)
retains explicit test limits; it is not a completed v1 or public release.

The separate [corrected v0 playtest](docs/V0_FIXES_PLAYTEST.md) addresses
the furniture-delivery conversation loop, later letter-advice continuation,
and the native shrine's map label. Its [checkpoint](docs/checkpoints/V0_HARDWARE_BUGS.md)
records the separate ROM/patch and focused native evidence. Ordinary hardware
replay and remaining Japanese artwork are still pending.

Proportional Latin text, complete English names/letters, and guarded GameCube
reference imports preserve native saved-name limits. The corrected v0 retains
the English-first radial keyboard; the combined candidate uses the grid. See
[building](docs/BUILDING.md), [keyboard design](specs/KEYBOARD.md), and the
[v0 plan](docs/V0_PLAN.md) for the bounded testing and human-playthrough workflow.

The repository stores tools, translation edits, and documentation. A legally
obtained source ROM is required to build; ROMs and extracted assets stay local.

## Priorities

1. Reproducible extraction and builds with input verification.
2. Halfwidth Latin rendering with safe control codes and buffer limits.
3. Complete text inventory and explicit translation/review status.
4. Translation, layout review, regression testing, and hardware validation.

Original project tooling is MIT licensed. Third-party material retains its own
terms; the project licence does not cover Nintendo assets or legacy work.
