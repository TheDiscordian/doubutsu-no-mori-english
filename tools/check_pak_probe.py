#!/usr/bin/env python3
"""Assemble and verify the test-only read-only Controller Pak probe."""

import os
from pathlib import Path
import subprocess
import tempfile

from aflib import sha256
from check_keyboard_assembly import IMAGE
from pak_mail import PROBE_CODE


def main():
    source = Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory(prefix='af-pak-probe-') as directory:
        common = ['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
                  '-v',f'{source}:/source:ro','-v',f'{directory}:/out','-w','/out','--entrypoint']
        subprocess.run(common+['/n64_toolchain/bin/mips64-elf-as',IMAGE,'-EB','-mabi=32',
                              '-march=vr4300','-o','probe.o','/source/pak_read_probe.s'],check=True,timeout=60)
        subprocess.run(common+['/n64_toolchain/bin/mips64-elf-objcopy',IMAGE,'-O','binary',
                              '-j','.text','probe.o','probe.bin'],check=True,timeout=60)
        if (Path(directory)/'probe.bin').read_bytes() != PROBE_CODE:
            raise ValueError('Controller Pak probe differs from assembled source')
    print(f'Verified {len(PROBE_CODE)} read-only probe bytes: {sha256(PROBE_CODE)}')


if __name__ == '__main__': main()
