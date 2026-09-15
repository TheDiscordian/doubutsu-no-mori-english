# Animal Crossing N64 🌳

An English fan translation of **Doubutsu no Mori**, the original Nintendo 64
Animal Crossing game. Meet your neighbours, decorate your house, write letters,
and experience where the series began—with the familiar English localisation
from the GameCube release adapted to the N64 game.

**[Open the browser patcher](https://thediscordian.github.io/doubutsu-no-mori-english/)**
· **[Watch the trailer](https://www.youtube.com/watch?v=UloFru4K4Q8)**
· **[Report a bug](https://github.com/TheDiscordian/doubutsu-no-mori-english/issues)**

## What’s included

The current V2 translation includes:

- English dialogue, letters, character and item names, menus, and interface text.
- Proportional Latin lettering and text editors adapted for English.
- English title artwork and translated signs and screen graphics.
- An N64-inspired English keyboard with navigation sounds, an animated control
  stick, and pressed-button feedback.
- Fixes identified through playtesting on original N64 hardware.

This is a translation of the N64 game, not a port of all GameCube content.
N64-specific places and gameplay remain intact. Some decorative Japanese
markings are intentionally retained where the English GameCube artwork keeps
them too.

## Patch your game

Bring your own copies of both original games:

1. **Doubutsu no Mori (Japan)** for N64: an original, unpatched 16-MiB ROM in
   `.z64`, `.v64`, or `.n64` format.
2. **Animal Crossing (USA, Canada)** for GameCube: game ID `GAFE01`, revision 0,
   in `.iso`, `.gcm`, or `.ciso` format.

Open the [patcher](https://thediscordian.github.io/doubutsu-no-mori-english/),
choose both files, and download the English N64 ROM. The patcher checks the
inputs and finished result. Everything is processed on your device; your game
files are not uploaded or overwritten. The GameCube image supplies English
text and artwork but is not itself patched.

Extract `.7z` or `.zip` archives first. For RVZ, GCZ, or NKit images, convert
to ISO before patching. The patcher’s FAQ lists supported input sizes and MD5
checksums. **No ROMs or disc images are provided by this project.**

## Playing on an N64

- An **Expansion Pak** is required: 8 MiB of RAM.
- Your flash cartridge needs **FlashRAM saves (128 KiB)** and **real-time clock
  support**. Select FlashRAM if the cartridge asks for a save type.
- Back up existing saves before using a patched game.

An N64 emulator can also run the patched ROM. Hardware playtesting has verified
ordinary saving and reloading and the reported gameplay and interface fixes.
Broader player testing continues.

## Feedback and known limits

[Open an issue](https://github.com/TheDiscordian/doubutsu-no-mori-english/issues)
with what happened, what you expected, how to reproduce it, and your emulator
or flash cartridge. Include a screenshot or short clip if it helps. The patcher
can download patch details identifying your build. **Do not attach ROMs, disc
images, or personal save files to public issues.**

Seasonal events, travel and Controller Pak interactions, and individual text
layouts still benefit from player testing. See the
[current progress](docs/PROGRESS.md) and [work queue](docs/WORK_QUEUE.md) for
implementation status and the limits of recorded tests.

## Source and development

This repository contains the translation tools, runtime changes, translation
edits, specifications, test records, and the complete browser patcher.

- [Build the translation](docs/BUILDING.md): original inputs and the pinned
  Docker toolchain are required.
- [Run or deploy the website](docs/WEB_PORTAL.md): `web/` contains the site;
  the Pages workflow publishes only the verified website artifact.
- [Formats and implementation specifications](specs/).
- [Source provenance and acknowledgements](docs/SOURCES.md).
- [Per-text credits, assistant translations, and human review](docs/TEXT_PROVENANCE.md).

ROMs, disc images, saves, extracted working assets, and emulator recordings stay
outside version control. The reviewed browser patch recipe, its manifest, and
the site poster are included so GitHub Pages can deploy without original game
inputs or access to a developer’s computer.

## Credits and licence

Project by **TheDiscordian**, with AI-assisted development. Thanks to **Zoinkity**
for earlier translation work and reverse-engineering notes, and to the
**zeldaret/af** and **ACreTeam/ac-decomp** contributors for their research.
[Full credits](web/SOURCE_NOTES.txt) identify additional references and tools.

Original games, English localisation, artwork, and music are Nintendo’s work.
This is an unofficial fan translation, not affiliated with or endorsed by Nintendo.

Original project tooling uses the [MIT licence](LICENSE). That licence does not
cover Nintendo content or third-party work; the referenced projects retain
their own notices and exclusions.
