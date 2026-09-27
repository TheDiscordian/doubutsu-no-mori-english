"""Shared native player/tree interaction bindings, composed with existing imports."""
import copy
import json
import re
import struct
import zlib

from aflib import CODE_VROM,CODE_RAM,by_vrom,sha256,u32,verified_rom
from v3_asset_loader import ROOT,BLOB
from v3_import_storage import jump
from v3_npc_clothing import guard_incoming
from v3_player_actions import native_references

PLAYER_VROM=0x7AC420
PLAYER_RELOC=0x7D9BA0
PLAYER_RAM=0x808B2D50
IMPACTS=((0x808CB160,'af_insect_player_axe',1,15),
         (0x808D1F9C,'af_insect_player_rock',2,13),
         (0x808D0798,'af_insect_player_dig',3,14))


def contract(image,prior,source):
    files=by_vrom(image)
    original=verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    retail=by_vrom(original)
    owner=files[PLAYER_VROM].extract(image);native=retail[PLAYER_VROM].extract(original)
    rel=files[PLAYER_RELOC].extract(image);sections=struct.unpack_from('>4I',rel)
    _,_,_,locations,_=native_references(owner,rel,expected_sections=sections)
    definitions=(ROOT/'upstream/af/linker_scripts/jp/symbol_addrs_overlays.txt').read_text()
    starts=sorted({int(a,16) for a in re.findall(r'= (0x[0-9A-Fa-f]+); // type:func',definitions)})
    functions=[]
    for start in (0x808B5698,0x808B56C4,0x808B5844,0x808B9594,
                  0x808CAE00,0x808CB104,0x808D0258,0x808D0748,0x808D1380,0x808D1F4C):
        end=next(a for a in starts if a>start);raw=owner[start-PLAYER_RAM:end-PLAYER_RAM]
        if not raw or raw!=native[start-PLAYER_RAM:end-PLAYER_RAM]:
            raise ValueError('Changed complete native player insect-event dependency')
        functions.append(dict(address=start,end=end,sha256=sha256(raw)))
    hooks=[]
    guard_incoming(owner,sections[0],PLAYER_RAM,[(a-PLAYER_RAM,4) for a,*_ in IMPACTS])
    for address,symbol,action,frame in IMPACTS:
        at=address-PLAYER_RAM
        if (struct.unpack_from('>II',owner,at)!=(jump(0x808B9594,link=True),0x00003825)
                or at not in locations or locations[at]>>24!=0x44):
            raise ValueError('Changed native impact call or relocation')
        hooks.append(dict(offset=at,address=address,symbol=symbol,before=owner[at:at+4].hex(),
                          action=action,frame=frame,removed_relocation=locations[at]))
    donor=[]
    for name,digest in (
        ('Player_actor_informed_insects_Reflect_axe','7a501ed8a368868d699d2f360fe29bef5bf339b5a5160a9bf1eed298a6af620e'),
        ('Player_actor_informed_insects_Reflect_scoop','6c009cd4cb2ebfa72014f892261de840a8e5e45800e12a81ad4990fec86d419a'),
        ('Player_actor_informed_insects_Dig_scoop','8de514ef5228558387298c844aa7514556cdc33c9616e9229789ad1951d13117')):
        matches=[at for at,rows in source.functions.items() if any(n==name for n,_ in rows)]
        if len(matches)!=1:raise ValueError('Ambiguous donor insect-event producer')
        raw,receipt=source.function(matches[0])
        if len(raw)!=176 or sha256(raw)!=digest:raise ValueError('Changed complete donor impact producer')
        donor.append(receipt)
    scenery=prior['equipment_resources']['scenery'];symbols=scenery['code']['symbols']
    blob=files[BLOB].extract(image);data=blob[scenery['blob_offset']:scenery['blob_offset']+scenery['bytes']]
    if sha256(data)!=scenery['sha256']:raise ValueError('Changed installed tree runtime')
    bee=symbols['af_v3_tree_bee_query'];owners=[]
    source_trees=scenery['interactions']['functions']['bg_item_tree_fruit_drop']
    for receipt in source_trees:
        raw,current=source.function(receipt['offset'])
        if sha256(raw)!=receipt['sha256'] or current['bytes']!=380:
            raise ValueError('Changed complete donor tree-shake producer')
    if len(source_trees)!=4:raise ValueError('Missing seasonal tree-shake producers')
    # All plain mature identities deliberately lack a fruit-drop record. Thus
    # retaining the native no-match drop call after notification has no side effect.
    if any(r[0] in (0x804,0x861,0x868) for r in scenery['interactions']['drops']):
        raise ValueError('Plain tree unexpectedly owns a fruit drop')
    for row in scenery['owners']:
        tree=files[row['vrom']].extract(image);tr=files[row['reloc']].extract(image)
        if sha256(tree)!=row['output_sha256'] or sha256(tr)!=row['output_reloc_sha256']:
            raise ValueError('Changed installed seasonal tree owner')
        _,_,_,tl,_=native_references(tree,tr,expected_sections=struct.unpack_from('>4I',tr))
        at=0x2960
        if (struct.unpack_from('>5I',tree,0x2954)!=(0xAFA5005C,0xAFA60060,0x97A4005A,jump(bee,link=True),0)
                or at in tl):raise ValueError('Changed tree item/tile argument contract')
        guard_incoming(tree,u32(tr,0),row['ram'],[(at,4)])
        owners.append(dict(vrom=row['vrom'],reloc=row['reloc'],ram=row['ram'],role=row['role'],
            sha256=sha256(tree),reloc_sha256=sha256(tr),hooks=[dict(offset=at,
                address=row['ram']+at,symbol='af_insect_hook_tree',before=tree[at:at+4].hex())]))
    return dict(player=dict(vrom=PLAYER_VROM,reloc=PLAYER_RELOC,ram=PLAYER_RAM,
            sha256=sha256(owner),reloc_sha256=sha256(rel),hooks=hooks),
        tree_owners=owners,native_functions=functions,source_impacts=donor,source_trees=source_trees,
        bee_query=bee,tree_runtime_sha256=scenery['sha256'],target_position_offset=0xD10,
        frame_control_offset=0x174,events_installed=False)


def install(image,symbols,prepared,changes=None):
    """Merge with other prepared owner patches, rejecting conflicting writes."""
    files=by_vrom(image);changes=dict(changes or {});patches=[]
    for row in [prepared['player'],*prepared['tree_owners']]:
        vrom,rv=row['vrom'],row['reloc']
        original=files[vrom].extract(image);original_rel=files[rv].extract(image)
        if sha256(original)!=row['sha256'] or sha256(original_rel)!=row['reloc_sha256']:
            raise ValueError('Changed prepared player-event owner')
        data=bytearray(changes.get(vrom,original));rel=bytearray(changes.get(rv,original_rel))
        records=list(struct.unpack_from('>'+str(u32(rel,16))+'I',rel,20));removed=[]
        for hook in row['hooks']:
            at=hook['offset'];target=symbols[hook['symbol']]
            if target&3 or not 0x80000000<=target<0x80800000:
                raise ValueError('Player-event bridge is not resident executable RAM')
            if data[at:at+4]!=bytes.fromhex(hook['before']):raise ValueError('Conflicting player-event hook')
            after=struct.pack('>I',jump(target,link=True));data[at:at+4]=after
            if 'removed_relocation' in hook:
                record=hook['removed_relocation']
                if records.count(record)!=1:raise ValueError('Missing impact relocation')
                records.remove(record);removed.append(record)
            patches.append(dict(hook,vrom=vrom,target=target,after=after.hex()))
        changes[vrom]=bytes(data)
        if removed:
            struct.pack_into('>I',rel,16,len(records))
            rel[20:-4]=struct.pack('>'+str(len(records))+'I',*records)+bytes(len(rel)-24-4*len(records))
            changes[rv]=bytes(rel)
    return changes,patches


def prepare_mosquito(image,prior,source,output):
    """Prepare both complete actions and resources for the common final installer."""
    from apply_translation import write_new
    from gc_text import decode_gc
    from runtime_module import module_command_info
    from textcodec import encode,tokenize
    from textvalidate import expanded_bound
    from text_provenance import validate
    from v3_camper_text import donor,extend_bank
    from v3_event_text import MESSAGE,TABLE,CHOICE_TABLE
    from v3_equipment_runtime import player_animation_sources,player_face_sources,FACE_TABLE,FACE_DATA
    original=verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    files,retail=by_vrom(image),by_vrom(original)
    old=prior['equipment_resources'];actions=old['player_actions'];motion=old['player_motion']
    if (sha256(source.rel)!=actions['source_rel_sha256'] or
            sha256(source.symbols.encode())!=actions['source_symbols_sha256']):
        raise ValueError('Changed complete pinned mosquito donor')
    blob=files[BLOB].extract(image);module=blob[old['blob_offset']:old['blob_offset']+old['bytes']]
    if sha256(module)!=old['sha256']:raise ValueError('Changed player action/resource module')
    owner=files[PLAYER_VROM].extract(image);native=retail[PLAYER_VROM].extract(original)
    core=files[CODE_VROM].extract(image);native_core=retail[CODE_VROM].extract(original)
    bounds=sorted({int(a,16) for part in ('code','overlays') for a in re.findall(
        r'= (0x[0-9A-Fa-f]+); // type:func',
        (ROOT/f'upstream/af/linker_scripts/jp/symbol_addrs_{part}.txt').read_text())})
    code=(ROOT/'overlays/v3/creature_insect_mosquito.c').read_text()
    addresses={int(a,16) for a in re.findall(r'FN\((0x[0-9A-F]+)u,',code)}
    # Complete rod setup/cancellation confirms the shared flag's whole lifetime;
    # real native bee-report/settle functions establish music 68 and report type 9.
    addresses.update((0x808CEAA0,0x808CEBD4,0x808DAE7C,0x808DAFB0,0x80051F3C))
    dependencies=[]
    for start in sorted(addresses):
        if start not in bounds:raise ValueError(f'Unknown mosquito player dependency {start:08X}')
        end=next(a for a in bounds if a>start)
        current,before,ram=(owner,native,PLAYER_RAM) if start>=PLAYER_RAM else (core,native_core,CODE_RAM)
        expected=bytearray(before[start-ram:end-ram]);edits=[]
        if start>=PLAYER_RAM:
            for p in actions['patches']:
                at=p['offset']+PLAYER_RAM-start
                if 0<=at<len(expected):
                    if u32(expected,at)!=p['before']:raise ValueError('Changed installed player table patch')
                    struct.pack_into('>I',expected,at,p['after']);edits.append(p)
            for p in actions['reward_exchange']['patches']:
                if p['vrom']!=PLAYER_VROM or not start<=p['address']<end:continue
                at=p['address']-start;before_patch=bytes.fromhex(p['before']);after=bytes.fromhex(p['after'])
                if expected[at:at+len(before_patch)]!=before_patch:
                    raise ValueError('Changed retained reward-request callback')
                expected[at:at+len(after)]=after;edits.append(p)
        raw=current[start-ram:end-ram]
        if raw!=expected:raise ValueError(f'Changed complete mosquito player dependency {start:08X}')
        dependencies.append(dict(address=start,end=end,sha256=sha256(raw),retained_patches=edits))
    donor_functions=[]
    for at,rows in sorted(source.functions.items()):
        names=[name for name,_ in rows]
        if any('mosquito' in name.lower() and name.startswith(('Player_actor_','mPlib_')) for name in names):
            donor_functions.append(source.function(at)[1])
    if len(donor_functions)!=22:raise ValueError('Changed complete mosquito player source inventory')
    donor_functions.append(source.function(0x594)[1]) # actual full keyframe consumer
    for row in actions['tables']:
        data=module[row['offset']:row['offset']+row['bytes']]
        if sha256(data)!=row['sha256']:raise ValueError('Changed complete player action table')
        if row['width']==4:
            if any(data[107*4:109*4]):raise ValueError('Mosquito action slots are already occupied')
        elif data[107:109]!=bytes.fromhex(row['source_hex'])[107:109]:
            raise ValueError('Missing complete source mosquito action metadata')
    assets,records,motion_source=player_animation_sources(source,[132,133],
        capacity=motion['allocation']['bank_bytes'])
    if {r['source_index'] for r in records}&{r['source_index'] for r in motion['records']}:
        raise ValueError('Mosquito animations would replace an installed identity')
    output.mkdir(parents=True,exist_ok=False)
    from v3_asset_loader import compile_part
    _,face_reader=compile_part('player_faces',output/'face-reader',defines=('AF_V3_EXTENDED_PLAYER_FACES',))
    for row in records:
        row['file']=f"motion-{row['source_index']}.bin"
        write_new(output/row['file'],assets[row['source_index']])
    previous_table,previous_data,_=player_face_sources(source,motion['records'])
    if (module[FACE_TABLE:FACE_TABLE+len(previous_table)]!=previous_table or
            module[FACE_DATA:FACE_DATA+len(previous_data)]!=previous_data):
        raise ValueError('Changed existing player face timelines')
    face_table,face_data,faces=player_face_sources(source,[*motion['records'],*records])
    write_new(output/'face-table.bin',face_table);write_new(output/'face-data.bin',face_data)
    info=module_command_info(image);bank,_,decoder=donor();source_id=0x3063;message=12032
    data=encode(decode_gc(bank[source_id],decoder),info);tokens=list(tokenize(data,info))
    if (not tokens or tokens[-1].data!=b'\x7f\0' or expanded_bound(data,info)>1024 or
            sum(t.kind=='cmd' and t.data[1] in (0,1) for t in tokens)!=1 or
            any(t.kind=='cmd' and t.data[1] not in (0,3,5) for t in tokens)):
        raise ValueError('Mosquito message has an unreviewed command or overflow')
    credit=dict(id=f'message:{message:04X}',native_sha256=None,locales=dict(en=dict(
        credit='official',locator=['tools/v3_creature_insect_player.py:prepare_mosquito',f'N64/message/{message:04X}'],
        source=dict(source='user-supplied GAFE01 revision 0 disc',reference_id='message:3063',
            reference_sha256=sha256(bank[source_id])),human_review='not_recorded',
        adaptations=['Native encoding; retain official wording, line breaks, pauses, and colours'],
        encoded_sha256=sha256(data))))
    catalogue=json.loads((ROOT/'translations/provenance.json').read_bytes());validate(catalogue)
    found=next((r for r in catalogue['entries'] if r['id']==credit['id']),None)
    if found is not None and found!=credit:raise ValueError('Conflicting mosquito text provenance')
    payload,directory=extend_bank(files[MESSAGE].extract(image),files[TABLE].extract(image),[data],message)
    text_files=[];choices=prior['import_storage']['choice_vrom']
    for v,raw in ((MESSAGE,payload),(TABLE,directory),(choices,files[choices].extract(image)),
                  (CHOICE_TABLE,files[CHOICE_TABLE].extract(image))):
        filename=f'text-{v:08X}.bin';write_new(output/filename,raw)
        text_files.append(dict(vrom=v,file=filename,bytes=len(raw),sha256=sha256(raw),
                               original_sha256=sha256(files[v].extract(image))))
    return dict(source_functions=donor_functions,native_functions=dependencies,
        actions=[107,108],native_relax_rod=51,rod_interruption_offset=0xD10,
        records=records,motion_source=motion_source,faces=faces,face_reader=face_reader,
        animation_bytes=sum(map(len,assets.values())),animation_bank_bytes=motion['allocation']['bank_bytes'],
        text=dict(id=message,first_id=message,count=1,choice_vrom=choices,source_id=source_id,bytes=len(data),sha256=sha256(data),
            expanded_bound=expanded_bound(data,info),resources=text_files,provenance_entry=credit,
            provenance_missing=[] if found else [credit]),
        source_animation_steps=2,native_physics_steps=1,native_museum_insect_room=False,
        player_allocation_changed=False,saved_format_changed=False,installed=False)


def compose_mosquito(equipment,module,symbols,prepared,directory,placed_motions,core):
    """Bind both actions and full resources during the complete runtime install.

    The enclosing importer supplies checked storage placements and loads the
    resident insect runtime. This does not place a ROM, select insects, or claim
    their remaining services are implemented.
    """
    from v3_equipment_runtime import RAM,PLAYER_TABLE,FACE_CODE,FACE_TABLE,FACE_DATA
    if sha256(module)!=equipment['sha256'] or prepared['text']['provenance_missing']:
        raise ValueError('Changed mosquito module or missing official text credit')
    if {r['source_index'] for r in placed_motions}!={132,133} or len(placed_motions)!=2:
        raise ValueError('Both complete mosquito motions require checked placements')
    result=bytearray(module);updated=copy.deepcopy(equipment);motion=updated['player_motion']
    for row in prepared['records']:
        placed=next(r for r in placed_motions if r['source_index']==row['source_index'])
        if any(placed.get(k)!=v for k,v in row.items()):raise ValueError('Changed complete mosquito motion placement')
        raw=(directory/row['file']).read_bytes();at=PLAYER_TABLE+16+row['source_index']*16
        if (len(raw)!=row['bytes'] or sha256(raw)!=row['sha256'] or any(result[at:at+16]) or
                row['bytes']>motion['allocation']['bank_bytes'] or placed['vrom']&15):
            raise ValueError('Invalid complete mosquito animation resource')
        struct.pack_into('>4I',result,at,placed['vrom'],row['bytes'],row['pointer'],row['type'])
        motion['records'].append(copy.deepcopy(placed))
    motion['records'].sort(key=lambda r:r['source_index'])
    faces=copy.deepcopy(prepared['faces']);table=bytearray((directory/'face-table.bin').read_bytes())
    data=(directory/'face-data.bin').read_bytes();previous=motion['faces']
    reader=(directory/'face-reader/code.bin').read_bytes();compiled=prepared['face_reader']
    old_size=previous['code']['bytes']
    if (sha256(reader)!=compiled['sha256'] or len(reader)!=compiled['bytes'] or
            FACE_CODE+len(reader)>FACE_TABLE or
            sha256(result[FACE_CODE:FACE_CODE+old_size])!=previous['code']['sha256'] or
            len(reader)>old_size and any(result[FACE_CODE+old_size:FACE_CODE+len(reader)])):
        raise ValueError('Changed or overlapping shared face reader')
    result[FACE_CODE:FACE_CODE+max(old_size,len(reader))]=reader+bytes(max(0,old_size-len(reader)))
    core=bytearray(core);face_hooks=[]
    for hook,name in zip(previous['hooks'],('af_v3_player_eye_sequence','af_v3_player_mouth_sequence'),strict=True):
        at=hook['entry']-CODE_RAM;before=bytes.fromhex(hook['after']);target=compiled['symbols'][name]
        if core[at:at+len(before)]!=before:raise ValueError('Changed native face-reader hook')
        after=struct.pack('>II',jump(target),0);core[at:at+8]=after
        face_hooks.append(dict(hook,before=before.hex(),after=after.hex(),target=target))
    if (len(table)!=faces['table_bytes'] or sha256(table)!=faces['table_sha256'] or
            len(data)!=faces['data_bytes'] or sha256(data)!=faces['data_sha256'] or
            FACE_TABLE+len(table)>FACE_DATA or
            sha256(result[FACE_TABLE:FACE_TABLE+previous['table_bytes']])!=previous['table_sha256'] or
            sha256(result[FACE_DATA:FACE_DATA+previous['data_bytes']])!=previous['data_sha256']):
        raise ValueError('Changed complete mosquito face timelines')
    # The occupied password bootstrap starts at 11D00. The old fixed face-data
    # reservation cannot grow into that code. All timelines are linked into the
    # complete insect runtime; the existing face reader already follows pointers.
    pool=symbols['af_insect_player_faces'];origin=RAM+FACE_DATA
    if pool&3 or not 0x80000000<=pool<pool+len(data)<=0x80800000:
        raise ValueError('Mosquito face timelines are not resident data')
    for at in range(16,len(table),4):
        pointer=u32(table,at)
        if not pointer:continue
        if not origin<=pointer<origin+len(data):raise ValueError('Unbounded face timeline pointer')
        struct.pack_into('>I',table,at,pool+pointer-origin)
    for row in faces['rows']:
        row['pointers']=[pool+p-origin if p else 0 for p in row['pointers']]
    for row in faces['arrays']:row['ram']+=pool-origin
    struct.pack_into('>I',table,4,2);table.extend(struct.pack('>II',pool,pool+len(data)))
    if len(table)!=FACE_DATA-FACE_TABLE:raise ValueError('External face bounds exceed the reserved table')
    result[FACE_TABLE:FACE_TABLE+len(table)]=table
    faces.update(table_sha256=sha256(table),table_bytes=len(table),data_offset=None,data_ram=pool,
        data_storage='insect-runtime',data_file='face-data.bin',code=compiled,hooks=face_hooks)
    motion['faces'].update(faces)
    actions=updated['player_actions'];patches=[]
    callbacks={0x808BE620:(0x808BE140,0x808BE140),0x808DD874:(0,0),
        0x808DD9B4:(0,'af_insect_mosquito_settle'),
        0x808DDA18:('af_insect_mosquito_setup','af_insect_mosquito_notice_setup'),
        0x808DDB5C:('af_insect_mosquito_main','af_insect_mosquito_notice_main')}
    for row in actions['tables']:
        if row['width']!=4:continue
        offset,size=row['offset'],row['bytes']
        if sha256(result[offset:offset+size])!=row['sha256']:raise ValueError('Changed player dispatch table')
        for index,callback in zip((107,108),callbacks[row['native_entry']],strict=True):
            value=symbols[callback] if isinstance(callback,str) else callback
            if isinstance(callback,str) and (value&3 or not 0x80000000<=value<0x80800000):
                raise ValueError('Mosquito action is not resident executable RAM')
            at=offset+4*index
            if u32(result,at):raise ValueError('Mosquito callback would replace an existing action')
            struct.pack_into('>I',result,at,value)
            patches.append(dict(offset=at,index=index,before=0,after=value))
        row['sha256']=sha256(result[offset:offset+size])
    actions['enabled_imported_actions']=sorted(set(actions['enabled_imported_actions'])|{107,108})
    actions['disabled_indices']=[i for i in actions['disabled_indices'] if i not in (107,108)]
    updated.update(sha256=sha256(result),crc32=zlib.crc32(result))
    return bytes(result),updated,dict(callback_patches=patches,motions=placed_motions,
        text=prepared['text'],face_hooks=face_hooks,native_execution_tested=False,
        runtime_installation_required=True),bytes(core)
