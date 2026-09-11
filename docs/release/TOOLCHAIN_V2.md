# Optional V2 source-build guide

Applying the [V2 patch](README.md#apply-the-patch-offline) needs only Python 3
and the supported original Japanese N64 ROM. This guide is for reproducing the
cartridge from source, which additionally requires the private checkout, local
inputs, and pinned Docker compiler described in the
[baseline source guide](V1_SOURCE_BUILD.md).

The manifest's `cartridge_source_revision` pins the V2 builder and its retained
sources. `packaging_source_revision` identifies the offline package code and
documents. These are separate from the historical V1 baseline construction
revisions; changing package documentation does not change the ROM.

## From the prepared development checkout

With the verified original ROM and extracted GC reference already in their
standard project locations, and the preserved V1 Final ROM available:

```sh
python3 tools/keyboard_v2.py --base "build/v1-final/Animal Forest English V1 Final.z64" --output build/v2-rebuilt
```

Use a new output directory. The builder checks the exact V1 Final baseline,
native controller texture tables, source identities, editor ownership, and
allocation limits, compiles the presentation suffix in the pinned Docker
container, and verifies complete UPS reconstruction. It preserves unrelated
resources and the accepted editing/input prefix. No earlier candidate replay
or host MIPS compiler is required.

## From freshly prepared inputs

Follow the [baseline source workflow](V1_SOURCE_BUILD.md#source-workflow) to
produce V1 Final. In its isolated source directory, run the V2 suffix against
the final data-only output:

```sh
cd build/complete-rebuilt/source
python3 tools/keyboard_v2.py --base build/v1-final/animal-forest-diagnostic-text.z64 --output build/v2-rebuilt
```

The resulting `build/v2-rebuilt/` contains `Animal Forest English V2 Development.z64`,
its matching UPS, and `build.json`. The expected output hashes are in the
included README and manifest. The V1 component builds and V2 suffix have
recorded construction evidence; the composed historical chain is not claimed
as a fresh end-to-end execution or hardware certification. These commands are
reproduction instructions, not a request for playtesters to rebuild old versions.

To prepare the private offline handoff from the preserved current V2 artifact,
the committed checkout provides `python3 tools/package_v2.py`. It runs only the
bundled standalone patcher, never an emulator or historical build, and refuses
an existing output directory or changed source/artifact identities. It does
not publish anything or change the repository's visibility.
