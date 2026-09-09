# Original translations for N64-specific item names

## Source and fidelity

`translations/n64-item-names.json` contains complete original English translations
where the supplied donor record is absent, garbled, or describes a different
native object. These are not GameCube reference approvals. Each entry binds the
actual native ID, complete Japanese name, source hash, English wording, and
reason for retaining the N64 meaning.

The selected names retain unused labels for the zabuton/chest/rack, N64-specific
shirt designs, the Famicom and Disk System labels, quest letter/cloth/money,
glasses, the 1,000-Bell amount, fortune slip, town map, empty slot, and native
yellow cosmos. No numbered shirt is matched to the donor's filler furniture
records, and no accented name is flattened into unaccented text.

"Yellow cosmos" translates the entire native `きいろいコスモス` name. The native
string has no seed/bag suffix, and the corresponding English table lacks that
yellow species entry. This is original wording, not a shortened donor name or
permission to remove suffixes from the other complete GameCube seed names.
The generic native Famicom labels are not assigned individual donor game titles.
Availability and artwork stay unchanged.

## Shared implementation

`tools/native_item_names.py` validates the versioned original wording. The shared
candidate importer and sixteen-byte resource generator receive the same
approvals. Names that fit ten bytes enter the unchanged native bank; longer names
remain complete only in the wider resource. Neither storage capacity grows.
Every furniture rotation must match the complete native source.

Provenance explicitly identifies project-authored translation. Its reference ID
uses `native:item_XX:NNNN`, and its hash identifies the complete padded English
translation in this registry, not bytes from the GameCube disc. The existing
generic provenance/hash fields remain usable without inventing donor evidence.
Donor and original approvals cannot overlap.

The existing cartridge conversion and exact Japanese field equality may propagate
a placed name to its ordinary-item alias. Independent build/resource validation
infers the approved alias even when an edit removes its metadata. Source, complete
wording, provenance, rotation identity, and conversion still must agree; removing
metadata or changing a self-reported hash cannot authorise a shorter name.
Unknown original IDs and mixed original/donor metadata fail.

## Acceptance and limits

Check all source-bound originals, both capacities, every rotation/alias, retained
previous edits, malformed approvals, conflicting identities, changed provenance,
metadata removal, and complete-wording rejection in both builders. Reconstruct
the complete resource and UPS and check unchanged non-item payloads. Batch the
new names through the existing cartridge loaders without rerunning completed
letter, song, or gyroid groups. Final contextual wording, wider callers, ordinary
gameplay, save/reload, and hardware remain separate requirements.
