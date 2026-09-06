#!/usr/bin/env python3
"""Disassemble verified retail code using the existing Docker N64 toolchain."""

import argparse
import os
from pathlib import Path
import subprocess

from aflib import CODE_RAM, CODE_VROM, by_vrom, verified_rom


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("build/disassembly"))
    parser.add_argument("--image", default="sha256:281fbf9b787994c0d9454a5d8bdcaba5e23407d53f2206c75ebdc97b09d29915")
    args = parser.parse_args()
    rom = verified_rom(args.rom.read_bytes())
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out/"code.bin").write_bytes(by_vrom(rom)[CODE_VROM].extract(rom))
    command = ["docker", "run", "--rm", "--network", "none", "--user", f"{os.getuid()}:{os.getgid()}",
               "-v", f"{out}:/work:ro", "-w", "/work", "--entrypoint",
               "/n64_toolchain/bin/mips64-elf-objdump", args.image,
               "-D", "-b", "binary", "-m", "mips:4300", "-EB", f"--adjust-vma={CODE_RAM}", "code.bin"]
    with (out/"code.asm").open("wb") as target:
        subprocess.run(command, stdout=target, check=True, timeout=120)
    print(out/"code.asm")


if __name__ == "__main__":
    main()
