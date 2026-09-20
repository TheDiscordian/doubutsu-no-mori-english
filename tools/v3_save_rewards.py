"""Shared per-player event/celebration flags and explicit format-3 migration."""
import copy
import struct
import zlib

from aflib import CODE_RAM, sha256
from v3_asset_loader import ROOT, BLOB, compile_part
from v3_import_storage import jump
from v3_save_clothing import DEFINES as CODEC_DEFINES
from v3_furniture_pipeline import Source

STATE_BYTES, WORKING_BYTES, REWARD_BYTES = 912, 880, 48
DEFINES=('AF_V3_CLOTHING_PROFILE=1','AF_V3_REWARD_PROFILE=1')
SOURCES=('tools/v3_save_rewards.py','overlays/v3/save_rewards.h','overlays/v3/save_rewards.ld',
    'overlays/v3/save_codec.c','overlays/v3/save_codec.h','overlays/v3/save_runtime.c',
    'overlays/v3/save_runtime.h','overlays/v3/save_runtime.ld',
    'overlays/v3/reward_state.c','overlays/v3/reward_state.ld')


def source_bindings():
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    rows=[]
    for at,size,digest in (
        (0x7C234,124,'a14f4a6ef86d1f896c91f7463f4eea6af6eeef2d9f178ed316315af77d56958c'),
        (0x7C2B0,108,'d38248de32fd321140e99b081f66ef38729d962820ff947020cc0c3f03bfaa64'),
        (0x19844C,112,'39355e06c2344881c3fe31300064b80ebca3c611c3f11597ce4f1dc046c43427')):
        raw,row=source.function(at)
        if len(raw)!=size or sha256(raw)!=digest:raise ValueError('Changed complete source reward flag consumer')
        rows.append(row)
    return dict(functions=rows,trophy_count=33,trophy_split=28,celebration_count=4,
        player_bytes=12,trophy_offsets=[0,4],celebration_offset=8,reserved_offsets=[9,10,11])


def install(base,prior,blob,core,output):
    old=prior['clothing']['save_extension'];runtime=prior['save_runtime'];legacy=prior['save_codec']['code']
    vrom,size,checksum,destination=struct.unpack_from('>4I',blob,0xE0)
    at=vrom-BLOB;resource=bytes(blob[at:at+size]);lamp=prior['tent_lamp']
    original_runtime=bytes(blob[0x9200:0x9200+runtime['code']['bytes']])
    if (old['format_version']!=2 or old['registry_version']!=2 or runtime['state_bytes']!=864
            or runtime['state_ram']!=0x8046C000 or old['resource_bytes']!=2976
            or int(old['resource_ram'],16)!=0x8046D000 or destination!=0x8046D000
            or size!=lamp['extra_bytes'] or vrom!=lamp['extra_vrom'] or size!=0x3000
            or sha256(resource)!=lamp['extra_sha256'] or zlib.crc32(resource)!=checksum
            or sha256(resource[:2976])!=old['resource_sha256']
            or sha256(original_runtime)!=runtime['code']['sha256']):
        raise ValueError('Changed complete format-2 codec/runtime reservation')
    # All original codec entries already jump to the separate clothing codec.
    # Recover and bind the entire retired image before reclaiming its first
    # unused body. Stable check/pack/collect jumps and native bridges stay live.
    retired=bytearray(blob[0xB400:0xB400+legacy['bytes']])
    for row in old['public_entries']:
        pos=int(row['entry'],16)-0x8046B400
        if retired[pos:pos+8]!=bytes.fromhex(row['after']):raise ValueError('Changed public codec dispatch')
        retired[pos:pos+8]=bytes.fromhex(row['before'])
    if sha256(retired)!=legacy['sha256']:raise ValueError('Retired codec body is not its complete checked image')
    bindings=source_bindings()
    helpers,h=compile_part('reward_state',output/'reward_state',defines=DEFINES)
    codec,c=compile_part('save_rewards',output/'save_rewards',primary_source='overlays/v3/save_codec.c',
        defines=CODEC_DEFINES+('AF_V3_REWARD_PROFILE=1','AF_V3_EXTERNAL_REWARD_VALIDATOR=1'))
    running,r=compile_part('save_runtime',output/'save_runtime',defines=DEFINES)
    if (len(helpers)>0xB7A0-0xB408 or len(codec)>0x8DC or len(running)!=len(original_runtime)
            or r['symbols']!=runtime['code']['symbols'] or 0x9200+len(running)>0x99C0
            or h['symbols']['af_v3_catalogue_clear']!=prior['collection']['code']['symbols']['af_v3_catalogue_clear']
            or h['symbols']['af_v3_reward_stop_fanfare']!=prior['equipment_resources']['player_actions']['reward_controls']['code']['symbols']['af_v3_reward_stop_fanfare']):
        raise ValueError('Reward persistence moves a stable API or exceeds its owned code space')
    symbols=r['symbols']
    if (h['symbols']['af_v3_require_save_state']!=symbols['require_state']
            or h['symbols']['af_v3_save_halt']!=symbols['af_v3_save_halt']
            or c['symbols']['af_v3_reward_data_valid']!=h['symbols']['af_v3_reward_data_valid']):
        raise ValueError('Reward helper dependency mismatch')
    new_resource=codec+bytes(0x8DC-len(codec))+resource[0x8DC:]
    blob[at:at+size]=new_resource
    blob[0x9200:0x9200+len(running)]=running
    blob[0xB408:0xB7A0]=helpers+bytes(0xB7A0-0xB408-len(helpers))
    entries=[]
    for name,row in zip(('check','pack','collect'),old['public_entries']):
        entry=int(row['entry'],16);target=c['symbols']['af_v3_save_'+name+'_extended']
        after=struct.pack('>II',jump(target),0)
        blob[entry-0x80460000:entry-0x80460000+8]=after
        entries.append({**row,'target':f'{target:08X}','after':after.hex()})
    struct.pack_into('>I',blob,0xE8,zlib.crc32(new_resource))
    entry=0x800B7ADC;before=struct.pack('>II',jump(h['symbols']['af_v3_catalogue_clear']),0)
    after=struct.pack('>II',jump(h['symbols']['af_v3_reward_player_clear']),0)
    if core[entry-CODE_RAM:entry-CODE_RAM+8]!=before:raise ValueError('Changed native player-clear hook')
    core[entry-CODE_RAM:entry-CODE_RAM+8]=after
    return dict(format_version=3,registry_version=2,working_state_bytes=WORKING_BYTES,
        runtime_bytes=STATE_BYTES,state_ram=0x8046C000,guard_ram=0x8046C380,
        reward_offset=832,reward_bytes=REWARD_BYTES,capsule_offset=0x360,
        source=bindings,code=h,codec_code=c,runtime_code=r,
        resource_sha256=sha256(new_resource),resource_vrom=vrom,resource_bytes=size,public_entries=entries,
        private_clear_hook=dict(entry=entry,before=before.hex(),after=after.hex()),
        retired_codec_sha256=sha256(retired),retired_body=[0x8046B408,0x8046B7A0],
        legacy_formats_read=['NAFJ','AFS3-v1','AFS3-v2'],older_v3_reads_new_saves=False,
        ordinary_persistence_tested=False,action_callbacks_installed=False)


def report_updates(prior,receipt):
    result={k:copy.deepcopy(prior[k]) for k in ('save_codec','save_runtime','clothing','tent_lamp')}
    result['save_codec'].update(format_version=3,registry_version=2,work_state_bytes=WORKING_BYTES,
        retired_body_ram_range=receipt['retired_body'])
    result['save_runtime'].update(code=receipt['runtime_code'],state_bytes=STATE_BYTES,
        guard_ram=receipt['guard_ram'])
    result['clothing']['save_extension'].update(format_version=3,registry_version=2,
        working_state_bytes=WORKING_BYTES,runtime_bytes=STATE_BYTES,
        resource_sha256=receipt['resource_sha256'],public_entries=receipt['public_entries'],
        resource_vrom=f'{receipt["resource_vrom"]:08X}',resource_bytes=receipt['resource_bytes'],
        active_codec_code=receipt['codec_code'],legacy_formats_read=receipt['legacy_formats_read'])
    result['tent_lamp']['extra_sha256']=receipt['resource_sha256']
    result.update(expansion_state_range=['8046C000','8046C390'],saved_format_changed=True,
        save_warning='Format-3 V3 saves require this or a newer compatible build. Valid older V3 saves '
        'migrate with reward flags clear; matching/equal-or-larger import profiles remain required. '
        'Do not load imported saves in V2 or older format-1/2 V3 builds. Preserve backups. '
        'Ordinary cross-version gameplay reload is not newly verified.')
    return result
