#!/usr/bin/env python3
"""Bind the installed renewal actor to complete source-derived English letters."""

import argparse
from datetime import date, timedelta
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256
from leaflet_date_scenario import reference_fields
from leaflet_letters import verify_templates
from mail_catalog import templates
from mail_record import Field, Record, pack
from mail_runtime_test_scenario import output_bytes
from renewal_actor import NEW_VROM, NEW_RELOCATION, verify_installation
from runtime_module import verify_test_module


def scenario(native, rom, build, creator):
    module, report = build['runtime_module'], build['renewal_actor']['overlay']
    verify_test_module(rom, module)
    verify_installation(rom, native, report, module, creator)
    files = by_vrom(rom)
    catalogue = files[0x03000000].extract(rom)
    verify_templates(native, catalogue)
    words, cases = reference_fields(), []
    for level in range(4):
        for capital in range(2):
            for when in (date(2000, 1, 1), date(2000, 3, 1), date(2001, 3, 1)):
                closed = when-timedelta(days=1)
                values = (Field(words['months'][closed.month-1].encode().ljust(9, b' ')),
                          Field(words['days'][closed.day-1].encode().ljust(4, b' ')),
                          Field(str(closed.year).encode()))
                record = Record(2, 0, (24+min(level, 2),), tuple(enumerate(values)), bool(capital))
                cases.append({'level': level, 'capital': capital,
                              'rtc': bytes((0, 0, 12, when.day, 0, when.month,
                                            when.year>>8, when.year&255)).hex(),
                              'wire': pack(record).hex(),
                              'text': output_bytes(record, templates(catalogue, record)).hex()})
    at = 0x1060+0x800262D0-0x80025C60
    loader = native[at:at+0xF0]
    if sha256(loader) != '2c3176abe096fa667cd77599844acff5e0f46507ddbe1e95bbc1caf90a7d2b00':
        raise ValueError('Changed native overlay loader')
    request = {'module': module, 'report': report, 'loader': loader.hex(), 'cases': cases,
               'data': files[NEW_VROM].extract(rom).hex(),
               'relocation': files[NEW_RELOCATION].extract(rom).hex(),
               'metadata': build['renewal_actor']['metadata']}
    return [{'wait': 8}, {'save_state': True}, {'pause_game_thread': True},
            {'test_renewal_actor': request}, {'load_state': True}, {'resume': True},
            {'wait': 2}, {'read': ['8019B000', 4], 'expect': '00000000'}]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-rom', type=Path, default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    parser.add_argument('--build', type=Path, default=Path('build/renewal-actor-pilot'))
    parser.add_argument('--creator', type=Path, default=Path('build/renewal-actor/creator-original.bin'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    actions = scenario(args.native_rom.read_bytes(), (args.build/'animal-forest-halfwidth.z64').read_bytes(),
                       json.loads((args.build/'build.json').read_text()), args.creator.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(actions, indent=2)+'\n')
    print(json.dumps({'actions': len(actions), 'complete_letter_cases': 24}))


if __name__ == '__main__':
    main()
