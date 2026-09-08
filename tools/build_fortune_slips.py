#!/usr/bin/env python3
"""Build complete local fortune-slip words and an additional frozen catalog."""

import argparse
import json
from pathlib import Path

from aflib import sha256, verified_rom
from fortune_slips import CATALOG_VROM, IDS, TEMPLATES, catalog_three, words
from mail_catalog import verify_registered
from runtime_module import module_command_info


def build(rom, original, original_report, inventory, references, out):
    if (original_report.get('source_sha256') != sha256(rom)
            or original_report.get('registered') is not True
            or any(original_report.get(k) != v for k,v in verify_registered(original).items())):
        raise ValueError('Changed source catalog manifest')
    info = module_command_info(rom)
    word_data = words(rom,references,inventory,info)
    additional = catalog_three(rom,original,inventory,info)
    extra = {**verify_registered(additional),'vrom':f'{CATALOG_VROM:08X}'}
    report = {**original_report,'fortune_catalog':extra}
    out.mkdir(parents=True,exist_ok=True)
    (out/'catalog.bin').write_bytes(original)
    (out/'catalog.json').write_text(json.dumps(report,indent=2)+'\n')
    (out/'fortune-catalog.bin').write_bytes(additional)
    (out/'fortune-words.bin').write_bytes(word_data)
    evidence = {'source_sha256':sha256(rom),'word_sha256':sha256(word_data),
                'word_ids':list(IDS),'word_bytes':len(word_data),
                'classic_templates':list(TEMPLATES),'catalog':extra,
                'status':'Complete source resources; native actor publication is not installed'}
    (out/'fortune-slips.json').write_text(json.dumps(evidence,indent=2)+'\n')
    return evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,required=True)
    parser.add_argument('--catalog',type=Path,default=Path('build/mail-catalog'))
    parser.add_argument('--inventory',type=Path,default=Path('build/inventory'))
    parser.add_argument('--references',type=Path,default=Path('build/gamecube/text'))
    parser.add_argument('--output',type=Path,default=Path('build/fortune-slip-resources'))
    args = parser.parse_args()
    inventory = {r['id']:r for name in ('string','super','mail','ps')
                 for r in map(json.loads,(args.inventory/(name+'.jsonl')).read_text().splitlines())}
    references = {r['id']:r for r in map(json.loads,(args.references/'string.jsonl').read_text().splitlines())}
    print(json.dumps(build(verified_rom(args.rom.read_bytes()),(args.catalog/'catalog.bin').read_bytes(),
        json.loads((args.catalog/'catalog.json').read_text()),inventory,references,args.output),indent=2))


if __name__ == '__main__': main()
