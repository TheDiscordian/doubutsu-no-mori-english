#!/usr/bin/env python3
"""Check complete secret letters through the ordinary unknown-sender window."""
import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256
from audit_secret_letters import ROOT,TEMPLATES
from display_names import HEADER as NAME_HEADER,VROM as NAME_VROM
from mail_catalog import templates
from mail_format import format_letter
from mail_record import Record,pack
from secret_actor import NEW_VROM,NEW_RELOCATION,verify_installation


def scenario(native,built,report):
    if sha256(built)!=report['output_sha256']: raise ValueError('Changed secret show cartridge')
    module = report['runtime_module'];verify_installation(built,native,module,report['secret_actor'])
    files = by_vrom(built);catalog = files[0x030A0000].extract(built)
    names = files[NAME_VROM].extract(built)
    if len(names)!=2272 or names[:32]!=NAME_HEADER: raise ValueError('Missing complete villager display names')
    name_index = next(i for i in range(216) if len(names[32+i*8:40+i*8].rstrip(b' '))==8)
    name = names[32+name_index*8:40+name_index*8]
    letters = {n:format_letter(Record(4,0,(n,),(),False),templates(catalog,Record(4,0,(n,),(),False))) for n in TEMPLATES}
    selected = {max(TEMPLATES,key=lambda n:len(getattr(letters[n],part))) for part in ('header','body','footer')}
    glyphs = [n for n in TEMPLATES if any(b'\x80'in getattr(letters[n],p) for p in ('header','body','footer'))]
    if not glyphs: raise ValueError('Secret show must cover its complete catalogue-four glyphs')
    selected.add(glyphs[0]);cases = []
    for index,n in enumerate(sorted(selected)):
        record = Record(4,0,(n,),(),bool(index%2));letter = format_letter(record,templates(catalog,record))
        mail = bytearray(164);mail[38:42] = bytes((0,128,0,0));mail[42:] = pack(record)
        header = letter.header[:letter.header_split]+name+letter.header[letter.header_split:]
        cases.append({'label':f'secret:{n:04X}','mail':mail.hex(),'snapshot':True,'header':header.hex(),
                      'body':letter.body.hex(),'footer':letter.footer.hex()})
    loader_at = 0x1060+0x800262D0-0x80025C60;loader = native[loader_at:loader_at+0xF0]
    if (sha256(loader)!='2c3176abe096fa667cd77599844acff5e0f46507ddbe1e95bbc1caf90a7d2b00'
            or built[loader_at:loader_at+0xF0]!=loader): raise ValueError('Changed secret show loader')
    code = files[CODE_VROM].extract(built)
    guards = {f'{lo:08X}':code[lo-CODE_RAM:hi-CODE_RAM].hex() for lo,hi in
              ((0x8009C384,0x8009C414),(0x8009C70C,0x8009C80C),(0x800A82C8,0x800A83F0),(0x800C4DB0,0x800C4E00))}
    request = {'branches':['unknown_sender'],'secret_overlay':report['secret_actor']['overlay'],
               'overlays':{'ordinary':{'data':files[NEW_VROM].extract(built).hex(),
                                       'relocation':files[NEW_RELOCATION].extract(built).hex()}},
               'cases':cases,'loader':loader.hex(),'guards':guards,
               'identity':struct.pack('>HH6sBB',0xE000+name_index,0xEAAA,b'OLDTWN',3,0).hex(),
               'reader':module['symbols']['af_mail_reader'],
               'hooks':{k:module['symbols'][k] for k in ('af_mail_header_hook','af_mail_body_hook','af_mail_footer_hook')}}
    return [{'wait':2},{'save_state':True},{'pause_game_thread':True},{'test_npc_mail_show':request},
            {'load_state':True},{'resume':True},{'wait':2}]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',type=Path,default=ROOT/'build/secret-letters-pilot')
    parser.add_argument('--output',type=Path,required=True);args = parser.parse_args()
    actions = scenario((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
                       (args.build/'animal-forest-halfwidth.z64').read_bytes(),json.loads((args.build/'build.json').read_text()))
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(actions,indent=2)+'\n')
    print(json.dumps({'actions':len(actions),'secret_windows':len(actions[3]['test_npc_mail_show']['cases'])}))


if __name__=='__main__': main()
