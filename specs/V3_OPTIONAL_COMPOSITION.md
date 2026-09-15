# Optional import composition

## Scope and authority

`config/v3-import-build.json` pins the complete installed development cartridge,
its report, and its runtime ABI. `tools/v3_optional_composition.py` is the
authoritative offline selector. `tools/v3_browser_composition.py` generates the
browser's data-only selection plan from those same checked records. Neither
selector maintains another item list. A newly installed supported item therefore
needs no browser item definition, checkbox-order identity, or bespoke patch path.

The current installed development catalogue contains 101 choices: 78 furniture
items, three shirts, and twenty villagers. A shirt's mannequin is a required
representation, not another selectable choice. This catalogue describes installed
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

The user-facing selection UI, unsupported-item explanations, selection/input
change invalidation, download/object-URL lifecycle, and public packaging remain
separate implementation work. Worker cancellation tests do not establish those
UI behaviours. The test server exposes only its explicit exported file list and
synthetic file-input page, and shuts down after the check.

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
