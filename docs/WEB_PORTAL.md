# Local browser patcher 🌿

The visitor-facing site is branded **Animal Crossing N64 · English Translation**.
Its copy is written for the public audience, without private build history or
local-preview explanations. Local-only hosting is an operational setting, not
part of the site's visitor instructions.

The portal is running at **http://127.0.0.1:8073/** through the enabled
`animal-forest-portal.service` user service. It remains local-only. The service
serves `build/web-portal-02/site`, not the repository or its game inputs.

The planned public address is
**https://thediscordian.github.io/animal-crossing-n64/**, matching the YouTube
upload copy. This targets a separate site-only `TheDiscordian/animal-crossing-n64`
repository, not a visibility change to the private translation repository.
The destination is not created or live; publication still requires approval.

## Use

Choose an extracted original Japanese **Doubutsu no Mori** N64 ROM and an
English **Animal Crossing (USA, Canada)** GameCube disc, ID `GAFE01`, revision 0.
Select **Build my English ROM**, then download the verified result.

- N64: `.z64`, `.v64`, and `.n64`. The patcher normalises byte order and checks
  the complete original-ROM SHA-256. Already patched ROMs are not inputs.
- GameCube: `.iso`, `.gcm`, and sparse `.ciso`. The patcher checks the disc
  identity and each required donor resource, without loading an entire ISO.
- Extract `.7z` and `.zip` first. Convert RVZ/GCZ/NKit to a full ISO with Dolphin.
- No account, uploads, analytics, external font/asset service, or persistent
  storage of game files. Original files and saves are never changed.
- The trailer plays with sound when the visitor presses Play. It does not autoplay.

The browser download is **Animal Crossing N64 - English.z64**, build **V2-07**, including the
map's omitted Japanese village-suffix image and the current N64 keyboard.
It is an N64 ROM; this does not patch the GameCube game. The existing local
cartridge artifact keeps its filename under `build/v2-map-suffix-07/`.

Output SHA-256:
`400423ea152338df763192f95c159a037453f4ddbc8711e83ef38d0a34fc8c25`.

Expansion Pak, 128-KiB FlashRAM, and RTC remain required. Saved formats are
unchanged from V1 Final and V2-06; compatibility is expected both ways without
migration. Back up saves and match the EverDrive save filename to the ROM name.
The page does not inspect or migrate saves. New hardware acceptance is not
implied by an exact patch-output checksum.

## Source and local operation

`web/` contains the original static page, CSS, SVG mark, UI module, module
worker, and dependency-free patch engine. `tools/build_portal.py` creates a
fresh ignored export from verified local source games and the corrected target.
`tools/serve_portal.py` supplies the read-only loopback server. Its unit is
tracked in `systemd/animal-forest-portal.service`; the installed copy matches.

For a fresh export, run `python3 tools/build_portal.py --output build/web-portal-N`
with an unused directory name. This reconstructs a multi-source recipe, verifies
its result against the existing target ROM, and copies only explicitly selected
website/media/source-note files. Do not serve the repository or the parent of
`build/`. Point the local unit at the new export's `site` directory when switching.

For copy/style changes, `python3 tools/build_portal.py --output build/web-portal-02
--refresh-web` updates the verified live export from `web/`, including current
download metadata. It rejects unrecorded edits to the served files and checks
the existing patch identity. It does not rebuild the ROM, regenerate the patch,
or change the trailer. Source hashes in the export receipt are refreshed.

The FAQ lists six MD5 reference checksums: three N64 byte orders, the catalogued
full GC ISO/GCM, the locally verified scrubbed ISO/GCM, and the verified CISO.
File format and size identify each entry. The full-disc value is attributed to
[GameTDB](https://www.gametdb.com/Wii/GAFE01); the others are measured directly
from the private inputs and the successful sparse-ISO browser fixture. The
patcher retains SHA-256 input/resource/output validation; displayed MD5s are
for manual file identification, not a replacement for those safeguards.

The GameCube input supplies **2,783,500 bytes** used in the output. The browser
reads and hashes `forest_1st.arc`, `forest_2nd.arc`, and Yaz0-decoded
`foresta.rel.szs`. The recipe contains 23,082 copy/literal commands and is
1,889,613 bytes compressed. This is a genuine two-input reconstruction, not a
disc-header gate in front of an otherwise independent patch.

## Static hosting later

The generated **`site/` directory** is the deployable static artifact. It
contains relative URLs, a `.nojekyll` marker, a manifest, patch recipe, and
selected media. No server-side runtime or database is required. Module workers,
file reads, hashing, and patching run on the visitor's device. Hosting must use
HTTPS; localhost is supported for local development.

Keep `site/` as the deployment root or mount it below a project path. Do not
deploy the private repository, `local/`, the wider `build/` tree, source ROMs,
saves, or browser-test downloads. Public hosting needs separate approval and
the existing [redistribution review](RELEASE_PREPARATION.md). There is no active
Pages workflow and no public patch upload. Requiring both games does not by
itself establish redistribution rights for the remaining patch literals/media.

The release manifest and deployment approval must be deliberately
updated for any authorised public release. The released trailer itself is not
altered by the portal or map fix.

## Verification

- `python3 -m unittest tests.test_portal_copy -v` checks visitor-facing wording,
  branding, and the measured reference MD5s without rebuilding the cartridge.
- `node --test tests/web_portal.test.mjs` uses Node 22 or newer for synthetic
  parser, endian, bounds, Yaz0, gzip, donor, and checksum checks.
- `python3 tools/check_portal.py --output build/web-portal-check-N` uses the
  installed Playwright/Chromium silently against the running portal. It checks
  real CISO and sparse-ISO patch downloads, cancellation, invalid inputs,
  stale-download removal, narrow layouts, and Pages-style subpath patching.
- `python3 -m unittest tests.test_map_town_suffix_fix -v` checks the corrected
  cartridge, independent texture reader, complete retained resources, checksum,
  and original-input UPS.

These checks do not replay old game builds or replace human hardware testing.
