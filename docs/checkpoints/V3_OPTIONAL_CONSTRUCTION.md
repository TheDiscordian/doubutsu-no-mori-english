# Optional construction items and subset catalogue completion

## Completed scope

The local composer uses the complete ABI 62 integration cartridge and exposes
33 experimental entries: twenty villagers, ten furniture items, and three shirts.
It derives actual house/outfit dependencies, preserves fixed identities, and
retains full source storage. No served web patcher changes.

Nine static furniture rows map from RAM `80481500` to blob offset `7E500` through
the verified package descriptor. Only their enabled words change. Calculate the
package CRC before the prefix CRC that covers it. The composer rejects altered
selection catalogues and incompatible old source cartridges.

Selected catalogue additions are packed after all native rows in their existing
storage. Furniture iteration/search/completion and clothing iteration/completion
counts change together. This fixes smaller profiles' completion indicators
without losing a selected later shirt or changing any ID. All-selected output
remains the exact full cartridge; empty output remains exact V2-11. No new code
reservation or allocation is introduced.

## Current local artifact

`build/v3-optional-construction-01/animal-forest-v3-asset-loader.z64` selects
O'Hare, the detour sign, and the saw horse. O'Hare requires the blue aloha shirt
and its fixed mannequin. Cherry/red aloha and other furnishings are excluded.
This deliberately tests selections that are not a prefix of the installed lists.

- ROM SHA-256:
  `9f56c924681f66a261ff7755c20b652560724402735bcf47159252d808f63e10`.
- UPS SHA-256:
  `310768e76c3c626d346ba816eca75989f2a8f64b184fb4dc447c26a6a1cdf5a5`.
- Saved-profile SHA-256:
  `104758e16fbc274946c31776bc1c223b03ffd4d1120777094dbe41c476798fc1`.
- Build report SHA-256:
  `dabb7cbc7bacc99531a6de87687701a897bfc50ef13704be33c28b46db42fa35`.

There are 59 guarded writes. All original object/audio positions, virtual file
identities, image allocations, and source assets remain. The cartridge is 64 MiB
and requires an Expansion Pak. It is not a complete gameplay/hardware handoff.

## Verification

Risk: wrong RAM-to-ROM mapping, stale package CRC, accidentally enabled imports,
truncated subset ordering, unreachable completion flags, and save dependencies.
Scope: the focused composer suite and one combined current native run.

Seven focused checks pass in 5.041 seconds: all 33 bindings, actual dependency
derivation, order-independent selection, all/empty reconstruction, both CRCs,
write reversal, non-prefix table packing/counts, rejected tampering, and the
actual C codec's equal/superset/missing-dependency handling. Source saves remain
untouched. The historical runtime fixture rejects its old input through the
current composer; its earlier gameplay is not replayed.

`build/v3-optional-construction-native-01/` passes on its initial attempt:
122 records, 69 explicit memory assertions, and 44 native calls. Result SHA-256:
`005b1bce57e481ad8d47b1e350d1bfd755cad992c8b00840045f5c4f8d24cad7`.

Startup accepts both CRCs. The package contains exactly the selected static
rows. Native readers accept selected furnishings and the blue shirt/display,
rejecting excluded records. O'Hare's full name and all six personality candidate
counts pass. The actual relocated catalogue contains 438 furniture and 246
clothing rows with correct complete-collection indicators. Native selection
loads both selected models and scrolls to the last shirt with its complete name.
Original fallback, temporary-history restoration, complete save/profile state,
guards, checkpoint reload, and graceful shutdown pass. Audio stays disabled.

No ordinary arrival, shop payment, placed-item persistence, save/restart cycle,
or GPU/hardware appearance is claimed. These checks do not assess the separate
missing red/blue aloha room-scoring records; that concrete gap is next work,
with donor rows verified as `D4050800` / neutral colour.

## Compatibility and remaining work

Smaller profiles reject saves requiring excluded imports; they do not migrate
them. Codec acceptance does not establish ordinary cross-profile reload. Keep
backups and never load imported saves in V2.

Complete aloha scoring, remaining donor conversions, ordinary gameplay/
persistence, and unserved browser composition/UI remain required. GitHub
development-branch source is authorised. Both web patchers remain V2 until the
user tests V3 and explicitly approves a switch.
