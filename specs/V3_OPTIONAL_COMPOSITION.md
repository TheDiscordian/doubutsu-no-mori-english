# Optional import composition

## Scope and authority

`config/v3-import-build.json` pins the complete installed development cartridge,
its report, and its runtime ABI. `tools/v3_optional_composition.py` is the
authoritative offline selector. `tools/v3_browser_composition.py` generates the
browser's data-only selection plan from those same checked records. Neither
selector maintains another item list. A newly installed supported item therefore
needs no browser item definition, checkbox-order identity, or bespoke patch path.

The main locked catalogue contains 104 choices: 81 furniture items, three shirts,
and twenty villagers. The explicit held-selection proposal contains 112, adding
eight equipment parents. A shirt's mannequin and a handheld's catalogue model
are required representations, not extra selectable choices. This catalogue describes installed
development content, not completed gameplay acceptance. Select-all means the
installed catalogue, not every entry on the donor disc. Unimplemented identities
are rejected rather than given substitutes.

An empty selection returns the exact V2-11 cartridge, SHA-256
`8bbd1955536a2a3ac9f76d6f323842f5ce25c037e1ff5fd3da9f28d6dfe20507`.
A nonempty selection retains the shared import engine and compiled resources,
but enables only the chosen identities and required dependencies. Object slots,
saved identities, house layers, allocations, and audio resources do not depend
on selection order. Resource compaction is not part of composition.

The experimental browser modules live under `experimental/imports/`, outside
the deployed `web/` tree. Exports go to a fresh ignored `build/` directory and
remain unserved. Both V2 patchers, recipes, services, and the Pages allowlist
stay unchanged until the user tests V3 and explicitly approves the switch.

## Shared equipment selections

`--refresh-runtime --held-selection` prepares a complete experimental reference
only after the shared equipment, inventory, ground, acquisition, collection, and
catalogue adapters are installed. It binds the complete equipment module,
prepared models, tagged profiles, inverse metadata, and canonical profile bits.
It enables the actual installed parent bits without changing gameplay code,
artwork, catalogue contents, allocations, or saved format. This is an explicit
development step, not a playable-handoff or publication claim.

Both composition CLIs and the isolated browser check accept `--base-lock` for a
checked proposal. This does not replace the main lock. The lock must bind the
full ROM, report, and ABI, and cannot point to a selected-only result. Input
verification remains mandatory after choosing a proposal.

Equipment choices come from installed parent/representation records. Their
canonical IDs are the actual pocket parents, while their single saved-profile
bit is the established collection-display bit. The composer verifies the parent
reader module and full prepared model, sparse profile, inverse metadata, and
bit correspondence before offering a choice. A display ID cannot be requested
as furniture. Disabled choices clear both the profile bit and representation
enable word. Collection/name/price/action readers already use the parent bit.

The umbrella list retains its 32 native entries, packs selected appended models
in donor order, zeros unused slots, and updates the shared iteration/completion
count. The browser generator consumes those same checked writes. Its Equipment
category supports individual selection, select/clear visible, and select all;
default selection remains empty. Implemented representations are omitted from
the unavailable-furniture queue because their parent is the user-facing choice.

All choices reproduce the full proposal; no choices reproduce the exact pinned
translation-only cartridge. The existing format-2 codec accepts equal or larger
profiles and rejects a missing equipment bit without modifying destination state.
Saves using these choices must not be loaded in V2 or an older profile without
them. A codec check does not establish ordinary cross-build save/reload. The
inherited seasonal-copy issue still prevents promotion or a playable handoff;
both served V2 patchers stay unchanged.

## Dependency resolution

Use fixed source identities from `v3_registry.py` and the installed report.
Derive required shirts from actual villager metadata and furnishings from both
installed house layers. Normalize furniture rotations to canonical identities.
Reject missing defaults, unknown imported furnishings, and missing dependencies.
Punchy requires the cherry shirt and speed bag; Cheri requires both barrels.
Imported islanders retain their reviewed starting outfits. Shirts require their
fixed mannequin in both the saved profile and native item records.

Canonicalize duplicate/order-varied requests into sorted sets. Record explicit
selections, automatically required identities, dependency reasons, destinations,
and the complete 192-byte saved profile. Re-resolve from the requested set after
removal; do not mutate a previously expanded dependency result. Browser plans
also reject cyclic dependencies and two options owning the same saved bit.

## Checked cartridge writes

Validate the complete source ROM/report and every installed binding. Resident
changes cover the profile at blob offset `20`, villager town-eligibility bytes,
villager metadata's `present` bytes, and furniture/clothing/mannequin enable
fields. Changing saved profile bits alone does not disable ordinary item stock.

Static furniture profiles occupy canonical slots at blob offset `211000`,
resident RAM `80484000`; each slot is 80 bytes and its four-byte enable field
starts at offset four. The slot is `(item - 3000) / 4`. Only installed reviewed
enable words are writable; absent slots stay zero. The animated speed bag and
clothing mannequins retain their checked prefix rows. Validate the actual package
descriptor before resolving a resident address. Source item metadata, model
banks, artwork, callbacks, and resource allocations remain unchanged.

Pack selected appended catalogue entries after the unchanged native prefix,
retaining donor order and fixed catalogue identities. Clear unused appended
slots in their existing allocation. Update all furniture initialization/search/
completion counts and the clothing shared iteration/completion count together.
The browser generator obtains row encodings, native addresses, and count bases
from the offline composer's checked table writes, not another hard-coded layout.

Exclude unselected furniture/mannequins from HRA groups and recommendations with
the existing inert `FC000000` entry. Native grouping scans the complete metadata
table independently of placed-item enable checks. Preserve native rows, selected
properties, series definitions, names, code, and relocation. The browser plan
assigns each scoring write to the option owning its fixed runtime identity.

Every field carries its expected source value. Reject unknown bytes, overlapping
destinations, invalid sizes, and out-of-range offsets before applying changes.
Update the package CRC first, then the prefix CRC that covers that descriptor,
then the CIC 6102/7101 cartridge checksum. Checksum destinations cannot overlap
their own covered range or invalidate a preceding checksum. Apart from the
reviewed count immediates, executable instructions remain unchanged.

All-selected output must reproduce the complete pinned integration ROM. The
offline CLI produces a ROM, UPS patch, selection receipt, and matching report
under a fresh ignored output; it reconstructs the result through the patch
before writing. Browser composition produces an independent output buffer and
a receipt listing selected identities, profile and output hashes, and changes.
Neither path modifies an input cartridge or save.

## Experimental browser plan and worker

`AFV3-BROWSER-COMPOSITION-1` contains source/stable sizes and SHA-256 pins,
runtime ABI, source-report hash, generated options, dependencies, disjoint
profile masks, per-option disable writes, packed catalogue suffixes/counts,
ordered resource CRC fields, and the cartridge checksum field. It is JSON,
not executable conversion code. The bundle binds its exact size and SHA-256.

The browser core validates the entire plan, resolves requests, snapshots inputs
before asynchronous hashing, and checks every expected field even when that
option remains enabled. Only a private copy receives changes. It reports the
actual result hash; it does not pretend to have a precomputed expected hash for
every possible subset. Representative complete-ROM equality with the offline
composer supplies the independent implementation check.

The module worker uses the existing V2 disc/recipe engine for source hash checks,
cartridge byte-order normalization, bounded ISO/CISO reads, Yaz0 decoding, and
two-input reconstruction. No-import requests reconstruct pinned V2 directly;
nonempty requests reconstruct the pinned complete development cartridge, then
apply generated selection rules. Manifest/plan/recipe reads are same-origin,
bounded, redirect-free GETs. Input games remain File objects inside the browser.
Terminating the worker cancels the build; no storage or upload API is used.

`tools/v3_browser_composition.py --output build/NAME --recipes` exports modules,
the generated plan, and checked reconstruction recipes to an unserved directory.
Omitting `--recipes` exports the plan/modules for development checks only.
The bundle reuses checked GameCube resource spans and prepared literal changes.
Converted artwork embedded in those literals is prepared by the Python importer;
this is not yet execution of its graphics converters in JavaScript. Exports are
private development data, not approved redistribution artifacts.

The private page provides name/identity search, category filtering, individual
choices, select/clear visible, and select/clear all installed imports. Selections
start empty. Required outfits/furnishings remain visibly checked, with the names
of the villagers requiring them. Removing a parent re-resolves the original
requested set. Explicitly choosing an already-required item keeps it selected
when its parent is removed; clearing a category does not remove another selected
villager's requirements.

`data/review.json` is generated from a fresh checked furniture-pipeline scan.
The bundle binds its hash and size, and the page rejects overlap with installed
options. It lists unavailable 3xxx furniture with actual reasons, not a promise
that all those records are distinct new content. Installed custom/animated items
are not downgraded because the generic converter handles fewer categories.
The review queue is explicitly not a complete inventory of every donor item.

Both file fields are checked for rejected archive formats on every state change.
Changing an input or requested selection terminates active work, invalidates its
generation, revokes both download URLs, and resets save acknowledgement. Late
worker messages cannot restore stale downloads. Search/filter changes alone do
not alter a profile or cancel a build. The worker requires the exact plan hash
shown by the page, rejecting an export changed between selection and build.

Nonempty selections require acknowledgement of separate test saves and retained
profiles. The resulting ROM filename includes the output hash prefix; the JSON
profile download shares that prefix. Download URLs are revoked on replacement,
cancellation, input/selection changes, and page exit. No download starts without
a click. The page has no external embeds, media, uploads, storage, or autoplay.

The temporary verification server exposes only its exact export file allowlist
and test page, and shuts down after the check. Interface checks cover actual
downloads and invalidation, not just worker termination. The page remains an
unserved private development export, not the approved public patcher design.
Public packaging, fuller donor classification, and browser-native artwork
conversion remain separate work.

## Saves and verification

Selected imports are saved dependencies even before acquisition. The format-2
codec accepts a saved profile in an equal or larger selection and rejects missing
dependencies before modifying output state. Removing imports is not migration.
Do not load imported saves in V2 or an older build lacking those identities.
Ordinary cross-profile reload remains unverified; stable field sizes do not
establish gameplay compatibility.

Focused checks cover dependency closure, source/field corruption, overlap/bounds,
selection-order independence, exact all/empty output, packed catalogue/HRA
membership, checksums, input immutability, and current-cartridge equivalence.
Silent browser-worker checks use the supplied original games and a temporary
isolated export, not either live patcher. Runtime code does not change in browser
composition, so unchanged native evidence is retained without replaying old builds.
