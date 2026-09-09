#!/usr/bin/env python3
"""Batch complete N64-original name identities and unchanged-width loads."""
import argparse
import json
from pathlib import Path

from aflib import verified_rom
from extended_items_test_scenario import combine_load_scenarios,scenario as wide_scenario
from item_names_test_scenario import scenario as short_scenario
from item_matches import load_matches,validate_candidate
from native_item_names import load_names,approval_key
from runtime_module import module_command_info
from textbanks import banks
from textcodec import encode


def scenario(native,built,module,names):
    originals = load_names()
    selected = [r for r in names['edits'] if approval_key(r['id'],originals) is not None]
    info = module_command_info(native)
    source = {b.name:b.entries() for b in banks(native)}
    if (len(originals)!=22 or len(selected)!=63 or
            {r.get('native_item_name') for r in selected} != originals.keys()):
        raise ValueError('Native-name batch requires 22 original identities and all 63 complete fields')
    matches = load_matches()
    for row in selected:
        validate_candidate(row,source,info,matches,originals=originals)
    short = [r for r in selected if len(encode(r['translation'],info))<=10]
    if len(short)!=31:
        raise ValueError('Native-name batch requires 31 complete original-width fields')
    items = [(0x1000 if r['id'].startswith('item_10:') else int(r['id'][5:7],16)<<8)+
             int(r['id'].split(':')[1],16) for r in short]
    return combine_load_scenarios(wide_scenario(built,module,{**names,'edits':selected}),
                                  short_scenario(native,built,items))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-rom',type=Path,default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    parser.add_argument('--build',type=Path,default=Path('build/native-items-pilot'))
    parser.add_argument('--names',type=Path,default=Path('build/native-items-resource/names.json'))
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
