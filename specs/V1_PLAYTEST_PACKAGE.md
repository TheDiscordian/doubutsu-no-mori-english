# Combined artwork playtest package

Package the approved complete title/keyboard/menu cartridge as a local,
patch-only experimental playtest. This does not mark v1 complete, publish a
release, certify original hardware, or grant third-party redistribution rights.

Bind the output ROM, UPS, canonical title report, originating source revision,
original retail ROM hash, and required eight-MiB memory configuration. Reject
unknown candidates or altered reports. Use the existing verified UPS application
and deterministic archive helpers. The output remains 32 MiB and the ordinary
heap ends at `80400000`; only the title overlay uses Expansion Pak memory.

The archive contains UPS, a machine-readable manifest, concise standalone
application/playtest notes, current feature/evidence notes, source provenance,
the tooling licence, the standalone Python patcher and its one local dependency,
and checksums for all those members. No ROM, disc, save, loose extracted texture,
secret, or user-specific absolute path belongs in the archive.

The manifest distinguishes cartridge-source and packaging-source revisions.
Preserve the known limitations: incomplete decorative artwork, unverified
ordinary menus/transactions/save/restart/hardware, and the incomplete embedded
warning drawing probe. Passing native checks for other changed components do
not erase these limitations.

Verify complete reconstruction, archive member/checksum restrictions, and actual
execution of the included patcher from an isolated extraction directory. The
patcher accepts the supported original ROM byte orders, validates all hashes and
the N64 boot checksum, and refuses to overwrite any existing output or source.
Keep prior playtest packages and ROMs untouched.
