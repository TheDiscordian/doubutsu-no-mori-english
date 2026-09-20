"""Install complete shared room rigs without enabling unfinished parent imports."""
import copy
import json
import struct
import zlib

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256
from v3_asset_loader import ROOT,BLOB,compile_part
from v3_equipment_runtime import RAM as EQUIPMENT_RAM,retired_module_space
from v3_furniture_pipeline import Source,prepare,room_aliases
from v3_furniture_rigs import CATEGORY,suffix
from v3_registry import furniture_representation_identity,ROOM_ALIAS_REGISTRY_VERSION
from v3_import_storage import ROWS,ITEMS,slot,END
from v3_tent_model import native_contract

RAM,TABLE,VTABLE,LIMIT,CAPACITY = 0x804B1800,0x804B1E00,0x804B1FA0,0x804B1FE0,24
MAGIC=0x41465231
SOURCES=('tools/v3_room_rig_runtime.py','tools/v3_asset_loader.py','tools/v3_furniture_rigs.py','tools/v3_keyframes.py',
    'tools/v3_furniture_pipeline.py','tools/v3_registry.py','tools/v3_equipment_runtime.py',
    'overlays/v3/room_rigs.c','overlays/v3/room_rigs.h','overlays/v3/room_rigs.ld',
    'overlays/v3/held_rigs.ld')


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
        if any(blob[ROWS+i*80:ROWS+(i+1)*80]) or any(blob[ITEMS+i*32:ITEMS+(i+1)*32]) or blob[32+i//8]&(1<<(i&7)):
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
