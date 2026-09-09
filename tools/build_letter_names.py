#!/usr/bin/env python3
"""Compile complete letter-editor names using the existing owned-overlay builder."""
import argparse
import json
from pathlib import Path
from build_catalogue_overlay import build
import letter_names as names

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=names.ROOT/'build/letter-names-overlay')
    args = parser.parse_args()
    native = (names.ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
    module = json.loads((names.ROOT/'build/notice-seasonal-runtime/module.json').read_text())
    result = build(native, module, args.output, names)
    print(json.dumps({k: result[k] for k in ('bytes', 'symbols', 'suffix_sha256', 'relocation_sha256', 'stack_usage')}, indent=2))

if __name__ == '__main__': main()
