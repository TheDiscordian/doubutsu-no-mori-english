"""Guarded native event-manager installation for complete sale/Redd letters."""

from dataclasses import dataclass
import json
from pathlib import Path
import re
import struct

from aflib import CODE_RAM,CODE_VROM,by_vrom,replace_dma,sha256
from event_leaflet_sources import evidence,HELPERS
from leaflet_dates import ACTORS,source,patched
from mail_generate_probe import validate as validate_creator
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM,MODULE_VROM,LINKED_LIMIT,RESERVATION

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ACTORS['event']
RAM,VROM,RELOCATION = NATIVE.ram,NATIVE.vrom,NATIVE.relocation
PREFIX_BYTES = NATIVE.file_bytes+NATIVE.sections[3]
LIMIT = 0xC000
NEW_VROM,NEW_RELOCATION = 0x03800000,0x03810000
METADATA = 0x80101310
METADATA_BYTES = bytes.fromhex('00850680008571008095b8b08096246000000000809622ec0000000000000000')
KINDS = {'32':2,'26':4,'HI16':5,'LO16':6}
NATIVE_IMPORTS = {
    'af_event_saved':0x80135C44,'af_event_init_flag':0x80135CE1,
    'af_event_native_sale_fields':0x8095BA60,'af_event_native_special_init':0x8095C37C,
    'af_event_native_save':0x8095BD8C,'af_event_native_destroy':0x8095BD7C,
}
DATA_IMPORTS = {'af_event_saved':156,'af_event_init_flag':1,'af_mail_generation_capital':4}
OWNED_DATA = {'af_event_pending':172,'af_event_work':5536,'af_event_count':4,'af_event_busy':4}
ENTRIES = ('af_event_sale_fields','af_event_register','af_event_retry','af_event_special_init',
           'af_event_save','af_event_destroy','af_event_capture')
CALLS = ((0x8095C05C,0x0C256E98,'af_event_sale_fields'),
         (0x8095C080,0x0C256E73,'af_event_register'),
         (0x8095BC48,0x0C256E73,'af_event_register'),
         (0x80961924,0x0C2570DF,'af_event_special_init'))
POINTERS = ((0x80962300,0x8095BD7C,'af_event_destroy'),(0x8096230C,0x8095BD8C,'af_event_save'))
GATE = ((0x8095C088,0x24020001,0),(0x8095C24C,0x24020001,0),(0x8095C494,0x24020001,0),
        (0x8096191C,0x15E10005,0x11E00005),(0x8096192C,0x3C018013,0),(0x80961930,0xA0205CE1,0))


def source_hashes():
    names = ['overlays/mail_generation/'+name for name in
             ('event_actor.c','event_actor.h','event_actor.s','event_actor.ld','event_leaflet.h','leaflet.h','generate.h')]
    return {name:sha256((ROOT/name).read_bytes()) for name in names}


def verify_code(code):
    for start,end,digest in HELPERS:
        if sha256(code[start-CODE_RAM:end-CODE_RAM]) != digest:
            raise ValueError('Changed native event letter helper')


def native_sources(rom):
    evidence(rom)
    data,reloc = source(rom,'event');files = by_vrom(rom)
    code = files[CODE_VROM].extract(rom)
    if (files[RELOCATION].index != files[VROM].index+1
            or code[METADATA-CODE_RAM:METADATA-CODE_RAM+32] != METADATA_BYTES):
        raise ValueError('Changed native event ownership or adjacent relocation row')
    return data,reloc


def imports_for(module):
    imports = dict(NATIVE_IMPORTS)
    value = int(module.get('symbols',{}).get('af_mail_generation_capital','0'),16)
    used = module.get('linked_bytes',0)
    if (type(used) is not int or not 0x300 < used <= LINKED_LIMIT or value&3
            or not MODULE_RAM+0x300 <= value <= MODULE_RAM+used-4):
        raise ValueError('Event capitalization import is outside the resident module')
    imports['af_mail_generation_capital'] = value
    return imports


def creator_image(code,report,module):
    validate_creator(code,report,module,event_leaflets=True)
    output = bytearray(code)
    for at in report['jump_relocations']:
        word = struct.unpack_from('>I',code,at)[0]
        target = 0x80000000|((word&0x3FFFFFF)<<2)
        target += RAM+PREFIX_BYTES-report['base']
        struct.pack_into('>I',output,at,(word&0xFC000000)|((target&0xFFFFFFF)>>2))
    return bytes(output)


def native_rows(reloc):
    text,data,_,_,count = struct.unpack_from('>5I',reloc)
    rows = []
    for entry in struct.unpack_from('>'+str(count)+'I',reloc,20):
        section,kind,at = entry>>30,(entry>>24)&63,entry&0xFFFFFF
        if section not in (1,2,3): raise ValueError('Invalid native event relocation section')
        rows.append(0x40000000|(kind<<24)|(at+(0,text,text+data)[section-1]))
    return rows


def patch_prefix(rom,module,symbols):
    native,reloc = native_sources(rom)
    output = bytearray(patched(rom,'event',module)[0])+bytes(NATIVE.sections[3])
    rows = {v&0xFFFFFF:(v>>24)&63 for v in native_rows(reloc)}
    changes = [(at,before,0x0C000000|(((RAM+symbols[name])&0xFFFFFFF)>>2),4) for at,before,name in CALLS]
    changes += [(at,before,RAM+symbols[name],2) for at,before,name in POINTERS]
    changes += [(at,before,after,None) for at,before,after in GATE]
    for address,before,after,kind in changes:
        at = address-RAM
        if struct.unpack_from('>I',native,at)[0] != before or rows.get(at) != kind:
            raise ValueError('Changed event caller, return gate, profile, or relocation')
        struct.pack_into('>I',output,at,after)
    return bytes(output)


def elf_inventory(text):
    rows = []
    for line in text.splitlines():
        if 'R_MIPS_' not in line: continue
        match = re.fullmatch(r'\s*([0-9a-fA-F]+)\s+[0-9a-fA-F]+\s+R_MIPS_(32|26|HI16|LO16)\s+([0-9a-fA-F]+)\s+(\S+)\s*',line)
        if not match: raise ValueError('Unsupported event ELF relocation: '+line)
        rows.append([int(match[1],16)-RAM,KINDS[match[2]],int(match[3],16),match[4]])
    return rows


def relocation_bytes(native_reloc,inventory,imports,creator,size):
    rows = native_rows(native_reloc)
    rows += [0x44000000|(PREFIX_BYTES+at) for at in creator['jump_relocations']]
    for at,kind,target,name in inventory:
        if RAM <= target < RAM+size: rows.append(0x40000000|(kind<<24)|at)
        elif imports.get(name) != target or name not in DATA_IMPORTS or kind not in (5,6):
            raise ValueError('Unapproved event external relocation')
    length = (24+len(rows)*4+15)&~15
    return (struct.pack('>5I',size,0,0,0,len(rows))+struct.pack('>'+str(len(rows))+'I',*rows)
            +bytes(length-24-len(rows)*4)+struct.pack('>I',length))


@dataclass(frozen=True)
class ActorImage:
    ram: int
    resident_bytes: int
    sections: tuple


def validate(rom,data,reloc,report,module,creator_code,creator):
    if report.get('accent_mail') is not None:
        from accent_mail_overlay_profile import validate as validate_accent
        old,oldrel,previous,spec=validate_accent('event',data,reloc,report)
        validate(rom,old,oldrel,previous,module,creator_code,creator)
        return spec
    _,native_reloc = native_sources(rom);imports = imports_for(module)
    embedded = creator_image(creator_code,creator,module)
    if (report.get('version') != 1 or report.get('ram') != RAM or report.get('bytes') != len(data)
            or report.get('overlay_sha256') != sha256(data) or report.get('relocation_bytes') != len(reloc)
            or report.get('relocation_sha256') != sha256(reloc) or report.get('sources') != source_hashes()
            or report.get('imports') != imports or report.get('module_sha256') != module['module_sha256']
            or report.get('creator') != creator or report.get('creator_sha256') != sha256(creator_code)):
        raise ValueError('Stale or changed complete event actor')
    start = PREFIX_BYTES+len(embedded);end = report.get('text_bytes',0)
    if not start < end < len(data) <= LIMIT or len(data)&15 or end&15 or len(reloc) > 4096:
        raise ValueError('Invalid event image, text, or guarded heap budget')
    symbols = report.get('symbols',{})
    for name in ENTRIES:
        at = symbols.get(name)
        if type(at) is not int or at&3 or not start <= at < end:
            raise ValueError('Event adapter entry is outside appended code')
    ranges = []
    for name,size in OWNED_DATA.items():
        at = symbols.get(name)
        if type(at) is not int or at&3 or not end <= at <= len(data)-size or any(data[at:at+size]):
            raise ValueError('Event owned object is outside zero-initialized data')
        if any(at < b and a < at+size for a,b in ranges): raise ValueError('Overlapping event owned objects')
        ranges.append((at,at+size))
    if (RAM+symbols['af_event_work'])&15: raise ValueError('Misaligned event work')
    if data[:PREFIX_BYTES] != patch_prefix(rom,module,symbols) or data[PREFIX_BYTES:start] != embedded:
        raise ValueError('Unapproved event native prefix or embedded creator change')
    seen,jumps,high,used_high = set(),set(),{},set()
    inventory = report.get('elf_relocations',[])
    for row in inventory:
        if (not isinstance(row,list) or len(row) != 4 or any(type(row[i]) is not int for i in range(3))
                or not isinstance(row[3],str)):
            raise ValueError('Malformed event ELF relocation inventory')
        at,kind,target,name = row
        if at&3 or not start <= at < end or at in seen or kind not in (4,5,6):
            raise ValueError('Invalid or repeated event adapter relocation')
        seen.add(at);word = struct.unpack_from('>I',data,at)[0]
        if kind == 4:
            actual = 0x80000000|((word&0x3FFFFFF)<<2)
            if word>>26 not in (2,3) or not RAM <= actual < RAM+end:
                raise ValueError('Event jump leaves actor code')
            if name in imports:
                if name in DATA_IMPORTS or actual != target or imports[name] != target:
                    raise ValueError('Changed native event helper jump')
            elif name == 'af_event_leaflet_publish':
                if actual != RAM+PREFIX_BYTES+creator['symbols'][name] or target != actual:
                    raise ValueError('Changed complete event publication jump')
            elif name == '.text':
                if target != RAM or actual != RAM+symbols['af_event_capture']:
                    raise ValueError('Changed local event capture jump')
            elif name not in ENTRIES or actual != RAM+symbols[name] or target != actual:
                raise ValueError('Unapproved event internal helper jump')
            jumps.add(at)
        else:
            if name in DATA_IMPORTS: lower,upper = imports[name],imports[name]+DATA_IMPORTS[name]
            elif name in OWNED_DATA: lower,upper = RAM+symbols[name],RAM+symbols[name]+OWNED_DATA[name]
            else: raise ValueError('Unapproved event data reference')
            if target != lower: raise ValueError('Changed event data symbol')
            if kind == 5:
                register = (word>>16)&31
                if word>>26 != 15: raise ValueError('Invalid event data high instruction')
                high[register] = at,word,name
            else:
                register = (word>>21)&31
                if register not in high or word>>26 not in (9,32,33,35,36,37,40,41,43):
                    raise ValueError('Missing event data high instruction')
                high_at,high_word,high_name = high[register]
                actual = ((high_word&65535)<<16)+(word&65535)-(65536 if word&32768 else 0)
                if high_name != name or not lower <= actual < upper:
                    raise ValueError('Event data instruction leaves approved object')
                used_high.add(high_at)
    if {r[0] for r in inventory if r[1]==5} != used_high: raise ValueError('Unpaired event data relocation')
    scanned = {at for at in range(start,end,4) if struct.unpack_from('>I',data,at)[0]>>26 in (2,3)}
    if scanned != jumps: raise ValueError('Untracked event adapter absolute jump')
    if reloc != relocation_bytes(native_reloc,inventory,imports,creator,len(data)):
        raise ValueError('Event relocation inventory differs from complete merge')
    spec = ActorImage(RAM,len(data),struct.unpack_from('>5I',reloc))
    for base in (MODULE_RAM+RESERVATION,0x802F8010,(0x80400000-len(data))&~15):
        relocate_verified_data(spec,data,reloc,base)
    return spec


def metadata(size):
    result = bytearray(METADATA_BYTES)
    struct.pack_into('>4I',result,0,NEW_VROM,NEW_VROM+size,RAM,RAM+size)
    return bytes(result)


def load(directory):
    return ((directory/'overlay.bin').read_bytes(),(directory/'relocation.bin').read_bytes(),
            json.loads((directory/'overlay.json').read_text()),(directory/'creator-original.bin').read_bytes())


def verify_installation(rom,native,report,module,creator_code):
    files = by_vrom(rom)
    if NEW_VROM not in files or NEW_RELOCATION not in files or VROM in files or RELOCATION in files:
        raise ValueError('Missing complete event DMA relocation')
    if files[NEW_VROM].index != by_vrom(native)[VROM].index or files[NEW_RELOCATION].index != files[NEW_VROM].index+1:
        raise ValueError('Event loader lost its original adjacent DMA rows')
    data,reloc = files[NEW_VROM].extract(rom),files[NEW_RELOCATION].extract(rom)
    spec = validate(native,data,reloc,report,module,creator_code,report['creator'])
    code = files[CODE_VROM].extract(rom);verify_code(code)
    if code[METADATA-CODE_RAM:METADATA-CODE_RAM+32] != metadata(len(data)):
        raise ValueError('Installed event ownership metadata differs')
    return spec


def install(rom,replacements,additions,relocations,module,directory):
    from mail_view_patch import install as install_reader
    from runtime_module import runtime_source_hashes,verify_test_module
    from leaflet_letters import verify_templates
    if (not module or MODULE_VROM not in additions or module.get('source_sha256') != sha256(rom)
            or module.get('runtime_sources') != runtime_source_hashes(ROOT/'runtime')):
        raise ValueError('Event delivery requires the current verified resident module')
    verify_templates(rom,additions.get(0x03000000,b''))
    binary = bytearray(additions[MODULE_VROM])
    if len(binary) != RESERVATION or struct.unpack_from('>I',binary,68)[0] != 0x03000000:
        raise ValueError('Event delivery requires the configured full mail reader')
    if not struct.unpack_from('>I',binary,56)[0]: raise ValueError('Event sale letters require full item names')
    binary[56:0x88] = bytes(0x88-56)
    if sha256(binary) != module['module_sha256']: raise ValueError('Changed event resident imports')
    expected_reader = {}
    install_reader(rom,expected_reader,{MODULE_VROM:bytes(binary)},module,snapshots=True)
    if any(replacements.get(vrom) != data for vrom,data in expected_reader.items()):
        raise ValueError('Event delivery requires the complete installed snapshot reader')
    data,reloc,report,creator_code = load(directory)
    validate(rom,data,reloc,report,module,creator_code,report['creator'])
    original,original_reloc = patched(rom,'event',module)
    if (replacements.get(VROM) != original or replacements.get(RELOCATION,original_reloc) != original_reloc
            or any(v in mapping for v in (VROM,RELOCATION,NEW_VROM,NEW_RELOCATION) for mapping in (additions,relocations))
            or any(v in replacements for v in (NEW_VROM,NEW_RELOCATION))):
        raise ValueError('Event delivery requires only the guarded date actor patch')
    code = bytearray(replacements.get(CODE_VROM,by_vrom(rom)[CODE_VROM].extract(rom)))
    verify_code(code);at = METADATA-CODE_RAM
    if code[at:at+32] != METADATA_BYTES: raise ValueError('Overlapping event ownership metadata patch')
    code[at:at+32] = metadata(len(data))
    prospective = replace_dma(rom,{**replacements,CODE_VROM:bytes(code),VROM:data,RELOCATION:reloc},
                              {**relocations,VROM:NEW_VROM,RELOCATION:NEW_RELOCATION},additions)
    verify_test_module(prospective,module)
    verify_installation(prospective,rom,report,module,creator_code)
    replacements.update({CODE_VROM:bytes(code),VROM:data,RELOCATION:reloc})
    relocations.update({VROM:NEW_VROM,RELOCATION:NEW_RELOCATION})
    return {'overlay':report,'vrom':f'{NEW_VROM:08X}','relocation_vrom':f'{NEW_RELOCATION:08X}',
            'metadata':metadata(len(data)).hex(),'temporary_allocation_bytes':0,
            'saved_layout_changed':False,'saved_flag_semantics_extended':True,'resident_growth_bytes':0,
            'status':'Complete event publication hooks; native validation and normal save/scheduling remain unverified'}
