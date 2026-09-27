"""Install complete format-five save storage through the shared runtime builder."""
import copy
import struct
import zlib
from aflib import CODE_RAM,sha256
from v3_asset_loader import ROOT,BLOB,compile_part
from v3_import_storage import jump
from v3_surface_save import DEFINES

RAM,SIZE,STATE,SCRATCH,HASH=0x804DE200,0x4E00,0x804DC800,0x804E3000,0x804F5000
SOURCES=('tools/v3_console_storage.py','tools/v3_furniture_install.py','tools/v3_room_goods.py',
    'tools/v3_asset_loader.py','overlays/v3/console_storage.c','overlays/v3/console_storage.h',
    'overlays/v3/console_storage.ld','overlays/v3/save_runtime.c','overlays/v3/save_runtime.h',
    'overlays/v3/save_codec.h','overlays/v3/save_compressed.c','overlays/v3/save_compressed.h',
    'overlays/v3/console_save.c','overlays/v3/console_save.h','overlays/v3/surface_bootstrap.c')
WARNING=('Format-5 V3 saves require this or a newer compatible build. Valid older saves migrate '
    'with console progress empty and native scores retained. Older format-1/2/3/4 V3 builds '
    'and V2 cannot load these saves. Preserve backups. Native gameplay/save reload is not newly verified.')


def install(base,prior,blob,core,output):
    equipment=copy.deepcopy(prior['equipment_resources'])
    surface=copy.deepcopy(prior['room_surfaces']);saved=copy.deepcopy(prior['save_runtime'])
    codec=copy.deepcopy(prior['save_codec']);clothing=copy.deepcopy(prior['clothing'])
    if equipment.get('console_storage') or codec['format_version']!=4 or saved['state_bytes']!=1232:
        raise ValueError('Console storage requires the complete current format-four runtime')
    carry=equipment['room_carry'];state=carry['state']
    if (state['ram']+state['bytes']!=STATE or STATE+0x19A0>RAM or RAM+SIZE!=SCRATCH or
        SCRATCH+72064+16>HASH or HASH+16384+16>prior['furniture']['bank_pool']['start']):
        raise ValueError('Console code/state/scratch overlaps an existing allocation')
    # Reject existing reservations in the new region, including future packets.
    def reservations(value):
        if isinstance(value,dict):
            if isinstance(value.get('ram'),int) and isinstance(value.get('bytes'),int):
                yield value['ram'],value['bytes']
            for v in value.values():yield from reservations(v)
        elif isinstance(value,list):
            for v in value:yield from reservations(v)
    if any(at<HASH+16384+16 and STATE<at+n for at,n in reservations(equipment)):
        raise ValueError('Console reservation intersects a retained equipment allocation')
    items=surface['items'];old=blob[items['blob_offset']:items['blob_offset']+items['bytes']]
    if sha256(old)!=items['sha256'] or zlib.crc32(old)!=items['crc32']:
        raise ValueError('Changed complete canonical codec/surface packet')
    canonical=surface['save']['codec'];functions=canonical['symbols']
    start=0x804BD000-0x804BC000
    if sha256(old[start:start+canonical['bytes']])!=canonical['sha256']:
        raise ValueError('Changed complete canonical format-four codec')
    previous=saved['code'];at=0x9200
    if sha256(blob[at:at+previous['bytes']])!=previous['sha256']:
        raise ValueError('Changed stable save runtime dispatch')
    for p in saved['patches']:
        pos=p['address']-CODE_RAM;value=bytes.fromhex(p['after'])
        if core[pos:pos+len(value)]!=value:raise ValueError('Changed native save integration route')
    prior_clear=surface['save']['helpers']['symbols']['af_v3_surface_player_clear']
    defines=DEFINES+('AF_V3_CONSOLE_STORAGE=1',
        f'AF_CONSOLE_CANONICAL_CHECK=0x{functions["af_v3_save_check_extended"]:X}u',
        f'AF_CONSOLE_CANONICAL_PACK=0x{functions["af_v3_save_pack_extended"]:X}u',
        f'AF_CONSOLE_PRIOR_PLAYER_CLEAR=0x{prior_clear:X}u')
    code,compiled=compile_part('console_storage',output/'console_storage',
        primary_source='overlays/v3/save_runtime.c',defines=defines,
        extra_sources=('overlays/v3/console_storage.c','overlays/v3/save_compressed.c','overlays/v3/console_save.c'))
    if len(code)>SIZE-16:raise ValueError('Console packet exceeds its guarded code reservation')
    packet=code+bytes(SIZE-16-len(code))+bytes.fromhex('AF4355DE')*4
    blob.extend(bytes(-len(blob)%16));offset=len(blob);blob.extend(packet)
    symbols=compiled['symbols'];dispatch=[]
    for row in previous['dispatch']:
        pos=row['address']-0x80460000;before=bytes.fromhex(row['after'])
        target=symbols[row['name']]
        if blob[pos:pos+8]!=before or not RAM<=target<RAM+len(code):
            raise ValueError('Changed stable runtime entry: '+row['name'])
        after=struct.pack('>2I',jump(target),0);blob[pos:pos+8]=after
        dispatch.append(dict(row,before=before.hex(),after=after.hex(),target=target))
    saved['code']=dict(previous,sha256=sha256(blob[at:at+previous['bytes']]),dispatch=dispatch)
    entries=[]
    for name,row in zip(('check','pack','collect'),clothing['save_extension']['public_entries']):
        pos=int(row['entry'],16)-0x80460000;before=bytes.fromhex(row['after'])
        if blob[pos:pos+8]!=before:raise ValueError('Changed stable save codec entry')
        if name=='collect':entries.append(row);continue
        target=symbols['af_v3_save_'+name];after=struct.pack('>2I',jump(target),0)
        blob[pos:pos+8]=after;entries.append(dict(row,before=before.hex(),after=after.hex(),target=f'{target:08X}'))
    pos=0x800B7ADC-CODE_RAM;before=struct.pack('>2I',jump(prior_clear),0)
    if core[pos:pos+8]!=before:raise ValueError('Changed complete player-clear chain')
    after=struct.pack('>2I',jump(symbols['af_v3_console_player_clear']),0);core[pos:pos+8]=after
    clear=dict(address=0x800B7ADC,before=before.hex(),after=after.hex(),prior=prior_clear)
    record=dict(format='AFV3-CONSOLE-STORAGE-RUNTIME-1',compiled=compiled,
        packet=dict(ram=RAM,bytes=SIZE,blob_offset=offset,vrom=BLOB+offset,
                    sha256=sha256(packet),crc32=zlib.crc32(packet)),
        state=dict(ram=STATE,bytes=0x19A0,player_bytes=1632,players=4,saved=True),
        scratch=dict(ram=SCRATCH,bytes=72064,guard=SCRATCH+72064),
        hash=dict(ram=HASH,bytes=16384,guard=HASH+16384),
        canonical_codec=canonical,canonical_packet_sha256=items['sha256'],
        stable_runtime_dispatch=dispatch,codec_entries=entries,player_clear=clear,
        save_format=5,bank_bytes=65536,flash_bytes=131072,canonical_save_format=4,
        installed=True,native_execution_tested=False,ordinary_save_reload_tested=False,
        console_launch_installed=False,choices_added=0,
        sources={p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    equipment['console_storage']=record
    codec.update(format_version=5,canonical_format_version=4,compressed_storage=True,
        active_codec_resource='equipment_resources.console_storage')
    saved.update(console_state_bytes=0x19A0,console_runtime_code=compiled,native_save_reload_tested=False)
    clothing['save_extension'].update(format_version=5,canonical_format_version=4,
        active_codec_resource='equipment_resources.console_storage',public_entries=entries,
        legacy_formats_read=['NAFJ','AFS3-v1','AFS3-v2','AFS3-v3','AFS3-v4'])
    # Keep surface ownership/canonical receipts intact; publish its outer disk format.
    surface['save'].update(disk_format_version=5,outer_storage='equipment_resources.console_storage')
    return equipment,{},dict(save_runtime=saved,save_codec=codec,clothing=clothing,
        room_surfaces=surface,saved_format_changed=True,save_warning=WARNING)
