# Portal visitor copy and reference hashes

The website uses **Animal Crossing N64 · English Translation**, matching the
in-game title and identifying the target console. The download is named
`Animal Crossing N64 - English.z64`; only the browser filename changes, not the
ROM contents or the preserved local cartridge filename.

The prose pass removes private V1/RC history, the local-preview badge/FAQ,
save-filename advice, and the audio-status caption. The page explains the input
games, translation, privacy, download, and hardware requirements for a visitor
without prior project knowledge. Muting and no-autoplay behaviour remain intact.

The input FAQ contains six explicit MD5 entries with format labels. N64 values
are measured from the verified original in all three supported byte orders.
GameCube CISO and scrubbed ISO values are measured from the private source and
the exact sparse-ISO fixture already used successfully in browser patching.
The catalogued full-disc ISO/GCM hash is supplied by
[GameTDB's GAFE01 entry](https://www.gametdb.com/Wii/GAFE01) and corroborated by
an original [Dolphin GAFE01 report](https://bugs.dolphin-emu.org/issues/13520).
That full-disc image is not present locally or claimed as a fresh local test.
The unhelpful different-packaging paragraph is replaced by concrete reference
entries; the displayed MD5s do not change runtime SHA-256 validation.

Two focused copy/hash checks pass. `build/web-portal-copy-check-01/results.json`
records successful real CISO, ISO, and subpath downloads after the branding/app
changes, with the new filename and unchanged target hash. Cancellation, wrong
inputs, no-upload behaviour, and narrow layouts also pass in that run. A final
live-page check confirms all six reference hashes are visible at 375, 768, and
1440 pixels without overflow or browser errors. No audio is played.

The guarded `--refresh-web` path updates the running `web-portal-02` export
without rebuilding the recipe, ROM, or trailer. The patch SHA-256 stays
`b36af1b824e0e1c09ca3634429fe46b8d075a6e1a6b62b0bb07c591ff91eeaa6`; the
ROM stays `400423ea152338df763192f95c159a037453f4ddbc8711e83ef38d0a34fc8c25`.
No saved format, native code, game artwork, server visibility, or public
deployment setting changes.
