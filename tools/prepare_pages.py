"""Prepare only the reviewed website for Pages, without private game inputs."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import struct

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    'index.html', 'style.css', 'app.mjs', 'core.mjs', 'worker.mjs', 'mark.svg',
    '.nojekyll', 'SOURCE_NOTES.txt', 'LICENSE-tooling.txt', 'media/town.webp',
    'release/manifest.json', 'release/patch.afwp.gz',
)
PATCH_SHA = '5d78bca089e2589e5647074662374b2096f10960cf934e27ecc916dbc43b0081'
OUTPUT_SHA = '08aa1c4418848138803059a68de667f473f9da490d7c0866ee501c58b8d0896b'


def prepare(source, output, public=False):
    source, output = Path(source).resolve(), Path(output).resolve()
    if output.exists() or output.is_relative_to(source) or source.is_relative_to(output):
        raise ValueError('Choose a fresh output directory outside the source tree')
    files = set()
    for entry in source.rglob('*'):
        if entry.is_symlink():
            raise ValueError('Website contains a symbolic link')
        if entry.is_file():
            files.add(entry.relative_to(source).as_posix())
    if files != set(FILES):
        raise ValueError('Website must contain exactly the reviewed file list')
    manifest = json.loads((source/'release/manifest.json').read_text())
    recipe = manifest['recipe']
    patch = (source/'release/patch.afwp.gz').read_bytes()
    if (hashlib.sha256(patch).hexdigest() != PATCH_SHA or recipe['sha256'] != PATCH_SHA
            or len(patch) != recipe['size'] or manifest['output_sha256'] != OUTPUT_SHA):
        raise ValueError('Website patch or output identity differs from the reviewed release')
    decoded = gzip.decompress(patch)
    if (hashlib.sha256(decoded).hexdigest() != recipe['decoded_sha256']
            or len(decoded) != recipe['decoded_size'] or decoded[:8] != b'AFWP0001'):
        raise ValueError('Decoded recipe verification failed')
    count, literals = struct.unpack_from('<II', decoded, 8)
    if len(decoded) != 16 + 16*count + literals:
        raise ValueError('Recipe command/literal lengths differ')
    if recipe['file'] != 'patch.afwp.gz' or manifest['output_size'] != 33554432:
        raise ValueError('Unsupported release manifest')
    if (source/'LICENSE-tooling.txt').read_bytes() != (ROOT/'LICENSE').read_bytes():
        raise ValueError('Published tooling licence must match the project licence')
    output.mkdir(parents=True)
    for name in FILES:
        destination = output/name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source/name, destination)
    manifest['public_release'] = public
    (output/'release/manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return {'files': len(FILES), 'patch_sha256': PATCH_SHA, 'output_sha256': OUTPUT_SHA,
            'public_release': public}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--public', choices=('true', 'false'), default='false')
    args = parser.parse_args()
    print(json.dumps(prepare(ROOT/'web', args.output, args.public == 'true'), indent=2))


if __name__ == '__main__':
    main()
