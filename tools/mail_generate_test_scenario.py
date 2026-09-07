#!/usr/bin/env python3
"""Generate isolated native whole-letter creation tests with English references."""

import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct

from aflib import by_vrom,sha256
from mail_catalog import VROM,CONFIG_OFFSET,verify_registered,templates
from mail_format import format_letter
from mail_generate_probe import validate
from mail_record import Record,Field,pack
from mail_runtime_test_scenario import reference_fixtures,output_bytes
from runtime_module import verify_test_module,MODULE_RAM,MODULE_VROM


def capture_bytes(record,extra=True):
    fields = {i:Field(b'UNUSED VALUE    ',4) for i in range(20)} if extra else {}
    fields.update(dict(record.fields))
    output = struct.pack('>2I',sum(1<<i for i in fields),int(record.initial_capital))
    for i in range(20):
        field = fields.get(i,Field(b''))
        output += bytes((len(field.text),field.article))+field.text.ljust(16,b'\0')
    if len(output) != 368: raise ValueError('Native generation capture size changed')
    return output


def scenario(rom,module,code,report,cases):
    verify_test_module(rom,module)
    validate(code,report,module)
    files = by_vrom(rom)
    catalog = files[VROM].extract(rom)
    verify_registered(catalog)
    if files[MODULE_VROM].extract(rom)[CONFIG_OFFSET:CONFIG_OFFSET+4] != VROM.to_bytes(4,'big'):
        raise ValueError('Native generation requires a configured catalog')
    rows = []
    def add(label,record,success=True,extra=True):
        selection = struct.pack('>HBB5H',record.catalog,record.kind,0,*(record.templates+(0,)*(5-len(record.templates))))
        capture = capture_bytes(record,extra)
        mail = bytearray(range(164))
        row = {'label':label,'selection':selection.hex(),'capture':capture.hex(),'success':success}
        after = bytearray(capture)
        if success:
            parts = templates(catalog,record)
            mail[39],mail[42:] = 128,pack(record)
            after[4:8] = int(format_letter(record,parts).final_capital).to_bytes(4,'big')
            row['text'] = output_bytes(record,parts).hex()
        row.update(mail=mail.hex(),after_capture=after.hex())
        rows.append(row)
    for label,record,parts,limitation in cases:
        record = replace(record,catalog=2)
        if format_letter(record,replace(parts,catalog=2)) != format_letter(record,templates(catalog,record)):
            raise ValueError('Native generation reference differs from catalog')
        add(label,record)
    for label,record,extra in (
            ('missing_required',Record(2,0,(2,),()),False),
            ('unknown_catalog',Record(3,0,(0,),()),True),
            ('classic_id_bound',Record(2,0,(982,),()),True),
            ('composite_id_bound',Record(2,1,(0,0,384,0,0),()),True),
            ('unavailable_classic',Record(2,0,(43,),()),True),
            ('unavailable_composite',Record(2,1,(0,0,0,0,77),()),True),
            ('exact_field_overflow',Record(2,0,(1,),tuple((i,Field(b'x'*16)) for i in range(10,20))),True)):
        add(label,record,False,extra)
    request = {'code':code.hex(),'probe':report,'module':module,'cases':rows,
               'configuration_ram':MODULE_RAM+CONFIG_OFFSET,'configuration':VROM.to_bytes(4,'big').hex()}
    return [{'wait':8},{'save_state':True},{'pause_game_thread':True},
            {'test_mail_generation':request},{'load_state':True},{'resume':True},{'wait':2}]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,required=True)
    parser.add_argument('--module',type=Path,default=Path('build/runtime-module/module.json'))
    parser.add_argument('--probe',type=Path,default=Path('build/mail-generation-probe'))
    parser.add_argument('--native-rom',type=Path,default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    parser.add_argument('--gc-data',type=Path,default=Path('build/gamecube/files/forest_1st.arc.unpacked/data'))
    parser.add_argument('--decomp',type=Path,default=Path('local/ac-decomp'))
    parser.add_argument('--rel',type=Path,default=Path('build/gamecube/files/foresta.rel.szs.decoded'))
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    cases = reference_fixtures(args.native_rom.read_bytes(),args.gc_data,args.decomp,args.rel)
    actions = scenario(args.rom.read_bytes(),json.loads(args.module.read_text()),
                       (args.probe/'generate.bin').read_bytes(),json.loads((args.probe/'generate.json').read_text()),cases)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(actions,indent=2)+'\n')
    print(json.dumps({'actions':len(actions),'reference_cases':len(cases),
                      'rejected_cases':len(actions[3]['test_mail_generation']['cases'])-len(cases)}))


if __name__ == '__main__': main()
