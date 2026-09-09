"""Source-bound complete villager-event and Christmas letter installation.

The CLI verifies references only. Installation and built-ROM verification are
explicit APIs; reference presence alone never credits an applied route.
"""

import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,verified_rom
from audit_mail_templates import template_fields
from gc_names import symbol_data
from gc_text import decoder_tables
from mail_catalog import parse
from mail_reference import BANK_HASHES,DECODER_SHA256,transcode
from npc_mail_loader import VROM as CREATOR_VROM,verify_configuration
from runtime_layout import MODULE_RAM,MODULE_VROM,LINKED_LIMIT
from textbanks import Bank,banks

ROOT = Path(__file__).resolve().parents[1]
EVENT = tuple(range(0x60,0x72))
BIRTHDAY = tuple(range(0xEA,0xFC))
GOODBYE = tuple(range(0x20E,0x220))
CHRISTMAS = (0xD7,)
TEMPLATES = (*EVENT,*BIRTHDAY,*GOODBYE,*CHRISTMAS)
UNAVAILABLE = (0xF6,)
COMPLETE = tuple(i for i in TEMPLATES if i not in UNAVAILABLE)
START = 0x800A93AC
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


def verify_code(code):
    for start,end,digest in GUARDS:
        if sha256(code[start-CODE_RAM:end-CODE_RAM]) != digest:
            raise ValueError(f'Changed native villager-event letter function at {start:08X}')


def verify_templates(rom,catalog,root=ROOT):
    import mail_creator_catalog as creator_catalog
    rom = verified_rom(rom);code = by_vrom(rom)[CODE_VROM].extract(rom)
    verify_code(code)
    catalog_id = creator_catalog.identity(catalog)
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
            try: value = transcode(reference[number],tables,extended_glyphs=catalog_id==4)
            except ValueError as error:
                if name != 'mail' or number != 0xF6 or 'GC D0' not in str(error): raise
                if installed[name][number] is not None: raise ValueError('Missing semicolon must stay unavailable')
                row['unavailable'] = str(error)
            else:
                if value != installed[name][number] or template_fields(value,extended_glyphs=catalog_id==4) != fields(name,number):
                    raise ValueError('Changed complete villager-event text or field identity')
                row.update(encoded_sha256=sha256(value),bytes=len(value),fields=sorted(fields(name,number)))
            rows.append(row)
    return {'catalog':catalog_id,'classic_templates':list(TEMPLATES),
            'complete_templates':list(TEMPLATES if catalog_id==4 else COMPLETE),
            'unavailable_templates':[] if catalog_id==4 else list(UNAVAILABLE),'parts':rows,
            'reference_functions':REFERENCE_FUNCTIONS,'native_guards':GUARDS,
            'status':'Verified reference content and callers only; no installed route'}


def patches(code,loader):
    verify_code(code)
    if type(loader) is not int or loader&3 or not MODULE_RAM+0x300 <= loader < MODULE_RAM+LINKED_LIMIT:
        raise ValueError('Villager-event loader must be inside resident code')
    jal = 0x0C000000|((loader>>2)&0x03FFFFFF)
    common = [0x27BDFFD0,0xAFBF002C,0x10C00023,0x30C80001,0x15000021,0x8FA80040,
              0x2D010040,0x1020001E,0x8FA90044,0x2D210220,0x1020001B,0x00070C02,
              0x14200019,0xA7A90024,0xA7A70026,0xA3A80029,0x340800FC,0xA3A80028,
              0x94C80000,0xA7A80018,0x94C80002,0xA7A8001A,0x94C80004,0xA7A8001C,
              0x94C80006,0xA7A8001E,0x94C80008,0xA7A80020,0x94C8000A,0xA7A80022,
              0x27A70018,0x00003025,0xAFA00010,0x34080001,jal,0xAFA80014,
              0x10000002,0,0x00001025,0x8FBF002C,0x03E00008,0x27BD0030]
    christmas = [0x27BDFFC0,0xAFBF003C,0xAFA40034,0xAFA50038,0xA7A0002E,0x00002025,
                 0x27A5002E,0x34060001,0x00003825,0xAFA00010,0xAFA00014,0x34080003,
                 0x0C02FF3C,0xAFA80018,0xAFA00020,0xAFA00024,0xAFA00028,
                 0x340800D7,0xA7A8002C,0x340800FC,0xA3A80030,0x34080016,0xA3A80031,
                 0x8FA40034,0x8FA50038,0x00003025,0x27A70020,0xAFA00010,
                 0x34080001,jal,0xAFA80014,0x8FBF003C,0x03E00008,0x27BD0040]
    output = {START:struct.pack('>42I',*common).ljust(188,b'\0'),
              0x800A9CD4:struct.pack('>34I',*christmas).ljust(148,b'\0'),
              0x800AC340:struct.pack('>I',0x0002182B)}
    # Native mailbox offset is index*164 + home + 0x478. Reuse the returned
    # staging pointer to fit the new failure check inside the original span.
    for at,end,index_slot,home_slot,home_reg,temp_reg in (
            (0x800A961C,0x800A969C,40,48,10,11),
            (0x800A9B3C,0x800A9BB0,32,40,8,9),
            (0x800A9E08,0x800A9E40,32,40,25,8)):
        words = [0x10400000|((end-at-4)//4),0x8FA30000|index_slot,
                 0x8FA00000|(home_reg<<16)|home_slot,(3<<16)|(temp_reg<<11)|(2<<6),
                 (temp_reg<<21)|(3<<16)|(temp_reg<<11)|0x21,
                 (temp_reg<<16)|(temp_reg<<11)|(3<<6),
                 (temp_reg<<21)|(3<<16)|(temp_reg<<11)|0x21,
                 (temp_reg<<16)|(temp_reg<<11)|(2<<6),
                 (home_reg<<21)|(temp_reg<<16)|(4<<11)|0x21,
                 0x24840478,0x0C02719F,0x00402825]
        output[at] = struct.pack('>12I',*words)
    for at,end in ((0x800A9688,0x800A969C),(0x800A9B9C,0x800A9BB0)):
        output[at] = struct.pack('>2I',0x10400000|((end-at-4)//4),0x00402025)
    return dict(sorted(output.items()))


def install(rom,replacements,additions,module):
    import mail_creator_catalog as creator_catalog
    from departed_letters import START as DSTART,END as DEND,patch as departed_patch
    from mother_letters import START as MSTART,END as MEND,patch as mother_patch
    from extended_items import HEADER,COUNTS,WIDTH
    rom = verified_rom(rom)
    if not module or module.get('npc_mail_loader',{}).get('overlay',{}).get('villager_events') is not True:
        raise ValueError('Villager-event letters require the extended event creator')
    if any(at not in additions for at in (MODULE_VROM,CREATOR_VROM,0x03000000,0x02A00000)):
        raise ValueError('Missing villager-event module, creator, catalogue, or full item names')
    verify_configuration(additions[MODULE_VROM],additions[CREATOR_VROM],module)
    items = additions[0x02A00000]
    if (struct.unpack_from('>I',additions[MODULE_VROM],56)[0] != 0x02A00000
            or items[:32] != HEADER or len(items) != 32+sum(COUNTS)*WIDTH):
        raise ValueError('Villager-event letters require the installed full item resource')
    original = by_vrom(rom)[CODE_VROM].extract(rom)
    code = bytearray(replacements.get(CODE_VROM,original))
    loader = int(module['symbols']['af_npc_mail_load'],16)
    for start,end,patch in ((MSTART,MEND,mother_patch),(DSTART,DEND,departed_patch)):
        if code[start-CODE_RAM:end-CODE_RAM] != patch(original[start-CODE_RAM:end-CODE_RAM],loader):
            raise ValueError('Villager-event letters require earlier complete system-letter routes')
    evidence = verify_templates(rom,creator_catalog.resource(additions,module));changes = patches(code,loader)
    for at,value in changes.items(): code[at-CODE_RAM:at-CODE_RAM+len(value)] = value
    replacements[CODE_VROM] = bytes(code)
    return {**evidence,'patches':[{'ram':f'{at:08X}','bytes':len(value),'sha256':sha256(value)} for at,value in changes.items()],
            'loader_ram':f'{loader:08X}','new_resident_bytes':0,'common_wrapper_stack_bytes':48,
            'christmas_wrapper_stack_bytes':64,'status':'Complete selected-catalogue event letters installed; gameplay acceptance remains'}


def verify_installation(built,native,module,report):
    import mail_creator_catalog as creator_catalog
    files = by_vrom(built)
    verify_configuration(files[MODULE_VROM].extract(built),files[CREATOR_VROM].extract(built),module)
    catalog = creator_catalog.verify_installation(built,module,report)
    if module['npc_mail_loader']['overlay'].get('villager_events') is not True:
        raise ValueError('Villager-event dispatcher is not installed')
    original = by_vrom(native)[CODE_VROM].extract(native)
    changes = patches(original,int(module['symbols']['af_npc_mail_load'],16))
    expected = [{'ram':f'{at:08X}','bytes':len(value),'sha256':sha256(value)} for at,value in changes.items()]
    if report.get('patches') != expected or report.get('complete_templates') != list(TEMPLATES if catalog==4 else COMPLETE):
        raise ValueError('Changed villager-event installation report')
    actual = bytearray(files[CODE_VROM].extract(built))
    for at,value in changes.items():
        offset = at-CODE_RAM
        if actual[offset:offset+len(value)] != value: raise ValueError('Villager-event creator or publication gate is not installed')
        actual[offset:offset+len(value)] = original[offset:offset+len(value)]
    verify_code(actual)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,default=ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    parser.add_argument('--catalog',type=Path,default=ROOT/'build/mail-catalog/catalog.bin')
    args = parser.parse_args()
    report = verify_templates(args.rom.read_bytes(),args.catalog.read_bytes())
    print(json.dumps({'templates':len(TEMPLATES),'complete':len(report['complete_templates']),'parts':len(report['parts']),
                      'unavailable':report['unavailable_templates'],'installed':False}))


if __name__ == '__main__': main()
