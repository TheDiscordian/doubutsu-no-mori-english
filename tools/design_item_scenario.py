#!/usr/bin/env python3
"""Batch the new complete design names and corrected ordinary species word."""

import argparse
import json
from pathlib import Path

from aflib import verified_rom
from extended_items_test_scenario import combine_load_scenarios, scenario as wide_scenario
from item_names_test_scenario import scenario as short_scenario
from item_matches import load_matches, validate_candidate, DESIGN_APPROVALS
from native_item_names import DESIGN_PATH
from runtime_module import module_command_info
from textbanks import banks
from textcodec import encode


def scenario(native, built, module, names):
    originals = {r['id'] for r in json.loads(DESIGN_PATH.read_text())}
    matched = {r['id'] for r in json.loads(DESIGN_APPROVALS.read_text())}
    selected = [r for r in names['edits'] if r.get('native_item_name') in originals
                or r.get('item_reference_match') in matched]
    if ((len(originals), len(matched), len(selected)) != (21, 4, 75)
            or {r.get('native_item_name') for r in selected if 'native_item_name' in r} != originals
            or {r.get('item_reference_match') for r in selected if 'item_reference_match' in r} != matched):
        raise ValueError('Design-name batch requires all 25 identities and 75 complete fields')
    source = {b.name: b.entries() for b in banks(native)}
    info, matches = module_command_info(native), load_matches()
    for row in selected: validate_candidate(row, source, info, matches)
    short = [r for r in selected if len(encode(r['translation'], info)) <= 10]
    if len(short) != 18: raise ValueError('Design-name batch requires all 18 complete short fields')
    items = [(0x1000 if r['id'].startswith('item_10:') else int(r['id'][5:7], 16)*256)
             +int(r['id'].split(':')[1], 16) for r in short]
    actions = combine_load_scenarios(wide_scenario(built, module, {**names, 'edits': selected}),
                                     short_scenario(native, built, items))
    # Execute the ordinary sixteen-byte string loader, not a copied expectation
    # from the separately embedded NPC word resource. Retain both edge guards.
    actions[-5:-5] = [
        {'write': ['8019B000', (b'G'*48).hex()]},
        {'call': {'address': '800C3F70', 'arguments': [0x8019B010, 16, 0x021A]}},
        {'read': ['8019B000', 48], 'expect': (b'G'*16+b'herabuna        '+b'G'*16).hex()},
    ]
    return actions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-rom', type=Path, default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    parser.add_argument('--build', type=Path, default=Path('build/design-items-pilot'))
    parser.add_argument('--names', type=Path, default=Path('build/design-items-resource/names.json'))
    parser.add_argument('--output', type=Path, default=Path('build/design-items-scenario.json'))
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
