"""Explicit personality-based town adaptation and experimental roster activation."""
import argparse
import copy
import json
from pathlib import Path
import struct
import zlib

from aflib import CODE_RAM,CODE_VROM,apply_ups,by_vrom,fix_checksum,make_ups,sha256,verified_rom
from apply_translation import write_new
from v3_asset_loader import BLOB,CONFIG,MODULE,ROOT,STARTUP,compile_part

ABI=57
BASE=ROOT/'build/v3-islander-houses-02'
BASE_SHA='e18e7ce0e52a745dbffc964b9c38122d11e0ac6a38433377ed9098c760c861b7'
MODE_OFFSET=0x1F60
SOURCES=('tools/v3_town_residents.py','tools/v3_asset_loader.py','overlays/v3/town_eligible.c',
         'overlays/v3/town_eligible.ld','overlays/v3/clothing_roster.S',
         'overlays/v3/startup.c','overlays/v3/startup.ld')
NATIVE_SCHEDULE_CODE=(0x800AEA80,0x800AEDDC)
NATIVE_SCHEDULE_DATA=(0x8010B970,0x8010BB28)


def build(output,enable='all'):
    if enable not in ('none','pilots','all') or not output.resolve().is_relative_to(ROOT/'build'):
        raise ValueError('Explicit experimental roster mode and ignored build/ output required')
    base=(BASE/'animal-forest-v3-asset-loader.z64').read_bytes()
    prior=json.loads((BASE/'build.json').read_text())
    if sha256(base)!=BASE_SHA or prior['output_sha256']!=BASE_SHA or prior['runtime_abi']!=56:
        raise ValueError('Changed complete arrival-house cartridge')
    native=verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    files=by_vrom(base)
    blob=bytearray(files[BLOB].extract(base))
    code=bytearray(files[CODE_VROM].extract(base))
    native_code=by_vrom(native)[CODE_VROM].extract(native)
    old=prior['villager_selection'];size=old['compiled_bytes']
    if (sha256(blob[0x3400:0x3400+size])!=old['compiled_sha256']
            or any(blob[MODE_OFFSET:MODE_OFFSET+20]) or any(blob[0x1E60:0x1E74])
            or prior['villager_houses']['installed_villagers']!=[f'{n:04X}' for n in range(0xE0DA,0xE0EE)]):
        raise ValueError('Changed selection code, mode reservation, flags, or complete house roster')
    schedule=[]
    for start,end in (NATIVE_SCHEDULE_CODE,NATIVE_SCHEDULE_DATA):
        original=native_code[start-CODE_RAM:end-CODE_RAM]
        if code[start-CODE_RAM:end-CODE_RAM]!=original:
            raise ValueError('Ordinary personality schedule contract has changed')
        schedule.append({'start':f'{start:08X}','end':f'{end:08X}','sha256':sha256(original)})
    enabled=[];adaptation=[]
    for slot,row in enumerate(prior['villager_text']['imports']):
        actor=0xE0DA+slot;data=blob[0x2C00+slot*32:0x2C20+slot*32]
        if (row['actor_id']!=f'{actor:04X}' or sha256(data)!=row['record_sha256']
                or not row['initial_defaults_applied'] or data[4]>=6 or data[7]!=1
                or data[6]!=(0 if actor in (0xE0EA,0xE0ED) else 2)
                or not blob[0x20+((actor&255)>>3)] & (1<<(actor&7))):
            raise ValueError('Incomplete selected villager metadata or starting outfit')
        blob[MODE_OFFSET+slot]=1
        active=enable=='all' or enable=='pilots' and actor in (0xE0EA,0xE0ED)
        blob[0x1E60+slot]=int(active)
        if active:enabled.append(row['actor_id'])
        adaptation.append({'actor_id':row['actor_id'],'name':row['name'],
            'donor_growth_permission':data[6],'town_mode':'native_personality_resident',
            'personality':data[4],'arrival_house_installed':True,'enabled_for_integration':active,
            'island_quest_system_imported':False,'ordinary_gameplay_verified':False})
    output.mkdir(parents=True,exist_ok=False)
    helper,compiled=compile_part('town_eligible',output/'town_eligible',
        extra_sources=('overlays/v3/clothing_roster.S',),defines=('AF_V3_TOWN_ELIGIBLE_BRIDGE=1',))
    offset=0x70E40
    if not helper or len(helper)>0x1C0 or any(blob[offset:0x71000]):
        raise ValueError('Town policy overlaps installed clothing or accessory data')
    target=compiled['symbols']['af_v3_town_eligible_bridge']
    predicate_entry=old['code']['symbols']['eligible'];at=predicate_entry-0x80460000
    if predicate_entry!=0x804634B0 or not 0x80473E40<=target<0x80473E40+len(helper):
        raise ValueError('Changed private eligible entry or preserving bridge')
    before=bytes(blob[at:at+8])
    if before!=bytes.fromhex('2c8300d81460002e'):
        raise ValueError('Changed compiled selection predicate')
    after=struct.pack('>2I',0x08000000|(target>>2&0x3FFFFFF),0)
    blob[at:at+8]=after
    blob[offset:offset+len(helper)]=helper
    package=blob[0x70000:0x7F000]
    struct.pack_into('>I',blob,0xF8,zlib.crc32(package))
    struct.pack_into('>I',blob,4,ABI)
    startup,startup_report=compile_part('startup',output/'startup',defines=(
        'AF_V3_BLOB_SIZE=49152',f'AF_V3_ABI={ABI}','AF_V3_OBJECT_CAPACITY=448',
        'AF_V3_SAVE_RUNTIME=1','AF_V3_CLOTHING_PROFILE=1','AF_V3_FURNITURE_TABLES=1',
        'AF_V3_ACCESSORIES=1','AF_V3_ACCESSORY_BYTES=61440'))
    module=bytearray(files[MODULE].extract(base));old_start=prior['startup']
    if (sha256(module[STARTUP:STARTUP+old_start['bytes']])!=old_start['sha256']
            or any(module[STARTUP+old_start['bytes']:CONFIG]) or len(startup)>CONFIG-STARTUP):
        raise ValueError('Changed startup code or reservation')
    module[STARTUP:CONFIG]=startup+bytes(CONFIG-STARTUP-len(startup))
    struct.pack_into('>4I',module,CONFIG,BLOB,0xC000,zlib.crc32(blob[:0xC000]),ABI)
    image=bytearray(base)
    for vrom,data in ((CODE_VROM,code),(MODULE,module),(BLOB,blob)):
        entry=files[vrom]
        if entry.pend or entry.size!=len(data):raise ValueError('Town update changes a physical allocation')
        image[entry.pstart:entry.pstart+entry.size]=data
    fix_checksum(image);image=bytes(image);patch=make_ups(native,image)
    if apply_ups(native,patch)!=image:raise ValueError('Town cartridge reconstruction failed')
    text=copy.deepcopy(prior['villager_text'])
    for row in text['imports']:
        row['town_behaviour_adapted']=True
        row['move_in_enabled']=row['actor_id'] in enabled
    text['remaining']=['ordinary town gameplay, house entry, and persistence integration']
    report={**prior,'build':'v3-town-residents','runtime_abi':ABI,'input_build_sha256':BASE_SHA,
        'output_sha256':sha256(image),'patch_sha256':sha256(patch),'blob_sha256':sha256(blob),
        'startup':startup_report,'villager_text':text,'new_villager_ids_enabled':bool(enabled),
        'villager_selection':{**old,'compiled_sha256':sha256(blob[0x3400:0x3400+size]),
            'content_ready':[r['actor_id'] for r in adaptation],
            'move_in_enabled':enabled,'native_execution':'pending for complete town mode'},
        'town_residents':{'selection_mode':enable,'adaptations':adaptation,'mode_ram':'80461F60',
            'code':compiled,'hook':{'entry':f'{predicate_entry:08X}','target':f'{target:08X}',
                                   'before':before.hex(),'after':after.hex()},
            'profile_checked_at_selection':True,'donor_metadata_unchanged':True,
            'retained_native_schedule_ranges':schedule,'resident_growth_bytes':0,
            'saved_formats_and_profile_changed':False,'native_test':'pending',
            'not_a_playtest_handoff':True,
            'remaining':['ordinary arrivals, conversations, house entry, and persistence',
                         'new instrument sample playback','aloha item display/catalogue/acquisition']},
        'native_test':'pending for town selection, schedules, and gameplay',
        'accessory_runtime':{**prior['accessory_runtime'],'package_sha256':sha256(package)},
        'sources':{**prior['sources'],**{p:sha256((ROOT/p).read_bytes()) for p in SOURCES}}}
    write_new(output/'animal-forest-v3-asset-loader.z64',image)
    write_new(output/'asset-loader.ups',patch)
    write_new(output/'build.json',(json.dumps(report,indent=2)+'\n').encode())
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--enable',choices=('none','pilots','all'),default='all')
    args=parser.parse_args();r=build(args.output,args.enable)
    print(json.dumps({k:r[k] for k in ('runtime_abi','output_sha256','patch_sha256')}))
