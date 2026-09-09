#!/usr/bin/env python3
"""Batch only newly translated resolved names through the native loaders."""

import argparse
import json
from pathlib import Path

from aflib import verified_rom
from extended_items_test_scenario import combine_load_scenarios, scenario as wide_scenario
from item_names_test_scenario import scenario as short_scenario
from item_matches import load_matches, validate_candidate, RESOLVED_APPROVALS
from runtime_module import module_command_info
from textbanks import banks
from textcodec import encode


def scenario(native, built, module, names):
    approvals = {r['id'] for r in json.loads(RESOLVED_APPROVALS.read_text())}-{'item_2D:0005'}
    selected = [r for r in names['edits'] if r.get('item_reference_match') in approvals]
    if len(approvals) != 29 or len(selected) != 65 or {r['item_reference_match'] for r in selected} != approvals:
        raise ValueError('Resolved-name batch requires all 29 new identities and 65 complete fields')
    source = {b.name: b.entries() for b in banks(native)}
    info, matches = module_command_info(native), load_matches()
    for row in selected: validate_candidate(row, source, info, matches)
    short = [r for r in selected if len(encode(r['translation'], info)) <= 10]
    if len(short) != 35: raise ValueError('Resolved-name batch requires all 35 complete short fields')
    items = [(0x1000 if r['id'].startswith('item_10:') else int(r['id'][5:7], 16)*256)
             +int(r['id'].split(':')[1], 16) for r in short]
    return combine_load_scenarios(wide_scenario(built, module, {**names, 'edits': selected}),
                                  short_scenario(native, built, items))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-rom', type=Path, default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    parser.add_argument('--build', type=Path, default=Path('build/resolved-items-pilot'))
    parser.add_argument('--names', type=Path, default=Path('build/resolved-items-resource/names.json'))
    parser.add_argument('--output', type=Path, default=Path('build/resolved-items-scenario.json'))
    args = parser.parse_args()
    actions = scenario(verified_rom(args.native_rom.read_bytes()),
                       (args.build/'animal-forest-halfwidth.z64').read_bytes(),
                       json.loads((args.build/'runtime-module.json').read_text()),
                       json.loads(args.names.read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(actions, indent=2)+'\n')
    print(json.dumps({'actions': len(actions), 'calls': sum('call' in a for a in actions),
                      'assertions': sum('expect' in a for a in actions)}))


if __name__ == '__main__': main()
