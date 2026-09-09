"""Complete source-bound museum notices and fossil letters with receipt gates."""

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
START,END,HOME_GATE,QUEUE_GATE = 0x800A345C,0x800A34E8,0x800A3580,0x800A3630
STAGING,NAME,TABLE = 0x80142730,0x8010AE40,0x8010AE50
FOSSILS = (0x10E,0x110,0x10F,0x111,0x113,0x112,0x114,0x116,0x115,
           0x117,0x119,0x118,0x11A,0x11B,0x11C,0x11D,0x11E,0x11F,
           0x120,0x121,0x126,0x125,0x123,0x124,0x122)
TEMPLATES = (0xBD,0xBE,*range(0x10E,0x127))
TABLE_HASH = 'd47fbce27270ce235e57caf85fa38b71d2ed287b707c6801ada618107b57e55f'
GUARDS = (
    (0x800A3420,START,'af54ffb1ee5bd11eca4bc3b26eecbf025f95c4304bc2096452afbc9a983f4f02'),
    (START,END,'36534ed97cf7dca4479762573af5a8aab477cb7f642ee7efa159331bbed8ce64'),
    (END,0x800A35C8,'6658f78bfffa7547911737bad0436093ebc4887175527d81e7fdbf47903ef403'),
    (0x800A35C8,0x800A3658,'7a2d44baf35ca3831ab5b0a12b77c0f3f1f4eeb9c9003613fbe6812379a239b7'),
    (0x800A36CC,0x800A3784,'351cca06d6266186227bc512d69eca1f22eedee6184ad70783a3f3e291341e56'),
    (0x800A3784,0x800A37D0,'44f0af6de758b19db1ad0ac547fa2d020fb7e9b806a5a66da7c0530afaaedb7b'),
    (0x800A37D0,0x800A3810,'ef3656608179edda5d47f35d4359295237b3e96846977665732d1af171792fd0'),
    (0x800A3810,0x800A3A5C,'65554f75dec69d166cad8aa054e7db3a2546ad3200ad03c415db920366e54c37'),
)
REFERENCE = {
    'mMsm_GetMuseumMailName':(68,'f5266daa234a7db789f0b3885122f5756b7361f5557f8fda4a86ab50bd56d8be'),
    'mMsm_SendInformationMail':(192,'d09527fa91811808b86937c6869f42cb6f3d65073abe549a7ddeea1d25626871'),
    'mMsm_GetFossil':(92,'2a14b1657cf6207007e0d977330fb51b6738b2ad3191226018610aff07c32e19'),
    'mMsm_GetFossilMailNo':(72,'a34d49366ee1f41842778c1947e239c54d42a336e0e3e37625f0eb47793dbaab'),
    'mMsm_SendResultMail':(748,'b75663039553ec9c959e36ba2b22a76842f04f1346e25a1b3ffe0185e78c8db1'),
    'mail_no_table$449':(100,TABLE_HASH),
    'l_museum_name_str':(8,'d361d5bc8ea259655bc0736e3b48d1939e0f62599a1a1e43ac0b2662db3b9130'),
}


def verify_code(code):
    for start,end,digest in GUARDS:
        if sha256(code[start-CODE_RAM:end-CODE_RAM])!=digest:
            raise ValueError(f'Changed native museum function at {start:08X}')
    table = code[TABLE-CODE_RAM:TABLE-CODE_RAM+100]
    if sha256(table)!=TABLE_HASH or struct.unpack('>25I',table)!=FOSSILS:
        raise ValueError('Changed native fossil template mapping')
    if code[NAME-CODE_RAM:NAME-CODE_RAM+6]!=bytes.fromhex('1907F81105C3'):
        raise ValueError('Changed canonical native museum sender identity')


def verify_templates(rom,catalog,root=ROOT):
    import mail_creator_catalog as creator_catalog
    rom = verified_rom(rom);verify_code(by_vrom(rom)[CODE_VROM].extract(rom))
    catalog_id = creator_catalog.identity(catalog)
    native = {b.name:b.entries() for b in banks(rom) if b.name in ('super','mail','ps')}
    installed = parse(catalog)[1]
    rel = (root/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
    symbols = (root/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_text()
    if sha256(rel)!='29306a927eee861b073c571408393f99cb384048684eee4bff3d219725429837':
        raise ValueError('Changed supplied museum executable')
    for name,expected in REFERENCE.items():
        data = symbol_data(rel,symbols,name)
        if (len(data),sha256(data))!=expected: raise ValueError('Changed supplied museum function/table')
    decoder = root/'local/ac-decomp/tools/msg_tool.py'
    if sha256(decoder.read_bytes())!=DECODER_SHA256: raise ValueError('Changed English mail decoder')
    tables = decoder_tables(decoder);rows = []
    directory = root/'build/gamecube/files/forest_1st.arc.unpacked/data'
    for name in ('super','mail','ps'):
        data = (directory/(name+'_data.bin')).read_bytes();table = (directory/(name+'_data_table.bin')).read_bytes()
        if (sha256(data),sha256(table))!=BANK_HASHES[name]: raise ValueError('Changed reference letter bank')
        reference = Bank(name,0,0,data,table).entries()
        for number in TEMPLATES:
            value = transcode(reference[number],tables,extended_glyphs=catalog_id==4)
            if (value!=installed[name][number] or template_fields(value,extended_glyphs=catalog_id==4)
                    or template_fields(native[name][number])):
                raise ValueError('Changed complete museum text or field contract')
            rows.append({'id':f'{name}:{number:04X}','source_sha256':sha256(native[name][number]),
                         'reference_sha256':sha256(reference[number]),'encoded_sha256':sha256(value),
                         'bytes':len(value),'fields':[]})
    return {'catalog':catalog_id,'complete_templates':list(TEMPLATES),'parts':rows,
            'reference_functions':REFERENCE,'fossil_templates':list(FOSSILS)}


def patches(code,loader):
    verify_code(code)
    if type(loader) is not int or loader&3 or not MODULE_RAM+0x300<=loader<MODULE_RAM+LINKED_LIMIT:
        raise ValueError('Museum loader must be inside resident code')
    # Return the complete destination pointer (or zero), and explicitly set a1
    # to zero for the original queue receipt's second argument. Both callers
    # are patched together and their full original functions are guarded.
    common = [0x27BDFFD0,0xAFBF002C,0xA7A7001C,0xA7A6001E,0x3C084146,0x35084D55,
              0xAFA80018,0x34080018,0xA3A80020,0xA3A00021,0xA3A00022,0x340800F8,
              0xA3A80023,0x27A60018,0x00003825,0xAFA00010,0xAFA00014,
              0x0C000000|((loader>>2)&0x3FFFFFF),0,0x00002825,0x8FBF002C,0x03E00008,0x27BD0030]
    home = [0x1040000C,0x8FA3001C,0x340800A4,0x00680019,0x00004012,0x8FB90024,
            0x03282021,0x24840478,0x0C02719F,0x8FA50030,0x24090001,0xAFA90018,0]
    queue = [0x10400004,0x00401825,0x0C02DA8F,0x00402025,0x00401825]
    return {START:struct.pack('>23I',*common).ljust(END-START,b'\0'),
            HOME_GATE:struct.pack('>13I',*home),QUEUE_GATE:struct.pack('>5I',*queue)}


def install(rom,replacements,additions,module):
    import mail_creator_catalog as creator_catalog
    rom = verified_rom(rom)
    if not module or module.get('npc_mail_loader',{}).get('overlay',{}).get('museum') is not True:
        raise ValueError('Museum letters require the complete museum creator')
    if any(v not in additions for v in (MODULE_VROM,CREATOR_VROM)):
        raise ValueError('Missing museum module or creator')
    verify_configuration(additions[MODULE_VROM],additions[CREATOR_VROM],module)
    code = bytearray(replacements.get(CODE_VROM,by_vrom(rom)[CODE_VROM].extract(rom)))
    loader = int(module['symbols']['af_npc_mail_load'],16)
    evidence = verify_templates(rom,creator_catalog.resource(additions,module));changes = patches(code,loader)
    for at,value in changes.items(): code[at-CODE_RAM:at-CODE_RAM+len(value)] = value
    replacements[CODE_VROM] = bytes(code)
    return {**evidence,'patches':[{'ram':f'{at:08X}','bytes':len(value),'sha256':sha256(value)} for at,value in changes.items()],
            'loader_ram':f'{loader:08X}','new_resident_bytes':0,'wrapper_stack_bytes':48,
            'status':'Complete museum notices and fossil letters installed; native and gameplay acceptance remain'}


def verify_installation(built,native,module,report):
    import mail_creator_catalog as creator_catalog
    files = by_vrom(built)
    verify_configuration(files[MODULE_VROM].extract(built),files[CREATOR_VROM].extract(built),module)
    creator_catalog.verify_installation(built,module,report)
    if module['npc_mail_loader']['overlay'].get('museum') is not True:
        raise ValueError('Museum dispatcher is not installed')
    original = by_vrom(native)[CODE_VROM].extract(native)
    changes = patches(original,int(module['symbols']['af_npc_mail_load'],16))
    expected = [{'ram':f'{at:08X}','bytes':len(value),'sha256':sha256(value)} for at,value in changes.items()]
    if (report.get('patches')!=expected or report.get('complete_templates')!=list(TEMPLATES)
            or report.get('fossil_templates')!=list(FOSSILS)):
        raise ValueError('Changed museum installation report')
    actual = bytearray(files[CODE_VROM].extract(built))
    for at,value in changes.items():
        offset = at-CODE_RAM
        if actual[offset:offset+len(value)]!=value: raise ValueError('Museum creation or receipt gate is not installed')
        actual[offset:offset+len(value)] = original[offset:offset+len(value)]
    verify_code(actual)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,default=ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    parser.add_argument('--catalog',type=Path,default=ROOT/'build/mail-glyph-catalog/catalog.bin')
    args = parser.parse_args();report = verify_templates(args.rom.read_bytes(),args.catalog.read_bytes())
    print(json.dumps({'templates':len(TEMPLATES),'parts':len(report['parts']),'installed':False}))


if __name__=='__main__': main()
