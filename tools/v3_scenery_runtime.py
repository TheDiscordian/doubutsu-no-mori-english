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
