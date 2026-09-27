"""Extend the existing save path for the complete creature category.

Called inside the shared fish/world batch. Keeps every published console entry
at its old address through checked tail jumps; no caller needs a guessed new
address and no existing console/player data is repurposed.
"""
import copy
import struct
import zlib
from aflib import sha256
from v3_asset_loader import ROOT,compile_part
from v3_import_storage import jump
from v3_surface_save import DEFINES as SURFACE_DEFINES
from v3_save_clothing import DEFINES as CODEC_DEFINES

DEFINES=SURFACE_DEFINES+('AF_V3_CREATURE_PROFILE=1',)
STATE_BYTES,WORKING_BYTES=1264,1232
WARNING=('Format-7 V3 saves require this or a newer compatible build. Valid older saves migrate '
    'with added-creature collections empty and seasonal state initialized on first use; console '
    'progress and existing collections are preserved. V2 and format-1/2/3/4/5 V3 builds cannot '
    'load new saves. Preserve backups. Native save/reload for this extension is unverified.')
SOURCES=('tools/v3_creature_save.py','overlays/v3/creature_save.c','overlays/v3/creature_save.ld',
    'overlays/v3/creature_codec.ld','overlays/v3/creature_storage.ld','overlays/v3/save_codec.c',
    'overlays/v3/save_codec.h','overlays/v3/save_runtime.c','overlays/v3/save_runtime.h',
    'overlays/v3/save_compressed.c','overlays/v3/console_storage.c')

INSECT_DEFINES=DEFINES+('AF_V3_INSECT_SEASONS=1',)
INSECT_WARNING=('Format-9 V3 saves require this or a newer compatible build. Valid older saves '
    'migrate forward, preserving town data, collections, fish seasons, and console progress; '
    'insect seasons initialize on first use. V2 and earlier V3 builds, including format-7 builds, '
    'cannot load new saves. Preserve backups. Native save/reload remains unverified.')


def prepare_insects(prior):
    """Bind full save code into the shared insect runtime, retaining existing icons.

    The old codec/storage padding holds the complete creature pocket artwork.
    Growing those functions in place would overwrite it. Link the new functions
    with the insect runtime and retarget the existing stable save exports.
    """
    e=prior['equipment_resources'];old=e['creature_fish']['world']['save']
    if (prior['save_codec']['format_version']!=7 or prior['save_codec']['registry_version']!=4
            or prior['save_runtime']['state_bytes']!=STATE_BYTES):
        raise ValueError('Insect seasons require the complete current creature save')
    clear=prior['room_surfaces']['save']['helpers']['symbols']['af_v3_surface_player_clear']
    codec_defines=CODEC_DEFINES+INSECT_DEFINES[1:]+('AF_V3_EXTERNAL_REWARD_VALIDATOR=1',)
    storage_defines=INSECT_DEFINES+('AF_V3_CONSOLE_STORAGE=1','AF_V3_LINKED_CANONICAL=1',
        f'AF_CONSOLE_PRIOR_PLAYER_CLEAR=0x{clear:X}u')
    return dict(format='AFV3-INSECT-SEASONS-1',
        compilation=[dict(file='save_codec',defines=codec_defines),
            *[dict(file=name,defines=storage_defines) for name in
              ('save_runtime','console_storage','save_compressed','console_save')]],
        prior_codec_sha256=old['codec']['sha256'],prior_runtime_sha256=old['runtime']['sha256'],
        bindings={**{name:old['helpers']['symbols'][name] for name in
            ('af_v3_creature_player_clear','af_v3_creature_profile_byte')},
            'af_v3_surface_profile_byte':0x804BC900,'af_v3_reward_data_valid':0x8046B408,
            'af_v3_original_save_read':0x8046BA60,'af_v3_original_save_clear':0x8046BA70},
        canonical_format=8,disk_format=9,registry=5,working_offset=1223,capsule_offset=0x4E7,
        bytes=3,state_bytes=STATE_BYTES,working_bytes=WORKING_BYTES,guard_ram=0x8046C4E0,
        save_warning=INSECT_WARNING,installed=False,native_save_reload_tested=False,
        sources={p:sha256((ROOT/p).read_bytes()) for p in (*SOURCES,'overlays/v3/creature_insect_save.c')})


def compose_insects(prior,equipment,blob,prepared,compiled):
    """Merge all save consumers into a caller-owned blob before runtime startup.

    The enclosing builder recomputes equipment/startup checksums after all insect
    changes. This does not write a ROM or silently activate disabled imports.
    """
    saved=copy.deepcopy(prior['save_runtime']);codec=copy.deepcopy(prior['save_codec'])
    clothing=copy.deepcopy(prior['clothing']);surface=copy.deepcopy(prior['room_surfaces'])
    world=equipment['creature_fish']['world'];old=world['save'];packet=world['packet']
    if (prepared['format']!='AFV3-INSECT-SEASONS-1' or codec['format_version']!=7 or
            codec['registry_version']!=4 or saved['state_bytes']!=STATE_BYTES or
            packet['ram']!=0x8064A000 or packet['bytes']<0xB000):
        raise ValueError('Changed insect save installation contract')
    raw=bytearray(blob[packet['blob_offset']:packet['blob_offset']+packet['bytes']])
    if sha256(raw)!=packet['sha256'] or zlib.crc32(raw)!=packet['crc32']:
        raise ValueError('Changed complete creature world/save packet')
    for name,offset in (('codec',0x4000),('runtime',0x6000)):
        previous=old[name]
        if (previous['sha256']!=prepared['prior_'+name+'_sha256'] or
                sha256(raw[offset:offset+previous['bytes']])!=previous['sha256']):
            raise ValueError('Changed complete predecessor save code: '+name)
    # The enclosing builder supplies the final loaded program and symbols;
    # this composer never invents addresses in the old occupied code padding.
    first,last=compiled['ram'],compiled['ram']+compiled['bytes']
    if first&15 or not 0x80000000<=first<last<=0x80800000:
        raise ValueError('Insect save functions are not resident code')

    def redirect(record,dispatch,compiled,start):
        p=record;data=bytearray(blob[p['blob_offset']:p['blob_offset']+p['bytes']])
        if sha256(data)!=p['sha256'] or zlib.crc32(data)!=p['crc32']:
            raise ValueError('Changed complete stable save-entry packet')
        offset=start-p['ram'];previous=data[offset:offset+dispatch['bytes']]
        if sha256(previous)!=dispatch['sha256']:raise ValueError('Changed complete save dispatch')
        patches=[]
        for row in dispatch['dispatch']:
            at=row['address']-p['ram'];before=bytes.fromhex(row['after'])
            target=compiled['symbols'][row['name']]
            if len(before)!=8 or data[at:at+8]!=before or target&3 or not first<=target<last:
                raise ValueError('Changed stable save export: '+row['name'])
            after=struct.pack('>II',jump(target),0);data[at:at+8]=after
            patches.append(dict(row,before=before.hex(),after=after.hex(),target=target))
        blob[p['blob_offset']:p['blob_offset']+len(data)]=data
        p.update(sha256=sha256(data),crc32=zlib.crc32(data))
        return dict(dispatch,sha256=sha256(data[offset:offset+dispatch['bytes']]),dispatch=patches),patches

    storage=equipment['console_storage']
    dispatch,entries=redirect(storage['packet'],storage['compiled'],compiled,0x804DE200)
    canonical,canonical_entries=redirect(surface['items'],surface['save']['codec'],compiled,0x804BD000)
    storage.update(compiled=dispatch,creature_runtime=compiled,canonical_codec=canonical,
        canonical_packet_sha256=surface['items']['sha256'],save_format=9,canonical_save_format=8,
        ordinary_save_reload_tested=False,native_execution_tested=False)
    surface['save'].update(codec=canonical,creature_canonical_codec=compiled,disk_format_version=9,
        ordinary_persistence_tested=False)
    old.update(codec=compiled,runtime=compiled,stable_console_entries=entries,
        stable_canonical_entries=canonical_entries,
        insect_seasons=dict(prepared,installed=True,runtime_installation_required=True))
    saved.update(creature_runtime_code=compiled,creature_season_bytes=6,
        insect_season_offset=1223,native_save_reload_tested=False)
    codec.update(format_version=9,canonical_format_version=8,registry_version=5,active_codec_code=compiled)
    clothing['save_extension'].update(format_version=9,canonical_format_version=8,registry_version=5,
        active_codec_code=compiled,active_codec_ram=compiled['symbols']['af_v3_save_check_extended'],
        legacy_formats_read=['NAFJ',*[f'AFS3-v{i}' for i in range(1,8)]])
    return dict(save_runtime=saved,save_codec=codec,clothing=clothing,room_surfaces=surface,
        saved_format_changed=True,save_warning=INSECT_WARNING)


def install(prior,equipment,blob,world_code,packet,output):
    """Install in the world packet's checked extension at 8064E000..80654FFF."""
    saved=copy.deepcopy(prior['save_runtime']);codec=copy.deepcopy(prior['save_codec'])
    clothing=copy.deepcopy(prior['clothing']);surface=copy.deepcopy(prior['room_surfaces'])
    storage=equipment['console_storage'];original=storage['compiled'];symbols=original['symbols']
    if codec['format_version']!=5 or saved['state_bytes']!=1232 or len(packet)!=0xB000:
        raise ValueError('Creature persistence requires complete format-five storage and checked extension')
    h,hc=compile_part('creature_save',output/'creature_save',defines=DEFINES,link_symbols={
        'AF_CREATURE_SPAWN_TERMS':world_code['symbols']['af_v3_spawn_terms'],
        'AF_CREATURE_ITEM_TYPE':equipment['creature_items']['code']['symbols']['af_v3_creature_item_type'],
        'AF_CREATURE_REQUIRE_STATE':symbols['af_v3_require_save_state'],
        'AF_CREATURE_SAVE_HALT':symbols['af_v3_save_halt']})
    if hc['symbols']['af_v3_creature_season']!=0x80654600:
        raise ValueError('Changed fixed creature-season entry')
    c,cc=compile_part('creature_codec',output/'creature_codec',primary_source='overlays/v3/save_codec.c',
        defines=CODEC_DEFINES+DEFINES[1:]+('AF_V3_EXTERNAL_REWARD_VALIDATOR=1',))
    canonical=surface['save']['codec'];cs=cc['symbols']
    prior_clear=surface['save']['helpers']['symbols']['af_v3_surface_player_clear']
    r,rc=compile_part('creature_storage',output/'creature_storage',primary_source='overlays/v3/save_runtime.c',
        defines=DEFINES+('AF_V3_CONSOLE_STORAGE=1',
            f'AF_CONSOLE_CANONICAL_CHECK=0x{cs["af_v3_save_check_extended"]:X}u',
            f'AF_CONSOLE_CANONICAL_PACK=0x{cs["af_v3_save_pack_extended"]:X}u',
            f'AF_CONSOLE_PRIOR_PLAYER_CLEAR=0x{prior_clear:X}u'),
        extra_sources=('overlays/v3/console_storage.c','overlays/v3/save_compressed.c','overlays/v3/console_save.c'),
        link_symbols={'AF_CREATURE_CLEAR':hc['symbols']['af_v3_creature_player_clear']})
    for offset,data,end in ((0x4000,c,0x6000),(0x6000,r,0xA000),(0xA000,h,0xAFF0)):
        if offset+len(data)>end or any(packet[offset:end]):
            raise ValueError('Creature save code exceeds its checked extension')
        packet[offset:offset+len(data)]=data

    def redirect(record,compiled,start,names):
        p=record;at=p['blob_offset'];raw=bytearray(blob[at:at+p['bytes']])
        if sha256(raw)!=p['sha256'] or zlib.crc32(raw)!=p['crc32']:
            raise ValueError('Changed complete prior save packet')
        old_code=original if start==0x804DE200 else canonical
        offset=start-p['ram']
        if sha256(raw[offset:offset+old_code['bytes']])!=old_code['sha256']:
            raise ValueError('Changed complete predecessor save code')
        addresses=sorted(set(old_code['symbols'].values()))
        patches=[]
        for name in names:
            address=old_code['symbols'][name];target=compiled['symbols'][name]
            end=min((a for a in addresses if a>address),default=start+old_code['bytes'])
            pos=address-p['ram']
            if not start<=address<start+old_code['bytes'] or end-address<8:
                raise ValueError('Unbounded stable save entry: '+name)
            before=bytes(raw[pos:pos+8]);after=struct.pack('>2I',jump(target),0)
            raw[pos:pos+8]=after
            patches.append(dict(name=name,address=address,target=target,before=before.hex(),after=after.hex()))
        blob[at:at+len(raw)]=raw
        p.update(sha256=sha256(raw),crc32=zlib.crc32(raw))
        dispatch=dict(old_code,format='AFV3-SAVE-STABLE-ENTRY-DISPATCH-1',
            compiled_sha256=old_code['sha256'],sha256=sha256(raw[offset:offset+old_code['bytes']]),dispatch=patches)
        return dispatch,patches

    # Old console programs and already compiled adapters call these exact
    # exports. Redirect all of them, including the guard checker and clear path.
    stable_names={r['name'] for r in saved['code']['dispatch']}
    names=[n for n,a in symbols.items() if (n.startswith('af_v3_') or n in stable_names)
           and 0x804DE200<=a<0x804DE200+original['bytes']]
    dispatch,patches=redirect(storage['packet'],rc,0x804DE200,names)
    storage.update(compiled=dispatch,creature_runtime=rc,save_format=7,canonical_save_format=6,
        native_execution_tested=False,ordinary_save_reload_tested=False)
    old_entries=('af_v3_save_check_extended','af_v3_save_pack_extended','af_v3_save_collect_extended')
    canonical_dispatch,canonical_patches=redirect(surface['items'],cc,0x804BD000,old_entries)
    surface['save'].update(codec=canonical_dispatch,disk_format_version=7,
        creature_canonical_codec=cc,ordinary_persistence_tested=False)
    storage.update(canonical_codec=canonical_dispatch,canonical_packet_sha256=surface['items']['sha256'])
    saved.update(state_bytes=STATE_BYTES,guard_ram=0x8046C4E0,
        creature_profile_bytes=4,creature_collection_bytes=16,creature_season_bytes=3,
        creature_runtime_code=rc,native_save_reload_tested=False)
    codec.update(format_version=7,canonical_format_version=6,registry_version=4,
        work_state_bytes=WORKING_BYTES,active_codec_code=cc)
    clothing['save_extension'].update(format_version=7,canonical_format_version=6,registry_version=4,
        working_state_bytes=WORKING_BYTES,runtime_bytes=STATE_BYTES,
        active_codec_code=cc,active_codec_ram=0x8064E000,
        legacy_formats_read=['NAFJ','AFS3-v1','AFS3-v2','AFS3-v3','AFS3-v4','AFS3-v5'])
    record=dict(format='AFV3-CREATURE-SAVE-1',helpers=hc,codec=cc,runtime=rc,
        stable_console_entries=patches,stable_canonical_entries=canonical_patches,
        capsule_offset=0x4D0,working_offset=1200,bytes=32,profile_bytes=4,
        player_bytes=4,players=4,season_offset=20,guard_ram=0x8046C4E0,
        forward_migration=True,older_versions_read_new_saves=False,
        native_execution_tested=False,ordinary_save_reload_tested=False,
        sources={p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    return record,dict(save_runtime=saved,save_codec=codec,clothing=clothing,room_surfaces=surface,
        expansion_state_range=['8046C000','8046C4F0'],saved_format_changed=True,save_warning=WARNING)
