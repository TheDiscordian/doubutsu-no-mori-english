"""Complete source-bound HRA welcome/advice letters and native success gates."""

import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,verified_rom
from audit_mail_templates import template_fields
from gc_names import symbol_data
from gc_text import decoder_tables
from mail_catalog import parse,verify_registered
from mail_reference import BANK_HASHES,DECODER_SHA256,transcode
from npc_mail_loader import VROM as CREATOR_VROM,verify_configuration
from runtime_layout import MODULE_RAM,MODULE_VROM,LINKED_LIMIT
from textbanks import Bank,banks

ROOT = Path(__file__).resolve().parents[1]
START,END,SCHEDULER = 0x8009CC94,0x8009CDA8,0x8009CDA8
TEMPLATES = tuple(range(0x1DC,0x1F0))
GUARDS = (
    (0x8009CA94,0x8009CB5C,'49fe8b16f69943289fdf9360ce6f56caf446ecff1e6fb738530775bcf860b981'),
    (0x8009CB5C,0x8009CC00,'57929566cace5a60c8468b8c1ddac4c179c19cab4efe39de6032a77bab47b9c5'),
    (START,END,'12b3ba80804712e6a9095cae1ba4ef4718167ff5e90021a008e770192a1f3302'),
    (SCHEDULER,0x8009CFB0,'f72844989cf4b94f994da3edb8b6607e91417325410dd1ca3ad858db8f6dd207'),
)
REFERENCE_FUNCTIONS = {
    'mMkRm_NoMarkLetter':(212,'d6714013f49c206bb44bdb43c7ad6196b3e01e14a9d83cbcfa1a494340c4521f'),
    'mMkRm_NoMarkLetter_Hint':(344,'ca0185294ccaa02de8e56c63470acd0c05b0699f7a77ae7c772b072efec08c8e'),
    'mMkRm_MarkRoom':(316,'182a0c3722402736d6a598b8a9f4db50ef919e6677685fc4260158407c80846a'),
}


def verify_code(code):
    for start,end,digest in GUARDS:
        if sha256(code[start-CODE_RAM:end-CODE_RAM]) != digest:
            raise ValueError(f'Changed native academy function at {start:08X}')


def verify_templates(rom,catalog,root=ROOT):
    rom = verified_rom(rom);verify_code(by_vrom(rom)[CODE_VROM].extract(rom))
    if verify_registered(catalog)['catalog'] != 2:
        raise ValueError('Academy letters require unchanged catalogue two')
    native = {b.name:b.entries() for b in banks(rom) if b.name in ('super','mail','ps')}
    installed = parse(catalog)[1]
    rel = (root/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
    symbols = (root/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_text()
    if sha256(rel) != '29306a927eee861b073c571408393f99cb384048684eee4bff3d219725429837':
        raise ValueError('Changed supplied academy executable')
    for name,expected in REFERENCE_FUNCTIONS.items():
        data = symbol_data(rel,symbols,name)
        if (len(data),sha256(data)) != expected: raise ValueError('Changed supplied academy caller')
    decoder = root/'local/ac-decomp/tools/msg_tool.py'
    if sha256(decoder.read_bytes()) != DECODER_SHA256: raise ValueError('Changed English mail decoder')
    tables = decoder_tables(decoder);rows = []
    directory = root/'build/gamecube/files/forest_1st.arc.unpacked/data'
    for name in ('super','mail','ps'):
        data = (directory/(name+'_data.bin')).read_bytes();table = (directory/(name+'_data_table.bin')).read_bytes()
        if (sha256(data),sha256(table)) != BANK_HASHES[name]: raise ValueError('Changed reference letter bank')
        reference = Bank(name,0,0,data,table).entries()
        for number in TEMPLATES:
            value = transcode(reference[number],tables)
            if (value != installed[name][number] or template_fields(value)
                    or template_fields(native[name][number])):
                raise ValueError('Changed complete academy text or field contract')
            rows.append({'id':f'{name}:{number:04X}','source_sha256':sha256(native[name][number]),
                         'reference_sha256':sha256(reference[number]),'encoded_sha256':sha256(value),
                         'bytes':len(value),'fields':[]})
    return {'classic_templates':list(TEMPLATES),'parts':rows,'reference_functions':REFERENCE_FUNCTIONS}


def patches(code,loader):
    verify_code(code)
    if type(loader) is not int or loader&3 or not MODULE_RAM+0x300 <= loader < MODULE_RAM+LINKED_LIMIT:
        raise ValueError('Academy loader must be inside resident code')
    entry = [0x27BDFF10,0xAFBF00EC,0x2C810004,0,0x24A8FE24,0x2D010014,0,0xA7A50024,
             0x34080B48,0x00880019,0x00004012,0x3C098013,0x2529A8A0,0x01092021,
             0xAFA400D4,0x0C02714D,0x3405000A,0,0xAFA200D8,0xAFA00018,0xAFA0001C,
             0xAFA00020,0xA7A00026,0x340800FB,0xA3A80028,0x34080033,0xA3A80029,
             0x27A40030,0x3C058013,0x8CA56FD8,0x00003025,0x27A70018,0xAFA00010,
             0x34080001,0x0C000000|((loader>>2)&0x3FFFFFF),0xAFA80014,0,0x8FA800D8,
             0x340900A4,0x01090019,0x00004012,0x8FA900D4,0x01092021,0x0C02719F,
             0x00402825,0x34020001,0x10000002,0,0x00001025,0x8FBF00EC,0x03E00008,0x27BD00F0]
    for index,op in ((3,0x10200000),(6,0x10200000),(17,0x04400000),(36,0x10400000)):
        entry[index] = op|(48-index-1)
    welcome = [0x10400000|((0x8009CF9C-0x8009CE2C-4)//4),0x8FA90038,0x340A0B48,
               0x012A0019,0x00005012,0x3C0B8013,0x014B1021,0x904DA444,0x35AE0020,
               0xA04EA444,0x0C0272D7,0x02002025,
               0x10000000|((0x8009CF9C-0x8009CE5C-4)//4),0,
               0x10400003,0,0x080272D7,0,0x03E00008,0]
    return {START:struct.pack('>52I',*entry).ljust(END-START,b'\0'),
            0x8009CE2C:struct.pack('>20I',*welcome),
            0x8009CF94:struct.pack('>I',0x0C000000|((0x8009CE64>>2)&0x3FFFFFF))}


def install(rom,replacements,additions,module):
    from villager_event_letters import patches as event_patches
    rom = verified_rom(rom)
    if not module or module.get('npc_mail_loader',{}).get('overlay',{}).get('academy_letters') is not True:
        raise ValueError('Academy letters require the extended academy creator')
    if any(v not in additions for v in (MODULE_VROM,CREATOR_VROM,0x03000000)):
        raise ValueError('Missing academy module, creator, or catalogue')
    verify_configuration(additions[MODULE_VROM],additions[CREATOR_VROM],module)
    original = by_vrom(rom)[CODE_VROM].extract(rom)
    code = bytearray(replacements.get(CODE_VROM,original));loader = int(module['symbols']['af_npc_mail_load'],16)
    for at,value in event_patches(original,loader).items():
        if code[at-CODE_RAM:at-CODE_RAM+len(value)] != value:
            raise ValueError('Academy letters require installed villager-event integration')
    evidence = verify_templates(rom,additions[0x03000000]);changes = patches(code,loader)
    for at,value in changes.items(): code[at-CODE_RAM:at-CODE_RAM+len(value)] = value
    replacements[CODE_VROM] = bytes(code)
    return {**evidence,'patches':[{'ram':f'{at:08X}','bytes':len(value),'sha256':sha256(value)} for at,value in changes.items()],
            'loader_ram':f'{loader:08X}','new_resident_bytes':0,'wrapper_stack_bytes':240,
            'status':'Complete welcome/advice letters installed; score/reward letters and gameplay acceptance remain'}


def verify_installation(built,native,module,report):
    files = by_vrom(built)
    verify_configuration(files[MODULE_VROM].extract(built),files[CREATOR_VROM].extract(built),module)
    if module['npc_mail_loader']['overlay'].get('academy_letters') is not True:
        raise ValueError('Academy dispatcher is not installed')
    original = by_vrom(native)[CODE_VROM].extract(native)
    changes = patches(original,int(module['symbols']['af_npc_mail_load'],16))
    expected = [{'ram':f'{at:08X}','bytes':len(value),'sha256':sha256(value)} for at,value in changes.items()]
    if report.get('patches') != expected or report.get('classic_templates') != list(TEMPLATES):
        raise ValueError('Changed academy installation report')
    actual = bytearray(files[CODE_VROM].extract(built))
    for at,value in changes.items():
        offset = at-CODE_RAM
        if actual[offset:offset+len(value)] != value: raise ValueError('Academy creation or success gate is not installed')
        actual[offset:offset+len(value)] = original[offset:offset+len(value)]
    if module['npc_mail_loader']['overlay'].get('academy_scores') is True:
        from academy_score_letters import scheduler_patch
        at,value = scheduler_patch();offset = at-CODE_RAM
        if actual[offset:offset+len(value)] == value:
            actual[offset:offset+len(value)] = original[offset:offset+len(value)]
    verify_code(actual)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,default=ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    parser.add_argument('--catalog',type=Path,default=ROOT/'build/mail-catalog/catalog.bin')
    args = parser.parse_args()
    report = verify_templates(args.rom.read_bytes(),args.catalog.read_bytes())
    print(json.dumps({'templates':len(TEMPLATES),'parts':len(report['parts']),'installed':False}))


if __name__ == '__main__': main()
