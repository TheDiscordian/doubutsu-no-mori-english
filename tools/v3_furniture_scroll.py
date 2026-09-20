"""Discover complete scrolling materials, retaining their actual draw contracts.

This resource category preserves both texture layers and callback parameters.
It does not enable an item before its renderer, lifecycle, and acquisition exist.
"""
import struct

from aflib import sha256, u32

CATEGORY = 'scrolling-material-assets'
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


def discover(source, name, at, functions):
    from v3_furniture_pipeline import ReviewRequired
    draw = functions['draw']; raw, _ = source.function(draw['offset'])
    forms = [form for form in FORMS if form[0] == len(raw)]
    if not forms: return None
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
    if form is None: return None
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
    source.checked_callback_code(common,204,
        '595b86c4d52240deb412e1eb8e36370b1445e77e805782439314800eb132011e',
        {0x10:(10,0,4,0x8009AED0),0xB8:(10,0,4,0x8009AF1C)}, {}, 'shared scroll generator',
        internal_branches=True)
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
            [r['index'] for r in tiles]!=[0,1] or row['model']!=adapter['model_order'][-1] or
            adapter['model_arenas'][row['model']]!='translucent'):
        raise ValueError('Invalid complete scroll material binding')
    dimensions = tuple((r['width'],r['height']) for r in tiles)
    if dimensions not in WRAPPERS: raise ValueError('Unsupported complete scrolling dimensions')
    return {row['model']:dict(segment=row['segment_address'],
                             dimensions=[list(shape) for shape in dimensions if shape!=(0,0)])}
