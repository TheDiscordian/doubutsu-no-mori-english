# Portal YouTube trailer integration

## Result

The live portal at `http://127.0.0.1:8073/` uses the user's uploaded trailer,
`https://www.youtube.com/watch?v=UloFru4K4Q8`, instead of serving the MP4.
The generated site is approximately 2 MB. Public hosting remains unchanged;
the YouTube video, existing trailer file, game build, and patch are not edited.

## Behaviour

- A local poster and accessible Play button require mouse or keyboard action
  before the page creates the YouTube iframe. No initial third-party request
  or automatic page-load playback occurs.
- The privacy-enhanced frame URL uses `autoplay=1&mute=0&playsinline=1&rel=0`:
  playback is requested when the visitor activates Play, with sound enabled.
  The iframe delegates autoplay, fullscreen, encrypted-media, and picture-in-picture.
- `strict-origin-when-cross-origin` on the iframe supplies YouTube's required
  origin-only Referer despite the local server's otherwise stricter policy.
  The page and server CSP permit the exact YouTube frame origin while retaining
  same-origin parent scripts, connections, and workers. No game file data or
  input names are supplied to the frame.
- A permanent Watch on YouTube link covers script-blocked browsers and viewers
  whose settings block an embedded player. YouTube controls the external
  player's network behaviour after activation.
- The responsive player has a 200-pixel minimum height and retains the portal's
  rounded green presentation. No additional thumbnail size exports are created.

The implementation follows the official
[player parameter documentation](https://developers.google.com/youtube/player_parameters)
and [embedding/referrer guidance](https://support.google.com/youtube/answer/171780?hl=en).

## Files and preservation

`web/index.html`, `web/app.mjs`, and `web/style.css` implement the player and
fallback link. `tools/serve_portal.py` supplies matching frame permissions;
the local service is restarted and responds HTTP 200. The first immediate
request during process startup precedes the listener; the subsequent check
and browser requests succeed without further service changes.

`tools/build_portal.py` omits the MP4 from fresh site exports. Refresh verifies
the known exported copy, then moves it to
`build/web-portal-02/retired-site-trailer.mp4`, outside the served folder. The
53,909,785-byte copy remains recoverable, with SHA-256
`3d3bc78875eefe98b0b0d8ed1499a86222fc44139b8ae1697e9128d87fdaf00a`.
The original remains in `build/trailer-cut-05/`. No material is deleted.
The refreshed export receipt includes the YouTube destination and current
source hashes. The patch retains SHA-256
`b36af1b824e0e1c09ca3634429fe46b8d075a6e1a6b62b0bb07c591ff91eeaa6`.

## Verification

- Four focused copy/server checks pass: current branding/player markup,
  restrictive headers, no upload methods, and traversal/listing boundaries.
- `python3 tools/check_portal_trailer.py` passes at 375, 768, and 1440 pixels.
  It verifies same-origin body-free GETs before Play, no local MP4 request,
  mouse/Enter activation, the exact video and playback parameters, origin-only
  Referer, frame size, fallback URL, no horizontal overflow, and no page errors.
  Its frame response is deliberately substituted; this deterministic check
  does not stand in for actual playback.
- A separate silent Chromium check loads the real YouTube player. The initial
  observation catches the video before buffering, so the corrected check waits
  for a decoded frame instead of stopping at element creation. That check passes:
  `readyState=4`, `currentTime=0.003042`, `paused=false`, `muted=false`, no media
  error, and no YouTube error message. The browser closes immediately afterward.
  This verifies playback starts, not a full trailer viewing or a listening review.
- Every browser uses `--mute-audio`; no physical audio is emitted. No user
  browser session, game save, ROM, or public account setting is changed.

The broader patch-flow checker now expects a dormant Play button rather than a
local HTML video. Its already-passing game reconstruction checks are not rerun
for this unrelated player change. Browser-specific YouTube settings and future
YouTube availability remain outside the site's control.
