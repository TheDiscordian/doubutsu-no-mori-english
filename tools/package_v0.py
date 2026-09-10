#!/usr/bin/env python3
"""Prepare a local patch-only playtest candidate, not a public release."""
import argparse
import io
import json
from pathlib import Path
import subprocess
import zipfile

from aflib import ROM_SHA256, sha256, verified_rom
from apply_translation import apply_bundle, write_new

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_SHA256 = '31c85f23c996b70bd7a4779b43f1039716a77c84806dfa5a7dd52e3780d50860'
CANDIDATE_REVISION = 'e5fbf80'


def archive_bytes(members):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(members.items()):
            if '/' in name or '\\' in name or name in ('.', '..'):
                raise ValueError('Package members must be simple filenames')
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data, compresslevel=9)
    return stream.getvalue()


def prepare(directory, source, revision):
    source = verified_rom(source)
    built = (directory/'animal-forest-halfwidth.z64').read_bytes()
    patch = (directory/'animal-forest-halfwidth.ups').read_bytes()
    report = json.loads((directory/'build.json').read_text())
    if sha256(built) != CANDIDATE_SHA256 or report.get('output_sha256') != CANDIDATE_SHA256:
        raise ValueError('Package requires the verified complete classic-letter candidate')
    manifest = {
        'format': 1, 'label': 'v0-playtest-candidate', 'public_release': False,
        'source_revision': 'Doubutsu no Mori (Japan), verified retail',
        'source_sha256': ROM_SHA256, 'output_sha256': sha256(built),
        'output_bytes': len(built), 'patch_sha256': sha256(patch),
        'cartridge_source_revision': CANDIDATE_REVISION, 'packaging_source_revision': revision,
        'emulator_memory_bytes': 4 * 1024 * 1024,
        'original_hardware_verified': False, 'human_playthrough_complete': False,
    }
    if apply_bundle(source, patch, manifest) != built:
        raise ValueError('Release patch does not reconstruct the candidate')
    members = {
        'animal-forest-english.ups': patch,
        'manifest.json': (json.dumps(manifest, indent=2, sort_keys=True)+'\n').encode(),
        'README.md': (ROOT/'docs/V0_PLAYTEST.md').read_bytes(),
        'SOURCES.md': (ROOT/'docs/SOURCES.md').read_bytes(),
        'LICENSE-tooling.txt': (ROOT/'LICENSE').read_bytes(),
        'apply_translation.py': (ROOT/'tools/apply_translation.py').read_bytes(),
        'aflib.py': (ROOT/'tools/aflib.py').read_bytes(),
    }
    members['SHA256SUMS'] = ''.join(f'{sha256(value)}  {name}\n' for name, value in sorted(members.items())).encode()
    return archive_bytes(members), manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, default=ROOT/'build/classic-letters-pilot')
    parser.add_argument('--rom', type=Path, default=ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    parser.add_argument('--output', type=Path, default=ROOT/'build/releases/v0-playtest-candidate.zip')
    args = parser.parse_args()
    revision = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()
    package, manifest = prepare(args.build, args.rom.read_bytes(), revision)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_new(args.output, package)
    print(json.dumps({'package': str(args.output), 'sha256': sha256(package), 'manifest': manifest}, indent=2))


if __name__ == '__main__':
    main()
