#!/usr/bin/env python3
"""Independently assemble and link the shop item-name tail-call adapter."""
import os
from pathlib import Path
import subprocess
import tempfile

from aflib import sha256
from check_keyboard_assembly import IMAGE
from shop_item_names import BODY_BYTES, IMPORTS, body


def main():
    source = Path(__file__).resolve().parents[1]/'overlays/shop'
    with tempfile.TemporaryDirectory(prefix='af-shop-item-asm-') as directory:
        common = ['docker', 'run', '--rm', '--network', 'none', '--user', f'{os.getuid()}:{os.getgid()}',
                  '-v', f'{source}:/source:ro', '-v', f'{directory}:/out', '-w', '/out', '--entrypoint']
        subprocess.run(common+['/n64_toolchain/bin/mips64-elf-as', IMAGE,
                               '-EB', '-mabi=32', '-march=vr4300', '-o', 'names.o', '/source/item_name.s'],
                       check=True, timeout=60)
        symbols = [f'--defsym={name}={address:#x}' for name, address in IMPORTS.items()]
        subprocess.run(common+['/n64_toolchain/bin/mips64-elf-ld', IMAGE, '-EB', '-Ttext=0x80000000',
                               '-e', 'af_shop_item_name', *symbols, '-o', 'names.elf', 'names.o'],
                       check=True, timeout=60)
        subprocess.run(common+['/n64_toolchain/bin/mips64-elf-objcopy', IMAGE,
                               '-O', 'binary', '-j', '.text', 'names.elf', 'names.bin'], check=True, timeout=60)
        data = (Path(directory)/'names.bin').read_bytes()
        if data[:BODY_BYTES] != body() or any(data[BODY_BYTES:]):
            raise ValueError('Shop item-name adapter differs from independent assembly')
    print(f'Verified {BODY_BYTES} shop item-name adapter bytes: {sha256(body())}')


if __name__ == '__main__':
    main()
