#!/usr/bin/env python3
"""Inventory native reply and quest scoring calls without treating bodies as records."""

import argparse
import json
from pathlib import Path

from aflib import sha256, verified_rom
from audit_display_names import audit as audit_references

TARGETS = {'ordinary_grade':0x800A86C4,'length_grade':0x800A8614,'word_rate':0x8009C900,
           'send':0x800A8868,'reply_dispatch':0x800A8814,'local_reply':0x800A86E8,
           'visitor_reply':0x800A8764,'quest_receiver':0x800BBB30}
EXPECTED = {'ordinary_grade':['800A8718','800A8770'],
            'length_grade':['800A86D0','800BBACC'],'word_rate':['800A8634'],
            'send':['800B69B4'],'reply_dispatch':['800A89A0'],'local_reply':['800A8838'],
            'visitor_reply':['800A8848'],'quest_receiver':['800A8A50']}


def audit(rom):
    rom = verified_rom(rom)
    reports = audit_references(rom,TARGETS,allow_empty=True)
    for name,report in reports.items():
        if ([row['call_ram'] for row in report['callers']] != EXPECTED[name]
                or report['literal_pointers']):
            raise ValueError('Unexpected native mail grading references: '+name)
        report['status'] = 'Original-ROM direct references; installed whole-record send handling and computed pointers require separate validation'
    return {'rom_sha256':sha256(rom),'targets':reports,
            'scope':'Direct jumps/calls and aligned literal pointers across extracted DMA files; not proof that computed indirect references are absent'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=Path('build/audits/mail-grade-callers.json'))
    args = parser.parse_args()
    report = audit(args.rom.read_bytes())
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({name:[r['call_ram'] for r in info['callers']]
                      for name,info in report['targets'].items()},indent=2))


if __name__ == '__main__': main()
