# Existing-repository Pages preparation

## Deliverable

The source repository remains `TheDiscordian/doubutsu-no-mori-english`, private
until the user makes it public. No separate repo, rename, visibility change,
history rewrite, or public deployment occurs during preparation.

The public-facing README is rewritten around V2: features, both required games,
browser patching, hardware needs, feedback, source development, and credits.
Private V1/RC paths and handoff instructions are removed from the introduction;
their development records remain available.

The complete 12-file site is tracked under `web/`, including the reviewed
1,889,613-byte recipe, manifest, poster, and public credits. Both the source and
bug-report links point to the existing repository. YouTube description and pinned
comment files use the matching Pages URL:

https://thediscordian.github.io/doubutsu-no-mori-english/

The local preview continues at http://127.0.0.1:8073/. Its public credits are
refreshed from the tracked site notices, with matching served/source SHA-256.
No cartridge, patch contents, save, original trailer, or thumbnail is changed.

## Pages setup

GitHub's Pages API accepts `build_type: workflow` for this repository and returns
the expected URL. The Actions workflow triggers on main pushes, the repository's
private-to-public event, and manual dispatch. Validation runs while private;
deployment requires public visibility. No extra token secret or source game
input is needed on the runner.

`tools/prepare_pages.py` stages the exact approved files into a fresh directory,
checks patch/output hashes and the decoded recipe, preserves the tooling licence,
and rejects extra files or symlinks. Only a public deployment artifact marks its
manifest `public_release: true`; tracked and local-preview manifests stay false.
The source repository's visibility still exposes its development records and
history; the website allowlist does not conceal them.

## Source/history review

- All 357 commits present before these changes are scanned with official
  Gitleaks, pinned image digest
  `sha256:c00b6bd0aeb3071cbcb79009cb16a60dd9e0a7c60e2be9ab65d25e6bc8abbb7f`.
  The scan covers all refs and uses redacted output.
  A second scan through implementation commit `dedbf77` covers 358 commits and
  reports the same two reviewed findings, with no additional matches.
- Both scanner matches are reviewed SHA-256 identity constants, not credentials:
  `tools/keyboard_grid_overlay.py` at `35583d8`, and
  `tools/item_articles.py` at `5a270f3`. No credential is identified by this scan.
- The all-history filename check finds no full N64 ROM, GC disc image, save,
  input archive, or video under the checked extensions. This is a filename
  inventory, not a claim that source/translation records contain no Nintendo data.
- Commit authors use the public TheDiscordian GitHub noreply identity. The
  targeted private first-name history check finds no matches. Historical local
  tool-install paths use the same already-public account name, not credentials.
- Raw redacted findings stay in ignored `local/publication-audit-01/`. No
  genuinely private finding requiring history removal is identified in this
  bounded review. Useful technical notes stay in the source repository.

## Fresh verification

- Five Pages packaging tests pass: exact public artifact, private staging,
  unreviewed-file/symlink rejection, changed-patch rejection, and output preservation.
- Eleven JavaScript patch-engine tests pass under Node 22.
- Five visitor-copy/server tests pass, including input MD5s and no-upload serving.
- Browser integration passes at 320, 375, 768, and 1440 pixels: dormant YouTube
  loading, mouse/keyboard activation, sound parameters, origin referrer, and layout.
  The browser is physically muted; the deterministic iframe response is synthetic.
- README local links resolve. The additional 320-pixel check identifies the
  trailer/FAQ grid's automatic minimum width expanding beyond the viewport.
  Allowing those grid children to shrink fixes the overflow. The final checker
  verifies all four footer links and no horizontal overflow at all four widths,
  with the checksum FAQ both closed and expanded. Its first failed 320-pixel
  attempt is not a passing result; the earlier premature pass note is corrected
  by this fresh execution after the CSS change.
- A fresh `build/pages-review-01` artifact stages successfully without game
  inputs. Recipe SHA-256 remains
  `b36af1b824e0e1c09ca3634429fe46b8d075a6e1a6b62b0bb07c591ff91eeaa6`.
  Target ROM SHA-256 remains
  `400423ea152338df763192f95c159a037453f4ddbc8711e83ef38d0a34fc8c25`.

Private [GitHub Actions run 34638150393](https://github.com/TheDiscordian/doubutsu-no-mori-english/actions/runs/34638150393)
passes on implementation commit `dedbf77`: staging, five packaging tests, eleven
browser-engine tests, and artifact upload all succeed. The stored `github-pages`
artifact is 1,949,837 bytes. The deploy job is **skipped**, as required while
private. Repository visibility is rechecked as private, Pages remains configured
for workflows at the expected URL, and the deployment list is empty. Public
deployment remains intentionally unexecuted until the user changes visibility.

## Platform references

- [GitHub Pages custom workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
- [Workflow events, including public](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)
- [Pages configuration API](https://docs.github.com/en/rest/pages/pages)
- [Gitleaks](https://github.com/gitleaks/gitleaks)
