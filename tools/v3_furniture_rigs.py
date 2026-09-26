"""Source-discovered indexed room rigs, retaining their complete behaviour.

This is a callback/asset category, not an item list. Preparing a rig does not
install its lifecycle callbacks or make its parent selectable.
"""
import re
import math
import struct

from aflib import sha256, u32
from v3_keyframes import animation, skeleton, model_descriptor, compile_skeleton, compile_animations

CATEGORY = 'indexed-switch-rig'
CLOCK_CATEGORY = 'indexed-loop-clock-rig'
STORAGE_CATEGORY = 'open-close-storage-rig'
HIT_CATEGORY = 'switch-hit-keyframe-rig'
BILLBOARD_CATEGORY = 'billboard-scroll-keyframe-rig'
from v3_furniture_motion import CATEGORY as ROLLING_CATEGORY
# Complete fixed rig resources with explicit, still-unimplemented callbacks.
# This category is deliberately not a native behaviour adapter.
FIXED_CATEGORY = 'fixed-keyframe-rig-assets'
STORAGE_CODE = {
    'create': (116, '17985ba5a79cb082f421871e07eca8189d15291d08d408f4d68c257b072d166d'),
    'move': (80, '74d56a7240cc6101e429e75a9163eacb63753bfb06e944d1e80d291853fa6690'),
    'draw': (140, '61e6b19d38da02cca2132d93466c24a5e2907042ce42521c49675b0c3dba0470'),
    'destroy': (4, 'f332ea5b5437103cbb6f1508679da89eec9288ad775c96c439a17fccabe3de8e'),
}
CLOCK_CODE = {
    'create': (140, '6979dab4959772e11795a2b2cd0711ffa5875e1243321c7c856974deea9a4064'),
    'move': (36, 'bb0989f0a657b30e25ea7de2e21589425883dfaed308bd116dabef8de4ef1dd2'),
    'draw': (200, 'f6e60a96386c7721dcd0c894196eae1ee3e5c6339aadf921e2f95952ff7584de'),
    'destroy': (4, 'f332ea5b5437103cbb6f1508679da89eec9288ad775c96c439a17fccabe3de8e'),
}
RIG_CATEGORIES = (CATEGORY, CLOCK_CATEGORY, STORAGE_CATEGORY, HIT_CATEGORY, BILLBOARD_CATEGORY, ROLLING_CATEGORY)
RESOURCE_CATEGORIES = RIG_CATEGORIES + (FIXED_CATEGORY,)
CODE = {
    'create': (164, '2a86d61bc9aaf4a0a6479fe97a7f0d5dfe3dc42f9eea663eeb3fd1b8cbc35733'),
    'move': (208, '4b36894add16ecf872c1bfdcbeed2331519049fffd5b3d1d1d5db533f7c68d89'),
    'draw': (148, 'a0546e1e4e5893a157857ce34244a4183e8991928ae34ce585f79b3da0d052bb'),
    'destroy': (4, 'f332ea5b5437103cbb6f1508679da89eec9288ad775c96c439a17fccabe3de8e'),
}


def discover_billboard(source, vtable_name, vtable_at, functions):
    """Discover complete looping rigs with a camera-facing scrolling joint."""
    from v3_furniture_pipeline import ReviewRequired
    from v3_furniture_scroll import checked_generator
    def reject(reason):raise ReviewRequired('custom callbacks: billboard rig '+reason)
    if set(functions)!={'create','move','draw'}:reject('changed lifecycle slots')
    module=u32(source.rel,0);create=functions['create'];move=functions['move'];draw=functions['draw']
    def pair(receipt,hi,lo,section):
        ref=receipt['relocations'].get(hi)
        if ref is None or ref[:3]!=(6,module,section):reject('missing paired source binding')
        return ref[3],{hi:ref,lo:(4,module,section,ref[3])}
    def constant(at,raw):
        base,n=source.sections[4]
        if not 0<=at<=n-len(raw) or source.rel[base+at:base+at+len(raw)]!=raw:
            reject('changed complete constant')
    bones,a=pair(create,0x0E,0x1A,5);motion,b=pair(create,0x16,0x2A,5)
    repeat,c=pair(create,0x3A,0x42,5);speed,d=pair(create,0x4E,0x56,4)
    if motion!=repeat:reject('changed constructor motion')
    constant(speed,struct.pack('>f',.5))
    helpers=source.checked_callback_code(create,116,
        '17985ba5a79cb082f421871e07eca8189d15291d08d408f4d68c257b072d166d',a|b|c|d,
        {0x34:(0x8D4,'cKF_SkeletonInfo_R_ct'),0x48:(0xA24,'cKF_SkeletonInfo_R_init_standard_repeat'),
         0x5C:(0xE54,'cKF_SkeletonInfo_R_play')},'billboard constructor')
    forms={88:(0x2E,0x36,0x3C,'0ba25ef4e6aa1d922958ab14804f260f4b3c85bae06161b45c32bcc51dab5fb9'),
        124:(0x2A,0x5E,0x60,'9b33d4bfc00c2ab1acafa1b8bd313661eb3377a321728db7e5863c5f9a409e25')}
    if move['bytes'] not in forms:reject('unknown motion/sound implementation')
    lo,operand,call,digest=forms[move['bytes']];at,refs=pair(move,0x26,lo,4)
    if at!=speed:reject('changed move speed')
    raw,_=source.function(move['offset']);sound=struct.unpack_from('>H',raw,operand)[0]
    if not 68<=sound<96:reject('unsupported source loop sound')
    helpers.update(source.checked_callback_code(move,move['bytes'],digest,refs,
        {0x20:(0xE54,'cKF_SkeletonInfo_R_play'),call:(0x2BDD84,'sAdo_OngenPos')},
        'billboard motion and sound',{operand:sound}))
    sound_helper=helpers['sAdo_OngenPos']
    if (sound_helper['bytes']!=100 or sound_helper['sha256']!='b982dbca7ed68e0565b554e142e64d69a1d2c47ec061169d114502a25e61f885' or
            sound_helper['relocations']!={72:(10,0,4,0x80012E2C),10:(6,module,6,2306744),34:(4,module,6,2306744)}):
        reject('changed positioned sound helper')
    before,a=pair(draw,0xB6,0xC6,1);after,b=pair(draw,0xBE,0xCE,1)
    raw,_=source.function(draw['offset']);normal=bytearray(raw)
    for p,(kind,_,_,_) in draw['relocations'].items():
        if kind in (4,6):normal[p:p+2]=bytes(2)
        elif kind==10:struct.pack_into('>I',normal,p,u32(raw,p)&0xFC000003)
        else:reject('unknown draw relocation')
    for p in range(0,len(raw),4):
        if u32(raw,p)&0xFC000003==0x48000001:struct.pack_into('>I',normal,p,u32(raw,p)&0xFC000003)
    forms={
        '233a0cce877849814d28e24b50e3fc3fbb836b60fe59d0773f42b7d67266b7b4':
            (((32,32),(32,64)),((0,0),(0,-8)),84,0x40,'2682e7f5f1755916c666209efb4544cd130fb1a8802a250151da8c02c14dbdc9'),
        'e3f027923c23bb0edfc2ff5e3b56c7353fd5885f4fadf9d30308e2f97553ee2c':
            (((32,64),(32,32)),((0,-6),(0,0)),80,0x3C,'7f7f55c6d933900a391ed32f6c38ca48b280f59eb7f70d4cdd44685edf79e94b'),
        'fa68bcdf2c223ec93650cf74ea2d0157af935e251dc8d6d47df8163e5f268fd1':
            (((32,64),(64,32)),((0,-3),(-2,0)),84,0x40,'45538a9d6afbcec56161b084e7b365bc79fe07794fa6371daaf94baef24e1769')}
    digest=sha256(normal)
    if digest not in forms:reject('unknown complete scroll drawing')
    dimensions,rates,wn,wcall,wh=forms[digest]
    word=u32(raw,0x5C);delta=word&0x3FFFFFC
    if delta&0x2000000:delta-=0x4000000
    wrapper=draw['offset']+0x5C+delta;_,receipt=source.function(wrapper)
    helpers.update(source.checked_callback_code(draw,268,digest,
        a|b|{0x10:(10,0,4,0x8009AEC4),0xF8:(10,0,4,0x8009AF10)},
        {0x5C:(wrapper,receipt['symbol']),0x88:(0x9D214,'_Matrix_to_Mtx_new'),
         0xAC:(0x9D214,'_Matrix_to_Mtx_new'),0xF0:(0x1578,'cKF_Si3_draw_R_SV')},'billboard drawing'))
    helpers.update(source.checked_callback_code(receipt,wn,wh,{},
        {wcall:(0x75400,'two_tex_scroll_dolphin')},'billboard scroll dimensions'))
    checked_generator(source,helpers['two_tex_scroll_dolphin'])
    _,pre=source.function(before);_,post=source.function(after)
    source.checked_callback_code(pre,24,'42c938f5045d988736d65f01c489ad51add9ea58363a4d7aa5b2582256ec4a4b',{}, {},'billboard hidden joint')
    zero,a=pair(post,0x2E,0x36,4);scale,b=pair(post,0x5A,0x62,4);flame,c=pair(post,0xFA,0x106,5)
    constant(zero,bytes(12));constant(scale,struct.pack('>f',.01))
    helpers.update(source.checked_callback_code(post,328,
        '681fdd9f27c937f2f0319a92497d4a42eaed981da6a711ed2fa4d4746a7fa3df',
        a|b|c|{0x28:(10,0,4,0x8009AED4),0x134:(10,0,4,0x8009AF20)},
        {0x84:(0x9D244,'Matrix_Position'),0x88:(0x9C014,'Matrix_push'),
         0x9C:(0x9C140,'Matrix_translate'),0xA8:(0x9C0D8,'Matrix_mult'),
         0xB4:(0x9C49C,'Matrix_RotateY'),0xC8:(0x9C22C,'Matrix_scale'),
         0xE8:(0x9D214,'_Matrix_to_Mtx_new'),0xF0:(0x9C054,'Matrix_pull')},'camera-facing joint'))
    rig=skeleton(source,bones);motion=animation(source,motion,joints=rig['joints'])
    if not 3<=rig['joints']<=6 or rig['rows'][2].get('model',{}).get('donor_offset')!=flame:
        reject('missing complete flame joint')
    descriptor=model_descriptor(rig,kind='animated-room-model')
    flame_label=next(r['model_label'] for r in descriptor['joint_models'] if r['joint_index']==2)
    excluded=[12,13,14,15] if move['bytes']==124 else []
    return descriptor['models'],{},dict(category=BILLBOARD_CATEGORY,vtable_symbol=vtable_name,
        vtable_offset=vtable_at,functions=functions,helpers=helpers,joint_callbacks=[pre,post],
        skeleton=rig,animation=motion,joint_models=descriptor['joint_models'],
        constructor=dict(mode='repeat',initial_speed=.5,initial_play_before_speed=False),
        billboard=dict(joint=2,model=flame_label,rotation_y=0x4000,scale=.01,
            source_billboard_offset=0x204C,native_billboard_offset=0x1E5C),
        scrolling=dict(segment_address=0x09000000,model=flame_label,input='room-or-preview-frame',
            source_coordinate_shift=1,tiles=[dict(index=i,width=w,height=h,rate=list(rates[i]))
                for i,(w,h) in enumerate(dimensions)]),
        level_sound=dict(category='positioned-loop',source_sound_id=sound,excluded_states=excluded,
            native_excluded_states=[5,6,13,15] if excluded else [],state_offset=0x3C,position_offset=8,
            switch_clicks=[],callback_installed=False),runtime_installed=False)


def checked_stop_initializer(source):
    """Bind the complete donor initializer, including its half-speed default."""
    module=u32(source.rel,0);base,_=source.sections[4]
    raw,receipt=source.function(0x934)
    refs={0x0A:(6,module,4,0),0x0E:(6,module,4,0x20),0x1E:(4,module,4,0),
        0x2E:(6,module,4,0x30),0x36:(4,module,4,0x20),0x3E:(4,module,4,0x30),
        0x42:(6,module,4,4),0x4E:(4,module,4,4)}
    constants=((0,'3f800000'),(4,'00000000'),(0x20,'4330000080000000'),(0x30,'3f000000'))
    if (len(raw)!=124 or sha256(raw)!='8045cfda172f82aae9f38054c5e7844b87a7f3428bfc612252eff8e75435efa4' or
            receipt['relocations']!=refs or any(source.rel[base+at:base+at+len(value)//2]!=bytes.fromhex(value)
                for at,value in constants)):
        raise ValueError('Changed source stop initializer')
    return receipt


def discover_idle_hit(source, adapter):
    """Complete stopped-hit variant; resource identities remain data, not cases."""
    functions=adapter['functions'];move=functions.get('move',{})
    if move.get('bytes')!=208 or adapter['constructor']['mode']!='stop':return None
    from v3_furniture_pipeline import ReviewRequired
    def reject(reason):raise ReviewRequired('custom callbacks: idle-hit rig '+reason)
    if (set(functions)!={'create','move','draw'} or adapter['constructor']['initial_speed']['hex']!='00000000'
            or not adapter['constructor']['initial_play_before_speed'] or adapter['joint_callbacks']):
        reject('changed complete lifecycle')
    initializer=checked_stop_initializer(source);module=u32(source.rel,0)
    expected={};constants={}
    for hi,lo,name,value in ((0x0A,0x12,'zero',0),(0x66,0x6E,'first_frame',1),
            (0x7A,0x7E,'speed',.25),(0xA2,0xA6,'speed',.25),(0xB2,0xB6,'zero',0)):
        ref=move['relocations'].get(hi)
        if ref is None or ref[:3]!=(6,module,4):reject('missing constant relocation')
        at=ref[3];base,n=source.sections[4]
        if not 0<=at<=n-4 or source.rel[base+at:base+at+4]!=struct.pack('>f',value):reject('changed animation constant')
        expected.update({hi:ref,lo:(4,module,4,at)})
        row=dict(section=4,offset=at,hex=struct.pack('>f',value).hex(),value=value)
        if name in constants and constants[name]!=row:reject('ambiguous constant')
        constants[name]=row
    if constants['zero']['offset']!=adapter['constructor']['initial_speed']['offset']:reject('changed initial speed')
    raw,_=source.function(move['offset']);sound=struct.unpack_from('>H',raw,0x5E)[0]
    if sound&0x80 or (sound&0x7FFF)>>8 not in (0,1,4):reject('unsupported sound word')
    helpers=source.checked_callback_code(move,208,
        '3bde8d1b666ce0a3b94696fe6b35b7e956bb442582ebfb6606d8a4236972f1a2',expected,
        {0x60:(0x2BDDE8,'sAdo_OngenTrgStart'),0x74:(0xE54,'cKF_SkeletonInfo_R_play'),
         0x8C:(0xE54,'cKF_SkeletonInfo_R_play'),0x9C:(0xE54,'cKF_SkeletonInfo_R_play')},
        'idle-hit motion',{0x5E:sound},internal_branches=True)
    trigger=helpers['sAdo_OngenTrgStart']
    if (trigger['bytes']!=72 or trigger['sha256']!='4fdc889bb1697c19c8f386d72b80585ea07706d9f26b328389766bec96f0f989'
            or trigger['relocations']!={48:(10,0,4,0x8001383C)}):reject('changed trigger helper')
    return dict(helpers=helpers,constants=constants,source_initializer=initializer,
        hit=dict(idle_only=True,playback_speed=.25,stop_at_endpoint=True,clear_initial_pulse=False),
        trigger=dict(sound_word=sound,excluded_states=[13,14,15,12],native_excluded_states=[5,6,13,15],
            state_offset=0x3C,switch_offset=0x12D,switch_value='nonzero',position_offset=8,runtime_installed=False))


def discover_hit(source, vtable_name, vtable_at, functions):
    """Convert the complete struck-animation category, including its trigger.

    Models, motions, and sound words are source parameters. No item identities
    or model names select this path, and no part of the move callback is dropped.
    """
    from v3_furniture_pipeline import ReviewRequired
    def reject(reason):raise ReviewRequired('custom callbacks: hit rig '+reason)
    if set(functions)!={'create','move','draw'}:reject('changed lifecycle slots')
    module=u32(source.rel,0);create=functions['create'];move=functions['move']
    def pair(role,hi,lo,section):
        ref=functions[role]['relocations'].get(hi)
        if ref is None or ref[:3]!=(6,module,section):reject('missing paired resource')
        return ref[3],{hi:ref,lo:(4,module,section,ref[3])}
    bones,a=pair('create',0x0A,0x12,5)
    motion,b=pair('create',0x22,0x2E,5)
    repeat,c=pair('create',0x3E,0x46,5)
    zero,d=pair('create',0x5A,0x62,4)
    if repeat!=motion:reject('constructor changes motion')
    helpers=source.checked_callback_code(create,132,
        '9f229825fdc6bc4d5741e0b27cfdfcd047b1bd836fdb31174413d9841a8cd6d7',a|b|c|d,
        {0x38:(0x8D4,'cKF_SkeletonInfo_R_ct'),0x4C:(0x934,'cKF_SkeletonInfo_R_init_standard_stop'),
         0x54:(0xE54,'cKF_SkeletonInfo_R_play')},'hit rig constructor')
    checked_stop_initializer(source)
    expected={};constants={}
    for hi,lo,label,value in ((0x2E,0x36,'zero',0),(0x4A,0x4E,'speed',.5),
            (0x92,0x9A,'first_frame',1),(0xA6,0xAA,'speed',.5),
            (0xF2,0xFA,'first_frame',1),(0x106,0x10A,'speed',.5)):
        at,refs=pair('move',hi,lo,4);expected.update(refs)
        base,n=source.sections[4];raw=source.rel[base+at:base+at+4]
        if not 0<=at<=n-4 or raw!=struct.pack('>f',value):reject('changed animation constant')
        if label in constants and constants[label]['offset']!=at:reject('ambiguous animation constant')
        constants[label]=dict(section=4,offset=at,hex=raw.hex(),value=value)
    if constants['zero']['offset']!=zero:reject('changed initial zero speed')
    raw,_=source.function(move['offset'])
    if len(raw)!=296:reject('unknown move implementation')
    sound=struct.unpack_from('>H',raw,0x8A)[0]
    if (struct.unpack_from('>H',raw,0xEA)[0]!=sound or sound&0x80 or
            (sound&0x7FFF)>>8 not in (1,4)):reject('inconsistent or unsupported sound word')
    helpers.update(source.checked_callback_code(move,296,
        '794e1c2365eda333908e60479b6320c1dde5672e5e7f1546ef56062772be78d3',expected,
        {0x20:(0xE54,'cKF_SkeletonInfo_R_play'),0x44:(0xE54,'cKF_SkeletonInfo_R_play'),
         0x8C:(0x2BDDE8,'sAdo_OngenTrgStart'),0xA0:(0xE54,'cKF_SkeletonInfo_R_play'),
         0xEC:(0x2BDDE8,'sAdo_OngenTrgStart'),0x100:(0xE54,'cKF_SkeletonInfo_R_play')},
        'hit rig movement',{0x8A:sound,0xEA:sound},internal_branches=True))
    helpers.update(source.checked_callback_code(functions['draw'],*STORAGE_CODE['draw'],
        {0x10:(10,0,4,0x8009AED0),0x78:(10,0,4,0x8009AF1C)},
        {0x50:(0x9D214,'_Matrix_to_Mtx_new'),0x70:(0x1578,'cKF_Si3_draw_R_SV')},'hit rig drawing'))
    rig=skeleton(source,bones);motion=animation(source,motion,joints=rig['joints'])
    descriptor=model_descriptor(rig,kind='animated-room-model')
    return descriptor['models'],{},dict(category=HIT_CATEGORY,vtable_symbol=vtable_name,
        vtable_offset=vtable_at,functions=functions,helpers=helpers,constants=constants,
        skeleton=rig,animation=motion,joint_models=descriptor['joint_models'],
        trigger=dict(sound_word=sound,excluded_states=[13,14,15,12],
            native_excluded_states=[5,6,13,15],state_offset=0x3C,switch_offset=0x12D,
            switch_value='nonzero',position_offset=8,runtime_installed=False),
        constructor=dict(mode='stop',initial_play_before_speed=True,clears_switch_pulse=True),
        runtime_installed=False)


def discover(source, vtable_name, vtable_at, functions, index):
    from v3_furniture_pipeline import ReviewRequired
    def reject(reason): raise ReviewRequired('custom callbacks: indexed rig '+reason)
    if set(functions) != set(CODE): reject('incomplete lifecycle')
    for role, (size, digest) in CODE.items():
        raw, current = source.function(functions[role]['offset'])
        if current != functions[role] or len(raw) != size or sha256(raw) != digest:
            reject('changed complete '+role+' implementation')
    create = functions['create']; raw, _ = source.function(create['offset'])
    origin = -struct.unpack_from('>h', raw, 0x26)[0]
    count = 8  # Verified rlwinm at +34 selects (index-origin)&7, then scales by four.
    if u32(raw, 0x34) != 0x541E16FA or not origin <= index < origin+count:
        reject('selector index escapes complete table')
    rel = create['relocations']; tables = {}
    for role, high, low in (('skeleton',0x1E,0x32),('animation',0x22,0x2E)):
        pointer = rel.get(high)
        if (pointer is None or pointer[:3] != (6,1,5) or
                rel.get(low) != (4,1,5,pointer[3])): reject('changed paired table binding')
        name, at, n = source.containing(pointer[3], exact=True)
        pointers = source.pointers(at, n)
        if n != count*4 or any(source.data[at:at+n]) or set(pointers) != set(range(at,at+n,4)):
            reject('incomplete rig table')
        tables[role] = dict(symbol=name,offset=at,bytes=n,targets=list(pointers.values()))
    # The instruction hashes do not bind relocated addresses. Check all actual
    # code dependencies separately, including floats and no-op joint callbacks.
    expected = {
        'create': {16:(10,0,4,0x8009AED0),144:(10,0,4,0x8009AF1C),
            30:(6,1,5,tables['skeleton']['offset']),50:(4,1,5,tables['skeleton']['offset']),
            34:(6,1,5,tables['animation']['offset']),46:(4,1,5,tables['animation']['offset']),
            98:(6,1,4,0xC104),106:(4,1,4,0xC104),
            102:(6,1,4,0xC118),110:(4,1,4,0xC118)},
        'move': {30:(6,1,4,0xC1B4),34:(4,1,4,0xC1B4),46:(6,1,4,0xC1B4),54:(4,1,4,0xC1B4),
            70:(6,1,4,0xC118),74:(4,1,4,0xC118),98:(6,1,4,0xC140),102:(4,1,4,0xC140),
            142:(6,1,4,0xC140),146:(4,1,4,0xC140)},
        'draw': {16:(10,0,4,0x8009AED0),128:(10,0,4,0x8009AF1C)}, 'destroy': {},
    }
    callbacks = []
    for high,low in ((86,98),(90,102)):
        r = functions['draw']['relocations'].get(high)
        if r is None or r[:3] != (6,1,1): reject('missing joint callback')
        raw, receipt = source.function(r[3])
        if raw != bytes.fromhex('386000014e800020') or receipt['relocations']:
            reject('joint callback has effects')
        callbacks.append(receipt)
        expected['draw'].update({high:r,low:(4,1,1,r[3])})
    for role, relocations in expected.items():
        if functions[role]['relocations'] != relocations: reject('changed '+role+' dependencies')
    helpers = {}
    calls = {'create':{0x4C:(0x8D4,'cKF_SkeletonInfo_R_ct'),
                      0x5C:(0xA24,'cKF_SkeletonInfo_R_init_standard_repeat'),0x88:(0xE54,'cKF_SkeletonInfo_R_play')},
             'move':{0xBC:(0xE54,'cKF_SkeletonInfo_R_play')},
             'draw':{0x50:(0x9D214,'_Matrix_to_Mtx_new'),0x78:(0x1578,'cKF_Si3_draw_R_SV')}}
    for role, rows in calls.items():
        raw, _ = source.function(functions[role]['offset'])
        for at,(target,name) in rows.items():
            word = u32(raw,at); delta = word & 0x3FFFFFC
            if delta & 0x2000000: delta -= 0x4000000
            _, helper = source.function(target)
            if (word & 0xFC000003 != 0x48000001 or functions[role]['offset']+at+delta != target
                    or helper['symbol'] != name): reject('changed native-compatible helper')
            helpers[name] = helper
    constants = {}
    for name,at,value in (('initial_speed',0xC104,0),('idle_speed',0xC118,.5),
                          ('approach_step',0xC140,.01),('switch_speed',0xC1B4,1.25)):
        data = source.rel[source.sections[4][0]+at:source.sections[4][0]+at+4]
        if data != struct.pack('>f',value): reject('changed speed constant')
        constants[name] = dict(section=4,offset=at,hex=data.hex())
    selected = index-origin
    rig = skeleton(source,tables['skeleton']['targets'][selected])
    motion = animation(source,tables['animation']['targets'][selected],joints=rig['joints'])
    descriptor = model_descriptor(rig,kind='animated-room-model')
    return descriptor['models'], {}, dict(category=CATEGORY,vtable_symbol=vtable_name,
        vtable_offset=vtable_at,functions=functions,helpers=helpers,joint_callbacks=callbacks,
        tables=tables,index_origin=origin,entries=count,selected_index=selected,
        constants=constants,skeleton=rig,animation=motion,joint_models=descriptor['joint_models'],
        runtime_installed=False)


def selector_table(source, functions, role, high, low, count, section=5):
    """Resolve a complete identity-indexed pointer table, never a model list."""
    from v3_furniture_pipeline import ReviewRequired
    relocations=functions[role]['relocations'];module=u32(source.rel,0)
    pointer=relocations.get(high)
    if (pointer is None or pointer[:3]!=(6,module,section)
            or relocations.get(low)!=(4,module,section,pointer[3])):
        raise ReviewRequired('custom callbacks: indexed rig changed paired table binding')
    name,at,n=source.containing(pointer[3],exact=True)
    pointers=source.pointers(at,n)
    if n!=count*4 or any(source.data[at:at+n]) or set(pointers)!=set(range(at,at+n,4)):
        raise ReviewRequired('custom callbacks: indexed rig incomplete selector table')
    return dict(symbol=name,offset=at,bytes=n,targets=[pointers[p] for p in range(at,at+n,4)])


def discover_fixed(source, vtable_name, vtable_at, functions):
    """Prepare full fixed rigs without treating arbitrary move code as ported.

    Constructor and drawing implementations establish the complete resources.
    Every remaining callback stays attached to the descriptor as pending code.
    No item IDs or artwork names participate in discovery.
    """
    from v3_furniture_pipeline import ReviewRequired
    def reject(reason):raise ReviewRequired('custom callbacks: fixed rig '+reason)
    if not {'create','move','draw'} <= functions.keys() or set(functions)-{'create','move','draw','destroy'}:
        reject('incomplete lifecycle')
    module=u32(source.rel,0);create=functions['create'];draw=functions['draw']
    def target(role,high,section):
        pointer=functions[role]['relocations'].get(high)
        if pointer is None or pointer[:3]!=(6,module,section):reject('missing paired resource')
        return pointer[3]
    def pair(high,low,address,section):return {high:(6,module,section,address),low:(4,module,section,address)}
    bones=target('create',0x0E,5);motion=target('create',0x16,5)
    speed=target('create',0x56,4);base,n=source.sections[4]
    if not 0<=speed<=n-4:reject('speed escapes source section')
    raw_speed=source.rel[base+speed:base+speed+4];value=struct.unpack('>f',raw_speed)[0]
    if not math.isfinite(value) or value<0:reject('invalid initial speed')
    raw,_=source.function(create['offset'])
    if len(raw)!=116:reject('unknown constructor')
    word=u32(raw,0x48);delta=word&0x3FFFFFC
    if delta&0x2000000:delta-=0x4000000
    init=create['offset']+0x48+delta
    modes={0x934:('stop','cKF_SkeletonInfo_R_init_standard_stop'),
           0xA24:('repeat','cKF_SkeletonInfo_R_init_standard_repeat')}
    if word&0xFC000003!=0x48000001 or init not in modes:reject('unsupported animation initializer')
    mode,helper=modes[init]
    expected=pair(0x0E,0x1A,bones,5)|pair(0x16,0x2A,motion,5)|pair(0x3A,0x42,motion,5)|pair(0x56,0x5A,speed,4)
    helpers=source.checked_callback_code(create,116,
        '455f9460b16f657d595ebc17273179ebb0d656711392835051bc2dd92be0eb23',expected,
        {0x34:(0x8D4,'cKF_SkeletonInfo_R_ct'),0x48:(init,helper),0x50:(0xE54,'cKF_SkeletonInfo_R_play')},'fixed rig')
    clock={};callbacks=[]
    if draw['bytes']==140:
        helpers.update(source.checked_callback_code(draw,*STORAGE_CODE['draw'],
            {0x10:(10,0,4,0x8009AED0),0x78:(10,0,4,0x8009AF1C)},
            {0x50:(0x9D214,'_Matrix_to_Mtx_new'),0x70:(0x1578,'cKF_Si3_draw_R_SV')},'fixed rig drawing'))
    elif draw['bytes']==80:
        expected={}
        for role,high,low,digest,length in (
                ('before',0x0E,0x26,'99f04fbcf9b117cc9cb4f790d376b2d806c2902868fce4a96d49c645f3d33dfd',84),
                ('after',0x16,0x1A,'2bf7a94759a252fd0d2af700ff876c19ab13998fb28ac5b0db3c70cdbc9ef8d6',8)):
            at=target('draw',high,1);code,receipt=source.function(at)
            relocations=({0x0A:(6,module,6,0xBC40),0x12:(4,module,6,0xBC40),
                          0x32:(6,module,6,0xBC40),0x3A:(4,module,6,0xBC40)} if role=='before' else {})
            if len(code)!=length or sha256(code)!=digest or receipt['relocations']!=relocations:
                reject('changed clock-joint behaviour')
            expected.update(pair(high,low,at,1));callbacks.append(dict(role=role,**receipt))
        helpers.update(source.checked_callback_code(draw,80,
            'e6b24d256d78fad6e7fa15a1114b82cb4ad3f570208a8748ee65489c8980319b',expected,
            {0x3C:(0x1578,'cKF_Si3_draw_R_SV')},'fixed clock drawing'))
        common=re.findall(r'^common_data = \.bss:0x([0-9A-Fa-f]+);[^\n]* size:0x([0-9A-Fa-f]+) ',source.symbols,re.M)
        if [(int(at,16),int(n,16)) for at,n in common]!=[(0xBC40,0x2DC00)]:reject('changed source clock owner')
        clock=dict(common_symbol='common_data',hour_joint=3,minute_joint=4,
                   hour_offset=0x2612A,minute_offset=0x26128,axis='z',operation='subtract')
    else:reject('drawing needs additional resource/effect discovery')
    rig=skeleton(source,bones);animation_record=animation(source,motion,joints=rig['joints'])
    if clock and rig['joints']<=4:reject('missing clock-hand joints')
    descriptor=model_descriptor(rig,kind='animated-room-model')
    category=FIXED_CATEGORY;pending=[role for role in ('move','destroy') if role in functions]
    runtime_contract={}
    if clock and mode=='repeat' and raw_speed==struct.pack('>f',.5) and set(functions)==set(CLOCK_CODE):
        # A fixed resource binding can use the existing clock runtime once all
        # remaining behaviour is proved identical. Resource preparation alone
        # never grants that permission.
        helpers.update(source.checked_callback_code(functions['move'],*CLOCK_CODE['move'],{},
            {0x10:(0xE54,'cKF_SkeletonInfo_R_play')},'fixed looping clock'))
        source.checked_callback_code(functions['destroy'],*CLOCK_CODE['destroy'],{},{},'fixed looping clock')
        init_raw,init_receipt=source.function(0xA24)
        expected={0x0A:(6,module,4,0),0x0E:(6,module,4,0x20),0x1E:(4,module,4,0),
                  0x2E:(6,module,4,0x30),0x36:(4,module,4,0x20),0x3E:(4,module,4,0x30),
                  0x42:(6,module,4,4),0x4E:(4,module,4,4)}
        constants=((0,bytes.fromhex('3f800000')),(4,bytes(4)),
                   (0x20,bytes.fromhex('4330000080000000')),(0x30,bytes.fromhex('3f000000')))
        if (len(init_raw)!=124 or sha256(init_raw)!='5c600ed1925e67be3f776252b5cb4617389ee5612133e188505d05ba28e3bd7c' or
                init_receipt['relocations']!=expected or
                any(source.rel[base+at:base+at+len(value)]!=value for at,value in constants)):
            reject('changed source repeat initialization speed')
        # Source init already supplies .5 before its initial play. The N64
        # initializer supplies 1, so the existing runtime explicitly assigns
        # .5 before playback. Both evaluate the same first frame and then loop.
        category=CLOCK_CATEGORY;pending=[]
        runtime_contract=dict(binding='fixed',category=CLOCK_CATEGORY,
            source_initial_speed=.5,source_move_steps_per_native_update=2,
            source_initializer=init_receipt)
    result=dict(category=category,vtable_symbol=vtable_name,
        vtable_offset=vtable_at,functions=functions,helpers=helpers,joint_callbacks=callbacks,
        constructor=dict(mode=mode,initial_speed=dict(section=4,offset=speed,hex=raw_speed.hex(),value=value),
                         initial_play_before_speed=True),
        **({'clock':clock} if clock else {}),skeleton=rig,animation=animation_record,
        joint_models=descriptor['joint_models'],runtime_installed=False,
        pending_callbacks=pending,**({'runtime_contract':runtime_contract} if runtime_contract else {}),
        resource_scope='complete fixed looping clock' if runtime_contract else
            'complete constructor rig; callback gameplay and spawned effects remain pending')
    if category==FIXED_CATEGORY:
        idle_hit=discover_idle_hit(source,result)
        if idle_hit:
            result['helpers'].update(idle_hit.pop('helpers'))
            result.update(category=HIT_CATEGORY,pending_callbacks=[],**idle_hit,
                resource_scope='complete idle-only stopped-hit rig')
            result['constructor']['clears_switch_pulse']=False
            return descriptor['models'],{},result
        from v3_furniture_motion import discover
        rolling=discover(source,result)
        if rolling:
            result.update(category=ROLLING_CATEGORY,rolling=rolling,pending_callbacks=[],
                resource_scope='complete displacement-driven rolling rig')
    return descriptor['models'],{},result


def discover_clock(source, vtable_name, vtable_at, functions, index):
    """Retain an indexed looping skeleton, constant palette, and live clock hands."""
    from v3_furniture_pipeline import ReviewRequired
    def reject(reason):raise ReviewRequired('custom callbacks: indexed clock rig '+reason)
    if set(functions)!=set(CLOCK_CODE):reject('incomplete lifecycle')
    create=functions['create'];draw=functions['draw']
    raw,_=source.function(create['offset']);draw_raw,_=source.function(draw['offset'])
    if len(raw)!=CLOCK_CODE['create'][0] or len(draw_raw)!=CLOCK_CODE['draw'][0]:
        reject('changed selector implementation')
    origin=-struct.unpack_from('>h',raw,0x26)[0];count=16
    if (u32(raw,0x34)!=0x541E16BA or u32(draw_raw,0x30)!=0x540016BA
            or raw[0x26:0x28]!=draw_raw[0x26:0x28] or not origin<=index<origin+count):
        reject('selector escapes the complete tables')
    tables={role:selector_table(source,functions,owner,hi,lo,count) for role,owner,hi,lo in (
        ('skeleton','create',0x1E,0x32),('animation','create',0x22,0x2E),('palette','draw',0x22,0x36))}
    module=u32(source.rel,0)
    speed_pointer=create['relocations'].get(0x62)
    if speed_pointer is None or speed_pointer[:3]!=(6,module,4):reject('missing repeat speed')
    speed_at=speed_pointer[3];base,size=source.sections[4]
    if not 0<=speed_at<=size-4 or source.rel[base+speed_at:base+speed_at+4]!=struct.pack('>f',.5):
        reject('changed repeat speed')
    def pair(high,low,target,section=5):return {high:(6,module,section,target),low:(4,module,section,target)}
    expected={
        'create':{0x10:(10,0,4,0x8009AED4),0x78:(10,0,4,0x8009AF20)} |
            pair(0x1E,0x32,tables['skeleton']['offset']) | pair(0x22,0x2E,tables['animation']['offset']) |
            pair(0x62,0x6A,speed_at,4),
        'move':{},'destroy':{},
        'draw':{0x10:(10,0,4,0x8009AEC8),0xB4:(10,0,4,0x8009AF14)} |
            pair(0x22,0x36,tables['palette']['offset']),
    }
    callbacks=[]
    for role,high,low,digest,length in (
            ('before',0x72,0x82,'99f04fbcf9b117cc9cb4f790d376b2d806c2902868fce4a96d49c645f3d33dfd',84),
            ('after',0x7A,0x8A,'2bf7a94759a252fd0d2af700ff876c19ab13998fb28ac5b0db3c70cdbc9ef8d6',8)):
        pointer=draw['relocations'].get(high)
        if pointer is None or pointer[:3]!=(6,module,1):reject('missing joint callback')
        code,receipt=source.function(pointer[3])
        relocations=({0x0A:(6,module,6,0xBC40),0x12:(4,module,6,0xBC40),
                      0x32:(6,module,6,0xBC40),0x3A:(4,module,6,0xBC40)} if role=='before' else {})
        if len(code)!=length or sha256(code)!=digest or receipt['relocations']!=relocations:
            reject('changed clock-joint behaviour')
        callbacks.append(dict(role=role,**receipt));expected['draw'].update(pair(high,low,pointer[3],1))
    common=re.findall(r'^common_data = \.bss:0x([0-9A-Fa-f]+);[^\n]* size:0x([0-9A-Fa-f]+) ',source.symbols,re.M)
    if [(int(at,16),int(n,16)) for at,n in common]!=[(0xBC40,0x2DC00)]:
        reject('changed source clock owner')
    calls={'create':{0x4C:(0x8D4,'cKF_SkeletonInfo_R_ct'),
                     0x5C:(0xA24,'cKF_SkeletonInfo_R_init_standard_repeat'),0x70:(0xE54,'cKF_SkeletonInfo_R_play')},
           'move':{0x10:(0xE54,'cKF_SkeletonInfo_R_play')},
           'draw':{0x68:(0x9D214,'_Matrix_to_Mtx_new'),0xAC:(0x1578,'cKF_Si3_draw_R_SV')},'destroy':{}}
    helpers={}
    for role,(length,digest) in CLOCK_CODE.items():
        helpers.update(source.checked_callback_code(functions[role],length,digest,expected[role],calls[role],
            'indexed clock rig',{0x26:(-origin)&65535} if role in ('create','draw') else {}))
    selected=index-origin
    rig=skeleton(source,tables['skeleton']['targets'][selected])
    if rig['joints']<=4:reject('missing clock-hand joints')
    motion=animation(source,tables['animation']['targets'][selected],joints=rig['joints'])
    palette=tables['palette']['targets'][selected];name,at,n=source.containing(palette,exact=True)
    if n!=32 or source.pointers(at,n):reject('incomplete constant palette')
    descriptor=model_descriptor(rig,kind='animated-room-model')
    return descriptor['models'],{0x08000000:palette},dict(category=CLOCK_CATEGORY,
        vtable_symbol=vtable_name,vtable_offset=vtable_at,functions=functions,helpers=helpers,
        joint_callbacks=callbacks,tables=tables,index_origin=origin,entries=count,selected_index=selected,
        constants=dict(repeat_speed=dict(section=4,offset=speed_at,hex='3f000000')),
        clock=dict(common_symbol='common_data',hour_joint=3,minute_joint=4,
                   hour_offset=0x2612A,minute_offset=0x26128,axis='z',operation='subtract'),
        palette=dict(symbol=name,donor_offset=at,bytes=n,source_sha256=sha256(source.data[at:at+n])),
        skeleton=rig,animation=motion,joint_models=descriptor['joint_models'],runtime_installed=False)


def discover_storage(source, vtable_name, vtable_at, functions):
    """Resolve complete stop-mode rigs controlled by the shared storage helper."""
    from v3_furniture_pipeline import ReviewRequired
    def reject(reason):raise ReviewRequired('custom callbacks: storage rig '+reason)
    if set(functions)!=set(STORAGE_CODE):reject('incomplete lifecycle')
    module=u32(source.rel,0)
    def target(role,high,section):
        pointer=functions[role]['relocations'].get(high)
        if pointer is None or pointer[:3]!=(6,module,section):reject('missing paired dependency')
        return pointer[3]
    def pair(high,low,address,section):return {high:(6,module,section,address),low:(4,module,section,address)}
    bones=target('create',0x0E,5);motion=target('create',0x16,5)
    constants={}
    for label,role,high in (('initial_speed','create',0x4E),('start_frame','move',0x2A),('end_frame','move',0x2E)):
        at=target(role,high,4);base,n=source.sections[4]
        if not 0<=at<=n-4:reject('float dependency escapes section')
        raw=source.rel[base+at:base+at+4];value=struct.unpack('>f',raw)[0]
        if not math.isfinite(value):reject('non-finite animation limit')
        constants[label]=dict(section=4,offset=at,hex=raw.hex(),value=value)
    if constants['initial_speed']['hex']!='00000000':reject('changed stopped initialization')
    common=target('move',0x0A,6)
    spans=re.findall(r'^common_data = \.bss:0x([0-9A-Fa-f]+);[^\n]* size:0x([0-9A-Fa-f]+) ',source.symbols,re.M)
    if [(int(at,16),int(n,16)) for at,n in spans]!=[(common,0x2DC00)]:reject('changed shared room owner')
    expected={
        'create':pair(0x0E,0x1A,bones,5)|pair(0x16,0x2A,motion,5)|pair(0x3A,0x42,motion,5)|
            pair(0x4E,0x56,constants['initial_speed']['offset'],4),
        'move':pair(0x0A,0x0E,common,6)|pair(0x2A,0x32,constants['start_frame']['offset'],4)|
            pair(0x2E,0x36,constants['end_frame']['offset'],4),
        'draw':{0x10:(10,0,4,0x8009AED0),0x78:(10,0,4,0x8009AF1C)},'destroy':{},
    }
    calls={'create':{0x34:(0x8D4,'cKF_SkeletonInfo_R_ct'),
                     0x48:(0x934,'cKF_SkeletonInfo_R_init_standard_stop'),0x5C:(0xE54,'cKF_SkeletonInfo_R_play')},
           'move':{},'draw':{0x50:(0x9D214,'_Matrix_to_Mtx_new'),0x70:(0x1578,'cKF_Si3_draw_R_SV')},'destroy':{}}
    helpers={}
    for role,(length,digest) in STORAGE_CODE.items():
        helpers.update(source.checked_callback_code(functions[role],length,digest,expected[role],calls[role],'storage rig'))
    rig=skeleton(source,bones);motion=animation(source,motion,joints=rig['joints'])
    if not 1<=constants['start_frame']['value']<constants['end_frame']['value']<=motion['duration']:
        reject('open/close limits escape complete motion')
    descriptor=model_descriptor(rig,kind='animated-room-model')
    return descriptor['models'],{},dict(category=STORAGE_CATEGORY,vtable_symbol=vtable_name,
        vtable_offset=vtable_at,functions=functions,helpers=helpers,constants=constants,
        room_callback=dict(common_symbol='common_data',common_offset=common,clip_offset=0x2608C,
                           callback_offset=0x34,nullable=True,animation_mode='stop'),
        skeleton=rig,animation=motion,joint_models=descriptor['joint_models'],runtime_installed=False)


def suffix(source, profile, model_offsets, *, start):
    """Pack the real skeleton and motion after the shared complete artwork."""
    adapter = profile.get('callback_adapter',{})
    if adapter.get('category') not in RESOURCE_CATEGORIES: return b'', {}
    roots = {root[1]:model_offsets[label] for label,root in profile['models'].items()}
    bones, rig = compile_skeleton(source,profile['skeleton'],roots,start=start)
    motion, animations = compile_animations(source,[adapter['animation']],start=start+len(bones))
    extra=b'';fields={}
    if adapter['category']==BILLBOARD_CATEGORY:
        scroll=adapter['scrolling'];sound=adapter['level_sound'];offset=start+len(bones)+len(motion)
        extra=struct.pack('>I4B4b4B',0x06000000+model_offsets[adapter['billboard']['model']],
            *(v for r in scroll['tiles'] for v in (r['width'],r['height'])),
            *(v for r in scroll['tiles'] for v in r['rate']),sound['source_sound_id'],
            bool(sound['excluded_states']),2,0)
        fields=dict(billboard_offset=offset,billboard_hex=extra.hex())
    return bones+motion+extra, dict(skeleton=rig,animations=animations,**fields,
        skeleton_offset=rig['header']['native_offset'],animation_offset=animations['headers'][0]['native_offset'],
        runtime_installed=False)


def estimated_suffix(source, profile, start):
    adapter = profile.get('callback_adapter',{})
    if adapter.get('category') not in RESOURCE_CATEGORIES: return 0
    bones = (profile['skeleton']['joint_table']['bytes']+8+15)&~15
    motion, _ = compile_animations(source,[adapter['animation']],start=start+bones)
    return bones+len(motion)+(16 if adapter['category']==BILLBOARD_CATEGORY else 0)
