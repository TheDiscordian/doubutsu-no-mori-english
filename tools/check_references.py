#!/usr/bin/env python3
"""Validate reference pins; optionally obtain the documented public sources."""

import argparse
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
GC_PIN = "09ca8e8b5b24e6ab44047ee980cf0088ad7ecb4c"
AF_PIN = "4ddba04604ee7b4c4cfc0b64f8ee4d094bb385be"


def git(path, *args):
    return subprocess.run(["git", "-C", str(path), *args], check=True,
                          text=True, stdout=subprocess.PIPE, timeout=120).stdout.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bootstrap", action="store_true")
    args = parser.parse_args()
    gc = ROOT/"local/ac-decomp"
    if args.bootstrap:
        git(ROOT, "submodule", "update", "--init", "--", "upstream/af")
        if not gc.exists():
            gc.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(["git", "clone", "--no-checkout", "https://github.com/ACreTeam/ac-decomp", str(gc)],
                           check=True, timeout=120)
            git(gc, "checkout", "--detach", GC_PIN)
    for path, pin in ((gc, GC_PIN), (ROOT/"upstream/af", AF_PIN)):
        if not path.is_dir():
            raise ValueError(f"Missing reference: {path.relative_to(ROOT)}; use --bootstrap")
        if git(path, "rev-parse", "HEAD") != pin:
            raise ValueError(f"Reference revision differs: {path.relative_to(ROOT)}")
        if git(path, "status", "--porcelain", "--untracked-files=no"):
            raise ValueError(f"Tracked reference files are modified: {path.relative_to(ROOT)}")
        print(f"{path.relative_to(ROOT)}: verified {pin}")


if __name__ == "__main__":
    main()
