# Animal Forest English V1RC1 — private playtest

V1RC1 combines the base English translation, English artwork, GameCube-style
keyboard, and corrections for the twelve reported V1 playtest findings.
An **Expansion Pak is required**. The ROM is 32 MiB. This is a release candidate
for testing, not a claim of completed hardware or full-game acceptance.

## Corrections to recheck

- Press Start artwork on first boot and returning to the title.
- Letter and notice-board editing: proportional wrapping, caret placement,
  and vertical navigation, retaining the native saved capacities.
- Keyboard navigation/page sound calls and a shaded, curved GC-style background.
- Notice-board date slashes, the house Camera hint, and time shown as `11:36 am`.
- English town-tune note labels and repositioned OK.
- English letter address prompts, stock To/from defaults, and full villager
  names in the recipient list. The name correction applies across villagers,
  not only the reported Limberg example; player names and saved identities stay.
- The shop's English Your Bells label and wider inventory digits in their bubbles.

Existing English text/artwork and both Nook tutorial conversation-loop fixes are
retained. Lucky-bag decoration intentionally stays Japanese, matching English GC.
The keyboard frame uses GC textures and colours, enlarged around the native
control hints; it is not an identical replacement of the entire GC controller UI.

## Saves and controls

Back up existing saves and test with a copy. Saved formats and input capacities
remain unchanged; English letter snapshots are not a supported migration back
to an unmodified Japanese ROM. The patcher does not read or alter save files.
On EverDrive, select **FLASHRAM (128 KB / 1 Mbit)** and enable **RTC**.
The ROM retains the original `AF` cartridge ID. For OS versions using
`ED64/save_db.txt`, `AF=51` selects FlashRAM with RTC, as documented in the
[official manual](https://krikzz.com/pub/support/everdrive-64/x-series/everdrive-64-manual.pdf).

Stick/D-pad selects a key, A types, B deletes, and Start finishes. L changes case,
Z changes page, L+Z changes QWERTY/alphabetical order, and R inserts a space.
C-buttons move the text cursor; L+A applies the native character alteration.
Unsupported input characters remain disabled.

## Verification and remaining work

The seven correction stages rebuild to the same final ROM and UPS. Focused
source, pixel, relocation, memory-allocation, and patch-retention checks pass.
Pixel-editor and letter UI checks have native execution evidence. The keyboard
background's native draw returns and its frame/key geometry checks pass, but
that test's later save/guard checks are unrun after a test comparison error.
The embedded-warning drawing test also remains incomplete. Neither limitation
is claimed as passed hardware validation.

Ordinary letter opening, all changed screen appearances, keyboard audio, normal
save/restart, existing-save/return-to-title paths, travel, seasonal events, and
the full hardware playthrough remain testing work. Report crashes, loops,
save problems, incorrect text, and layout defects with reproduction steps and
the V1RC1 label. Preserve a copy of the test save when useful.

## Apply the patch

The local test ROM can be used directly. For the patch-only archive, use your
own extracted original Japanese retail ROM, not an earlier translation:

```sh
python3 apply_translation.py --rom 'Doubutsu no Mori (Japan).z64' --output 'Animal Forest English V1RC1.z64'
```

The included Python 3 patcher accepts standard N64 byte orders, verifies input,
patch, output, and boot checksums, and refuses existing output files. An ordinary
UPS patcher also works with the supported big-endian original. The manifest and
SHA256SUMS identify the exact input, output, sources, and archive contents.

Keep this playtest private. The archive contains a patch and original tooling,
not a ROM or loose game assets. Public release still requires provenance review
and release approval. The tooling licence does not license Nintendo assets or
legacy work; see SOURCES.md and LICENSE-tooling.txt.
