# N64 compiler dependency

The checked build dependency is local Docker image
`sha256:281fbf9b787994c0d9454a5d8bdcaba5e23407d53f2206c75ebdc97b09d29915`,
tagged `doom-n64:tc`. Native commands run under `/n64_toolchain/bin/`, with
network disabled and the translation source mounted read-only. No host compiler
installation or libdragon game runtime is required for the translation.

The actual executable reports GCC 14.2.0, target `mips64-elf`, and GNU Binutils
2.44, configured for `mips64vr4300`. GCC's recorded configure options include
`--with-arch=vr4300 --with-tune=vr4300 --enable-languages=c,c++ --without-headers
--enable-multilib --disable-shared --with-newlib --disable-nls`.
The container labels its base as Ubuntu 22.04. These are inspected properties,
not a claim that a rebuilt container has the identical image digest.

## Executable identity

Paths below are relative to `/n64_toolchain/`.

| Executable | SHA-256 |
| --- | --- |
| `bin/mips64-elf-gcc` | `ee5475301e9bad284a7ca956c08032bd6943eb118c3913b66f4164da347b7da7` |
| `bin/mips64-elf-as` | `0932516ca08e61fa013c0d3d3c2ede6549d89834fd199ea0986de459f348ec77` |
| `bin/mips64-elf-ld` | `1895c88f17f53a1952220abae81fb76adea114430f69ae0eff6917ed2d3b15bb` |
| `bin/mips64-elf-objcopy` | `21033e315a4e6fac3a8c4a903a0a95642f3d83c8b6edacae03204a24ded7c751` |
| `bin/mips64-elf-objdump` | `f1f9a6ea73da12b219c7055f8f8ae2ecc19faaca6241f27b85e7607568bd363c` |
| `bin/mips64-elf-nm` | `3af48b28348fb1cc54b74677c4de049c7ae26011610264fb94adab26e7a2ef59` |
| `bin/mips64-elf-readelf` | `9180757c6ef87f0ec97dcbba6a9de03d2ad888b3f4b35563a2196155291b1a1f` |
| `libexec/gcc/mips64-elf/14.2.0/cc1` | `d4e0db019203db15bd4cf9ab77a72b5c5efbf8246975ce3861423ce803535c43` |
| `libexec/gcc/mips64-elf/14.2.0/collect2` | `6a6ceb5fad65e226b818abe5f565c7927a0b995559ecccc00805156ab5c38f95` |

The actual container has no `mips64-elf/include/toolchain.version` file. Do not
infer an installed C-library version from a separate checkout's build script.
The executable hashes are a scoped identity record, not an inventory of every
host shared library or compiler support file.

## Public setup work

The pinned [libdragon build script](https://github.com/DragonMinded/libdragon/blob/5cb976aab11eb30622c33b112c120a1107eedb5e/tools/build-toolchain.sh)
and [Dockerfile](https://github.com/DragonMinded/libdragon/blob/5cb976aab11eb30622c33b112c120a1107eedb5e/Dockerfile)
are available in the prior local project and match that checkout without edits.
Their hashes are respectively
`d30640d9010dc669de21d2f9d92f5a7b10026db56bfe7e57a99b7efda4cbba00` and
`b4b935daa40ea8d1ed09e5ff740f1732396d9504e1fac25368bcc4c84096ca74`.
The script specifies GCC 14.2.0 and Binutils 2.44, matching the observed tools.
That correspondence alone does not prove the exact container's full origin.

A portable setup must pin source downloads/base dependencies, build a clean
compiler-only image, and preserve the compiler's own source/licence notices.
It must accommodate a new image identity honestly in build reports and verify
the existing native output identities. Do not publish the current development
container or assume its digest is available from a public registry. The local
image includes prior project execution history and is not a prepared release.
The translation's MIT licence does not relicense GCC, Binutils, upstream SDK
headers, legacy work, or Nintendo assets.
