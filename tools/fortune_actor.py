"""Guard the complete Miko actor extension, native ownership, and relocations."""

from dataclasses import dataclass
import json
from pathlib import Path
import re
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, replace_dma, sha256
from fortune_slips import (RAM, VROM, RELOCATION, METADATA, METADATA_BYTES,
                           WORDS_HASH, verify_native)
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM, MODULE_VROM, LINKED_LIMIT, RESERVATION

ROOT = Path(__file__).resolve().parents[1]
NEW_VROM, NEW_RELOCATION = 0x03600000, 0x03608000
NATIVE_BYTES, PREFIX_BYTES, NATIVE_TEXT = 2992, 3008, 2848
INSTANCE_BYTES, LIMIT = 2400, 8192
PROFILE_SIZE, INIT_SLOT, GIVE_SLOT = 0xB2C, 0xB94, 0xBA8
NATIVE_IMPORTS = {
    'af_miko_private':0x80136FD8, 'af_miko_random':0x8002C9AC,
    'af_miko_malloc':0x8009BFC0, 'af_miko_free':0x8009C040,
    'af_miko_get_order':0x8007B49C, 'af_miko_set_order':0x8007B44C,
    'af_miko_clear_mail':0x8009C384, 'af_miko_set_recipient':0x8009C4A0,
    'af_miko_free_mail':0x8009C534, 'af_miko_copy_mail':0x8009C67C,
}
INTERNAL_IMPORTS = {'af_miko_original_init':0x809E5FA0,'af_miko_setup_action':0x809E6014}
RESIDENT_IMPORTS = ('af_mail_record_pack','af_mail_restore','af_mail_catalog_header_valid',
                    'af_mail_generation_capital')
DATA_IMPORTS = {'af_miko_private','af_mail_generation_capital'}
KINDS = {'32':2,'26':4,'HI16':5,'LO16':6}


def source_hashes():
    sources = ['overlays/mail_generation/'+name for name in
               ('generate.c','generate.h','fortune_slip.c','fortune_slip.h',
                'fortune_actor.c','fortune_actor.h','fortune_actor.s','fortune_actor.ld')]
    sources += ['runtime/mail/'+name for name in ('catalog.h','format.h','record.h')]
    return {name:sha256((ROOT/name).read_bytes()) for name in sources}


def native_sources(rom):
    verify_native(rom)
    files = by_vrom(rom)
    if files[RELOCATION].index != files[VROM].index+1:
        raise ValueError('Miko relocation must be the next DMA entry')
    # This controller owns both native D03D overlay paths and the nine actor
    # instances. Its unchecked overlay allocator requires our explicit limit.
    if sha256(files[0x8681F0].extract(rom)) != '460777a8c6d6b57e9c83a7c9f3efe02593fd01b75f9a4e108db5b9c2a54a18e3':
        raise ValueError('Changed native NPC allocator capacity evidence')
    code = files[CODE_VROM].extract(rom)
    at = 0x80057D3C-CODE_RAM
    if sha256(code[at:at+48]) != 'aef7ac2b327aedb17d1ee2eb6a32c30b51089835db4d9dedec0eb43f4d97cf33':
        raise ValueError('Changed native profile-sized instance initialization')
    return files[VROM].extract(rom),files[RELOCATION].extract(rom)


def imports_for(module):
    imports = dict(NATIVE_IMPORTS)
    for name in RESIDENT_IMPORTS:
        value = int(module.get('symbols',{}).get(name,'0'),16)
        if value&3 or not MODULE_RAM+0x300 <= value < MODULE_RAM+min(module['linked_bytes'],LINKED_LIMIT):
            raise ValueError('Miko import is outside the current resident module')
        imports[name] = value
    return imports


def elf_inventory(text):
    result = []
    for line in text.splitlines():
        if 'R_MIPS_' not in line: continue
        match = re.fullmatch(r'\s*([0-9a-fA-F]+)\s+[0-9a-fA-F]+\s+R_MIPS_(32|26|HI16|LO16)\s+([0-9a-fA-F]+)\s+(\S+)\s*',line)
        if not match: raise ValueError('Unsupported Miko ELF relocation: '+line)
        result.append([int(match[1],16)-RAM,KINDS[match[2]],int(match[3],16),match[4]])
    return result


def merged_rows(native_reloc,inventory,imports,size):
    count = struct.unpack_from('>I',native_reloc,16)[0]
    result = []
    for entry in struct.unpack_from('>'+str(count)+'I',native_reloc,20):
        section,kind,offset = entry>>30,(entry>>24)&63,entry&0xFFFFFF
        if section not in (1,2): raise ValueError('Unexpected original Miko relocation section')
        result.append(0x40000000|(kind<<24)|(offset+(NATIVE_TEXT if section == 2 else 0)))
    for at,kind,target,name in inventory:
        if RAM <= target < RAM+size:
            # New relocations may refer back to original functions and data.
            result.append(0x40000000|(kind<<24)|at)
        elif (name not in imports or imports[name] != target
              or (kind not in (5,6) if name in DATA_IMPORTS else kind != 4)):
            raise ValueError('Unapproved Miko external relocation')
    # Native rows remain in their original order (HI16 caches may be reused).
    return result


def relocation_bytes(native_reloc,inventory,imports,text,size):
    rows = merged_rows(native_reloc,inventory,imports,size)
    length = (24+len(rows)*4+15)&~15
    return (struct.pack('>5I',text,0,size-text,0,len(rows))+
            struct.pack('>'+str(len(rows))+'I',*rows)+bytes(length-24-len(rows)*4)+struct.pack('>I',length))


@dataclass(frozen=True)
class ActorImage:
    ram: int
    resident_bytes: int
    sections: tuple


def validate(rom,data,reloc,report,module):
    native,native_reloc = native_sources(rom)
    imports = imports_for(module)
    if (report.get('version') != 1 or report.get('ram') != RAM
            or report.get('bytes') != len(data) or report.get('overlay_sha256') != sha256(data)
            or report.get('relocation_bytes') != len(reloc) or report.get('relocation_sha256') != sha256(reloc)
            or report.get('sources') != source_hashes() or report.get('imports') != imports
            or report.get('module_sha256') != module['module_sha256']
            or report.get('instance_bytes') != INSTANCE_BYTES or report.get('word_sha256') != WORDS_HASH):
        raise ValueError('Stale or changed complete Miko actor')
    text = report.get('text_bytes',0)
    if (type(text) is not int or text&15 or not PREFIX_BYTES < text < len(data)
            or len(data)&15 or len(data) > LIMIT or len(reloc) > 4096):
        raise ValueError('Miko exceeds its native loaded-image bounds')
    symbols = report.get('symbols',{})
    for name in ('af_miko_fortune_init','af_miko_fortune_give'):
        offset = symbols.get(name)
        if type(offset) is not int or offset&3 or not PREFIX_BYTES <= offset < text:
            raise ValueError('Miko callback export is outside new code')
    words = symbols.get('af_fortune_words')
    if type(words) is not int or words&15 or not text <= words <= len(data)-1088:
        raise ValueError('Miko phrase export is outside read-only data')
    if sha256(data[words:words+1088]) != WORDS_HASH:
        raise ValueError('Miko no longer contains the complete verified phrases')
    expected = bytearray(native+bytes(16))
    for at,value in ((PROFILE_SIZE,INSTANCE_BYTES),(INIT_SLOT,RAM+symbols['af_miko_fortune_init']),
                     (GIVE_SLOT,RAM+symbols['af_miko_fortune_give'])):
        struct.pack_into('>I',expected,at,value)
    if data[:PREFIX_BYTES] != expected:
        raise ValueError('Unapproved native Miko prefix change')
    inventory = report.get('elf_relocations',[])
    seen, internal_jumps, external_jumps, external_high = set(),set(),set(),{}
    for row in inventory:
        if (not isinstance(row,list) or len(row) != 4 or any(type(row[i]) is not int for i in range(3))
                or not isinstance(row[3],str)):
            raise ValueError('Malformed Miko ELF relocation inventory')
        at,kind,target,name = row
        if at&3 or not PREFIX_BYTES <= at <= len(data)-4 or at in seen or kind not in KINDS.values():
            raise ValueError('Invalid or repeated new Miko relocation')
        seen.add(at)
        word = struct.unpack_from('>I',data,at)[0]
        if kind == 4:
            actual = 0x80000000|((word&0x3FFFFFF)<<2)
            if at >= text or word>>26 not in (2,3): raise ValueError('Miko jump relocation is not code')
            if RAM <= target < RAM+len(data):
                if not (RAM <= actual < RAM+NATIVE_TEXT or RAM+PREFIX_BYTES <= actual < RAM+text):
                    raise ValueError('Internal Miko jump is outside executable code')
                internal_jumps.add(at)
            elif imports.get(name) != actual or target != actual:
                raise ValueError('External Miko jump differs from its import')
            else: external_jumps.add(at)
        elif kind == 5 and word>>26 != 15:
            raise ValueError('Miko high relocation is not LUI')
        if not RAM <= target < RAM+len(data) and kind in (5,6):
            if name not in DATA_IMPORTS or imports.get(name) != target:
                raise ValueError('Unapproved Miko fixed data import')
            if kind == 5:
                register = (word>>16)&31
                if register in external_high: raise ValueError('Unpaired Miko fixed data high')
                external_high[register] = word,name
            else:
                register = (word>>21)&31
                if register not in external_high or word>>26 not in (9,35):
                    raise ValueError('Missing Miko fixed data high')
                high,high_name = external_high.pop(register)
                actual = ((high&65535)<<16)+(word&65535)-(65536 if word&32768 else 0)
                if high_name != name or actual != target:
                    raise ValueError('Miko fixed data instructions disagree with import')
    if external_high: raise ValueError('Unpaired Miko fixed data relocation')
    expected_reloc = relocation_bytes(native_reloc,inventory,imports,text,len(data))
    if reloc != expected_reloc:
        raise ValueError('Miko native relocation inventory differs from complete ELF merge')
    scanned = {at for at in range(PREFIX_BYTES,text,4)
               if struct.unpack_from('>I',data,at)[0]>>26 in (2,3)}
    if scanned != internal_jumps|external_jumps:
        raise ValueError('Missing Miko absolute-jump relocation')
    spec = ActorImage(RAM,len(data),struct.unpack_from('>5I',reloc))
    for base in (MODULE_RAM+RESERVATION,0x802F8010,(0x80400000-len(data))&~15):
        relocate_verified_data(spec,data,reloc,base)
    return spec


def metadata(size):
    value = bytearray(METADATA_BYTES)
    struct.pack_into('>4I',value,0,NEW_VROM,NEW_VROM+size,RAM,RAM+size)
    return bytes(value)


def verify_installation(rom,native,report,module):
    files = by_vrom(rom)
    if NEW_VROM not in files or NEW_RELOCATION not in files or VROM in files or RELOCATION in files:
        raise ValueError('Missing complete Miko DMA relocation')
    if (files[NEW_VROM].index != by_vrom(native)[VROM].index
            or files[NEW_RELOCATION].index != files[NEW_VROM].index+1):
        raise ValueError('Native Miko loader no longer sees its adjacent relocation row')
    data,reloc = files[NEW_VROM].extract(rom),files[NEW_RELOCATION].extract(rom)
    spec = validate(native,data,reloc,report,module)
    code = files[CODE_VROM].extract(rom)
    if code[METADATA-CODE_RAM:METADATA-CODE_RAM+32] != metadata(len(data)):
        raise ValueError('Installed Miko ownership metadata differs')
    return spec


def install(rom,replacements,additions,relocations,module,directory):
    from fortune_slips import CATALOG_VROM,CATALOG_HASH
    from mail_view_patch import install as install_reader
    from runtime_module import runtime_source_hashes,verify_test_module
    if (not module or MODULE_VROM not in additions or module.get('source_sha256') != sha256(rom)
            or module.get('runtime_sources') != runtime_source_hashes(ROOT/'runtime')):
        raise ValueError('Miko hand-off requires the current verified resident module')
    if sha256(additions.get(CATALOG_VROM,b'')) != CATALOG_HASH:
        raise ValueError('Miko hand-off requires the complete immutable fortune catalog')
    binary = bytearray(additions[MODULE_VROM])
    if len(binary) != RESERVATION or struct.unpack_from('>I',binary,68)[0] != 0x03000000:
        raise ValueError('Miko hand-off requires the configured full mail reader')
    binary[56:0x88] = bytes(0x88-56)
    if sha256(binary) != module['module_sha256']:
        raise ValueError('Miko hand-off resident code differs from its verified imports')
    expected_reader = {}
    install_reader(rom,expected_reader,{MODULE_VROM:bytes(binary)},module,snapshots=True)
    if any(replacements.get(vrom) != data for vrom,data in expected_reader.items()):
        raise ValueError('Miko hand-off requires the installed complete snapshot reader')
    data,reloc = (directory/'overlay.bin').read_bytes(),(directory/'relocation.bin').read_bytes()
    report = json.loads((directory/'overlay.json').read_text())
    validate(rom,data,reloc,report,module)
    if any(v in mapping for v in (VROM,RELOCATION,NEW_VROM,NEW_RELOCATION)
           for mapping in (replacements,additions,relocations)):
        raise ValueError('Duplicate or overlapping Miko actor patch')
    files = by_vrom(rom)
    code = bytearray(replacements.get(CODE_VROM,files[CODE_VROM].extract(rom)))
    at = METADATA-CODE_RAM
    if code[at:at+32] != METADATA_BYTES:
        raise ValueError('Overlapping Miko ownership metadata patch')
    code[at:at+32] = metadata(len(data))
    changed = {**replacements,CODE_VROM:bytes(code),VROM:data,RELOCATION:reloc}
    moved = {**relocations,VROM:NEW_VROM,RELOCATION:NEW_RELOCATION}
    # Exercise final virtual intervals, adjacent native DMA indices, all prior
    # module configurations, and exact installed bytes before publishing maps.
    prospective = replace_dma(rom,changed,moved,additions)
    verify_test_module(prospective,module)
    verify_installation(prospective,rom,report,module)
    replacements.update({CODE_VROM:bytes(code),VROM:data,RELOCATION:reloc})
    relocations.update({VROM:NEW_VROM,RELOCATION:NEW_RELOCATION})
    return {'overlay':report,'vrom':f'{NEW_VROM:08X}','relocation_vrom':f'{NEW_RELOCATION:08X}',
            'metadata':metadata(len(data)).hex(),'temporary_allocation_bytes':5471,
            'saved_layout_changed':False,
            'status':'Experimental complete fortune hand-off; cancellation lifetime, normal gameplay, and hardware remain unverified'}
