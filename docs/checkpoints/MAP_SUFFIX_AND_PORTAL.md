# Map suffix correction and local portal

## Cartridge correction

The user identified `むら` beside the town name in the released trailer's map
shot and requested a ROM-only correction. Decoding the independent I4 bitmap
at `00AAE1C8` confirmed the exact reported lettering. It is not the dialogue
suffix or the inventory suffix, which already have separate English handling.

The current V2-07 removes only that 256-byte bitmap, following the English
GameCube map's town-name presentation. No native instructions, display lists,
vertices, other textures, saved names, allocations, or saved formats change.
Four focused checks pass, including every other DMA resource, boot checksum,
source guards, and full original-ROM UPS reconstruction. No old build is
replayed in an emulator. Original-hardware appearance of this new omission
remains a human playtest check.

- ROM: `build/v2-map-suffix-07/Animal Forest English V2.z64`.
- SHA-256: `400423ea152338df763192f95c159a037453f4ddbc8711e83ef38d0a34fc8c25`.
- UPS: `build/v2-map-suffix-07/Animal Forest English V2.ups`.
- UPS SHA-256: `4d612dc29ced2390ea954629cbdeaa7c4f274bafae058cec55d1b0ddf674de5e`.
- Saved formats: unchanged from V2-06 and V1 Final; no migration required.
- Released trailer: unchanged; source and live-site copy retain its exact hash.

## Browser portal

The implemented [portal](../WEB_PORTAL.md) reconstructs this corrected cartridge
from both supplied games entirely in the browser. The native N64 input is
whole-file hash verified after byte-order normalisation. Required GC files are
hash verified, decoded where needed, and supply actual output spans. The final
ROM hash must match before a download link exists.

The local service is enabled at `http://127.0.0.1:8073/`. The generated export
is `build/web-portal-02/site`, with recipe/build details in its manifest and
`build/web-portal-02/build.json`. No repository visibility change, Pages
activation, public patch upload, ROM distribution, or audio playback occurs.

Eleven focused JavaScript checks pass. Real Chromium downloads from CISO and
sparse ISO both match the target hash. The complete local browser run records
cancel, wrong N64/archive rejection, input-change download invalidation,
375/768/1440-pixel layouts, no script errors, and body-free local GET requests.
The Pages-style `/site/` deployment also completes a real CISO-to-ROM download
with the same target hash. Final browser results and desktop/mobile images are
in `build/web-portal-check-03/`; measured patch/download runs take 0.61–0.74
seconds on this machine with local cached inputs. This is not a browser/device
performance guarantee. Desktop and mobile images are visually reviewed.
Three local-server checks also pass: module/CSP headers, rejected upload
methods, and blocked traversal, symlink escape, and directory listing.
The initial browser driver hit CSP's string-evaluation restriction; using a
function predicate fixes the driver without weakening the website's CSP.
The initial export stopped at an incorrect licence-source filename; the fresh
complete export uses the repository's actual `LICENSE` and retains the failed
partial export separately. Neither setup issue changes game content.

The recipe uses 2,783,500 bytes from the GC resources, with 23,082 commands,
5,087,732 literal bytes, and 1,889,613 compressed bytes. The remaining literals
and media still require the recorded public-redistribution review; this design
is not a claim that game-derived material is absent or legally cleared.

## Remaining scope

User feedback on the local portal, human hardware acceptance of the new map
omission, and separately authorised public deployment. The browser patcher
does not require further historical game replay or percentage-tool work.
