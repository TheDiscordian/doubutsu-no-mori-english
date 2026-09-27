"""Bind complete console furniture to the existing native room interaction."""
import struct
import zlib

from aflib import by_vrom,sha256,CODE_VROM,CODE_RAM
from v3_asset_loader import ROOT,BLOB,compile_part
from v3_registry import LEGACY_FURNITURE,furniture_identity,furniture_source_index

RAM,TABLE,VTABLE,END=0x804FB000,0x804FC000,0x804FC7E0,0x804FC820
CATEGORY='constant-model-sequence-pending-lifecycle'
SOURCES=('tools/v3_console_room.py','overlays/v3/console_room.c','overlays/v3/console_room.ld',
    'overlays/v3/room_rigs.h','overlays/v3/sparse_furniture.h','tools/v3_registry.py',
    'tools/v3_room_rig_runtime.py','tools/v3_furniture_pipeline.py','tools/v3_furniture_install.py',
    'tools/v3_console_games.py','tools/v3_asset_loader.py')
ROOM_VROM,ROOM_RAM=0x82D7F0,0x80936710
NATIVE=(
    ('clip_setup',0x80939050,332,'829a1b5c83b3284fe2e0174932f22be1ad56e184b4540017259fe6b229ed381a'),
    ('request',0x8093BC30,100,'5b6cdeaefec7e22482d34e9c00c5bc1b10a7f1cb4e47755b547f41f592e1f7ab'),
    ('move',0x8093BD60,84,'a9445a66567e543844fd0e204ea15365dd86a740fd7038bed8827c33ba55ffc6'),
    ('transition',0x800C6D5C,184,'178086395a4be1a03c1dcab948e36b57dafe8f81ed5184d5034f32b41961a8ef'),
    ('return',0x800C6E14,92,'55b6a0d64c5af1f5ebc7f1be6bd9c424933d999cd080e649bb85420ee9fe09bf'))


def lifecycle(profile):
    a=profile.get('callback_adapter',{});launch=a.get('console_launch')
    if (a.get('category')!=CATEGORY or not launch or launch['payload_status']!='present' or
            a.get('pending_callbacks')!=['move'] or profile['scalar_hex']!='419000003c23d70a0400000000000800'):
        return None
    game=launch['game_index']
    if not 8<=game<=19:return None
    return dict(category='native-console-interaction',game_index=game,
        source_gba_game_index=launch['gba_game_index'],native_clip_offset=0x54,
        native_interaction_flags=0x800,gba_link_available=False)


def native_contract(base):
    files=by_vrom(base);owner=files[ROOM_VROM].extract(base);core=files[CODE_VROM].extract(base)
    for name,address,size,digest in NATIVE:
        data,origin=(core,CODE_RAM) if address<ROOM_RAM else (owner,ROOM_RAM)
        if sha256(data[address-origin:address-origin+size])!=digest:
            raise ValueError('Changed complete console room dependency: '+name)
    return dict(functions=[dict(name=n,address=a,bytes=b,sha256=h) for n,a,b,h in NATIVE],
                room_clip_ram=0x80136F2C,native_clip_offset=0x54,switch_changed_offset=0x12D)


def table_bytes(rows):
    if not 0<len(rows)<=19:raise ValueError('Invalid console room binding count')
    out=struct.pack('>4I',0x41464352,len(rows),8,0);seen=set()
    for r in rows:
        index,item=furniture_identity(int(r['source_item_id'],16))
        if (index in seen or r['runtime_index']!=index or r['item_id']!=f'{item:04X}' or
                not 8<=r['game_index']<=19 or type(r['engine_installed']) is not bool):
            raise ValueError('Changed console room identity/engine binding')
        seen.add(index);out+=struct.pack('>HBBI',index,r['game_index'],int(r['engine_installed']),0)
    return out


def checked_runtime(equipment,blob,base=None):
    images=equipment.get('console_images',{});room=images.get('room')
    if not room:return {}
    p=images['packet'];raw=blob[p['blob_offset']:p['blob_offset']+p['bytes']]
    at=RAM-p['ram'];table=TABLE-p['ram'];vtable=VTABLE-p['ram']
    code=room['compiled'];data=table_bytes(room['rows'])
    if (not images.get('emulator',{}).get('installed') or sha256(raw)!=p['sha256'] or
            sha256(raw[at:at+code['bytes']])!=code['sha256'] or
            raw[table:table+len(data)]!=data or raw[vtable:vtable+20].hex()!=room['vtable_hex'] or
            struct.unpack_from('>5I',raw,vtable)!=(0,code['symbols']['af_v3_console_room_move'],0,0,0) or
            base is not None and room['native']!=native_contract(base)):
        raise ValueError('Changed complete console room dispatch/bindings')
    metadata=raw[images['metadata']['ram']-p['ram']:]
    for r in room['rows']:
        entry=metadata[32+(r['game_index']-1)*64:32+r['game_index']*64]
        kind=struct.unpack_from('>I',entry,4)[0]
        if r['image_kind']!=kind or r['engine_installed']!=(kind==1):
            raise ValueError('Console room readiness differs from installed emulator')
    return {r['source_item_id']:r for r in room['rows']}


def install(source,base,equipment,blob,output):
    if equipment.get('console_images',{}).get('room'):
        return checked_runtime(equipment,blob,base)
    images=equipment.get('console_images',{})
    if not images.get('emulator',{}).get('installed'):
        raise ValueError('Console room profiles require installed full-image emulator/storage')
    native=native_contract(base);p=images['packet'];at=p['blob_offset'];raw=bytearray(blob[at:at+p['bytes']])
    if (sha256(raw)!=p['sha256'] or images['compiled']['bytes']>RAM-p['ram'] or
            any(raw[RAM-p['ram']:END-p['ram']])):
        raise ValueError('Console room reservation is occupied or reader packet changed')
    rows=[];metadata=raw[images['metadata']['ram']-p['ram']:]
    for donor in LEGACY_FURNITURE:
        profile=source.profile(donor);life=lifecycle(profile)
        if life is None:continue
        index,item=furniture_identity(donor);entry=metadata[32+(life['game_index']-1)*64:]
        kind=struct.unpack_from('>I',entry,4)[0]
        rows.append(dict(source_item_id=f'{donor:04X}',item_id=f'{item:04X}',runtime_index=index,
            donor_runtime_index=furniture_source_index(donor),game_index=life['game_index'],image_kind=kind,
            engine_installed=kind==1,profile_installed=False,parent_selectable=False,
            room_lifecycle=life,source_profile_sha256=profile['profile_sha256']))
    rows.sort(key=lambda r:r['runtime_index']);data=table_bytes(rows)
    code,compiled=compile_part('console_room',output/'console_room')
    if len(code)>TABLE-RAM or len(data)>VTABLE-TABLE:raise ValueError('Console room reservation overflow')
    raw[RAM-p['ram']:RAM-p['ram']+len(code)]=code
    raw[TABLE-p['ram']:TABLE-p['ram']+len(data)]=data
    vtable=struct.pack('>5I',0,compiled['symbols']['af_v3_console_room_move'],0,0,0)
    raw[VTABLE-p['ram']:VTABLE-p['ram']+20]=vtable
    blob[at:at+len(raw)]=raw;p.update(sha256=sha256(raw),crc32=zlib.crc32(raw))
    images['room']=dict(format='AFV3-CONSOLE-ROOM-1',compiled=compiled,native=native,rows=rows,
        vtable_hex=vtable.hex(),additional_resident_bytes=0,source_mapping_installed=True,
        ordinary_gameplay_tested=False,sources={s:sha256((ROOT/s).read_bytes()) for s in SOURCES})
    return checked_runtime(equipment,blob,base)


def profile_lifecycle(profile,life):
    expected=lifecycle(profile)
    return expected is not None and life==expected
