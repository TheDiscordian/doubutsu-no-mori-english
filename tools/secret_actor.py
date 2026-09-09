"""Complete secret letters without changing the quest manager's allocation."""

from dataclasses import dataclass
import json
import re
import struct

from aflib import by_vrom,replace_dma,sha256,verified_rom
from audit_secret_letters import ROOT,START,END,COMPACT,TEMPLATES,snapshots
from npc_mail_show import OVERLAYS,source,relocate_verified_data
from resident_words import patch as word_patch,relocated as word_relocated
from runtime_layout import MODULE_RAM,MODULE_VROM,RESERVATION,LINKED_LIMIT

SPEC = OVERLAYS['ordinary']
RAM,VROM,RELOCATION = SPEC.ram,SPEC.vrom,SPEC.relocation
PREFIX_BYTES,RESIDENT_BYTES,LIMIT = SPEC.file_bytes,SPEC.resident_bytes,0x8800
NEW_VROM,NEW_RELOCATION = 0x03910000,0x03918000
OWNER_VROM,OWNER_RELOCATION,OWNER_RAM = 0x849B50,0x84C8A0,0x80954D80
METADATA = 0x245C
METADATA_BYTES = bytes.fromhex('00815b700081a1a08091d7b080921f40809218e8')
KINDS = {'32':2,'26':4,'HI16':5,'LO16':6}
CREATOR_SHA256 = '4595cc9ec74b14bd755a57d95a56b30711f6ef9d80d99fbdd0d0551655228c82'


def source_hashes():
    paths = ['overlays/mail_generation/'+n for n in ('secret_creator.c','secret_actor.s','secret_actor.ld')]
    paths += ['tools/'+n for n in ('audit_secret_letters.py','resident_words.py','dialogue_dates.py','birthday_fields.py')]
    return {p:sha256((ROOT/p).read_bytes()) for p in paths}


def native_sources(native):
    native = verified_rom(native);data,reloc = source(native,'ordinary');files = by_vrom(native)
    owner,owner_reloc = files[OWNER_VROM].extract(native),files[OWNER_RELOCATION].extract(native)
    if (sha256(owner)!='67464dc7e81d45cb168ca929c80ec56c1eea09b9c64c48c03d7a53815ed5c51b'
            or sha256(owner_reloc)!='be7fa75ae8e1b2373f031efdaaee1de4ac9d241459749c7184a9d74848574d70'
            or owner[METADATA:METADATA+20]!=METADATA_BYTES
            or files[RELOCATION].index!=files[VROM].index+1):
        raise ValueError('Changed secret-letter owner, metadata, or adjacent relocation')
    # The manager allocates and clears 0x8800 bytes, loads all three conversation
    # kinds into that buffer, and frees it on destruction. Metadata is external
    # to the manager image and deliberately has no manager relocation rows.
    sections = struct.unpack_from('>5I',owner_reloc)
    for row in struct.unpack_from('>'+str(sections[4])+'I',owner_reloc,20):
        section,at = row>>30,row&0xFFFFFF
        at += (0,0,sections[0],sections[0]+sections[1])[section]
        if METADATA<=at<METADATA+20: raise ValueError('Unexpected cross-overlay metadata relocation')
    return data,reloc


def baseline(native,module):
    data,reloc = native_sources(native)
    return word_patch(data,reloc,module=module,dates=True)


def wrapper(module,symbols):
    capital = int(module['symbols']['af_mail_generation_capital'],16)
    creator = RAM+symbols['af_secret_create']
    if (capital&3 or not MODULE_RAM+0x300<=capital<MODULE_RAM+LINKED_LIMIT
            or creator&3 or not RAM+RESIDENT_BYTES<=creator<RAM+LIMIT):
        raise ValueError('Secret wrapper target is outside owned code/data')
    words = [0x27BDFFE0,0xAFBF001C,0xAFB00018,0xAFB10014,0x00808025,
             0x0C00B26B,0,0x3C014170,0x44812000,0x46040182,
             0x4600320D,0x44064000,0,0x3C118092,0x26311B54,
             0x02202025,0x02002825,0x3C070000|((capital+32768)>>16),
             0x24E70000|(capital&65535),0x0C000000|((creator>>2)&0x3FFFFFF),0,
             0x10400006,0,0x0C02A4D9,0,0xA2220001,0xAE000000,0x02201025,
             0x8FBF001C,0x8FB00018,0x8FB10014,0x03E00008,0x27BD0020]
    return struct.pack('>'+str(len(words))+'I',*words).ljust(END-START,b'\0')


def patch_prefix(native,module,symbols):
    data,_ = baseline(native,module);out = bytearray(data)
    out[START-RAM:END-RAM] = wrapper(module,symbols)
    return bytes(out)


def elf_inventory(text):
    result = []
    for line in text.splitlines():
        if 'R_MIPS_' not in line: continue
        match = re.fullmatch(r'\s*([0-9a-fA-F]+)\s+[0-9a-fA-F]+\s+R_MIPS_(32|26|HI16|LO16)\s+([0-9a-fA-F]+)\s+(\S+)\s*',line)
        if not match: raise ValueError('Unsupported secret creator ELF relocation')
        result.append([int(match[1],16)-RAM,KINDS[match[2]],int(match[3],16),match[4]])
    return result


def relocation_bytes(baseline_reloc,inventory,size):
    text,data,_,_,count = struct.unpack_from('>5I',baseline_reloc);rows = []
    for row in struct.unpack_from('>'+str(count)+'I',baseline_reloc,20):
        section,kind,offset = row>>30,(row>>24)&63,row&0xFFFFFF
        if section not in (1,2,3): raise ValueError('Invalid original secret relocation')
        offset += (0,text,text+data)[section-1]
        if START-RAM<=offset<END-RAM: continue
        rows.append(0x40000000|(kind<<24)|offset)
    # Keep original row order, including reused-HI semantics. New wrapper and
    # ELF rows have their own paired registers and follow the retained rows.
    rows += [0x45000000|(START-RAM+13*4),0x46000000|(START-RAM+14*4),0x44000000|(START-RAM+19*4)]
    rows += [0x40000000|(kind<<24)|at for at,kind,_,_ in inventory]
    if len({r&0xFFFFFF for r in rows})!=len(rows): raise ValueError('Duplicate secret relocation')
    length = (24+len(rows)*4+15)&~15
    return struct.pack('>5I',size,0,0,0,len(rows))+struct.pack('>'+str(len(rows))+'I',*rows)+bytes(length-24-4*len(rows))+struct.pack('>I',length)


@dataclass(frozen=True)
class OverlayImage:
    ram: int
    resident_bytes: int
    sections: tuple


def validate(native,data,reloc,report,module,catalog):
    _,original_reloc = baseline(native,module);table,prepared = snapshots(native,catalog)
    if (report.get('version')!=1 or report.get('ram')!=RAM or report.get('bytes')!=len(data)
            or report.get('overlay_sha256')!=sha256(data) or report.get('relocation_bytes')!=len(reloc)
            or report.get('relocation_sha256')!=sha256(reloc) or report.get('sources')!=source_hashes()
            or report.get('module_sha256')!=module['module_sha256'] or report.get('snapshots')!=prepared
            or report.get('capital_ram')!=int(module['symbols']['af_mail_generation_capital'],16)):
        raise ValueError('Stale or changed secret-letter overlay')
    symbols,end = report.get('symbols',{}),report.get('code_end')
    if (set(symbols)!={'af_secret_create','af_secret_templates'} or type(end) is not int or end&15
            or not RESIDENT_BYTES<end<len(data)<=LIMIT or len(data)&15
            or any(type(v) is not int or v&3 for v in symbols.values())
            or symbols['af_secret_create']!=RESIDENT_BYTES or symbols['af_secret_templates']!=end
            or len(data)!=end+608 or data[end:]!=table+bytes(8)
            or sha256(data[RESIDENT_BYTES:end])!=CREATOR_SHA256
            or data[:PREFIX_BYTES]!=patch_prefix(native,module,symbols)
            or data[PREFIX_BYTES:RESIDENT_BYTES]!=bytes(SPEC.sections[3])):
        raise ValueError('Changed secret prefix, BSS initialization, code, or immutable table')
    inventory = report.get('elf_relocations',[]);seen,high = set(),{}
    if len(inventory)!=2 or [row[1] for row in inventory if isinstance(row,list) and len(row)==4]!=[5,6]:
        raise ValueError('Secret creator requires exactly its immutable-table relocation pair')
    for at,kind,target,name in inventory:
        if (type(at) is not int or at&3 or not RESIDENT_BYTES<=at<end or at in seen
                or target!=RAM+end or name!='af_secret_templates'):
            raise ValueError('Invalid secret creator relocation')
        seen.add(at);word = struct.unpack_from('>I',data,at)[0]
        if kind==5:
            if word>>26!=15: raise ValueError('Invalid secret table high instruction')
            high[(word>>16)&31] = word
        else:
            register = (word>>21)&31
            if register not in high or word>>26!=9: raise ValueError('Unpaired secret table low')
            value = ((high[register]&65535)<<16)+(word&65535)-(65536 if word&32768 else 0)
            if value!=RAM+end: raise ValueError('Secret creator table address changed')
    if any(struct.unpack_from('>I',data,at)[0]>>26 in (2,3) for at in range(RESIDENT_BYTES,end,4)):
        raise ValueError('Secret creator must not make absolute calls')
    if reloc!=relocation_bytes(original_reloc,inventory,len(data)):
        raise ValueError('Changed secret relocation merge')
    spec = OverlayImage(RAM,len(data),struct.unpack_from('>5I',reloc))
    original,original_reloc = native_sources(native)
    for base in (MODULE_RAM+RESERVATION,0x802F8010,(0x80400000-LIMIT)&~15):
        moved = relocate_verified_data(spec,data,reloc,base)
        expected = word_relocated(original,original_reloc,base,module=module,dates=True)
        if moved[:START-RAM]!=expected[:START-RAM] or moved[END-RAM:RESIDENT_BYTES]!=expected[END-RAM:]:
            raise ValueError('Secret growth changes unrelated date/item/birthday or BSS relocation')
    return spec


def metadata(size):
    if size&15 or not RESIDENT_BYTES<size<=LIMIT: raise ValueError('Secret image exceeds conversation allocation')
    return struct.pack('>5I',NEW_VROM,NEW_VROM+size,RAM,RAM+size,0x809218E8)


def verify_resources(built,native,module):
    # Existing full-reader verification also pins catalogue four, glyph atlas,
    # configured module, and native snapshot hooks. No new reader is required.
    from snowman_actor import verify_resources as verify_reader
    return verify_reader(built,native,module)[0]


def verify_installation(built,native,module,report):
    catalog = verify_resources(built,native,module);files = by_vrom(built)
    if (NEW_VROM not in files or NEW_RELOCATION not in files or VROM in files or RELOCATION in files
            or files[NEW_VROM].index!=by_vrom(native)[VROM].index or files[NEW_RELOCATION].index!=files[NEW_VROM].index+1
            or report.get('catalog')!=4 or report.get('complete_templates')!=list(TEMPLATES)):
        raise ValueError('Missing installed secret-letter route')
    data,reloc = files[NEW_VROM].extract(built),files[NEW_RELOCATION].extract(built)
    spec = validate(native,data,reloc,report['overlay'],module,catalog)
    owner = files[OWNER_VROM].extract(built);original = by_vrom(native)[OWNER_VROM].extract(native)
    if owner[METADATA:METADATA+20]!=metadata(len(data)):
        raise ValueError('Changed secret-letter loading metadata')
    for lo,hi in ((0x80955224,0x809552E8),(0x80956F2C,0x80957100)):
        if owner[lo-OWNER_RAM:hi-OWNER_RAM]!=original[lo-OWNER_RAM:hi-OWNER_RAM]:
            raise ValueError('Changed quest conversation allocation/loading/free policy')
    if files[OWNER_RELOCATION].extract(built)!=by_vrom(native)[OWNER_RELOCATION].extract(native):
        raise ValueError('Changed quest manager relocation')
    return spec


def install(native,replacements,additions,relocations,module,directory):
    if not module or MODULE_VROM not in additions: raise ValueError('Secret letters require the resident reader')
    expected = baseline(native,module);files = by_vrom(native)
    if (replacements.get(VROM),replacements.get(RELOCATION))!=expected:
        raise ValueError('Secret letters require the complete date/birthday/wider-word overlay')
    if any(v in mapping for v in (NEW_VROM,NEW_RELOCATION) for mapping in (replacements,additions,relocations)) or any(v in relocations for v in (VROM,RELOCATION)):
        raise ValueError('Overlapping secret-letter DMA replacement')
    data = (directory/'overlay.bin').read_bytes();reloc = (directory/'relocation.bin').read_bytes()
    actor = json.loads((directory/'overlay.json').read_text())
    owner = bytearray(replacements.get(OWNER_VROM,files[OWNER_VROM].extract(native)))
    if owner[METADATA:METADATA+20]!=METADATA_BYTES: raise ValueError('Overlapping conversation metadata')
    owner[METADATA:METADATA+20] = metadata(len(data))
    report = {'overlay':actor,'catalog':4,'complete_templates':list(TEMPLATES),
              'vrom':f'{NEW_VROM:08X}','relocation_vrom':f'{NEW_RELOCATION:08X}',
              'allocation_bytes':LIMIT,'new_resident_bytes':0,'new_saved_bytes':0,'new_per_letter_allocation_bytes':0,
              'status':'Complete secret letters installed; native and gameplay acceptance remain'}
    changes = {VROM:data,RELOCATION:reloc,OWNER_VROM:bytes(owner)}
    moves = {VROM:NEW_VROM,RELOCATION:NEW_RELOCATION}
    prospective = replace_dma(native,{**replacements,**changes},{**relocations,**moves},additions)
    verify_installation(prospective,native,module,report)
    replacements.update(changes);relocations.update(moves)
    return report
