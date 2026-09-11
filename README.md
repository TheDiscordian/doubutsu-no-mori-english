# Doubutsu no Mori English 🌲

English translation project for the Japanese Nintendo 64 release of
**Doubutsu no Mori**, targeting original hardware.

This project is under development, with original-hardware playtesting and
accepted fixes. It is not a final public release. See [progress](docs/PROGRESS.md) for verified results
and remaining work, and [sources](docs/SOURCES.md) for third-party provenance.

The [current V1RC7 playtest](docs/V1RC7_PLAYTEST.md) includes the English
title, GameCube-style keyboard, translated screen/building artwork, and embedded
menu responses, along with the main English text and progression fixes. It also
includes all 23 human-reported V1 corrections and additional source-identified
menu translations. The user confirms all reported fixes and repeated ordinary
save/restart/reload cycles on hardware. [Human acceptance](docs/checkpoints/V1_HUMAN_ACCEPTANCE.md)
is recorded separately from RC7's new, not-yet-playtested labels. Save formats
remain unchanged, and an Expansion Pak is required. The
[package checkpoint](docs/checkpoints/V1RC7_PACKAGE.md) identifies the local ROM,
verified patch-only bundle, compatibility, and remaining limits.

The separate [corrected v0 playtest](docs/V0_FIXES_PLAYTEST.md) addresses
the furniture-delivery conversation loop, later letter-advice continuation,
and the native shrine's map label. Its [checkpoint](docs/checkpoints/V0_HARDWARE_BUGS.md)
records the separate ROM/patch and focused native evidence. The reported v0
defects are also human-accepted; current V1 builds retain those corrections.

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

`make complete` rebuilds the base, v1 artwork, and all current correction layers
from clean source checkouts and verified local inputs. The
[build guide](docs/BUILDING.md) describes prerequisites, outputs, and evidence.
The seven-stage `tools/rebuild_v1_fixes.py` recipe provides the V1RC1 corrections
after the artwork/title baseline. Its verified output is recorded in the
[V1RC1 checkpoint](docs/checkpoints/V1RC1_PACKAGE.md).
The three-stage `tools/rebuild_v1rc2.py` adds the RC1 hardware follow-up and
matches the [V1RC2 package](docs/checkpoints/V1RC2_PACKAGE.md).
The two-stage `tools/rebuild_v1rc3.py` adds font/transition edge corrections and
matches the [V1RC3 package](docs/checkpoints/V1RC3_PACKAGE.md).
`tools/rebuild_v1rc4.py` adds the dedicated font-memory owner and ordinary-space
marker correction; its output matches [V1RC4](docs/checkpoints/V1RC4_PACKAGE.md).
The catalogue/repayment, tune/Pak, title-warning, and gamestate-label correction
stages extend that recipe to the [current RC7](docs/checkpoints/V1RC7_PACKAGE.md).
The [current correction runner](specs/CURRENT_V1_REBUILD.md) combines those
recipes and the scene-menu translation without retained RC inputs. Its complete
execution status is recorded in [the checkpoint](docs/checkpoints/CURRENT_V1_REBUILD.md).
RC3 has a known town-loading memory defect; use the current RC7 handoff. The
[N64-inspired V2 keyboard](specs/KEYBOARD_V2.md) remains deferred until V1 is
fully complete.
The [pinned published compiler](docs/TOOLCHAIN.md) is verified by the complete
clean-source rebuild; the local development Docker image is not required.

Original project tooling is MIT licensed. Third-party material retains its own
terms; the project licence does not cover Nintendo assets or legacy work.
