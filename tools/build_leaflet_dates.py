#!/usr/bin/env python3
"""Compile the full leaflet time into the original native formatter's code span."""

import argparse
import json
import os
from pathlib import Path
import subprocess

from aflib import sha256
from check_keyboard_assembly import IMAGE
from leaflet_dates import HOUR, source_hashes, validate_hour


def build(out):
    root = Path(__file__).resolve().parents[1]
    hashes = source_hashes()
    out.mkdir(parents=True, exist_ok=True)
    common = ['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
              '-v',f'{root}:/source:ro','-v',f'{out}:/out','-w','/out','--entrypoint']
    def run(tool, *args):
        result = subprocess.run(common+['/n64_toolchain/bin/mips64-elf-'+tool,IMAGE,*args],
                                capture_output=True,text=True,timeout=60)
        if result.returncode:
            raise ValueError('Leaflet compiler failed: '+result.stdout+result.stderr)
        return result.stdout
    flags = ['-c','-Os','-EB','-mabi=32','-march=vr4300','-mfix4300','-G0','-mno-abicalls',
             '-fno-pic','-ffreestanding','-fno-builtin','-fno-common','-fno-stack-protector',
             '-fno-jump-tables','-fstack-usage','-Wall','-Wextra','-Werror']
    run('gcc',*flags,'/source/overlays/leaflet_dates/hour.c','-o','hour.o')
    run('ld','-EB','--emit-relocs','-T','/source/overlays/leaflet_dates/hour.ld',
        '-Map=hour.map','-o','hour.elf','hour.o')
    if run('nm','--undefined-only','hour.elf').strip():
        raise ValueError('Undefined leaflet hour symbol')
    symbols = {}
    for line in run('nm','--defined-only','hour.elf').splitlines():
        fields = line.split()
        if len(fields) == 3:
            symbols[fields[2]] = int(fields[0],16)
    if symbols.get('af_leaflet_hour') != HOUR or symbols.get('__hour_start') != HOUR:
        raise ValueError('Leaflet hour entry moved')
    run('objcopy','-O','binary','-j','.text','hour.elf','hour.bin')
    data = (out/'hour.bin').read_bytes()
    relocations = run('readelf','-rW','hour.elf')
    if 'R_MIPS_' in relocations or symbols.get('__hour_end') != HOUR+len(data):
        raise ValueError('Leaflet hour has unexpected references or bounds')
    report = {'version':1,'ram':HOUR,'bytes':len(data),'sha256':sha256(data),
              'sources':hashes,'compiler':run('gcc','--version').splitlines()[0],
              'flags':flags,'toolchain_image':IMAGE,'stack_usage':(out/'hour.su').read_text(),
              'imports':[],'relocations':[],'destination_bytes':7}
    validate_hour(data,report)
    (out/'hour.json').write_text(json.dumps(report,indent=2)+'\n')
    (out/'hour.asm').write_text(run('objdump','-d','hour.elf'))
    (out/'hour-relocations.txt').write_text(relocations)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('build/leaflet-dates'))
    args = parser.parse_args()
    print(json.dumps(build(args.output.resolve()),indent=2))


if __name__ == '__main__':
    main()
