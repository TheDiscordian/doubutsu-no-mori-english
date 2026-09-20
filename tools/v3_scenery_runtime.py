"""Owner-local seasonal banks and shared native scenery integration.

All bank pointers are explicit relocations; no donor address or segment-six
binding survives packing. Scene lifetimes, not a global heap pointer, own art.
"""
import copy
import json
import struct
import zlib

from aflib import sha256, u32
from v3_furniture_pipeline import Source, prepare_material_pair
from v3_scenery import discover, palettes, SEASONS

MAGIC = 0x41465343
HEADER_BYTES = 128
BOOT_RAM, BOOT_END = 0x804ADC90, 0x804ADFF0
RUNTIME_RAM, RUNTIME_END = 0x804B5000, 0x804B6000
SOURCES = ('tools/v3_scenery_runtime.py', 'tools/v3_scenery.py',
           'overlays/v3/scenery.h', 'overlays/v3/scenery.c',
           'overlays/v3/scenery.ld', 'overlays/v3/scenery_bootstrap.c',
           'overlays/v3/scenery_bootstrap.ld', 'overlays/v3/scenery_palette.c',
           'overlays/v3/scenery_trees.c', 'overlays/v3/scenery_trees.h',
           'overlays/v3/scenery_daily.c', 'overlays/v3/scenery_contents.c', 'overlays/v3/scenery_world.c',
           'overlays/v3/scenery_interactions.c', 'overlays/v3/scenery_player.c',
           'tools/v3_scenery_player.py',
           'tools/v3_asset_loader.py', 'translations/provenance.json')


def prepared(source, path):
    """Validate every prepared relationship/resource, without recompiling art."""
    path = path.resolve()
    raw = (path/'art.json').read_bytes(); art = json.loads(raw)
    expected = json.loads(json.dumps(discover(source)))
    if (art.get('format') != 'AFV3-SCENERY-PREPARED-ASSETS-1' or art.get('version') != 1
            or any(art.get(k) != v for k, v in expected.items()
                   if k not in ('format', 'objects', 'palettes'))):
        raise ValueError('Changed complete prepared scenery/source graph')
    palette, bank = palettes(source, expected['functions'])
    if art['palettes'] != dict(palette, object_file='seasonal-palettes.rgba16.bin'):
        raise ValueError('Changed scenery palette relationships')
    if (path/art['palettes']['object_file']).read_bytes() != bank:
        raise ValueError('Changed complete scenery palette bank')
    reference = {r['key']: r for r in expected['objects']}
    assets = {}
    for row in art['objects']:
        key = row['key']; ref = reference.get(key)
        if key in assets or ref is None or any(row.get(k) != v for k,v in ref.items()):
            raise ValueError('Changed or duplicate prepared scenery object')
        profile, body, resources, _, models, commands, sections = prepare_material_pair(
            source, ref['models'], render_context=ref['render_context'])
        file = (path/row['object_file']).resolve()
        if file.parent != path: raise ValueError('Scenery artwork escapes its directory')
        data = file.read_bytes(); cursor = (len(body)+7)&~7
        if (len(data) != row['object_bytes'] or sha256(data) != row['object_sha256']
                or data[:len(body)] != body or any(data[len(body):cursor])
                or row['profile'] != json.loads(json.dumps(profile)) or row['resources'] != resources
                or (path/key/'commands.c').read_text() != commands
                or len(row['compiled_models']) != len(sections)):
            raise ValueError('Changed complete prepared scenery artwork')
        for model,(label,n) in zip(row['compiled_models'], sections, strict=True):
            if (model['layer'] != label or model['native_offset'] != cursor or model['bytes'] != n
                    or row['model_offsets'].get(label) != cursor
                    or model['source_sha256'] != models[label]['source_sha256']
                    or model['output_sha256'] != sha256(data[cursor:cursor+n])):
                raise ValueError('Changed prepared scenery display list')
            cursor += n
        if set(row['model_offsets']) != {'material','geometry'} or any(data[cursor:]):
            raise ValueError('Unexpected scenery display data')
        assets[key] = data
    if assets.keys() != reference.keys(): raise ValueError('Incomplete prepared scenery objects')
    return art, assets, bank, dict(art_report_sha256=sha256(raw),
        source_rel_sha256=sha256(source.rel), source_symbols_sha256=sha256(source.symbols.encode()))


class Bank:
    def __init__(self):
        self.data = bytearray(HEADER_BYTES)
        self.cpu, self.gpu, self.callbacks = [], [], []

    def put(self, data, alignment=4):
        self.data.extend(bytes(-len(self.data)%alignment))
        at = len(self.data); self.data.extend(data)
        return at

    def pointer(self, at, target, kind='cpu'):
        if at%4 or target < HEADER_BYTES or target >= len(self.data):
            raise ValueError('Scenery pointer outside complete bank')
        if at in self.cpu or at in self.gpu or any(at==p for p,_ in self.callbacks):
            raise ValueError('Duplicate scenery relocation')
        struct.pack_into('>I', self.data, at, target)
        getattr(self, kind).append(at)


def pack_bank(art, assets, palette_data, season, palette_wrapper):
    """Pack one complete season; native table indices are assigned at loading."""
    if season not in SEASONS: raise ValueError('Unknown scenery season')
    descriptors = [r for r in art['descriptors'] if r['season']==season]
    bindings = [r for r in art['bindings'] if r['season']==season]
    used = {d['object'] for r in descriptors for d in
            r['body']+([r['shadow']['draw']] if r['shadow'] else [])}
    objects = {r['key']:r for r in art['objects'] if r['key'] in used}
    if len(descriptors)!=10 or len(bindings)!=14 or len(objects)!=19:
        raise ValueError('Incomplete seasonal scenery category')
    bank = Bank(); pal = bank.put(palette_data,16); active = bank.put(bytes(32),16)
    terms = bank.put(bytes(art['palettes']['term_indices']))
    trampoline = bank.put(bytes(16),16)
    objects_at, model_targets, object_receipts = {}, {}, []
    for key,row in objects.items():
        data = assets[key]; at = bank.put(data,16); objects_at[key] = at
        resources = {r['native_offset']:r for r in row['resources']}; used_resources=set()
        for model in row['compiled_models']:
            start=model['native_offset']; end=start+model['bytes']
            for p in range(start,end,8):
                op=data[p]
                if op not in (1,0xFD): continue
                pointer=u32(data,p+4); offset=pointer&0xFFFFFF; resource=resources.get(offset)
                kind='vertices' if op==1 else 'palette' if u32(data,p)>>21&7==0 else 'texture'
                if op==1:
                    count=(u32(data,p)>>12)&255
                    matches=[r for start,r in resources.items() if r['kind']=='vertices'
                             and start<=offset<offset+count*16<=start+r['bytes']
                             and (offset-start)%16==0]
                    resource=matches[0] if len(matches)==1 else None
                if pointer>>24!=6 or resource is None or resource['kind']!=kind:
                    raise ValueError('Unbound scenery model resource')
                bank.pointer(at+p+4,at+offset,'gpu'); used_resources.add(resource['native_offset'])
        external=row['render_context'].get('external_vertices')
        if external:
            matches=[r for r in resources.values() if r['donor_offset']==external[1]
                     and r['kind']=='vertices' and r['bytes']==external[2]]
            if len(matches)!=1: raise ValueError('Missing scenery caller-owned vertices')
            used_resources.add(matches[0]['native_offset'])
        if used_resources!=set(resources): raise ValueError('Unconsumed scenery object resource')
        for label,offset in row['model_offsets'].items():
            target=at+offset
            if label=='material' and not external:
                # One caller-independent palette load before the complete material.
                wrapper=bank.put(palette_wrapper,8)
                for loc,value in ((4,active),(52,target)):
                    bank.pointer(wrapper+loc,value,'gpu')
                target=wrapper
            donor=row['profile']['models'][label][1]
            if donor in model_targets and model_targets[donor]!=target:
                # Repeated geometry can be shared by several material pairs.
                old=model_targets[donor]
                n=next(m['bytes'] for m in row['compiled_models'] if m['layer']==label)
                if label!='geometry' or bytes(bank.data[old:old+n])!=bytes(bank.data[target:target+n]):
                    # Pointer offsets differ for otherwise identical vertex arrays;
                    # retain the first complete model, already source-validated.
                    if label!='geometry': raise ValueError('Conflicting scenery model binding')
            else: model_targets[donor]=target
        object_receipts.append(dict(key=key,offset=at,bytes=len(data),source_sha256=sha256(data)))
    display_tables={}; draws={}; descriptor_targets={}; descriptor_receipts=[]
    for row in descriptors:
        table=row['display_table']; donor=table['donor_offset']
        if donor not in display_tables:
            at=bank.put(bytes(table['bytes']))
            for p,target in table['pointers'].items():
                if target not in model_targets: raise ValueError('Missing complete scenery display dependency')
                bank.pointer(at+int(p)-donor,model_targets[target],'gpu')
            display_tables[donor]=at
        for draw in row['body']+([row['shadow']['draw']] if row['shadow'] else []):
            identity=draw['donor_offset']
            shadow=draw not in row['body']
            if identity not in draws:
                at=bank.put(struct.pack('>IBBH',0,draw['material_index'],draw['geometry_index'],0))
                bank.callbacks.append((at,int(shadow))); draws[identity]=at
        lists=bank.put(bytes(len(row['body'])*4))
        for i,draw in enumerate(row['body']): bank.pointer(lists+i*4,draws[draw['donor_offset']])
        at=bank.put(bytes(32)); descriptor_targets[row['key']]=at
        bank.pointer(at,display_tables[donor]); struct.pack_into('>I',bank.data,at+4,len(row['body']))
        bank.pointer(at+8,lists)
        if row['shadow']:
            shadow=row['shadow']; obj=objects[shadow['draw']['object']]
            resources=[r for r in obj['resources'] if r['donor_offset']==shadow['vertices']['donor_offset']]
            if len(resources)!=1 or resources[0]['bytes']!=64: raise ValueError('Missing full shadow vertices')
            vertices=objects_at[obj['key']]+resources[0]['native_offset']
            flags=bank.put(bytes.fromhex(shadow['fix']['hex']))
            struct.pack_into('>I',bank.data,at+12,4); bank.pointer(at+16,vertices)
            struct.pack_into('>f',bank.data,at+20,shadow['length'])
            bank.pointer(at+24,flags);bank.pointer(at+28,draws[shadow['draw']['donor_offset']])
        descriptor_receipts.append(dict(key=row['key'],offset=at,source_table_index=row['table_index']))
    positions={}; types=[]
    for row in bindings:
        pointers=[]
        for position in row['positions']:
            raw=bytes.fromhex(position['hex'])
            if raw not in positions: positions[raw]=bank.put(raw)
            pointers.append(positions[raw])
        types.append((int(row['foreground_id'],16),list(descriptor_targets).index(row['descriptor']),pointers))
    type_at=bank.put(bytes(len(types)*16))
    for i,(fg,index,pointers) in enumerate(sorted(types)):
        at=type_at+i*16;struct.pack_into('>IHH',bank.data,at,fg,0,index)
        for j,target in enumerate(pointers): bank.pointer(at+8+j*4,target)
    rows=bank.put(bytes(len(descriptors)*8))
    for i,at in enumerate(descriptor_targets.values()): bank.pointer(rows+i*8,at)
    cpu=bank.put(struct.pack('>'+str(len(bank.cpu))+'I',*sorted(bank.cpu)))
    gpu=bank.put(struct.pack('>'+str(len(bank.gpu))+'I',*sorted(bank.gpu)))
    callbacks=bank.put(b''.join(struct.pack('>II',*r) for r in sorted(bank.callbacks)))
    bank.data.extend(bytes(-len(bank.data)%16))
    header=(MAGIC,1,len(bank.data),0,cpu,len(bank.cpu),gpu,len(bank.gpu),callbacks,len(bank.callbacks),
            rows,len(descriptors),type_at,len(types),pal,active,terms,trampoline)
    struct.pack_into('>'+str(len(header))+'I',bank.data,0,*header)
    receipt=dict(season=season,bytes=len(bank.data),sha256=sha256(bank.data),objects=object_receipts,
        descriptors=descriptor_receipts,foreground_ids=[f'{fg:04X}' for fg,_,_ in sorted(types)],
        cpu_fixups=len(bank.cpu),gpu_fixups=len(bank.gpu),callback_fixups=len(bank.callbacks),
        palette_offset=pal,active_palette_offset=active,trampoline_offset=trampoline,
        descriptor_table_offset=rows,type_table_offset=type_at)
    return bytes(bank.data),receipt


def install(base, prior, blob, core, original, output, art_path):
    """Extend the existing seasonal owners without relocating their DMA IDs."""
    from aflib import CODE_RAM, CODE_VROM, by_vrom
    from apply_translation import write_new
    from map_artwork import compile_commands
    from v3_asset_loader import ROOT, BLOB, compile_part
    from v3_equipment_runtime import RAM, retired_module_space
    from v3_import_storage import jump
    from v3_player_actions import native_references
    from v3_npc_clothing import guard_incoming

    old=prior['equipment_resources']; ground=old['ground_categories']
    pos=old['blob_offset'];module=bytearray(blob[pos:pos+old['bytes']])
    if (old.get('scenery') or old['bytes']!=0x12000 or old['ram']!=RAM
            or RAM+old['bytes']!=RUNTIME_RAM or RUNTIME_END>prior['furniture']['bank_pool']['start']
            or sha256(module)!=old['sha256'] or any(module[BOOT_RAM-RAM:BOOT_END-RAM])
            or ground['config_offset']+ground['config_bytes']!=BOOT_RAM-RAM
            or old['player_actions']['code']['symbols']['af_v3_player_selected_equipment']!=0x804A5828):
        raise ValueError('Changed scenery code/resident ownership')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                  (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    art,assets,palette_data,evidence=prepared(source,art_path)
    wrapper=compile_commands(output/'palette', ROOT/'overlays/v3/scenery_palette.c',(('palette',64),))['palette']
    if wrapper.hex()!='fd10000001000000e800000000000000f500018007000000e600000000000000f00000000703c000e700000000000000de00000002000000df00000000000000':
        raise ValueError('Changed complete palette wrapper')
    banks={};unique={};reservations=[];allocation=copy.deepcopy(prior)
    for season in SEASONS:
        bank,record=pack_bank(art,assets,palette_data,season,wrapper)
        checksum=sha256(bank)
        if checksum not in unique:
            needed=len(bank)+(RUNTIME_END-RUNTIME_RAM if not unique else 0)
            space=retired_module_space(base,allocation,blob,needed)
            if space is None: raise ValueError('No verified retired storage for complete scenery bank')
            at=space['blob_offset']; unique[checksum]=at;reservations.append(space)
            allocation.setdefault('scenery_reservations',[]).append(space)
            blob[at:at+len(bank)]=bank
            if len(unique)==1: packet_at=(at+len(bank)+15)&~15
        at=unique[checksum]
        record.update(blob_offset=at,vrom=BLOB+at,crc32=zlib.crc32(bank))
        banks[season]=record
        write_new(output/f'scenery-{season}.bin',bank)
    files,native=by_vrom(base),by_vrom(original)
    rows=[]; configs=[]
    occupied={r['native_category'] for r in old['item_categories']['objects']}
    native_term=native[CODE_VROM].extract(original)[0x800CA070-CODE_RAM:0x800CA1DC-CODE_RAM]
    if bytes(core[0x800CA070-CODE_RAM:0x800CA1DC-CODE_RAM])!=native_term:
        raise ValueError('Changed complete native calendar-term consumer')
    for variant,spec in enumerate(ground['owners']):
        data=files[spec['vrom']].extract(base);rel=files[spec['reloc']].extract(base)
        orig=native[spec['vrom']].extract(original);cap=spec['capacity'];ram=spec['ram']
        if sha256(data)!=spec['output_sha256'] or sha256(rel)!=spec['output_reloc_sha256']:
            raise ValueError('Changed complete seasonal owner or relocation')
        groups,absolute,records,locations,slots=native_references(data,rel,
            expected_sections=tuple(spec['sections'][:3])+ (cap['bss_bytes'],))
        # Native tables contain 112 low and 84 environmental rows. The new IDs
        # lie beyond both tables, not over existing scenery identities.
        candidate=[]
        for at in range(spec['sections'][0],len(data)-24,4):
            values=[absolute.get(at+4*i) for i in range(6)]
            if (all(v is not None for v in values) and values[1]-values[0]==112*12
                    and values[5]-values[1]==84*12): candidate.append((at,values))
        if len(candidate)!=1: raise ValueError('Changed complete native scenery type tables')
        table_at,values=candidate[0]
        for fg in banks[spec['role']]['foreground_ids']:
            identity=int(fg,16)
            if not (112<=identity<0x800 or 0x800+84<=identity<0x1000):
                raise ValueError('Scenery identity overlaps original foreground content')
        body=cap['callback_offset'];shadow=body+0x138
        for start,end in ((body,body+0x138),(shadow,shadow+0x13C),(0x47A8,0x47C0),(0x47C8,0x495C)):
            if data[start:end]!=orig[start:end]: raise ValueError('Changed native scenery consumer body')
        if tuple(struct.unpack_from('>2I',data,0x47A8))!=(0x27BDFFE0,0xAFB00018):
            raise ValueError('Changed scenery classification prologue')
        guard_incoming(data,spec['sections'][0],ram,[(0x47A8,8)])
        if slots & {0x47A8,0x47AC,spec['sections'][0]+16}:
            raise ValueError('Scenery hook contains unexpected relocation')
        if any(v==ram+0x47AC for v in absolute.values()):
            raise ValueError('Scenery pointer enters displaced prologue')
        used=set(range(spec['count']+1))|{cap['type_base']+c for c in occupied}
        starts=[n for n in range(spec['count']+1,cap['count']-9) if not set(range(n,n+10))&used]
        if not starts: raise ValueError('No free complete scenery descriptor range')
        first=starts[0];bank=banks[spec['role']]
        size=cap['resident_bytes']+bank['bytes'];profile=spec['sections'][0]
        if u32(data,profile+16)!=ground['code']['symbols']['af_v3_ground_'+spec['role']]:
            raise ValueError('Changed seasonal constructor owner')
        descriptor=spec['allocation_descriptor']-CODE_RAM
        if tuple(struct.unpack_from('>4I',core,descriptor))!=(spec['vrom'],spec['vrom']+len(data),ram,ram+cap['resident_bytes']):
            raise ValueError('Changed complete scenery overlay allocation')
        configs.append((spec['slot'],spec['constructor']-ram,cap['resident_bytes'],bank['bytes'],bank['vrom'],bank['crc32'],
                        cap['table_offset'],cap['count'],first,body,shadow,0x47A8))
        rows.append(dict(role=spec['role'],vrom=spec['vrom'],reloc=spec['reloc'],ram=ram,
            before_sha256=sha256(data),before_reloc_sha256=sha256(rel),bank_offset=cap['resident_bytes'],
            bank_bytes=bank['bytes'],resident_bytes=size,allocation_descriptor=spec['allocation_descriptor'],
            actor_bytes=cap['actor_bytes'],first_index=first,descriptor_count=10,
            native_type_table=dict(offset=table_at,low_count=112,environment_count=84,pointers=values),
            consumers=dict(body_offset=body,body_sha256=sha256(data[body:body+0x138]),
                shadow_offset=shadow,shadow_sha256=sha256(data[shadow:shadow+0x13C]),
                classify_offset=0x47A8,classify_sha256=sha256(data[0x47A8:0x495C]))))
    header='../'*len(output.relative_to(ROOT).parts)+'overlays/v3/scenery.h'
    config_source=f'#include "{header}"\nconst Scenery af_v3_scenery_config[4]={{\n'
    config_source+=''.join(' {'+','.join(f'0x{v:X}u' for v in row)+'},\n' for row in configs)+'};\n'
    config_path=output/'scenery-config.c';write_new(config_path,config_source.encode())
    code,compiled=compile_part('scenery',output/'scenery',extra_sources=(str(config_path.relative_to(ROOT)),))
    if len(code)>RUNTIME_END-RUNTIME_RAM: raise ValueError('Scenery code exceeds owned reservation')
    if packet_at+len(code)>reservations[0]['blob_offset']+reservations[0]['bytes']:
        raise ValueError('Scenery code exceeds retired cartridge storage')
    blob[packet_at:packet_at+len(code)]=code
    boot,bootstrap=compile_part('scenery_bootstrap',output/'scenery_bootstrap',defines=(
        f'AF_SCENERY_VROM=0x{BLOB+packet_at:X}u',f'AF_SCENERY_BYTES={len(code)}u',
        f'AF_SCENERY_CRC=0x{zlib.crc32(code):X}u'))
    if len(boot)>BOOT_END-BOOT_RAM: raise ValueError('Scenery bootstrap exceeds existing free space')
    module[BOOT_RAM-RAM:BOOT_RAM-RAM+len(boot)]=boot
    changes={}
    for variant,(row,spec) in enumerate(zip(rows,ground['owners'],strict=True)):
        data=bytearray(files[spec['vrom']].extract(base));rel=bytearray(files[spec['reloc']].extract(base))
        patches=[]
        for at,after in ((spec['sections'][0]+16,bootstrap['symbols']['af_v3_scenery_'+spec['role']]),
                         (0x47A8,jump(compiled['symbols'][f'af_v3_scenery_type{variant}'])),(0x47AC,0)):
            patches.append(dict(offset=at,before=u32(data,at),after=after));struct.pack_into('>I',data,at,after)
        struct.pack_into('>I',rel,12,row['resident_bytes']-len(data))
        struct.pack_into('>I',core,spec['allocation_descriptor']-CODE_RAM+12,spec['ram']+row['resident_bytes'])
        row.update(patches=patches,output_sha256=sha256(data),output_reloc_sha256=sha256(rel),
                   config=list(configs[variant]))
        changes[spec['vrom']]=bytes(data);changes[spec['reloc']]=bytes(rel)
    blob[pos:pos+len(module)]=module
    receipt=dict(format='AFV3-SCENERY-RUNTIME-1',**evidence,art_directory=str(art_path.resolve().relative_to(ROOT)),
        banks=list(banks.values()),reservations=reservations,owners=rows,bootstrap=bootstrap,
        bootstrap_ram=BOOT_RAM,code=compiled,ram=RUNTIME_RAM,bytes=len(code),blob_offset=packet_at,vrom=BLOB+packet_at,
        sha256=sha256(code),crc32=zlib.crc32(code),config_sha256=sha256(config_source.encode()),
        native_term_sha256=sha256(native_term),additional_fixed_resident_bytes=RUNTIME_END-RUNTIME_RAM,
        additional_scene_resident_bytes=max(r['bank_bytes'] for r in rows),
        selected_item='223B',selectable=False,acquisition_installed=False,saved_format_changed=False,
        source_palette_wrapper_sha256=sha256(wrapper),native_render_tested=False)
    report=copy.deepcopy(old);report['scenery']=receipt
    report.update(sha256=sha256(module),crc32=zlib.crc32(module),additional_resident_bytes=RUNTIME_END-RUNTIME_RAM)
    return report,changes


TREE_CONTRACTS={
    'bg_item_fg_sub_tree_grow':(280,('b2ebf5ae218081b040b81e79e2554cd3b7d388555d76087e916dabb98f26de70',)),
    'bg_item_fg_sub':(720,('3ffbead261c106ac1e79f2b6254334e0cafbfbc41c01d98fea671205a5abbc9a',)),
    'bIT_common_bury_after':(496,(
        '30ce1d551b95d0ed31ac7e232f46a72e8209752b66a336a3c623726f00c0ef6f',
        '9f1a7b58e97782284590597ff983337fe0bbf8ce964271a179f02e4fd02063cf',
        '28bc9af9a5fe106a65e01d2805f63f6cfc1bf4a8abc2c26e9e42ac35636ac930',
        '178eafc4e48e52786ad9e8d9b857eff51a5713b734f7872eea3e7c1f4857eb89')),
}


def tree_rules(source):
    """Complete donor consumers and actual growth/stump tables, not name rules."""
    functions={}
    for name,(size,hashes) in TREE_CONTRACTS.items():
        offsets=sorted(at for at,rows in source.functions.items() if any(n==name for n,_ in rows))
        if len(offsets)!=len(hashes): raise ValueError('Missing complete tree-state consumers')
        functions[name]=[]
        for at,digest in zip(offsets,hashes,strict=True):
            raw,receipt=source.function(at)
            if len(raw)!=size or sha256(raw)!=digest: raise ValueError('Changed complete tree-state consumer')
            functions[name].append(receipt)
    targets={name:{r[3] for r in rows[0]['relocations'].values() if r[2]==5}
             for name,rows in functions.items()}
    if targets['bg_item_fg_sub_tree_grow']!={0xD510} or targets['bg_item_fg_sub']!={0xD4F0}:
        raise ValueError('Changed complete tree-state table references')
    from v3_scenery import resource
    grow=resource(source,0xD510,size=84*4);stump=resource(source,0xD4F0,size=4*4*2)
    states=list(struct.iter_unpack('>hh',bytes.fromhex(grow['hex'])))[78:84]
    stumps=[struct.unpack_from('>H',bytes.fromhex(stump['hex']),i*8+6)[0] for i in range(4)]
    if states!=[(-1,0),(-1,1),(-1,2),(-1,3),(0,4),(0,4)] or stumps!=[0x7E,0x7D,0x7C,0x7B]:
        raise ValueError('Changed golden-tree source stages or stump sizes')
    return dict(functions=functions,tables=dict(growth=grow,stumps=stump),first=0x863,count=6,
        hidden_first=0x7F,hidden_count=3,selected_item=0x223B,plant_item=0x2202,hole=0x5D,
        growth=states,stumps=stumps,source_rel_sha256=sha256(source.rel),
        source_symbols_sha256=sha256(source.symbols.encode()))


def install_gameplay(base,prior,blob,core,original,output):
    """Connect shared planting and tree-state primitives without enabling tools."""
    from aflib import CODE_RAM,CODE_VROM,by_vrom
    from apply_translation import write_new
    from v3_asset_loader import ROOT,BLOB,compile_part
    from v3_equipment_runtime import RAM
    from v3_import_storage import jump
    from v3_player_actions import native_references
    from v3_npc_clothing import guard_incoming
    old=prior['equipment_resources'];previous=old['scenery'];position=old['blob_offset']
    if previous.get('tree_states'):
        return install_daily(base,prior,blob,core,original,output)
    module=bytearray(blob[position:position+old['bytes']])
    if (previous.get('tree_states') or old['bytes']!=0x12000 or sha256(module)!=old['sha256']
            or previous['ram']!=RUNTIME_RAM or previous['additional_fixed_resident_bytes']!=4096
            or RUNTIME_END>prior['furniture']['bank_pool']['start']):
        raise ValueError('Changed tree-state runtime dependency')
    start=previous['blob_offset'];old_code=blob[start:start+previous['bytes']]
    if sha256(old_code)!=previous['sha256'] or module[BOOT_END-RAM-4:BOOT_END-RAM]!=bytes(4):
        raise ValueError('Changed scenery packet or occupied cache word')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                  (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    rules=tree_rules(source);files,native=by_vrom(base),by_vrom(original);original_core=native[CODE_VROM].extract(original)
    core_ranges=((0x800A5970,0x800A5A0C,'grow'),(0x800A56F0,0x800A5970,'stump'))
    core_consumers=[]
    for a,b,name in core_ranges:
        at=a-CODE_RAM;data=bytes(core[at:b-CODE_RAM])
        if data!=original_core[at:b-CODE_RAM]: raise ValueError('Changed complete native tree-state consumer')
        guard_incoming(bytes(core),len(core),CODE_RAM,[(at,8)])
        core_consumers.append(dict(name=name,start=a,end=b,sha256=sha256(data),before=data[:8].hex()))
    layouts=[]
    for variant,row in enumerate(previous['owners']):
        data,rel=(files[row[k]].extract(base) for k in ('vrom','reloc'))
        if sha256(data)!=row['output_sha256'] or sha256(rel)!=row['output_reloc_sha256']:
            raise ValueError('Changed complete tree planting owner')
        sections=struct.unpack_from('>5I',rel);original_owner=native[row['vrom']].extract(original)
        begin,end=0x19A4,0x1B68
        if data[begin:end]!=original_owner[begin:end] or data[begin:begin+8]!=bytes.fromhex('27bdffd8afa40028'):
            raise ValueError('Changed complete native bury conversion')
        groups,absolute,records,locations,slots=native_references(data,rel,expected_sections=sections[:4])
        target=row['ram']+begin
        calls=[at for at in range(0,sections[0],4) if u32(data,at)==jump(target,link=True)]
        if len(calls)!=1 or any(v==target for v in absolute.values()) or any(v==target for lows in groups.values() for _,v in lows):
            raise ValueError('Changed complete native bury consumer references')
        if any(at not in slots or locations[at]>>24!=0x44 for at in calls):
            raise ValueError('Missing native bury call relocation')
        layouts.append((row,data,rel,records,locations,calls))
    include='../'*len(output.relative_to(ROOT).parts)+'overlays/v3/scenery_trees.h'
    config_source=f'#include "{include}"\nconst Scenery af_v3_scenery_config[4]={{\n'
    config_source+=''.join(' {'+','.join(f'0x{v:X}u' for v in row['config'])+'},\n' for row in previous['owners'])+'};\n'
    fields=[rules[k] for k in ('first','count','hidden_first','hidden_count','selected_item','plant_item','hole')]+[0]
    config_source+='const TreeRule af_v3_tree_rule={'+','.join(f'0x{v:X}' for v in fields)+',\n {'
    config_source+=','.join('{'+','.join(str(v) for v in stage)+'}' for stage in rules['growth'])+'},\n {'
    config_source+=','.join(str(v) for v in rules['stumps'])+'}};\n'
    config_source+='const u32 af_v3_tree_bury_offsets[4]={0x19A4,0x19A4,0x19A4,0x19A4};\n'
    config_path=output/'scenery-config.c';write_new(config_path,config_source.encode())
    code,compiled=compile_part('scenery',output/'scenery',extra_sources=(
        'overlays/v3/scenery_trees.c',str(config_path.relative_to(ROOT))))
    reservation=previous['reservations'][0]
    if len(code)>RUNTIME_END-RUNTIME_RAM or start+len(code)>reservation['blob_offset']+reservation['bytes']:
        raise ValueError('Tree-state code exceeds reserved memory or cartridge storage')
    if any(blob[start+len(old_code):start+len(code)]) and start+len(code)>start+len(old_code):
        # Bytes after the old packet are the checked retired module, not empty
        # padding. The entire reservation was already retained as live storage.
        pin=reservation['predecessor_report'];raw=(ROOT/pin).read_bytes()
        if sha256(raw)!=reservation['predecessor_report_sha256']:
            raise ValueError('Changed full retired-module reservation evidence')
    boot,bootstrap=compile_part('scenery_bootstrap',output/'scenery_bootstrap',defines=(
        'AF_V3_SCENERY_TREES',f'AF_SCENERY_VROM=0x{BLOB+start:X}u',f'AF_SCENERY_BYTES={len(code)}u',
        f'AF_SCENERY_CRC=0x{zlib.crc32(code):X}u',
        f'AF_SCENERY_GROW=0x{compiled["symbols"]["af_v3_tree_grow"]:X}u',
        f'AF_SCENERY_STUMP=0x{compiled["symbols"]["af_v3_tree_stump"]:X}u'))
    if (len(boot)>BOOT_END-BOOT_RAM-4 or bootstrap['symbols']['af_v3_native_tree_grow']!=0x804ADFC0
            or bootstrap['symbols']['af_v3_native_tree_stump']!=0x804ADFD0):
        raise ValueError('Tree-state bootstrap exceeds its fixed contract')
    # Before replacing the complete owned prefix, retain its original code and
    # verify all remaining bytes are the previously unused zeros.
    bstart=BOOT_RAM-RAM;n=previous['bootstrap']['bytes']
    if sha256(module[bstart:bstart+n])!=previous['bootstrap']['sha256'] or any(module[bstart+n:BOOT_END-RAM]):
        raise ValueError('Changed bootstrap code or occupied owned suffix')
    module[bstart:BOOT_END-RAM]=boot+bytes(BOOT_END-BOOT_RAM-len(boot))
    blob[start:start+len(code)]=code
    owners=[];changes={};planting=[]
    for variant,(row,old_data,old_rel,records,locations,calls) in enumerate(layouts):
        data=bytearray(old_data);rel=bytearray(old_rel);patches=[];profile=u32(rel,0)
        edits=[(profile+16,bootstrap['symbols']['af_v3_scenery_'+row['role']]),
            (0x47A8,jump(compiled['symbols'][f'af_v3_scenery_type{variant}']))]
        edits += [(at,jump(compiled['symbols'][f'af_v3_tree_bury{variant}'],link=True)) for at in calls]
        for at,after in edits:
            patches.append(dict(offset=at,before=u32(data,at),after=after));struct.pack_into('>I',data,at,after)
        removed={locations[at] for at in calls};kept=[r for r in records if r not in removed]
        struct.pack_into('>I',rel,16,len(kept))
        rel[20:-4]=struct.pack('>'+str(len(kept))+'I',*kept)+bytes(len(rel)-24-4*len(kept))
        updated=copy.deepcopy(row);updated.update(before_sha256=sha256(old_data),before_reloc_sha256=sha256(old_rel),
            output_sha256=sha256(data),output_reloc_sha256=sha256(rel),patches=patches)
        owners.append(updated);changes[row['vrom']]=bytes(data);changes[row['reloc']]=bytes(rel)
        planting.append(dict(role=row['role'],entry=0x19A4,end=0x1B68,native_sha256=sha256(old_data[0x19A4:0x1B68]),
            calls=calls,removed_relocations=sorted(removed)))
    for row in core_consumers:
        at=row['start']-CODE_RAM;after=jump(bootstrap['symbols']['af_v3_tree_'+row['name']+'_dispatch'])
        struct.pack_into('>2I',core,at,after,0);row['after']=struct.pack('>2I',after,0).hex()
    blob[position:position+len(module)]=module
    current=copy.deepcopy(previous)
    current.update(owners=owners,code=compiled,bytes=len(code),sha256=sha256(code),crc32=zlib.crc32(code),
        bootstrap=bootstrap,config_sha256=sha256(config_source.encode()))
    current['tree_states']=dict(source=rules,core_consumers=core_consumers,planting=planting,
        cache_word=0x804ADFEC,shared_packet_bytes=len(code),growth_and_stumps_installed=True,
        planting_conversion_installed=True,daily_growth_owner_installed=False,collision_installed=False,
        shake_drop_installed=False,planting_effect_installed=False,additional_resident_bytes=0,
        saved_format_changed=False,choices_enabled=0,native_test='pending')
    current['reservations'][0]['used_bytes']=start+len(code)-reservation['blob_offset']
    result=copy.deepcopy(old);result['scenery']=current
    result.update(sha256=sha256(module),crc32=zlib.crc32(module),additional_resident_bytes=0)
    return result,changes


DAILY_DONOR={
    'mAGrw_KillTree':(88,'7f267745be95ce99ac5076282d0acadc226ef08d18212b9c9aa2470ae0675b83'),
    'mAGrw_CheckNearTree':(944,'9db649d9a8d186980156d17f53ce40306232eaf51b9db5d6148823fba656e4ba'),
    'mAGrw_CheckGoldTree':(32,'3897bda5f11a6fc1aae082fd0e77fdb94577c837df85a3240e95d50bcb1357f6'),
    'mAGrw_GrowTree':(324,'74d640617aaa4c0a829ceac720e05dbb0f2f0c7309bc65edd5c95eca1246bcb2'),
    'mAGrw_GrowPlant':(428,'886427f98f89b4d293d33ce93c21e054d863ec48272de02db6db3f93f37713d1'),
    'mAGrw_SetTree0Info':(232,'969f1a3a820f006b36d5221ec9fbc5e4ea4126fb6e0b94e439eaf79ef13d79f4'),
    'mAGrw_ResetTree0Info':(196,'d79b6bbcf4f05a1b3a04d3ae0ccfb1deddce19e2a4df288b8603a467b583452b'),
    'mAGrw_KillTree0':(320,'1daa4bc17dde08e2dadb313dfbf77aaa24e48625d6db479d1def49ec6df414f4'),
    'mAGrw_ThinTree':(300,'753ba275cb451a0e93f5300e6d6d0db15d5c6632a599ed833d5bc1fa4bfa675f'),
}
DAILY_NATIVE=(
    ('near',0x398,764,'b81bf642c642221868b2971399d3ab226dc6b04d85beaedc43a1d41828dc4e0f'),
    ('plant',0x910,368,'b552a920c7096e2a682cab4e9b38d40d1e25a58ab42f1beaa00c41ed8e1b49d2'),
    ('set_info',0x14A0,364,'c001b64f1378c6cd1a658f4485d70357cea6ca41d1b34d59a5f618e01cacd599'),
    ('reset_info',0x160C,308,'73fd7f748d268bc9dd9f6084c28df31d91000ab9f736ecdfafa16fc696b44b30'),
    ('kill_info',0x1740,276,'1b4cc9a70c0ae9366bb057aeffaa77b0d4498a6f8916e824c3bb632688022cf9'),
    ('thin',0x1854,376,'165dbafc3f476eef73cf8301679c1a84cb4e6babbc94a20dcb75a79577cc64ce'),
    ('renew',0x475C,692,'0f84891a0dd782361ed0ab687fc81b0b8775b59b26514f9735ee358afb6a1651'),
)


def daily_contract(source,owner,rel,core):
    from aflib import CODE_RAM
    from v3_player_actions import native_references
    from v3_import_storage import jump
    donor={}
    for name,(size,digest) in DAILY_DONOR.items():
        offsets=[at for at,rows in source.functions.items() if any(n==name for n,_ in rows)]
        if len(offsets)!=1:raise ValueError('Missing unique daily tree consumer')
        raw,receipt=source.function(offsets[0])
        if len(raw)!=size or sha256(raw)!=digest:raise ValueError('Changed complete daily tree source rule')
        donor[name]=receipt
    native=[]
    for name,at,n,digest in DAILY_NATIVE:
        if sha256(owner[at:at+n])!=digest:raise ValueError('Changed native daily tree consumer: '+name)
        native.append(dict(name=name,offset=at,bytes=n,sha256=digest))
    # The original loader establishes the exact owner pointer before invoking
    # renewal and keeps both loaded dimensions intact throughout this extension.
    loader=core[0x8005615C-CODE_RAM:0x80056234-CODE_RAM]
    expected=bytes.fromhex('27bdffc83c03801224636ea0afbf001cafa400388c6e001424010007246f7fff15c100293c0280ab91ef78b23c1880ab27185760244207c003022023afa200280c026ff0afaf002c3c08801025080c5c1040001bad0200003c0400973c0500973c0680ab3c0780ab24e7576024c607c024a554a0248409200c0098f0afa200103c1980108f390c5c8fab00283c0980ab25294f1c03295021014b10238fa400380040f80927a5002c8fac002c3c0180133c0480108c840c5c0c027010a02c67510c0156e1000000008fbf001c27bd003803e0000800000000')
    if loader!=expected:raise ValueError('Changed complete daily owner loading/lifetime')
    hi,absolute,records,locations,slots=native_references(owner,rel,expected_sections=(18960,368,0,1056))
    bindings=((0x830,0x398,'af_v3_tree_near',True),(0x4ABC,0x910,'af_v3_tree_daily_plant',False),
        (0x28E0,0x14A0,'af_v3_tree_set_info',True),(0x296C,0x160C,'af_v3_tree_reset_info',True),
        (0x2980,0x1854,'af_v3_tree_thin',True))
    for at,target,_,link in bindings:
        address=0x80AB07C0+target
        calls=[i for i in range(0,18960,4) if u32(owner,i)==jump(address,link=True)]
        pointers=[i for i,v in absolute.items() if v==address]
        splits=[h for h,ls in hi.items() if any(v==address for _,v in ls)]
        if (calls!=([at] if link else []) or pointers!=([] if link else [at]) or splits
                or at not in slots or locations[at]>>24!=(0x44 if link else 0x82)):
            raise ValueError('Changed complete daily callback references')
    return dict(donor=donor,native=native,loader_sha256=sha256(loader)),bindings,records,locations


CONTENTS_CORE_SHA='7ebf96a954c2c53346e132ea182ddc36c5b760905af03353563c9b1c3ed68cea'
CONTENTS_DONOR={
    'mAGrw_RecordCheckItem':(76,'7cc4e970a79e717aeac5d67e125e62c528ab6779f14ecdbb71692829f66b22d2'),
    'mAGrw_RecordHoneycombTree':(60,'0fff88dc37e6863ecf511c1e6517c5a6f53614990fd8db48faa3ebe7e6193441'),
    'mAGrw_RecordFtrTree':(60,'d4e8dd1313dce2d423ea54ed8dd02fa1d7025e109de2316abf0128932f7f7db7'),
    'mAGrw_CheckChangeTree':(60,'27a6f046636f765754937ab3cd1c1f7aa6c19e30c68ce8302c00fb45f5a51f95'),
    'mAGrw_CheckMoneyTree':(60,'27a6f046636f765754937ab3cd1c1f7aa6c19e30c68ce8302c00fb45f5a51f95'),
    'mAGrw_CountMoneyTree':(88,'7ac6ae4ff481d815c708753cc17a254062377b88c5f04aa11e553b3f13747d1d'),
    'mAGrw_GetChangeAbleTreeNum2':(100,'50e15816cd1611247f9e3ecf7715f1b5e4b6c16a4684e2fcd14e4b3306238db8'),
    'mAGrw_ChangeItemBlock2':(216,'1cf97b013fa54753455284c46499e8f44caf5907ca7d0ee6236a83630b402943'),
    'mAGrw_SetTreeBlockLine':(300,'6cf64cdf144c8728098b0faf1f7549e5dcb96531d942aa7bad1f6852b27c995e'),
    'mAGrw_SetHoneycombTree':(120,'7fff400f669c5334f73a5597f617d27a04eaa4f832f53d2668ead9d9593a10ad'),
    'mAGrw_SetFtrTree':(256,'06a3f177b9497c9d1e30ff7772bbd5122d750362816a53374b71c06e1288f8da'),
    'mAGrw_SetMoneyTreeRandom':(220,'356c51a13f98eb3257757f8cec25eadafbba92a664f3e43ff08de910412451da'),
    'mAGrw_SetMoneyTree':(236,'81b2fddc5d348026d96fd4e7f6a557a484e940f07ac62b9302ffebbe6857a8bc'),
}
CONTENTS_NATIVE=(
    ('record',0xC30,60,'724d0d87e2532b98f3d463d7a03b65739fa34e6eade14408d23a9eb685d1873d'),
    ('bees',0xC6C,60,'2304f8e8f3c4bef594275de961d11f8f4ce9bd91b5ce18951d2219542411a648'),
    ('furniture',0xCA8,60,'e059a2084f739237d13d0b8c3a928b616007023f20acd2a92a48c8ebd8781eba'),
    ('money',0xD4C,48,'6119832be372959e9ff3e61ba4a8262f5fab6a49f5eb204cec81e1d5d2bfa20f'),
    ('line',0xDB4,268,'08f5a0f50a95c1046e3b4a7d710341ddd44f9c5e377ca41d8d32e69fcbc84df2'),
    ('set_bees',0xEC0,116,'25c8688e5e9cbd5713219346c8c004a0dd237a57eb77b3539bec1d341e479759'),
    ('set_furniture',0xF34,268,'55d2a24422516db7e61d80cc00b5d9a9881f86bfe377aaf04c1292e6504e4ae2'),
    ('money_random',0x1040,208,'63f7a3ef9823659d5da077cf774dfc8b0ca9b840f1e4689b560b441a0aec8813'),
    ('set_money',0x1110,260,'d51f8b69b0fc6784fae609cee42e62ef9f23e275c42b3ab853e1b6f1c982055c'),
)


def contents_contract(source,owner,rel,core):
    from aflib import CODE_RAM
    from v3_player_actions import native_references
    from v3_import_storage import jump
    donor={}
    for name,(size,digest) in CONTENTS_DONOR.items():
        # The REL also has an unrelated same-named core helper. Bind this owner.
        offsets=[at for at,rows in source.functions.items() if at>0x190000 and any(n==name for n,_ in rows)]
        if len(offsets)!=1:raise ValueError('Missing unique daily content consumer')
        raw,receipt=source.function(offsets[0])
        if len(raw)!=size or sha256(raw)!=digest:raise ValueError('Changed complete tree-content source rule')
        donor[name]=receipt
    tables=[];table_receipts=[]
    for at,expected in ((0x52664,(0x804,0x861,0x868)),(0x5266C,(0x5E,0x7A,0x81)),
            (0x52674,(0x5F,0x79,0x80)),(0x5267C,(0x69,0x78,0x7F))):
        raw=source.rel[source.sections[5][0]+at:source.sections[5][0]+at+6]
        values=struct.unpack('>3H',raw)
        if values!=expected:raise ValueError('Changed tree-content source family table')
        tables.append(values);table_receipts.append(dict(section=5,offset=at,bytes=6,sha256=sha256(raw)))
    native=[]
    for name,at,n,digest in CONTENTS_NATIVE:
        if sha256(owner[at:at+n])!=digest:raise ValueError('Changed native content consumer: '+name)
        native.append(dict(name=name,offset=at,bytes=n,sha256=digest))
    # Full core count/change helpers remain untouched, including holiday users.
    core_data=core[0x80055E34-CODE_RAM:0x80055F28-CODE_RAM]
    if sha256(core_data)!=CONTENTS_CORE_SHA:raise ValueError('Changed native core content helpers')
    hi,absolute,records,locations,slots=native_references(owner,rel,expected_sections=(18960,368,0,1056))
    groups=((0x80AB13F0,(0xC90,0xCCC),'af_v3_tree_record_content',True,True),
        (0x80AB150C,(0x4AA8,0x4AD4),'af_v3_tree_count_money',False,True),
        (0x80055E34,(0xDF4,0x117C),'af_v3_tree_count_eligible',True,False),
        (0x80055EF8,(0xE84,0x10BC),'af_v3_tree_change_content',True,False))
    bindings=[]
    for target,ats,name,link,relocated in groups:
        calls=[i for i in range(0,18960,4) if u32(owner,i)==jump(target,link=True)]
        pointers=[i for i,v in absolute.items() if v==target]
        splits=[h for h,ls in hi.items() if any(v==target for _,v in ls)]
        if calls!=(list(ats) if link else []) or pointers!=([] if link else list(ats)) or splits:
            raise ValueError('Changed full content callback inventory')
        for at in ats:
            if (at in slots)!=relocated or (relocated and locations[at]>>24!=(0x44 if link else 0x82)):
                raise ValueError('Changed content callback relocation')
            bindings.append((at,target,name,link))
    return dict(donor=donor,native=native,tables=tables,table_sources=table_receipts,
        core_helpers_sha256=sha256(core_data)),tuple(bindings),records,locations


WORLD_NATIVE=(
    ('column',0x8006C980,2608,'69ed68aa1a87b3b8b9edb773746ba60a2d9116b148ba051ff69076ea6c0445c0','27bdffe0afb10018'),
    ('dig',0x8008C964,176,'a0899af5a2cc5d190d31cd7297f0440131bec7707f564ed7d9526d1b5afbeb3d','afa50004afa60008'),
    ('npc',0x8008D7B0,212,'859d536b93bd64b97a3c4a2287a851fcb38f9c1f181e86f678b6079777dcc43b','afa400003084ffff'),
)


def world_contract(source,core):
    from aflib import CODE_RAM
    from v3_npc_clothing import guard_incoming
    donor={}
    for at,size,digest in ((0x1DB50,3332,'bce9070a5a5bff8b86dc7d1829c576feab3ecd5446cb96f6f0e879253f14db54'),
            (0x39040,248,'cc9e0122c561705f90e0e61308b3f98cb2c89fd8449a52f583b24bdc34384e4d'),
            (0x39D88,220,'61ca154407ea62ee18164e6ebd400fb4ec55f545a119cd6b215f5906e25d3a99')):
        raw,receipt=source.function(at)
        if len(raw)!=size or sha256(raw)!=digest:raise ValueError('Changed complete donor world query')
        donor[receipt['symbol']]=receipt
    dimensions=[]
    for at,expected in ((2140,40.0),(2144,20.0),(2160,10.0),(2264,30.0),(2272,19.0),
            (2276,60.0),(2280,80.0),(2284,18.0)):
        raw=source.rel[source.sections[4][0]+at:source.sections[4][0]+at+4]
        if struct.unpack('>f',raw)[0]!=expected:raise ValueError('Changed source tree collision dimensions')
        dimensions.append(dict(section=4,offset=at,hex=raw.hex(),value=expected))
    native=[]
    for name,start,n,digest,prologue in WORLD_NATIVE:
        at=start-CODE_RAM
        if sha256(core[at:at+n])!=digest or core[at:at+8].hex()!=prologue:
            raise ValueError('Changed complete native world query: '+name)
        native.append(dict(name=name,start=start,bytes=n,sha256=digest,prologue=prologue))
    guard_incoming(core,len(core),CODE_RAM,[(at-CODE_RAM,8) for _,at,*_ in WORLD_NATIVE])
    return dict(donor=donor,dimensions=dimensions,native=native)


def interaction_contract(source,base,original,previous,ground):
    """Bind complete source records to retained native drop/cutting machinery."""
    from aflib import by_vrom
    from v3_player_actions import native_references
    from v3_import_storage import jump
    from v3_npc_clothing import guard_incoming
    from v3_scenery import resource
    functions={}
    specs={
        'drop_fruit':(496,('b8abf3d9b34277fca04d054d0746b16c349017c58241d120e61b2ce3f0c1834d',
            '3f7170eb94bd1460117429bb663ecd4c613664640ad11a9537ceb3d4091f8a41',
            '3599eabce6ae745ba9493ae9e63284e5ba5e9ffc007022f4390f041956ad917d',
            '71eb8c4e14f0b9298e7760627a0966a1c1c42fcbbd4242ae47c3c2ce05691711')),
        'bg_item_tree_fruit_drop':(380,('a5b7c44e8dd145096ad27042cc60e161c557e73b4e970300999306006a84d67b',
            '0cbc7bed7c4e6aff247a9e7cb43efb3b78c06f8e298fc60b299b942276b7f25e',
            'b9e32f05846920ef4bcc72f798b3239f887ad22e532572d6c765253f7fb6bb79',
            '8c1d450d793f61b60c44ad5a885ec3d88f76dddd02b60df8695e6c76a0548f83')),
        'bIT_common_clear_treeatr':(176,('79e048bcd56c300d19d10e71d233cbc76ac4cbfd64d2865e35b635d5e2cdd372',
            '38c428a0afa9e7c2de1578167c927c38c3fff5147f62fb98f8bb1fb019471e9a',
            '1abe7dc07be15bb56afe2d71f151d84a33b55261cd47babc61fc2178c1f6e563',
            'bbfbd1141cad3ee687e9e3fc55026a17c23570c07d55540c864a2d3ca2aa7c18'))}
    for name,(size,hashes) in specs.items():
        offsets=sorted(at for at,rows in source.functions.items() if any(n==name for n,_ in rows))
        if len(offsets)!=4:raise ValueError('Missing complete seasonal interaction consumers')
        functions[name]=[]
        for at,digest in zip(offsets,hashes,strict=True):
            raw,receipt=source.function(at)
            if len(raw)!=size or sha256(raw)!=digest:raise ValueError('Changed complete donor tree interaction')
            functions[name].append(receipt)
    drops=[];cuts=[]
    for at in (0x4549C,0x483FC,0x4B5CC,0x4E5CC):
        drop=resource(source,at,size=168);cut=resource(source,at+180,size=332)
        if (drop['sha256']!='5efec02170f3f9b95bbe34d1be9e4a7b5eee4355b4550994dd1df9ae52e48cce'
                or cut['sha256']!='2003feb5ef735364198ded81bcf04fbd54f90c814531fc8fbe753942bfe28fcb'):
            raise ValueError('Changed complete seasonal drop/cut records')
        drops.append(drop);cuts.append(cut)
    for name,tables in (('drop_fruit',drops),('bIT_common_clear_treeatr',cuts)):
        for fn,table in zip(functions[name],tables,strict=True):
            if table['donor_offset'] not in {r[3] for r in fn['relocations'].values() if r[2]==5}:
                raise ValueError('Missing source interaction table binding')
    drop_rows=list(struct.iter_unpack('>4H',bytes.fromhex(drops[0]['hex'])))
    cut_rows=list(struct.iter_unpack('>2H',bytes.fromhex(cuts[0]['hex'])))
    if (drop_rows[-4:]!=[(0x7F,0x2103,0x868,1),(0x80,0x1088,0x868,1),
                         (0x81,0x62,0x868,1),(0x867,0x223B,0x868,1)]
            or cut_rows[-8:]!=[(0x864,1),(0x865,2),(0x866,3),(0x867,3),
                              (0x868,3),(0x7F,3),(0x80,3),(0x81,3)]):
        raise ValueError('Changed source gold-tree interaction rules')
    current,native=by_vrom(base),by_vrom(original);owners=[]
    for row,expected_calls in zip(previous['owners'],((0x52C4,0x780C),(0x52C4,0x783C,0x78FC),
            (0x52C4,0x7814),(0x52C4,0x7818)),strict=True):
        data=current[row['vrom']].extract(base);old=native[row['vrom']].extract(original)
        rel=current[row['reloc']].extract(base);sections=struct.unpack_from('>5I',rel)
        groups,_,records,locations,_=native_references(data,rel,expected_sections=sections[:4])
        if sha256(data)!=row['output_sha256'] or sha256(rel)!=row['output_reloc_sha256']:
            raise ValueError('Changed complete interaction owner')
        complete=[]
        restored=bytearray(data)
        held=next(g for g in ground['owners'] if g['vrom']==row['vrom'])
        retained=[p for p in held['patches'] if 0x2100<=p['offset']<0x265C]
        if {p['offset'] for p in retained}!={0x2358,0x235C,0x24EC,0x24F0}:
            raise ValueError('Changed installed held-item drop windows')
        original_words={0x2358:0x308CF000,0x235C:0x000C6B03,0x24EC:0x00095303,0x24F0:0x15410004}
        for p in retained:
            if u32(data,p['offset'])!=p['after'] or u32(old,p['offset'])!=original_words[p['offset']]:
                raise ValueError('Changed retained held-item drop hook')
            struct.pack_into('>I',restored,p['offset'],original_words[p['offset']])
        for name,a,b in (('fruit_set',0x2100,0x265C),('drop_fruit',0x2698,0x2854),
                ('cut_decrement',0x2854,0x2940),('shake',0x2940,0x2A8C),('cut_attributes',0x4F98,0x5044)):
            if restored[a:b]!=old[a:b]:raise ValueError('Changed complete native tree interaction')
            complete.append(dict(name=name,offset=a,bytes=b-a,sha256=sha256(data[a:b])))
        start=groups[0x26B8];end=groups[0x26BC];cut=groups[0x4FBC]
        if (len(start)!=1 or len(end)!=1 or len(cut)!=1 or start[0][0]!=0x26C4
                or end!=[(0x26C0,start[0][1]+104)] or cut[0][0]!=0x4FC8):
            raise ValueError('Changed native complete drop/cut table references')
        da,ca=start[0][1]-row['ram'],cut[0][1]-row['ram']
        if (data[da:da+104]!=bytes.fromhex(drops[0]['hex'])[:104]
                or data[ca:ca+240]!=bytes.fromhex(cuts[0]['hex'])[:240]):
            raise ValueError('Native interaction prefix differs from the source')
        calls=tuple(at for at in range(0,sections[0],4) if u32(data,at)==jump(row['ram']+0x4F98,link=True))
        if calls!=expected_calls or any(at not in locations for at in calls):
            raise ValueError('Changed complete cut-attribute call inventory')
        spans=[(0x26B8,20),(0x2780,48),(0x295C,16)]+[(at,4) for at in calls]
        guard_incoming(data,sections[0],row['ram'],spans)
        if (struct.unpack_from('>4I',data,0x295C)!=(0x97AE005A,0x2401005E,0x97A4005A,0x15C1003F)
                or {a for a in locations if any(p<=a<p+n for p,n in spans)}
                    !={0x26B8,0x26BC,0x26C0,0x26C4,*calls}):
            raise ValueError('Changed interaction query instructions or relocations')
        owners.append(dict(role=row['role'],complete=complete,retained_held_patches=retained,drop_table=da,cut_table=ca,
                           calls=list(calls),spans=spans))
    return dict(functions=functions,drop_sources=drops,cut_sources=cuts,
                drops=drop_rows[:13]+drop_rows[-4:],cuts=cut_rows[-8:],owners=owners)


def install_daily(base,prior,blob,core,original,output):
    """Refresh shared tree stages and all installed consumers together."""
    from aflib import CODE_RAM,by_vrom
    from apply_translation import write_new
    from v3_asset_loader import ROOT,BLOB,compile_part
    from v3_import_storage import jump
    from v3_npc_clothing import guard_incoming
    old=prior['equipment_resources'];previous=old['scenery'];position=old['blob_offset']
    module=bytearray(blob[position:position+old['bytes']]);files=by_vrom(base)
    contents=bool(previous.get('daily_growth'))
    world=bool(previous.get('hidden_contents'))
    interactions=bool(previous.get('world_queries'))
    player=bool(previous.get('interactions'))
    capacity=12288 if interactions else 8192
    added=capacity-previous['additional_fixed_resident_bytes']
    if (previous.get('player_queries') or not previous.get('tree_states') or old['bytes']!=0x12000
            or sha256(module)!=old['sha256'] or previous['additional_fixed_resident_bytes']!=(12288 if player else 8192 if contents else 4096)
            or RUNTIME_RAM+capacity>prior['furniture']['bank_pool']['start']):
        raise ValueError('Changed daily-growth runtime dependency')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                  (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    rules=tree_rules(source)
    owner,rel=(files[v].extract(base) for v in (0x970920,0x9754A0))
    if contents:
        before=previous['daily_growth']
        if sha256(owner)!=before['sha256'] or sha256(rel)!=before['reloc_sha256']:
            raise ValueError('Changed installed daily owner')
        if world:
            from v3_player_actions import native_references
            evidence=(copy.deepcopy(previous['world_queries']) if interactions else world_contract(source,core))
            _,_,records,locations,_=native_references(owner,rel,expected_sections=(18960,368,0,1056))
            bindings=((0xC90,0,'af_v3_tree_record_content',True),(0xCCC,0,'af_v3_tree_record_content',True),
                (0x4AA8,0,'af_v3_tree_count_money',False),(0x4AD4,0,'af_v3_tree_count_money',False),
                (0xDF4,0,'af_v3_tree_count_eligible',True),(0x117C,0,'af_v3_tree_count_eligible',True),
                (0xE84,0,'af_v3_tree_change_content',True),(0x10BC,0,'af_v3_tree_change_content',True))
            evidence['tables']=previous['hidden_contents']['tables']
            actual=[list(struct.unpack_from('>3H',source.data,at)) for at in (0x52664,0x5266C,0x52674,0x5267C)]
            if evidence['tables']!=actual:raise ValueError('Changed installed hidden-content tables')
        else:evidence,bindings,records,locations=contents_contract(source,owner,rel,core)
        daily_bindings=((0x830,0x398,'af_v3_tree_near',True),(0x4ABC,0x910,'af_v3_tree_daily_plant',False),
            (0x28E0,0x14A0,'af_v3_tree_set_info',True),(0x296C,0x160C,'af_v3_tree_reset_info',True),
            (0x2980,0x1854,'af_v3_tree_thin',True))
        for at,_,name,link in (*daily_bindings,*(bindings if world else ())):
            target=previous['code']['symbols'][name]
            if u32(owner,at)!=(jump(target,link=True) if link else target) or at in locations:
                raise ValueError('Changed installed daily callback')
        bindings=(*bindings,*daily_bindings)
    else:
        evidence,bindings,records,locations=daily_contract(source,owner,rel,core)
    interaction=(copy.deepcopy(previous['interactions']) if player else
                 interaction_contract(source,base,original,previous,old['ground_categories']) if interactions else None)
    if player:
        import v3_scenery_player as player_adapter
        player_evidence,player_owner,player_rel,player_records=player_adapter.contract(source,base,original,old['player_actions'])
    guard_incoming(owner,18960,0x80AB07C0,[(0x475C,8)])
    include='../'*len(output.relative_to(ROOT).parts)+'overlays/v3/scenery_trees.h'
    configuration=f'#include "{include}"\nconst Scenery af_v3_scenery_config[4]={{\n'
    configuration+=''.join(' {'+','.join(f'0x{v:X}u' for v in row['config'])+'},\n' for row in previous['owners'])+'};\n'
    fields=[rules[k] for k in ('first','count','hidden_first','hidden_count','selected_item','plant_item','hole')]+[0]
    configuration+='const TreeRule af_v3_tree_rule={'+','.join(f'0x{v:X}' for v in fields)+',\n {'
    configuration+=','.join('{'+','.join(str(v) for v in stage)+'}' for stage in rules['growth'])+'},\n {'
    configuration+=','.join(str(v) for v in rules['stumps'])+'}};\n'
    configuration+='const u32 af_v3_tree_bury_offsets[4]={0x19A4,0x19A4,0x19A4,0x19A4};\n'
    config=[0x80100C5C,0x398,0x910,0x14A0,0x160C,0x1854,0x869,0x84E,32]
    configuration+='const TreeDaily af_v3_tree_daily_config={'+','.join(f'0x{v:X}' for v in config)+'};\n'
    if contents:
        configuration+='const u16 af_v3_tree_content_tables[4][3]={'+','.join(
            '{'+','.join(f'0x{v:X}' for v in row)+'}' for row in evidence['tables'])+'};\n'
    if interaction:
        for typename,name,shape,rows in (('TreeDrop','drops','[17]',interaction['drops']),
                ('u16','cuts','[8][2]',interaction['cuts'])):
            configuration+=f'const {typename} af_v3_tree_{name}{shape}={{'+','.join(
                '{'+','.join(f'0x{v:X}' for v in row)+'}' for row in rows)+'};\n'
    if player:
        configuration+='const u32 af_v3_tree_player_masks[2][3]={'+','.join(
            '{'+','.join(f'0x{v:X}u' for v in row)+'}' for row in player_evidence['masks'])+'};\n'
    path=output/'scenery-config.c';write_new(path,configuration.encode())
    sources=['overlays/v3/scenery_trees.c','overlays/v3/scenery_daily.c']
    if contents:sources.append('overlays/v3/scenery_contents.c')
    if world:sources.append('overlays/v3/scenery_world.c')
    if interactions:sources.append('overlays/v3/scenery_interactions.c')
    if player:sources.append('overlays/v3/scenery_player.c')
    code,compiled=compile_part('scenery',output/'scenery',extra_sources=(*sources,str(path.relative_to(ROOT))))
    start=previous['blob_offset'];reservation=previous['reservations'][0]
    if (sha256(blob[start:start+previous['bytes']])!=previous['sha256'] or len(code)>capacity
            or start+len(code)>reservation['blob_offset']+reservation['bytes']):
        raise ValueError('Daily tree packet exceeds owned cartridge or memory')
    defines=['AF_V3_SCENERY_WORLD'] if world else []
    if world:defines.extend(f'AF_SCENERY_{name.upper()}=0x{compiled["symbols"]["af_v3_tree_"+name]:X}' for name, *_ in WORLD_NATIVE)
    boot,bootstrap=compile_part('scenery_bootstrap',output/'scenery_bootstrap',defines=(*defines,
        'AF_V3_SCENERY_TREES','AF_V3_SCENERY_DAILY',f'AF_SCENERY_VROM=0x{BLOB+start:X}u',
        f'AF_SCENERY_BYTES={len(code)}u',f'AF_SCENERY_CRC=0x{zlib.crc32(code):X}u',
        f'AF_SCENERY_GROW=0x{compiled["symbols"]["af_v3_tree_grow"]:X}u',
        f'AF_SCENERY_STUMP=0x{compiled["symbols"]["af_v3_tree_stump"]:X}u',
        f'AF_SCENERY_RENEW=0x{compiled["symbols"]["af_v3_tree_renew_native"]:X}u'))
    a,b=BOOT_RAM-old['ram'],BOOT_END-old['ram'];n=previous['bootstrap']['bytes']
    if (sha256(module[a:a+n])!=previous['bootstrap']['sha256'] or any(module[a+n:b])
            or len(boot)>b-a-4 or bootstrap['symbols']['af_v3_native_tree_grow']!=0x804ADFC0
            or bootstrap['symbols']['af_v3_native_tree_stump']!=0x804ADFD0):
        raise ValueError('Changed daily bootstrap/cache/fallback reservation')
    module[a:b]=boot+bytes(b-a-len(boot));blob[start:start+len(code)]=code
    changes={};owners=[]
    for variant,row in enumerate(previous['owners']):
        data=bytearray(files[row['vrom']].extract(base));orel=files[row['reloc']].extract(base)
        if sha256(data)!=row['output_sha256'] or sha256(orel)!=row['output_reloc_sha256']:
            raise ValueError('Changed complete seasonal tree consumer')
        patches=[]
        edits=[(u32(orel,0)+16,bootstrap['symbols']['af_v3_scenery_'+row['role']],
                previous['bootstrap']['symbols']['af_v3_scenery_'+row['role']]),
            (0x47A8,jump(compiled['symbols'][f'af_v3_scenery_type{variant}']),
                jump(previous['code']['symbols'][f'af_v3_scenery_type{variant}']))]
        edits += [(at,jump(compiled['symbols'][f'af_v3_tree_bury{variant}'],link=True),
            jump(previous['code']['symbols'][f'af_v3_tree_bury{variant}'],link=True))
            for at in previous['tree_states']['planting'][variant]['calls']]
        for at,after,before in edits:
            if u32(data,at)!=before:raise ValueError('Changed seasonal tree dispatch')
            patches.append(dict(offset=at,before=before,after=after));struct.pack_into('>I',data,at,after)
        removed_owner=[]
        if interaction:
            from v3_player_actions import native_references
            _,_,owner_records,owner_locations,_=native_references(data,orel,expected_sections=struct.unpack_from('>4I',orel))
            symbol=compiled['symbols']
            blocks={0x26B8:(jump(symbol['af_v3_tree_drop_table'],link=True),0,0x8C500000,0x8C430004,0x97A2005A),
                0x2780:(0x00402025,jump(symbol['af_v3_tree_drop_item'],link=True),0x00602825,
                    0x00402025,0x8FA5005C,0x8FA60060,0x8FAB0064,0x8FAC0068,0,0,0,0),
                0x295C:(0x97A4005A,jump(symbol['af_v3_tree_bee_query'],link=True),0,0x1040003F)}
            blocks.update({at:(jump(symbol[f'af_v3_tree_cut{variant}'],link=True),)
                for at in interaction['owners'][variant]['calls']})
            for block_offset,words in blocks.items():
                for i,word in enumerate(words):
                    at=block_offset+i*4;patches.append(dict(offset=at,before=u32(data,at),after=word))
                    struct.pack_into('>I',data,at,word)
                    if at in owner_locations:removed_owner.append(owner_locations[at])
            keep=[v for v in owner_records if v not in removed_owner];orel=bytearray(orel)
            struct.pack_into('>I',orel,16,len(keep))
            orel[20:-4]=struct.pack('>'+str(len(keep))+'I',*keep)+bytes(len(orel)-24-4*len(keep))
            changes[row['reloc']]=bytes(orel)
        new=copy.deepcopy(row);new.update(before_sha256=row['output_sha256'],before_reloc_sha256=row['output_reloc_sha256'],
            output_sha256=sha256(data),output_reloc_sha256=sha256(orel),patches=patches,
            removed_relocations=removed_owner);owners.append(new);changes[row['vrom']]=bytes(data)
    core_hooks=[]
    for row in previous['tree_states']['core_consumers']:
        at=row['start']-CODE_RAM;before=bytes(core[at:at+8])
        if before.hex()!=row['after']:raise ValueError('Changed core tree-state dispatch')
        after=struct.pack('>2I',jump(bootstrap['symbols']['af_v3_tree_'+row['name']+'_dispatch']),0)
        core[at:at+8]=after;core_hooks.append(dict(offset=at,before=before.hex(),after=after.hex()))
    world_hooks=[]
    if world:
        for name,address,_,_,expected in WORLD_NATIVE:
            at=address-CODE_RAM;after=struct.pack('>2I',jump(bootstrap['symbols']['af_v3_tree_'+name+'_dispatch']),0)
            if interactions:
                matches=[h for h in previous['world_queries']['core_hooks'] if h['offset']==at]
                if len(matches)!=1:raise ValueError('Missing installed world-query hook')
                expected=matches[0]['after']
            if core[at:at+8].hex()!=expected:raise ValueError('Changed native world-query entry')
            core[at:at+8]=after;world_hooks.append(dict(offset=at,before=expected,after=after.hex(),name=name))
    data=bytearray(owner);relocation=bytearray(rel);patches=[];removed=set()
    for at,_,name,link in bindings:
        target=compiled['symbols'][name];after=jump(target,link=True) if link else target
        patches.append(dict(offset=at,before=u32(data,at),after=after));struct.pack_into('>I',data,at,after)
        if at in locations:removed.add(locations[at])
    for at,after in ((0x475C,jump(bootstrap['symbols']['af_v3_tree_renew_dispatch'])),(0x4760,0)):
        patches.append(dict(offset=at,before=u32(data,at),after=after));struct.pack_into('>I',data,at,after)
    kept=[v for v in records if v not in removed];struct.pack_into('>I',relocation,16,len(kept))
    relocation[20:-4]=struct.pack('>'+str(len(kept))+'I',*kept)+bytes(len(relocation)-24-4*len(kept))
    changes[0x970920]=bytes(data);changes[0x9754A0]=bytes(relocation)
    blob[position:position+len(module)]=module
    current=copy.deepcopy(previous);current.update(owners=owners,code=compiled,bytes=len(code),sha256=sha256(code),
        crc32=zlib.crc32(code),bootstrap=bootstrap,config_sha256=sha256(configuration.encode()),additional_fixed_resident_bytes=capacity)
    current['reservations'][0]['used_bytes']=start+len(code)-reservation['blob_offset']
    current['tree_states'].update(daily_growth_owner_installed=True,shared_packet_bytes=len(code))
    for row,hook in zip(current['tree_states']['core_consumers'],core_hooks,strict=True):row['after']=hook['after']
    receipt=dict(evidence,config=config,vrom=0x970920,reloc=0x9754A0,ram=0x80AB07C0,
        resident_bytes=sum(struct.unpack_from('>4I',rel)),previous_sha256=sha256(owner),previous_reloc_sha256=sha256(rel),
        sha256=sha256(data),reloc_sha256=sha256(relocation),patches=patches,removed_relocations=sorted(removed),
        core_hooks=core_hooks+world_hooks,additional_resident_bytes=added,additional_scene_resident_bytes=0,
        hidden_content_refresh_installed=contents,ordinary_gameplay_tested=False,native_test='pending')
    if contents:
        if interactions:
            current['interactions']=dict(interaction,additional_resident_bytes=added,additional_scene_resident_bytes=0,
                daily_owner=receipt,ordinary_gameplay_tested=False,native_test='pending')
            current['world_queries'].update(sha256=sha256(data),reloc_sha256=sha256(relocation),
                                            core_hooks=core_hooks+world_hooks)
            current['tree_states']['shake_drop_installed']=True
        else:current['world_queries' if world else 'hidden_contents']=receipt
        if world:current['hidden_contents'].update(sha256=sha256(data),reloc_sha256=sha256(relocation))
        current['daily_growth'].update(sha256=sha256(data),reloc_sha256=sha256(relocation),
            hidden_content_refresh_installed=True)
    else:current['daily_growth']=receipt
    result=copy.deepcopy(old);result['scenery']=current
    if player:
        po,pr,player_receipt=player_adapter.install(player_evidence,player_owner,player_rel,player_records,bootstrap,compiled['symbols'])
        changes[player_adapter.VROM]=po;changes[player_adapter.RELOC]=pr
        current['player_queries']=player_receipt
        result['player_actions'].update(owner_sha256=sha256(po),relocation_sha256=sha256(pr))
        result['player_motion'].update(owner_sha256=sha256(po),reloc_sha256=sha256(pr))
    result.update(sha256=sha256(module),crc32=zlib.crc32(module),additional_resident_bytes=added)
    return result,changes
