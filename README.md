# Doubutsu no Mori English 🌲

English translation framework for the Japanese Nintendo 64 release of
**Doubutsu no Mori**, targeting original hardware.

This project is under development. It is not a complete translation or a
hardware-validated release. See [progress](docs/PROGRESS.md) for verified results
and remaining work, and [sources](docs/SOURCES.md) for third-party provenance.

The [v0 plan](docs/V0_PLAN.md) targets the base translation and bounded safety
checks, then a playtest patch. The human playthrough follows that build. English
title artwork and the GameCube-style keyboard are v1 stretch goals.

The [current private playtest correction](docs/V0_FIXES_PLAYTEST.md) addresses
the furniture-delivery conversation loop, later letter-advice continuation,
and the native shrine's map label. Its [checkpoint](docs/checkpoints/V0_HARDWARE_BUGS.md)
records the separate ROM/patch and focused native evidence. Ordinary hardware
replay and remaining Japanese artwork are still pending.

The experimental pilot includes proportional Latin text, guarded GameCube
reference imports, and an English-first N64 keyboard with translated labels and
prompts. It retains the native radial layout and saved-name limits; a
GameCube-style grid remains a separate upgrade. See [building](docs/BUILDING.md)
and [keyboard design](specs/KEYBOARD.md).

The repository stores tools, translation edits, and documentation. A legally
obtained source ROM is required to build; ROMs and extracted assets stay local.

## Priorities

1. Reproducible extraction and builds with input verification.
2. Halfwidth Latin rendering with safe control codes and buffer limits.
3. Complete text inventory and explicit translation/review status.
4. Translation, layout review, regression testing, and hardware validation.

Original project tooling is MIT licensed. Third-party material retains its own
terms; the project licence does not cover Nintendo assets or legacy work.
