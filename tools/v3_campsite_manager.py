"""Extend the installed English event owner with the additive summer camper."""
import argparse
import copy
import json
from pathlib import Path
import struct
from types import SimpleNamespace
import zlib

from aflib import (CODE_RAM,CODE_VROM,DMA_START,DMA_END,by_vrom,sha256,u32,
                   verified_rom,fix_checksum,make_ups,apply_ups)
from apply_translation import write_new
from catalogue_names import elf_inventory
from npc_mail_show import relocate_verified_data
from v3_asset_loader import ROOT,BLOB,MODULE,STARTUP,CONFIG,compile_part
from v3_import_storage import END,replace_checked
from v3_campsite_calendar import PACKAGE_SIZE

BASE = ROOT/'build/v3-campsite-placement-runtime-01'
BASE_SHA = 'f3893696555b91f4852e87b7bce6d09b1213faf4defe75e3f3dc09ece2b02efe'
REPORT_SHA = '1b8c52f53a4d12effba713b1b8c02f3fc06008f47606c099d0792f50e4913762'
ABI,VROM,RELOC,RAM,SIZE = 76,0x03800000,0x03810000,0x8095B8B0,38128
OWNER_SHA = '8fcde6e3c4b2fb84c956e92043637091209c901f8d493c1cea5484aebe842e2b'
RELOC_SHA = '5e87254084e743ef9dbc0d4b4d7bc9faede2a8f2b7623ade973f210033a9011c'
METADATA,CONTROL,CONTROL_COUNT = 0x80101310,0x80961F48,0x809622C8
IMPORTS = dict(camper=0x804A1A00,native_installed=0x8019ACD0,selected_furniture=0x80484000,
    native_event_index=0x804A2B00,native_today=0x80139F98,native_changes=0x80104F9C,
    selected_villager=0x804634B0,native_event=0x800AA14C,af_v3_camper_register=0x804A2D00,
    af_v3_campsite_choose=0x804A2478,native_field_valid=0x80087C40,native_field_id=0x80087C88,
    native_get_save=0x8008033C,native_reserve_save=0x80080080,native_clear_save=0x800804AC,
    native_check_keep=0x80080040,native_set_keep=0x8007FFC4,native_clear_keep=0x80080000,
    native_set_status=0x8007FDA8,native_clear_status=0x8007FE74,
    native_reset_appeared=0x800AA49C,native_shuffle=0x800A6810,native_unseen=0x800AA3A4,
    native_grow=0x800AD6D4,native_mark_appeared=0x800AA2F8,native_get_place=0x80080D68,
    native_get_fg=0x8008A670,native_place_tent=0x8095D324,native_remove_tent=0x8095D1E0)
DATA_IMPORTS = {'camper','native_installed','selected_furniture','native_event_index','native_today','native_changes'}
CONTROL_POINTERS = ((0x809612F4,0x80961300,20),(0x809612F0,0x80961304,17))


def sources(base):
    files=by_vrom(base)
    data,reloc=files[VROM].extract(base),files[RELOC].extract(base)
    if (sha256(data)!=OWNER_SHA or sha256(reloc)!=RELOC_SHA or len(data)!=SIZE
            or struct.unpack_from('>5I',reloc)!=(SIZE,0,0,0,433)
            or len(reloc)!=1760 or files[RELOC].index!=files[VROM].index+1
            or files[VROM].index!=158 or any(data[0x6A80:0x6BB0])):
        raise ValueError('Changed complete English event owner, BSS, or relocation adjacency')
    return data,reloc


def install(base, suffix, compiled):
    old,reloc=sources(base); symbols=compiled['symbols']
    if (len(suffix)!=compiled['bytes'] or sha256(suffix)!=compiled['sha256'] or len(suffix)%16
            or any(symbols.get(name)!=target for name,target in IMPORTS.items())):
        raise ValueError('Changed camper manager suffix or native bindings')
    data=bytearray(old+suffix); table=symbols['af_v3_camper_controls']
    at=table-RAM
    if not SIZE<=at<=len(data)-29*32 or any(data[at:at+29*32]):
        raise ValueError('Missing independent complete camper control directory')
    originals=old[CONTROL-RAM:CONTROL-RAM+28*32]
    for row in range(28):
        values=struct.unpack_from('>8I',originals,row*32)
        if (not 0<=values[0]<70 or values[6:]!=(0,0)
                or any(value and not RAM<=value<RAM+SIZE for value in values[1:6])):
            raise ValueError('Changed original event control layout')
    data[at:at+28*32]=originals
    names=['af_v3_camper_event_'+part for part in ('start','stop','in','out')]
    struct.pack_into('>8I',data,at+28*32,70,*(symbols[name] for name in names),0,0,0)
    rows=list(struct.unpack_from('>433I',reloc,20)); hooks=[]
    old_slots={word&0xFFFFFF:word>>24&63 for word in rows}
    if len(old_slots)!=433 or any(word>>30!=1 for word in rows):
        raise ValueError('Changed original English-owner relocation inventory')
    def patch(address,before,after):
        replace_checked(data,address-RAM,struct.pack('>I',before),struct.pack('>I',after))
        hooks.append(dict(address=address,before=before,after=after))
    for high,low,register in CONTROL_POINTERS:
        if old_slots.get(high-RAM)!=5 or old_slots.get(low-RAM)!=6:
            raise ValueError('Unrelocated original control base')
        patch(high,0x3C000000 | register<<16 | ((CONTROL+0x8000)>>16),
                   0x3C000000 | register<<16 | ((table+0x8000)>>16))
        patch(low,0x24000000 | register<<21 | register<<16 | (CONTROL&65535),
                  0x24000000 | register<<21 | register<<16 | (table&65535))
    patch(CONTROL_COUNT,28,29)
    # All original table pointers retain their own relocations as well. The
    # copied directory must have independently relocated pointers, not literals
    # into this overlay's unallocated linked addresses.
    added_table=[]
    for index in range(29):
        for field in range(1,6):
            pos=at+index*32+field*4
            if u32(data,pos): added_table.append(0x42000000|pos)
    rows+=added_table
    suffix_slots=[]
    for pos,kind,target,name in elf_inventory(compiled['elf_relocations'],ram=RAM):
        if not SIZE<=pos<=len(data)-4 or pos&3:
            raise ValueError('Camper suffix relocation escapes owned image')
        if RAM<=target<RAM+len(data):
            suffix_slots.append(0x40000000|kind<<24|pos)
        elif IMPORTS.get(name)!=target or (name in DATA_IMPORTS and kind not in (5,6)):
            raise ValueError('Unbound external camper manager reference')
        elif name not in DATA_IMPORTS and kind not in (2,4,5,6):
            raise ValueError('Invalid native function reference')
    rows+=suffix_slots
    if len({word&0xFFFFFF for word in rows})!=len(rows):
        raise ValueError('Duplicate camper manager relocation')
    length=(24+len(rows)*4+15)&~15
    updated=(struct.pack('>5I',len(data),0,0,0,len(rows))+struct.pack('>'+str(len(rows))+'I',*rows)
        +bytes(length-24-len(rows)*4)+struct.pack('>I',length))
    if len(data)+length>0xC000 or RAM+len(data)>0x809670B0 or VROM+len(data)>RELOC:
        raise ValueError('Camper manager exceeds on-demand/virtual reservation')
    allowed={i for row in hooks for i in range(row['address']-RAM,row['address']-RAM+4)}
    bases=(0x801A0010,0x802F8010,0x803D0010)
    for base_address in bases:
        before=relocate_verified_data(SimpleNamespace(ram=RAM,resident_bytes=SIZE,sections=(SIZE,0,0,0,433)),old,reloc,base_address)
        after=relocate_verified_data(SimpleNamespace(ram=RAM,resident_bytes=len(data),
            sections=(len(data),0,0,0,len(rows))),bytes(data),updated,base_address)
        if any(a!=b and i not in allowed for i,(a,b) in enumerate(zip(before,after))):
            raise ValueError('Camper changes unrelated relocated English owner code/data')
        for row in range(28):
            # Original and copied controls must agree AFTER actual relocation.
            if after[at+row*32:at+(row+1)*32]!=before[CONTROL-RAM+row*32:CONTROL-RAM+(row+1)*32]:
                raise ValueError('Copied native controls have different relocated pointers')
    return bytes(data),updated,dict(code=compiled,table=table,table_bytes=29*32,
        old_control_count=28,control_count=29,today_pointer_capacity=32,retained_relocations=433,
        copied_table_relocations=len(added_table),suffix_relocations=len(suffix_slots),
        relocation_count=len(rows),bytes=len(data),relocation_bytes=len(updated),
        on_demand_growth=len(data)-SIZE,relocation_test_bases=list(bases),hooks=hooks,
        output_sha256=sha256(data),relocation_sha256=sha256(updated),
        source_sha256=OWNER_SHA,source_relocation_sha256=RELOC_SHA)


def build(output):
    output=output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'build'):
        raise ValueError('Choose a fresh ignored build directory')
    native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(); verified_rom(native)
    base=(BASE/'animal-forest-v3-asset-loader.z64').read_bytes(); raw=(BASE/'build.json').read_bytes()
    if (sha256(base),sha256(raw))!=(BASE_SHA,REPORT_SHA):
        raise ValueError('Changed complete native tent placement base')
    prior,files=json.loads(raw),by_vrom(base)
    sources(base)
    if (prior['camper']['registration']['symbols']['af_v3_camper_register']!=IMPORTS['af_v3_camper_register']
            or prior['campsite_calendar']['event_code']['symbols']['af_v3_campsite_choose']!=IMPORTS['af_v3_campsite_choose']):
        raise ValueError('Changed installed complete camper/selection entry')
    output.mkdir(parents=True)
    suffix,compiled=compile_part('campsite_manager',output/'manager',extra_sources=('overlays/v3/campsite_manager.S',))
    owner,reloc,manager=install(base,suffix,compiled)
    code=bytearray(files[CODE_VROM].extract(base)); offset=METADATA-CODE_RAM
    before=struct.pack('>8I',VROM,VROM+SIZE,RAM,RAM+SIZE,0,0x809622EC,0,0)
    after=struct.pack('>8I',VROM,VROM+len(owner),RAM,RAM+len(owner),0,0x809622EC,0,0)
    replace_checked(code,offset,before,after)
    blob=bytearray(files[BLOB].extract(base)); old_size=len(blob); moves=[]
    for vrom,data in ((VROM,owner),(RELOC,reloc)):
        blob.extend(bytes(-len(blob)%16)); at=len(blob); blob.extend(data)
        moves.append(dict(vrom=vrom,bytes=len(data),blob_offset=at,physical=files[BLOB].pstart+at,sha256=sha256(data)))
    start,end=files[BLOB].pstart+old_size,files[BLOB].pstart+len(blob)
    if (BLOB+len(blob)>END or end>len(base) or any(base[start:end])
            or any(e.pstart<end and start<(e.pend or e.pstart+e.size)
                   for v,e in files.items() if v!=BLOB and e.pstart!=0xFFFFFFFF)
            or any(e.vstart<BLOB+len(blob) and BLOB+old_size<e.vend for v,e in files.items() if v!=BLOB)
            or any(e.vstart<RELOC+len(reloc) and RELOC<e.vend for v,e in files.items() if v!=RELOC)):
        raise ValueError('Extended English event owner overlaps a live resource')
    startup,startup_report=compile_part('startup',output/'startup',defines=(
        'AF_V3_BLOB_SIZE=49152',f'AF_V3_ABI={ABI}','AF_V3_OBJECT_CAPACITY=448',
        'AF_V3_SAVE_RUNTIME=1','AF_V3_CLOTHING_PROFILE=1','AF_V3_FURNITURE_TABLES=1',
        'AF_V3_ACCESSORIES=1',f'AF_V3_ACCESSORY_BYTES={PACKAGE_SIZE}',
        'AF_V3_ACCESSORY_VROM=0x02400000','AF_V3_WESTERN_LARGE=1',
        'AF_V3_CAMPSITE=1','AF_V3_CAMPER_CALENDAR=1','AF_V3_CAMPER=1'))
    module=bytearray(files[MODULE].extract(base)); old=prior['startup']
    if (sha256(module[STARTUP:STARTUP+old['bytes']])!=old['sha256']
            or any(module[STARTUP+old['bytes']:CONFIG]) or len(startup)>CONFIG-STARTUP):
        raise ValueError('Changed or insufficient startup reservation')
    module[STARTUP:CONFIG]=startup+bytes(CONFIG-STARTUP-len(startup))
    struct.pack_into('>I',blob,4,ABI)
    struct.pack_into('>4I',module,CONFIG,BLOB,0xC000,zlib.crc32(blob[:0xC000]),ABI)
    result=bytearray(base)
    for vrom,data in ((BLOB,blob),(MODULE,module),(CODE_VROM,code)):
        entry=files[vrom]
        if entry.pend or vrom!=BLOB and len(data)!=entry.size: raise ValueError('Unexpected owner resize')
        result[entry.pstart:entry.pstart+len(data)]=data
    struct.pack_into('>I',result,DMA_START+files[BLOB].index*16+4,BLOB+len(blob))
    for row in moves:
        struct.pack_into('>4I',result,DMA_START+files[row['vrom']].index*16,
            row['vrom'],row['vrom']+row['bytes'],row['physical'],0)
    fix_checksum(result); result=bytes(result)
    if len(by_vrom(result))!=3389 or result[DMA_END-16:DMA_END]!=bytes(16):
        raise ValueError('Camper manager changes DMA count/terminator')
    patch=make_ups(native,result)
    if apply_ups(native,patch)!=result: raise ValueError('Camper manager patch reconstruction failed')
    report=copy.deepcopy(prior)
    report.update(build='v3-campsite-manager',runtime_abi=ABI,input_build_sha256=BASE_SHA,
        output_sha256=sha256(result),patch_sha256=sha256(patch),blob_sha256=sha256(blob),blob_bytes=len(blob),
        startup=startup_report,native_test='pending current summer event-manager integration')
    manager.update(moves=moves,metadata_address=METADATA,metadata_before=before.hex(),metadata_after=after.hex(),
        additional_resident_bytes=0,actor_instance_bytes=592,saved_format_changed=False,saved_profile_changed=False,
        manager_installed=True,acquisition_installed=False,web_patcher_enabled=False,not_a_playtest_handoff=True,
        pending=['masked actor/quest conversation and greeting-state integration',
                 'selected summer rewards, native lighting, ordinary entry/exit, and persistence'])
    report['campsite_manager']=manager
    for section in ('camper','campsite_calendar','campsite_placement'):
        report[section]['manager_installed']=True
    source_names=('tools/v3_campsite_manager.py','tools/v3_asset_loader.py',
        'overlays/v3/campsite_manager.c','overlays/v3/campsite_manager.h',
        'overlays/v3/campsite_manager.S','overlays/v3/campsite_manager.ld')
    report['sources'].update({p:sha256((ROOT/p).read_bytes()) for p in source_names})
    write_new(output/'animal-forest-v3-asset-loader.z64',result)
    write_new(output/'animal-forest-v3-asset-loader.ups',patch)
    write_new(output/'build.json',(json.dumps(report,indent=2,sort_keys=True)+'\n').encode())
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    report=build(parser.parse_args().output)
    print(json.dumps({key:report[key] for key in ('build','runtime_abi','output_sha256','patch_sha256')},indent=2))
