#!/usr/bin/env python3
"""Verify the embedded choice-width routine with the pinned MIPS assembler."""

import os
from pathlib import Path
import subprocess
import tempfile

from aflib import sha256
from check_keyboard_assembly import IMAGE
from english_runtime import ChoiceLayout, width_code


def main():
    source = Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory(prefix="af-runtime-asm-") as directory:
        common = ["docker", "run", "--rm", "--network", "none", "--user",
                  f"{os.getuid()}:{os.getgid()}", "-v", f"{source}:/source:ro",
                  "-v", f"{directory}:/out", "-w", "/out", "--entrypoint"]
        for layout in (ChoiceLayout(), ChoiceLayout(20, 32, 0x80196000, 0x80196080)):
            subprocess.run(common+["/n64_toolchain/bin/mips64-elf-as", IMAGE,
                           "-EB", "-mabi=32", "-march=vr4300", "-o", "width.o",
                           "--defsym", f"choice_rows={layout.rows}",
                           "--defsym", f"choice_stride={layout.stride}",
                           "/source/choice_width.s"], check=True, timeout=60)
            subprocess.run(common+["/n64_toolchain/bin/mips64-elf-objcopy", IMAGE,
                           "-O", "binary", "-j", ".patch", "width.o", "width.bin"],
                           check=True, timeout=60)
            code = width_code(layout)
            if (Path(directory)/"width.bin").read_bytes() != code:
                raise ValueError("Embedded choice-width instructions differ from assembled source")
            print(f"Verified {layout.capacity}-character width code ({len(code)} bytes): {sha256(code)}")


if __name__ == "__main__":
    main()
