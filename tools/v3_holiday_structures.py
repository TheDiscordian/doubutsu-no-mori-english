"""Convert the complete event-decoration batch through the shared model pipeline.

Discover owners from actual layout and structure-setup records, not a per-item
allowlist. Retain both seasonal palettes, complete shadows, and source lifecycle
dependencies. Prepared graphics do not enable an unfinished actor.
"""
import argparse
import json
import math
from pathlib import Path
import re
import struct

from aflib import sha256
from apply_translation import write_new
from map_artwork import compile_commands_batch
from v3_asset_loader import ROOT
from v3_furniture_pipeline import Source, ReviewRequired, prepare_models, assemble_models
from v3_holiday_maps import discover as discover_maps
from v3_keyframes import skeleton, animation
from v3_keyframes import model_descriptor, compile_skeleton, compile_animations
from v3_furniture_art import command_source
from title_assets import model_texture_shape

PREPARED = ROOT/'build/v3-diary-category-work-01/decorations-01'


def receipt(source, at):
    name, start, size = source.containing(at, exact=True)
    raw = source.data[start:start + size]
    return dict(symbol=name, donor_offset=start, bytes=size, sha256=sha256(raw))


def source_bundle(path):
    """Only follow an actor's own source includes; never swallow engine headers."""
    files = {}
    def visit(file):
        file = file.resolve()
        if not file.is_relative_to(ROOT / 'local/ac-decomp/src/actor'):
            raise ValueError('Actor include leaves its source directory')
        key = str(file.relative_to(ROOT / 'local/ac-decomp'))
        if key in files:
            return ''
        raw = file.read_bytes(); files[key] = sha256(raw)
        text = re.sub(r'/\*.*?\*/|//[^\n]*', '', raw.decode(), flags=re.S)
        for target in re.findall(r'^\s*#include\s+"([^"]+\.c_inc)"', text, re.M):
            # The donor also spells includes relative to its repository root.
            options = {p.resolve() for p in (file.parent / target,
                ROOT / 'local/ac-decomp/include' / target) if p.is_file()}
            if len(options) != 1:
                raise ValueError('Ambiguous actor source include: ' + target)
            text += '\n' + visit(options.pop())
        return text
    return visit(path), files


def discover(source):
    maps = discover_maps(source)
    names = sorted({a['source_name'] for row in maps['maps'] if row['available']
        for layout in row['layouts'] for a in layout if a['source_name'] >> 12 == 5})
    setup_functions = [at for at, rows in source.functions.items()
        if any(name == 'aSTR_setupActor_proc' for name, _ in rows)]
    if len(setup_functions) != 1:
        raise ValueError('Ambiguous complete structure setup owner')
    _, setup = source.function(setup_functions[0])
    if setup['sha256'] != 'e4e7619784ac66807f5acc1d32d827cc53886a90d7799552979a415958f86c9f':
        raise ValueError('Changed complete structure setup owner')
    tables = {r[3] for r in setup['relocations'].values() if r[:3] == (6, 1, 5)}
    if len(tables) != 1:
        raise ValueError('Ambiguous structure setup directory')
    table = receipt(source, tables.pop()); setup_start = table['donor_offset']
    if table['bytes'] != 83 * 8 or source.pointers(setup_start, table['bytes']):
        raise ValueError('Changed complete structure setup records')
    profiles = {}
    for name in source.names:
        if not name.endswith('_Profile') or len(source.names[name]) != 1:
            continue
        at, size = source.symbol(name)
        if size == 36:
            identity = struct.unpack_from('>H', source.data, at)[0]
            profiles.setdefault(identity, []).append((name, at, size))
    # Source-file indexing is shared for the complete category, not one search
    # or one conversion script per decoration.
    profile_files = {}
    for path in (ROOT / 'local/ac-decomp/src/actor').glob('*.c'):
        text = path.read_text()
        for name in re.findall(r'\bACTOR_PROFILE\s+(\w+)\s*=', text):
            profile_files.setdefault(name, []).append(path)
    owners, bindings = {}, []
    for name in names:
        index = name - 0x5800
        if not 0 <= index < table['bytes'] // 8:
            raise ValueError('Layout decoration exceeds the actual setup directory')
        profile, kind, palette, pad = struct.unpack_from('>4h', source.data, setup_start + index * 8)
        if pad or len(profiles.get(profile, [])) != 1:
            raise ValueError('Unresolved decoration profile')
        symbol, at, size = profiles[profile][0]
        bindings.append(dict(source_name=name, profile=profile, structure_type=kind,
            palette_index=palette, owner=symbol))
        if symbol in owners:
            continue
        paths = profile_files.get(symbol, [])
        if len(paths) != 1:
            raise ValueError('Unresolved decoration source: ' + symbol)
        text, references = source_bundle(paths[0])
        callbacks = {}
        for off in range(16, 36, 4):
            fix = source.relocations.get(at + off)
            if fix:
                if fix[:3] != (1, True, 1):
                    raise ValueError('External decoration callback')
                _, callbacks[str(off)] = source.function(fix[3])
            elif any(source.data[at + off:at + off + 4]):
                raise ValueError('Unresolved decoration callback address')
        if not {'16', '24', '28'} <= set(callbacks):
            raise ValueError('Incomplete decoration lifecycle')
        # Every locally declared list is retained, including models reached
        # through draw tables and projected shadows. Validate against the REL.
        models = sorted(set(re.findall(r'\bextern\s+Gfx\s+(\w+)\s*\[', text)))
        rigs = [skeleton(source, source.symbol(n)[0]) for n in
            re.findall(r'\bextern\s+cKF_Skeleton_R_c\s+(\w+)\s*;', text)]
        motions = []
        for n in re.findall(r'\bextern\s+cKF_Animation_R_c\s+(\w+)\s*;', text):
            if len(rigs) != 1:
                raise ValueError('Ambiguous decoration animation skeleton')
            motions.append(animation(source, source.symbol(n)[0], joints=rigs[0]['joints']))
        models = sorted(set(models) | {r['model']['symbol'] for rig in rigs
            for r in rig['rows'] if 'model' in r})
        if not models:
            raise ValueError('Owner has no complete drawing resources: ' + symbol)
        for model in models:
            raw = source.raw(model)
            if len(raw) % 8 or raw[-8:] != bytes.fromhex('df00000000000000'):
                raise ValueError('Incomplete declared model: ' + model)
        shadows = []
        for shadow in re.findall(r'\bbIT_ShadowData_c\s+(\w+)\s*=', text):
            desc = receipt(source, source.symbol(shadow)[0]); q = desc['donor_offset']
            refs = source.pointers(q, desc['bytes'])
            count, _, height, _, _ = struct.unpack('>IIfII', source.raw(shadow))
            if (desc['bytes'] != 20 or set(refs) != {q + 4, q + 12, q + 16}
                    or not 0 < count <= 32 or not math.isfinite(height) or not 0 <= height <= 100):
                raise ValueError('Unsupported projected shadow: ' + shadow)
            flags, vertices, model = [receipt(source, refs[q + off]) for off in (4, 12, 16)]
            capacity = vertices['bytes'] // 16
            if (vertices['bytes'] % 16 or flags['bytes'] != capacity
                    or any(v > 1 for v in source.raw(flags['symbol'])) or model['symbol'] not in models):
                raise ValueError('Incomplete shadow resources: ' + shadow)
            # The donor's right fireworks stall requests ten projections from
            # two seven-entry arrays. Retain the whole arrays and model, but
            # never reproduce the out-of-bounds reads. Model conversion below
            # independently checks every referenced vertex against capacity.
            shadows.append(dict(descriptor=desc, source_count=count,
                projection_count=min(count, capacity), height=height, flags=flags,
                vertices=vertices, model=model['symbol'],
                source_count_exceeds_arrays=count > capacity))
        owners[symbol] = dict(profile=receipt(source, at), callbacks=callbacks,
            references=references, models=models, shadows=shadows, skeletons=rigs,
            animations=motions, behaviour_installed=False, texture_frames=[])
        textures = [source.symbol(n)[0] for n in re.findall(r'\bextern\s+u8\s+(\w+)\s*\[',text)]
        if textures:
            draw = callbacks['28']; found = []
            for at in sorted({r[3] for r in draw['relocations'].values() if r[:3]==(6,1,5)}):
                _, start, size = source.containing(at,exact=True)
                refs = source.pointers(start,size)
                if (set(refs)==set(range(start,start+size,4)) and
                        list(refs.values())==textures):
                    found.append(receipt(source,start))
            if len(found)!=1:
                raise ValueError('Unresolved complete actor texture-frame table')
            owners[symbol]['texture_frame_table']=found[0]
            owners[symbol]['texture_frames']=[dict(receipt(source,at),
                source_sha256=sha256(source.data[at:at+source.containing(at,exact=True)[2]])) for at in textures]
    return dict(format='AFV3-HOLIDAY-STRUCTURES-1', source_rel_sha256=sha256(source.rel),
        source_symbols_sha256=sha256(source.symbols.encode()), setup=setup, table=table,
        layouts=maps, bindings=bindings, owners=owners, installed=False, selectable=False)


def plans(source, inventory):
    """Build and deduplicate every model/season/shadow contract before compiling."""
    result = {}; palettes = {}; pending = {}
    for season in ('nowinter', 'winter'):
        key = 'structure_pal_adrs_' + season
        at, size = source.symbol(key)
        palettes[season] = (receipt(source, at), source.pointers(at, size))
    for owner_name, owner in inventory['owners'].items():
        palette_indices = sorted({r['palette_index'] for r in inventory['bindings'] if r['owner'] == owner_name})
        rig_models={r['model']['symbol'] for rig in owner['skeletons'] for r in rig['rows'] if 'model' in r}
        groups=[(m,dict(models={'opaque':(m,*source.symbol(m))})) for m in owner['models'] if m not in rig_models]
        groups += [(rig['header']['symbol'], model_descriptor(rig,kind='animated-room-model')) for rig in owner['skeletons']]
        for model, description in groups:
            shadows = [r for r in owner['shadows'] if r['model'] == model]
            variants = [(None, None)] if shadows else [(s, i) for s in palettes for i in palette_indices]
            for season, index in variants:
                desc = dict(description)
                desc['callback_adapter']=dict(category='actor-model-assets',model_scrolls={})
                if shadows:
                    if len({r['vertices']['donor_offset'] for r in shadows}) != 1:
                        raise ValueError('Conflicting projected vertex contracts')
                    v = shadows[0]['vertices']
                    desc['vertex_bindings'] = {0x08000000:v['donor_offset']}
                else:
                    table, pointers = palettes[season]; loc = table['donor_offset'] + index * 4
                    if not 0 <= index < table['bytes'] // 4 or loc not in pointers:
                        raise ValueError('Missing complete seasonal palette')
                # The model parser rejects unused supplied palette bindings.
                # Only caller-loaded palettes actually referenced by this
                # complete graph belong in its descriptor.
                dynamic=set();frame_addresses=set()
                for label,root in desc['models'].items():
                    raw, refs, joined = source.model_graph(root)
                    base = 0 if joined else root[1]
                    position=0;shapes=[];scroll=[]
                    while position<len(raw):
                        a,b=struct.unpack_from('>II',raw,position);op=a>>24
                        if base+position+4 not in refs:
                            if op==0xF0:dynamic.add(b)
                            elif op==0xFD:frame_addresses.add(b)
                            elif op==0xDE:scroll.append(b)
                        if op==0xFD:shapes.append(list(model_texture_shape(raw[position:position+8])[:2]))
                        size=(1+(max(0,((a>>17&127)+1)-3)+3)//4)*8 if op==0x0A else 8
                        position+=size
                    if scroll:
                        if len(scroll)!=1:raise ValueError('Ambiguous actor scroll caller')
                        desc['callback_adapter']['model_scrolls'][label]=dict(segment=scroll[0],dimensions=shapes)
                if dynamic:
                    if shadows or not dynamic <= {0x08000000,0x09000000,0x0A000000}:
                        raise ValueError('Unbound decoration palette segment')
                    desc['palette_bindings'] = {address:pointers[loc] for address in dynamic}
                if frame_addresses:
                    if not owner['texture_frames'] or not frame_addresses<={0x08000000,0x09000000}:
                        raise ValueError('Unresolved complete actor texture frames')
                    desc['callback_adapter'].update(independent_material_frames=True,
                        material_frames=[dict(kind='texture',segment_address=address,
                            frames=owner['texture_frames']) for address in sorted(frame_addresses)])
                try:
                    empty=all(source.data[at:at+n]==bytes.fromhex('df00000000000000') for _,at,n in desc['models'].values())
                    if empty:
                        # Preserve actual empty draw streams as returns, not
                        # fabricated geometry or an omitted source dependency.
                        models={label:dict(symbol=n,donor_offset=at,source_sha256=sha256(source.data[at:at+size]),
                            inherited_material=True,rows=[dict(opcode=0xDF,words=(0xDF000000,0))])
                            for label,(n,at,size) in desc['models'].items()}
                        commands,sections=command_source(models,{})
                        prepared=(desc,b'',[],{},models,commands,sections)
                    else:prepared = prepare_models(source, desc)
                except (ReviewRequired, ValueError) as error:
                    pending.setdefault(str(error),set()).add(owner_name + '/' + model)
                    continue
                fingerprint = sha256(prepared[1] + prepared[5].encode())
                row = result.setdefault(fingerprint, dict(key=f'model-{len(result):03d}',
                    prepared=prepared, consumers=[],animations=owner['animations'] if 'skeleton' in desc else []))
                row['consumers'].append(dict(owner=owner_name, model=model, season=season,
                    palette_index=index, shadow=bool(shadows),
                    source_models=[receipt(source,r[1]) for r in desc['models'].values()]))
    if pending:
        raise ValueError('Complete decoration batch needs shared format support: ' +
            json.dumps({reason:sorted(names) for reason,names in pending.items()},indent=2))
    return list(result.values()), {k:v[0] for k,v in palettes.items()}


def convert(source, output):
    output = output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Use a fresh ignored conversion directory')
    inventory = discover(source)
    batch, palettes = plans(source, inventory)
    output.mkdir(parents=True)
    jobs = []
    for row in batch:
        path = output / row['key']; path.mkdir()
        command = path / 'commands.c'; write_new(command, row['prepared'][5].encode())
        jobs.append((row['key'], command, row['prepared'][6]))
    compiled = compile_commands_batch(output / 'compiled', jobs)
    objects = []
    for row in batch:
        prepared = row['prepared']
        asset, offsets, models, sequence = assemble_models(prepared, compiled[row['key']])
        if sequence is not None:
            raise ValueError('Unexpected decoration draw-sequence adaptation')
        rig_record={}
        if 'skeleton' in prepared[0]:
            rig=prepared[0]['skeleton']; roots={r[1]:offsets[label] for label,r in prepared[0]['models'].items()}
            extra,rig_record['skeleton']=compile_skeleton(source,rig,roots,start=len(asset));asset+=extra
            if row['animations']:
                extra,rig_record['animations']=compile_animations(source,row['animations'],start=len(asset));asset+=extra
        filename = row['key'] + '.n64obj.bin'; write_new(output / filename, asset)
        objects.append(dict(key=row['key'], consumers=row['consumers'], resources=prepared[2],
            models=models, model_offsets=offsets, object_file=filename,
            rig=rig_record,draw_context=prepared[0],
            object_bytes=len(asset), object_sha256=sha256(asset)))
    report = dict(inventory, objects=objects, palette_tables=palettes,
        source_files={p:sha256((ROOT/p).read_bytes()) for p in (
            'tools/v3_holiday_structures.py','tools/v3_furniture_pipeline.py','tools/v3_furniture_art.py')},
        pending=['native actor lifecycle, collision, interactions, and shared event consumers',
                 'additive identities, loading, draw-context binding, and native execution'])
    write_new(output / 'art.json', (json.dumps(report, indent=2) + '\n').encode())
    return report


def prepared_packet(source, directory):
    """Reuse checked artwork; this stage never starts another compiler."""
    report=json.loads((directory/'art.json').read_bytes())
    inventory=discover(source)
    # JSON normalisation accounts for integer relocation keys, not differences
    # in the actual source graph, owner callbacks, or resource contents.
    if any(report[k]!=json.loads(json.dumps(v)) for k,v in inventory.items()):
        raise ValueError('Prepared decorations have changed source owners or identities')
    batch,_=plans(source,inventory)
    if len(batch)!=len(report['objects']):raise ValueError('Incomplete prepared decoration batch')
    data=bytearray();objects=[]
    for plan,row in zip(batch,report['objects'],strict=True):
        profile,body,resources,_,models,commands,sections=plan['prepared']
        filename=row['object_file']
        if Path(filename).name!=filename or row['key']!=plan['key']:
            raise ValueError('Invalid prepared decoration path/identity')
        asset=(directory/filename).read_bytes()
        if (len(asset)!=row['object_bytes'] or sha256(asset)!=row['object_sha256'] or
                asset[:len(body)]!=body or row['resources']!=json.loads(json.dumps(resources)) or
                row['draw_context']!=json.loads(json.dumps(profile)) or
                row['consumers']!=json.loads(json.dumps(plan['consumers'])) or
                (directory/plan['key']/'commands.c').read_text()!=commands or
                len(row['models'])!=len(sections)):
            raise ValueError('Prepared decoration differs from complete source conversion')
        compiled={}
        for old,(label,n) in zip(row['models'],sections,strict=True):
            at=old['native_offset'];part=asset[at:at+n]
            if (old['layer']!=label or old['bytes']!=n or at<len(body) or at%8 or
                    len(part)!=n or sha256(part)!=old['output_sha256']):
                raise ValueError('Incomplete converted decoration model')
            compiled[label]=part
        packed,offsets,records,sequence=assemble_models(plan['prepared'],compiled)
        rig_record={}
        if 'skeleton' in profile:
            roots={r[1]:offsets[label] for label,r in profile['models'].items()}
            extra,rig_record['skeleton']=compile_skeleton(source,profile['skeleton'],roots,start=len(packed));packed+=extra
            if plan['animations']:
                extra,rig_record['animations']=compile_animations(source,plan['animations'],start=len(packed));packed+=extra
        if (packed!=asset or row['model_offsets']!=offsets or row['models']!=json.loads(json.dumps(records)) or
                row['rig']!=json.loads(json.dumps(rig_record)) or sequence is not None):
            raise ValueError('Prepared complete rig/model reconstruction differs')
        objects.append(dict(row,packet_offset=len(data)))
        data.extend(asset)
    # The projected vertices are inside their complete model objects. Keep
    # every projection flag array too, with the checked count on its owner.
    flags=[]
    for at in sorted({s['flags']['donor_offset'] for o in inventory['owners'].values() for s in o['shadows']}):
        r=receipt(source,at);raw=source.data[at:at+r['bytes']]
        data.extend(bytes(-len(data)%16));flags.append(dict(r,packet_offset=len(data)))
        data.extend(raw)
    data.extend(bytes(-len(data)%16))
    return bytes(data),dict(report,objects=objects,projection_flags=flags,
        prepared_directory=str(directory.relative_to(ROOT)),
        prepared_report_sha256=sha256((directory/'art.json').read_bytes()))


def install(base, prior, output):
    """Bulk-stage resources without enabling actors with missing services."""
    import copy
    import v3_physical_resources as physical
    if prior['equipment_resources']['npc_extra']['events'].get('decorations'):
        from v3_decoration_draw import install as install_draw
        return install_draw(base,prior,output)
    equipment=copy.deepcopy(prior['equipment_resources'])
    events=equipment['npc_extra']['events']
    if not events.get('transition') or events.get('decorations'):
        raise ValueError('Decoration resources require connected scene services, once')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    data,report=prepared_packet(source,PREPARED)
    records=copy.deepcopy(prior['physical_resources'])
    resource=physical.allocate(base,records,data,'holiday-decorations-GAFE01-r0');records.append(resource)
    report.update(packet=resource,resources_installed=True,installed=False,
        actors_installed=False,additional_resident_bytes=0,saved_format_changed=False,
        saved_profile_changed=False,native_execution_verified=False)
    report['source_files'].update({p:sha256((ROOT/p).read_bytes()) for p in (
        'tools/v3_holiday_structures.py','tools/v3_holiday_active.py','tools/v3_furniture_install.py',
        'tools/v3_furniture_materials.py','tools/v3_furniture_scroll.py','tools/v3_keyframes.py')})
    events['decorations']=report;equipment['npc_extra']['sources'].update(report['source_files'])
    directory=output/'holiday-decorations';directory.mkdir(parents=True)
    write_new(directory/'installed.json',(json.dumps(report,indent=2)+'\n').encode())
    write_new(directory/'resources.bin',data)
    return equipment,{},dict(physical_resources=records),[(resource,data)]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    source = Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    report = convert(source, args.output)
    print(json.dumps(dict(decorations=len(report['bindings']), owners=len(report['owners']),
        objects=len(report['objects']), bytes=sum(r['object_bytes'] for r in report['objects']),
        installed=False)))
