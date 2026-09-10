"""Inspect the pinned compiler dependency; optionally pull it if missing."""
import argparse
import json
from pathlib import Path
import subprocess

from apply_translation import write_new
from toolchain import EXECUTABLES, IMAGE, LEGACY_IMAGE, PUBLIC_IMAGE


def verify(image=IMAGE, *, pull=False):
    if image not in (PUBLIC_IMAGE, LEGACY_IMAGE):
        raise ValueError('Only registered immutable compiler images are supported')
    inspect = ['docker', 'image', 'inspect', image]
    result = subprocess.run(inspect, capture_output=True, text=True, timeout=30)
    if result.returncode and pull and image == PUBLIC_IMAGE:
        subprocess.run(['docker', 'pull', image], check=True, timeout=300)
        result = subprocess.run(inspect, capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise ValueError('Compiler image unavailable; use tools/setup_toolchain.py --pull for the public image. '+result.stderr)
    metadata = json.loads(result.stdout)[0]
    if metadata['Architecture'] != 'amd64' or metadata['Os'] != 'linux':
        raise ValueError('The verified compiler profile requires Linux amd64')
    prefix = '/n64_toolchain/'
    command = ['docker', 'run', '--rm', '--network', 'none', '--entrypoint']
    hashes = subprocess.run(command+['sha256sum', image, *(prefix+p for p in EXECUTABLES)],
                            check=True, capture_output=True, text=True, timeout=60).stdout
    actual = {}
    for line in hashes.splitlines():
        digest, name = line.split(maxsplit=1)
        if not name.startswith(prefix) or name[len(prefix):] in actual:
            raise ValueError('Changed or duplicated compiler executable inventory')
        actual[name[len(prefix):]] = digest
    if actual != EXECUTABLES:
        raise ValueError('Compiler executables differ from the verified profile')
    version = subprocess.run(command+[prefix+'bin/mips64-elf-gcc', image, '--version'],
                             check=True, capture_output=True, text=True, timeout=60).stdout.splitlines()[0]
    if version != 'mips64-elf-gcc (GCC) 14.2.0':
        raise ValueError('Unexpected compiler version')
    return {'toolchain_image': image, 'inspected_image_id': metadata['Id'],
            'repository_digests': metadata.get('RepoDigests', []),
            'platform': 'linux/amd64', 'compiler': version, 'executables': actual,
            'complete_compiler_source_rebuild': False, 'gameplay_test': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pull', action='store_true', help='Obtain the registered public image if missing')
    parser.add_argument('--output', type=Path, help='Exclusive local JSON evidence file')
    args = parser.parse_args()
    if args.output and (args.output.exists() or args.output.is_symlink()):
        parser.error('Evidence output must be a new file')
    report = verify(pull=args.pull)
    encoded = (json.dumps(report, indent=2)+'\n').encode()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        write_new(args.output, encoded)
    print(encoded.decode(), end='')


if __name__ == '__main__':
    main()
