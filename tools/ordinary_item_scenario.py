#!/usr/bin/env python3
"""Reproduce the bounded ordinary-name batch with both native name loaders."""
import argparse
import json
from pathlib import Path

from aflib import verified_rom
from extended_items_test_scenario import combine_load_scenarios, scenario as wide_scenario
from item_names_test_scenario import scenario as short_scenario
from item_matches import load_matches
from runtime_module import module_command_info
from textcodec import encode

GROUPS = ('20', '21', '22', '25', '28', '29', '2A', '2C', '2E', '2F')


def scenario(native, built, module, names):
    info = module_command_info(native)
    approved = {key for key in load_matches() if key[5:7] in GROUPS}
    selected = [r for r in names['edits'] if r['id'] in approved]
    if len(selected) != 209 or {r['id'] for r in selected} != approved:
        raise ValueError('Ordinary item batch requires all 209 complete approved names')
    short = [r for r in selected if len(encode(r['translation'], info)) <= 10]
    if len(short) != 50:
        raise ValueError('Ordinary item batch requires fifty complete native-width names')
    items = [(int(r['id'][5:7], 16) << 8)+int(r['id'].split(':')[1], 16) for r in short]
    return combine_load_scenarios(
        wide_scenario(built, module, names, ['item_'+g for g in GROUPS]),
        short_scenario(native, built, items))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-rom', type=Path, default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    parser.add_argument('--build', type=Path, default=Path('build/ordinary-items-pilot'))
    parser.add_argument('--names', type=Path, default=Path('build/ordinary-items-resource/names.json'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    actions = scenario(verified_rom(args.native_rom.read_bytes()),
                       (args.build/'animal-forest-halfwidth.z64').read_bytes(),
                       json.loads((args.build/'runtime-module.json').read_text()),
                       json.loads(args.names.read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(actions, indent=2)+'\n')
    print(json.dumps({'actions':len(actions), 'calls':sum('call' in a for a in actions)}))


if __name__ == '__main__':
    main()
