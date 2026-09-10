# V1RC4 patch-documentation correction

The supplementary archive at `build/v1rc4-package-docs-01/V1RC4-patch.zip`
fixes the bundled source notes' missing local `TOOLCHAIN.md` link. It points
to the actual guide at the packaging source revision in the private repository.
The target exists at that revision. Repository access remains required for the
guide; the patcher itself is standalone and does not need network access.

The original `build/v1rc4/` handoff stays intact. Both archives reconstruct
exactly the same RC4 cartridge; this is not RC5, a save change, or new gameplay
evidence. No repeat hardware test is requested for this documentation change.

## Verification

The affected package test passes in 3.671 seconds:

```sh
PYTHONPATH=tools:tests python3 -m unittest test_v1rc4_package.PackageTests.test_complete_patch_archive_and_scoped_save_evidence -v
```

In addition to the existing complete patch reconstruction and native-evidence
binding, it checks the revision-bound guide link, all bundled Markdown link
destinations that refer to local files, and every `SHA256SUMS` entry. Existing
source notes must contain exactly the expected link before packaging; a changed
link requires review instead of silently shipping another missing target.

The committed packaging command completes successfully:

```sh
python3 tools/package_v1rc4.py --output build/v1rc4-package-docs-01
```

It executes the archived standalone patcher in a fresh temporary directory and
compares the result against the verified RC4 image. The complete source-to-ROM
rebuild and gameplay scenarios are not repeated for this package-only edit.

| Artifact | SHA-256 |
| --- | --- |
| Supplementary ZIP | `d68abe3651edbc43a73956960a7cbf726edc1967dac8d0085d1868c78c6cf324` |
| Supplementary manifest | `26eb6ade80f7f6bce547e28b1c8ab9228286b1f98099b8e00aeb3d16a969276a` |
| Unchanged ROM | `5930435f588947df35313ae9cc2ea301af9fc7e68d59a7d8e13a48741d4f3067` |
| Preserved original ZIP | `b12db3634936ceeef06bcd2047d5771c4b420146de1c9c9a07e820ef59998119` |

Packaging source is `4352c37a1105b30fbb934aaf3e6f11b2c1389591`; cartridge source
remains `b772f334db544227736d92827f0ed7347f0cce43`. Direct archive comparison
finds only three changed members: `SOURCES.md`, `manifest.json`, and
`SHA256SUMS`. The sole changed manifest field is `packaging_source_revision`.
README, tooling, licence, patch, save-compatibility statements, native evidence,
and all public-release/hardware limitations remain unchanged.

The source guide link targets a private repository, appropriate for this private
playtest. Public distribution still requires the documented provenance review,
release approval, and a decision about source visibility. The link correction
does not supply redistribution permission or complete V1 acceptance.
