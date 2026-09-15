# Generated browser composition checkpoint

## Delivered implementation

`tools/v3_browser_composition.py` compiles the complete pinned ABI-93 build into
a data-only browser plan. Every choice, dependency, disjoint saved-profile mask,
enable flag, HRA write, catalogue row, and count comes from the existing installed
records or offline writer. There is no browser item allowlist and no per-item
patch implementation. The catalogue contains 101 choices: 78 furniture, three
shirts, and twenty villagers.

`experimental/imports/composer.mjs` independently resolves dependencies, packs
tables, clears disabled scoring records, applies checked writes, and updates
resource and cartridge checksums. It rejects malformed/cyclic dependencies,
duplicate saved identities, overlap, bounds errors, source corruption, and
changed fields. Source and request snapshots prevent caller changes during
asynchronous verification from altering the build. Inputs remain untouched.

`experimental/imports/worker.mjs` reads original game File objects with the
existing bounded disc/recipe engine, reconstructs the pinned full image, and
applies selections. Empty selections reconstruct pinned V2 instead. Network
reads are restricted to fixed relative bundle paths, bounded, and redirect-free.
Plan, recipe, source, and reconstructed-base hashes are checked; each selected
output gets its own recorded hash. Termination cancels the worker.

No runtime code, ABI, saved format, source assets, input ROMs, existing artifacts,
V2 service, Pages workflow, or served recipe changes. The browser code is outside
`web/`. Generated recipes and plans remain ignored and unserved.

## Artifacts and evidence

- Complete source ROM SHA-256:
  `fe9b175801c5b1d7eb00b7ddf23d01d4fd164643cd01d9f2f6270d7e89f8598e`.
- Complete source report SHA-256:
  `4973f7d2705be2c280c321d29b7c51daddfa2e708b949db5c6cfd6153a5ec1c3`.
- Unserved bundle: `build/v3-browser-bundle-01/site/`.
- Generated plan SHA-256:
  `f8aeeaed3a02d1697202a3ec96929f57f4574b1b2fd7aa623fbc95f074a5af1f`.
- V3 reconstruction recipe SHA-256:
  `c38022a588edfef59564f418d4ae41ba3e15743144838b4a8b7c970607284aaa`.
- Worker results: `build/v3-browser-worker-check-01/results.json`, SHA-256
  `68230ffa5e33c5604359e605b45f5f02e7f6f1e3f6547675a5162bb7181c0207`.

Nine synthetic JS tests pass. They cover CRC/CIC calculations, dependency reasons,
selection removal/order/duplicates, packed tables and counts, ordered resource
checksums, exact all/empty results, immutable source buffers, malformed fields,
cyclic/missing dependencies, saved-bit collisions, and caller mutation during
asynchronous verification.

Three current-build Python tests pass. They verify complete menu generation,
source/report/output-directory guards, and eleven browser/offline differential
profiles: empty, all, villagers, furniture, shirts, Punchy's dependencies, Cheri's
house furnishings, a later shirt plus winter reward, sparse categories, a mixed
17-choice set, and the same mixed requests reordered and duplicated. Every full
output SHA-256, profile hash, dependency result, cartridge checksum, and restored
source matches. No exhaustive all-subsets or per-item test harness is added.

The first actual Chromium worker check passes using the original N64 file and
supplied sparse CISO. It uses a temporary loopback server with an explicit export
file allowlist and a synthetic file-input page; no route exposes games/saves.
All requests are local, body-free GETs. There are no browser errors or audio.
The server shuts down at completion. Results:

- No imports: exact V2 SHA-256
  `8bbd1955536a2a3ac9f76d6f323842f5ce25c037e1ff5fd3da9f28d6dfe20507`.
- All installed: exact complete source SHA-256 above.
- Punchy plus snow bunny: SHA-256
  `00dfbda48b1fa115c13bb0c1a027c1379365f65a0f0b0a1181657d15739bbad5`,
  matching the independent offline composer with cherry-shirt/speed-bag requirements.
- Active-worker termination, unknown identity rejection, and corrupted plan
  rejection pass without exposing an output.

## Limits and next work

This is a checked browser engine and worker, not the finished selection webpage
or an approved public import release. The user-facing search/category/all/clear
controls, dependency explanations, unsupported-content records, input/selection
invalidation, download cleanup, and layout remain. Worker termination alone is
not evidence of correct UI cancellation or object-URL cleanup.

The export reuses verified GameCube resource spans plus prepared literal changes.
Python prepares converted artwork; the worker does not yet execute those graphics
converters itself. Generated recipes include game-derived changes and remain
private artifacts, not approved public redistribution packages.

Browser reconstruction does not establish ordinary imported gameplay, catalogue
construction, appearance, interactions, saves/reloads, or original-hardware
acceptance. Existing bounded native evidence remains attached to its actual build;
no old candidate is rerun. Do not load a save into a profile missing its selected
imports, V2, or an older build missing those identities. Neither served patcher
may switch until the user tests V3 and explicitly approves it.
