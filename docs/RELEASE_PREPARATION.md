# V2 publication preparation

The release is the **V2 browser patcher** and this source repository. The browser
produces the reviewed V2-07 N64 build, including the N64-inspired keyboard and
map town-label correction. Earlier V1 and private offline packages remain
development records, not the public download route.

## Publication controls

Use the existing **TheDiscordian/doubutsu-no-mori-english** repository, without
renaming it or introducing a separate website repo. The repository remains
private during review. The user changes its visibility when ready.

Pages is configured for GitHub Actions. The committed workflow validates the
complete website and patch data while private, with deployment skipped. Making
the repository public triggers validation and deployment automatically. The
[deployment guide](WEB_PORTAL.md) gives the expected URL and sequence. YouTube
release descriptions use that same address.

## What becomes public

Making this repository public exposes its tracked files **and Git history**.
The website's file allowlist is not a privacy boundary for repository contents.

| Material | Treatment |
| --- | --- |
| Original N64 ROM and English GC disc | Supplied by each player; never committed or hosted |
| Legacy archive, extracted working assets, and bundled programs | Ignored local research inputs; not republished |
| Browser patch recipe, manifest, and poster | Exact reviewed files committed under `web/` for Pages |
| Translation source, tools, specifications, and development records | Included in the public source repository |
| Decompilation references | Public upstream projects with their own notices and exclusions |
| User saves, emulator checkpoints, and recordings | Ignored local files; not publication material |
| Earlier offline patch archives | Preserved locally; not included in the website |
| Raw publication-audit output | Ignored under `local/`; not included in the website or repository |

Only the 12 files checked by `tools/prepare_pages.py` enter the website artifact.
The repository does not contain a full ROM, disc image, or player save as a
release asset. Keep future game inputs and test outputs ignored.

## Attribution

[Public credits](../web/SOURCE_NOTES.txt) and [research provenance](SOURCES.md)
distinguish project tooling, Nintendo content, Zoinkity's earlier work, and the
decompilation references. The supplied legacy patch is a research reference,
not the base cartridge used for this translation.

English resources come from verified GameCube payloads or recorded project
translations. The browser actually copies matching spans from the supplied GC
disc; it does not simply check ownership and apply an unrelated patch.

The MIT licence covers original project tooling, not Nintendo content or
third-party work. The decompilation projects retain their own licence exclusions.
The patch recipe and source records contain game-derived material; requiring
original games and avoiding full ROM distribution do not establish permission
to redistribute that material. No rights clearance is claimed.

## Verification and remaining testing

The reviewed output SHA-256 is
`400423ea152338df763192f95c159a037453f4ddbc8711e83ef38d0a34fc8c25`.
The [portal checkpoint](checkpoints/MAP_SUFFIX_AND_PORTAL.md) records real browser
reconstruction from supported original inputs. Packaging changes do not change
that cartridge or require replaying old builds.

Preserve [human acceptance](checkpoints/V1_HUMAN_ACCEPTANCE.md) of reported
gameplay/interface fixes and ordinary saving/reloading. Broader seasonal events,
travel, Controller Pak interactions, and V2 keyboard contexts retain their
recorded playtest limits. These are not prerequisites for the build that lets
players test them. Concrete crashes, save damage, and blocked progression take
priority when reported.

The [publication checkpoint](checkpoints/PAGES_PREPARATION.md) records the source
review and fresh website checks. Technical tests do not certify every game
scenario, original-hardware configuration, or redistribution right.
