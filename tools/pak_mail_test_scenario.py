#!/usr/bin/env python3
"""Generate isolated native Controller Pak letter write/read scenarios."""

import argparse
import json
from pathlib import Path

from flash_mail_test_scenario import scenario as flash_scenario
from mail_runtime_test_scenario import reference_fixtures
from pak_mail import evidence, passport_slots, letter_slots


def scenario(rom,module,fixtures,exported=None):
    request = flash_scenario(rom,module,fixtures)[3]['test_native_flash_mail_save']
    request = {key:request[key] for key in ('rom_sha256','cases','restore')}
    request.update(evidence(rom))
    action = 'test_native_pak_mail_save'
    if exported is not None:
        if (exported['rom_sha256'] != request['rom_sha256']
                or exported['passport_slots'] != passport_slots()
                or exported['letter_slots'] != letter_slots()):
            raise ValueError('Pak export must match the tested ROM and both exact storage inventories')
        request['export'] = exported
        action = 'test_native_pak_mail_read'
    return [{'wait':8},{'save_state':True},{'pause_game_thread':True},
            {action:request},{'load_state':True},{'resume':True},{'wait':2}]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,required=True)
    parser.add_argument('--module',type=Path,default=Path('build/runtime-module/module.json'))
    parser.add_argument('--native-rom',type=Path,default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    parser.add_argument('--gc-data',type=Path,default=Path('build/gamecube/files/forest_1st.arc.unpacked/data'))
    parser.add_argument('--decomp',type=Path,default=Path('local/ac-decomp'))
    parser.add_argument('--rel',type=Path,default=Path('build/gamecube/files/foresta.rel.szs.decoded'))
    parser.add_argument('--export',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    fixtures = reference_fixtures(args.native_rom.read_bytes(),args.gc_data,args.decomp,args.rel)
    exported = json.loads(args.export.read_text()) if args.export else None
    actions = scenario(args.rom.read_bytes(),json.loads(args.module.read_text()),fixtures,exported)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(actions,indent=2)+'\n')
    print(json.dumps({'mode':'read' if exported else 'save','actions':len(actions),'mail_slots':177}))


if __name__ == '__main__': main()
