# Independent carried-item selections

## Current proposal

ABI 369 / save format 19:
`build/v3-carried-selection-03/build-lock.json`.

ROM SHA-256:
`297eea5aededf42081b59f50cc0b20e83b4367f2c1ec601a315297c15cf2ac9f`.
UPS SHA-256:
`dcf050ef8395ccf47dcf0e58891660352e4a67331a7ed6b7b09ab549427c0c16`.

The development catalogue has 213 selectable entries. Six carried parents own
25 states: orange paper, exercise card, knife and fork, coconut, cedar sapling,
and spirit. Ready/selected masks are `7D`; the sign-board bit stays off because
sign-board designs belong to the complete V4 Able Sisters feature.

## Shared integration

`tools/v3_carried_selection.py` binds the complete installed state directory,
source names, fixed identities, and save masks. Browser/offline composers derive
their fields from that binding. Shared mask fields have one physical owner;
options contribute disjoint bits. A single checkbox controls every quantity or
stamp state of its parent. No per-item installer or replacement art is added.

Card/cutlery bits also drive the existing event-item header. Their selections
activate the installed holiday providers without selecting a diary. Spirit
selection independently enables the quest's `af_cw_available` at `807B3BD0` and
Wisp's actual character-registry flags at `806EE0F0`. Clearing spirit selection
disables the quest and retains only the character's implemented flag. The shared
NPC registry, field creature, saved quest, and actor services use those gates.

All original resource addresses, models, textures, animations, audio, and code
are retained. Only five admission words change inside existing physical packets;
startup checksums are regenerated. No new RAM reservation or save format is used.
The existing all-paper single-sheet/four-sheet choice remains independent.

## Evidence

- `tests/test_v3_carried_selection.py` checks the complete retained physical
  resources, exact parent/state/name records, disabled sign board, mask/source
  validation, and the eleven browser/offline profiles below.
- Empty selection reproduces V2-14. Full selection, all six carried parents,
  all six with packs, pack-only, and each of the six individual parents produce
  matching browser/offline output. Selected card/cutlery headers agree with the
  saved-family mask. Wisp enables independently of diary/event selections.
- Browser validation rejects duplicate mask bits, unknown masked imports, and
  carried options without an installed selection field. Receipts retain the
  selected carried mask and explicit save warnings.
- `build/v3-carried-selection-boot-02/` passes twelve silent scenario steps on
  the same ROM hash: startup, carried/event masks, Wisp availability/allocation,
  final packet guard, and no faulted thread. The final proposal changes report
  metadata only relative to that tested cartridge; do not repeat its boot.
- `build/v3-carried-spirit-only-01/` is an actual offline export with no diary
  dependency. Its ROM hash is
  `71a57fc8e767be0beaaa6528dce67e97616cefb210b025c4ca537e8fed2bb1a5`.
- Passing unchanged source, sanitizer, save-transaction, and native component
  evidence remains attached to the existing carried specifications. This batch
  does not repeat it or relabel it as a new native gameplay test.

Ordinary carried-item gameplay, Wisp conversation, and native save/reload remain
unverified. No original-hardware result or V3 deployment is claimed. Both stable
V2 patchers and all existing user saves remain unchanged.

## Save compatibility and next work

Format 19 is unchanged, but saves require every carried family selected when
written. ABI 368 has no admitted carried families and rejects these saves.
Removing a family is not a migration. Four-sheet saves require pack mode;
format-18-or-earlier builds cannot read format 19. Keep separate V3 test saves.

The existing progress tool identifies only four golden tools plus the deferred
sign board as unfinished identities in this cartridge. Continue the golden-tool
shared behaviour/reward/acquisition paths and full golden-shovel route. Reuse
installed tree resources and effects. Acquisition, transport, combined gameplay,
and private hardware handoff remain broader V3 completion work; the identity
count alone does not establish release readiness.
