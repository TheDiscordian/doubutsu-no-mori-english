# V2-13 combined correction and publication

## Current deliverable

V2-13 includes both the official `Animal Crossing` credits title and the English
`Museum` name in letter headers, while retaining the existing museum recipient
translation, K.K. credits performance correction, and polished N64 keyboard.
It is the target for the public Pages patcher and the local patcher at port 8073.
Experimental V3 imports are not included in either deployment.

- Local ROM: `build/v2-combined-13/Animal Forest English V2.z64`.
- ROM SHA-256: `f96395426808200dc6faaac0386aec9839ddcf3a4251eaaf98f371b8029a5e68`.
- Local original-ROM patch: `build/v2-combined-13/Animal Forest English V2.ups`.
- UPS SHA-256: `960e84f64c313b03bf353f7b5f031c12bff01ce5f3e0bcb20fdf23a5b2efacff`.
- Browser export: `build/web-portal-07/site`.
- Browser recipe SHA-256: `40c9a6217f3d79cc8e4a0a67456da3a0f841fe32e2c239df516cde28046064c2`.
- Browser download: `Animal Crossing N64 - English.z64`.

The data-only credits correction consumes the museum-header V2-12 image, not
the V2-11 image. It changes `string:04EA` to the active English GameCube credits
title from `string:077B`, removing only the decorative prefix. The general bank
grows two bytes within verified padding; every other text record and executable
resource is retained. Museum header wording comes from the supplied GAFE01-r0
`foresta.rel` data at `0000CD80`. The existing per-text source catalogue on
`v3/optional-imports`, `translations/provenance.json`, remains the single
maintained catalogue; this checkpoint does not create another translation list.

## Verification

Eight focused cartridge and publication checks pass: actual installed credits
wording, all museum correction resources retained, all unrelated resources and
strings retained, N64 checksum, original-ROM UPS reconstruction, matching build
identities, safe Pages staging, and rejection of modified publication inputs.
The CI identity check runs without original games; private cartridge checks
are explicitly skipped when the local build is absent.

The silent Chromium run at `build/web-portal-check-v2-13/` downloads the exact
V2-13 ROM using both CISO and full-size sparse ISO input. Pages-style subpath
patching also matches. Cancellation, invalid inputs, stale-download clearing,
responsive layouts, GET-only local requests, and no browser errors pass.
Eleven synthetic browser-engine checks pass with the installed system Node;
the initial invocation picked Node 18 from PATH and failed because it lacks
the required browser globals. No game or patcher change was needed.

The trailer, poster, website layout, and experimental V3 selection UI are
unchanged. Only the reviewed twelve-file website package is deployed; no ROM,
disc image, or save is published.

## Saves and remaining evidence

V2 saved formats and fossil processing/delivery code are unchanged. Compatibility
with V2-11 and V2-12 is expected in both directions without migration. Existing
builds and saves are preserved. This batch does not claim a fresh hardware
playthrough or cross-version save cycle. The museum component's previous native
name-resolution/relocation evidence is retained; its incomplete graphics-fixture
comparison is not relabelled as passed. The data-only title fix needs no replay
of the unchanged K.K. renderer or historical builds.

Stable V2 fixes belong in both patcher deployments. The publication hold applies
only to experimental V3 until the user tests and approves that version.
