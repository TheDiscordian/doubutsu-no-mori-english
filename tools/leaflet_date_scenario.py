#!/usr/bin/env python3
"""Bind complete English date expectations and installed leaflet actor code."""

import argparse
import json
from pathlib import Path

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,verified_rom
from gc_names import symbol_data
from leaflet_dates import ACTORS,HOUR,HOUR_END,source,verify_installation
from runtime_module import verify_test_module

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_FUNCTIONS = {
    'aSL_SetShopRenewalChirashi_Notice':(412,'76d2569d8b9abfaa60c93a4285006b1efa05895c8f4060cc23395e1b38f49446'),
    'aEvMgr_actor_set_shop_handbill_str':(304,'b4e33b81b177d0f51a4af98b7408ffd17cee131c35052b9d2a1f0a4820492169'),
    'aEvMgr_actor_set_broker_handbill_str':(172,'006f97f4eee056b20da18b4b0675abe1fa7010bd8e8a7f64f35d5d0d3bec3d1c'),
    'mString_Load_HourStringFromRom':(220,'5dbd604d57d8b273e4016f04e3eb0be0d0631bd814480a60979496179521f3e6'),
}


def reference_fields():
    rel = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
    symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_text()
    if sha256(rel) != '29306a927eee861b073c571408393f99cb384048684eee4bff3d219725429837':
        raise ValueError('Changed supplied English leaflet executable')
    for name,expected in REFERENCE_FUNCTIONS.items():
        data = symbol_data(rel,symbols,name)
        if (len(data),sha256(data)) != expected:
            raise ValueError('Changed English leaflet/date reference')
    rows = {r['id']:r for r in map(json.loads,(ROOT/'build/gamecube/text/string.jsonl').read_text().splitlines())}
    def word(id):
        row = rows[f'string:{id:04X}'];data = row['text'].encode('ascii')
        if sha256(data) != row['sha256']:
            raise ValueError('Changed complete English date word')
        return data.rstrip(b' ').decode('ascii')
    return {'months':[word(i) for i in range(0x66D,0x679)],
            'days':[word(i) for i in range(0x64E,0x66D)],'ampm':[word(1),word(2)]}


def scenario(rom,native,build,directory):
    native = verified_rom(native);module = build['runtime_module']
    verify_test_module(rom,module);verify_installation(rom,native,module,directory)
    files = by_vrom(rom)
    actors = {name:{'original':source(native,name)[0].hex(),
                    'data':files[spec.vrom].extract(rom).hex(),
                    'reloc':files[spec.relocation].extract(rom).hex()} for name,spec in ACTORS.items()}
    at = 0x1060+0x800262D0-0x80025C60;loader = native[at:at+0xF0]
    if sha256(loader) != '2c3176abe096fa667cd77599844acff5e0f46507ddbe1e95bbc1caf90a7d2b00':
        raise ValueError('Changed native overlay loader')
    original = by_vrom(native)[CODE_VROM].extract(native);code = files[CODE_VROM].extract(rom)
    # The complete unchanged setter owns twenty ten-byte handbill rows.
    start,end = 0x80092D10,0x80092DA8
    if code[start-CODE_RAM:end-CODE_RAM] != original[start-CODE_RAM:end-CODE_RAM]:
        raise ValueError('Changed native leaflet field publication helper')
    request = {'module':module,'actors':actors,'fields':reference_fields(),'loader':loader.hex(),
               'hour':code[HOUR-CODE_RAM:HOUR_END-CODE_RAM].hex(),
               'setter':code[start-CODE_RAM:end-CODE_RAM].hex()}
    return [{'wait':8},{'save_state':True},{'pause_game_thread':True},{'test_leaflet_dates':request},
            {'load_state':True},{'resume':True},{'wait':2},{'read':['8019B000',4],'expect':'00000000'}]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-rom',type=Path,default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    parser.add_argument('--rom',type=Path,required=True)
    parser.add_argument('--build-report',type=Path,required=True)
    parser.add_argument('--code',type=Path,default=Path('build/leaflet-dates'))
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    actions = scenario(args.rom.read_bytes(),args.native_rom.read_bytes(),
                       json.loads(args.build_report.read_text()),args.code)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(actions,indent=2)+'\n')
    print(json.dumps({'actions':len(actions),'output':str(args.output)}))


if __name__ == '__main__':
    main()
