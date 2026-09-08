"""Complete Mom letters through the existing synchronous cartridge creator."""

from pathlib import Path
import struct

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,verified_rom
from audit_mail_templates import template_fields
from gc_names import symbol_data
from gc_text import decoder_tables
from mail_catalog import VROM as CATALOG_VROM,parse,verify_registered
from mail_reference import BANK_HASHES,DECODER_SHA256,transcode
from mail_view_patch import install as install_reader
from npc_mail_loader import VROM as CREATOR_VROM,verify_configuration
from runtime_layout import MODULE_RAM,MODULE_VROM,LINKED_LIMIT
from textbanks import Bank,banks

ROOT = Path(__file__).resolve().parents[1]
START,POST,END = 0x800B8FB8,0x800B9038,0x800B9170
STAGING = 0x80144570
TEMPLATES = (*range(0x12C,0x182),0x184,0x185,*range(0x18A,0x1A4))
UNAVAILABLE = (0x136,)
COMPLETE = tuple(i for i in TEMPLATES if i not in UNAVAILABLE)
CODE_GUARDS = (
    (0x800B8F20,START,'5b78d0446a96d13a7e5692c637ceb0e17114a309fd2421190fbcc4fe4207d678'),
    (START,END,'b6d54b6de1def80ab2adbdbb8cfbc362eb9142b0e6d19c54b47e64bbae0a3c76'),
    (END,0x800B9350,'068c5afe089e352cee5149f2c02e7345cfd9637b825bc9ea12d788cbab56982d'),
    (0x800B94E0,0x800B9704,'49199a7d21e47c37e891e3edd39c9342b54234e3bb7edaeafdefaa1076956ff2'),
    (0x800B97F8,0x800B996C,'065f3e497b9029f686a60b082e57df8296132a3cbd3251583b04bc231de00e48'),
    (0x800B996C,0x800B9C34,'90a1a63a48af861114a1a60a82d98e8efd759e9d876705436a95d8372c832cac'),
    (0x8009C384,0x8009C3D0,'1d2ff0e947ac76c27913e319506be74da4cab34b6cee4db2703662a45ff758e1'),
    (0x8009C4A0,0x8009C4D0,'57889df1b13158baf0de0b816f9ad2302459fc1a4a2288debd3b9e45c2df795d'),
)
REFERENCE_FUNCTIONS = {
    'mPr_GetMotherMail':(136,'9ebbb25a3bc66e0d11f396a60925a9a98b051fb66f9badac4a031a3f9d4fe6e0'),
    'mPr_SendMotherMailPost':(260,'8fbcf7252d8e9675e869cb249e13e2469f2ced2bfa1d507f7fcbf87ce5d25cb4'),
    'mPr_SendMotherMailDate':(528,'f03294a7ac0c1b8f9dd3c2c8aad7c63402d9d4e0ea7cbd68cfab3f037310925b'),
    'mPr_GetMotherMailMonthlyData':(484,'bc40936e6ba5341db5b38804009cd72dc316fb8171860e8440cecf786f41951a'),
    'mPr_GetMotherMailNormalData':(340,'e5b34cb8e89fbaea17b12b735da5d53692ff283b9f7991a4f99a109ac4ef929e'),
}


def verify_code(code):
    for start,end,digest in CODE_GUARDS:
        if sha256(code[start-CODE_RAM:end-CODE_RAM]) != digest:
            raise ValueError(f'Changed native Mom-letter function at {start:08X}')


def verify_templates(rom,catalog,root=ROOT):
    rom = verified_rom(rom)
    verify_code(by_vrom(rom)[CODE_VROM].extract(rom))
    if verify_registered(catalog)['catalog'] != 2:
        raise ValueError('Mom letters require unchanged immutable catalogue two')
    installed = parse(catalog)[1]
    native = {b.name:b.entries() for b in banks(rom) if b.name in ('super','mail','ps')}
    rel = (root/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
    symbols = (root/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_text()
    if sha256(rel) != '29306a927eee861b073c571408393f99cb384048684eee4bff3d219725429837':
        raise ValueError('Changed supplied Mom-letter executable')
    for name,expected in REFERENCE_FUNCTIONS.items():
        data = symbol_data(rel,symbols,name)
        if (len(data),sha256(data)) != expected:
            raise ValueError('Changed English Mom-letter selection or metadata reference')
    decoder = root/'local/ac-decomp/tools/msg_tool.py'
    if sha256(decoder.read_bytes()) != DECODER_SHA256:
        raise ValueError('Changed English Mom-letter decoder')
    tables = decoder_tables(decoder)
    directory = root/'build/gamecube/files/forest_1st.arc.unpacked/data'
    rows = []
    for name in ('super','mail','ps'):
        data = (directory/(name+'_data.bin')).read_bytes()
        table = (directory/(name+'_data_table.bin')).read_bytes()
        if (sha256(data),sha256(table)) != BANK_HASHES[name]:
            raise ValueError('Changed supplied Mom-letter text bank')
        reference = Bank(name,0,0,data,table).entries()
        for number in TEMPLATES:
            row = {'id':f'{name}:{number:04X}','source_sha256':sha256(native[name][number]),
                   'reference_sha256':sha256(reference[number])}
            if template_fields(native[name][number]):
                raise ValueError('Unexpected native Mom-letter free-string field')
            try:
                value = transcode(reference[number],tables)
            except ValueError as error:
                if name != 'mail' or number != 0x136 or 'GC D0' not in str(error): raise
                if installed[name][number] is not None:
                    raise ValueError('Unsupported Mom letter must remain explicitly unavailable')
                row['unavailable'] = str(error)
            else:
                if value != installed[name][number] or template_fields(value):
                    raise ValueError('Changed complete Mom-letter part or field identities')
                row.update(encoded_sha256=sha256(value),bytes=len(value))
            rows.append(row)
    return {'parts':rows,'classic_templates':list(TEMPLATES),'complete_templates':list(COMPLETE),
            'unavailable_templates':list(UNAVAILABLE),'reference_functions':REFERENCE_FUNCTIONS}


def patch(original,loader):
    if len(original) != END-START or sha256(original) != CODE_GUARDS[1][2]:
        raise ValueError('Changed original Mom-letter creator or delivery')
    if type(loader) is not int or loader&3 or not MODULE_RAM+0x300 <= loader < MODULE_RAM+LINKED_LIMIT:
        raise ValueError('Mom-letter loader must be inside resident code')
    # The 12-byte stack descriptor shares the ordinary animal argument slot.
    # Its marker (FE) cannot be a valid native personality (0..5).
    words = [0x27BDFFD0,0xAFBF002C,0x8FA80040,0x2D0101A4,0x10200014,
             0x2CE10040,0x10200012,0x3C094146,0x35294D4F,0xAFA90018,
             0xA7A8001C,0xA7A6001E,0xA3A70020,0xA3A00021,0xA3A00022,
             0x340900FE,0xA3A90023,0x27A60018,0x00003825,0xAFA00010,
             0xAFA00014,0x0C000000|((loader>>2)&0x03FFFFFF),0,0x10000002,0,
             0x00001025,0x8FBF002C,0x03E00008,0x27BD0030,0,0,0]
    out = bytearray(original)
    out[:POST-START] = struct.pack('>32I',*words)
    mailbox = [0x1040001F,0x8FA30028,0x8FA80030,0x00034880,0x01234821,
               0x000948C0,0x01234821,0x00094880,0x01092021,0x24840478,
               0x0C02719F,0x00402825]
    out[0x800B90DC-START:0x800B910C-START] = struct.pack('>12I',*mailbox)
    struct.pack_into('>2I',out,0x800B9148-START,0x10400004,0x00402025)
    return bytes(out)


def install(rom,replacements,additions,module):
    rom = verified_rom(rom)
    if not module or not module.get('npc_mail_loader',{}).get('overlay',{}).get('mother_letters'):
        raise ValueError('Mom letters require the verified system creator variant')
    if any(vrom not in additions for vrom in (MODULE_VROM,CREATOR_VROM,CATALOG_VROM)):
        raise ValueError('Mom letters require the installed module, creator, and catalogue')
    binary = additions[MODULE_VROM]
    verify_configuration(binary,additions[CREATOR_VROM],module)
    baseline = bytearray(binary);baseline[56:0x88] = bytes(0x88-56)
    if sha256(baseline) != module['module_sha256'] or module['source_sha256'] != sha256(rom):
        raise ValueError('Changed resident module for Mom letters')
    reader = {}
    install_reader(rom,reader,{MODULE_VROM:bytes(baseline)},module,snapshots=True)
    if any(replacements.get(vrom) != data for vrom,data in reader.items()):
        raise ValueError('Mom letters require the installed complete snapshot reader')
    evidence = verify_templates(rom,additions[CATALOG_VROM])
    code = bytearray(replacements.get(CODE_VROM,by_vrom(rom)[CODE_VROM].extract(rom)))
    verify_code(code)
    loader = int(module['symbols']['af_npc_mail_load'],16)
    if loader >= MODULE_RAM+module['linked_bytes']:
        raise ValueError('Mom-letter loader exceeds linked resident code')
    value = patch(code[START-CODE_RAM:END-CODE_RAM],loader)
    code[START-CODE_RAM:END-CODE_RAM] = value
    replacements[CODE_VROM] = bytes(code)
    return {**evidence,'loader_ram':f'{loader:08X}','patch_sha256':sha256(value),
            'native_guards':CODE_GUARDS,'new_resident_bytes':0,'creator_stack_bytes':48,
            'status':'Complete supported Mom letters installed; one glyph row, gameplay, and save acceptance remain'}


def verify_installation(built,native,module,report):
    files = by_vrom(built)
    verify_configuration(files[MODULE_VROM].extract(built),files[CREATOR_VROM].extract(built),module)
    if not module['npc_mail_loader']['overlay'].get('mother_letters'):
        raise ValueError('Mom-letter dispatch is not installed')
    original = by_vrom(native)[CODE_VROM].extract(native)
    verify_code(original)
    expected = patch(original[START-CODE_RAM:END-CODE_RAM],int(module['symbols']['af_npc_mail_load'],16))
    actual = files[CODE_VROM].extract(built)
    if (actual[START-CODE_RAM:END-CODE_RAM] != expected or report['patch_sha256'] != sha256(expected)
            or report['complete_templates'] != list(COMPLETE)):
        raise ValueError('Mom-letter creation or publication gate is not installed')
    restored = bytearray(actual);restored[START-CODE_RAM:END-CODE_RAM] = original[START-CODE_RAM:END-CODE_RAM]
    verify_code(restored)
