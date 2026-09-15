"""Prevent the saved summer visitor from simultaneously moving into town."""
import argparse
import copy
import json
from pathlib import Path
import struct
import zlib

from aflib import (CODE_RAM,CODE_VROM,DMA_START,DMA_END,by_vrom,sha256,
                   verified_rom,fix_checksum,make_ups,apply_ups)
from apply_translation import write_new
from v3_asset_loader import ROOT,BLOB,MODULE,STARTUP,CONFIG,compile_part
from v3_import_storage import replace_checked
from v3_campsite_calendar import PACKAGE_SIZE
from v3_furniture_art import verify_sources

BASE=ROOT/'build/v3-campsite-manager-runtime-02'
BASE_SHA='12715890318357a7150abeb8d29d59ed6e867ad00e247f9961be1febed62c195'
REPORT_SHA='f0c29e139ad55b84df92dd073ac60e71c928c287cc713d7fa98a3b73b2fb9f73'
ABI,CODE,LIMIT=77,0x3EE0,0x4000
SELECTION_END=0x39E0
IMPORTS=dict(native_installed=0x8019ACD0,native_event_save=0x8008033C,
             native_animal_search=0x800A7C30,native_animal_free=0x800A7AEC)


def install(base,helper,compiled,prior):
    files=by_vrom(base);blob=bytearray(files[BLOB].extract(base))
    code=bytearray(files[CODE_VROM].extract(base));old=prior['villager_selection'];symbols=compiled['symbols']
    if (old['compiled_bytes']!=1504 or sha256(blob[0x3400:SELECTION_END])!=old['compiled_sha256']
            or any(blob[CODE:LIMIT]) or not helper or len(helper)>LIMIT-CODE
            or len(helper)!=compiled['bytes'] or sha256(helper)!=compiled['sha256']
            or any(symbols.get(name)!=address for name,address in IMPORTS.items())):
        raise ValueError('Changed selection owner, native bindings, or unused guard reservation')
    hooks=[]
    for target_data,address,before,name in (
        (blob,0x804636B8,0x02A0F809,'af_v3_camper_movein_candidate'),
        (code,0x800AC650,0x0C029EBB,'af_v3_camper_transfer_blocked')):
        target=symbols[name]
        if not 0x80460000+CODE<=target<0x80460000+CODE+len(helper):
            raise ValueError('Camper candidate helper escapes its checked reservation')
        offset=address-(0x80460000 if target_data is blob else CODE_RAM)
        after=0x0C000000|(target>>2&0x3FFFFFF)
        replace_checked(target_data,offset,struct.pack('>I',before),struct.pack('>I',after))
        hooks.append(dict(address=address,before=f'{before:08X}',after=f'{after:08X}',symbol=name))
    blob[CODE:CODE+len(helper)]=helper
    return blob,code,dict(code=compiled,hooks=hooks,additional_resident_bytes=0,
        additional_heap_bytes=0,saved_format_changed=False,saved_profile_changed=False,
        natural_growth_guard=True,transferred_villager_guard=True,
        saved_camper_area=(70,0),web_patcher_enabled=False,ordinary_move_in_tested=False)


def build(output):
    output=output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'build'):
        raise ValueError('Choose a fresh ignored build directory')
    native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes();verified_rom(native)
    base=(BASE/'animal-forest-v3-asset-loader.z64').read_bytes();raw=(BASE/'build.json').read_bytes()
    if (sha256(base),sha256(raw))!=(BASE_SHA,REPORT_SHA): raise ValueError('Changed complete camper-manager base')
    verify_sources((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                   (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    prior,files=json.loads(raw),by_vrom(base)
    original=by_vrom(native)[CODE_VROM].extract(native)
    if files[CODE_VROM].extract(base)[0x800AC57C-CODE_RAM:0x800AC800-CODE_RAM]!=original[0x800AC57C-CODE_RAM:0x800AC800-CODE_RAM]:
        raise ValueError('Changed complete native villager-transfer function')
    output.mkdir(parents=True)
    helper,compiled=compile_part('camper_movein',output/'camper_movein')
    blob,code,guard=install(base,helper,compiled,prior)
    startup,startup_report=compile_part('startup',output/'startup',defines=(
        'AF_V3_BLOB_SIZE=49152',f'AF_V3_ABI={ABI}','AF_V3_OBJECT_CAPACITY=448',
        'AF_V3_SAVE_RUNTIME=1','AF_V3_CLOTHING_PROFILE=1','AF_V3_FURNITURE_TABLES=1',
        'AF_V3_ACCESSORIES=1',f'AF_V3_ACCESSORY_BYTES={PACKAGE_SIZE}',
        'AF_V3_ACCESSORY_VROM=0x02400000','AF_V3_WESTERN_LARGE=1',
        'AF_V3_CAMPSITE=1','AF_V3_CAMPER_CALENDAR=1','AF_V3_CAMPER=1'))
    module=bytearray(files[MODULE].extract(base));old=prior['startup']
    if (sha256(module[STARTUP:STARTUP+old['bytes']])!=old['sha256']
            or any(module[STARTUP+old['bytes']:CONFIG]) or len(startup)>CONFIG-STARTUP):
        raise ValueError('Changed startup or insufficient reservation')
    module[STARTUP:CONFIG]=startup+bytes(CONFIG-STARTUP-len(startup))
    struct.pack_into('>I',blob,4,ABI)
    struct.pack_into('>4I',module,CONFIG,BLOB,0xC000,zlib.crc32(blob[:0xC000]),ABI)
    image=bytearray(base)
    for vrom,data in ((BLOB,blob),(MODULE,module),(CODE_VROM,code)):
        entry=files[vrom]
        if entry.pend or len(data)!=entry.size: raise ValueError('Camper move-in guard changes an allocation')
        image[entry.pstart:entry.pstart+len(data)]=data
    fix_checksum(image);image=bytes(image)
    if image[DMA_START:DMA_END]!=base[DMA_START:DMA_END]: raise ValueError('Camper guard changes DMA directory')
    patch=make_ups(native,image)
    if apply_ups(native,patch)!=image: raise ValueError('Camper guard patch reconstruction failed')
    report=copy.deepcopy(prior)
    report.update(build='v3-camper-movein',runtime_abi=ABI,input_build_sha256=BASE_SHA,
        output_sha256=sha256(image),patch_sha256=sha256(patch),blob_sha256=sha256(blob),
        startup=startup_report,camper_movein=guard,native_test='pending current camper/move-in exclusion')
    report['villager_selection']['compiled_sha256']=sha256(blob[0x3400:SELECTION_END])
    source_names=('tools/v3_camper_movein.py','tools/v3_asset_loader.py',
                  'overlays/v3/camper_movein.c','overlays/v3/camper_movein.ld')
    report['sources'].update({p:sha256((ROOT/p).read_bytes()) for p in source_names})
    write_new(output/'animal-forest-v3-asset-loader.z64',image)
    write_new(output/'animal-forest-v3-asset-loader.ups',patch)
    write_new(output/'build.json',(json.dumps(report,indent=2,sort_keys=True)+'\n').encode())
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    report=build(parser.parse_args().output)
    print(json.dumps({key:report[key] for key in ('build','runtime_abi','output_sha256','patch_sha256')},indent=2))
