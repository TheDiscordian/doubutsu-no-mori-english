"""Complete reversible rigs with delayed materials and particle emitters.

Recognise full callback shapes and dependencies, not item identities. Resource
conversion retains every joint, model, motion channel, and material table entry.
"""
import struct
import json
from aflib import sha256,u32,by_vrom
from v3_keyframes import skeleton,animation,model_descriptor

CATEGORY='reversible-material-effect-rig'


def checked_native(image):
    # The float RNG uses the same LCG as qrand, then returns its high 23 bits
    # as [0,1). Bind the full function, including its return delay instruction.
    data=by_vrom(image)[0x1060].extract(image)
    raw=data[0x8002C9AC-0x80025C60:0x8002CA00-0x80025C60]
    if len(raw)!=84 or sha256(raw)!='54eaafabfeeb3e70158a80e2e61b775f4340c6620b3984238268d2765f34bb56':
        raise ValueError('Changed native complete floating-point random generator')


def checked_binding(profile,binding,contracts,runtime,data):
    """Require full sound, particles, packed resources, and destruction dispatch."""
    adapter=profile['callback_adapter'];rig=binding['source']['rig'];offset=rig['material_offset']
    particles=runtime.get('effects',{}).get('particles',{})
    callbacks=struct.unpack('>5I',bytes.fromhex(runtime['vtable_hex']))
    flags=runtime['code']['flags']
    if (binding.get('mode')!=10 or binding.get('first')!=0x06000000+offset or binding.get('last') or
            data[offset:offset+32].hex()!=rig['material_hex'] or
            contracts.get(binding['source_item_id'])!=adapter['level_sound'] or
            not particles.get('installed') or particles.get('source')!=json.loads(json.dumps(adapter['effect_source'])) or
            any('-D'+flag not in flags for flag in ('AF_V3_ROOM_EFFECT_RIG','AF_V3_ROOM_REVERSIBLE','AF_V3_ROOM_PARTICLES')) or
            callbacks[3]!=runtime['bootstrap']['symbols'].get('af_v3_room_boot_dt') or not callbacks[3]):
        raise ValueError('Incomplete reversible material/effect rig dependencies')


def discover(source,name,at,functions):
    from v3_furniture_pipeline import ReviewRequired
    from v3_furniture_rigs import checked_stop_initializer
    if tuple(functions.get(r,{}).get('bytes') for r in ('create','move','draw','destroy'))!=(256,648,416,36):return None
    def reject(message):raise ReviewRequired('reversible material rig: '+message)
    if set(functions)!={'create','move','draw','destroy'}:reject('changed complete lifecycle')
    module=u32(source.rel,0);ct,mv,dw,dt=(functions[r] for r in ('create','move','draw','destroy'))
    constants={0xC100:'3f800000',0xC104:'00000000',0xC110:'4330000080000000',
        0xC118:'3f000000',0xC11C:'41200000',0xC1B0:'41a00000',0xC1D8:'41900000'}
    for p,value in constants.items():
        start,n=source.sections[4];raw=bytes.fromhex(value)
        if p+len(raw)>n or source.rel[start+p:start+p+len(raw)]!=raw:reject('changed complete constant')
    def pairs(receipt,rows):
        refs={};targets=[]
        for hi,lo,section,target in rows:
            ref=receipt['relocations'].get(hi)
            if ref is None or ref[:3]!=(6,module,section) or target is not None and ref[3]!=target:
                reject('changed paired dependency')
            targets.append(ref[3]);refs.update({hi:ref,lo:(4,module,section,ref[3])})
        return targets,refs
    (bones,motion),refs=pairs(ct,[(10,18,5,None),(34,46,5,None)])
    _,more=pairs(ct,[(62,70,5,motion),(98,118,5,motion),(82,90,4,0xC104),
        (86,94,4,0xC100),(110,126,4,0xC110)])
    helpers=source.checked_callback_code(ct,256,
        '89291f3c020dd008369f7b33e2c0dc9b3db3e44ff74f5034eccb835bd6135fc8',refs|more,
        {0x38:(0x8D4,'cKF_SkeletonInfo_R_ct'),0x4C:(0x934,'cKF_SkeletonInfo_R_init_standard_stop'),
         0xDC:(0xE54,'cKF_SkeletonInfo_R_play')},'combined reversible constructor',internal_branches=True)
    initializer=checked_stop_initializer(source)
    _,refs=pairs(mv,[(110,114,4,0xC1D8),(118,126,6,0xBC40),(238,246,4,0xC1B0),
        (242,250,4,0xC11C),(302,310,4,0xC104),(362,370,4,0xC118),
        (366,382,5,motion),(378,390,4,0xC110),(398,406,4,0xC100),
        (458,466,4,0xC118),(470,478,4,0xC100),(482,502,4,0xC110),
        (486,498,5,motion),(594,598,4,0xC104)])
    refs.update({16:(10,0,4,0x8009AED0),232:(10,0,4,0x8005CCF4),628:(10,0,4,0x8009AF1C)})
    helpers.update(source.checked_callback_code(mv,648,
        'eada8f13a1ea987fba09a085db3fa01ae7dec68a2860fa99f654497381a142cd',refs,
        {0x58:(0x2BDD84,'sAdo_OngenPos'),0x1C0:(0x2BDDE8,'sAdo_OngenTrgStart'),
         0x220:(0x2BDDE8,'sAdo_OngenTrgStart'),0x244:(0xE54,'cKF_SkeletonInfo_R_play')},
        'combined reversible movement',internal_branches=True))
    for symbol,n,digest,refs in (
        ('sAdo_OngenPos',100,'b982dbca7ed68e0565b554e142e64d69a1d2c47ec061169d114502a25e61f885',
         {72:(10,0,4,0x80012E2C),10:(6,module,6,2306744),34:(4,module,6,2306744)}),
        ('sAdo_OngenTrgStart',72,'4fdc889bb1697c19c8f386d72b80585ea07706d9f26b328389766bec96f0f989',
         {48:(10,0,4,0x8001383C)})):
        if any(helpers[symbol][k]!=v for k,v in dict(bytes=n,sha256=digest,relocations=refs).items()):
            reject('changed complete sound helper')
    (table,off,before,after),refs=pairs(dw,[(114,122,5,None),(134,138,5,None),
        (330,346,1,None),(338,354,1,None)])
    _,more=pairs(dw,[(150,158,5,motion),(170,174,4,0xC110),(242,250,5,table),
        (262,266,5,off),(278,282,5,off)])
    helpers.update(source.checked_callback_code(dw,416,
        '94c29f15353e4ee9b6713b2cfe56492edb6a52ca85d858ff1b5c03fdf24c6dca',
        refs|more|{16:(10,0,4,0x8009AEC4),396:(10,0,4,0x8009AF10)},
        {0x140:(0x9D214,'_Matrix_to_Mtx_new'),0x184:(0x1578,'cKF_Si3_draw_R_SV')},
        'combined reversible drawing',internal_branches=True))
    _,pre=source.function(before);_,post=source.function(after)
    source.checked_callback_code(pre,24,'42c938f5045d988736d65f01c489ad51add9ea58363a4d7aa5b2582256ec4a4b',
        {},{},'hidden fire joint')
    (fire,),refs=pairs(post,[(70,82,5,None)])
    source.checked_callback_code(post,128,'6a516c8956a06a507ed5ba86f3565fcd301f2c21df66ee30787b16246d82f8a8',
        refs,{0x3C:(0x9D214,'_Matrix_to_Mtx_new')},'translucent fire joint',internal_branches=True)
    source.checked_callback_code(dt,36,'c50acb633e458da05b486ad2ee3523889f1a150e7554746d62a89f2e56e2d718',
        {},{},'combined reversible persistence')
    rig=skeleton(source,bones);animated=animation(source,motion,joints=rig['joints'])
    if (rig['joints']>16 or rig['shown_joints']>6 or any(r['draw_stream'] for r in rig['rows']) or
            len(rig['rows'])<=2 or rig['rows'][2].get('model',{}).get('donor_offset')!=fire):
        reject('changed joint workspace or translucent model identity')
    desc=model_descriptor(rig,kind='animated-room-model')
    label=next(r['model_label'] for r in desc['joint_models'] if r['joint_index']==2)
    symbol,table,n=source.containing(table,exact=True);pointers=source.pointers(table,n)
    if n!=16 or any(source.data[table:table+n]) or set(pointers)!=set(range(table,table+n,4)):
        reject('incomplete complete fire sequence')
    frames=[]
    for target in [pointers[table+i*4] for i in range(4)]+[off]:
        frame_name,target,size=source.containing(target,exact=True)
        if size!=128 or source.pointers(target,size):reject('incomplete fire frame')
        frames.append(dict(symbol=frame_name,donor_offset=target,bytes=size,source_sha256=sha256(source.data[target:target+size])))
    material=dict(kind='texture',segment_address=0x08000000,frames=frames,
        selector=dict(input='delayed-state-and-context-frame',modulo=4,off_frame=4,
            preview_condition='animation-end-equals-duration'),
        table=dict(symbol=symbol,donor_offset=table,bytes=n,source_sha256=sha256(source.data[table:table+n]),
                   targets=[pointers[table+i*4] for i in range(4)]))
    from v3_room_particles import source_contract
    return desc['models'],{},dict(category=CATEGORY,vtable_symbol=name,vtable_offset=at,
        functions=functions,helpers=helpers,constants=constants,initializer=initializer,
        skeleton=rig,animation=animated,joint_models=desc['joint_models'],joint_callbacks=[pre,post],
        material_frames=[material],translucent_joint=2,translucent_model=label,
        constructor=dict(mode='stop',initial_speed=0,initial_state='saved-switch-not-one',counter_initial=0),
        reversible=dict(speed=.5,delay=19,source_steps_per_native_update=2,accept='idle-and-delay-zero',
            destructor='state-to-saved-switch'),
        steam=dict(height=18.0,spread=6,minimum_interval=10,random_interval=20,effect=113,
            interval_countdown='only-while-active-and-not-in-transition'),effects=['steam'],
        effect_source=source_contract(source),
        level_sound=dict(category='reversible-material-loop',source_sound_id=0x50,switch_clicks=[0x16,0x17],
            excluded_states=[13,14,15,12],native_excluded_states=[5,6,13,15],click_excluded_states=[],
            loop_state='internal-equals-one',callback_installed=False),runtime_installed=False)
