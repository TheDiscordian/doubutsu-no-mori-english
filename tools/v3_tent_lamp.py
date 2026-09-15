"""Install the complete timed tent-lamp lifecycle without changing either patcher."""
import argparse
import copy
import json
from pathlib import Path
import struct
from types import SimpleNamespace
import zlib
from aflib import (CODE_RAM,CODE_VROM,DMA_START,DMA_END,by_vrom,sha256,
                   verified_rom,fix_checksum,make_ups,apply_ups)
from apply_translation import write_new
from gc_names import symbol_data
from npc_mail_show import relocate_verified_data
from v3_asset_loader import ROOT,BLOB,MODULE,STARTUP,CONFIG,compile_part
from v3_import_storage import END,replace_checked
from v3_campsite_calendar import PACKAGE_SIZE
from v3_furniture_art import verify_sources

BASE=ROOT/'build/v3-campsite-environment-runtime-02'
BASE_SHA='6d2d533bbf85b961560417293626400222f7c2576c565adfa1b93465f41e21f6'
REPORT_SHA='1fc74f38d403e4982a486009e66e162700bbc33425149a384a5b9466164bd381'
ABI,VROM,RELOC,RAM=83,0x8E0A30,0x8E4170,0x80A17190
SOURCES={VROM:'01a72c566b8198e20ec5d2659ab3d58e7fb26e2bff460a33952ee1ff0945ac75',
         RELOC:'79c3813b5cbf68b2c3ab3825bfa4d4cbef4e3cc546afdcee369a79bea6961b1e'}
EXTRA_RAM,EXTRA_SIZE,ENTRY,STATE=0x8046D000,0x3000,0x8046E000,0x8046FFC0
IMPORTS=dict(af_v3_lamp_state=STATE,native_scene=0x80126EB4,native_seconds=0x80136FB8,
    native_effect_loaded=0x801010C0,native_malloc=0x8009BFC0,native_free=0x8009C040,
    native_dma=0x80026B44,native_writeback=0x8002FE00,native_approach=0x8009A570,
    native_opaque_state=0x800BD5E8,native_environment_continue=0x800984D4,
    native_room_prim_continue=0x800981C0,native_set_diffuse=0x8009802C,native_permit_diffuse=0x80098158)


def words(*v):return struct.pack('>'+str(len(v))+'I',*v)
def jump(target):return 0x08000000|(target>>2&0x3FFFFFF)


def donor():
    rel=(ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
    raw=(ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
    verify_sources(rel,raw);symbols=raw.decode()
    return {name:sha256(symbol_data(rel,symbols,name)) for name in (
        'eTL_init','eTL_GetNiceSwitchStat','eTL_ct','eTL_mv','eTL_dw',
        'iam_ef_tent_lamp','mEnv_RequestChangeLightON','mEnv_RequestChangeLightOFF',
        'mEnv_ManagePointLight','mEnv_GetRoomPrimColor','mEnv_DiffuseLightEffectRate')}


def install(native,base,helper,compiled):
    original=by_vrom(native)[CODE_VROM].extract(native);files=by_vrom(base)
    sources={v:files[v].extract(base) for v in SOURCES}
    if any(sha256(sources[v])!=digest for v,digest in SOURCES.items()):
        raise ValueError('Changed complete native effect owner or relocation')
    symbols=compiled['symbols']
    if (not helper or len(helper)>STATE-ENTRY or len(helper)!=compiled['bytes']
            or sha256(helper)!=compiled['sha256'] or any(symbols.get(n)!=a for n,a in IMPORTS.items())):
        raise ValueError('Changed resident lamp code, bindings, or state bound')
    owner=bytearray(sources[VROM]);reloc=sources[RELOC];sections=struct.unpack_from('>5I',reloc)
    if sections!=(0x2A00,0xCF0,0x50,0x1DD0,325):raise ValueError('Changed effect owner dimensions')
    hooks=[]
    for address,before,name in ((0x80A1A840,0x80A1896C,'af_v3_lamp_ct'),
        (0x80A1A844,0x80A18A58,'af_v3_lamp_dt'),(0x80A1A848,0x80A18FCC,'af_v3_lamp_mv'),
        (0x80A1A84C,0x80A18C10,'af_v3_lamp_dw')):
        target=symbols[name]
        if not ENTRY<=target<ENTRY+len(helper):raise ValueError('Lamp callback escapes loaded code')
        replace_checked(owner,address-RAM,words(before),words(target))
        hooks.append(dict(address=address,before=before,after=target,symbol=name))
    removed=[0x82000CB0,0x82000CB4,0x82000CB8,0x82000CBC]
    rows=list(struct.unpack_from('>'+str(sections[4])+'I',reloc,20))
    if [r for r in rows if r in removed]!=removed:raise ValueError('Changed effect profile relocation ownership')
    keep=[r for r in rows if r not in removed];new_reloc=bytearray(reloc)
    struct.pack_into('>I',new_reloc,16,len(keep))
    new_reloc[20:-4]=words(*keep)+bytes(len(reloc)-24-4*len(keep))
    current_sections=(*sections[:4],len(keep))
    for address in (0x80210000,0x80300000):
        old=relocate_verified_data(SimpleNamespace(ram=RAM,resident_bytes=0x5510,sections=sections),
                                  sources[VROM],reloc,address)
        current=bytearray(relocate_verified_data(SimpleNamespace(ram=RAM,resident_bytes=0x5510,sections=current_sections),
                                                owner,new_reloc,address))
        for hook in hooks:
            at=hook['address']-RAM
            if current[at:at+4]!=words(hook['after']):raise ValueError('Resident callback incorrectly relocates')
            current[at:at+4]=old[at:at+4]
        if current!=old:raise ValueError('Lamp modifies unrelated relocated effect code/state')
    code=bytearray(files[CODE_VROM].extract(base));native_hooks=[]
    for start,end,name in ((0x800984CC,0x80098558,'af_v3_lamp_environment'),
                           (0x800981B8,0x80098380,'af_v3_lamp_room_prim')):
        at=start-CODE_RAM
        if code[at:end-CODE_RAM]!=original[at:end-CODE_RAM]:raise ValueError('Changed original environment body')
        target=symbols[name];before=bytes(code[at:at+8]);after=words(jump(target),0)
        if not ENTRY<=target<ENTRY+len(helper):raise ValueError('Environment callback escapes loaded lamp')
        replace_checked(code,at,before,after)
        native_hooks.append(dict(address=start,before=before.hex(),after=after.hex(),symbol=name))
    blob=bytearray(files[BLOB].extract(base))
    source,size,crc,destination=struct.unpack_from('>4I',blob,0xE0)
    previous=bytes(blob[source-BLOB:source-BLOB+size])
    if ((source,size,destination)!=(BLOB+0xF400,0xBA0,EXTRA_RAM)
            or zlib.crc32(previous)!=crc
            or sha256(previous)!='e0f8938fea8bca30eaf4919c38ba79062388bf02946e0d324292b2dc4c35a8b4'):
        raise ValueError('Changed original save-code resource')
    # V3 already owns 80460000..8046FFFF. Mutable save state ends C35F;
    # unchanged extended save code ends DBA0, and furniture starts 80470000.
    extra=bytearray(EXTRA_SIZE);extra[:size]=previous
    extra[0xFF0:0x1000]=words(*([0xAF1AC0DE]*4))
    extra[0x1000:0x1000+len(helper)]=helper
    extra[-16:]=words(*([0xAF1AC0DE]*4))
    asset=blob[0x289000:0x289000+3248]
    if sha256(asset)!='7b920ca7cd74f94554dfd322c2c8af8cc95ea28c4591debf2d8804579b8739dd':
        raise ValueError('Changed complete scene-lamp model')
    return blob,code,bytes(owner),bytes(new_reloc),bytes(extra),dict(code=compiled,
        profile_hooks=hooks,native_hooks=native_hooks,removed_relocations=removed,
        owner_sha256=sha256(owner),relocation_sha256=sha256(new_reloc),owner_bytes=len(owner),
        owner_resident_bytes=0x5510,relocation_bytes=len(reloc),state_ram=STATE,state_reserved_bytes=48,
        extra_ram=EXTRA_RAM,extra_bytes=EXTRA_SIZE,extra_sha256=sha256(extra),
        preserved_save_code_bytes=size,asset_bytes=3248,asset_sha256=sha256(asset),
        scene_heap_bytes=3280,additional_resident_reservation_bytes=0,
        saved_format_changed=False,saved_profile_changed=False,timed_lamp_installed=True,
        ordinary_scene_tested=False,web_patcher_enabled=False)


def build(output):
    output=output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'build'):raise ValueError('Choose fresh ignored output')
    native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes();verified_rom(native)
    base=(BASE/'animal-forest-v3-asset-loader.z64').read_bytes();raw=(BASE/'build.json').read_bytes()
    if (sha256(base),sha256(raw))!=(BASE_SHA,REPORT_SHA):raise ValueError('Changed current environment base')
    source=donor();prior,files=json.loads(raw),by_vrom(base);output.mkdir(parents=True)
    helper,compiled=compile_part('tent_lamp',output/'lamp',extra_sources=('overlays/v3/tent_lamp_tail.S',))
    blob,code,owner,reloc,extra,lamp=install(native,base,helper,compiled)
    old_size=len(blob);blob.extend(bytes(-len(blob)%16));extra_offset=len(blob);blob.extend(extra)
    moves=[]
    for vrom,data in ((VROM,owner),(RELOC,reloc)):
        blob.extend(bytes(-len(blob)%16));at=len(blob);blob.extend(data)
        moves.append(dict(vrom=vrom,blob_offset=at,physical=files[BLOB].pstart+at,bytes=len(data),sha256=sha256(data)))
    start,end=files[BLOB].pstart+old_size,files[BLOB].pstart+len(blob)
    if (BLOB+len(blob)>END or end>len(base) or any(base[start:end])
            or any(e.pstart<end and start<(e.pend or e.pstart+e.size)
                   for v,e in files.items() if v!=BLOB and e.pstart!=0xFFFFFFFF)
            or any(e.vstart<BLOB+len(blob) and BLOB+old_size<e.vend for v,e in files.items() if v!=BLOB)):
        raise ValueError('Lamp append overlaps used cartridge storage')
    struct.pack_into('>4I',blob,0xE0,BLOB+extra_offset,len(extra),zlib.crc32(extra),EXTRA_RAM)
    startup,startup_report=compile_part('startup',output/'startup',defines=(
        'AF_V3_BLOB_SIZE=49152',f'AF_V3_ABI={ABI}','AF_V3_OBJECT_CAPACITY=448',
        'AF_V3_SAVE_RUNTIME=1','AF_V3_CLOTHING_PROFILE=1','AF_V3_FURNITURE_TABLES=1',
        'AF_V3_ACCESSORIES=1',f'AF_V3_ACCESSORY_BYTES={PACKAGE_SIZE}',
        'AF_V3_ACCESSORY_VROM=0x02400000','AF_V3_WESTERN_LARGE=1',
        'AF_V3_CAMPSITE=1','AF_V3_CAMPER_CALENDAR=1','AF_V3_CAMPER=1',
        f'AF_V3_SAVE_CODE_VROM={BLOB+extra_offset}',f'AF_V3_EXTRA_CODE_LIMIT={EXTRA_SIZE}'))
    module=bytearray(files[MODULE].extract(base));old=prior['startup']
    if (sha256(module[STARTUP:STARTUP+old['bytes']])!=old['sha256']
            or any(module[STARTUP+old['bytes']:CONFIG]) or len(startup)>CONFIG-STARTUP):
        raise ValueError('Changed or insufficient startup reservation')
    module[STARTUP:CONFIG]=startup+bytes(CONFIG-STARTUP-len(startup));struct.pack_into('>I',blob,4,ABI)
    struct.pack_into('>4I',module,CONFIG,BLOB,0xC000,zlib.crc32(blob[:0xC000]),ABI)
    image=bytearray(base)
    for vrom,data in ((BLOB,blob),(MODULE,module),(CODE_VROM,code)):
        e=files[vrom]
        if e.pend or vrom!=BLOB and len(data)!=e.size:raise ValueError('Unexpected lamp owner allocation')
        image[e.pstart:e.pstart+len(data)]=data
    struct.pack_into('>I',image,DMA_START+files[BLOB].index*16+4,BLOB+len(blob))
    for row in moves:
        struct.pack_into('>4I',image,DMA_START+files[row['vrom']].index*16,
                         row['vrom'],row['vrom']+row['bytes'],row['physical'],0)
    fix_checksum(image);image=bytes(image);installed=by_vrom(image)
    if (set(installed)!=set(files) or image[DMA_END-16:DMA_END]!=bytes(16)
            or any(installed[v]!=files[v] for v in files if v not in (VROM,RELOC,BLOB))):
        raise ValueError('Lamp changes unrelated DMA metadata')
    patch=make_ups(native,image)
    if apply_ups(native,patch)!=image:raise ValueError('Lamp patch reconstruction failed')
    report=copy.deepcopy(prior);lamp.update(donor=source,moves=moves,extra_vrom=BLOB+extra_offset)
    report.update(build='v3-tent-lamp',runtime_abi=ABI,input_build_sha256=BASE_SHA,
        output_sha256=sha256(image),patch_sha256=sha256(patch),blob_sha256=sha256(blob),
        blob_bytes=len(blob),blob_file_bytes=len(blob),startup=startup_report,tent_lamp=lamp,
        native_test='pending current timed scene-lamp and expanded startup execution')
    report['campsite_environment']['timed_lamp_installed']=True
    report['import_storage']['remaining_bytes']=END-BLOB-len(blob)
    names=('tools/v3_tent_lamp.py','tools/v3_asset_loader.py','overlays/v3/tent_lamp.c',
           'overlays/v3/tent_lamp.h','overlays/v3/tent_lamp.ld','overlays/v3/tent_lamp_tail.S',
           'overlays/v3/startup.c','overlays/v3/storage.h')
    report['sources'].update({n:sha256((ROOT/n).read_bytes()) for n in names})
    write_new(output/'animal-forest-v3-asset-loader.z64',image)
    write_new(output/'animal-forest-v3-asset-loader.ups',patch)
    write_new(output/'build.json',(json.dumps(report,indent=2,sort_keys=True)+'\n').encode())
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    report=build(parser.parse_args().output)
    print(json.dumps({k:report[k] for k in ('build','runtime_abi','output_sha256','patch_sha256')},indent=2))
