"""Complete fixed rigs whose joint callbacks rotate or redraw their models.

Resource preparation retains every lifecycle and draw dependency. It does not
install those callbacks or enable an inert substitute for the source furniture.
"""
from aflib import u32
from v3_keyframes import skeleton, animation, model_descriptor

CATEGORY = 'joint-callback-rig-assets'
CONSTRUCTORS = {
    132: ('6f035ad757f005d83160b57d4c01275eb088558bb7a9dff5a7123f8373ed07e3', 'stop'),
    160: ('48e2144b533a58471a4cfe6c4dfd74694d6ed66a753a92e2d3be71fa43c0b6e8', 'repeat'),
    168: ('7f8874a013328dc7b5539ed68e52b5e022c2100dab0cf2fec65d9d7e23f0f00a', 'repeat'),
    236: ('f05297ca31ee01899077ec77991bd4e4dd0aed9e0f531c5ca1d309c4df6a93b8', 'repeat'),
}
CONSTANTS = {0xC100:'3f800000', 0xC104:'00000000', 0xC110:'4330000080000000',
             0xC118:'3f000000', 0xC150:'4622f983', 0xC154:'3c8efa35',
             0xC158:'437f0000', 0xC24C:'44160000'}


def discover(source, vtable_name, vtable_at, functions):
    from v3_furniture_pipeline import ReviewRequired
    if functions.get('create',{}).get('bytes') not in CONSTRUCTORS or functions['draw']['bytes']!=148:
        return None
    def reject(reason):raise ReviewRequired('joint callback rig: '+reason)
    if set(functions)!={'create','move','draw'}:reject('unsupported lifecycle slots')
    module=u32(source.rel,0);constants={};helpers={}
    def pair(receipt,hi,lo,section,expected=None):
        ref=receipt['relocations'].get(hi)
        if ref is None or ref[:3]!=(6,module,section) or expected is not None and ref[3]!=expected:
            reject('changed paired dependency')
        return ref[3],{hi:ref,lo:(4,module,section,ref[3])}
    def fixed_pairs(rows):
        result={}
        for hi,lo,sec,at in rows:
            result.update({hi:(6,module,sec,at),lo:(4,module,sec,at)})
            if sec==4:
                value=bytes.fromhex(CONSTANTS[at]);base,n=source.sections[4]
                if not 0<=at<=n-len(value) or source.rel[base+at:base+at+len(value)]!=value:
                    reject('changed complete constant')
                constants[f'{at:X}']=dict(section=4,offset=at,hex=value.hex())
        return result
    create=functions['create'];size=create['bytes'];digest,mode=CONSTRUCTORS[size]
    if size==236:
        bones,a=pair(create,0x26,0x3E,5);motion,b=pair(create,0x2A,0x32,5)
        _,c=pair(create,0x52,0x5A,5,motion)
        expected=a|b|c|fixed_pairs(((0x16,0x1E,6,0xBC40),(0x7A,0x7E,4,0xC100),
            (0x8E,0x92,4,0xC104),(0xAA,0xB2,4,0xC110),(0xAE,0xBA,4,0xC24C)))
        expected.update({0x10:(10,0,4,0x8009AED0),0xD8:(10,0,4,0x8009AF1C)})
        ct,init,play=0x4C,0x60,0x68
    else:
        bones,a=pair(create,0x0A,0x12,5);motion,b=pair(create,0x22,0x2E,5)
        _,c=pair(create,0x3E,0x46,5,motion);expected=a|b|c
        rows={132:((0x5A,0x5E,4,0xC104),),
              160:((0x66,0x6A,4,0xC100),(0x7A,0x7E,4,0xC104)),
              168:((0x66,0x6E,4,0xC118),(0x6A,0x72,4,0xC100),(0x82,0x86,4,0xC104))}[size]
        expected.update(fixed_pairs(rows));ct,init,play=0x38,0x4C,0x54
    initializer=(0x934,'cKF_SkeletonInfo_R_init_standard_stop') if mode=='stop' else (0xA24,'cKF_SkeletonInfo_R_init_standard_repeat')
    helpers.update(source.checked_callback_code(create,size,digest,expected,
        {ct:(0x8D4,'cKF_SkeletonInfo_R_ct'),init:initializer,play:(0xE54,'cKF_SkeletonInfo_R_play')},
        'joint-rig constructor',internal_branches=True))
    rig=skeleton(source,bones);motion=animation(source,motion,joints=rig['joints'])
    descriptor=model_descriptor(rig,kind='animated-room-model')
    draw=functions['draw'];before,a=pair(draw,0x56,0x62,1);after,b=pair(draw,0x5A,0x66,1)
    helpers.update(source.checked_callback_code(draw,148,
        '9569119bcf3009294c97f88744ddbbded40fde642128378b1c3a8bb459cd474d',
        a|b|{0x10:(10,0,4,0x8009AED0),0x80:(10,0,4,0x8009AF1C)},
        {0x50:(0x9D214,'_Matrix_to_Mtx_new'),0x78:(0x1578,'cKF_Si3_draw_R_SV')},'joint-rig drawing'))
    _,pre=source.function(before);_,post=source.function(after)
    expected={};calls={};features={};scrolling={}
    if pre['bytes']==200:
        digest='4a9db8a005a9a40839ae1f31b69e631b0dabd2d2e3049f3c4e751c99c634a031'
        expected=fixed_pairs(((0x16,0x26,4,0xC154),(0x1A,0x2E,4,0xC150),(0x4E,0x56,6,0xBC40)))
        expected.update({0x10:(10,0,4,0x8009AED4),0xB4:(10,0,4,0x8009AF20)})
        calls={0x90:(0x103C60,'aMR_GetParentAngleOffset')}
        features=dict(mode='parent-relative-needle',joint=3,axis='y',operation='subtract')
    elif pre['bytes']==52:
        digest='bf81c4b44f97129403ee4ef0266147947d1a13719f06dea73f77296faf027937'
        features=dict(mode='accumulated-rotation',joint=1,axis='z',operation='add')
    elif pre['bytes']==32:
        raw,_=source.function(before)
        from aflib import sha256
        digest=sha256(raw)
        if digest=='8b8d3120858adb9e211d008022dae989538947871007eb385255895de1a079d6':
            features=dict(mode='translucent-joints',joints=[3,7],colour='primitive-lod')
        elif digest=='6a5ba4eb4e2ad1afeaa2e3670e830842e4bdcc88da498d9386188a0edfb56d9b':
            features=dict(mode='translucent-joints',joints=[3,4],colour='primitive-alpha')
        else:reject('unknown hidden-joint implementation')
    else:reject('unknown joint transform')
    helpers.update(source.checked_callback_code(pre,pre['bytes'],digest,expected,calls,
        'joint-rig before callback',internal_branches=True))
    expected={};calls={}
    if features['mode']!='translucent-joints':
        if not 0<=features['joint']<rig['joints']:reject('transform exceeds complete skeleton')
        digest='2bf7a94759a252fd0d2af700ff876c19ab13998fb28ac5b0db3c70cdbc9ef8d6';length=8
    else:
        if post['bytes'] not in (272,384):reject('missing translucent-joint drawing')
        length=post['bytes'];hidden=features['joints']
        if (length,hidden) not in ((272,[3,7]),(384,[3,4])):reject('changed joint drawing combination')
        pairs=((0x66,0x72),(0xD6,0xE2)) if length==272 else ((0x66,0x72),(0x116,0x132))
        for joint,(hi,lo) in zip(hidden,pairs):
            address,refs=pair(post,hi,lo,5);expected.update(refs)
            if joint>=rig['joints'] or rig['rows'][joint].get('model',{}).get('donor_offset')!=address:
                reject('joint callback model differs from its complete skeleton')
        if length==272:
            digest='78c5b2af3e36913108232f4a8b5b7472481775d07c5b7c21c89d7217f267ca9c'
            expected.update(fixed_pairs(((0x0A,0x16,4,0xC158),)))
            calls={0x5C:(0x9D214,'_Matrix_to_Mtx_new'),0xCC:(0x9D214,'_Matrix_to_Mtx_new')}
        else:
            digest='15182743de790412d184e3c36199bec4fc455e2521b48816f654d07c14d12556'
            expected.update(fixed_pairs(((0xAA,0xBA,4,0xC118),(0xAE,0xBE,4,0xC158))))
            expected.update({0x10:(10,0,4,0x8009AECC),0x16C:(10,0,4,0x8009AF18)})
            raw,_=source.function(after);word=u32(raw,0xA4);delta=word&0x3FFFFFC
            if delta&0x2000000:delta-=0x4000000
            wrapper=after+0xA4+delta;_,receipt=source.function(wrapper)
            helpers.update(source.checked_callback_code(receipt,84,
                'fe49f006bf5da863593bf239c8d49834ff91a60126c9489aed542ca9236f12b8',{},
                {0x40:(0x75400,'two_tex_scroll_dolphin')},'joint-rig scrolling dimensions'))
            from v3_furniture_scroll import checked_generator
            checked_generator(source,helpers['two_tex_scroll_dolphin'])
            helpers[receipt['symbol']]=receipt
            calls={0x5C:(0x9D214,'_Matrix_to_Mtx_new'),0xA4:(wrapper,receipt['symbol']),0xFC:(0x9D214,'_Matrix_to_Mtx_new')}
            label=next(r['model_label'] for r in descriptor['joint_models'] if r['joint_index']==hidden[1])
            from v3_furniture_pipeline import model_texture_shape
            _,at,n=descriptor['models'][label];raw=source.data[at:at+n]
            textures=[model_texture_shape(raw[p:p+8]) for p in range(0,n,8) if raw[p]==0xFD]
            if textures!=[(16,32,4,0)]:reject('changed complete scrolling intensity image')
            scrolling=dict(model=label,segment_address=0x09000000,input='room-or-preview-frame',
                texture_dimensions=[list(t[:2]) for t in textures],
                tiles=[dict(index=i,width=8,height=32,rate=[0,8 if i==0 else 0]) for i in range(2)])
    helpers.update(source.checked_callback_code(post,length,digest,expected,calls,
        'joint-rig after callback',internal_branches=True))
    callbacks=[dict(role='before',**pre),dict(role='after',**post)]
    return descriptor['models'],{},dict(category=CATEGORY,vtable_symbol=vtable_name,vtable_offset=vtable_at,
        functions=functions,helpers=helpers,constants=constants,joint_callbacks=callbacks,
        joint_features=features,**({'scrolling':scrolling} if scrolling else {}),
        constructor=dict(mode=mode,source_binding_only=True),skeleton=rig,animation=motion,
        joint_models=descriptor['joint_models'],pending_callbacks=['create','move','draw'],runtime_installed=False,
        resource_scope='complete skeleton, motion, joint models, and callback dependencies; native gameplay pending')
