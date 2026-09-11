# YouTube upload resources

## Copy

- [Title](youtube-title.txt): `Animal Crossing N64 — English Translation Trailer`.
- [Unlisted description](youtube-description-unlisted.txt): includes the planned
  public address and a single line explaining that the patcher launches at release.
- [Release description](youtube-description-release.txt): complete release copy
  with the planned public HTTPS patcher address already filled in.
- [Optional release pinned comment](youtube-pinned-comment-release.txt): use the
  same public address. This comment is for release, not the unlisted upload.

Copy the contents of the appropriate plain-text file into YouTube Studio.
The planned public address is
`https://thediscordian.github.io/doubutsu-no-mori-english/`. It is not live;
deployment uses the existing development repository, which the user plans to
make public. Keep its name and history; no second repository is needed.
If that destination changes, replace the exact URL once in each description and
the pinned comment. The public main page supplies file hashes and instructions.

These resources do not upload a video, post a comment, publish a patch, change
repository visibility, or alter the existing trailer. The trailer remains
`build/trailer-cut-05/Animal Forest English - Trailer.mp4`.
The user's uploaded video is `https://www.youtube.com/watch?v=UloFru4K4Q8`;
the local portal embeds that upload on Play. Do not upload another copy.

## Thumbnail direction

The [current thumbnail](../../build/youtube-promo-02/Animal-Crossing-N64-thumbnail.jpg)
uses clean, flat sans-serif lettering for `N64 / IN / ENGLISH`, with straight
baselines and no cartoon extrusion or heavy shadow. It retains the green
patterned panel, curved gold divider, and title-screen composition. The revision
addresses the user's typography feedback; user approval is not assumed.

Hand over **one upload-ready thumbnail file**, not a selection of export sizes.
Keep any source masters or small inspection images internal. The current file
is 3840×2160, RGB, and 773,658 bytes; earlier exports remain preserved locally.

The thumbnail pairs the translated title screen with the short headline
`N64 / IN / ENGLISH`. Forest green, warm ivory, and the existing gold title
connect it to the game and portal. The familiar logo identifies the series;
the headline explains what is different without repeating the whole video title.
The supplied title frame is the image-generation reference. The resulting
composite is promotional artwork, not a claim of an untouched gameplay capture.

Keep the actual N64-era appearance, generous margins, and two clear visual
groups. Avoid a menu collage, tiny feature lists, a fake modern remaster,
unsupported `first ever` or `100%` claims, and text under the lower-right duration
badge. The generated artwork and its upload exports belong in ignored
`build/youtube-promo-02/`; the prompt and production record are versioned.

The built-in image-generation tool produces a 1672×941 PNG master; the 4K JPG
is an upscaled delivery export, not a claim of native 4K screenshot detail.
FFmpeg performs size/format conversion only. The [final edit prompt](thumbnail-revision-prompt.txt)
and [production record](../checkpoints/YOUTUBE_RESOURCES.md) preserve the method,
reference, hashes, and verification results.

## Research applied

YouTube's own guidance informs the choices below. These are design decisions,
not a promise of a particular click-through rate or search ranking.

- **Immediate recognition:** simple composition and readable lettering;
  accurate, succinct title with the subject first. Our choice is the real
  project's title-screen reference and three short headline words, not a list
  of features. [YouTube thumbnail and title tips](https://support.google.com/youtube/answer/12340300?hl=en).
- **Useful opening lines:** identify the English N64 translation first and put
  the patcher link directly beneath it. The full description naturally uses
  `Animal Crossing N64`, `English`, and `Doubutsu no Mori`, then explains the
  inputs and gives credit. The two versions avoid announcing availability
  before release. [YouTube description tips](https://support.google.com/youtube/answer/12948449?hl=en-GB).
- **Upload format:** YouTube recommends a 3840×2160 landscape video thumbnail,
  16:9, in JPG or PNG. Its current limits differ by uploader: 2 MB on mobile,
  50 MB on desktop. Export a high-resolution master and a compact JPG under
  2 MB so the upload does not depend on the device. Inspect the design at
  320×180 as a practical readability check, not a separate platform minimum.
  [YouTube thumbnail specifications](https://support.google.com/youtube/answer/72431?hl=en).
- **Clickable destination:** external description/comment links require the
  channel's advanced features. Check the actual link after saving in Studio;
  a correct URL alone does not establish channel eligibility.
  [YouTube external-link guidance](https://support.google.com/youtube/answer/13748639?hl=en).
- **No tag stuffing:** use three relevant hashtags; do not paste a keyword wall.
  YouTube says tags contribute little beyond common misspellings. If desired,
  use `Doubutsu no Mori`, `Dobutsu no Mori`, and `Dōbutsu no Mori` as spelling
  variants in Studio's tag field, not as repeated description paragraphs.
  [YouTube tag guidance](https://support.google.com/youtube/answer/146402?hl=en).

No channel analytics or private audience data is available for this work. A
thumbnail can be assessed for clarity now; its audience performance cannot be
measured before viewers see it. YouTube's optional testing feature measures
watch-time share, not just clicks. There is no reason to hold release for that
experiment. [YouTube thumbnail testing](https://support.google.com/youtube/answer/13861714?hl=en-on).

## Upload checklist

1. Use the existing trailer MP4, the supplied title, and the unlisted description.
   Keep visibility unlisted until release is approved.
2. Use the revised thumbnail and check its crop in Studio. Creative approval
   remains the user's decision.
3. Review YouTube's upload checks for the game's soundtrack. Attribution is
   included; it does not determine whether a claim or restriction will occur.
4. At release, use the release description and optional pinned comment. Verify
   the planned public address works and the saved link opens correctly. If a
   different address is deployed, replace the one URL in each copy first.

The thumbnail has no launch date or `out now` label, so it is suitable for both
the unlisted upload and the eventual public trailer.
