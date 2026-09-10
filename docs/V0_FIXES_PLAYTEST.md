# English translation: private v0 hardware-fix build

This separate build corrects the Nook furniture-delivery conversation loop, a
related loss of the later letter-sharing advice, and the map's incorrect
"Wishing Well" label, which becomes "Shrine". The complete
English dialogue and all other v0 translation resources remain unchanged.
The original handed-off v0 is preserved separately.

## Apply and play

Apply the included UPS to your own extracted Japanese retail ROM, not an earlier
English build. The bundled patcher verifies the source, patch, complete output,
and boot checksums, and refuses to overwrite an existing output:

```sh
python3 apply_translation.py --rom 'Doubutsu no Mori (Japan).z64' --output 'Animal Forest English v0 fixes.z64'
```

The ROM is 32 MiB and the translation uses four MiB of RAM; this correction does
not add an Expansion Pak requirement or change the save format. Back up test
saves before switching builds. Use the flash cartridge's normal Doubutsu no Mori
save/RTC configuration. Do not overwrite a valued town or distribute full ROMs.

## Verified and pending

The focused native test reproduces the old conversation restart and checks the
corrected owner for all six villager personalities: complete remaining English,
one reward/handoff request, completed quest state, and the normal conversation
closure request. It also checks memory guards and restores an isolated emulator
checkpoint. The native message engine and quest handlers execute; synthetic
quest/NPC/player fixtures replace an ordinary tutorial walkthrough.

The later letter-advice check reproduces premature cleanup replacing the next
page with message zero. Both corrected long explanations and an ordinary
single-record explanation reach the normal conversation-closing request with
complete English, completed quest state, and no inventory changes.

The correction still needs ordinary tutorial replay on hardware, including
finishing the delivery conversation and returning to Nook. Normal game saving
and post-load gameplay are not established by this focused check. The initial
hardware report applies to the original v0, not this corrected build.

Japanese artwork remains on some signs, bags, buildings, and interface screens.
The English title preview is separate, and a GameCube-style keyboard is not
included. Native custom-name/catchphrase limits remain. Line-layout polish,
seasonal/travel coverage, and the full playthrough remain open. Preserve the
GameCube dialogue's intentional line/page breaks and timing when reviewing.

This is a private playtest patch, not a public release. `manifest.json` binds
the input/output hashes and source revisions; `SHA256SUMS` checks package files.
Public distribution still requires the project's provenance review. The tooling
licence does not grant rights to game assets or extracted/legacy translations;
see `SOURCES.md` and `LICENSE-tooling.txt`.
