#!/usr/bin/env python3
"""One bounded batch for all gyroid identities and native-width rotations."""
import argparse
import json
from pathlib import Path

from aflib import verified_rom
from extended_items_test_scenario import combine_load_scenarios, scenario as wide_scenario
from item_names_test_scenario import scenario as short_scenario
from item_matches import load_matches, validate_candidate
from runtime_module import module_command_info
from textbanks import banks
from textcodec import encode


def scenario(native, built, module, names):
    keys = {f'item_10:{i*4:04X}' for i in range(364,491)}
    slots = {f'item_10:{i*4+r:04X}' for i in range(364,491) for r in range(4)}
    matches = load_matches()
    selected = [r for r in names['edits'] if r['id'] in slots]
    if not keys <= matches.keys() or len(selected) != 508 or {r['id'] for r in selected} != slots:
        raise ValueError('Gyroid batch requires all 127 identities and 508 complete rotation names')
    info = module_command_info(native)
    source = {b.name:b.entries() for b in banks(native)}
    for row in selected:
        validate_candidate(row,source,info,matches)
    short = [r for r in selected if len(encode(r['translation'],info)) <= 10]
    if len(short) != 124:
        raise ValueError('Gyroid batch requires 124 complete native-width rotations')
    items = [0x1000+int(r['id'].split(':')[1],16) for r in short]
    return combine_load_scenarios(wide_scenario(built,module,{**names,'edits':selected}),
                                  short_scenario(native,built,items))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-rom',type=Path,default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    parser.add_argument('--build',type=Path,default=Path('build/gyroid-items-pilot'))
    parser.add_argument('--names',type=Path,default=Path('build/gyroid-items-resource/names.json'))
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    actions = scenario(verified_rom(args.native_rom.read_bytes()),
                       (args.build/'animal-forest-halfwidth.z64').read_bytes(),
                       json.loads((args.build/'runtime-module.json').read_text()),
                       json.loads(args.names.read_text()))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(actions,indent=2)+'\n')
    print(json.dumps({'actions':len(actions),'calls':sum('call' in a for a in actions),
                      'assertions':sum('expect' in a for a in actions)}))


if __name__ == '__main__':
    main()
