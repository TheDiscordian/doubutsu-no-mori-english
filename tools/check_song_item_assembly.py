#!/usr/bin/env python3
"""Independently assemble the complete song-title tail-call adapter."""
import os
from pathlib import Path
import subprocess
import tempfile

from aflib import sha256
from check_keyboard_assembly import IMAGE
from song_item_names import PATCH


def main():
    source = Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory(prefix='af-song-asm-') as directory:
        common = ['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
                  '-v',f'{source}:/source:ro','-v',f'{directory}:/out','-w','/out','--entrypoint']
        subprocess.run(common+['/n64_toolchain/bin/mips64-elf-as',IMAGE,'-EB','-mabi=32','-march=vr4300',
                               '-o','song.o','/source/song_item_names.s'], check=True, timeout=60)
        subprocess.run(common+['/n64_toolchain/bin/mips64-elf-objcopy',IMAGE,'-O','binary','-j','.text',
                               'song.o','song.bin'], check=True, timeout=60)
        assembled = (Path(directory)/'song.bin').read_bytes()
        if assembled != PATCH[:16] or any(PATCH[16:]):
            raise ValueError('Song-title adapter differs from independent assembly')
    print(f'Verified sixteen song-title instruction bytes: {sha256(assembled)}')


if __name__ == '__main__':
    main()
