"""Complete renewal delivery with guarded native ownership and relocation."""

from dataclasses import dataclass
import json
from pathlib import Path
import re
import struct

from aflib import CODE_RAM,CODE_VROM,by_vrom,replace_dma,sha256
from leaflet_dates import ACTORS,source,patched
from mail_generate_probe import validate as validate_creator
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM,MODULE_VROM,LINKED_LIMIT,RESERVATION

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ACTORS['renewal']
RAM,VROM,RELOCATION = NATIVE.ram,NATIVE.vrom,NATIVE.relocation
PREFIX_BYTES,NATIVE_TEXT,LIMIT = NATIVE.file_bytes,NATIVE.sections[0],0x3000
NEW_VROM,NEW_RELOCATION = 0x03700000,0x03708000
METADATA = 0x801011B0
METADATA_BYTES = bytes.fromhex('0084d1800084e000809583b08095923000000000809590400000000000000000')
KINDS = {'32':2,'26':4,'HI16':5,'LO16':6}
NATIVE_IMPORTS = {
    'af_renewal_save':0x80126EA0,'af_renewal_malloc':0x8009BFC0,'af_renewal_free':0x8009C040,
    'af_renewal_house_player':0x80094C10,'af_renewal_working_player':0x800816C0,
    'af_renewal_free_mail':0x8009C534,'af_renewal_clear_mail':0x8009C384,
    'af_renewal_copy_id':0x800B79E0,'af_renewal_copy_mail':0x8009C67C,
}
DATA_IMPORTS = {'af_renewal_save':0xF980,'af_mail_generation_capital':4}
CODE_GUARDS = (
    (0x80056E88,0x80057274,'fd0ee1ba6090a1fe12661f1c521b9a6da56516e2e31312332ee1d99bc2e7cdbf'),
    (0x800578E0,0x80057940,'6f975d4f06b43143adb1cd0ed21677684b2384cfcbc5e80e020944599a7f3883'),
    (0x80057940,0x80057A8C,'9ad2bc856a8c2d20f3859b9261735101595e446e3b26b85ef68fa21ec6422852'),
    (0x80057E24,0x80057FD0,'e779de1b8597a4a44c879f26269ce4246a4590f7a51854ac2808fbcc596ff402'),
    (0x8007D318,0x8007D36C,'18e838e8d94bdedb0bb5b0852ab6420514c509983418e36f58bed8b7e2b58f78'),
    (0x800816C0,0x8008172C,'6a6e5cdfcb5b87ee182c8b7651a16657ead882f59708aa98493baf3aa99ed049'),
    (0x80094C10,0x80094C44,'55bffc7c18ebecca5d26540777b718ac4678f6dbe7414f770315a725247fe71b'),
    (0x8009BFC0,0x8009C040,'e7fc6dbc77fda4e45e904bc9334f29fa4dc3849df9c8406952d526777d0142d8'),
    (0x8009C040,0x8009C0C0,'36460dd497306abd9d051d1662ac69d9828eb6169bf35944f8233fd69024ec9a'),
    (0x8009C344,0x8009C384,'1cbcfab16c9b0b9bf50234f8cff8215025bf814fc33d61879696800a3e90db96'),
    (0x8009C384,0x8009C3D0,'1d2ff0e947ac76c27913e319506be74da4cab34b6cee4db2703662a45ff758e1'),
    (0x8009C414,0x8009C438,'e5b0400e6ced8d6da09d67da8b80e96142f377308af59a33be43b9cb3b4e8dd7'),
    (0x8009C534,0x8009C5A4,'db6019924a8091970902074d4e0399035fa8360beefede44eece4d0a529a82fd'),
    (0x8009C67C,0x8009C69C,'a400c949f99131dd1a1cd3a9a6363728182d1d9a903f17e4eeda11c8adec1ab9'),
    (0x800B79E0,0x800B7A00,'dc38f2ea30816da9b014e027664a2c967ca61aa4270eb705ea8aa2eae0b3be62'),
)
# The original caller must retain the notification on zero from the creator.
# Both return paths still execute the original frame/return epilogue.
GATE = (
    (0x300,0x3C028012,0x1040000E),(0x304,0x24426EA0,0),
    (0x308,0x244B7FFF,0x3C0B8013),(0x30C,0x916B6D73,0x916B5C12),
    (0x310,0x24417FFF,0x3C018013),(0x314,0x316CFFEF,0x316CFFEF),
    (0x318,0xA02C6D73,0xA02C5C12),
)


def source_hashes():
    names = ['overlays/mail_generation/'+name for name in
             ('renewal_actor.c','renewal_actor.h','renewal_actor.s','renewal_actor.ld',
              'leaflet.h','generate.h')]
    names += ['runtime/mail/'+name for name in ('catalog.h','format.h','record.h')]
    return {name:sha256((ROOT/name).read_bytes()) for name in names}


def verify_code(code):
    for start,end,digest in CODE_GUARDS:
        if sha256(code[start-CODE_RAM:end-CODE_RAM]) != digest:
            raise ValueError(f'Changed renewal ownership/mail helper {start:08X}')


def native_sources(rom):
    data,reloc = source(rom,'renewal');files = by_vrom(rom)
    code = files[CODE_VROM].extract(rom)
    verify_code(code)
    if (files[RELOCATION].index != files[VROM].index+1
            or code[METADATA-CODE_RAM:METADATA-CODE_RAM+32] != METADATA_BYTES):
        raise ValueError('Changed native renewal ownership or adjacent relocation row')
    return data,reloc


def imports_for(module):
    imports = dict(NATIVE_IMPORTS)
    value = int(module.get('symbols',{}).get('af_mail_generation_capital','0'),16)
    used = module.get('linked_bytes',0)
    if (type(used) is not int or not 0x300 < used <= LINKED_LIMIT or value&3
            or not MODULE_RAM+0x300 <= value <= MODULE_RAM+used-4):
        raise ValueError('Renewal capitalization import is outside the resident module')
    imports['af_mail_generation_capital'] = value
    return imports


def creator_image(code,report,module):
    validate_creator(code,report,module,leaflets=True)
    output = bytearray(code)
    for at in report['jump_relocations']:
        word = struct.unpack_from('>I',code,at)[0]
        target = 0x80000000|((word&0x3FFFFFF)<<2)
        target += RAM+PREFIX_BYTES-report['base']
        struct.pack_into('>I',output,at,(word&0xFC000000)|((target&0xFFFFFFF)>>2))
    return bytes(output)


def patch_prefix(rom,module,symbols):
    native,reloc = native_sources(rom)
    expected = bytearray(patched(rom,'renewal',module)[0])
    changes = [(0,0x27BDFEB8,0x08000000|(((RAM+symbols['af_renewal_deliver'])&0xFFFFFFF)>>2)),
               (4,0xAFBF0044,0),*GATE]
    original_rows = struct.unpack_from('>23I',reloc,20)
    for at,before,after in changes:
        if struct.unpack_from('>I',native,at)[0] != before or any(row&0xFFFFFF == at for row in original_rows):
            raise ValueError('Renewal entry/failure gate differs or overlaps a native relocation')
        struct.pack_into('>I',expected,at,after)
    return bytes(expected)


def elf_inventory(text):
    result = []
    for line in text.splitlines():
        if 'R_MIPS_' not in line: continue
        match = re.fullmatch(r'\s*([0-9a-fA-F]+)\s+[0-9a-fA-F]+\s+R_MIPS_(32|26|HI16|LO16)\s+([0-9a-fA-F]+)\s+(\S+)\s*',line)
        if not match: raise ValueError('Unsupported renewal ELF relocation: '+line)
        result.append([int(match[1],16)-RAM,KINDS[match[2]],int(match[3],16),match[4]])
    return result


def relocation_bytes(native_reloc,inventory,imports,creator,size):
    rows = []
    for entry in struct.unpack_from('>23I',native_reloc,20):
        section,kind,offset = entry>>30,(entry>>24)&63,entry&0xFFFFFF
        if section not in (1,2): raise ValueError('Unexpected native renewal relocation section')
        rows.append(0x40000000|(kind<<24)|(offset+(NATIVE_TEXT if section == 2 else 0)))
    rows.append(0x44000000)  # New entry trampoline, with no original row.
    rows += [0x44000000|(PREFIX_BYTES+at) for at in creator['jump_relocations']]
    for at,kind,target,name in inventory:
        if RAM <= target < RAM+size:
            rows.append(0x40000000|(kind<<24)|at)
        elif (imports.get(name) != target or
              (kind not in (5,6) if name in DATA_IMPORTS else kind != 4)):
            raise ValueError('Unapproved renewal external relocation')
    length = (24+len(rows)*4+15)&~15
    return (struct.pack('>5I',size,0,0,0,len(rows))+struct.pack('>'+str(len(rows))+'I',*rows)
            +bytes(length-24-len(rows)*4)+struct.pack('>I',length))


@dataclass(frozen=True)
class ActorImage:
    ram: int
    resident_bytes: int
    sections: tuple


def validate(rom,data,reloc,report,module,creator_code,creator):
    _,native_reloc = native_sources(rom);imports = imports_for(module)
    embedded = creator_image(creator_code,creator,module)
    if (report.get('version') != 1 or report.get('ram') != RAM or report.get('bytes') != len(data)
            or report.get('overlay_sha256') != sha256(data) or report.get('relocation_bytes') != len(reloc)
            or report.get('relocation_sha256') != sha256(reloc) or report.get('sources') != source_hashes()
            or report.get('imports') != imports or report.get('module_sha256') != module['module_sha256']
            or report.get('creator') != creator or report.get('creator_sha256') != sha256(creator_code)):
        raise ValueError('Stale or changed complete renewal actor')
    start = PREFIX_BYTES+len(embedded)
    if not start < len(data) <= LIMIT or len(data)&15 or len(reloc) > 4096:
        raise ValueError('Renewal image exceeds its guarded general-heap budget')
    symbols = report.get('symbols',{})
    entry = symbols.get('af_renewal_deliver')
    if type(entry) is not int or entry&3 or not start <= entry < len(data):
        raise ValueError('Renewal entry is outside appended adapter code')
    if data[:PREFIX_BYTES] != patch_prefix(rom,module,symbols) or data[PREFIX_BYTES:start] != embedded:
        raise ValueError('Unapproved renewal native prefix or embedded creator change')
    seen,jumps,high = set(),set(),{}
    inventory = report.get('elf_relocations',[])
    for row in inventory:
        if (not isinstance(row,list) or len(row) != 4 or any(type(row[i]) is not int for i in range(3))
                or not isinstance(row[3],str)):
            raise ValueError('Malformed renewal ELF relocation inventory')
        at,kind,target,name = row
        if at&3 or not start <= at <= len(data)-4 or at in seen or kind not in (4,5,6):
            raise ValueError('Invalid or repeated renewal adapter relocation')
        seen.add(at);word = struct.unpack_from('>I',data,at)[0]
        if kind == 4:
            actual = 0x80000000|((word&0x3FFFFFF)<<2)
            if word>>26 not in (2,3): raise ValueError('Renewal jump relocation is not code')
            if RAM <= target < RAM+len(data):
                if not RAM+PREFIX_BYTES <= actual < RAM+len(data):
                    raise ValueError('Renewal adapter jump leaves appended code')
            elif target != actual or imports.get(name) != actual or name in DATA_IMPORTS:
                raise ValueError('Renewal external jump differs from approved helper')
            jumps.add(at)
        else:
            if name not in DATA_IMPORTS or imports.get(name) != target:
                raise ValueError('Unapproved renewal fixed data import')
            if kind == 5:
                register = (word>>16)&31
                if word>>26 != 15 or register in high: raise ValueError('Invalid renewal fixed data high')
                high[register] = word,name
            else:
                register = (word>>21)&31
                if register not in high or word>>26 not in (9,35,43):
                    raise ValueError('Missing renewal fixed data high')
                upper,upper_name = high.pop(register)
                actual = ((upper&65535)<<16)+(word&65535)-(65536 if word&32768 else 0)
                if upper_name != name or not target <= actual < target+DATA_IMPORTS[name]:
                    raise ValueError('Renewal fixed data instructions leave approved object')
    if high: raise ValueError('Unpaired renewal fixed data relocation')
    scanned = {at for at in range(start,len(data),4) if struct.unpack_from('>I',data,at)[0]>>26 in (2,3)}
    if scanned != jumps: raise ValueError('Untracked renewal adapter absolute jump')
    if reloc != relocation_bytes(native_reloc,inventory,imports,creator,len(data)):
        raise ValueError('Renewal relocation inventory differs from complete merge')
    spec = ActorImage(RAM,len(data),struct.unpack_from('>5I',reloc))
    for base in (MODULE_RAM+RESERVATION,0x802F8010,(0x80400000-len(data))&~15):
        relocate_verified_data(spec,data,reloc,base)
    return spec


def metadata(size):
    value = bytearray(METADATA_BYTES)
    struct.pack_into('>4I',value,0,NEW_VROM,NEW_VROM+size,RAM,RAM+size)
    return bytes(value)


def load(directory):
    return ((directory/'overlay.bin').read_bytes(),(directory/'relocation.bin').read_bytes(),
            json.loads((directory/'overlay.json').read_text()),(directory/'creator-original.bin').read_bytes())


def verify_installation(rom,native,report,module,creator_code):
    files = by_vrom(rom)
    if NEW_VROM not in files or NEW_RELOCATION not in files or VROM in files or RELOCATION in files:
        raise ValueError('Missing complete renewal DMA relocation')
    if files[NEW_VROM].index != by_vrom(native)[VROM].index or files[NEW_RELOCATION].index != files[NEW_VROM].index+1:
        raise ValueError('Renewal loader lost its original adjacent DMA rows')
    data,reloc = files[NEW_VROM].extract(rom),files[NEW_RELOCATION].extract(rom)
    spec = validate(native,data,reloc,report,module,creator_code,report['creator'])
    code = files[CODE_VROM].extract(rom);verify_code(code)
    if code[METADATA-CODE_RAM:METADATA-CODE_RAM+32] != metadata(len(data)):
        raise ValueError('Installed renewal ownership metadata differs')
    return spec


def install(rom,replacements,additions,relocations,module,directory):
    from mail_view_patch import install as install_reader
    from runtime_module import runtime_source_hashes,verify_test_module
    from leaflet_letters import verify_templates
    if (not module or MODULE_VROM not in additions or module.get('source_sha256') != sha256(rom)
            or module.get('runtime_sources') != runtime_source_hashes(ROOT/'runtime')):
        raise ValueError('Renewal delivery requires the current verified resident module')
    verify_templates(rom,additions.get(0x03000000,b''))
    binary = bytearray(additions[MODULE_VROM])
    if len(binary) != RESERVATION or struct.unpack_from('>I',binary,68)[0] != 0x03000000:
        raise ValueError('Renewal delivery requires the configured full mail reader')
    binary[56:0x88] = bytes(0x88-56)
    if sha256(binary) != module['module_sha256']:
        raise ValueError('Renewal resident code differs from verified imports')
    expected_reader = {}
    install_reader(rom,expected_reader,{MODULE_VROM:bytes(binary)},module,snapshots=True)
    if any(replacements.get(vrom) != data for vrom,data in expected_reader.items()):
        raise ValueError('Renewal delivery requires the complete installed snapshot reader')
    data,reloc,report,creator_code = load(directory)
    validate(rom,data,reloc,report,module,creator_code,report['creator'])
    original,original_reloc = patched(rom,'renewal',module)
    if (replacements.get(VROM) != original or replacements.get(RELOCATION,original_reloc) != original_reloc
            or any(v in mapping for v in (VROM,RELOCATION,NEW_VROM,NEW_RELOCATION)
                   for mapping in (additions,relocations))
            or any(v in replacements for v in (NEW_VROM,NEW_RELOCATION))):
        raise ValueError('Renewal delivery requires only the guarded date actor patch')
    code = bytearray(replacements.get(CODE_VROM,by_vrom(rom)[CODE_VROM].extract(rom)))
    verify_code(code);at = METADATA-CODE_RAM
    if code[at:at+32] != METADATA_BYTES: raise ValueError('Overlapping renewal ownership metadata patch')
    code[at:at+32] = metadata(len(data))
    changed = {**replacements,CODE_VROM:bytes(code),VROM:data,RELOCATION:reloc}
    moved = {**relocations,VROM:NEW_VROM,RELOCATION:NEW_RELOCATION}
    prospective = replace_dma(rom,changed,moved,additions)
    verify_test_module(prospective,module)
    verify_installation(prospective,rom,report,module,creator_code)
    replacements.update({CODE_VROM:bytes(code),VROM:data,RELOCATION:reloc})
    relocations.update({VROM:NEW_VROM,RELOCATION:NEW_RELOCATION})
    return {'overlay':report,'vrom':f'{NEW_VROM:08X}','relocation_vrom':f'{NEW_RELOCATION:08X}',
            'metadata':metadata(len(data)).hex(),'temporary_allocation_bytes':5471,
            'saved_layout_changed':False,'resident_growth_bytes':0,
            'status':'Complete renewal mailbox publication; normal scheduling, delivery, and hardware remain unverified'}
