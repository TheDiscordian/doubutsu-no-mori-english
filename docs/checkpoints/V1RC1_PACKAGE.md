# V1RC1 package verification

The private hardware-playtest handoff is
`build/v1rc1/Animal Forest English V1RC1.z64`.
The patch-only archive is `build/v1rc1/V1RC1-patch.zip`.
Both are local ignored artifacts; no ROM, extracted asset, or save is committed.
An Expansion Pak is required. Existing artifacts and the user's saves are
unchanged. Use a backup and a separate copy of any existing save for testing.

## Identity

- ROM SHA-256: `63794bd31fe5c7c9ae786b15a41d6a80c2390c890b2edd963ace9a9e5edb8d37`.
- ROM size: 33,554,432 bytes.
- UPS SHA-256: `b0316888443f92bc2a56aa3eeec8f49a8278bf834bb8e495278ac1d2bff975bb`.
- Archive SHA-256: `9daf88f0649527c26f118508c84c6ad796bf561371d495a1a508a6d7a8dc353d`.
- Original ROM SHA-256: `d9417be056534fcc0bdff2e6cd5f1135511be7c0a4dace04a96a2649596ce908`.
- Cartridge-source revision: `d56215cc4b3afcafbfa2ec26146ace20afc7eefb`.
- Packaging-source revision: `281db13e3500cb00fb9d67b85faffce2c7ed077d`.
- Seven-stage receipt SHA-256: `c3954725bc51122bdf8236ec96f7d69b840db2988762d599b53bbbe813cce593`.

## Completed verification

The seven-stage correction recipe at `build/v1-fixes-rebuild-01` rebuilds each
changed overlay and produces the same final ROM and UPS. It follows the checked
artwork/title baseline; this is not another execution of the unchanged full
base recipe. Its `fixes.json` and `inputs.json` retain the inputs and source
inventory. The [background checkpoint](V1_KEYBOARD_BACKGROUND_FIX.md) records
the correction reconstruction and focused evidence.

The two package tests pass. Packaging validates the complete correction chain,
source/output/patch identity, ROM size, memory configuration, archive allowlist,
and member checksums. The packaged standalone Python patcher was actually run
from an isolated temporary extraction against the original source ROM. It
produced the expected output and passed the N64 boot checksum check. The local
`build/v1rc1/verification.json` records successful standalone application.

The archive contains only the patch, original tooling, checksums, manifest,
licence/provenance information, and playtest notes. It contains no ROM, save,
loose extracted asset, or user-specific absolute path. Packaging refuses to
overwrite an existing output directory.

## Scope and limits at handoff

The [playtest notes](../V1RC1_PLAYTEST.md) list corrections for findings V1-01
through V1-12. The recipient-name reader uses villager identity for all 216
villagers; Limberg and Buzz are representative tested cases, not exceptions.
Player names and saved identities are preserved. Both Nook conversation-loop
fixes remain installed. Lucky-bag decoration intentionally stays Japanese.

Focused source/ROM/patch checks pass for the correction batches. The pixel
editor and letter UI have the native evidence described in their checkpoints.
The keyboard background has partial native drawing evidence only; later guard
checks were not reached after a classified comparison error. The embedded
warning drawing test is also incomplete. Neither is represented as a complete
passed native scenario.

The existing full regression suite is running with output at
`build/v1rc1-regression.log` (execution session `47111` at this checkpoint).
The academy and academy-score setup failures were separately traced to stale
historical `build/runtime-module` source inventories before testing V1RC1.
Other reported errors are not yet classified. The full suite is not passed;
finish that execution and repair affected fixtures/checks without discarding
source guards or repeating the entire suite unnecessarily.

Ordinary screen appearance, keyboard audio, letter opening, save/restart,
existing-save and return-to-title paths, travel, events, and the hardware
playthrough remain acceptance work. The build enables that playtesting; it
does not certify hardware compatibility, complete v1, or approve public release.
Confirmed game crashes, save damage, and memory corruption require fixes.
