# Trailer town and interface revision

## Requested change

The user likes the opening, name entry, and notice board in cut 04, but finds
the second keyboard appearance repetitive and wants more buildings and menus.
Preserve those accepted sections and the native music. Replace repeated
keyboard/scenic material with distinct translated places and interfaces.

## Capture scope

All new footage uses the current V2-06 cartridge and disposable copies of the
existing daytime checkpoints. The English map guides normal walking routes to
buildings. No ROM, original save, host clock, audio output, or public-release
changes are part of this revision. Cut 04 remains unchanged.

## Captured material

- `build/trailer-map-01`: English town map and native resident-name selection.
- `build/trailer-nook-04`: translated Nook's Cranny sign from beside the shop.
- `build/trailer-nook-06`: ordinary entry and Nook's English greeting, with the
  English funds/Bells bubble visible inside the shop.
- `build/trailer-nook-08`: shop choices after ordinary Happy Room Academy
  registration on the disposable town copy.
- `build/trailer-catalogue-03`: held catalogue and an actual item selection
  change from reel-to-reel to tape deck, including English prices/labels.
- `build/trailer-post-route-03`: ordinary diagonal bridge crossing between
  the shop and post-office parts of the montage.
- `build/trailer-post-01`: English Post Office and Melody signs.
- `build/trailer-post-02`: Pelly's counter, the English mail bag, and service
  choices, reached by ordinary door interaction and walking.
- `build/trailer-post-04`: the English loan-payment screen, held without
  submitting a payment or modifying the wallet.

Navigation takes are setup evidence, not automatically approved footage. Shop
doors require a diagonal approach; the existing local GameCube source supplies
the relevant geometry. No native position, progression, inventory, or currency
injection is used. Catalogue page-advance automation can select an item after
the menu opens, so the selected take uses a fixed observed introduction prefix
and then holds the menu without confirming an order.

## Edit

The 66.5-second cut preserves the original title/opening, both selected K.K.
passages, Fae's complete name-entry segment, and the native notice-board flip.
Rover's completed reaction is shortened to one four-second musical phrase;
the repeated keyboard close-up is removed completely. Short exterior and
walking cuts alternate with readable shop, catalogue, and loan-menu holds.
The middle contains no promotional captions; the native English content
demonstrates the work. Only the opening identifier and closing title/credits
remain overlaid. The soundtrack and source cartridge are unchanged.

The editor uses an explicit current-cartridge footage allowlist. Its focused
checks require exactly one name-entry keyboard segment and the new building,
map, catalogue, post-office, and repayment sources. New review frames follow
the actual cut midpoints rather than the previous edit's fixed sample times.

## Finished private cut

File: `build/trailer-cut-05/Animal Forest English - Trailer.mp4`.

- SHA-256: `3d3bc78875eefe98b0b0d8ed1499a86222fc44139b8ae1697e9128d87fdaf00a`.
- 53,909,785 bytes; 66.5 seconds; 1,995 frames; 1920×1080 at 30 fps.
- H.264/yuv420p, stereo AAC, MP4 fast-start. Full video/audio decode passes.
- Seven focused production checks pass in 1.430 seconds, including the single
  keyboard segment, new scene coverage, current-ROM/name validation, audio
  isolation, and final stream format. No historical cartridge is tested.
- All four one-second timeline sheets and all 15 transition strips are visually
  inspected. Full-size frames at 35.6, 42.7, 47.8, 52.9, and 63.8 seconds receive
  separate inspection, alongside native source frames during capture.
- Final audio measures −18.06 LUFS / −1.26 dBTP. This is the unchanged native
  opening soundtrack; no physical listening audition is claimed.
- Temporary recording sinks are removed. The original input save retains
  SHA-256 `d489736e39abc7eff1c5b5085bf52e679186f2882a0247339e11603799b80b60`.
- GitHub repository visibility is verified private. No trailer, ROM, patch,
  or repository publication occurs. Cut 04 and all original saves are preserved.

The render's `edit.json`, `music.json`, `video.json`, and `review/checks.json`
record the source identities, timing, soundtrack, output, and inspection.
The revised trailer is ready for creative review. No ROM changes are part of
this batch, and no further speculative trailer revisions are queued.
