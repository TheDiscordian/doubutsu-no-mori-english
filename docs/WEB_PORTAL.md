# Browser patcher and GitHub Pages 🌿

The visitor-facing site is branded **Animal Crossing N64 · English Translation**.
Its copy is written for the public audience, without private build history or
local-preview explanations. Local-only hosting is an operational setting, not
part of the site's visitor instructions.

The portal is running at **http://127.0.0.1:8073/** through the enabled
`animal-forest-portal.service` user service. It remains local-only. The service
serves `build/web-portal-06/site`, not the repository or its game inputs.

The public address is
**https://thediscordian.github.io/doubutsu-no-mori-english/**, matching the YouTube
upload copy. The public development repository contains the Pages setup;
main-branch pushes validate and deploy the website. No rename or second
repository is needed.

## Use

Choose an extracted original Japanese **Doubutsu no Mori** N64 ROM and an
English **Animal Crossing (USA, Canada)** GameCube disc, ID `GAFE01`, revision 0.
Select **Build my English ROM**, then download the verified result.

- N64: `.z64`, `.v64`, and `.n64`. The patcher normalises byte order and checks
  the complete original-ROM SHA-256. Already patched ROMs are not inputs.
- GameCube: `.iso`, `.gcm`, and sparse `.ciso`. The patcher checks the disc
  identity and each required donor resource, without loading an entire ISO.
- Extract `.7z` and `.zip` first. Convert RVZ/GCZ/NKit to a full ISO with Dolphin.
- No patcher account, uploads, analytics, or persistent storage of game files.
  Original files and saves are never changed. Patcher assets remain local.
- Play loads [the YouTube trailer](https://www.youtube.com/watch?v=UloFru4K4Q8)
  in a privacy-enhanced embed, requesting sound. Nothing autoplays or contacts
  YouTube before Play. A direct Watch on YouTube link is always available.
  YouTube controls its player/network behaviour after the visitor opens it.

The browser download is **Animal Crossing N64 - English.z64**, build **V2-11**,
including the museum recipient and credits-buffer corrections, the map-suffix
fix, and the polished N64 keyboard with smooth controller shells and reordered controls.
It is an N64 ROM; this does not patch the GameCube game. The existing local
cartridge artifact keeps its filename under `build/v2-keyboard-fit-11/`.

Output SHA-256:
`8bbd1955536a2a3ac9f76d6f323842f5ce25c037e1ff5fd3da9f28d6dfe20507`.

Expansion Pak, 128-KiB FlashRAM, and RTC remain required. Saved formats are
unchanged from V1 Final and V2-10; compatibility is expected both ways without
migration. Back up saves and match the EverDrive save filename to the ROM name.
The page does not inspect or migrate saves. New hardware acceptance is not
implied by an exact patch-output checksum.

## Source and local operation

`web/` contains the complete deployable source: HTML, CSS, SVG mark, UI module,
module worker, dependency-free patch engine, public credits and licence, poster,
manifest, and reviewed patch recipe. `tools/prepare_pages.py --output build/pages-N`
stages and verifies this site without original game inputs. Use an unused output
directory. `tools/build_portal.py` creates a new recipe/export from verified
local source games and the corrected target when the game build changes.
`tools/serve_portal.py` supplies the read-only loopback server. Its unit is
tracked in `systemd/animal-forest-portal.service`; the installed copy matches.

For a fresh export, run `python3 tools/build_portal.py --output build/web-portal-N`
with an unused directory name. This reconstructs a multi-source recipe, verifies
its result against the existing target ROM, and copies only explicitly selected
website/media/source-note files. Do not serve the repository or the parent of
`build/`. Point the local unit at the new export's `site` directory when switching.

For copy/style changes, `python3 tools/build_portal.py --output build/web-portal-06
--refresh-web` updates the verified live export from `web/`, including current
download metadata. It rejects unrecorded edits to the served files and checks
the existing patch identity. It does not rebuild the ROM, regenerate the patch,
or edit the trailer. Exports contain no MP4. Source hashes and the
YouTube destination and public-credit hashes in the export receipt are refreshed.
Public credits come from `web/SOURCE_NOTES.txt`, not the longer research notes.
Server CSP changes
require restarting `animal-forest-portal.service`; the page CSP matches it.

The FAQ lists six MD5 reference checksums: three N64 byte orders, the catalogued
full GC ISO/GCM, the locally verified scrubbed ISO/GCM, and the verified CISO.
File format and size identify each entry. The full-disc value is attributed to
[GameTDB](https://www.gametdb.com/Wii/GAFE01); the others are measured directly
from the private inputs and the successful sparse-ISO browser fixture. The
patcher retains SHA-256 input/resource/output validation; displayed MD5s are
for manual file identification, not a replacement for those safeguards.

The GameCube input supplies **2,783,780 bytes** used in the output. The browser
reads and hashes `forest_1st.arc`, `forest_2nd.arc`, and Yaz0-decoded
`foresta.rel.szs`. The recipe contains 23,093 copy/literal commands and is
1,889,821 bytes compressed. This is a genuine two-input reconstruction, not a
disc-header gate in front of an otherwise independent patch.

## GitHub Pages publication

The generated **`site/` directory** is the deployable static artifact. It
contains relative URLs, a `.nojekyll` marker, a manifest, patch recipe, and
selected media. No server-side runtime or database is required. Module workers,
file reads, hashing, and patching run on the visitor's device. Hosting must use
HTTPS; localhost is supported for local development.

The existing repository is **TheDiscordian/doubutsu-no-mori-english**. Pages is
configured to use GitHub Actions, and `.github/workflows/pages.yml` handles
validation and deployment. No repository rename or separate website repository
is involved. The complete website and recipe are committed; deployment requires
no ROMs, developer computer, or extra secret token.

For game corrections, rebuild and verify the recipe from the corrected cartridge,
update `web/release/` and the staging tool's pinned hashes, and push the complete
change to `main`. Confirm **Validate and deploy website** succeeds and the live
manifest and recipe match the new build. The released trailer stays unchanged.

While private, the workflow stages and tests the website and preserves the
verified artifact, but skips deployment. A manual workflow run is available if
needed; it obeys the same visibility guard. The public artifact's manifest has
`public_release: true`; the tracked and local-preview manifests remain false.

Only the 12 explicitly allowed website files are deployed. The staging tool
rejects extra files, symlinks, a changed recipe, a changed output identity, and
an existing output directory. Never deploy `local/`, the wider `build/` tree,
source ROMs, saves, or browser-test downloads. See the
[publication review](RELEASE_PREPARATION.md) for distribution boundaries.
Requiring both games does not itself establish redistribution rights for the
remaining game-derived patch material. The released trailer is unchanged.

## Verification

- `python3 -m unittest tests.test_prepare_pages -v` checks private/public staging,
  the exact file set, input preservation, and rejection of changed patches,
  unexpected files, and symlinks. It requires no private input files.
- `python3 tools/check_portal_trailer.py` checks the live page at four widths,
  no pre-click third-party requests, mouse/keyboard activation, unmuted playback
  parameters, origin-only Referer, minimum player size, and the direct link.
  It substitutes a silent iframe response; it does not claim a YouTube playback
  test. The browser always uses `--mute-audio` to suppress physical sound.
- `python3 -m unittest tests.test_portal_copy -v` checks visitor-facing wording,
  branding, and the measured reference MD5s without rebuilding the cartridge.
- `node --test tests/web_portal.test.mjs` uses Node 22 or newer for synthetic
  parser, endian, bounds, Yaz0, gzip, donor, and checksum checks.
- `python3 tools/check_portal.py --output build/web-portal-check-N` uses the
  installed Playwright/Chromium silently against the running portal. It checks
  real CISO and sparse-ISO patch downloads, cancellation, invalid inputs,
  stale-download removal, narrow layouts, and Pages-style subpath patching.
- `python3 -m unittest tests.test_keyboard_v2_layout -v` checks the current
  cartridge, retained input code/artwork/resources, allocation, and original-ROM
  UPS reconstruction. The [fit record](checkpoints/KEYBOARD_V2_FIT.md)
  identifies the exact native-tested ROM and current browser outputs. The
  [native verification record](checkpoints/V2_PERFORMANCE_FIXES.md) records all
  credits pages against the actual drawing-buffer capacity; those resources
  remain unchanged and are not replayed for the layout change.

These checks do not replay old game builds or replace human hardware testing.
