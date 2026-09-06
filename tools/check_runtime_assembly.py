#!/usr/bin/env python3
"""Verify the embedded choice-width routine with the pinned MIPS assembler."""

import os
from pathlib import Path
import subprocess
import tempfile

from aflib import sha256
from check_keyboard_assembly import IMAGE
from english_runtime import WIDTH_CODE


def main():
    source = Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory(prefix="af-runtime-asm-") as directory:
        common = ["docker", "run", "--rm", "--network", "none", "--user",
                  f"{os.getuid()}:{os.getgid()}", "-v", f"{source}:/source:ro",
                  "-v", f"{directory}:/out", "-w", "/out", "--entrypoint"]
        subprocess.run(common+["/n64_toolchain/bin/mips64-elf-as", IMAGE,
                       "-EB", "-mabi=32", "-march=vr4300", "-o", "width.o",
                       "/source/choice_width.s"], check=True, timeout=60)
        subprocess.run(common+["/n64_toolchain/bin/mips64-elf-objcopy", IMAGE,
                       "-O", "binary", "-j", ".patch", "width.o", "width.bin"],
                       check=True, timeout=60)
        if (Path(directory)/"width.bin").read_bytes() != WIDTH_CODE:
            raise ValueError("Embedded choice-width instructions differ from assembled source")
    print(f"Verified {len(WIDTH_CODE)} choice-width instruction bytes: {sha256(WIDTH_CODE)}")


if __name__ == "__main__":
    main()
