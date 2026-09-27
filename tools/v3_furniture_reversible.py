"""Complete reversible skeleton resources and source lifecycle contracts.

The category retains larger skeletons without dropping hidden joints. Runtime
installation remains separate from complete artwork preparation.
"""
import struct
from aflib import sha256,u32
from v3_keyframes import skeleton,animation,model_descriptor

CATEGORY='reversible-keyframe-rig-assets'


def discover(source,name,at,functions):
    from v3_furniture_pipeline import ReviewRequired
    from v3_furniture_rigs import checked_stop_initializer
    if (functions.get('create',{}).get('bytes'),functions.get('move',{}).get('bytes'),
            functions.get('draw',{}).get('bytes'))!=(248,316,140):return None
    def reject(message):raise ReviewRequired('reversible rig: '+message)
    if set(functions)!={'create','move','draw','destroy'}:reject('changed complete lifecycle slots')
    module=u32(source.rel,0);ct,mv,dw,dt=(functions[r] for r in ('create','move','draw','destroy'))
    def pairs(receipt,rows):
        refs={};targets=[]
        for hi,lo,section,expected in rows:
            ref=receipt['relocations'].get(hi)
            if ref is None or ref[:3]!=(6,module,section) or expected is not None and ref[3]!=expected:
                reject('changed paired dependency')
            targets.append(ref[3]);refs.update({hi:ref,lo:(4,module,section,ref[3])})
        return targets,refs
    (bones,motion),refs=pairs(ct,[(0x0A,0x12,5,None),(0x22,0x2E,5,None)])
    _,more=pairs(ct,[(0x3E,0x46,5,motion),(0x62,0x76,5,motion),
        (0x52,0x5A,4,0xC104),(0x56,0x5E,4,0xC100),(0x6E,0x7E,4,0xC110)])
    helpers=source.checked_callback_code(ct,248,
        'b989f7731a6285f71342054495809c7b9c91da1e4e15748db0fa1bcfed0abdc6',refs|more,
        {0x38:(0x8D4,'cKF_SkeletonInfo_R_ct'),0x4C:(0x934,'cKF_SkeletonInfo_R_init_standard_stop'),
         0xDC:(0xE54,'cKF_SkeletonInfo_R_play')},'reversible constructor',internal_branches=True)
    constants={0xC100:'3f800000',0xC104:'00000000',0xC110:'4330000080000000',0xC118:'3f000000'}
    for offset,value in constants.items():
        base,n=source.sections[4];wanted=bytes.fromhex(value)
        if offset+len(wanted)>n or source.rel[base+offset:base+offset+len(wanted)]!=wanted:
            reject('changed motion constant')
    initializer=checked_stop_initializer(source)
    _,refs=pairs(mv,[(0x22,0x2A,4,0xC104),(0x52,0x5A,4,0xC118),
        (0x56,0x6E,5,motion),(0x5E,0x62,4,0xC110),(0x76,0x7E,4,0xC100),
        (0xB2,0xBA,4,0xC118),(0xB6,0xBE,4,0xC100),(0xC2,0xDE,5,motion),
        (0xCE,0xD6,4,0xC110),(0x11E,0x122,4,0xC104)])
    raw,_=source.function(mv['offset']);sounds={p:struct.unpack_from('>H',raw,p)[0] for p in (0x96,0xE6)}
    if len(set(sounds.values()))!=1 or any(v&0x8080 for v in sounds.values()):reject('unsupported bidirectional sound')
    sound=next(iter(sounds.values()))
    helpers.update(source.checked_callback_code(mv,316,
        'd69b58f7a33b06836e88598dccab2f3e8f0cf24939e1d50ac62a316afe13dbe0',refs,
        {0xA8:(0x2BDDE8,'sAdo_OngenTrgStart'),0x108:(0x2BDDE8,'sAdo_OngenTrgStart'),
         0x110:(0xE54,'cKF_SkeletonInfo_R_play')},'reversible movement',sounds,internal_branches=True))
    helper=helpers['sAdo_OngenTrgStart']
    if (helper['bytes']!=72 or helper['sha256']!='4fdc889bb1697c19c8f386d72b80585ea07706d9f26b328389766bec96f0f989' or
            helper['relocations']!={48:(10,0,4,0x8001383C)}):reject('changed complete trigger helper')
    helpers.update(source.checked_callback_code(dw,140,
        '61e6b19d38da02cca2132d93466c24a5e2907042ce42521c49675b0c3dba0470',
        {0x10:(10,0,4,0x8009AED0),0x78:(10,0,4,0x8009AF1C)},
        {0x50:(0x9D214,'_Matrix_to_Mtx_new'),0x70:(0x1578,'cKF_Si3_draw_R_SV')},'reversible drawing'))
    source.checked_callback_code(dt,36,
        'c50acb633e458da05b486ad2ee3523889f1a150e7554746d62a89f2e56e2d718',{}, {},'reversible save switch')
    rig=skeleton(source,bones);motion=animation(source,motion,joints=rig['joints'])
    if rig['joints']>16 or rig['shown_joints']>6 or any(r['draw_stream'] for r in rig['rows']):
        reject('extended work requires at most sixteen joints and six opaque matrices')
    descriptor=model_descriptor(rig,kind='animated-room-model')
    return descriptor['models'],{},dict(category=CATEGORY,vtable_symbol=name,vtable_offset=at,
        functions=functions,helpers=helpers,constants=constants,initializer=initializer,
        skeleton=rig,animation=motion,joint_models=descriptor['joint_models'],joint_callbacks=[],
        constructor=dict(mode='stop',initial_speed=0,start=1,end=motion['duration'],
            initial_state='saved-switch-equals-one',closed_frame=motion['duration']),
        reversible=dict(press='any-nonzero',accept='idle',speed=.5,source_steps_per_native_update=2,
            on_start=motion['duration'],on_end=1,off_start=1,off_end=motion['duration'],
            stop_result=1,destructor='state-to-saved-switch',excluded_states=[]),
        trigger=dict(sound_word=sound,excluded_states=[],switch_value='nonzero-idle',runtime_installed=False),
        work=dict(vectors=17,maximum_shown_matrices=6,joint_bytes=102,morph_bytes=102,
            saved_state_bytes=0),runtime_installed=False)
