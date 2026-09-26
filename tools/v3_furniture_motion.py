"""Complete source rolling motion and checked native furniture-state mapping."""
import struct
from aflib import by_vrom,sha256,u32

CATEGORY='contact-rolling-keyframe-rig'
PUSH_STATES=(9,11,14,1)
PULL_STATES=(10,12,2)
OWNER,OWNER_RAM=0x82D7F0,0x80936710
NATIVE_BLOCKS=(
    ('state_dispatch_table',0x8094D0F4,64,'7a92b223bba1da2db031c25cf15cd144efb9dd44254a00d58498a5e6cceebb5f'),
    ('wait_state_transitions',0x809442CC,140,'a247eb1d17d6035a4a23e75ed315174176c7abde3d894494b0618fd52f22866e'),
    ('push_pull_movement',0x80944080,588,'f1292b5bb437e83f3354e4d4305c464d76b0b539a52bb5152544cfc6fa9bc540'),
    ('state_dispatch',0x80944EA4,48,'961535d000978cd945e3984f59d89ff8007a84e150101eaf02eb1fb27ea47cc6'),
    ('position_copy_before_callback',0x80944ED4,48,'25e953de3851e431b4674da0fd99af8d394b74072c0830f89f75b2ce87db98dd'),
    ('move_callback_dispatch',0x80944F78,88,'88a82e1c648c3e672dd22378e8ab8bc72c095beee1579de0c142c3f479e2ae4d'),
)

def native_contract(image):
    from v3_furniture_contact import native_contract as contact_contract
    contract=contact_contract(image);owner=by_vrom(image)[OWNER].extract(image)
    blocks=[]
    for name,at,n,digest in NATIVE_BLOCKS:
        if sha256(owner[at-OWNER_RAM:at-OWNER_RAM+n])!=digest:
            raise ValueError('Changed native furniture motion dependency: '+name)
        blocks.append(dict(name=name,address=at,bytes=n,sha256=digest))
    # libultra lives in boot, below the main-code image.
    root=by_vrom(image)[0x1060].extract(image)
    raw=root[0x80033470-0x80025C60:0x80033478-0x80025C60]
    if raw!=bytes.fromhex('03e0000846006004'):
        raise ValueError('Changed native square-root implementation')
    blocks.append(dict(name='sqrtf',address=0x80033470,bytes=8,sha256=sha256(raw)))
    return dict(blocks=blocks,contact=contract,push_states=list(PUSH_STATES),pull_states=list(PULL_STATES),
        position_offset=8,previous_xz_offsets=[0x204,0x208],
        native_previous_position_unusable=True,source_steps_per_native_update=2)

def discover(source,adapter):
    """Recognise behaviour through full callbacks, never an item identity."""
    functions=adapter['functions'];move=functions.get('move',{})
    if move.get('bytes')!=612:return None
    def reject(reason):raise ValueError('Rolling rig: '+reason)
    if (set(functions)!={'create','move','draw'} or adapter['constructor']['mode']!='repeat' or
            adapter['constructor']['initial_speed']['hex']!='00000000' or
            not adapter['constructor']['initial_play_before_speed']):reject('changed complete lifecycle')
    raw,receipt=source.function(move['offset']);module=u32(source.rel,0)
    init_raw,initializer=source.function(0xA24)
    refs={0x0A:(6,module,4,0),0x0E:(6,module,4,0x20),0x1E:(4,module,4,0),
        0x2E:(6,module,4,0x30),0x36:(4,module,4,0x20),0x3E:(4,module,4,0x30),
        0x42:(6,module,4,4),0x4E:(4,module,4,4)}
    if (len(init_raw)!=124 or sha256(init_raw)!='5c600ed1925e67be3f776252b5cb4617389ee5612133e188505d05ba28e3bd7c'
            or initializer['relocations']!=refs):reject('changed complete repeat initializer')
    motion=adapter['animation']['header']['donor_offset']
    refs={0x10:(10,0,4,0x8009AED4),0x250:(10,0,4,0x8009AF20)}
    groups=((4,49736,((0x36,0x3E),)),(4,49416,((0x3A,0x42),)),(4,49432,((0x46,0x4E),)),
        (4,49408,((0xAA,0xB2),(0x116,0x126),(0x18A,0x192),(0x1F6,0x206))),
        (4,49424,((0xC2,0xCE),(0x106,0x10A),(0x1A2,0x1AE),(0x1E6,0x1EA))),
        (4,49412,((0x13A,0x13E),(0x21A,0x21E),(0x22A,0x22E),(0x23A,0x23E))),
        (5,motion,((0xAE,0xC6),(0xF2,0xFA),(0x18E,0x1A6),(0x1D2,0x1DA))))
    for section,at,pairs in groups:
        for hi,lo in pairs:refs.update({hi:(6,module,section,at),lo:(4,module,section,at)})
    if receipt['relocations']!=refs or sha256(raw)!='6e2f6c3932b6d42137f72e300ada90552015e3a33ab3d792622b1b70a38de5ed':
        reject('changed full motion code or resource bindings')
    helpers={}
    for loc,name,digest in ((0x1C,'aMR_GetContactInfoLayer1','db0a6978f69d604ba28b26684d101066aebdeb796c8c1972909e1f1062de4006'),
        (0x28,'fTMny_GetSpeed','86324309a9f33bbcd0055fcd7ea499d8ac4400e33caf5ebd297105edb1b0dcab'),
        (0x248,'cKF_SkeletonInfo_R_play','4d3b0e1c9c715419e1953549ddb4bf9da2824bfdf37e69f4f92ba483a0764425')):
        word=u32(raw,loc);delta=word&0x3FFFFFC
        if delta&0x2000000:delta-=0x4000000
        _,helper=source.function(move['offset']+loc+delta)
        if word&0xFC000003!=0x48000001 or helper['symbol']!=name or helper['sha256']!=digest:
            reject('changed complete motion helper')
        helpers[name]=helper
    expected_speed={}
    for at,hi,lo in ((49412,6,10),(49412,50,58),(49412,90,98),(49600,118,122),(49608,126,138)):
        expected_speed.update({hi:(6,module,4,at),lo:(4,module,4,at)})
    if (helpers['fTMny_GetSpeed']['relocations']!=expected_speed or
            helpers['aMR_GetContactInfoLayer1']['relocations']!={2:(6,module,6,48192),6:(4,module,6,48192)}):
        reject('changed speed/contact dependencies')
    constants={0:'3f800000',4:'00000000',0x20:'4330000080000000',0x30:'3f000000',
        49408:'3f800000',49412:'00000000',49416:'3dcccccd',49424:'4330000080000000',
        49432:'3f000000',49736:'3fc66666',49600:'3fe0000000000000',49608:'4008000000000000'}
    for at,value in constants.items():
        raw=bytes.fromhex(value);base,size=source.sections[4]
        if at+len(raw)>size or source.rel[base+at:base+at+len(raw)]!=raw:reject('changed motion constant')
    return dict(category=CATEGORY,functions=functions,helpers=helpers,source_initializer=initializer,
        constants={str(at):value for at,value in constants.items()},source_push_states=[1,2,3,4],
        source_pull_states=[5,6,7],native_push_states=list(PUSH_STATES),native_pull_states=list(PULL_STATES),
        source_left=3,source_right=1,contact_direction_offset=0x28,
        duration=adapter['animation']['duration'],initial_speed=0.5,initial_frame=1.5,
        displacement_divisor=1.55,minimum_motion=0.1,source_speed_scale=0.5,
        source_steps_per_native_update=2,movement_sound_required=True)
