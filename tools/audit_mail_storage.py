#!/usr/bin/env python3
"""Record selected metadata/storage boundaries and the Pelly failure-loss path."""

import argparse
import json
from pathlib import Path

from aflib import sha256, verified_rom
from audit_display_names import audit as references
from mail_storage import FUNCTIONS, evidence, pelly_evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=Path('build/audits/mail-storage.json'))
    args = parser.parse_args()
    rom = verified_rom(args.rom.read_bytes())
    result = {'rom_sha256':sha256(rom),'storage':evidence(rom),'pelly':pelly_evidence(rom),
              'references':references(rom,{name:row[0] for name,row in FUNCTIONS.items()},allow_empty=True)}
    for value in result['references'].values():
        value['status'] = 'Selected native mail predicate/storage references; inline/computed-pointer consumers require independent review'
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'output':str(args.output),'references':{name:len(value['callers'])
                      for name,value in result['references'].items()},'pelly':result['pelly']['status']}))


if __name__ == '__main__': main()
