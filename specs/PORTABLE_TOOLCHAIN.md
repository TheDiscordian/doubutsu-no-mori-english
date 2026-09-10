# Portable compiler dependency and report compatibility

## Source

Use the pinned published libdragon image
`ghcr.io/dragonminded/libdragon@sha256:b68e8dfd393f76ba69c1ba62da6b42dcda8b5b52eaa8fb96adc5aab7865a2d40`
for Linux amd64 builds. Do not publish or reconstruct the local development
container's additional project layer. The published image's three filesystem
layers are exactly the first three layers of the local development image.
The nine compiler/linker executable hashes in [the identity record](../docs/TOOLCHAIN.md)
match in both images. The registry serves the pinned OCI index and its amd64
manifest. These observations do not claim a complete source-built compiler
reproduction or licence clearance for third-party inputs.

## Implementation contract

Provide a setup/verifier command for the known pinned image, with an explicit
pull option when it is absent. Verify actual executable hashes and record the
requested image reference, inspected image identity, and platform. Preserve all
upstream notices and keep local development payloads out of public dependencies.

Select only the two known compiler images: the published image and the retained
legacy image. New builds default to the published image; an explicit legacy
selection supports old reproducibility checks. Carry that selection through the
isolated base runner without admitting arbitrary feature/output overrides.

Every generated report must record the image actually used. Never substitute
the local development image's identity into a report produced by the published
image. ROM/resource/relocation/source hashes, symbols, buffer bounds, compiler
flags, and saved-layout assertions remain unchanged.

Some existing approvals fingerprint a complete metadata object, including its
compiler image. Allow compatibility with those historical approvals only through
a separate comparison fingerprint: recursively map any of the three existing
image-field names (`toolchain_image`, `compiler_image`, and `toolchain`)
from either of the two explicitly verified images to the legacy comparison
identity, and leave every other value untouched. Unknown image values fail.
Do not mutate the original report, rewrite stored provenance, or describe this
comparison fingerprint as the checksum of the actual JSON. Record actual JSON
hashes separately. Mixed retained/new compiler provenance is permitted only for
these two images; the native code and all other metadata still match exactly.

Apply that narrow comparison to the frozen accent/classic metadata profiles,
approved whole-cartridge report checks, and the final base/v1 packaging gates.
The apology, grid, birthday, and text-extension validators accept either explicitly verified
image while retaining all of their existing native-image assertions. Existing
legacy reports and the current measured-progress path must continue to validate.

## Verification and boundaries

Test that only the recognised metadata field changes the comparison identity,
unknown images fail, original reports remain unchanged, and changes to code,
sources, flags, symbols, or other values remain rejected. Verify both frozen
profile families and the existing candidate without recompiling unchanged native
gameplay fixtures.

Execute the complete clean-source base and v1 recipes with the published image.
Require the exact already-approved ROM and UPS identities, while retaining their
actual new report hashes and image provenance. Run the relevant counter/report
verification for the compatibility change, without presenting an unrequested
percentage. Preserve earlier builds and failed-run evidence. Do not repeat the
entire old regression suite or a hardware/playthrough matrix for unchanged code.

Successful public-image reproduction resolves the build dependency, not public
release approval, human gameplay acceptance, or third-party redistribution review.
