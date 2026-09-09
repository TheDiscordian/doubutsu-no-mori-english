"""Source-bound complete departed-villager letters and receipt retention."""

from pathlib import Path
import struct

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,verified_rom
from audit_mail_templates import template_fields
from gc_names import symbol_data
from gc_text import decoder_tables
from mail_catalog import parse
from mail_reference import BANK_HASHES,DECODER_SHA256,transcode
from mother_letters import START as MOM_START,END as MOM_END,patch as mother_patch
from npc_mail_loader import VROM as CREATOR_VROM,verify_configuration
from runtime_layout import MODULE_RAM,MODULE_VROM,LINKED_LIMIT
from textbanks import Bank,banks

ROOT = Path(__file__).resolve().parents[1]
START,POST,END = 0x800B9C34,0x800B9DAC,0x800B9E44
TEMPLATES = tuple(range(0xFC,0x10E))
GUARDS = (
    (START,POST,'a23000c283f82ab03d9af62ab377460d27caf3539f316b7717b116ff7d6250f3'),
    (POST,END,'56babf0ec91465d24802377cc595c1a36ece8e949c549aa586a69e9ca7b6f7de'),
    (0x800AA1E0,0x800AA218,'7c3c02c70afbbf3f0759e2f89f6ebd00e37160925c0513fe001168a1cae23e8c'),
    (0x800ACC38,0x800ACCAC,'fc4a5219f7c4dd81271e534b6be3ea060c06768b8d6abdacda10fe90bf2750ea'),
    (0x80092D10,0x80092E14,'25e0eb7687fcca1a9d82ce2c8788651b7b7b7c715fa943274854bd4cd8c5e906'),
    (0x800A9364,0x800A93AC,'dd0b66f3483a36736c812028432e878124f718309a313e03d6093a7ee2e0b09f'),
    (0x8009C70C,0x8009C780,'e4eaf965033e414fe876b90d236a6ae9e79199171b8601270dc4798d7008d07d'),
    (0x800B7AB0,0x800B7ADC,'697480d04b906d01bca642ba9bf72ff475ee84c9640f58d5274be4735bc9b947'),
    (0x8010AF58,0x8010B030,'97f56cd0d5e29f6c791790531029deb1ce55415217329a3e1d42b1497880ca12'),
    (0x8009C384,0x8009C3D0,'1d2ff0e947ac76c27913e319506be74da4cab34b6cee4db2703662a45ff758e1'),
)
REFERENCE_FUNCTIONS = {
    'mPr_GetForeingerAnimalMail':(360,'e52db84f05b3eeddb0bc4fb2658a2bd9528ab4a1515db932d276d88956607ff3'),
    'mPr_SendForeingerAnimalMail':(156,'ecb310217d103a0e450730000121b1baa25e48fbb2fadb9eec9f43fafb527045'),
}
BODY_FIELDS = ((0,2),(3,),(2,),(0,2),(3,),(0,2),(0,3),(2,),(2,),
               (0,2),(2,3),(2,),(2,),(2,),(0,2),(0,2),(2,),(0,3))
TOWN_FOOTERS = (0xFD,0xFF,0x100,0x102,0x10D)


def fields(name,number,*,native=False):
    if number not in TEMPLATES or name not in ('super','mail','ps'):
        raise ValueError('Unknown departed-villager template')
    if name == 'super': return {3} if native else set()
    if name == 'ps': return {1,2} if number in TOWN_FOOTERS else {1}
    return set(BODY_FIELDS[number-0xFC])|({0} if native and number in (0x100,0x107) else set())


def verify_code(code):
    for start,end,digest in GUARDS:
        if sha256(code[start-CODE_RAM:end-CODE_RAM]) != digest:
            raise ValueError(f'Changed native departed-villager function/data at {start:08X}')


def verify_templates(rom,catalog,root=ROOT):
    import mail_creator_catalog as creator_catalog
    rom = verified_rom(rom);verify_code(by_vrom(rom)[CODE_VROM].extract(rom))
    catalog_id = creator_catalog.identity(catalog)
    at = 0x1060+0x8002C970-0x80025C60
    if sha256(rom[at:at+0xE8]) != 'bebe6ab1df04e185b55ed2719392f11a4e9c2e85c443f5771d95eabad1105de0':
        raise ValueError('Changed original departed-villager RNG')
    native = {b.name:b.entries() for b in banks(rom) if b.name in ('super','mail','ps')}
    installed = parse(catalog)[1]
    rel = (root/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
    symbols = (root/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_text()
    if sha256(rel) != '29306a927eee861b073c571408393f99cb384048684eee4bff3d219725429837':
        raise ValueError('Changed supplied departed-villager executable')
    for name,expected in REFERENCE_FUNCTIONS.items():
        value = symbol_data(rel,symbols,name)
        if (len(value),sha256(value)) != expected: raise ValueError('Changed departed-villager reference function')
    decoder = root/'local/ac-decomp/tools/msg_tool.py'
    if sha256(decoder.read_bytes()) != DECODER_SHA256: raise ValueError('Changed English mail decoder')
    tables = decoder_tables(decoder);rows = []
    directory = root/'build/gamecube/files/forest_1st.arc.unpacked/data'
    for name in ('super','mail','ps'):
        data = (directory/(name+'_data.bin')).read_bytes();table = (directory/(name+'_data_table.bin')).read_bytes()
        if (sha256(data),sha256(table)) != BANK_HASHES[name]: raise ValueError('Changed departed-villager reference bank')
        reference = Bank(name,0,0,data,table).entries()
        for number in TEMPLATES:
            value = transcode(reference[number],tables,extended_glyphs=catalog_id==4)
            if (installed[name][number] != value or template_fields(value,extended_glyphs=catalog_id==4) != fields(name,number)
                    or template_fields(native[name][number]) != fields(name,number,native=True)):
                raise ValueError('Changed departed-villager text or field identity')
            rows.append({'id':f'{name}:{number:04X}','source_sha256':sha256(native[name][number]),
                         'reference_sha256':sha256(reference[number]),'encoded_sha256':sha256(value),
                         'bytes':len(value),'fields':sorted(fields(name,number))})
    return {'catalog':catalog_id,'classic_templates':list(TEMPLATES),'parts':rows,'reference_functions':REFERENCE_FUNCTIONS}


def patch(original,loader):
    if (len(original) != END-START or sha256(original[:POST-START]) != GUARDS[0][2]
            or sha256(original[POST-START:]) != GUARDS[1][2]):
        raise ValueError('Changed departed-villager creator or delivery')
    if type(loader) is not int or loader&3 or not MODULE_RAM+0x300 <= loader < MODULE_RAM+LINKED_LIMIT:
        raise ValueError('Departed-villager loader must be inside resident code')
    words = [0x27BDFFD0,0xAFBF002C,0x10C00017,0x30C90001,0x15200015,0x3408444D,
             0xA7A80018,0x94C80000,0xA7A8001A,0x94C80002,0xA7A8001C,
             0x94C80004,0xA7A8001E,0x94C80006,0xA7A80020,0xA3A00022,
             0x340800FD,0xA3A80023,0x27A60018,0x00003825,0xAFA00010,0xAFA00014,
             0x0C000000|((loader>>2)&0x03FFFFFF),0,0x10000002,0,
             0x00001025,0x8FBF002C,0x03E00008,0x27BD0030]
    out = bytearray(original)
    out[:POST-START] = struct.pack('>'+str(len(words))+'I',*words).ljust(POST-START,b'\0')
    gate = (0x24844570,0x8FA50028,0x0C000000|((START>>2)&0x03FFFFFF),0x8FA6001C,
            0x10400008,0x00402025,0x0C02DA8F,0x00002825,0x10400004,0x8FA4001C,
            0x0C02DEAC,0,0)
    out[0x800B9E00-START:0x800B9E34-START] = struct.pack('>13I',*gate)
    return bytes(out)


def install(rom,replacements,additions,module):
    import mail_creator_catalog as creator_catalog
    rom = verified_rom(rom)
    if not module or not module.get('npc_mail_loader',{}).get('overlay',{}).get('departed_letters'):
        raise ValueError('Departed letters require the verified extended system creator')
    if any(v not in additions for v in (MODULE_VROM,CREATOR_VROM,0x03000000)):
        raise ValueError('Missing departed-villager module, creator, or catalogue')
    verify_configuration(additions[MODULE_VROM],additions[CREATOR_VROM],module)
    original = by_vrom(rom)[CODE_VROM].extract(rom)
    code = bytearray(replacements.get(CODE_VROM,original));verify_code(code)
    loader = int(module['symbols']['af_npc_mail_load'],16)
    if code[MOM_START-CODE_RAM:MOM_END-CODE_RAM] != mother_patch(original[MOM_START-CODE_RAM:MOM_END-CODE_RAM],loader):
        raise ValueError('Departed letters require complete installed Mom-letter integration')
    evidence = verify_templates(rom,creator_catalog.resource(additions,module))
    value = patch(code[START-CODE_RAM:END-CODE_RAM],loader)
    code[START-CODE_RAM:END-CODE_RAM] = value
    replacements[CODE_VROM] = bytes(code)
    return {**evidence,'loader_ram':f'{loader:08X}','patch_sha256':sha256(value),
            'native_guards':GUARDS,'new_resident_bytes':0,'wrapper_stack_bytes':48,
            'status':'Complete departed letters installed; remembered villager cleared only after successful receipt'}


def verify_installation(built,native,module,report):
    import mail_creator_catalog as creator_catalog
    files = by_vrom(built)
    verify_configuration(files[MODULE_VROM].extract(built),files[CREATOR_VROM].extract(built),module)
    creator_catalog.verify_installation(built,module,report)
    if not module['npc_mail_loader']['overlay'].get('departed_letters'):
        raise ValueError('Departed-villager dispatcher is not installed')
    original = by_vrom(native)[CODE_VROM].extract(native);verify_code(original)
    expected = patch(original[START-CODE_RAM:END-CODE_RAM],int(module['symbols']['af_npc_mail_load'],16))
    actual = files[CODE_VROM].extract(built)
    if (actual[START-CODE_RAM:END-CODE_RAM] != expected or report['patch_sha256'] != sha256(expected)
            or report['classic_templates'] != list(TEMPLATES)):
        raise ValueError('Complete departed-villager creation or delivery is not installed')
    restored = bytearray(actual);restored[START-CODE_RAM:END-CODE_RAM] = original[START-CODE_RAM:END-CODE_RAM]
    verify_code(restored)
