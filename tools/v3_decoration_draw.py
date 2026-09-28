"""Bind all prepared event artwork to the complete donor draw controllers.

Generated donor functions/assets stay ignored. One shared native adapter owns
graphics allocation, segmented objects, projected shadows, and rig drawing.
"""
import copy
import json
import re
import struct
import zlib

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256
from apply_translation import write_new
from v3_asset_loader import ROOT,compile_part
from v3_furniture_pipeline import Source
from v3_holiday_structures import PREPARED,prepared_packet,source_bundle
from v3_password_policy import function

RAM,TABLE,ART,END=0x80700000,0x80704000,0x80708000,0x8072A000
SOURCES=('tools/v3_decoration_draw.py','overlays/v3/decoration_draw.c',
    'overlays/v3/decoration_draw.h','overlays/v3/decoration_draw.ld',
    'tools/v3_asset_loader.py','tools/v3_holiday_structures.py','tools/v3_room_goods.py')
NATIVE={
    'mCoBG_SetPlussOffset':'mCoBG_SetPlussOffset',
    'mCoBG_SetPluss5PointOffset_file':'mCoBG_SetPluss5PointOffset_file',
    'native_decor_matrix':'_Matrix_to_Mtx',
    'native_decor_rig_draw':'cKF_Si3_draw_R_SV',
    'Matrix_push':'Matrix_push','Matrix_pull':'Matrix_pull',
    'Matrix_translate':'Matrix_translate','Matrix_RotateZ':'Matrix_RotateZ',
    **{s:s for s in ('_texture_z_light_fog_prim','_texture_z_light_fog_prim_npc',
        '_texture_z_light_fog_prim_shadow','_texture_z_light_fog_prim_xlu')}}
# Bounds for the actual source table indices and digit/colour callback state.
# Masked Goza indices and owners without dynamic indexing need no extra bound.
BOUNDS={
    'Goza_Profile':'1','Radio_Profile':'1','Mikuji_Profile':'1','Ghog_Profile':'1',
    'Yatai_Profile':'(unsigned)a->arg0<2',
    'Turi_Profile':'(unsigned)a->arg0<2',
    'Kago_Profile':'(unsigned)a->action<2','Tama_Profile':'(unsigned)a->action<2',
    'Htable_Profile':'(unsigned)a->arg0<3',
    'Count_Profile':'(unsigned)a->arg0<3 && (unsigned)a->action<60',
    'Count02_Profile':'(unsigned)a->arg0<=3600 && (unsigned)a->arg1<=3600 && '
        '(unsigned)a->arg2<16 && a->arg1_f>=0.0f && a->arg1_f<=8.0f'}


def resources(source,art):
    data=bytearray();symbols={};wrappers={};rigs={};palettes={}
    def put(name,raw):
        data.extend(bytes(-len(data)%8));address=TABLE+len(data)
        if name in symbols:raise ValueError('Duplicate decoration symbol: '+name)
        symbols[name]=address;data.extend(raw);return address
    # Reserve the fixed directory, populated after the complete batch links.
    put('af_decor_records',bytes(18*24))
    for obj in art['objects']:
        base=ART+obj['packet_offset']
        for model in obj['models']:
            at=base+model['native_offset']
            wrapper=put('af_decor_list_'+obj['key'].replace('-','_')+'_'+model['layer'],
                struct.pack('>6I',0xDB060018,base&0x1FFFFFFF,0xDE000000,at,0xDF000000,0))
            # Separate lists can use different segment-six objects inside one
            # source draw. Each wrapper restores its own complete object.
            roots=[r for r in obj['consumers'] if not obj['rig']]
            for consumer in roots:
                name=consumer['model']
                if name in wrappers and wrappers[name]!=wrapper:
                    raise ValueError('Seasonal model requires an explicit runtime selector: '+name)
                wrappers[name]=wrapper
        for consumer in obj['consumers']:
            if obj['rig']:
                rig=obj['rig'];header=rig['skeleton']['header'];motion=rig['animations']['headers']
                if len(motion)!=1:raise ValueError('Ambiguous complete actor rig motion')
                binding=dict(base=base,skeleton=base+header['native_offset'],animation=base+motion[0]['native_offset'])
                if consumer['owner'] in rigs and rigs[consumer['owner']]!=binding:
                    raise ValueError('Ambiguous complete actor rig')
                rigs[consumer['owner']]=binding
            for address,offset in obj['draw_context'].get('palette_bindings',{}).items():
                del address
                found=[r for r in obj['resources'] if r['kind']=='palette' and r['donor_offset']==offset]
                if len(found)!=1:raise ValueError('Missing converted caller palette')
                key=consumer['palette_index'];p=base+found[0]['native_offset']
                # Identical duplicated palette bytes are interchangeable.
                palettes.setdefault(key,p)
        for row in obj['resources']:
            if any(row['symbol']==f['symbol'] for o in art['owners'].values() for f in o['texture_frames']):
                if row['symbol'] in symbols and symbols[row['symbol']]!=base+row['native_offset']:
                    raise ValueError('Ambiguous complete texture bank')
                symbols[row['symbol']]=base+row['native_offset']
    symbols.update(wrappers)
    shadow_rows=[]
    for owner in art['owners'].values():
        for shadow in owner['shadows']:
            matches=[o for o in art['objects'] if any(c['model']==shadow['model'] for c in o['consumers'])]
            if len(matches)!=1:raise ValueError('Ambiguous converted shadow object')
            obj=matches[0]
            v=next(r for r in obj['resources'] if r['symbol']==shadow['vertices']['symbol'])
            flag=next(r for r in art['projection_flags'] if r['symbol']==shadow['flags']['symbol'])
            vertex=ART+obj['packet_offset']+v['native_offset'];flags=ART+flag['packet_offset']
            name=shadow['descriptor']['symbol']
            put(name,struct.pack('>IIfII',shadow['projection_count'],flags,shadow['height'],vertex,symbols[shadow['model']]))
            shadow_rows.append(dict(symbol=name,address=symbols[name],count=shadow['projection_count'],
                vertices=vertex,flags=flags,model=symbols[shadow['model']]))
    if TABLE+len(data)>ART:raise ValueError('Decoration descriptors exceed reservation')
    return data,symbols,rigs,palettes,shadow_rows


def draw_sources(source,art,directory,symbols,palettes):
    if set(BOUNDS)!=set(art['owners']):raise ValueError('Unreviewed source draw-state indices')
    header='#include "/source/overlays/v3/decoration_draw.h"\n'
    # Only unused donor parameters/locals are suppressed; type errors, missing
    # declarations, and all native-adapter warnings remain fatal.
    diagnostic='\n'.join('#pragma GCC diagnostic ignored "-W'+w+'"' for w in
        ('unused-parameter','unused-variable','unused-but-set-variable'))+'\n'
    enums=(ROOT/'local/ac-decomp/include/ac_structure.h').read_text()
    palette_enum=re.search(r'enum structure_palette\s*\{.*?\};',enums,re.S).group()
    files=[];receipts=[]
    for index,(owner,record) in enumerate(art['owners'].items()):
        root=next(p for p in record['references'] if p.endswith('.c'))
        text,refs=source_bundle(ROOT/'local/ac-decomp'/root)
        name=record['callbacks']['28']['symbol'];draw=function(text,name)
        parts=[]
        for helper in sorted(set(re.findall(r'\ba\w+\b',draw))-{name}):
            if re.search(r'(?:static|extern)\s+[^;{}]*?\b'+helper+r'\s*\([^;{}]*\)\s*\{',text):
                parts.append(function(text,helper))
        body='\n'.join(parts+[draw])
        constructor=function(text,record['callbacks']['16']['symbol'])
        collisions=re.findall(r'\b(\w+_set_bgOffset)\(([^;]+)\);',constructor)
        if len(collisions)>1:raise ValueError('Ambiguous source collision initializer')
        collision_entry=None;collision_receipt=None
        if collisions:
            collision_name,args=collisions[0]
            collision=function(text,collision_name)
            collision_receipt=sha256(collision.encode())
            # The donor leaves pos.y indeterminate in several X/Z-only calls.
            # Initialize it without changing any coordinate the code supplies.
            collision=collision.replace('xyz_t pos;','xyz_t pos = {0};')
            collision=re.sub(r'\b(?:static\s+)?(?:const\s+)?mCoBG_OffsetTable_c',
                lambda m:('static ' if m[0].startswith('static') else '')+'const mCoBG_OffsetTable_c',collision)
            collision=re.sub(r'(static const mCoBG_OffsetTable_c\s*\*)',r'\1 const ',collision)
            collision=re.sub(r'static\s+(f32|float)\s+',r'static const \1 ',collision)
            argv=args.split(',');argv[0]='(void*)actor'
            if len(argv)>1:
                argv[1]=re.sub(r'\b\w+->(?:structure_class\.)?',r'((STRUCTURE_ACTOR*)actor)->',argv[1])
            collision_entry=f'af_decor_owner_collision_{index}'
            body+='\n'+collision+'\n'+f'void {collision_entry}(ACTOR *actor) {{ {collision_name}('+','.join(argv)+'); }\n'
        needed=set(re.findall(r'\b\w+\b',body))
        declarations=[]
        for s in record['shadows']:
            declarations.append('extern bIT_ShadowData_c '+s['descriptor']['symbol']+';')
        declarations += ['extern Gfx '+s+'[];' for s in record['models'] if s in symbols]
        declarations += ['extern u8 '+s['symbol']+'[];' for s in record['texture_frames']]
        # Complete file-scope draw/shadow directories, including Harvest's
        # three variants. Local directories remain inside their source function.
        for match in re.finditer(r'static\s+(?:Gfx|bIT_ShadowData_c)\s*\*\s*(\w+)\s*\[[^]]*\]\s*=\s*\{[^;]*\};',text):
            if match[1] in needed and match.group() not in body:
                declarations.append(match.group())
        # These source tables are read-only. Keep them in the loaded image,
        # not compiler-emitted writable data omitted by the packet loader.
        combined='\n'.join(declarations)+'\n'+body
        combined=re.sub(r'static\s+((?:Gfx|bIT_ShadowData_c|u8)\s*\*)',r'static \1 const ',combined)
        combined=re.sub(r'static\s+(rgba_t|float)\s+',r'static const \1 ',combined)
        combined=combined.replace('rgba_t* color;','const rgba_t* color;')
        # The negative signed shift in the donor digit callback is harmless
        # for its admitted 0..8 phase, but keep the source expression intact.
        entry=f'af_decor_owner_draw_{index}'
        generated=header+diagnostic+palette_enum+'\n'+combined+'\n'
        generated+=f'void {entry}(ACTOR *actor,GAME *game) {{ {name}(actor,game); }}\n'
        file=directory/f'owner-{index:02}.c';write_new(file,generated.encode());files.append(str(file.relative_to(ROOT)))
        receipts.append(dict(owner=owner,entry=entry,source_callback=record['callbacks']['28'],
            source_functions=[sha256(p.encode()) for p in parts+[draw]],references=refs,
            collision_entry=collision_entry,collision_source_sha256=collision_receipt,
            generated_sha256=sha256(generated.encode())))
    text=header+'u16 *af_decor_palette(int index) { switch(index) {\n'
    for index,p in sorted(palettes.items()):text+=f'case {index}:return (u16*)0x{p:X}u;\n'
    text+='default:return (u16*)0; }}\n'
    text+='int af_decor_valid(const STRUCTURE_ACTOR *a,u16 owner) { switch(owner) {\n'
    for i,owner in enumerate(art['owners']):text+=f'case {i}:return {BOUNDS[owner]};\n'
    text+='default:return 0; }}\n'
    file=directory/'palettes.c';write_new(file,text.encode());files.append(str(file.relative_to(ROOT)))
    return files,receipts


def native_bindings(base):
    path=ROOT/'upstream/af/linker_scripts/jp/symbol_addrs_code.txt'
    source=path.read_text();addresses={n:int(a,16) for n,a in re.findall(r'^(\w+) = (0x[0-9A-Fa-f]+);',source,re.M)}
    functions=sorted(int(a,16) for a in re.findall(r'^\w+ = (0x[0-9A-Fa-f]+); // type:func',source,re.M))
    core=by_vrom(base)[CODE_VROM].extract(base);bindings={};checks=[]
    for name,original in NATIVE.items():
        start=addresses[original];end=next(a for a in functions if a>start)
        body=core[start-CODE_RAM:end-CODE_RAM]
        if not body or len(body)!=end-start:raise ValueError('Missing native drawing function')
        bindings[name]=start;checks.append(dict(symbol=original,start=start,end=end,sha256=sha256(body)))
    from v3_holiday_transition import MEMORY_NATIVE
    for name,vrom,ram,at,size,digest in MEMORY_NATIVE:
        if name!='memcpy':continue
        data=by_vrom(base)[vrom].extract(base)
        if sha256(data[at-ram:at-ram+size])!=digest:raise ValueError('Changed native shadow copy helper')
        bindings[name]=at
    bindings.update(native_decor_writeback=0x8002FE00,af_decor_segments=addresses['SegmentBaseAddress'])
    return bindings,checks


def install(base,prior,output):
    from v3_console_disk_install import reservations
    from v3_furniture_capacity import checked
    from v3_holiday_state import RAM as STATE_RAM,GUARD
    import v3_physical_resources as physical
    e=copy.deepcopy(prior['equipment_resources']);events=e['npc_extra']['events'];s=e['holiday_state']
    decorations=events['decorations']
    if decorations.get('renderer') or not decorations['resources_installed']:
        raise ValueError('Decoration drawing requires the complete prepared batch, once')
    checked(base,prior)
    if END>0x807DA800 or any(a<END and RAM<b for a,b in reservations(prior)):
        raise ValueError('Decoration runtime overlaps retained reserved RAM')
    old=s['packet'];prefix=base[old['physical']:old['physical']+old['bytes']]
    if old['ram']!=STATE_RAM or STATE_RAM+len(prefix)!=RAM or sha256(prefix)!=old['sha256'] or prefix[-16:]!=GUARD:
        raise ValueError('Changed complete holiday packet')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    artwork,art=prepared_packet(source,PREPARED)
    p=decorations['packet']
    if artwork!=base[p['physical']:p['physical']+p['bytes']] or sha256(artwork)!=p['sha256']:
        raise ValueError('Prepared artwork differs from installed complete resource')
    directory=output/'decoration-draw';directory.mkdir(parents=True)
    table,link,rigs,palettes,shadows=resources(source,art)
    files,owners=draw_sources(source,art,directory,link,palettes)
    bindings,native=native_bindings(base);link.update(bindings)
    try:
        code,compiled=compile_part('decoration_draw',directory/'code',extra_sources=files,link_symbols=link)
    except __import__('subprocess').CalledProcessError as error:
        raise ValueError(error.stderr) from error
    by_owner={r['owner']:(i,r) for i,r in enumerate(owners)}
    rows=[]
    for i,b in enumerate(art['bindings']):
        owner,r=by_owner[b['owner']];rig=rigs.get(b['owner'],{})
        values=(b['source_name'],owner,rig.get('base',0),rig.get('skeleton',0),
            rig.get('animation',0),compiled['symbols'][r['entry']],
            compiled['symbols'][r['collision_entry']] if r['collision_entry'] else 0)
        struct.pack_into('>HH5I',table,i*24,*values)
        rows.append(dict(b,rig=rig,draw=values[-2],collision=values[-1]))
    raw=bytearray(prefix)+bytearray(END-RAM)
    for address,data in ((RAM,code),(TABLE,table),(ART,artwork)):
        raw[address-STATE_RAM:address-STATE_RAM+len(data)]=data
    raw[-16:]=GUARD
    records=copy.deepcopy(prior['physical_resources'])
    new=physical.allocate(base,records,raw,'holiday-decoration-runtime-GAFE01-r0');records.append(new)
    s['packet']=dict(new,ram=STATE_RAM,crc32=zlib.crc32(raw),storage='physical-ROM',guard=GUARD.hex())
    report=dict(installed=True,actors_installed=False,native_execution_verified=False,
        code=compiled,owners=owners,bindings=rows,shadows=shadows,native_functions=native,
        original_packet=old,preserved_prefix_bytes=len(prefix),preserved_prefix_sha256=sha256(prefix),
        packet_ram=STATE_RAM,packet_bytes=len(raw),additional_resident_bytes=END-RAM,
        loaded_code=dict(ram=RAM,bytes=len(code),sha256=sha256(code)),
        tables=dict(ram=TABLE,bytes=len(table),sha256=sha256(table)),
        artwork=dict(ram=ART,bytes=len(artwork),sha256=sha256(artwork)),
        sources={p:sha256((ROOT/p).read_bytes()) for p in SOURCES},
        pending=['native owner setup/allocation, collision/movement/interactions and activation',
            'native execution of the connected event actors'])
    decorations['renderer']=report;decorations['additional_resident_bytes']=END-RAM
    e['npc_extra']['sources'].update(report['sources'])
    write_new(directory/'installed.json',(json.dumps(report,indent=2)+'\n').encode())
    write_new(directory/'state-packet.bin',raw)
    return e,{},dict(physical_resources=records),[(new,bytes(raw))]
