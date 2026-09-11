# YouTube thumbnail and description resources

## Request and scope

Research thumbnail/description practices and create resources for the user's
YouTube trailer upload, kept unlisted until release. Do not modify the released
trailer, the ROM, the portal, or public visibility. No upload, comment posting,
external publication, channel setting change, or audible playback is performed.

## Deliverables

The [upload guide](../promotion/YOUTUBE.md) links the title, separate unlisted
and public-release descriptions, an optional release pinned comment, and the
thumbnail exports. Source prose and the complete generation prompt are tracked
under `docs/promotion/`. The ignored `build/youtube-promo-01/` folder contains
the image master, both upload JPGs, the small-size review image, and copies of
all four plain-text upload resources.

The public patcher address is not assigned. The unlisted description is complete
without one; the release description and pinned comment each reserve exactly
one `[PUBLIC_PATCHER_URL]`. Neither copy sends visitors to localhost or the
private source repository. The copy does not claim a first-ever translation,
perfect coverage, a modern remaster, or public availability before release.

## Research and design

The guide cites six official YouTube Help pages covering thumbnail/title design,
description writing, current size/format limits, external-link eligibility,
tags, and thumbnail testing. No private analytics or channel access is used.
The choices favour a recognisable title, a short readable headline, accurate
subject-first copy, one immediate patcher destination, and useful input and
credit details. No speculative ranking/CTR claims or keyword stuffing.

The image-generation skill's built-in tool is used with the actual translated
title frame as its reference:
`build/trailer-cut-05/review/frame-010.0.png`.
The [verbatim prompt](../promotion/thumbnail-prompt.txt) asks for the title-screen
scene with a forest-green headline panel, `N64 / IN / ENGLISH`, faithful to the
N64-era appearance. The result is AI-composited promotional art, not an unmodified
screenshot. It is inspected at its generated size and at 320×180: the headline
and game logo remain readable, and the lower-right corner
contains no essential text or subject under the prospective duration badge.
One generation is used; no iterative image-generation loop is needed.

## Artifact identities

| File in `build/youtube-promo-01/` | Dimensions | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| `thumbnail-source.png` | 1672×941 | 2234828 | `763d4e247e3ea925e139cde53fd97a2a919a3852529072a3d3711a063febcd25` |
| `Animal-Crossing-N64-thumbnail-4k.jpg` | 3840×2160 | 931134 | `4857df5446d135da17c7009736763d5ac7205798c219640623016014208aff29` |
| `Animal-Crossing-N64-thumbnail-720p.jpg` | 1280×720 | 318970 | `4573dcec27136331bd5a49d5fa29a2e92f9e8f363e38fbba26b9c025ee464dca` |
| `thumbnail-small-preview.jpg` | 320×180 | 46486 | `496a80e07d365a9c5f66fb90b7bae8f5bb1e1d45e19285c0ba9db126b0cef156` |

The generated original is copied from its image-tool output directory into the
project without deleting the original. Image output carries generated-content
metadata. Preserve the source PNG alongside its size-converted JPG exports;
the JPEGs are not represented as camera originals or native 4K game captures.

FFmpeg export from the saved master, using the project directory:

```sh
ffmpeg -hide_banner -loglevel error -nostdin -n \
  -i build/youtube-promo-01/thumbnail-source.png \
  -vf 'scale=3840:2160:flags=lanczos,setsar=1' \
  -frames:v 1 -q:v 3 -update 1 \
  build/youtube-promo-01/Animal-Crossing-N64-thumbnail-4k.jpg
```

The 720p and review versions use `1280:720` and `320:180`, respectively, and
`-q:v 2`. These are format/size conversions, not additional artwork changes.
The raw generated dimensions are approximately 16:9; the exports use exact
16:9 dimensions and square pixels. The 4K file is upscaled.

## Verification

- Both upload JPGs decode, are RGB, match their exact 16:9 dimensions, and are
  below 2,000,000 bytes; source and output hashes are recorded above.
- Full composition and 320×180 legibility are visually inspected.
- The title is 49 characters excluding its final newline. Release/unlisted
  descriptions are 1,517/1,471 characters including their final newline, below
  YouTube's 5,000-character limit. The pinned comment is 266 characters.
- URL/internal-version scan finds only the two intentional release placeholders.
  Unlisted copy has no unresolved link. All outbound prose carries the required
  author sign-off; the title is metadata, not a message body.
- The game-derived/generated image artifacts remain ignored by Git. Only
  original copy, the prompt, research links, and records are committed.
- The existing trailer retains SHA-256
  `3d3bc78875eefe98b0b0d8ed1499a86222fc44139b8ae1697e9128d87fdaf00a`.
  No ROM build, old gameplay test, video render, or sound playback occurs.

Audience performance, YouTube's final thumbnail rendering, channel feature
eligibility, and upload/music checks are not claimed as tested. Those require
the actual upload/channel; they do not block the local resource deliverables.

## User design feedback

The user likes the green text background but rejects the cartoon lettering in
`N64 / IN / ENGLISH`. Record that distinction: technical image checks are not
creative approval. Future thumbnail handoffs contain one upload-ready image,
not multiple sizes. Preserve the current artifacts; this feedback record does
not generate a replacement or claim the font is fixed.

## Typography revision

On the user's explicit instruction to implement the feedback, the built-in
image tool edits the original generated master using the
[recorded edit prompt](../promotion/thumbnail-revision-prompt.txt). The revised
headline uses flat sans-serif letters, straight baselines, and no extruded
black shadows. Visual inspection confirms the green patterned panel, curved
gold divider, and recognisable game scene remain. This is an AI image edit,
not a claim that every unaffected source pixel is identical.

The single upload deliverable is
`build/youtube-promo-02/Animal-Crossing-N64-thumbnail.jpg`: 3840×2160, RGB,
773,658 bytes, SHA-256
`ef16f1c6268db0667124f4177b06759c7a03966f7b828d74d2901add523837fc`.
Its decoder, dimensions, colour mode, and sub-2-MB check pass. The source PNG
is retained privately as `thumbnail-source.png`, SHA-256
`130a45745d51cd7fa5985a1f9f1503ea2c76301927c86d019418586b2e773089`.
Only the upload JPG is handed over; no size variants or preview exports are
generated. The source is 1672×941; FFmpeg upscales the delivery copy with the
same Lanczos conversion and quality 3 settings as the initial export.
The source/master is not a second thumbnail choice. No trailer, ROM, portal,
or upload copy changes. The revision is delivered for review, not recorded as
human-approved.

## Planned public link

The user requests a concrete estimated public address rather than missing-link
copy. Both descriptions and the pinned comment now contain
`https://thediscordian.github.io/animal-crossing-n64/`. The portal operator guide
records that destination for a separate site-only repository. GitHub's repository
lookup does not resolve `TheDiscordian/animal-crossing-n64`; no repository is
created, no Pages deployment is performed, and the URL is not claimed live.
The unlisted description has one removable launch-status line; release copy is
ready without a placeholder. If the final destination changes, the exact URL
occurs once in each upload text. The saved handoff copies are refreshed to match.
