"""Known compiler images and narrow compatibility with historical report approvals."""
import hashlib
import json
import os

LEGACY_IMAGE = 'sha256:281fbf9b787994c0d9454a5d8bdcaba5e23407d53f2206c75ebdc97b09d29915'
PUBLIC_IMAGE = 'ghcr.io/dragonminded/libdragon@sha256:b68e8dfd393f76ba69c1ba62da6b42dcda8b5b52eaa8fb96adc5aab7865a2d40'
IMAGES = {'public': PUBLIC_IMAGE, 'legacy': LEGACY_IMAGE}
KNOWN_IMAGES = tuple(IMAGES.values())
IMAGE_FIELDS = ('toolchain_image', 'compiler_image', 'toolchain')
TOOLCHAIN = os.environ.get('AF_TOOLCHAIN', 'public')
if TOOLCHAIN not in IMAGES:
    raise ValueError('AF_TOOLCHAIN must select public or legacy; arbitrary images are not accepted')
IMAGE = IMAGES[TOOLCHAIN]

# These exact executables match in both registered immutable images. All native
# output/source/relocation assertions remain independently enforced by builders.
EXECUTABLES = {
    'bin/mips64-elf-gcc': 'ee5475301e9bad284a7ca956c08032bd6943eb118c3913b66f4164da347b7da7',
    'bin/mips64-elf-as': '0932516ca08e61fa013c0d3d3c2ede6549d89834fd199ea0986de459f348ec77',
    'bin/mips64-elf-ld': '1895c88f17f53a1952220abae81fb76adea114430f69ae0eff6917ed2d3b15bb',
    'bin/mips64-elf-objcopy': '21033e315a4e6fac3a8c4a903a0a95642f3d83c8b6edacae03204a24ded7c751',
    'bin/mips64-elf-objdump': 'f1f9a6ea73da12b219c7055f8f8ae2ecc19faaca6241f27b85e7607568bd363c',
    'bin/mips64-elf-nm': '3af48b28348fb1cc54b74677c4de049c7ae26011610264fb94adab26e7a2ef59',
    'bin/mips64-elf-readelf': '9180757c6ef87f0ec97dcbba6a9de03d2ad888b3f4b35563a2196155291b1a1f',
    'libexec/gcc/mips64-elf/14.2.0/cc1': 'd4e0db019203db15bd4cf9ab77a72b5c5efbf8246975ce3861423ce803535c43',
    'libexec/gcc/mips64-elf/14.2.0/collect2': '6a6ceb5fad65e226b818abe5f565c7927a0b995559ecccc00805156ab5c38f95',
}


def comparison_profile(value):
    """Return a comparison copy, never a replacement for actual image provenance."""
    if isinstance(value, dict):
        result = {}
        for key, child in value.items():
            if key in IMAGE_FIELDS:
                if child not in KNOWN_IMAGES:
                    raise ValueError('Unknown compiler image in approved metadata')
                result[key] = LEGACY_IMAGE
            else:
                result[key] = comparison_profile(child)
        return result
    if isinstance(value, (list, tuple)):
        return [comparison_profile(child) for child in value]
    return value


def profile_sha256(value):
    """Historical approval fingerprint, not the hash of the actual report JSON."""
    encoded = json.dumps(comparison_profile(value), sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(encoded).hexdigest()
