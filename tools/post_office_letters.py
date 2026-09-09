"""Source-bound catalogue-order and raffle-ticket letters with receipt gates."""

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
START,END = 0x800B6B94,0x800B6C14
ORDER_GATE,TICKET_GATE = 0x800B6C6C,0x800B6DB0
TEMPLATES = (0x49,0x4A,0x4B,0x4C,0x57)
GUARDS = (
    (0x800B6AC8,START,'da36ae83aedf2509b8ff0f98db3574dc5a2e6ed8f6bec2e35293125f2933c388'),
    (START,END,'59edde594228ebe64e0b3637558bd493cf3ce98e1ad7476f9da8b4e0b87c1294'),
    (END,0x800B6C88,'9161bab2cb2f26a863d80ca1c4db5a6d5d997fc4ac862b6d0f6d87e94daa2497'),
    (0x800B6C88,0x800B6D40,'d9fb16bbb82826a262c0b36d0df0c603a5b29b5c3fc400985400c19ad5396d7a'),
    (0x800B6D40,0x800B6D80,'617bb5db5a0f4ee0a7a130510609f58ecc808f51400fa24f8fd86da06ef9b715'),
    (0x800B6D80,0x800B6DCC,'15a6ec5d532557c680c07b152d2e73139b0ff666db07c2a25fa445aca22a3c76'),
    (0x800B6DCC,0x800B6EBC,'9e7709c21d9ce66846b6cf01c7f623781ca85878bf339662a9f7c30f27c9f208'),
)
REFERENCE_FUNCTIONS = {
    'mPO_copy_contents':(124,'eed764b9aeb7468d2b3b297d8b85ba7bfb9cf80c51c8d4be3efeadd4f10a08bc'),
    'mPO_delivery_mail_with_item':(128,'37e1b9644ddbb3ffea91be03551492824f7e652ea3bc05fbd5b5051bf1f6de2d'),
    'mPO_delivery_mail_with_order_ftr_sub':(128,'74c10cb9cd454a508c47cdc2988a46880ebeb7ec23b008b62e583b3c078a0cbb'),
    'mPO_delivery_mail_with_order_ftr':(148,'9911285ee312fa11ffc69a801571d77e1e0fa3dc1ae1aae40d6c09951df86d32'),
    'mPO_delivery_mail_with_ticket_set_free_str':(132,'23a575a582111df92be15af5978c64198f92811115dad1e132453aae2f324a5a'),
    'mPO_delivery_mail_with_ticket_sub':(96,'87f525c8bf81e65c16061f232099647a7cd0cbc8a4dd616877d74ca4c277cb52'),
    'mPO_delivery_mail_with_ticket':(188,'727780a58f0bf7eb08b0fda3242f7b2adee16be68fe18239f055ed1f9e4a1a6f'),
}


def verify_code(code):
    for start,end,digest in GUARDS:
        if sha256(code[start-CODE_RAM:end-CODE_RAM]) != digest:
            raise ValueError(f'Changed native post-office function at {start:08X}')


def fields(name,number):
    return {4 if number==0x57 else 0} if name=='mail' else set()


def verify_templates(rom,catalog,root=ROOT):
    import mail_creator_catalog as creator_catalog
    rom = verified_rom(rom);verify_code(by_vrom(rom)[CODE_VROM].extract(rom))
    catalog_id = creator_catalog.identity(catalog)
    native = {b.name:b.entries() for b in banks(rom) if b.name in ('super','mail','ps')}
    installed = parse(catalog)[1]
    rel = (root/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
    symbols = (root/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_text()
    if sha256(rel) != '29306a927eee861b073c571408393f99cb384048684eee4bff3d219725429837':
        raise ValueError('Changed supplied post-office executable')
    for name,expected in REFERENCE_FUNCTIONS.items():
        data = symbol_data(rel,symbols,name)
        if (len(data),sha256(data)) != expected: raise ValueError('Changed supplied post-office caller')
    decoder = root/'local/ac-decomp/tools/msg_tool.py'
    if sha256(decoder.read_bytes()) != DECODER_SHA256: raise ValueError('Changed English mail decoder')
    tables = decoder_tables(decoder);rows = []
    directory = root/'build/gamecube/files/forest_1st.arc.unpacked/data'
    for name in ('super','mail','ps'):
        data = (directory/(name+'_data.bin')).read_bytes();table = (directory/(name+'_data_table.bin')).read_bytes()
        if (sha256(data),sha256(table)) != BANK_HASHES[name]: raise ValueError('Changed reference letter bank')
        reference = Bank(name,0,0,data,table).entries()
        for number in TEMPLATES:
            value = transcode(reference[number],tables,extended_glyphs=catalog_id==4)
            if (value != installed[name][number]
                    or template_fields(value,extended_glyphs=catalog_id==4) != fields(name,number)
                    or template_fields(native[name][number]) != fields(name,number)):
                raise ValueError('Changed complete post-office text or field contract')
            rows.append({'id':f'{name}:{number:04X}','source_sha256':sha256(native[name][number]),
                         'reference_sha256':sha256(reference[number]),'encoded_sha256':sha256(value),
                         'bytes':len(value),'fields':sorted(fields(name,number))})
    return {'catalog':catalog_id,'complete_templates':list(TEMPLATES),'parts':rows,
            'reference_functions':REFERENCE_FUNCTIONS}


def patches(code,loader):
    verify_code(code)
    if type(loader) is not int or loader&3 or not MODULE_RAM+0x300 <= loader < MODULE_RAM+LINKED_LIMIT:
        raise ValueError('Post-office loader must be inside resident code')
    common = [0x27BDFFD0,0xAFBF002C,0xA7A5001C,0xA7A6001E,0x3C084146,0x3508504F,
              0xAFA80018,0x34080037,0xA3A80020,0xA3A00021,0xA3A00022,0x340800F9,
              0xA3A80023,0x00E02825,0x27A60018,0x00003825,0xAFA00010,0xAFA00014,
              0x0C000000|((loader>>2)&0x3FFFFFF),0,0x0002102B,0x8FBF002C,0x03E00008,0x27BD0030]
    result = {START:struct.pack('>24I',*common).ljust(END-START,b'\0')}
    for at,frame,mail in ((ORDER_GATE,208,44),(TICKET_GATE,192,28)):
        # On creation failure v0 stays zero. On success the unchanged copy
        # helper returns mailbox receipt, including full-mailbox rejection.
        gate = [0x10400003,0x8FA40000|frame,0x0C02DAB2,0x27A50000|mail,
                0x8FBF0014,0x03E00008,0x27BD0000|frame]
        result[at] = struct.pack('>7I',*gate)
    return result


def verify_items(module_data,items,digest=None):
    from extended_items import HEADER,COUNTS,WIDTH
    if (len(module_data)<60 or struct.unpack_from('>I',module_data,56)[0] != 0x02A00000
            or items[:32] != HEADER or len(items) != 32+sum(COUNTS)*WIDTH
            or (digest is not None and sha256(items) != digest)):
        raise ValueError('Post-office letters require the installed complete item-name resource')


def install(rom,replacements,additions,module):
    import mail_creator_catalog as creator_catalog
    rom = verified_rom(rom)
    if not module or module.get('npc_mail_loader',{}).get('overlay',{}).get('post_office') is not True:
        raise ValueError('Post-office letters require the extended postal creator')
    if any(v not in additions for v in (MODULE_VROM,CREATOR_VROM,0x02A00000)):
        raise ValueError('Missing post-office module, creator, or full item names')
    verify_configuration(additions[MODULE_VROM],additions[CREATOR_VROM],module)
    verify_items(additions[MODULE_VROM],additions[0x02A00000])
    original = by_vrom(rom)[CODE_VROM].extract(rom)
    code = bytearray(replacements.get(CODE_VROM,original));loader = int(module['symbols']['af_npc_mail_load'],16)
    evidence = verify_templates(rom,creator_catalog.resource(additions,module));changes = patches(code,loader)
    for at,value in changes.items(): code[at-CODE_RAM:at-CODE_RAM+len(value)] = value
    replacements[CODE_VROM] = bytes(code)
    return {**evidence,'patches':[{'ram':f'{at:08X}','bytes':len(value),'sha256':sha256(value)} for at,value in changes.items()],
            'loader_ram':f'{loader:08X}','item_resource_sha256':sha256(additions[0x02A00000]),
            'new_resident_bytes':0,'wrapper_stack_bytes':48,
            'status':'Complete order/ticket letters installed; native delivery and gameplay acceptance remain'}


def verify_installation(built,native,module,report):
    import mail_creator_catalog as creator_catalog
    files = by_vrom(built)
    verify_configuration(files[MODULE_VROM].extract(built),files[CREATOR_VROM].extract(built),module)
    creator_catalog.verify_installation(built,module,report)
    if module['npc_mail_loader']['overlay'].get('post_office') is not True:
        raise ValueError('Post-office dispatcher is not installed')
    if not isinstance(report.get('item_resource_sha256'),str): raise ValueError('Missing post-office item approval')
    verify_items(files[MODULE_VROM].extract(built),files[0x02A00000].extract(built),report['item_resource_sha256'])
    original = by_vrom(native)[CODE_VROM].extract(native)
    changes = patches(original,int(module['symbols']['af_npc_mail_load'],16))
    expected = [{'ram':f'{at:08X}','bytes':len(value),'sha256':sha256(value)} for at,value in changes.items()]
    if report.get('patches') != expected or report.get('complete_templates') != list(TEMPLATES):
        raise ValueError('Changed post-office installation report')
    actual = bytearray(files[CODE_VROM].extract(built))
    for at,value in changes.items():
        offset = at-CODE_RAM
        if actual[offset:offset+len(value)] != value: raise ValueError('Post-office creation or receipt gate is not installed')
        actual[offset:offset+len(value)] = original[offset:offset+len(value)]
    verify_code(actual)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,default=ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    parser.add_argument('--catalog',type=Path,default=ROOT/'build/mail-glyph-catalog/catalog.bin')
    args = parser.parse_args()
    report = verify_templates(args.rom.read_bytes(),args.catalog.read_bytes())
    print(json.dumps({'templates':len(TEMPLATES),'parts':len(report['parts']),'installed':False}))


if __name__ == '__main__': main()
