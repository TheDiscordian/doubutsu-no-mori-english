#!/usr/bin/env python3
"""Bind native Mom delivery tests to complete source-derived English text."""

import argparse
import json
from pathlib import Path

from aflib import CODE_RAM,CODE_VROM,by_vrom
from mail_catalog import templates
from mail_record import Record,pack
from mail_runtime_test_scenario import output_bytes
from mother_letters import START,END,COMPLETE,verify_templates,verify_installation
from runtime_module import verify_test_module


def scenario(native,built,report):
    module = report['runtime_module'];verify_test_module(built,module)
    verify_installation(built,native,module,report['mother_letters'])
    files = by_vrom(built);catalog = files[0x03000000].extract(built)
    verify_templates(native,catalog)
    cases = []
    for index,number in enumerate(COMPLETE):
        record = Record(2,0,(number,),(),bool(index%2))
        cases.append({'template':number,'capital':index%2,'paper':index%64,'gift':0x1000+index,
                      'wire':pack(record).hex(),'text':output_bytes(record,templates(catalog,record)).hex()})
    code = files[CODE_VROM].extract(built)
    request = {'module':module,'cases':cases,'code':code[START-CODE_RAM:END-CODE_RAM].hex()}
    return [{'wait':8},{'save_state':True},{'pause_game_thread':True},
            {'test_mother_letters':request},{'load_state':True},{'resume':True},
            {'wait':2},{'read':['8019B000',4],'expect':'00000000'}]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-rom',type=Path,default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    parser.add_argument('--build',type=Path,default=Path('build/mother-letters-pilot'))
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    actions = scenario(args.native_rom.read_bytes(),(args.build/'animal-forest-halfwidth.z64').read_bytes(),
                       json.loads((args.build/'build.json').read_text()))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(actions,indent=2)+'\n')
    print(json.dumps({'actions':len(actions),'complete_mom_templates':len(COMPLETE)}))


if __name__ == '__main__': main()
