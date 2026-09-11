# Patch-only release preparation

The current deliverable is the private playtest identified in
[progress](PROGRESS.md), not a public release.
The repository remains private. This document separates technical packaging
evidence from attribution, redistribution review, and gameplay acceptance.
The [provenance checkpoint](checkpoints/RELEASE_PROVENANCE_REVIEW.md) binds the
inspected source versions, archive contents, and remaining limits.

## Distribution boundaries

| Material | Current treatment |
| --- | --- |
| Japanese N64 ROM and English GC disc | User-supplied local inputs; never included in a release |
| Legacy archive, UPS, extracted assets, and bundled programs | Local research/reference inputs; not republished |
| Translation UPS | Private patch artifact; contains game-derived changes, not a rights clearance |
| Standalone Python patcher and helper | Project tooling with `LICENSE-tooling.txt`; no game files required until the user supplies the original ROM |
| Project translations and source-derived records | Tracked in the private repository; not automatically covered by the tooling-only licence statement |
| N64/GC decompilation references | Pinned sources with their own notices; preserve root-licence exclusions and dependency terms |
| Compiler and emulator | Separately obtained tools; not bundled in the patch archive |
| User saves and emulator checkpoints | Local validation inputs; never release material |

The [current RC8 archive](checkpoints/V1RC8_PACKAGE.md) has only the UPS,
manifest, README, source notes, optional toolchain/source guide, bug-report guide,
tooling licence, two Python files, and checksums. Its standalone application and
offline-document links are verified. Keep earlier artifacts intact; review the exact archive selected for
publication rather than treating all files in a build directory as distributable.

The source tree includes translation strings, native command/instruction records,
and derived layout information. A file-extension check for ROMs/images does not
establish that the tree contains no third-party material. Publishing the source
repository is a separate decision from publishing a patch.

## Attribution and input provenance

The [source notes](SOURCES.md) distinguish original project tooling, the supplied
Nintendo games, Zoinkity's legacy work, and the pinned decompilations. Legacy
utilities retain their identified authors even though those programs are not
shipped. A general licence for the supplied legacy distribution is not established
by its invitation to work on the script. No Nintendo-content redistribution
permission is inferred from the decompilation licences.

The inspected builders use legacy text to corroborate reference identity, not
as the base ROM. English dialogue/names/items come from independently bound GC
payloads or native original-translation approvals; the mail catalogue binds GC
banks directly. Preserve actual payload sources separately from matching evidence.
Item approval files have a source-specific schema: the generated edits receive
their required provenance through `native_item_names` and `item_candidates`.
A missing generic `provenance` key in those approval records is not proof that
the generated resource lacks attribution.

## Outstanding public-release decisions

- Resolve the redistribution review for game-derived material and any reused
  third-party work. Keep the actual source and uncertainty recorded; neither
  an absent licence nor a permissive tooling licence is an affirmative clearance.
- Obtain the user's public-release approval. Do not change repository visibility,
  upload a public patch, or distribute input archives as a side effect of preparation.
- Preserve the self-contained documentation included in the current package.
  Patch instructions, credits, compatibility, known limits, and the optional
  source-build guide need no private documentation link. Source compilation
  still requires access to the private checkout and separately supplied inputs;
  publishing that checkout remains a separate decision.
- Select the final checked candidate and publish only its patch package, source/
  output hashes, required memory/save type, known issues, and compatibility notes.
  A docs-only archive change does not require another gameplay pass or a new ROM.
- Preserve [human acceptance](checkpoints/V1_HUMAN_ACCEPTANCE.md) of all reported
  fixes and ordinary save/restart/reload. Keep source-identified menu findings,
  remaining artwork, untested gameplay, and scoped test failures at their actual
  status. The incomplete gyroid automation is not an outstanding ordinary-save
  gate. Do not withhold private builds for broader playtesting or claim untested
  cases have passed.

Successful compilation, archive checks, and patch application prove their own
technical results. They do not certify the full game, original hardware, saved
data round trips, or redistribution permission.
