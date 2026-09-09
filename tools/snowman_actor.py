"""Source-bound Snowman snapshots in the original actor's allocation lifetime."""

from dataclasses import dataclass
import json
from pathlib import Path
import re
import struct

from aflib import CODE_RAM,CODE_VROM,by_vrom,replace_dma,sha256,verified_rom
from audit_snowman_letters import ROOT,VROM,RAM,RELOCATION
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM,MODULE_VROM,RESERVATION,LINKED_LIMIT
from snowman_snapshots import snapshots,TABLE_BYTES

PREFIX_BYTES,NATIVE_TEXT,NATIVE_DATA,LIMIT = 16912,16400,208,0x6000
START,END,GATE = 0x8096E1A4,0x8096E274,0x8096E2B4
NEW_VROM,NEW_RELOCATION = 0x03900000,0x03908000
METADATA = 0x80100FF0
METADATA_BYTES = bytes.fromhex('0086287000866a808096dc3080971e400000000080971c400000000000000000')
KINDS = {'32':2,'26':4,'HI16':5,'LO16':6}


def source_hashes():
    paths = ['overlays/mail_generation/'+name for name in
             ('snowman_creator.c','snowman_creator.h','snowman_actor.s','snowman_actor.ld')]
    paths += ['tools/snowman_snapshots.py','tools/audit_snowman_letters.py']
    return {p:sha256((ROOT/p).read_bytes()) for p in paths}


def native_sources(native):
    native = verified_rom(native);files = by_vrom(native)
    data,reloc = files[VROM].extract(native),files[RELOCATION].extract(native)
    if (sha256(data)!='9ddb45f07394e967bf42e121d11ae25fe39814b68c22dc41b238818c48d99d88'
            or sha256(reloc)!='84e8a1a9211ff0f9733b4c46f23389ae65db6a102c66fb601119b1ce1082d75c'
            or files[RELOCATION].index!=files[VROM].index+1
            or files[CODE_VROM].extract(native)[METADATA-CODE_RAM:METADATA-CODE_RAM+32]!=METADATA_BYTES):
        raise ValueError('Changed original Snowman ownership or adjacent relocation')
    return data,reloc


def patches(module,symbols):
    capital = int(module['symbols']['af_mail_generation_capital'],16)
    creator = RAM+symbols['af_snowman_create']
    if (capital&3 or not MODULE_RAM+0x300<=capital<MODULE_RAM+LINKED_LIMIT
            or creator&3 or not RAM+PREFIX_BYTES<=creator<RAM+LIMIT):
        raise ValueError('Snowman wrapper imports are outside their owned code/data')
    wrapper = [0x27BDFFE0,0xAFB00018,0x00808025,0xAFBF001C,0x3C0E8013,0x8DCE6FD8,
               0x0C00B26B,0xAFAE0014,0x3C014140,0x44812000,0x02002025,0x8FA50014,
               0x46040182,0x4600320D,0x44064000,0,0x3C070000|((capital+32768)>>16),
               0x24E70000|(capital&65535),0x0C000000|((creator>>2)&0x3FFFFFF),0,
               0x8FBF001C,0x8FB00018,0x03E00008,0x27BD0020]
    # The complete creator initializes all metadata itself. Reuse the removed
    # clear call's words for a receipt failure gate, preserving owner allocation,
    # local-player/queue checks, receipt policy, and unconditional native free.
    gate = [0x0C25B869,0x02002025,0x10400004,0x02002025,0x0C02DA8F,0x00002825,0]
    return {START:struct.pack('>24I',*wrapper).ljust(END-START,b'\0'),GATE:struct.pack('>7I',*gate)}


def patch_prefix(native,module,symbols):
    data,_ = native_sources(native);out = bytearray(data)
    for at,value in patches(module,symbols).items(): out[at-RAM:at-RAM+len(value)] = value
    return bytes(out)


def elf_inventory(text):
    rows = []
    for line in text.splitlines():
        if 'R_MIPS_' not in line: continue
        match = re.fullmatch(r'\s*([0-9a-fA-F]+)\s+[0-9a-fA-F]+\s+R_MIPS_(32|26|HI16|LO16)\s+([0-9a-fA-F]+)\s+(\S+)\s*',line)
        if not match: raise ValueError('Unsupported Snowman ELF relocation')
        rows.append([int(match[1],16)-RAM,KINDS[match[2]],int(match[3],16),match[4]])
    return rows


def relocation_bytes(native_reloc,inventory,size):
    rows = []
    for entry in struct.unpack_from('>269I',native_reloc,20):
        section,kind,offset = entry>>30,(entry>>24)&63,entry&0xFFFFFF
        if section not in (1,2,3): raise ValueError('Unsupported original Snowman relocation section')
        offset += (0,NATIVE_TEXT,NATIVE_TEXT+NATIVE_DATA)[section-1]
        if START-RAM<=offset<END-RAM or GATE-RAM<=offset<GATE-RAM+28: continue
        rows.append(0x40000000|(kind<<24)|offset)
    rows += [0x44000000|(START-RAM+18*4),0x44000000|(GATE-RAM)]
    for at,kind,target,name in inventory:
        if not RAM+PREFIX_BYTES<=target<RAM+size: raise ValueError('Snowman creator imports outside its actor')
        rows.append(0x40000000|(kind<<24)|at)
    rows.sort(key=lambda r:r&0xFFFFFF)
    if len({r&0xFFFFFF for r in rows})!=len(rows): raise ValueError('Duplicate Snowman relocation')
    length = (24+len(rows)*4+15)&~15
    return struct.pack('>5I',size,0,0,0,len(rows))+struct.pack('>'+str(len(rows))+'I',*rows)+bytes(length-24-4*len(rows))+struct.pack('>I',length)


@dataclass(frozen=True)
class ActorImage:
    ram: int
    resident_bytes: int
    sections: tuple


def validate(native,data,reloc,report,module,catalog,items):
    _,native_reloc = native_sources(native);table,prepared = snapshots(native,catalog,items)
    if (report.get('version')!=1 or report.get('ram')!=RAM or report.get('bytes')!=len(data)
            or report.get('overlay_sha256')!=sha256(data) or report.get('relocation_bytes')!=len(reloc)
            or report.get('relocation_sha256')!=sha256(reloc) or report.get('sources')!=source_hashes()
            or report.get('module_sha256')!=module['module_sha256'] or report.get('snapshots')!=prepared
            or report.get('capital_ram')!=int(module['symbols']['af_mail_generation_capital'],16)):
        raise ValueError('Stale or changed complete Snowman actor')
    symbols = report.get('symbols',{});end = report.get('code_end')
    if (set(symbols)!= {'af_snowman_create','af_snowman_templates'} or type(end) is not int or end&15
            or not PREFIX_BYTES<end<len(data)<=LIMIT or len(data)&15
            or any(type(v) is not int or v&3 for v in symbols.values())
            or not PREFIX_BYTES<=symbols['af_snowman_create']<end
            or symbols['af_snowman_templates']!=end or len(data)!=end+TABLE_BYTES
            or data[end:]!=table or data[:PREFIX_BYTES]!=patch_prefix(native,module,symbols)):
        raise ValueError('Unapproved Snowman code, immutable snapshots, or native prefix')
    inventory = report.get('elf_relocations',[])
    if (len(inventory)!=2 or [row[1] for row in inventory if isinstance(row,list) and len(row)==4]!=[5,6]
            or any(row[3]!='af_snowman_templates' for row in inventory)):
        raise ValueError('Snowman requires exactly its immutable-table high/low relocation pair')
    seen,jumps,high = set(),set(),{}
    for row in inventory:
        if (not isinstance(row,list) or len(row)!=4 or any(type(row[i]) is not int for i in range(3))
                or not isinstance(row[3],str)):
            raise ValueError('Malformed Snowman ELF relocation')
        at,kind,target,name = row
        if at&3 or not PREFIX_BYTES<=at<=end-4 or at in seen or kind not in (4,5,6):
            raise ValueError('Invalid Snowman creator relocation location')
        seen.add(at);word = struct.unpack_from('>I',data,at)[0]
        if kind==4:
            actual = 0x80000000|((word&0x3FFFFFF)<<2)
            if word>>26 not in (2,3) or not RAM+PREFIX_BYTES<=actual<RAM+end or not RAM+PREFIX_BYTES<=target<RAM+end:
                raise ValueError('Snowman creator has an unapproved external call')
            jumps.add(at)
        elif kind==5:
            if word>>26!=15 or target!=RAM+end: raise ValueError('Snowman high relocation is not its immutable table')
            high[(word>>16)&31] = word
        else:
            register = (word>>21)&31
            if register not in high or target!=RAM+end or word>>26!=9: raise ValueError('Snowman low relocation lacks its table high')
            upper = high[register]
            actual = ((upper&65535)<<16)+(word&65535)-(65536 if word&32768 else 0)
            if actual!=RAM+end: raise ValueError('Snowman table address is not its immutable table start')
    scanned = {at for at in range(PREFIX_BYTES,end,4) if struct.unpack_from('>I',data,at)[0]>>26 in (2,3)}
    if scanned!=jumps: raise ValueError('Snowman has an untracked absolute call')
    if reloc!=relocation_bytes(native_reloc,report['elf_relocations'],len(data)):
        raise ValueError('Snowman relocation merge differs from its approved inventory')
    spec = ActorImage(RAM,len(data),struct.unpack_from('>5I',reloc))
    for base in (MODULE_RAM+RESERVATION,0x802F8010,(0x80400000-len(data))&~15):
        relocate_verified_data(spec,data,reloc,base)
    return spec


def metadata(size):
    value = bytearray(METADATA_BYTES)
    struct.pack_into('>4I',value,0,NEW_VROM,NEW_VROM+size,RAM,RAM+size)
    return bytes(value)


def verify_resources(built,native,module):
    from runtime_module import verify_test_module
    from mail_creator_catalog import identity
    from extended_font_cartridge import VROM as FONT_VROM,verify_configuration
    from mail_view_patch import install as install_reader
    verify_test_module(built,module);files = by_vrom(built)
    catalog = files[0x030A0000].extract(built);items = files[0x02A00000].extract(built)
    if identity(catalog)!=4 or module.get('extended_font',{}).get('font',{}).get('mail_glyphs') is not True:
        raise ValueError('Snowman letters require the complete glyph catalogue and font')
    verify_configuration(files[MODULE_VROM].extract(built),files[FONT_VROM].extract(built),module)
    baseline = bytearray(files[MODULE_VROM].extract(built));baseline[56:0x88] = bytes(0x88-56)
    reader = {};install_reader(native,reader,{MODULE_VROM:bytes(baseline)},module,snapshots=True)
    from mail_view_patch import verify_reader_files
    verify_reader_files(built,native,module,reader)
    return catalog,items


def verify_installation(built,native,module,report):
    catalog,items = verify_resources(built,native,module);files = by_vrom(built)
    if (NEW_VROM not in files or NEW_RELOCATION not in files or VROM in files or RELOCATION in files
            or files[NEW_VROM].index!=by_vrom(native)[VROM].index or files[NEW_RELOCATION].index!=files[NEW_VROM].index+1
            or report.get('catalog')!=4 or report.get('complete_templates')!=list(range(0x202,0x20E))):
        raise ValueError('Missing complete Snowman route or original adjacent DMA rows')
    data,reloc = files[NEW_VROM].extract(built),files[NEW_RELOCATION].extract(built)
    spec = validate(native,data,reloc,report['overlay'],module,catalog,items)
    code = files[CODE_VROM].extract(built)
    if code[METADATA-CODE_RAM:METADATA-CODE_RAM+32]!=metadata(len(data)):
        raise ValueError('Changed Snowman ownership metadata')
    return spec


def install(native,replacements,additions,relocations,module,directory):
    if not module or MODULE_VROM not in additions: raise ValueError('Snowman letters require the configured resident reader')
    native_sources(native)
    if any(v in mapping for v in (VROM,RELOCATION,NEW_VROM,NEW_RELOCATION)
           for mapping in (replacements,additions,relocations)):
        raise ValueError('Overlapping Snowman actor or DMA replacement')
    data = (directory/'overlay.bin').read_bytes();reloc = (directory/'relocation.bin').read_bytes()
    actor = json.loads((directory/'overlay.json').read_text())
    code = bytearray(replacements.get(CODE_VROM,by_vrom(native)[CODE_VROM].extract(native)))
    at = METADATA-CODE_RAM
    if code[at:at+32]!=METADATA_BYTES: raise ValueError('Overlapping Snowman ownership metadata')
    code[at:at+32] = metadata(len(data))
    report = {'overlay':actor,'catalog':4,'complete_templates':list(range(0x202,0x20E)),
              'vrom':f'{NEW_VROM:08X}','relocation_vrom':f'{NEW_RELOCATION:08X}',
              'new_resident_bytes':0,'new_saved_bytes':0,'new_per_letter_allocation_bytes':0,
              'status':'Complete fixed Snowman letters installed; native and gameplay acceptance remain'}
    prospective = replace_dma(native,{**replacements,CODE_VROM:bytes(code),VROM:data,RELOCATION:reloc},
                              {**relocations,VROM:NEW_VROM,RELOCATION:NEW_RELOCATION},additions)
    verify_installation(prospective,native,module,report)
    replacements.update({CODE_VROM:bytes(code),VROM:data,RELOCATION:reloc})
    relocations.update({VROM:NEW_VROM,RELOCATION:NEW_RELOCATION})
    return report
