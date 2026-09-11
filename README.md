# Doubutsu no Mori English 🌲

English translation of the Japanese Nintendo 64 release, targeting original
hardware. **V1 Final is available locally**, with a verified patch-only package.
The repository and release artifacts remain private; no public upload is made.

## V2 development

The N64-inspired keyboard is implemented in
`build/v2-keyboard-02/Animal Forest English V2 Development.z64`, with a matching
UPS alongside it. It adds grey panel shading, native N64 control artwork,
pressed-button feedback, and a left-side stick image. Accepted key positions,
font metrics, input behaviour, sounds, and saved formats are retained.

Four focused cartridge/retention checks and four texture-decoder checks pass.
Native visual verification remains incomplete: the isolated preview stops in
test setup before the new keyboard runs. V1 Final remains untouched and is the
stable baseline. See the [V2 work record](docs/checkpoints/KEYBOARD_V2.md) for
exact build hashes, test limits, and the next useful check. No public release
is authorised.

## V1 Final

- ROM: `build/v1-final/Animal Forest English V1 Final.z64`.
- Patch archive: `build/v1-final/V1-Final-patch.zip`.
- Requirements: Expansion Pak, 128-KiB FlashRAM, and RTC.
- ROM SHA-256:
  `0561182044c1526010ed77b1b9c72ac268794c2f7b615f8fa70c007f366483bf`.

The [final guide](docs/V1_FINAL.md) covers patch application, compatibility,
included changes, and known limits. The [handoff checkpoint](docs/checkpoints/V1_FINAL_PACKAGE.md)
records exact artifact/source hashes and passing final-package verification.
The archive includes offline instructions, credits, source-build notes, and a
standalone Python patcher; no private checkout is needed to apply the patch.

V1 includes proportional Latin text, English dialogue/names/items/letters,
translated menus and screen/building artwork, the English animated title, and
the GC-style keyboard. All tracked V1-01 through V1-29 fixes are implemented.
The user confirms all reported V1-01 through V1-23 and v0 corrections are fixed
and repeated ordinary saving/restarting/reloading works on hardware. Preserve
that [human acceptance](docs/checkpoints/V1_HUMAN_ACCEPTANCE.md); later source-
identified labels are not claimed as part of those playtest sessions.

RC8 saves are expected compatible with V1 Final in both directions without
migration; those particular loading directions are not independently tested.
Keep backups and use the appropriate EverDrive save filename for the renamed
ROM. RC3 retains its known existing-town loading defect and is not a fallback.

## Scope and continuing work

GameCube wording, intentional breaks, and timing guide the translation, while
native N64 structures, identities, and saved capacities remain. Lucky-bag
Japanese decoration is intentionally retained to match English GC. Neutral
artwork is not changed or exhaustively reviewed without an actual translation
defect. No further RCs, old-build retesting, or speculative neutral-image sweeps
are queued.

Broader seasonal/travel/Pak cases, individual dialogue layouts, and ordinary
appearance of both adapted stall placements remain playtest work, not completed
proof. See [progress](docs/PROGRESS.md), [tracked findings](docs/V1_PLAYTEST_BUGS.md),
and the [completion queue](docs/WORK_QUEUE.md). Concrete new crashes, save damage,
blocked progression, or text defects take priority. The
[N64-inspired V2 keyboard](specs/KEYBOARD_V2.md) is the active development work.

## Source and reproduction

The repository tracks tools, translation edits, specifications, and evidence.
ROMs, extracted assets, saves, and generated patches remain local and ignored.
[Sources](docs/SOURCES.md) records third-party provenance.

`make complete` rebuilds the base, artwork, corrections, and final diagnostic
suffix from verified local inputs using the pinned published Docker compiler.
The [build guide](docs/BUILDING.md) describes the final output and recorded
component runs. The composed 109-stage command is not claimed as a new complete
end-to-end execution; unchanged historical builds are not replayed.

Original tooling is MIT licensed; that licence does not cover Nintendo content
or legacy work. Public patch/source publication requires the separate
[redistribution review and approval](docs/RELEASE_PREPARATION.md).
