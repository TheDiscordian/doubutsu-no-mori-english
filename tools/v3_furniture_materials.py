"""Prepare complete material-frame banks without flattening their callbacks.

Draw implementations identify resource layouts, not individual item IDs. All
frames and their duplicate table entries survive. Preparation never implies
that the renderer, source timing, interaction, sound, or acquisition is ported.
"""
import struct

from aflib import sha256, u32

CATEGORY='material-frame-assets'
# size, complete normalized draw digest, table pair, model pairs in actual
# submission order, matrix call, material kind, segment, table entries, selector.
FORMS=(
    (204,'cfb95eaef4f9a64d4f50229828d086ef2f2efe3b6e6628a7452650a43413c518',
     (0x6A,0x82),((0x6E,0x96),),0x4C,'palette',9,7,
     dict(input='room-or-preview-frame',division=8,modulo=7)),
    (232,'7e97ef50f92d6664d20f8d8f2a88598e0666931e3ccee718204e910186003fb9',
     (0x6A,0x8E),((0x6E,0x9E),(0x7A,0xA2)),0x4C,'palette',9,7,
     dict(input='room-or-preview-frame',division=8,modulo=7)),
    (240,'f33cdbbaa63cdab4a2c1308ed3aef3d374ff0db2da411a87594d93b0b4f2de51',
     (0x92,0xA6),((0x96,0xB6),),0x84,'palette',9,4,
     dict(input='room-or-preview-frame',division=10,modulo=4,signed=True,
          stopped_in_room_when_switch_off=True)),
    (220,'2df0ca124079361330a3e575f1860f3fd3a61e31fe5492125e964e81e0da70b9',
     (0x76,0x7A),((0x66,0x8E),(0x86,0x96)),0x4C,'palette',9,4,
     dict(input='room-or-preview-frame',division=20,modulo=4)),
    (212,'8d55b9c94b8ca5e3b1dc3949f2227d16736a7032eb261a7a4c7b98b7b7fac027',
     (0x5E,0x6A),((0x5A,0x86),(0x6E,0x7E)),0x4C,'texture',9,2,
     dict(input='room-or-preview-frame',division=2,modulo=2)),
    (168,'848b13d31a924efdfd525f925d6d2456e1d4b8640f7b4cba9bc3f3b3abc08af6',
     (0x4A,0x5E),((0x4E,0x6E),),0x3C,'texture',8,2,
     dict(input='actor-s16',offset=0x82C,mask=1)),
)


def discover(source,name,at,functions):
    from v3_furniture_pipeline import ReviewRequired
    draw=functions['draw'];raw,_=source.function(draw['offset'])
    forms=[r for r in FORMS if r[0]==len(raw)]
    if not forms:return None
    # Fingerprinting only chooses a candidate. Complete relocation, helper,
    # branch, table, and model validation below establishes its resource contract.
    normalized=bytearray(raw)
    for loc,(kind,_,_,_) in draw['relocations'].items():
        if kind in (4,6):normalized[loc:loc+2]=bytes(2)
        elif kind==10:struct.pack_into('>I',normalized,loc,u32(raw,loc)&0xFC000003)
        else:return None
    for loc in range(0,len(raw),4):
        word=u32(raw,loc)
        if word&0xFC000003==0x48000001:
            struct.pack_into('>I',normalized,loc,word&0xFC000003)
    form=next((r for r in forms if sha256(normalized)==r[1]),None)
    if form is None:return None
    size,digest,table_pair,model_pairs,call,kind,segment,count,selector=form
    module=u32(source.rel,0)
    expected={0x10:(10,0,4,0x8009AED4),size-20:(10,0,4,0x8009AF20)}
    def pair(hi,lo):
        pointer=draw['relocations'].get(hi)
        if pointer is None or pointer[:3]!=(6,module,5):
            raise ReviewRequired('material frames: missing paired data binding')
        target=pointer[3]
        expected.update({hi:(6,module,5,target),lo:(4,module,5,target)})
        return source.containing(target,exact=True)
    table,table_at,n=pair(*table_pair);pointers=source.pointers(table_at,n)
    if (n!=count*4 or any(source.data[table_at:table_at+n]) or
            set(pointers)!=set(range(table_at,table_at+n,4))):
        raise ReviewRequired('material frames: incomplete source frame table')
    frames=[]
    for pos in range(table_at,table_at+n,4):
        symbol,target,length=source.containing(pointers[pos],exact=True)
        if source.pointers(target,length) or (kind=='palette' and length!=32):
            raise ReviewRequired('material frames: incomplete frame resource')
        frames.append(dict(symbol=symbol,donor_offset=target,bytes=length,
                           source_sha256=sha256(source.data[target:target+length])))
    if len({r['bytes'] for r in frames})!=1:
        raise ReviewRequired('material frames: inconsistent complete frame sizes')
    models={f'part{i}':pair(*p) for i,p in enumerate(model_pairs)}
    helpers=source.checked_callback_code(draw,size,digest,expected,
        {call:(0x9D214,'_Matrix_to_Mtx_new')},'material frames',internal_branches=True)
    material=dict(kind=kind,segment_address=segment<<24,frames=frames,selector=dict(selector),
        table=dict(symbol=table,donor_offset=table_at,bytes=n,
                   source_sha256=sha256(source.data[table_at:table_at+n]),targets=list(pointers.values())))
    return models,{},dict(category=CATEGORY,vtable_symbol=name,vtable_offset=at,
        functions=functions,helpers=helpers,material_frames=[material],
        model_order=list(models),draw_arena='opaque',runtime_installed=False,
        pending_callbacks=list(functions),
        resource_scope='complete draw models and every material frame; lifecycle effects remain pending')


def bindings(adapter):
    """Require complete typed frame records before exposing dynamic segments."""
    if adapter.get('category')!=CATEGORY:return {}
    result={}
    for row in adapter['material_frames']:
        address=row['segment_address']
        if (address not in (0x08000000,0x09000000) or address in result or
                row['kind'] not in ('palette','texture') or not row['frames']):
            raise ValueError('Invalid complete material-frame binding')
        result[address]=row
    if not result:raise ValueError('Missing material-frame dependencies')
    return result
