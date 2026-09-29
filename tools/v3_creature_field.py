"""Shared fish/insect field-model discovery and complete frame conversion.

The source's frame tables supply every root. Repeated frames share geometry;
distinct poses remain distinct. These are carried/field representations of the
existing creature identities, never separate furniture or equipment choices.
"""
import json
import struct

from aflib import sha256, u32
from apply_translation import write_new
from map_artwork import compile_commands_batch
from v3_creature_items import source_records
from v3_furniture_pipeline import prepare_models, assemble_models

CATEGORY = 'creature-field-frames'
FORMAT = 'AFV3-CREATURE-FIELD-ASSETS-1'
FISH_TABLES = (0x35B88, 0x35FE8, 0x76500)
INSECT_TABLE = 0x75A34


def table(source, offset, size, name):
    if source.containing(offset, exact=True) != (name, offset, size):
        raise ValueError('Changed complete creature field table: '+name)
    raw = source.data[offset:offset+size]
    if len(raw) != size:
        raise ValueError('Truncated creature field table')
    return raw, dict(symbol=name, offset=offset, bytes=size, sha256=sha256(raw),
                     pointers=source.pointers(offset,size))


def named_table(source, name, size):
    offset, actual = source.symbol(name)
    if actual != size:
        raise ValueError('Changed creature field table size: '+name)
    return table(source,offset,size,name)


def frame_roots(source, pointer, category):
    name, offset, size = source.containing(pointer,exact=True)
    if size not in ((12,) if category=='fish' else (8,16,24)):
        raise ValueError('Unsupported complete creature frame-array length')
    raw, receipt = table(source,offset,size,name)
    refs = source.pointers(offset,size)
    if raw != bytes(size) or set(refs) != set(range(offset,offset+size,4)):
        raise ValueError('Incomplete creature frame relocations')
    frames = [source.containing(refs[p],exact=True) for p in range(offset,offset+size,4)]
    return frames, receipt


def discover(source, *, carried_rows=None):
    if carried_rows is None:
        parents, identity = source_records(source)
    else:
        # Quest creatures use the same complete frame/program tables, but are
        # not museum insects or cage furniture. Quantity states share a parent.
        from v3_registry import CARRIED_ITEMS
        parents=[]
        for row in carried_rows:
            item=int(row['donor_item_id'],16)
            if item>>8!=0x2D or row['state_index']:
                continue
            if item not in CARRIED_ITEMS or item<0x2D28:
                raise ValueError('Unknown additional carried-creature identity')
            parents.append(dict(source_index=item&255,category='insect',
                item_id=f'{CARRIED_ITEMS[item]:04X}',source_item_id=f'{item:04X}',
                display_item_id=None,name=row['name']))
        identity=dict(rel_sha256=sha256(source.rel),symbols_sha256=sha256(source.symbols.encode()))
    tables = {}; fish = []
    for address in FISH_TABLES:
        _, receipt = table(source,address,45*4,'aGYO_displayList')
        tables[f'fish_models_{address:X}'] = receipt
        fish.append(source.pointers(address,45*4))
    _, tables['insect_models'] = table(source,INSECT_TABLE,41*4,'aINS_displayList')
    insects = source.pointers(INSECT_TABLE,41*4)
    animation, tables['fish_animation'] = named_table(source,'aGYO_anime_ptn',45*4)
    release, tables['fish_release_animation'] = table(source,0x35CD0,45*4,'aGYR_anime_ptn$480')
    height, tables['fish_height'] = named_table(source,'aGYO_hosei_y$690',45*4)
    programs, tables['insect_program'] = named_table(source,'aINS_program_type',41*4)
    # Keep both actual frame sequences. Field and release choose independently
    # between fast/slow; the jellyfish and three large sea fish differ.
    sequences = {}
    for name, count in (('aGYO_frame_ptn1$672',8),('aGYO_frame_ptn2$673',16)):
        raw, receipt = named_table(source,name,count*4)
        values = list(struct.unpack('>'+str(count)+'I',raw))
        if values != ([1,1,0,0,2,2,0,0] if count==8 else [1,1,1,1,0,0,0,0,2,2,2,2,0,0,0,0]):
            raise ValueError('Changed complete source fish frame sequence')
        tables[name] = receipt; sequences[str(1 if count==8 else 2)] = values
    functions = []
    for name in ('aGYO_anime_frame','aGYO_actor_draw_fish','aGYR_anime_frame',
                 'aGYR_actor_draw','aINS_actor_draw_sub','aINS_actor_draw'):
        candidates = [at for at, entries in source.functions.items() if any(n==name for n,_ in entries)]
        if len(candidates)!=1:
            raise ValueError('Missing complete creature drawing consumer: '+name)
        functions.append(source.function(candidates[0])[1])
    rows = []
    for parent in parents:
        index, category = parent['source_index'], parent['category']
        if category=='fish':
            frame_sets = [frame_roots(source,refs[at+index*4],category)
                          for at,refs in zip(FISH_TABLES,fish,strict=True)]
            if any(frames!=frame_sets[0][0] for frames,_ in frame_sets[1:]):
                raise ValueError('Fish field/release model consumers disagree')
        else:
            frame_sets = [frame_roots(source,insects[INSECT_TABLE+index*4],category)]
        frames = frame_sets[0][0]
        unique = list(dict.fromkeys(frames))
        descriptor = dict(kind=CATEGORY,models={f'frame{i}':root for i,root in enumerate(unique)})
        row = dict(item_id=parent['item_id'], source_item_id=parent['source_item_id'],
            display_item_id=parent['display_item_id'], source_index=index,
            native_index=int(parent['item_id'],16)&255, category=category,name=parent['name'],
            descriptor=descriptor, frame_labels=[f'frame{unique.index(root)}' for root in frames],
            frame_tables=[receipt for _,receipt in frame_sets],
            runtime_installed=False,selectable=False)
        if category=='fish':
            row.update(animation=u32(animation,index*4),release_animation=u32(release,index*4),
                       height_correction=struct.unpack_from('>f',height,index*4)[0])
            if row['animation'] not in (1,2) or row['release_animation'] not in (1,2):
                raise ValueError('Ordinary fish lacks a supported complete animation')
        else:
            row['program_type'] = u32(programs,index*4)
            if row['program_type']>=14:
                raise ValueError('Insect behaviour escapes the donor program table')
        prepared = prepare_models(source,descriptor)
        row.update(object_bytes=(len(prepared[1])+sum(n for _,n in prepared[6])+15)&~15,
            unique_models=len(unique),frame_count=len(frames),asset_ready=True)
        rows.append(row)
    return dict(format='AFV3-CREATURE-FIELD-SOURCES-1',source=identity,tables=tables,
                functions=functions,frame_sequences=sequences,rows=rows,
                counts=dict(creatures=len(rows),frames=sum(r['frame_count'] for r in rows),
                            unique_models=sum(r['unique_models'] for r in rows),
                            object_bytes=sum(r['object_bytes'] for r in rows)))


def convert(source, output, *, carried_rows=None, reuse=None):
    inventory = discover(source,carried_rows=carried_rows)
    prepared = {r['item_id']:prepare_models(source,r['descriptor']) for r in inventory['rows']}
    output.mkdir(parents=True,exist_ok=False)
    jobs = []; compiled={}
    previous=json.loads((reuse/'art.json').read_bytes()) if reuse else None
    if previous and (previous['format']!=FORMAT or
            previous['inventory']!=json.loads(json.dumps(inventory))):
        raise ValueError('Reusable field objects do not match the complete source category')
    for item, part in prepared.items():
        directory = output/item; directory.mkdir()
        command_file = directory/'commands.c'; write_new(command_file,part[5].encode())
        if previous:
            row=next(r for r in previous['objects'] if r['item_id']==item)
            old=(reuse/row['object_file']).read_bytes()
            if (sha256(old)!=row['object_sha256'] or len(old)!=row['object_bytes'] or
                    old[:len(part[1])]!=part[1] or row['resources']!=part[2] or
                    (reuse/item/'commands.c').read_text()!=part[5]):
                raise ValueError('Changed reusable complete field model')
            code={m['layer']:old[m['native_offset']:m['native_offset']+m['bytes']] for m in row['models']}
            if any(sha256(code[m['layer']])!=m['output_sha256'] for m in row['models']):
                raise ValueError('Changed reusable field display list')
            assembled,offsets,models,_=assemble_models(part,code)
            if assembled!=old or offsets!=row['model_offsets'] or models!=row['models']:
                raise ValueError('Reusable field assembly does not match complete resources')
            compiled[item]=code
        else:
            jobs.append((item,command_file,part[6]))
    # One container invocation for the complete category, not one per species.
    if jobs:compiled.update(compile_commands_batch(output/'compiled',jobs))
    objects = []
    for row in inventory['rows']:
        item = row['item_id']; part = prepared[item]
        asset, offsets, models, sequence = assemble_models(part,compiled[item])
        if sequence is not None or len(asset)!=row['object_bytes']:
            raise ValueError('Creature animation frames cannot be flattened into a draw sequence')
        name = item+'.n64obj.bin'; write_new(output/name,asset)
        objects.append(dict(row,resources=part[2],models=models,model_offsets=offsets,
            frame_offsets=[offsets[label] for label in row['frame_labels']],
            object_file=name,object_sha256=sha256(asset)))
    report = dict(format=FORMAT,version=1,source=inventory['source'],
                  inventory=inventory,objects=objects,counts=inventory['counts'],
                  runtime_installed=False,selectable=False)
    write_new(output/'art.json',(json.dumps(report,indent=2)+'\n').encode())
    return report
