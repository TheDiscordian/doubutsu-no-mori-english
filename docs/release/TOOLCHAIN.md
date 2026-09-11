# Optional source-build guide

Applying the supplied patch needs only Python 3 and an original Japanese N64
ROM. It does not need a compiler, GameCube disc, or repository access. Follow
the [patch instructions](README.md#apply-the-patch-offline) for that workflow.

Rebuilding the translation from source additionally requires the private
source checkout, Git, Make, Python 3, `7z`, Docker, and three local inputs:

- The Japanese N64 ROM archive.
- The supplied `AFProjectDistro.zip` reference archive.
- The English `Animal Crossing (USA, Canada)` GameCube archive, GAFE01 revision 0.

None of those inputs or the source checkout is included in the patch ZIP.
The repository records the individual extracted-input identities and rejects
unsupported versions. The [source notes](SOURCES.md) include reference pins,
legacy-input hashes, and third-party attribution.

## Compiler

The pinned published Linux amd64 Docker image is:

```text
ghcr.io/dragonminded/libdragon@sha256:b68e8dfd393f76ba69c1ba62da6b42dcda8b5b52eaa8fb96adc5aab7865a2d40
```

It supplies GCC 14.2.0 and GNU Binutils 2.44 for `mips64-elf`, with commands under
`/n64_toolchain/bin/`. The translation uses this compiler, not the libdragon
game runtime. Source compilation uses a read-only source mount and disables
container networking. No host MIPS compiler or private Docker image is required.

In a source checkout, `python3 tools/setup_toolchain.py --pull` obtains the
pinned image if absent and verifies nine executable hashes and the compiler
version. `--pull` needs network access when the image is absent. The detailed
executable identities and upstream source notices are in the checkout's
`docs/TOOLCHAIN.md`; the compiler and its dependencies retain their own terms.

## Source workflow

Commands below are for a source checkout, not the extracted patch folder:

```sh
python3 tools/prepare_inputs.py --n64-archive /path/to/n64.7z --legacy-zip /path/to/AFProjectDistro.zip --gamecube-archive /path/to/gamecube.7z
python3 tools/check_references.py --bootstrap
python3 tools/setup_toolchain.py --pull
make complete V0_OUT=build/complete-rebuilt
```

Use a fresh output directory. The recipe copies the verified inputs into an
isolated source checkout, builds the base translation, adds the artwork/title,
and applies all current corrections. Final files are in
`build/complete-rebuilt/source/build/v1-final/`; the ROM is
`animal-forest-diagnostic-text.z64`.
The source guide documents a reproduction command; it does not request that
playtesters rebuild or re-test old candidates.

The 61-stage base and 28-stage artwork recipes have recorded passing builds.
The nineteen-stage correction run and final data-only diagnostic stage also
pass. The latter produces the exact final ROM/UPS hashes in the included README
and manifest. The composed 109-stage command has not had a fresh end-to-end
execution. These separate results are
not presented as one new full run or as hardware certification.

The manifest separates the cartridge build revision from the packaging
revision. Repackaging documentation does not change the ROM or saved formats.
Building or applying the patch does not grant third-party redistribution rights.
