"""Discover complete scrolling materials, retaining their actual draw contracts.

This resource category preserves both texture layers and callback parameters.
It does not enable an item before its renderer, lifecycle, and acquisition exist.
"""
import struct
import copy
import json
import zlib

from aflib import sha256, u32

CATEGORY = 'scrolling-material-assets'
RAM,TABLE,BYTES,CAPACITY,VTABLE = 0x804BA000,0x804BB000,8192,64,0x804B1E30
MAGIC = 0x41464332
LIFE_TABLE,LIFE_MAGIC,LIFE_CAPACITY=0x804BBC10,0x41464C31,64
# Complete normalized draw code, paired model relocations in submission order,
# scroll helper call, matrix calls, external save/restore addresses, and runtime
# parameters. These are implementation shapes, never item or artwork selectors.
FORMS = (
    (312, '6a7833d36916c82e04bafa71caa37ae6010b0d7568719b0c0baac1fef905529f',
     ((0x96,0xBA),(0x9A,0xBE),(0xA2,0xC2),(0xA6,0xCA)), 0x3C, (0x64,0x88),
     0x8009AED0, 9, ((16,16),(0,0)), ((3,0),(0,0)), None),
    (272, '27674442623f3994b732d39f1dda4f2bc0cb84e85c31e4011cb0eae364ab655f',
     ((0xA6,0xBA),(0xAA,0xC2)), 0x48, (0x74,0x98),
     0x8009AED0, 9, ((32,32),(32,64)), ((0,0),(0,-4)), None),
    (356, '48dffe770a97956ac9521a3af58362742514841dea26ee90653b7cc73546b312',
     ((0xD2,0xF2),(0xE6,0x10A)), 0x4C, (0xA4,0xC8),
     0x8009AECC, 8, ((16,16),(16,16)), ((0,0),(0,-10)),
     dict(command='environment',rgb=(0,180,255),field='alpha',room_f32_offset=0x834,preview=100)),
    (372, '5427835eb262741edb287b3e2ab0bac2712cb7fc98cd297f29ec78e528a1b5c7',
     ((0xCA,0xEA),(0xCE,0xF2),(0xDE,0x106)), 0x44, (0x9C,0xC0),
     0x8009AECC, 8, ((8,8),(8,8)), ((-1,4),(1,4)),
     dict(command='primitive',rgba=(255,255,255,127),field='lod_fraction',room_f32_offset=0x834,preview=156)),
    (356, '6b74309561d2d32894a5bb2d0a2c43afd0454c57039bbb52d92837dc2c440b69',
     ((0xCE,0xF6),(0xE6,0x10A)), 0x48, (0xA0,0xC4),
     0x8009AECC, 9, ((32,32),(32,32)), ((0,6),(0,0)),
     dict(command='primitive',rgb=(120,160,255),lod_fraction=255,field='alpha',room_f32_offset=0x834,preview=255)),
)

# Complete dimension wrappers around the shared source scroll generator.
WRAPPERS = {
    ((16,16),(0,0)): (84,'fe33f75e74233bd0f46dc7bc3c51d0b4ea227db2c37146257d6d4fedac999279',0x40),
    ((32,32),(32,64)): (84,'2682e7f5f1755916c666209efb4544cd130fb1a8802a250151da8c02c14dbdc9',0x40),
    ((16,16),(16,16)): (80,'392d5583a36a6f59214dcb4c9e02d22fee54f805ae70505b99b55bc5d67cdc03',0x3C),
    ((8,8),(8,8)): (80,'2bd9877cb044f5fe6fc0cd8f1e3d84804f98c2fc01e4345c7edf92f4bdcc299d',0x3C),
    ((32,32),(32,32)): (80,'4143e78e3cc0b2584100976c31cfa54b503389a191dcecf86228e15d4e03ad68',0x3C),
}


def checked_generator(source, receipt):
    source.checked_callback_code(receipt,204,
        '595b86c4d52240deb412e1eb8e36370b1445e77e805782439314800eb132011e',
        {0x10:(10,0,4,0x8009AED0),0xB8:(10,0,4,0x8009AF1C)}, {}, 'shared scroll generator',
        internal_branches=True)


def evw_scroll(source, target, setter):
    """Decode complete EVW two-tile tables, including signed rates and terminator.

    Colour/texture-animation variants need their own complete implementations;
    none can be interpreted as a scrolling row or silently omitted.
    """
    from v3_furniture_pipeline import ReviewRequired
    def reject(reason): raise ReviewRequired('EVW scrolling: '+reason)
    module=u32(source.rel,0)
    expected={0x10:(10,0,4,0x8009AED0),0x78:(10,0,4,0x8009AF1C),
              0x2E:(6,module,5,0x80),0x32:(4,module,5,0x80)}
    source.checked_callback_code(setter,140,
        '96f668c610ec8c66b1c8e0e2048472b67b039a03634fbe16bd846c747956c22b',
        expected,{},'EVW table dispatcher',internal_branches=True)
    symbol,at,n=source.containing(0x80,exact=True)
    dispatch={p-at:r for p,r in source.relocations.items() if at<=p<at+n}
    targets=(10800,11068,11400,11548,12364,13084)
    if n!=24 or source.data[at:at+n]!=bytes(n) or dispatch!={i*4:(1,True,1,t) for i,t in enumerate(targets)}:
        reject('changed complete handler table')
    helpers={setter['symbol']:setter}
    _,handler=source.function(targets[1]);helpers[handler['symbol']]=handler
    helpers.update(source.checked_callback_code(handler,132,
        '2f929583442982283e82f98fc931e885db5f755a8b894472d9da958630ee22e6',{},
        {0x20:(0x2AB4,'evw_two_tex_scroll_set')},'EVW two-tile binding'))
    helper=helpers['evw_two_tex_scroll_set']
    helpers.update(source.checked_callback_code(helper,136,
        'a1211cc4c3f8d6217e831006d29369a99ac4049a02494dddf7345ac981830196',{},
        {0x74:(0x75400,'two_tex_scroll_dolphin')},'EVW two-tile rates'))
    checked_generator(source,helpers['two_tex_scroll_dolphin'])
    table_name,start,n=source.containing(target,exact=True);raw=source.data[start:start+n]
    if not n or n%8 or n>64:reject('incomplete animation table')
    expected_data={};rows=[];segments=set()
    for p in range(0,n,8):
        segment,pad,kind,pointer=struct.unpack_from('>bBhI',raw,p)
        if (not 1<=abs(segment)<=8 or pad or kind!=1 or pointer or
                (segment<0)!=(p==n-8) or abs(segment) in segments):
            reject('unsupported type, segment, or termination')
        segments.add(abs(segment))
        ref=source.relocations.get(start+p+4)
        if ref is None or ref[:3]!=(1,True,5):reject('missing scroll data')
        expected_data[start+p+4]=ref
        name,at,size=source.containing(ref[3],exact=True);data=source.data[at:at+size]
        if size!=8 or source.pointers(at,size):reject('incomplete two-tile data')
        tiles=[]
        for i,(x,y,w,h) in enumerate(struct.iter_unpack('>bbBB',data)):
            if any(v<8 or v>64 or v&(v-1) for v in (w,h)):reject('unsupported complete tile dimensions')
            tiles.append(dict(index=i,width=w,height=h,rate=[x,-y]))
        rows.append(dict(segment_address=(7+abs(segment))<<24,input='play-frame',tiles=tiles,
            data=dict(symbol=name,donor_offset=at,bytes=size,source_sha256=sha256(data))))
    if {p:r for p,r in source.relocations.items() if start<=p<start+n}!=expected_data:
        reject('unaccounted animation relocations')
    return dict(symbol=table_name,donor_offset=start,bytes=n,source_sha256=sha256(raw),rows=rows,
        dispatch=dict(symbol=symbol,donor_offset=0x80,bytes=24,targets=list(targets))),helpers


EXTENDED_FORMS={
    (468,'4bbcf5a499849b0d06544ff62a78e065da22b0b131213ca4229ab945d7337665'):'evw-colour-sequence',
    (344,'6b546b76476693bdbaab15e19182f038e0f7b79a39894fffbfef582cdab21627'):'parameter-scroll-state-alpha',
}


def discover_extended(source,name,at,functions,digest):
    from v3_furniture_pipeline import ReviewRequired
    draw=functions['draw'];kind=EXTENDED_FORMS.get((draw['bytes'],digest))
    if kind is None:return None
    module=u32(source.rel,0);models={}
    def pair(hi,lo,section=5):
        ref=draw['relocations'].get(hi)
        if ref is None or ref[:3]!=(6,module,section):
            raise ReviewRequired('scrolling materials: missing paired source binding')
        expected.update({hi:ref,lo:(4,module,section,ref[3])})
        return ref[3]
    if kind=='evw-colour-sequence':
        expected={0x10:(10,0,4,0x8009AED4),0x1C0:(10,0,4,0x8009AF20)}
        pairs=((0xA6,0xBE),(0x186,0x196),(0x18A,0x19E))
        for i,(hi,lo) in enumerate(pairs):models[f'part{i}']=source.containing(pair(hi,lo),exact=True)
        table=pair(0xAE,0xB6);debug=pair(0xAA,0xC6,6)
        if debug!=0x39840:raise ReviewRequired('scrolling materials: changed debug-register owner')
        helpers=source.checked_callback_code(draw,468,digest,expected,
            {0x4C:(0x2CE81C,'fSKP_GetTwoTileGfx'),0x78:(0x9D214,'_Matrix_to_Mtx_new'),
             0x9C:(0x9D214,'_Matrix_to_Mtx_new'),0x17C:(0x339C,'Evw_Anime_Set')},
            'EVW colour sequence',internal_branches=True)
        wrapper=helpers['fSKP_GetTwoTileGfx'];wn,wh,wcall=WRAPPERS[((16,16),(16,16))]
        helpers.update(source.checked_callback_code(wrapper,wn,wh,{},
            {wcall:(0x75400,'two_tex_scroll_dolphin')},'unused allocation guard'))
        evw,dependencies=evw_scroll(source,table,helpers['Evw_Anime_Set']);helpers.update(dependencies)
        if len(evw['rows'])!=1:raise ReviewRequired('scrolling materials: draw needs exactly one EVW binding')
        scrolling=dict(evw['rows'][0],model='part1',colour=None,evw=evw,
            source_coordinate_shift=1,allocation_failure='skip-draw',
            unused_scroll_allocation=dict(dimensions=[[16,16],[16,16]],rates=[[1,0],[0,2]],
                                          input='room-or-preview-frame'),
            draw_features=['multiple-translucent-models','debug-register-colours','play-frame-preview'],
            colours=[dict(command='primitive',before_model='part1',minimum_level=0,
                          fields=['lod_fraction','r','g','b','a'],base=[160,55,255,255,200],
                          debug_indices=[47,48,49,50,51]),
                     dict(command='environment',before_model='part1',fields=['r','g','b','a'],
                          base=[0,155,205,255],debug_indices=[52,53,54,55])],
            debug_owner=dict(section=6,offset=debug,kind='pointer-to-debug-mode',register_bank='CRV'))
        arenas=['opaque','translucent','translucent']
    else:
        expected={0x10:(10,0,4,0x8009AECC),0x144:(10,0,4,0x8009AF18)}
        for i,(hi,lo) in enumerate(((0x9A,0xAA),(0xF2,0x10E))):
            models[f'part{i}']=source.containing(pair(hi,lo),exact=True)
        constant=pair(0x16,0x26,4);section,size=source.sections[4]
        if (constant&3 or constant+4>size or source.rel[section+constant:section+constant+4]!=struct.pack('>f',255.0)
                or any((4,p) in source.section_relocations for p in range(constant,constant+4))):
            raise ReviewRequired('scrolling materials: changed alpha multiplier')
        helpers=source.checked_callback_code(draw,344,digest,expected,
            {0x64:(0x2BE944,'fFTR_GetTwoTileGfx'),0x90:(0x9D214,'_Matrix_to_Mtx_new'),
             0xD4:(0x9D214,'_Matrix_to_Mtx_new')},'parameter scrolling and state alpha',internal_branches=True)
        helper=helpers['fFTR_GetTwoTileGfx']
        helpers.update(source.checked_callback_code(helper,160,
            '1526a19c4fb00f3f24e833c6139daeb9a116eee0a93562185db011535577f526',{},
            {0x84:(0x75400,'two_tex_scroll_dolphin')},'shared parameter scrolling',internal_branches=True))
        checked_generator(source,helpers['two_tex_scroll_dolphin'])
        scrolling=dict(segment_address=0x08000000,model='part1',input='room-or-preview-frame',
            tiles=[dict(index=i,width=16,height=16,rate=rate) for i,rate in enumerate(([0,0],[0,-10]))],
            source_coordinate_shift=1,allocation_failure='skip-draw',source_frame_offset=0,
            draw_features=['scaled-state-alpha','state-alpha-preview'],
            colour=dict(command='primitive',rgb=[120,255,180],lod_fraction=255,field='alpha',
                        room_f32_offset=0x834,preview='actor-state',multiplier=255.0,
                        multiplier_source=dict(section=4,offset=constant,bytes=4,source_hex='437f0000')))
        arenas=['opaque','translucent']
    labels=list(models)
    return models,{},dict(category=CATEGORY,vtable_symbol=name,vtable_offset=at,
        functions=functions,helpers=helpers,scrolling=scrolling,model_order=labels,
        model_arenas=dict(zip(labels,arenas)),runtime_installed=False,pending_callbacks=list(functions),
        resource_scope='complete opaque/translucent models and scrolling layers; runtime and lifecycle pending')


def discover(source, name, at, functions):
    from v3_furniture_pipeline import ReviewRequired
    draw = functions['draw']; raw, _ = source.function(draw['offset'])
    forms = [form for form in FORMS if form[0] == len(raw)]
    if not forms and len(raw) not in {r[0] for r in EXTENDED_FORMS}: return None
    normalized = bytearray(raw)
    for loc, (kind, _, _, _) in draw['relocations'].items():
        if kind in (4,6): normalized[loc:loc+2] = bytes(2)
        elif kind == 10: struct.pack_into('>I',normalized,loc,u32(raw,loc)&0xFC000003)
        else: return None
    for loc in range(0,len(raw),4):
        word = u32(raw,loc)
        if word&0xFC000003 == 0x48000001:
            struct.pack_into('>I',normalized,loc,word&0xFC000003)
    form = next((r for r in forms if sha256(normalized) == r[1]),None)
    if form is None: return discover_extended(source,name,at,functions,sha256(normalized))
    size,digest,pairs,call,matrices,save,segment,dimensions,rates,colour = form
    module = u32(source.rel,0); models = {}
    expected = {0x10:(10,0,4,save),size-20:(10,0,4,save+0x4C)}
    for i,(hi,lo) in enumerate(pairs):
        pointer = draw['relocations'].get(hi)
        if pointer is None or pointer[:3] != (6,module,5):
            raise ReviewRequired('scrolling materials: missing paired model binding')
        target = pointer[3]
        expected.update({hi:(6,module,5,target),lo:(4,module,5,target)})
        models[f'part{i}'] = source.containing(target,exact=True)
    word = u32(raw,call); displacement = word&0x3FFFFFC
    if displacement&0x2000000: displacement -= 0x4000000
    target = draw['offset']+call+displacement
    _, wrapper = source.function(target)
    wn,wh,wcall = WRAPPERS[dimensions]
    helpers = source.checked_callback_code(wrapper,wn,wh,{},
        {wcall:(0x75400,'two_tex_scroll_dolphin')},'scroll dimension wrapper')
    common = helpers['two_tex_scroll_dolphin']
    checked_generator(source,common)
    calls = {loc:(0x9D214,'_Matrix_to_Mtx_new') for loc in matrices}
    calls[call] = (target,wrapper['symbol'])
    helpers.update(source.checked_callback_code(draw,size,digest,expected,calls,'scrolling materials',internal_branches=True))
    helpers[wrapper['symbol']] = wrapper
    # Only the final model is translucent and consumes the scroll list. The
    # source callback installs colour state immediately before that submission.
    labels = list(models)
    scrolling = dict(segment_address=segment<<24,model=labels[-1],
        input='room-or-preview-frame',tiles=[dict(index=i,width=w,height=h,rate=list(rates[i]))
            for i,(w,h) in enumerate(dimensions)],source_coordinate_shift=1,
        colour=colour,allocation_failure='skip-draw' if size!=312 else 'unchecked-source-allocation')
    return models,{},dict(category=CATEGORY,vtable_symbol=name,vtable_offset=at,
        functions=functions,helpers=helpers,scrolling=scrolling,model_order=labels,
        model_arenas={label:'translucent' if label==labels[-1] else 'opaque' for label in labels},
        runtime_installed=False,pending_callbacks=list(functions),
        resource_scope='complete opaque/translucent models and scrolling layers; runtime and lifecycle pending')


def bindings(adapter):
    """Expose only the complete model-local scroll dependency to the parser."""
    if adapter.get('category') != CATEGORY: return {}
    row = adapter['scrolling']; tiles = row['tiles']
    if (row['segment_address'] not in (0x08000000,0x09000000) or len(tiles)!=2 or
            [r['index'] for r in tiles]!=[0,1] or row['model'] not in adapter['model_order'] or
            adapter['model_arenas'][row['model']]!='translucent'):
        raise ValueError('Invalid complete scroll material binding')
    dimensions = tuple((r['width'],r['height']) for r in tiles)
    if dimensions not in WRAPPERS: raise ValueError('Unsupported complete scrolling dimensions')
    return {row['model']:dict(segment=row['segment_address'],
                             dimensions=[list(shape) for shape in dimensions if shape!=(0,0)])}


def runtime_record(row):
    from v3_registry import furniture_identity
    a=row['profile']['callback_adapter'];binding=bindings(a)
    if not binding:raise ValueError('Missing complete scrolling resource category')
    source=a['scrolling'];colour=source['colour'];mode=word_a=word_b=preview=state=0
    second_a=second_b=debug=0;adaptations=[]
    arenas=[a['model_arenas'][label] for label in a['model_order']];opaque=arenas.count('opaque')
    features=set(source.get('draw_features',[]))
    if features-{'multiple-translucent-models','debug-register-colours','play-frame-preview',
                 'scaled-state-alpha','state-alpha-preview'}:
        raise ValueError('Scrolling draw features need runtime adapters')
    if colour:
        if colour['room_f32_offset']!=0x834:raise ValueError('Changed source colour state')
        mode=2 if colour['field']=='lod_fraction' else 1
        if colour.get('multiplier',1)!=1 or type(colour['preview']) is not int:
            if (colour.get('multiplier')!=255.0 or colour['preview']!='actor-state' or mode!=1 or
                    features!={'scaled-state-alpha','state-alpha-preview'} or source.get('source_frame_offset')!=0):
                raise ValueError('Scrolling state scaling or preview needs a runtime adapter')
            mode=3
        if colour['command']=='environment':word_a=0xFB000000
        elif colour['command']=='primitive':word_a=0xFA000000|colour.get('lod_fraction',0)
        else:raise ValueError('Unknown complete source colour command')
        components=colour['rgba'] if mode==2 else (*colour['rgb'],0)
        word_b=int.from_bytes(bytes(components),'big');preview=0 if mode==3 else colour['preview'];state=0x1A4
    if source.get('colours'):
        prim,env=source['colours'];owner=source['debug_owner']
        if (colour or features!={'multiple-translucent-models','debug-register-colours','play-frame-preview'} or
                owner!=dict(section=6,offset=0x39840,kind='pointer-to-debug-mode',register_bank='CRV') or
                prim['command']!='primitive' or env['command']!='environment' or prim['minimum_level']!=0 or
                prim['fields']!=['lod_fraction','r','g','b','a'] or env['fields']!=['r','g','b','a'] or
                any(c['before_model']!=a['model_order'][opaque] for c in (prim,env)) or
                prim['debug_indices']+env['debug_indices']!=list(range(47,56))):
            raise ValueError('Unsupported complete debug colour sequence')
        mode=4;word_a=0xFA000000|prim['base'][0];word_b=int.from_bytes(bytes(prim['base'][1:]),'big')
        second_a=0xFB000000;second_b=int.from_bytes(bytes(env['base']),'big');debug=0x14+2*(11*96+47)
    if source['input']=='play-frame':
        if mode!=4:raise ValueError('Unmapped play-only scrolling context')
        adaptations.append('Use generic preview frame when no native room owner is supplied; retain play frame in rooms')
    if mode not in (3,4) and features:raise ValueError('Unused scrolling draw features')
    index,item=furniture_identity(int(row['item_id'],16))
    dimensions=[(r['width'],r['height']) for r in source['tiles'] if r['width']]
    rates=[r['rate'] for r in source['tiles'] if r['width']]
    models=[row['model_offsets'][label] for label in a['model_order']]
    if (a['model_order']!=list(row['model_offsets']) or
            not 1<=opaque<len(models) or arenas!=['opaque']*opaque+['translucent']*(len(models)-opaque) or
            source['input'] not in ('room-or-preview-frame','play-frame') or source['source_coordinate_shift']!=1):
        raise ValueError('Changed complete source scroll draw contract')
    result=dict(source_item_id=row['item_id'],item_id=f'{item:04X}',runtime_index=index,
        bytes=row['object_bytes'],sha256=row['object_sha256'],segment=source['segment_address']>>24,
        model_offsets=models,dimensions=dimensions,rates=rates,colour_mode=mode,colour_a=word_a,colour_b=word_b,
        opaque_models=opaque,colour2_a=second_a,colour2_b=second_b,debug_offset=debug,adaptations=adaptations,
        state_offset=state,preview=preview,source=row,renderer_installed=True,lifecycle_installed=False,
        profile_installed=False,parent_selectable=False)
    encode([result]);return result


def encode(rows):
    if not rows or len(rows)>CAPACITY or [r['runtime_index'] for r in rows]!=sorted({r['runtime_index'] for r in rows}):
        raise ValueError('Unordered, duplicate, or excessive scroll records')
    out=bytearray(struct.pack('>4I',MAGIC,len(rows),48,0))
    for r in rows:
        index,n,models,dimensions,rates=r['runtime_index'],r['bytes'],r['model_offsets'],r['dimensions'],r['rates']
        mode,a,b,state,preview=r['colour_mode'],r['colour_a'],r['colour_b'],r['state_offset'],r['preview']
        opaque=r.get('opaque_models',len(models)-1);a2=r.get('colour2_a',0);b2=r.get('colour2_b',0);debug=r.get('debug_offset',0)
        if (not 1024<=index<2048 or not 32<=n<=9216 or n&15 or not 2<=len(models)<=4 or
                any(type(p) is not int or p&7 or not 0<=p<=n-8 for p in models) or
                r['segment'] not in (8,9) or not 1<=len(dimensions)<=2 or len(dimensions)!=len(rates) or
                any(len(d)!=2 or any(type(v) is not int or v<8 or v>64 or v&(v-1) for v in d) for d in dimensions) or
                any(len(d)!=2 or any(type(v) is not int or not -16<=v<=16 for v in d) for d in rates) or
                type(opaque) is not int or not 1<=opaque<len(models) or mode not in (0,1,2,3,4) or
                any(type(v) is not int or not 0<=v<=0xFFFFFFFF for v in (a,b,a2,b2)) or not 0<=preview<=255 or
                mode==0 and (a or b or state or preview) or mode in (1,2,3) and state!=0x1A4 or
                mode in (1,3) and (a!=0xFB000000 and a&0xFFFFFF00!=0xFA000000 or b&255) or
                mode==2 and a!=0xFA000000 or mode==3 and preview or
                mode!=4 and (a2 or b2 or debug) or
                mode==4 and (state or preview or a&0xFFFFFF00!=0xFA000000 or a2!=0xFB000000 or
                             debug&1 or not 0x14<=debug<=0x1C94-18)):
            raise ValueError('Invalid complete scrolling record or native bounds')
        d=[v for pair in dimensions for v in pair]+[0]*(4-len(dimensions)*2)
        rates=[v for pair in rates for v in pair]+[0]*(4-len(rates)*2)
        out.extend(struct.pack('>HH4B4H4B4bIIHBBIIHH',index,n,len(models),r['segment'],len(dimensions),mode,
            *(models+[0]*(4-len(models))),*d,*rates,a,b,state,preview,opaque,a2,b2,debug,0))
    return bytes(out)


def draw_only_lifecycle(profile,source=None):
    """Accept complete empty callbacks only; drawing does not waive gameplay.

    Source-bound callers re-read each function. The native profile writer also
    checks the receipt, so merely supplying a vtable/readiness flag is insufficient.
    """
    adapter=profile.get('callback_adapter',{})
    if (adapter.get('category')!=CATEGORY or adapter.get('pending_profile_fields') or
            profile['contact_action'] or profile['interaction_flags'] or adapter['scrolling']['colour']):
        return None
    functions=adapter['functions'];callbacks={}
    if 'draw' not in functions or set(functions)-{'create','move','draw','destroy'}:return None
    empty=bytes.fromhex('4e800020')
    for role,receipt in functions.items():
        if role=='draw':continue
        if receipt['bytes']!=4 or receipt['sha256']!=sha256(empty) or receipt['relocations']:return None
        if source is not None:
            raw,actual=source.function(receipt['offset'])
            if raw!=empty or any(receipt[k]!=v for k,v in actual.items()):
                raise ValueError('Changed source empty furniture lifecycle')
        callbacks[role]=receipt
    return dict(category='draw-only-scrolling',callbacks=callbacks,actor_state_used=False)


def lifecycle_record(row,contract):
    """Pack only completely implemented source lifecycle shapes."""
    from v3_furniture_contact import CATEGORY as CONTACT,lifecycle_record as contact_record
    if contract['category']==CONTACT:return contact_record(row,contract)
    fade=contract['category']=='switch-fade-loop'
    if contract['category'] not in ('positioned-loop','switch-fade-loop'):
        raise ValueError('Unsupported scrolling lifecycle category')
    parameters=contract['constants'];maximum=parameters['maximum']['value'] if fade else 0
    step=parameters['step']['value'] if fade else 0
    if int(maximum)!=maximum or int(step)!=step:raise ValueError('Unrepresentable exact fade constants')
    on,off=contract['switch_clicks'] or (0,0)
    return dict(source_item_id=row['source_item_id'],runtime_index=row['runtime_index'],mode=2 if fade else 1,
        flags=int(contract['persist_private_switch']),sound=contract['source_sound_id'],on=on,off=off,
        maximum=int(maximum),step=int(step),source=contract)


def encode_lifecycles(rows):
    if (len(rows)>LIFE_CAPACITY or
            [r['runtime_index'] for r in rows]!=sorted({r['runtime_index'] for r in rows})):
        raise ValueError('Duplicate or excessive scrolling lifecycles')
    data=bytearray(struct.pack('>4I',LIFE_MAGIC,len(rows),12,0))
    for r in rows:
        index,mode,flags=r['runtime_index'],r['mode'],r['flags']
        sound,on,off,maximum,step=(r[k] for k in ('sound','on','off','maximum','step'))
        if mode==3:
            if (not 1024<=index<2048 or any((flags,sound,maximum,step)) or
                    not 0<=on<128 or not 0<=off<128 or on==off):
                raise ValueError('Invalid complete contact/floor lifecycle record')
            data.extend(struct.pack('>HBBHHHBB',index,mode,flags,sound,on,off,maximum,step))
            continue
        if (not 1024<=index<2048 or mode not in (1,2) or flags not in (0,1) or not 68<=sound<96 or
                bool(on)!=bool(off) or not 0<=on<128 or not 0<=off<128 or
                mode==1 and any((flags,on,off,maximum,step)) or mode==2 and not 0<step<=maximum<=255):
            raise ValueError('Invalid complete scrolling lifecycle record')
        data.extend(struct.pack('>HBBHHHBB',index,mode,flags,sound,on,off,maximum,step))
    return bytes(data)


def tables(runtime):
    drawing=encode(runtime['rows']);life=runtime.get('lifecycle_rows',[])
    if not life:return drawing.ljust(BYTES-(TABLE-RAM),b'\0')
    data=drawing.ljust(LIFE_TABLE-TABLE,b'\0')+encode_lifecycles(life)
    if len(data)>BYTES-(TABLE-RAM):raise ValueError('Scrolling tables exceed their complete reservation')
    return data.ljust(BYTES-(TABLE-RAM),b'\0')


def profile_lifecycle(profile,contract,placement=None):
    """Check the source-bound lifecycle carried into an ordinary profile.

    The binding caller additionally verifies actual source code, installed
    table/dispatch, and complete audio. A readiness annotation alone is not used.
    Start-disabled placement requires the checked native owner adapter.
    """
    if draw_only_lifecycle(profile) is not None:return True
    adapter=profile.get('callback_adapter',{})
    start=profile['interaction_flags']==0x1000
    if start:
        from v3_furniture_behaviours import initial_switch_patch
        if (not placement or placement.get('mask')!=0x1000 or
                placement.get('owner_patch_sha256')!=sha256(initial_switch_patch(placement.get('entry')))):return False
    if (not contract or adapter.get('category')!=CATEGORY or
            adapter.get('pending_profile_fields')!=(['interaction'] if start else []) or profile['contact_action'] or
            profile['interaction_flags'] not in (0,0x1000) or bool(contract.get('start_disabled'))!=start or
            contract.get('category') not in ('positioned-loop','switch-fade-loop')):return False
    functions=json.loads(json.dumps(adapter['functions']));bound=contract.get('functions',{})
    if (set(bound)!=set(functions) or any(bound[role].get(k)!=v
            for role,receipt in functions.items() for k,v in receipt.items())):return False
    record=lifecycle_record(dict(source_item_id='',runtime_index=1024),contract)
    encode_lifecycles([record])
    return True


def checked_lifecycle(source,profile,binding,runtime,contracts):
    empty=draw_only_lifecycle(profile,source)
    contract=empty or contracts.get(binding['source_item_id'])
    if (contract is None or not binding.get('lifecycle_installed') or
            binding.get('lifecycle')!=json.loads(json.dumps(contract))):
        return None
    if empty is None:
        expected=json.loads(json.dumps(lifecycle_record(binding,contract)))
        matches=[r for r in runtime.get('lifecycle_rows',[]) if r['source_item_id']==binding['source_item_id']]
        if matches!=[expected]:raise ValueError('Changed installed scrolling lifecycle source binding')
    return json.loads(json.dumps(contract))


def checked_runtime(equipment,blob):
    """Verify complete scrolling drawing/storage before binding ordinary profiles."""
    from v3_asset_loader import BLOB
    from v3_equipment_runtime import RAM as EQUIPMENT_RAM
    runtime=equipment['room_rigs'].get('scrolling')
    if runtime is None:return {}
    if runtime['format']=='AFV3-ROOM-SCROLL-1':
        # The earlier renderer has no ordinary lifecycle/profile support.
        # Leave unrelated staged categories usable while requiring an upgrade
        # before any scrolling record can acquire an ordinary profile.
        if any(r.get(k) for r in runtime['rows'] for k in
               ('lifecycle_installed','profile_installed','parent_selectable')):
            raise ValueError('Legacy scrolling renderer cannot expose ordinary profiles')
        return {}
    packet=runtime['packet'];at=packet['blob_offset'];data=blob[at:at+BYTES]
    module=blob[equipment['blob_offset']:equipment['blob_offset']+equipment['bytes']]
    code=runtime['code'];n=code['bytes'];table=tables(runtime)
    symbols=equipment['room_rigs']['bootstrap']['symbols']
    lifecycle=bool(runtime.get('lifecycle_rows'))
    entries=[symbols['af_v3_room_boot_scroll_'+role] if role=='dw' or lifecycle else 0 for role in ('ct','mv','dw','dt')]
    vtable=struct.pack('>5I',*entries,0)
    if (runtime['format']!=('AFV3-ROOM-SCROLL-3' if lifecycle else 'AFV3-ROOM-SCROLL-2') or packet['ram']!=RAM or packet['bytes']!=BYTES or
            packet['vrom']!=BLOB+at or at&15 or len(data)!=BYTES or sha256(data)!=packet['sha256'] or
            not 0<n<=TABLE-RAM or sha256(data[:n])!=code['sha256'] or any(data[n:TABLE-RAM]) or
            data[TABLE-RAM:]!=table or
            module[VTABLE-EQUIPMENT_RAM:VTABLE-EQUIPMENT_RAM+20]!=vtable or
            runtime['vtable_hex']!=vtable.hex()):
        raise ValueError('Changed complete scrolling renderer, table, or dispatch')
    rows={}
    for r in runtime['rows']:
        start=r['blob_offset'];n=r['bytes'];key=r['source_item_id']
        if (key in rows or r['vrom']!=BLOB+start or start&15 or not 0<=start<start+n<=len(blob) or
                sha256(blob[start:start+n])!=r['sha256'] or not r['renderer_installed']):
            raise ValueError('Changed complete installed scrolling artwork')
        rows[key]=r
    if lifecycle:
        if (runtime.get('lifecycle_table')!=LIFE_TABLE or
                runtime.get('lifecycle_table_sha256')!=sha256(encode_lifecycles(runtime['lifecycle_rows']))):
            raise ValueError('Changed scrolling lifecycle table receipt')
        for r in runtime['lifecycle_rows']:
            parent=rows.get(r['source_item_id'])
            if (not parent or not parent.get('lifecycle_installed') or
                    r!=json.loads(json.dumps(lifecycle_record(parent,parent['lifecycle'])))):
                raise ValueError('Changed installed scrolling lifecycle source binding')
    return rows


def publish(equipment,blob,output):
    """Publish a bounded extension; existing rig/material tables stay put."""
    from v3_asset_loader import BLOB,compile_part
    runtime=equipment['room_rigs']['scrolling'];packet=runtime['packet'];at=packet['blob_offset']
    if (packet['ram']!=RAM or packet['bytes']!=BYTES or packet['vrom']!=BLOB+at or
            at&15 or at+BYTES>len(blob) or
            ('sha256' in packet and sha256(blob[at:at+BYTES])!=packet['sha256'])):
        raise ValueError('Changed complete scroll packet storage')
    lifecycle=bool(runtime.get('lifecycle_rows'))
    defines=('AF_V3_ROOM_SCROLL_LIFECYCLE=1',) if lifecycle else ()
    if any(r['mode']==3 for r in runtime.get('lifecycle_rows',[])):defines+=('AF_V3_ROOM_CONTACT=1',)
    code,compiled=compile_part('room_scroll',output/'room_scroll',defines=defines)
    table=tables(runtime);data=code.ljust(TABLE-RAM,b'\0')+table
    entry=compiled['symbols']['af_v3_room_scroll_dw']
    if len(code)>TABLE-RAM or len(data)!=BYTES or entry!=RAM or not zlib.crc32(data):
        raise ValueError('Scroll code/records exceed reservation')
    blob[at:at+BYTES]=data;packet.update(sha256=sha256(data),crc32=zlib.crc32(data))
    runtime.update(format='AFV3-ROOM-SCROLL-3' if lifecycle else 'AFV3-ROOM-SCROLL-2',code=compiled,
        table_sha256=sha256(encode(runtime['rows'])),capacity=CAPACITY,table_ram=TABLE)
    extra=()
    if lifecycle:
        runtime.update(lifecycle_table=LIFE_TABLE,lifecycle_table_sha256=sha256(encode_lifecycles(runtime['lifecycle_rows'])))
        extra=tuple(f'AF_ROOM_SCROLL_{role.upper()}=0x{compiled["symbols"]["af_v3_room_scroll_"+role]:X}u' for role in ('ct','mv','dt'))
    return (f'AF_ROOM_SCROLL_DW=0x{entry:X}u',f'AF_ROOM_SCROLL_VROM=0x{BLOB+at:X}u',
            f'AF_ROOM_SCROLL_BYTES={BYTES}u',f'AF_ROOM_SCROLL_CRC=0x{zlib.crc32(data):X}u',*extra)


def install(base,prior,blob,core,original,output,directories):
    from aflib import by_vrom,CODE_VROM,CODE_RAM
    from v3_asset_loader import ROOT,BLOB
    from v3_equipment_runtime import RAM as EQUIPMENT_RAM
    from v3_furniture_pipeline import Source,PreparedAssets,prepare,identity_rows
    from v3_import_storage import ROWS,ITEMS,slot
    from v3_resource_capacity import checked_limit
    from v3_tent_model import native_contract
    import v3_room_rig_runtime as room
    result=copy.deepcopy(prior['equipment_resources']);runtime=result['room_rigs'];packet=runtime['packet']
    module=blob[result['blob_offset']:result['blob_offset']+result['bytes']]
    if (runtime['format']!='AFV3-ROOM-RIGS-2' or sha256(module)!=result['sha256'] or
            sha256(blob[packet['blob_offset']:packet['blob_offset']+packet['bytes']])!=packet['sha256'] or
            EQUIPMENT_RAM+result['bytes']>room.PACKET_RAM or
            result['scenery']['ram']+result['scenery']['additional_fixed_resident_bytes']>room.PACKET_RAM or
            packet['ram']+packet['bytes']>RAM or RAM+BYTES>prior['furniture']['bank_pool']['start']):
        raise ValueError('Changed shared material runtime or overlapping scroll reservation')
    contract=native_contract(original,base,expected_sha=sha256(base))
    debug_at=0x8007A0C0-CODE_RAM
    debug_code=by_vrom(original)[CODE_VROM].extract(original)[debug_at:debug_at+0x90]
    if (sha256(debug_code)!='8ff8f035c40cae35db40b0f6e33422620870608e15a4356ca2ed08e512fb09ed' or
            core[debug_at:debug_at+0x90]!=debug_code):
        raise ValueError('Changed native debug-register allocation or zero initialization')
    contract.update(debug_owner_ram=0x80138E50,debug_bytes=0x1C94,debug_register_offset=0x14,
                    debug_initializer_sha256=sha256(debug_code))
    old_catalogue=by_vrom(original)[0x7A28F0].extract(original)
    catalogue=by_vrom(base)[0x3970000].extract(base);at=0x808A7814-0x808A6100
    if (sha256(old_catalogue[at:at+0xD0])!='aa1cd409237c29058fb12a0b15225172d7e25c3cbde53509bf87231fa3a790c1' or
            catalogue[at:at+0xD0]!=old_catalogue[at:at+0xD0]):
        raise ValueError('Changed preview null-room drawing contract')
    contract.update(preview_draw_sha256=sha256(catalogue[at:at+0xD0]),private_colour_offset=0x1A4,
        preview_frame_offset=0xA0,room_frame_offset=0x1EA0,source_frames_per_native_frame=2,
        native_coordinate_fraction_bits=2,source_coordinate_fraction_bits=4,maximum_frame_scratch_bytes=104,
        maximum_frame_alignment_padding=8,opaque_and_translucent_atomic_reservation=True)
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    from v3_furniture_contact import checked_contracts
    contacts=checked_contracts(source,base,prior)
    profile_bindings=room.bind_profiles(source,base,prior)
    directories=[d.resolve() for d in directories];cache=PreparedAssets(source,directories)
    identities=identity_rows(ROOT/'build/item-identity-megasheet.xlsx',include_unmapped_legacy=True)
    installed=runtime.get('scrolling',dict(format='AFV3-ROOM-SCROLL-1',rows=[],sources=[]))
    if installed['format'] not in ('AFV3-ROOM-SCROLL-1','AFV3-ROOM-SCROLL-2','AFV3-ROOM-SCROLL-3'):
        raise ValueError('Unknown scrolling runtime format')
    progress_fields={'lifecycle_installed','lifecycle','profile_installed','parent_selectable'}
    for old in installed['rows']:
        regenerated=json.loads(json.dumps(runtime_record(old['source'])))
        if any(value!=regenerated[key] for key,value in old.items()
               if key not in {'blob_offset','vrom'}|progress_fields):
            raise ValueError('Changed installed scroll source contract')
        if old.get('lifecycle_installed'):
            actual=draw_only_lifecycle(prepare(source,int(old['source_item_id'],16))[0],source)
            if actual is None:
                from v3_sound_programs import furniture_level
                actual=furniture_level(source,prepare(source,int(old['source_item_id'],16))[0])
            if actual is None:actual=contacts.get(old['source_item_id'])
            if actual is None or old.get('lifecycle')!=json.loads(json.dumps(actual)):
                raise ValueError('Changed completed scrolling lifecycle')
        if old.get('profile_installed'):
            binding=profile_bindings.get(old['source_item_id'])
            if binding is None or old['parent_selectable']==binding['staged']:
                raise ValueError('Changed retained scrolling profile')
        elif old.get('parent_selectable'):raise ValueError('Selected scrolling resource has no profile')
        old.update({k:v for k,v in regenerated.items() if k not in progress_fields})
    retained={r['source_item_id']:r for r in installed['rows']};reused=[]
    occupied={r['item_id'] for r in runtime['rows']+runtime.get('sound_rows',[])+
              runtime.get('material_rows',[])+installed['rows']}
    assets={};rows=[];evidence=[]
    for directory in directories:
        if not directory.is_relative_to(ROOT/'build'):raise ValueError('Scroll materials require ignored prepared artwork')
        raw=(directory/'art.json').read_bytes();art=json.loads(raw)
        if art['format']!='AFV3-AUTO-FURNITURE-PREPARED-ASSETS-1':raise ValueError('Expected complete prepared scroll assets')
        evidence.append(dict(directory=str(directory.relative_to(ROOT)),sha256=sha256(raw)))
        for row in art['objects']:
            donor=row['item_id'];item=int(donor,16);prepared=prepare(source,item)
            if (prepared[0]['callback_adapter']['category']!=CATEGORY or
                    row['profile']!=json.loads(json.dumps(prepared[0])) or
                    row['native_profile_scalar_hex']!=prepared[0]['scalar_hex'] or
                    any(identities[item][1].get(k)!='-' for k in ('C','H','CG','CJ')) or
                    cache.reuse(source,donor,prepared) is None):
                raise ValueError('Incomplete, changed, or unreviewed scrolling resources')
            path=(directory/row['object_file']).resolve()
            if path.parent!=directory:raise ValueError('Scroll artwork escapes its prepared directory')
            data=path.read_bytes();record=json.loads(json.dumps(runtime_record(row)));i=slot(int(record['item_id'],16))
            if len(data)!=record['bytes'] or sha256(data)!=record['sha256']:
                raise ValueError('Changed complete scrolling artwork')
            if donor in retained:
                old=retained[donor]
                if ({k:v for k,v in record.items() if k not in {'source'}|progress_fields}!=
                        {k:v for k,v in old.items() if k not in {'blob_offset','vrom','source'}|progress_fields} or
                        {k:v for k,v in record['source'].items() if k!='reused_artwork'}!=
                        {k:v for k,v in old['source'].items() if k!='reused_artwork'} or donor in reused):
                    raise ValueError('Changed or duplicate retained scrolling resources')
                reused.append(donor);continue
            if (record['item_id'] in occupied or any(blob[ROWS+i*80:ROWS+(i+1)*80]) or
                    any(blob[ITEMS+i*32:ITEMS+(i+1)*32]) or blob[0x40+i//8]&(1<<(i&7))):
                raise ValueError('Occupied scrolling destination')
            occupied.add(record['item_id']);rows.append(record);assets[donor]=data
    all_rows=sorted(installed['rows']+rows,key=lambda r:r['runtime_index']);encode(all_rows)
    contacts=checked_contracts(source,base,prior,rows=all_rows)
    from v3_sound_programs import checked_furniture_loops
    lifecycles,proof=checked_furniture_loops(base,core,result,source)
    if lifecycles.keys()&contacts.keys():raise ValueError('Overlapping scrolling lifecycle categories')
    lifecycles.update(contacts)
    new_lives=[]
    for row in all_rows:
        lifecycle=lifecycles.get(row['source_item_id'])
        if lifecycle is not None and not row['lifecycle_installed']:
            new_lives.append(lifecycle_record(row,lifecycle))
            row.update(lifecycle_installed=True,lifecycle=json.loads(json.dumps(lifecycle)))
    if not rows and not new_lives:raise ValueError('Empty scrolling material batch')
    if new_lives:
        native_core=by_vrom(original)[CODE_VROM].extract(original)
        first,last=0x800D1D08-CODE_RAM,0x800D1D94-CODE_RAM
        if core[first:last]!=native_core[first:last]:raise ValueError('Changed complete native positioned sound wrappers')
        installed['lifecycle_rows']=sorted(installed.get('lifecycle_rows',[])+new_lives,key=lambda r:r['runtime_index'])
        installed['lifecycle_audio']=proof
        installed['lifecycle_native_contract']=dict(address=first+CODE_RAM,bytes=last-first,sha256=sha256(native_core[first:last]))
    for r in installed['rows']:
        if sha256(blob[r['blob_offset']:r['blob_offset']+r['bytes']])!=r['sha256']:
            raise ValueError('Changed installed scrolling artwork')
    fresh='packet' not in installed;needed=sum(len(d) for d in assets.values())+(BYTES if fresh else 0)
    start=(len(blob)+15)&~15
    if BLOB+start+needed>checked_limit(base,prior):raise ValueError('Scroll resources exceed cartridge reservation')
    blob.extend(bytes(start-len(blob)))
    if fresh:
        installed['packet']=dict(ram=RAM,bytes=BYTES,blob_offset=len(blob),vrom=BLOB+len(blob));blob.extend(bytes(BYTES))
    for r in rows:
        at=len(blob);blob.extend(assets[r['source_item_id']]);r.update(blob_offset=at,vrom=BLOB+at)
    installed.update(rows=all_rows,native_contract=contract,additional_fixed_resident_bytes=BYTES,
                     batch=dict(added=len(rows),retained=len(reused),compiled_artwork=0))
    installed['sources'].extend(evidence);runtime['scrolling']=installed
    runtime['artwork_bytes']+=sum(len(d) for d in assets.values())
    room.publish_packet(result,blob,output)
    result['additional_resident_bytes']=BYTES if fresh else 0
    return result,{}


SOURCES=('tools/v3_furniture_scroll.py','tools/v3_furniture_contact.py','tools/v3_furniture_pipeline.py','tools/v3_furniture_art.py',
    'tools/v3_furniture_install.py','tools/v3_registry.py','tools/v3_asset_loader.py','tools/v3_tent_model.py',
    'tools/v3_room_rig_runtime.py','tools/v3_sound_programs.py','overlays/v3/room_scroll.c','overlays/v3/room_scroll.h','overlays/v3/room_scroll.ld',
    'overlays/v3/room_materials.c','overlays/v3/room_materials.h','overlays/v3/room_rigs.c',
    'overlays/v3/room_rigs_packet.ld','overlays/v3/room_rigs.h','overlays/v3/room_rigs_bootstrap.c',
    'overlays/v3/room_rigs_bootstrap.ld')
