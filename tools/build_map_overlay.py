#!/usr/bin/env python3
"""Compile the owned map display-name cache with the pinned MIPS toolchain."""
import argparse
import json
from pathlib import Path

from build_catalogue_overlay import build
import map_names as m


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, default=m.ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    parser.add_argument('--module', type=Path, default=m.ROOT/'build/notice-seasonal-runtime/module.json')
    parser.add_argument('--output', type=Path, default=m.ROOT/'build/map-names-overlay')
    args = parser.parse_args()
    print(json.dumps(build(args.rom.read_bytes(), json.loads(args.module.read_text()), args.output, c=m), indent=2))


if __name__ == '__main__': main()
