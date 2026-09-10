#!/usr/bin/env python3
"""Apply a checksummed private playtest bundle without changing the source ROM."""
import argparse
import json
from pathlib import Path
import struct

from aflib import ROM_SHA256, apply_ups, n64_checksum, sha256, verified_rom


def apply_bundle(source, patch, manifest):
    if manifest.get('format') != 1 or manifest.get('source_sha256') != ROM_SHA256:
        raise ValueError('Unsupported translation manifest or source revision')
    source = verified_rom(source)
    if sha256(patch) != manifest.get('patch_sha256'):
        raise ValueError('Translation patch SHA-256 mismatch')
    result = apply_ups(source, patch)
    if len(result) != manifest.get('output_bytes') or sha256(result) != manifest.get('output_sha256'):
        raise ValueError('Translated ROM does not match the release manifest')
    if struct.unpack_from('>2I', result, 0x10) != n64_checksum(result):
        raise ValueError('Translated ROM has an invalid N64 boot checksum')
    return result


def write_new(path, data):
    # Exclusive creation also refuses existing files, directories, and symlinks.
    with path.open('xb') as output:
        output.write(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', required=True, type=Path, help='Extracted Japanese retail ROM')
    parser.add_argument('--output', required=True, type=Path, help='New .z64 file; never overwritten')
    parser.add_argument('--bundle', type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    try:
        manifest = json.loads((args.bundle/'manifest.json').read_text())
        result = apply_bundle(args.rom.read_bytes(), (args.bundle/'animal-forest-english.ups').read_bytes(), manifest)
        write_new(args.output, result)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f'Patch not applied: {error}\n')
    print(json.dumps({'output': str(args.output), 'bytes': len(result), 'sha256': sha256(result)}, indent=2))


if __name__ == '__main__':
    main()
