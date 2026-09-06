#!/usr/bin/env python3
"""Build the bounded resident module with the existing pinned Docker toolchain."""

import argparse
import json
import os
from pathlib import Path
import subprocess

from aflib import sha256, verified_rom
from check_keyboard_assembly import IMAGE
from runtime_module import (MODULE_INIT, MODULE_RAM, MODULE_VROM, RESERVATION,
                            audit_watchdog_references, watchdog_bytes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("build/runtime-module"))
    args = parser.parse_args()
    rom = verified_rom(args.rom.read_bytes())
    audit = audit_watchdog_references(rom)
    out, source = args.output.resolve(), Path(__file__).resolve().parents[1]/"runtime"
    out.mkdir(parents=True, exist_ok=True)
    (out/"watchdog.bin").write_bytes(watchdog_bytes(rom))
    common = ["docker", "run", "--rm", "--network", "none", "--user", f"{os.getuid()}:{os.getgid()}",
              "-v", f"{source}:/source:ro", "-v", f"{out}:/out", "-w", "/out", "--entrypoint"]
    def run(tool, *arguments):
        result = subprocess.run(common+["/n64_toolchain/bin/mips64-elf-"+tool, IMAGE, *arguments],
                                capture_output=True, text=True, timeout=60)
        if result.returncode:
            raise RuntimeError(f"Runtime {tool} failed ({result.returncode}):\n{result.stdout}{result.stderr}")
        return result.stdout
    compiler = run("gcc", "--version").splitlines()[0]
    c_objects = []
    for path in sorted(source.glob("*.c")):
        name = path.stem+".o"
        run("gcc", "-c", "-Os", "-EB", "-mabi=32", "-march=vr4300", "-mfix4300", "-G0",
            "-mno-abicalls", "-fno-pic", "-ffreestanding", "-fno-builtin", "-fno-common",
            "-fno-stack-protector", "-ffunction-sections", "-fdata-sections", "-Wall", "-Wextra", "-Werror",
            "-I/source", "/source/"+path.name, "-o", name)
        c_objects.append(name)
    for name in ("header", "watchdog", "bootstrap"):
        run("as", "-EB", "-mabi=32", "-march=vr4300", "-I", "/out", "-o", name+".o", "/source/"+name+".s")
    run("ld", "-EB", "-T", "/source/module.ld", "-Map=module.map", "-o", "module.elf", "header.o", "watchdog.o", *c_objects)
    run("objcopy", "-O", "binary", "module.elf", "module.bin")
    run("objcopy", "-O", "binary", "-j", ".bootstrap", "bootstrap.o", "bootstrap.bin")
    symbols = {}
    for line in run("nm", "--defined-only", "module.elf").splitlines():
        parts = line.split()
        if len(parts) == 3:
            symbols[parts[2]] = int(parts[0], 16)
    if symbols.get("af_runtime_init") != MODULE_INIT or symbols.get("__module_start") != MODULE_RAM:
        raise ValueError("Runtime module link addresses do not match the bootstrap")
    binary = (out/"module.bin").read_bytes()
    if len(binary) > RESERVATION-16 or symbols["__module_end"] > MODULE_RAM+RESERVATION-16:
        raise ValueError("Runtime module exceeds reserved RAM")
    binary = binary.ljust(RESERVATION, b"\0")
    (out/"module.bin").write_bytes(binary)
    (out/"module.asm").write_text(run("objdump", "-d", "module.elf"))
    (out/"bootstrap.asm").write_text(run("objdump", "-d", "-j", ".bootstrap", "bootstrap.o"))
    report = {"source_sha256": sha256(rom), "module_sha256": sha256(binary),
              "bootstrap_sha256": sha256((out/"bootstrap.bin").read_bytes()),
              "ram": f"{MODULE_RAM:08X}", "vrom": f"{MODULE_VROM:08X}", "reserved_bytes": RESERVATION,
              "linked_bytes": symbols["__module_end"]-MODULE_RAM, "compiler": compiler, "toolchain_image": IMAGE,
              "runtime_sources": {p.name: sha256(p.read_bytes()) for p in sorted(source.iterdir()) if p.is_file()},
              "symbols": {name: f"{value:08X}" for name, value in sorted(symbols.items())}, "audit": audit,
              "status": "experimental; boot, heap, gameplay, and hardware validation required"}
    (out/"module.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
