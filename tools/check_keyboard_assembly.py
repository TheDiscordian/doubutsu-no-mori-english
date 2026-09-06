#!/usr/bin/env python3
"""Verify the embedded cursor patch against its MIPS assembly source."""

import os
from pathlib import Path
import subprocess
import tempfile

from aflib import sha256
from keyboard import CURSOR_CODE

IMAGE = "sha256:281fbf9b787994c0d9454a5d8bdcaba5e23407d53f2206c75ebdc97b09d29915"


def main():
    source = Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory(prefix="af-keyboard-asm-") as directory:
        common = ["docker", "run", "--rm", "--network", "none", "--user",
                  f"{os.getuid()}:{os.getgid()}", "-v", f"{source}:/source:ro",
                  "-v", f"{directory}:/out", "-w", "/out", "--entrypoint"]
        subprocess.run(common+["/n64_toolchain/bin/mips64-elf-as", IMAGE,
                       "-EB", "-mabi=32", "-march=vr4300", "-o", "cursor.o",
                       "/source/keyboard_cursor.s"], check=True, timeout=60)
        subprocess.run(common+["/n64_toolchain/bin/mips64-elf-objcopy", IMAGE,
                       "-O", "binary", "-j", ".text", "cursor.o", "cursor.bin"],
                       check=True, timeout=60)
        if (Path(directory)/"cursor.bin").read_bytes() != CURSOR_CODE:
            raise ValueError("Embedded cursor instructions differ from assembled source")
    print(f"Verified {len(CURSOR_CODE)} cursor instruction bytes: {sha256(CURSOR_CODE)}")


if __name__ == "__main__":
    main()
