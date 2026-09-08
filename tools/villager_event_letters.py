"""Source binding for the next complete villager-event and Christmas letter batch.

This verifies content and native callers only; it does not install or credit a route.
"""

import argparse
import json
from pathlib import Path

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,verified_rom
from audit_mail_templates import template_fields
from gc_names import symbol_data
from gc_text import decoder_tables
from mail_catalog import parse,verify_registered
from mail_reference import BANK_HASHES,DECODER_SHA256,transcode
from textbanks import Bank,banks

ROOT = Path(__file__).resolve().parents[1]
EVENT = tuple(range(0x60,0x72))
BIRTHDAY = tuple(range(0xEA,0xFC))
GOODBYE = tuple(range(0x20E,0x220))
CHRISTMAS = (0xD7,)
TEMPLATES = (*EVENT,*BIRTHDAY,*GOODBYE,*CHRISTMAS)
UNAVAILABLE = (0xF6,)
COMPLETE = tuple(i for i in TEMPLATES if i not in UNAVAILABLE)
GUARDS = (
    (0x800A93AC,0x800A9468,'c032ea2500931cc53d4fc3b0abb2b210b825b3775189e9d675109d18fceb48e8'),
    (0x800A94C8,0x800A956C,'7ba71c6bad42f967404d40f31a00931fdcd56782441c52f674f3bd5882975127'),
    (0x800A956C,0x800A96B0,'5af0d28226e52e97534728e3e29d07725e66eb60287d3820fbd1fe7213283984'),
    (0x800A99B8,0x800A9A98,'fbfea591ef2685ce4392ef461b47830d794cad8f61073f540f4496f7acf67f22'),
    (0x800A9A98,0x800A9BC4,'e46642ea1ba1c1d44b9d391415ca1fdcd418b37c79ab002dd78097105fbe786b'),
    (0x800AC284,0x800AC358,'b352ca90c52694fcac1b0503bf32805a998080ed053e15a9be2b4cb12d1dc5c7'),
    (0x800AC358,0x800AC488,'00d312b9676e9c08a2c3b478e6d0d0e74be925d94e1dd2306e185ac958fe3ea6'),
    (0x800AC488,0x800AC558,'1452561af23a2f8e8abf43d41f8618404cd93d893e017e0f8beb558cbe177875'),
    (0x800A9CD4,0x800A9D68,'09e3ea007632aa12c0455d2bd0d48974ff1d0b9e311d6c639f9315035717da28'),
    (0x800A9D68,0x800A9E54,'65114935548de2301ff47394b2344e93ab81e69434961c7802347e56f520e0dc'),
)
REFERENCE_FUNCTIONS = {
    'mNpc_LoadMailDataCommon2':(196,'f7385282f3b0433a1513f6941b8658d50a9a449a46f23e21ac53a2dda547bad0'),
    'mNpc_GetEventMail':(164,'a43819e81972770a1bc05559d00c223a46f71ede064eb081d1989fbb77114a5d'),
    'mNpc_SendEventPresentMail':(268,'06fe516f045ac166871e1d90cbc5e0e1c639e1c69cae7717a34f1cccbe05decf'),
    'mNpc_GetBirthdayCard':(220,'0e09bf989806d9745273a028e5292ddb091072d36a84b8de875d51ed7d1d321c'),
    'mNpc_SendBirthdayCard':(260,'ddde2fa5fca63e3d02f5512299c3cd1a3d1d415a274b224651ed1ff7456b30a9'),
    'mNpc_SetGoodbyMailData':(212,'5f5455192f3fa51a00edca3d74b7906a4ed06f0bf033ce7bcf18d2b00cffd381'),
    'mNpc_SendGoodbyAnimalMailOne':(260,'6535e4fe08549e196616942d7fae3538b29c0c10e2ecf32279044116629be153'),
    'mNpc_SendGoodbyAnimalMail':(196,'481a8877c9745d65ee32d817e1cb645d60d2c8bf920c3cda8609f5794834ceb6'),
    'mNpc_GetXmasCardData':(136,'e477a78e36897823c01c902cefb155a4340121e85c3e9d47c0c225732231fcb9'),
    'mNpc_SendEventXmasCard':(204,'dd690cdbb457140a8e0abcf1c88a31898b58a9a14a905e46513ac40b9bdcbef4'),
}


def fields(name,number,*,native=False):
    if name not in ('super','mail','ps') or number not in TEMPLATES:
        raise ValueError('Unknown villager-event letter part')
    if number in CHRISTMAS or name == 'super': return set()
    if name == 'ps': return {6} if number in EVENT else {1}
    if number in EVENT:
        return {0} if number in (0x61,0x62,0x63,0x69,0x6C,0x6D,0x6F,0x70) or native and number == 0x64 else set()
    if number in GOODBYE:
        return ({3} if number in (0x214,0x217) or native and number == 0x219 else set())|(
            {0} if native and number in (0x218,0x219) else set())
    body = ((),(0,),(0,),(),(),(2,),(),(0,2),(),(0,),(0,2),(0,),(0,),(0,),(),(),(0,),(2,))
    result = set(body[number-0xEA])
    if native and number == 0xEF: result.add(1)
    if native and number in (0xF8,0xF9): result.add(0)
    return result


def verify_templates(rom,catalog,root=ROOT):
    rom = verified_rom(rom);code = by_vrom(rom)[CODE_VROM].extract(rom)
    for start,end,digest in GUARDS:
        if sha256(code[start-CODE_RAM:end-CODE_RAM]) != digest:
            raise ValueError(f'Changed native villager-event letter function at {start:08X}')
    if verify_registered(catalog)['catalog'] != 2:
        raise ValueError('Villager-event references require unchanged catalogue two')
    native = {b.name:b.entries() for b in banks(rom) if b.name in ('super','mail','ps')}
    installed = parse(catalog)[1]
    rel = (root/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
    symbols = (root/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_text()
    if sha256(rel) != '29306a927eee861b073c571408393f99cb384048684eee4bff3d219725429837':
        raise ValueError('Changed supplied villager-event executable')
    for name,expected in REFERENCE_FUNCTIONS.items():
        data = symbol_data(rel,symbols,name)
        if (len(data),sha256(data)) != expected:
            raise ValueError('Changed supplied villager-event creator or caller')
    decoder = root/'local/ac-decomp/tools/msg_tool.py'
    if sha256(decoder.read_bytes()) != DECODER_SHA256: raise ValueError('Changed mail decoder')
    tables = decoder_tables(decoder);rows = []
    directory = root/'build/gamecube/files/forest_1st.arc.unpacked/data'
    for name in ('super','mail','ps'):
        data = (directory/(name+'_data.bin')).read_bytes();table = (directory/(name+'_data_table.bin')).read_bytes()
        if (sha256(data),sha256(table)) != BANK_HASHES[name]: raise ValueError('Changed reference letter bank')
        reference = Bank(name,0,0,data,table).entries()
        for number in TEMPLATES:
            if template_fields(native[name][number]) != fields(name,number,native=True):
                raise ValueError('Changed native villager-event field source')
            row = {'id':f'{name}:{number:04X}','source_sha256':sha256(native[name][number]),
                   'reference_sha256':sha256(reference[number])}
            try: value = transcode(reference[number],tables)
            except ValueError as error:
                if name != 'mail' or number != 0xF6 or 'GC D0' not in str(error): raise
                if installed[name][number] is not None: raise ValueError('Missing semicolon must stay unavailable')
                row['unavailable'] = str(error)
            else:
                if value != installed[name][number] or template_fields(value) != fields(name,number):
                    raise ValueError('Changed complete villager-event text or field identity')
                row.update(encoded_sha256=sha256(value),bytes=len(value),fields=sorted(fields(name,number)))
            rows.append(row)
    return {'classic_templates':list(TEMPLATES),'complete_templates':list(COMPLETE),
            'unavailable_templates':list(UNAVAILABLE),'parts':rows,
            'reference_functions':REFERENCE_FUNCTIONS,'native_guards':GUARDS,
            'status':'Verified reference content and callers only; no installed route'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,default=ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    parser.add_argument('--catalog',type=Path,default=ROOT/'build/mail-catalog/catalog.bin')
    args = parser.parse_args()
    report = verify_templates(args.rom.read_bytes(),args.catalog.read_bytes())
    print(json.dumps({'templates':len(TEMPLATES),'complete':len(COMPLETE),'parts':len(report['parts']),
                      'unavailable':report['unavailable_templates'],'installed':False}))


if __name__ == '__main__': main()
