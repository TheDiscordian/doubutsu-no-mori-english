#!/usr/bin/env python3
"""Prepare verified, local-only build inputs from the supplied archives."""

import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import zipfile

from aflib import sha256, verified_rom
from gamecube import Disc

LEGACY_ZIP_SHA256 = "d0f7e708fa2453c9f06714d9d39b1265e02f4878d330dcea99c85c52123838ed"
LEGACY_UPS_SHA256 = "ae4d50632e9d9bcf19ccc0f9672afd3aed592784e62c7b6422526da86d74e1da"


def store_input(path, data):
    """Refuse to overwrite a different input, including through a symlink."""
    if path.exists() or path.is_symlink():
        if not path.is_file() or path.read_bytes() != data:
            raise ValueError(f"Existing input differs: {path}")
        return "already_verified"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as target:
        target.write(data)
    return "prepared"


def extract_7z(path, member):
    return subprocess.run(["7z", "x", "-so", "--", str(path.resolve()), member],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          check=True, timeout=120).stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n64-archive", type=Path, required=True)
    parser.add_argument("--legacy-zip", type=Path, required=True)
    parser.add_argument("--gamecube-archive", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]/"local"
    report = {}
    rom = verified_rom(extract_7z(args.n64_archive, "Doubutsu no Mori (Japan).z64"))
    report["n64"] = {"sha256": sha256(rom), "status": store_input(root/"rom/Doubutsu no Mori (Japan).z64", rom)}
    if sha256(args.legacy_zip.read_bytes()) != LEGACY_ZIP_SHA256:
        raise ValueError("Unsupported legacy distribution archive")
    with zipfile.ZipFile(args.legacy_zip) as archive:
        members = [n for n in archive.namelist() if n.endswith("/NAFE-WIP-2_12_2010.ups")]
        if len(members) != 1:
            raise ValueError("Missing or ambiguous legacy patch")
        patch = archive.read(members[0])
    if sha256(patch) != LEGACY_UPS_SHA256:
        raise ValueError("Unexpected legacy patch hash")
    report["legacy_ups"] = {"sha256": sha256(patch), "status": store_input(root/"legacy/AFProjectDistro/NAFE-WIP-2_12_2010.ups", patch)}
    disc = extract_7z(args.gamecube_archive, "Animal Crossing (USA, Canada).ciso")
    if len(disc) < 0x8000 or disc[:4] != b"CISO":
        raise ValueError("Expected a GameCube CISO member")
    target = root/"gamecube/Animal Crossing (USA, Canada).ciso"
    # Validate before creating the durable input. A failed disc check must not
    # leave an unsupported file at the path used by subsequent builds.
    with tempfile.TemporaryDirectory(prefix="af-disc-check-") as directory:
        temporary = Path(directory)/"disc.ciso"
        temporary.write_bytes(disc)
        with Disc(temporary) as image:
            if image.header[:6] != b"GAFE01" or image.header[7] != 0:
                raise ValueError("Expected GAFE01 revision 0")
            image.files()
    status = store_input(target, disc)
    report["gamecube"] = {"sha256": sha256(disc), "status": status, "revision": "GAFE01_00"}
    (root/"prepared-inputs.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
