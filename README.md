# Doubutsu no Mori English 🌲

English translation project for the Japanese Nintendo 64 release of
**Doubutsu no Mori**, targeting original hardware.

This project is under development. It is not a complete translation or a
hardware-validated release. See [progress](docs/PROGRESS.md) for verified results
and remaining work, and [sources](docs/SOURCES.md) for third-party provenance.

The [current V1RC3 playtest](docs/V1RC3_PLAYTEST.md) includes the English
title, GameCube-style keyboard, translated screen/building artwork, and embedded
menu responses, along with the main English text and progression fixes. It also
includes corrections for the eighteen reported V1 playtest findings, including
name/option font edges and the exposed building-transition strip. It requires
an Expansion Pak. The [package checkpoint](docs/checkpoints/V1RC3_PACKAGE.md)
identifies the local ROM, verified patch-only bundle, and explicit test limits;
this is not a completed v1 or public release.

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

1. Fix concrete playtest bugs, prioritising crashes, saves, and progression.
2. Review remaining artwork and polish English layout without changing GC intent.
3. Complete ordinary gameplay and original-hardware acceptance through playtesting.
4. Prepare the patch-only public release with provenance review.

`make complete` rebuilds the base and v1 layers from clean source checkouts and
verified local inputs, without old generated resources or translation ROMs. The
[build guide](docs/BUILDING.md) describes prerequisites, outputs, and evidence.
The V1RC1 corrections follow that artwork/title baseline through the separate
seven-stage `tools/rebuild_v1_fixes.py` recipe; `make complete` alone does not
include that correction suffix. Its verified output is recorded in the
[V1RC1 checkpoint](docs/checkpoints/V1RC1_PACKAGE.md).
The three-stage `tools/rebuild_v1rc2.py` adds the RC1 hardware follow-up and
matches the [V1RC2 package](docs/checkpoints/V1RC2_PACKAGE.md).
The two-stage `tools/rebuild_v1rc3.py` adds font/transition edge corrections and
matches the [V1RC3 package](docs/checkpoints/V1RC3_PACKAGE.md). The
[N64-inspired V2 keyboard](specs/KEYBOARD_V2.md) remains deferred until V1 is
fully complete.
The [pinned published compiler](docs/TOOLCHAIN.md) is verified by the complete
clean-source rebuild; the local development Docker image is not required.

Original project tooling is MIT licensed. Third-party material retains its own
terms; the project licence does not cover Nintendo assets or legacy work.
