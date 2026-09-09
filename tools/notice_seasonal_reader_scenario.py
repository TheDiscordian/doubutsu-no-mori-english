#!/usr/bin/env python3
"""Bind all 82 complete seasonal body/capital cases to the installed native reader."""

import argparse
import json
from pathlib import Path

from aflib import by_vrom
from mail_record import Field, Record
from notice_record import pack
from notice_seasonal import ROOT, compiled_resource, complete_body
from notice_reader_scenario import scenario as reader_scenario


def scenario(native, built, report, *, skip_complete=0):
    if type(skip_complete) is not int or not 0 <= skip_complete <= 82:
        raise ValueError('Invalid completed seasonal reader count')
    if report.get('noticeboard', {}).get('overlay', {}).get('seasonal') is not True:
        raise ValueError('Seasonal reader is not installed')
    actions = reader_scenario(native, built, report, skip_initial=8)
    resource = compiled_resource(native, by_vrom(built)[0x030A0000].extract(built))
    samples = {0: Field(b'TownXX'), 1: Field(resource['shops'][3]),
               2: Field(b'September 30th'), 3: Field(b'October 31st'), 4: Field(b'October 14th')}
    cases = []
    for entry in resource['templates']:
        for capital in (False, True):
            record = Record(4, 0, (entry['template'],), tuple((i, samples[i]) for i in entry['fields']), capital)
            cases.append({'template': entry['template'], 'capital': int(capital),
                          'wire': pack(record).hex(), 'body': complete_body(record, entry).hex()})
    actions[3]['test_notice_reader'].update(cases=cases, skip_initial=skip_complete, seasonal_only=True)
    return actions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, default=ROOT/'build/notice-seasonal-pilot')
    parser.add_argument('--output', type=Path, default=ROOT/'build/noticeboard-seasonal/native-reader-scenario.json')
    parser.add_argument('--skip-complete', type=int, default=0)
    args = parser.parse_args()
    actions = scenario((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
                       (args.build/'animal-forest-halfwidth.z64').read_bytes(),
                       json.loads((args.build/'build.json').read_text()), skip_complete=args.skip_complete)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(actions, indent=2)+'\n')
    print(json.dumps({'seasonal_bodies': 82-args.skip_complete, 'replayed_initial_or_treasure_bodies': 0,
                      'actual_calendar_or_creation': False, 'save_io': False, 'hardware_verified': False}))


if __name__ == '__main__': main()
