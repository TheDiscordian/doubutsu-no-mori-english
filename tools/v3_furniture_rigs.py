"""Source-discovered indexed room rigs, retaining their complete behaviour.

This is a callback/asset category, not an item list. Preparing a rig does not
install its lifecycle callbacks or make its parent selectable.
"""
import struct

from aflib import sha256, u32
from v3_keyframes import animation, skeleton, model_descriptor, compile_skeleton, compile_animations

CATEGORY = 'indexed-switch-rig'
CODE = {
    'create': (164, '2a86d61bc9aaf4a0a6479fe97a7f0d5dfe3dc42f9eea663eeb3fd1b8cbc35733'),
    'move': (208, '4b36894add16ecf872c1bfdcbeed2331519049fffd5b3d1d1d5db533f7c68d89'),
    'draw': (148, 'a0546e1e4e5893a157857ce34244a4183e8991928ae34ce585f79b3da0d052bb'),
    'destroy': (4, 'f332ea5b5437103cbb6f1508679da89eec9288ad775c96c439a17fccabe3de8e'),
}


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


def suffix(source, profile, model_offsets, *, start):
    """Pack the real skeleton and motion after the shared complete artwork."""
    adapter = profile.get('callback_adapter',{})
    if adapter.get('category') != CATEGORY: return b'', {}
    roots = {root[1]:model_offsets[label] for label,root in profile['models'].items()}
    bones, rig = compile_skeleton(source,profile['skeleton'],roots,start=start)
    motion, animations = compile_animations(source,[adapter['animation']],start=start+len(bones))
    return bones+motion, dict(skeleton=rig,animations=animations,
        skeleton_offset=rig['header']['native_offset'],animation_offset=animations['headers'][0]['native_offset'],
        runtime_installed=False)


def estimated_suffix(source, profile, start):
    adapter = profile.get('callback_adapter',{})
    if adapter.get('category') != CATEGORY: return 0
    bones = (profile['skeleton']['joint_table']['bytes']+8+15)&~15
    motion, _ = compile_animations(source,[adapter['animation']],start=start+bones)
    return bones+len(motion)
