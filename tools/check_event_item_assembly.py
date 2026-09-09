#!/usr/bin/env python3
"""Independently assemble the seven event/home item-name call sequences."""
import os
from pathlib import Path
import subprocess
import tempfile

from aflib import sha256
from check_keyboard_assembly import IMAGE
from event_item_names import BRIDGE, CALLS, call_body


def main():
    source = Path(__file__).resolve().parents[1]/'overlays/events'
    with tempfile.TemporaryDirectory(prefix='af-event-item-asm-') as directory:
        common = ['docker', 'run', '--rm', '--network', 'none', '--user', f'{os.getuid()}:{os.getgid()}',
                  '-v', f'{source}:/source:ro', '-v', f'{directory}:/out', '-w', '/out', '--entrypoint']
        subprocess.run(common+['/n64_toolchain/bin/mips64-elf-as', IMAGE,
                               '-EB', '-mabi=32', '-march=vr4300', '-o', 'names.o', '/source/item_names.s'],
                       check=True, timeout=60)
        subprocess.run(common+['/n64_toolchain/bin/mips64-elf-ld', IMAGE, '-EB', '-Ttext=0x80930000',
                               '-e', 'af_room_first_name', f'--defsym=af_item_name_bridge={BRIDGE:#x}',
                               '-o', 'names.elf', 'names.o'], check=True, timeout=60)
        subprocess.run(common+['/n64_toolchain/bin/mips64-elf-objcopy', IMAGE,
                               '-O', 'binary', '-j', '.text', 'names.elf', 'names.bin'], check=True, timeout=60)
        data = (Path(directory)/'names.bin').read_bytes()
        expected = b''.join(call_body(name) for name in CALLS)
        if data[:len(expected)] != expected or any(data[len(expected):]):
            raise ValueError('Event/home item-name calls differ from independent assembly')
    print(f'Verified {len(expected)} event/home item-name instruction bytes: {sha256(expected)}')


if __name__ == '__main__': main()
