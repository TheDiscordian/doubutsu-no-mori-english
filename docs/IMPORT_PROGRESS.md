# Importing progress

Run `python3 tools/v3_import_progress.py` for a fresh combined percentage and
category counts. `--json` includes every counted identity, its status, and its
evidence. `--base-lock PATH` measures a particular proposal; the default follows
the current proposal already recorded in `docs/PROGRESS.md`.

The percentage is completed importing integrations divided by known distinct
English GameCube additions. Each villager or item counts once, regardless of
implementation difficulty. This is a simple content-weighted approximation,
not an estimate of remaining hours or overall V3 release readiness.

The denominator comes from the existing pinned item identity worksheet and donor
roster. It covers every item category, including stationery, music, equipment,
diaries, gyroids, and fossils, not just categories with working importers. Native
counterparts, unused records, museum placeholders, player-created designs, and
duplicate room representations are excluded. Paper quantities, axe wear, exercise
card stamps, and spirit instances are not separate additions. Existing reviewed
import records also contribute supported hidden items and artwork variants of
native items. Undiscovered variants can change the denominator when identified.
No e/e+ content is included.

Completion comes from the current cartridge's checked selection catalogue,
installed shared furniture behaviour/profile records, and integrated surfaces
whose only selector restriction is acquisition. Prepared artwork or an incomplete
behaviour does not count. Acquisition, hardware verification, and broad
playtesting are separate from this importing figure. The tool does not enable
anything, run an emulator, rebuild assets, or change either web patcher.

Gyroids/fossils with no additional identities are shown explicitly, not credited
as a pile of completed imports. The identity worksheet is an approximation of
content differences, not an exhaustive comparison of every native/donor asset.

There is no progress checklist or second build pointer to maintain. The report
reads the existing sources each time and fails on mismatching build hashes.
