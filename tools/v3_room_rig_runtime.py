"""Install complete shared room rigs without enabling unfinished parent imports."""
import copy
import json
import struct
import zlib

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256
from v3_asset_loader import ROOT,BLOB,compile_part
from v3_equipment_runtime import RAM as EQUIPMENT_RAM,retired_module_space
from v3_furniture_pipeline import Source,prepare,room_aliases,PreparedAssets
from v3_furniture_rigs import CATEGORY,CLOCK_CATEGORY,STORAGE_CATEGORY,suffix
from v3_registry import furniture_representation_identity,ROOM_ALIAS_REGISTRY_VERSION
from v3_import_storage import ROWS,ITEMS,slot,END
from v3_tent_model import native_contract
from v3_resource_capacity import checked_limit

RAM,TABLE,VTABLE,LIMIT,CAPACITY = 0x804B1800,0x804B1E00,0x804B1FA0,0x804B1FE0,24
MAGIC=0x41465231
PACKET_RAM,PACKET_TABLE,PACKET_BYTES,PACKET_CAPACITY=0x804B8000,0x804B9000,8192,128
PACKET_MAGIC=0x41465232
SOUND_TABLE,SOUND_VTABLE,SOUND_MAGIC,SOUND_CAPACITY=0x804B9C10,0x804B1FC0,0x41465331,64
SOURCES=('tools/v3_room_rig_runtime.py','tools/v3_asset_loader.py','tools/v3_furniture_rigs.py','tools/v3_keyframes.py',
    'tools/v3_furniture_pipeline.py','tools/v3_furniture_install.py','tools/v3_registry.py','tools/v3_equipment_runtime.py',
    'tools/v3_display_aliases.py','tools/v3_held_catalogue.py',
    'tools/v3_resource_capacity.py',
    'overlays/v3/room_rigs.c','overlays/v3/room_rigs.h','overlays/v3/room_rigs.ld',
    'overlays/v3/held_rigs.ld','overlays/v3/room_rigs_packet.ld',
    'overlays/v3/room_rigs_bootstrap.c','overlays/v3/room_rigs_bootstrap.ld')


def install_profiles(base,prior,blob,core,original,output,directories):
    """Bind complete implemented categories to ordinary, unselected item slots.

    Acquisition, catalogue, and scoring activation remain explicit later stages.
    Existing model storage is reused; no partial graphics or per-item list enters
    this adapter. The selected-profile bits remain unchanged throughout.
    """
    from apply_translation import write_new
    from v3_furniture_install import profile,provenance_patch
    from v3_furniture_pipeline import identity_rows,name_metadata
    from v3_import_storage import ROWS_RAM
    result=copy.deepcopy(prior['equipment_resources']);runtime=result['room_rigs']
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    directories=[d.resolve() for d in directories]
    cache=PreparedAssets(source,directories)
    identities=identity_rows(ROOT/'build/item-identity-megasheet.xlsx')
    module=blob[result['blob_offset']:result['blob_offset']+result['bytes']]
    packet=runtime['packet'];at=packet['blob_offset']
    if (sha256(module)!=result['sha256'] or sha256(blob[at:at+packet['bytes']])!=packet['sha256'] or
            module[VTABLE-EQUIPMENT_RAM:VTABLE-EQUIPMENT_RAM+20].hex()!=runtime['vtable_hex'] or
            module[SOUND_VTABLE-EQUIPMENT_RAM:SOUND_VTABLE-EQUIPMENT_RAM+20].hex()!=runtime.get('sound_vtable_hex')):
        raise ValueError('Changed complete shared room category runtime')
    rigs={r['source_item_id']:r for r in runtime['rows']}
    sounds={r['source_item_id']:r for r in runtime.get('sound_rows',[])}
    old=copy.deepcopy(prior.get('staged_furniture',dict(format='AFV3-STAGED-FURNITURE-PROFILES-1',rows=[],sources=[])))
    if old['format']!='AFV3-STAGED-FURNITURE-PROFILES-1':raise ValueError('Unknown staged furniture format')
    occupied={r['item_id'] for r in old['rows']};staged=[];evidence=[]
    limit=checked_limit(base,prior)
    for directory in directories:
        if not directory.is_relative_to(ROOT/'build'):raise ValueError('Profiles require ignored prepared artwork')
        raw=(directory/'art.json').read_bytes();art=json.loads(raw)
        if art['format']!='AFV3-AUTO-FURNITURE-PREPARED-ASSETS-1':raise ValueError('Expected complete prepared furniture category')
        evidence.append(dict(directory=str(directory.relative_to(ROOT)),sha256=sha256(raw)))
        for row in art['objects']:
            donor=row['item_id'];item=int(donor,16);prepared_row=prepare(source,item)
            descriptor=prepared_row[0];category=descriptor.get('callback_adapter',{}).get('category')
            if (category not in (CLOCK_CATEGORY,STORAGE_CATEGORY,'switch-trigger-sound') or
                    donor in occupied or item not in identities or
                    row['profile']!=json.loads(json.dumps(descriptor)) or
                    row['native_profile_scalar_hex']!=descriptor['scalar_hex']):
                raise ValueError('Unsupported, duplicate, or changed complete room category')
            reused=cache.reuse(source,donor,prepared_row)
            if reused is None:raise ValueError('Missing complete prepared profile artwork')
            data=(directory/row['object_file']).read_bytes()
            if len(data)!=row['object_bytes'] or sha256(data)!=row['object_sha256']:
                raise ValueError('Changed complete prepared profile object')
            index,destination=furniture_representation_identity(item);i=slot(destination)
            if destination!=item or index!=1024+i:
                raise ValueError('Parent/display aliases require their shared parent adapter')
            if any(identities[item][1].get(k)!='-' for k in ('C','H','CG','CJ')):
                raise ValueError('Staged identity needs native correspondence review')
            if (any(blob[ROWS+i*80:ROWS+(i+1)*80]) or any(blob[ITEMS+i*32:ITEMS+(i+1)*32]) or
                    blob[0x40+i//8]&(1<<(i&7))):raise ValueError('Profile staging overwrites an existing or selected identity')
            if category in (CLOCK_CATEGORY,STORAGE_CATEGORY):
                installed=rigs.get(donor)
                if (not installed or installed['profile_installed'] or installed['source']!=row or
                        installed['bytes']!=len(data) or installed['sha256']!=sha256(data) or
                        blob[installed['blob_offset']:installed['blob_offset']+len(data)]!=data):
                    raise ValueError('Prepared rig is not completely installed in the current runtime')
                vrom=installed['vrom'];vtable=VTABLE;reused_asset=True
            else:
                installed=sounds.get(donor);audio=result.get('furniture_audio',{})
                audio_row=next((r for r in audio.get('furniture',[]) if r['item_id']==donor),None)
                if (not installed or installed['profile_installed'] or not audio_row or
                        audio_row['callback']!=json.loads(json.dumps(descriptor['callback_adapter'])) or
                        not all(audio.get(k) for k in ('runtime_installed','dispatch_and_priority_installed',
                            'allocation_installed','callback_installed'))):
                    raise ValueError('Sound furniture lacks its complete installed audio/callback')
                blob.extend(bytes(-len(blob)%16));vrom=BLOB+len(blob);blob.extend(data)
                if vrom+len(data)>limit:raise ValueError('Complete sound models exceed checked import reservation')
                vtable=SOUND_VTABLE;reused_asset=False
                installed.update(blob_offset=vrom-BLOB,vrom=vrom,bytes=len(data),sha256=sha256(data),source=row)
            generated=copy.deepcopy(row);generated['room_runtime']=dict(vtable=vtable,vrom=vrom)
            native=profile(generated,vrom,limit=limit)
            if len(native)!=68:raise ValueError('Incomplete ordinary furniture profile')
            names=name_metadata(source,item,identities[item])
            price=struct.unpack_from('>H',source.raw('ftr_price_table'),index*2)[0]
            record=struct.pack('>HHHBB',index,item,price,descriptor['size_code'],0)+names['name'].encode().ljust(16,b' ')+bytes(8)
            profile_record=struct.pack('>HHI',index,item,0)+native+bytes(4)
            blob[ROWS+i*80:ROWS+(i+1)*80]=profile_record
            blob[ITEMS+i*32:ITEMS+(i+1)*32]=record
            installed.update(profile_installed=True,parent_selectable=False)
            staged.append(dict(**names,category=category,price=price,size_code=descriptor['size_code'],
                object_vrom=vrom,object_bytes=len(data),object_sha256=sha256(data),reused_asset=reused_asset,
                profile_ram=ROWS_RAM+i*80+8,profile_hex=native.hex(),profile_record_sha256=sha256(profile_record),
                item_record_sha256=sha256(record),source_profile_sha256=descriptor['profile_sha256'],
                room_runtime=generated['room_runtime'],profile_installed=True,item_record_installed=True,
                selected=False,acquisition_installed=False,catalogue_installed=False,scoring_installed=False))
            occupied.add(donor)
    if not staged:raise ValueError('Empty complete furniture profile batch')
    old['rows']=sorted(old['rows']+staged,key=lambda r:r['runtime_index']);old['sources'].extend(evidence)
    old.update(profile_bits_changed=False,additional_resident_bytes=0)
    patch=provenance_patch(staged)
    if patch:write_new(output/'provenance.patch',patch.encode())
    return result,{},dict(staged_furniture=old)


def bind_profiles(source,base,report):
    """Expose checked installed lifecycles to the ordinary category importer.

    Staged records remain inactive. This removes only the lifecycle prerequisite;
    normal acquisition, catalogue, scoring, and selection checks still apply.
    """
    from v3_furniture_install import profile
    source.runtime_profiles={}
    staged=report.get('staged_furniture',{})
    activated=[r for r in report['furniture']['imports'] if r.get('room_runtime')]
    if not staged and not activated:return source.runtime_profiles
    if staged and staged['format']!='AFV3-STAGED-FURNITURE-PROFILES-1':
        raise ValueError('Unknown staged furniture profile format')
    blob=by_vrom(base)[BLOB].extract(base);e=report['equipment_resources'];runtime=e['room_rigs']
    packet=runtime['packet'];raw=blob[packet['blob_offset']:packet['blob_offset']+packet['bytes']]
    module=blob[e['blob_offset']:e['blob_offset']+e['bytes']]
    if (sha256(blob)!=report['blob_sha256'] or sha256(raw)!=packet['sha256'] or
            sha256(module)!=e['sha256'] or raw[PACKET_TABLE-PACKET_RAM:]!=encode_packet(runtime['rows'],runtime['sound_rows']) or
            module[VTABLE-EQUIPMENT_RAM:VTABLE-EQUIPMENT_RAM+20].hex()!=runtime['vtable_hex'] or
            module[SOUND_VTABLE-EQUIPMENT_RAM:SOUND_VTABLE-EQUIPMENT_RAM+20].hex()!=runtime['sound_vtable_hex'] or
            blob[0x20:0xE0].hex()!=report['save_runtime']['profile_hex']):
        raise ValueError('Changed installed furniture lifecycle, packet, or selection')
    limit=checked_limit(base,report)
    bindings={r['source_item_id']:r for r in runtime['rows']+runtime['sound_rows']}
    for row,enabled in [(r,False) for r in staged.get('rows',[])]+[(r,True) for r in activated]:
        item=int(row['item_id'],16);i=slot(item);binding=bindings.get(row['item_id'])
        if (row['item_id'] in source.runtime_profiles or not binding or not binding['profile_installed'] or
                row['runtime_index']!=1024+i or binding['runtime_index']!=1024+i or
                bool(blob[0x40+i//8]&(1<<(i&7)))!=enabled):
            raise ValueError('Changed furniture profile identity or activation')
        descriptor=prepare(source,item)[0];art=copy.deepcopy(binding['source']);vrom=binding['vrom']
        expected_vtable=SOUND_VTABLE if descriptor['callback_adapter']['category']=='switch-trigger-sound' else VTABLE
        art['room_runtime']=dict(vtable=expected_vtable,vrom=vrom)
        at=vrom-BLOB;n=art['object_bytes'];native=profile(art,vrom,limit=limit)
        current=blob[ROWS+i*80:ROWS+(i+1)*80];record=blob[ITEMS+i*32:ITEMS+(i+1)*32]
        expected=struct.pack('>HHI',1024+i,item,int(enabled))+native+bytes(4)
        if (art['profile']!=json.loads(json.dumps(descriptor)) or row['room_runtime']!=art['room_runtime'] or
                not 0<=at<at+n<=len(blob) or sha256(blob[at:at+n])!=art['object_sha256'] or
                current!=expected or record[:8]!=struct.pack('>HHHBB',1024+i,item,row['price'],descriptor['size_code'],int(enabled)) or
                record[8:24]!=row['name'].encode().ljust(16,b' ') or
                sha256(record)!=row['record_sha256' if enabled else 'item_record_sha256'] or
                not enabled and (sha256(current)!=row['profile_record_sha256'] or row['selected'])):
            raise ValueError('Changed complete installed furniture profile, artwork, or item record')
        source.runtime_profiles[row['item_id']]=dict(room_runtime=art['room_runtime'],
            source_profile_sha256=descriptor['profile_sha256'],category=descriptor['callback_adapter']['category'],
            object_sha256=art['object_sha256'],object_bytes=n,profile_hex=native.hex(),staged=not enabled)
    return source.runtime_profiles


def reuse_profile(source,row,asset,blob,*,limit):
    """Promote a checked inactive record without duplicating its complete model."""
    from v3_furniture_install import profile
    binding=getattr(source,'runtime_profiles',{}).get(row['item_id'])
    if binding is None:return None
    i=slot(int(row['item_id'],16));vrom=binding['room_runtime']['vrom'];at=vrom-BLOB
    native=profile(row,vrom,limit=limit)
    if (not binding['staged'] or row.get('room_runtime')!=binding['room_runtime'] or
            len(asset)!=binding['object_bytes'] or sha256(asset)!=binding['object_sha256'] or
            blob[at:at+len(asset)]!=asset or native.hex()!=binding['profile_hex'] or
            blob[ROWS+i*80:ROWS+(i+1)*80]!=struct.pack('>HHI',row['runtime_index'],int(row['item_id'],16),0)+native+bytes(4) or
            blob[ITEMS+i*32:ITEMS+(i+1)*32]!=struct.pack('>HHHBB',row['runtime_index'],int(row['item_id'],16),row['price'],row['size_code'],0)+row['name'].encode().ljust(16,b' ')+bytes(8)):
        raise ValueError('Changed staged record or model during ordinary furniture promotion')
    return vrom,native


def prepared_categories(source,directories):
    """Use the normal complete-art cache for all implemented room rig categories."""
    rows=[];assets={};evidence=[]
    for directory in directories:
        directory=directory.resolve()
        if not directory.is_relative_to(ROOT/'build'):raise ValueError('Room rigs require ignored prepared assets')
        cache=PreparedAssets(source,[directory]);raw=(directory/'art.json').read_bytes();art=json.loads(raw)
        if art['format']!='AFV3-AUTO-FURNITURE-PREPARED-ASSETS-1':raise ValueError('Expected complete prepared room rigs')
        for row in art['objects']:
            donor=row['item_id'];item=int(donor,16);prepared_row=prepare(source,item)
            profile=prepared_row[0];adapter=profile.get('callback_adapter',{});category=adapter.get('category')
            if category not in (CLOCK_CATEGORY,STORAGE_CATEGORY):
                raise ValueError('Unimplemented additional room-rig category')
            if (row['profile']!=json.loads(json.dumps(profile)) or donor in assets or
                    row['native_profile_scalar_hex']!=profile['scalar_hex'] or
                    profile['skeleton']['joints']>6 or any(r.get('draw_stream') for r in profile['skeleton']['rows'])):
                raise ValueError('Changed room-rig profile or native work capacity')
            cache.reuse(source,donor,prepared_row)
            data=(directory/row['object_file']).read_bytes()
            if len(data)>9216:raise ValueError('Complete rig exceeds room bank')
            rig=row['rig'];index,destination=furniture_representation_identity(item)
            if category==CLOCK_CATEGORY:
                mode=1;first=adapter['clock']['hour_joint'];last=adapter['clock']['minute_joint']
            else:
                mode=2;first=int(adapter['constants']['start_frame']['hex'],16)
                last=int(adapter['constants']['end_frame']['hex'],16)
            rows.append(dict(source_item_id=donor,item_id=f'{destination:04X}',runtime_index=index,
                bytes=len(data),sha256=sha256(data),category=category,mode=mode,first=first,last=last,
                skeleton=0x06000000+rig['skeleton_offset'],animation=0x06000000+rig['animation_offset'],
                joints=rig['skeleton']['joints'],shown=rig['skeleton']['shown_joints'],source=row,
                profile_installed=False,parent_selectable=False))
            assets[donor]=data
        evidence.append(dict(directory=str(directory.relative_to(ROOT)),sha256=sha256(raw),
                             source_rel_sha256=sha256(source.rel)))
    if not rows:raise ValueError('Empty additional room-rig batch')
    return sorted(rows,key=lambda r:r['runtime_index']),assets,evidence


def encode_packet(rows,sound_rows=()):
    if not rows or len(rows)>PACKET_CAPACITY:raise ValueError('Room-rig packet capacity exceeded')
    if [r['runtime_index'] for r in rows]!=sorted({r['runtime_index'] for r in rows}):
        raise ValueError('Unordered or duplicate room-rig records')
    table=bytearray(struct.pack('>4I',PACKET_MAGIC,len(rows),24,0))
    for r in rows:
        encode([r])  # Retain the complete existing object/pointer/work-area checks.
        mode,first,last=r.get('mode',0),r.get('first',0),r.get('last',0)
        if (mode not in (0,1,2) or mode==0 and (first or last) or
                mode==1 and not (0<first<r['joints'] and 0<last<r['joints'] and first!=last) or
                mode==2 and not 0x3F800000<=first<last<=0x43800000):
            raise ValueError('Invalid complete room-rig behaviour parameters')
        table.extend(struct.pack('>HHIIBBBBII',r['runtime_index'],r['bytes'],r['skeleton'],r['animation'],
                                 r['joints'],r['shown'],mode,0,first,last))
    if sound_rows:
        if (len(sound_rows)>SOUND_CAPACITY or
                [r['runtime_index'] for r in sound_rows]!=sorted({r['runtime_index'] for r in sound_rows})):
            raise ValueError('Unordered, duplicate, or excessive room-sound records')
        table.extend(bytes(SOUND_TABLE-PACKET_TABLE-len(table)))
        table.extend(struct.pack('>4I',SOUND_MAGIC,len(sound_rows),8,0))
        for r in sound_rows:
            word=r['native_sound_word']
            if (not 1024<=r['runtime_index']<2048 or not 0<=word<=65535 or
                    word&0x80 or (word&0x7FFF)>>8 not in (1,4)):
                raise ValueError('Invalid room sound identity or full native sound word')
            table.extend(struct.pack('>HHI',r['runtime_index'],word,0))
    return bytes(table).ljust(PACKET_BYTES-(PACKET_TABLE-PACKET_RAM),b'\0')


def extended_contract(base,core,original):
    """Native storage owns its existing state machine, audio, and room interaction."""
    current=by_vrom(base)[0x82D7F0].extract(base);native=by_vrom(original)[0x82D7F0].extract(original)
    a,b=0x8094630C-0x80936710,0x809465CC-0x80936710
    if sha256(native[a:b])!='3453821b77da92ff7456b8c495c9c9cbb2e6372ce303400bec0e2d08473fb37e':
        raise ValueError('Changed complete native storage state machine')
    expected=bytearray(native[a:b])
    # The installed shared profile table is the only change to the native helper.
    struct.pack_into('>I',expected,0x24,0x3C188047)
    struct.pack_into('>I',expected,0x30,0x8F180010)
    c,d=0x80939050-0x80936710,0x8093919C-0x80936710
    if (current[a:b]!=expected or current[c:d]!=native[c:d] or
            sha256(native[c:d])!='829a1b5c83b3284fe2e0174932f22be1ad56e184b4540017259fe6b229ed381a'):
        raise ValueError('Changed native room clip registration or storage profile binding')
    n=by_vrom(original)[CODE_VROM].extract(original);a,b=0x80052228-CODE_RAM,0x80053170-CODE_RAM
    if core[a:b]!=n[a:b]:raise ValueError('Changed native complete keyframe APIs')
    return dict(storage_owner_vrom=0x82D7F0,storage_helper=0x8094630C,
        storage_helper_sha256=sha256(expected),clip_registration_sha256=sha256(native[c:d]),
        room_clip=0x80136F2C,open_close_offset=0x34,hour=0x80136FC6,minute=0x80136FC4,
        keyframe_api_sha256=sha256(n[a:b]),native_storage_speed=1.0,source_storage_speed=0.5)


def publish_packet(equipment,blob,output):
    """Compile shared behaviour once and publish it through the stable room vtable."""
    runtime=equipment['room_rigs'];packet=runtime['packet'];at=packet['blob_offset']
    sound_rows=runtime.get('sound_rows',[])
    defines=('AF_V3_ROOM_RIG_PACKET',)+(('AF_V3_ROOM_TRIGGER_SOUND',) if sound_rows else ())
    code,compiled=compile_part('room_rigs_packet',output/'room_rigs_packet',
        primary_source='overlays/v3/room_rigs.c',defines=defines)
    table=encode_packet(runtime['rows'],sound_rows)
    data=code.ljust(PACKET_TABLE-PACKET_RAM,b'\0')+table
    if len(code)>PACKET_TABLE-PACKET_RAM or len(data)!=PACKET_BYTES or not zlib.crc32(data):
        raise ValueError('Room code/table exceeds owned packet or has an invalid cache identity')
    symbols=compiled['symbols'];entries=[symbols['af_v3_room_rig_'+role] for role in ('ct','mv','dw')]
    if any(p&3 or not PACKET_RAM<=p<PACKET_RAM+len(code) for p in entries):
        raise ValueError('Room lifecycle entry escapes packet')
    sound_defines=()
    if sound_rows:
        entry=symbols['af_v3_room_sound_mv']
        if entry&3 or not PACKET_RAM<=entry<PACKET_RAM+len(code):raise ValueError('Room sound entry escapes packet')
        sound_defines=(f'AF_ROOM_SOUND_MV=0x{entry:X}u',)
    boot,bootstrap=compile_part('room_rigs_bootstrap',output/'room_rigs_bootstrap',defines=(
        f'AF_ROOM_VROM=0x{BLOB+at:X}u',f'AF_ROOM_BYTES={PACKET_BYTES}u',f'AF_ROOM_CRC=0x{zlib.crc32(data):X}u',
        *(f'AF_ROOM_{role.upper()}=0x{entry:X}u' for role,entry in zip(('ct','mv','dw'),entries)),*sound_defines))
    start=equipment['blob_offset'];module=bytearray(blob[start:start+equipment['bytes']])
    if sha256(module)!=equipment['sha256']:raise ValueError('Changed installed equipment before room publication')
    entries=[bootstrap['symbols']['af_v3_room_boot_'+role] for role in ('ct','mv','dw')]
    if len(boot)>TABLE-RAM or any(p&3 or not RAM<=p<RAM+len(boot) for p in entries):
        raise ValueError('Room bootstrap escapes stable reservation')
    vtable=struct.pack('>5I',*entries,0,0)
    module[RAM-EQUIPMENT_RAM:TABLE-EQUIPMENT_RAM]=boot+bytes(TABLE-RAM-len(boot))
    module[TABLE-EQUIPMENT_RAM:VTABLE-EQUIPMENT_RAM]=bytes(VTABLE-TABLE)
    module[VTABLE-EQUIPMENT_RAM:VTABLE-EQUIPMENT_RAM+20]=vtable
    if sound_rows:
        entry=bootstrap['symbols']['af_v3_room_boot_sound_mv']
        if entry&3 or not RAM<=entry<RAM+len(boot):raise ValueError('Room sound bootstrap escapes reservation')
        before=module[SOUND_VTABLE-EQUIPMENT_RAM:SOUND_VTABLE-EQUIPMENT_RAM+20]
        if before!=bytes.fromhex(runtime.get('sound_vtable_hex','00'*20)):
            raise ValueError('Occupied room sound vtable reservation')
        sound_vtable=struct.pack('>5I',0,entry,0,0,0)
        module[SOUND_VTABLE-EQUIPMENT_RAM:SOUND_VTABLE-EQUIPMENT_RAM+20]=sound_vtable
        runtime.update(sound_vtable=SOUND_VTABLE,sound_vtable_hex=sound_vtable.hex(),sound_table=SOUND_TABLE)
    blob[at:at+len(data)]=data;blob[start:start+len(module)]=module
    packet.update(sha256=sha256(data),crc32=zlib.crc32(data))
    runtime.update(code=compiled,bootstrap=bootstrap,table_sha256=sha256(table),
                   vtable_hex=vtable.hex(),catalogue_index_supported=True)
    equipment.update(sha256=sha256(module),crc32=zlib.crc32(module))


def extend(base,prior,blob,core,original,output,directories):
    old=prior['equipment_resources'];runtime=old['room_rigs'];start=old['blob_offset']
    module=blob[start:start+old['bytes']];scenery=old['scenery']
    if (sha256(module)!=old['sha256'] or EQUIPMENT_RAM+old['bytes']>PACKET_RAM or
            scenery['ram']+scenery['additional_fixed_resident_bytes']>PACKET_RAM or
            PACKET_RAM+PACKET_BYTES>prior['furniture']['bank_pool']['start'] or
            module[VTABLE-EQUIPMENT_RAM:VTABLE-EQUIPMENT_RAM+20]!=bytes.fromhex(runtime['vtable_hex'])):
        raise ValueError('Changed room module/vtable or occupied packet reservation')
    is_packet=runtime['format']=='AFV3-ROOM-RIGS-2'
    if is_packet:
        packet=runtime['packet'];boot=runtime['bootstrap']
        if sha256(blob[packet['blob_offset']:packet['blob_offset']+PACKET_BYTES])!=packet['sha256']:
            raise ValueError('Changed complete installed room packet')
    elif runtime['format']=='AFV3-ROOM-RIGS-1':
        boot=runtime['code']
        if module[TABLE-EQUIPMENT_RAM:VTABLE-EQUIPMENT_RAM]!=encode(runtime['rows']):
            raise ValueError('Changed complete installed room records')
    else:raise ValueError('Unknown room runtime format')
    if (sha256(module[RAM-EQUIPMENT_RAM:RAM-EQUIPMENT_RAM+boot['bytes']])!=boot['sha256'] or
            any(module[RAM-EQUIPMENT_RAM+boot['bytes']:TABLE-EQUIPMENT_RAM])):
        raise ValueError('Changed complete room lifecycle reservation')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    rows,assets,evidence=prepared_categories(source,directories)
    occupied={r['item_id'] for r in runtime['rows']}
    for r in runtime['rows']:
        if sha256(blob[r['blob_offset']:r['blob_offset']+r['bytes']])!=r['sha256']:
            raise ValueError('Changed installed complete room artwork')
    for r in rows:
        i=slot(int(r['item_id'],16))
        if (r['item_id'] in occupied or any(blob[ROWS+i*80:ROWS+(i+1)*80]) or
                any(blob[ITEMS+i*32:ITEMS+(i+1)*32]) or blob[0x40+i//8]&(1<<(i&7))):
            raise ValueError('Additional room category collides with an installed identity')
    all_rows=sorted(copy.deepcopy(runtime['rows'])+rows,key=lambda r:r['runtime_index']);encode_packet(all_rows)
    needed=sum(len(d) for d in assets.values())+(0 if is_packet else PACKET_BYTES)
    reuse=retired_module_space(base,prior,blob,needed)
    contract=extended_contract(base,core,original)
    if reuse:
        cursor=reuse['blob_offset']
    else:
        cursor=(len(blob)+15)&~15
        if BLOB+cursor+needed>checked_limit(base,prior):
            raise ValueError('Complete room category exceeds checked cartridge reservation')
        blob.extend(bytes(cursor+needed-len(blob)))
    result=copy.deepcopy(old);installed=result['room_rigs']
    if not is_packet:
        installed['packet']=dict(ram=PACKET_RAM,bytes=PACKET_BYTES,blob_offset=cursor,vrom=BLOB+cursor)
        cursor+=PACKET_BYTES
    for r in rows:
        data=assets[r['source_item_id']];at=cursor;cursor+=len(data)
        blob[at:cursor]=data;r.update(blob_offset=at,vrom=BLOB+at)
    installed.update(format='AFV3-ROOM-RIGS-2',categories=[CATEGORY,CLOCK_CATEGORY,STORAGE_CATEGORY],rows=all_rows,
        table_ram=PACKET_TABLE,capacity=PACKET_CAPACITY,ram=PACKET_RAM,extended_native_contract=contract,
        additional_resident_bytes=0 if is_packet else PACKET_BYTES,
        artwork_bytes=runtime['artwork_bytes']+sum(len(d) for d in assets.values()))
    installed.setdefault('additional_sources',[]).extend(evidence)
    installed.setdefault('reservations',[]).append(reuse or dict(
        blob_offset=cursor-needed,bytes=needed,appended=True))
    publish_packet(result,blob,output)
    result['additional_resident_bytes']=installed['additional_resident_bytes']
    return result,{}


def prepared(source,directory):
    """Verify the category's complete prepared data without recompiling graphics."""
    directory=directory.resolve();raw=(directory/'art.json').read_bytes();art=json.loads(raw)
    if (not directory.is_relative_to(ROOT/'build') or art['format']!='AFV3-AUTO-FURNITURE-PREPARED-ASSETS-1'
            or art['source_rel_sha256']!=sha256(source.rel)
            or art['source_symbols_sha256']!=sha256(source.symbols.encode())):
        raise ValueError('Changed complete prepared room-rig source')
    aliases={r['display_item_id']:r for r in room_aliases(source)['rows'] if r['room_placement_uses_display']}
    rows=[];assets={};seen=set()
    for row in art['objects']:
        donor=row['item_id'];item=int(donor,16)
        if donor in seen or donor not in aliases:raise ValueError('Unreviewed or duplicate room-rig parent')
        seen.add(donor);alias=aliases[donor]
        descriptor,body,resources,_,models,commands,sections=prepare(source,item)
        rig=descriptor.get('callback_adapter',{})
        if (rig.get('category')!=CATEGORY or row['profile']!=json.loads(json.dumps(descriptor))
                or row['resources']!=resources or row.get('room_alias')!=alias
                or descriptor['skeleton']['joints']>6 or
                any(r.get('draw_stream') for r in descriptor['skeleton']['rows'])
                or row['native_profile_scalar_hex']!=descriptor['scalar_hex']):
            raise ValueError('Changed complete room-rig category or native work capacity')
        path=(directory/row['object_file']).resolve()
        if path.parent!=directory:raise ValueError('Room asset escapes prepared directory')
        data=path.read_bytes();artwork=(len(body)+sum(n for _,n in sections)+15)&~15
        tail,receipt=suffix(source,descriptor,row['model_offsets'],start=artwork)
        if (len(data)!=row['object_bytes'] or sha256(data)!=row['object_sha256']
                or len(data)>9216 or data[:len(body)]!=body or data[artwork:]!=tail
                or row['rig']!=json.loads(json.dumps(receipt))
                or (directory/donor/'commands.c').read_text()!=commands
                or len(row['models'])!=len(sections) or set(row['model_offsets'])!=set(models)):
            raise ValueError('Changed complete room-rig resource or emitter input')
        cursor=len(body)
        for model,(label,size) in zip(row['models'],sections):
            if (model['layer']!=label or model['native_offset']!=cursor or row['model_offsets'][label]!=cursor
                    or model['bytes']!=size or model['source_sha256']!=models[label]['source_sha256']
                    or sha256(data[cursor:cursor+size])!=model['output_sha256']):
                raise ValueError('Changed complete room-rig drawing commands')
            cursor+=size
        if any(data[cursor:artwork]):raise ValueError('Changed room-rig alignment padding')
        index,destination=furniture_representation_identity(item)
        records=dict(source_item_id=donor,parent_item_id=alias['parent_item_id'],
            item_id=f'{destination:04X}',runtime_index=index,bytes=len(data),sha256=sha256(data),
            skeleton=0x06000000+receipt['skeleton_offset'],animation=0x06000000+receipt['animation_offset'],
            joints=receipt['skeleton']['joints'],shown=receipt['skeleton']['shown_joints'],
            source=row,profile_installed=False,parent_selectable=False)
        rows.append(records);assets[donor]=data
    if not rows or len(rows)>CAPACITY or set(aliases)!=seen:
        raise ValueError('Prepared room-rig bundle omits a complete source category')
    rows.sort(key=lambda r:r['runtime_index'])
    if len({r['runtime_index'] for r in rows})!=len(rows):raise ValueError('Colliding room-rig destinations')
    return rows,assets,dict(directory=str(directory.relative_to(ROOT)),sha256=sha256(raw),
        source_rel_sha256=sha256(source.rel),registry_version=ROOM_ALIAS_REGISTRY_VERSION)


def encode(rows):
    if not rows or len(rows)>CAPACITY:raise ValueError('Room-rig record capacity exceeded')
    indices=[r['runtime_index'] for r in rows]
    if indices!=sorted(set(indices)):raise ValueError('Unordered or duplicate room-rig records')
    table=bytearray(struct.pack('>4I',MAGIC,len(rows),16,0))
    for r in rows:
        if (r['runtime_index']!=1024+slot(int(r['item_id'],16)) or
                not 32<=r['bytes']<=9216 or r['bytes']%16 or
                not 1<=r['shown']<=r['joints']<=6 or
                any(p&3 or not 0x06000000<=p<=0x06000000+r['bytes']-n for p,n in
                    ((r['skeleton'],8),(r['animation'],20)))):
            raise ValueError('Invalid complete room-rig record')
        table.extend(struct.pack('>HHIIHH',r['runtime_index'],r['bytes'],r['skeleton'],r['animation'],r['joints'],r['shown']))
    return bytes(table).ljust(VTABLE-TABLE,b'\0')


def install(base,prior,blob,core,original,output,directory):
    directories=list(directory) if isinstance(directory,(list,tuple)) else [directory]
    if prior['equipment_resources'].get('room_rigs'):
        return extend(base,prior,blob,core,original,output,directories)
    if len(directories)!=1:raise ValueError('Initial room runtime requires one complete category')
    directory=directories[0]
    old=prior['equipment_resources'];start=old['blob_offset'];offset=RAM-EQUIPMENT_RAM
    module=bytearray(blob[start:start+old['bytes']])
    if (old.get('room_rigs') or not old.get('inventory_preview',{}).get('balloon_drawer') or
            sha256(module)!=old['sha256'] or len(module)!=0xF000 or
            any(module[offset:LIMIT-EQUIPMENT_RAM]) or
            old['held_rig_actions']['code']['bytes']>RAM-0x804B0000):
        raise ValueError('Room rigs require the checked unused module reservation')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    rows,assets,evidence=prepared(source,directory)
    for r in rows:
        i=slot(int(r['item_id'],16))
        if any(blob[ROWS+i*80:ROWS+(i+1)*80]) or any(blob[ITEMS+i*32:ITEMS+(i+1)*32]) or blob[0x40+i//8]&(1<<(i&7)):
            raise ValueError('Room-rig reservation collides with installed data or a selected identity')
    contract=native_contract(original,base,expected_sha=sha256(base))
    native=by_vrom(original)[CODE_VROM].extract(original)
    # Complete native construction/initialization/play/draw code owns at most
    # (joints+1) work vectors. The last two morph vectors remain callback-owned.
    first,last=0x80052228,0x80053170
    if core[first-CODE_RAM:last-CODE_RAM]!=native[first-CODE_RAM:last-CODE_RAM]:
        raise ValueError('Changed complete native keyframe ownership or rendering APIs')
    contract=dict(blocks=contract['blocks'],actor_bytes=0x740,keyframe=0x134,joint=0x1A4,morph=0x1DA,
        work_vectors=7,state=0x204,state_bytes=8,matrix=0x210,matrix_bank_bytes=0x280,
        keyframe_api_sha256=sha256(core[first-CODE_RAM:last-CODE_RAM]))
    code,compiled=compile_part('room_rigs',output/'room_rigs')
    if len(code)>TABLE-RAM:raise ValueError('Room-rig code escapes its reservation')
    needed=sum(len(d) for d in assets.values());reuse=retired_module_space(base,prior,blob,needed)
    cursor=reuse['blob_offset'] if reuse else len(blob)
    for r in rows:
        data=assets[r['source_item_id']];cursor=(cursor+15)&~15;at=cursor;cursor+=len(data)
        if reuse:
            if cursor>reuse['blob_offset']+reuse['bytes']:raise ValueError('Room rigs exceed reusable resource bounds')
            blob[at:cursor]=data
        else:
            if BLOB+cursor>END:raise ValueError('Complete room rigs exceed checked ROM storage')
            blob.extend(bytes(at-len(blob)));blob.extend(data)
        r.update(blob_offset=at,vrom=BLOB+at)
    table=encode(rows);entries=[compiled['symbols']['af_v3_room_rig_'+r] for r in ('ct','mv','dw')]
    if any(p&3 or not RAM<=p<RAM+len(code) for p in entries):raise ValueError('Room-rig vtable escapes code')
    vtable=struct.pack('>5I',*entries,0,0)
    module[offset:offset+len(code)]=code
    module[TABLE-EQUIPMENT_RAM:VTABLE-EQUIPMENT_RAM]=table
    module[VTABLE-EQUIPMENT_RAM:VTABLE-EQUIPMENT_RAM+len(vtable)]=vtable
    report=copy.deepcopy(old)
    report['room_rigs']=dict(format='AFV3-ROOM-RIGS-1',category=CATEGORY,rows=rows,source=evidence,
        code=compiled,ram=RAM,table_ram=TABLE,table_sha256=sha256(table),capacity=CAPACITY,
        vtable=VTABLE,vtable_hex=vtable.hex(),native_contract=contract,retired_space=reuse,
        artwork_bytes=needed,additional_resident_bytes=0,saved_format_changed=False,
        profile_bits_enabled=0,ordinary_room_tested=False,hardware_tested=False)
    report.update(sha256=sha256(module),crc32=zlib.crc32(module),additional_resident_bytes=0)
    blob[start:start+len(module)]=module
    return report,{}


def refresh_code(equipment,blob,output):
    """Retain full room resources while connecting an additional native consumer."""
    runtime=equipment['room_rigs']
    if runtime['format']=='AFV3-ROOM-RIGS-2':
        packet=runtime['packet'];at=packet['blob_offset']
        if sha256(blob[at:at+PACKET_BYTES])!=packet['sha256']:raise ValueError('Changed complete room packet')
        return publish_packet(equipment,blob,output)
    old=runtime['code'];start=equipment['blob_offset']
    module=bytearray(blob[start:start+equipment['bytes']]);at=RAM-EQUIPMENT_RAM
    if (sha256(module)!=equipment['sha256'] or sha256(module[at:at+old['bytes']])!=old['sha256'] or
            any(module[at+old['bytes']:TABLE-EQUIPMENT_RAM]) or
            module[VTABLE-EQUIPMENT_RAM:VTABLE-EQUIPMENT_RAM+20]!=bytes.fromhex(runtime['vtable_hex'])):
        raise ValueError('Changed complete installed room lifecycle reservation')
    code,compiled=compile_part('room_rigs',output/'room_rigs')
    entries=[compiled['symbols']['af_v3_room_rig_'+role] for role in ('ct','mv','dw')]
    if len(code)>TABLE-RAM or any(p&3 or not RAM<=p<RAM+len(code) for p in entries):
        raise ValueError('Changed room lifecycle bounds')
    table=struct.pack('>5I',*entries,0,0)
    module[at:TABLE-EQUIPMENT_RAM]=code+bytes(TABLE-RAM-len(code))
    module[VTABLE-EQUIPMENT_RAM:VTABLE-EQUIPMENT_RAM+20]=table
    runtime.update(code=compiled,vtable_hex=table.hex(),catalogue_index_supported=True)
    equipment.update(sha256=sha256(module),crc32=zlib.crc32(module))
    blob[start:start+len(module)]=module
