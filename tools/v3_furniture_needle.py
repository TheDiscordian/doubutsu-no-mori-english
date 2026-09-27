"""Source-bound parent-sensitive needle motion, pending native carrying support.

This contract is not an installable lifecycle. In particular, a compiled needle
callback is not a substitute for the donor's moving-parent registration/rendering.
"""
import json
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256

# Complete instruction and relocation identities bind local calls as well as
# external references. No item-ID dispatch is used to recognise this behaviour.
BLOCKS=(
    (0x2BFB60,132,'461f230c628de966d1c2c11f3f0e0a190ad885aea88b8bb62f6c5b0b76969b51','5d87627225e383fbc05e481fd3048473dce6d7ef3a2bb0f3a599767dd6dc913c'),
    (0x2BFBE4,264,'960307bfd8f7dd3f1aac005ffc6baec6191985753e7d69eb6144493a022881f5','e7ae01e2bc90b15d29fbc4bbbfd6f11bc990a4131eeede9ea03393ed41c60f6a'),
    (0x2BFCEC,456,'39dff0f906c0e52d325bc290959d1adc2cdf6d65afb03d736a21832dd875000f','dac83218a1c0da6b7552b715c4960781411bd5a616fc2dac84c33b3ce798fc9f'),
    (0x2BFEB4,200,'078e2f37442d1beb9fea4533eef3b5ac535097b5c23f8f20ece50da101df553f','c963c09d7e1a1a67192a3c71362931bead059ad709e7571f031f1b89e5212457'),
    (0x2BFF7C,8,'2bf7a94759a252fd0d2af700ff876c19ab13998fb28ac5b0db3c70cdbc9ef8d6','4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945'),
    (0x2BFF84,148,'3dcbf5da1a240195f7c46203c6aa5dc1dd74154c926eff0f9f98ee4fc2268e5e','7ebfd4d8345d7e4049eb1e8b9e34cc90879faf300ddc7d8e7156e5ed8d44fdc7'),
    (0x4A930,84,'93582f42865f358805756d645e164741a4387c76b89e9f6d15b4eb3593578c90','866141a47f53e9bbb7f0442728036b6f609782b5e2727ac245877a6e30b073aa'),
    (0x4AFF0,228,'359dc44aa01a58167db714cebdf511184f871bbd151298261ddb220ad2417580','f6c056a7e924624907461bfac1590e2bd88057eb2a695ccfd348709a075ec12e'),
    (0x8D4,92,'de6473013149427e5a7318e4abe4ed2fda98d1544e8936be16ef135e107d6886','77d702970e25ebe130b2a406475974e2e20548a25cdffcd1385a4d28899ab5fc'),
    (0x934,124,'8045cfda172f82aae9f38054c5e7844b87a7f3428bfc612252eff8e75435efa4','8a12d73effd1e9616526c1f48afdaf9b9edf91c89c224db2d35f0b9e179800d7'),
    (0xE54,936,'4d3b0e1c9c715419e1953549ddb4bf9da2824bfdf37e69f4f92ba483a0764425','d044984c1845d6f289a6a4ac6cb765ea0ad3252949b4fa1517ab138b2f25a3de'),
    (0x103BF8,104,'64b45a3de3487f0074da5a40d98e556abca64f22aaabd6215fddf6d10e39929b','0cda855d265230b6c8260b51ce7070da60892772b85dcd9244fb5a8cc30ac58e'),
    (0x103C60,120,'d7f16d629f2e96ff2d04e1192e1c0397673ca1d736d57065806474e978ed8ffa','0cda855d265230b6c8260b51ce7070da60892772b85dcd9244fb5a8cc30ac58e'),
    (0x10C1B8,304,'f33c79dcb021ba91025a251482d0930436fc2b66909eca15f6dfbad474bcc876','602d2fbe8fcf52df5bcaaf0499b682ea87def6f58610f359e55ac5bae38955c3'),
)
CONSTANTS={0xC104:'00000000',0xC110:'4330000080000000',0xC134:'42340000',
    0xC138:'c2340000',0xC13C:'3e4ccccd',0xC140:'3c23d70a',0xC144:'3e99999a',
    0xC148:'42c80000',0xC14C:'38d1b717',0xC150:'4622f983',0xC154:'3c8efa35',
    0x13E0:'38000100',0x13E8:'4330000080000000',0x13F0:'00000000'}


def source_contract(source,profile):
    adapter=profile.get('callback_adapter',{})
    if adapter.get('joint_features',{}).get('mode')!='parent-relative-needle':return None
    if (adapter['category']!='joint-callback-rig-assets' or
            adapter['joint_features']!=dict(mode='parent-relative-needle',joint=3,axis='y',operation='subtract') or
            adapter['constructor']['mode']!='stop' or profile['contact_action'] or profile['interaction_flags']):
        raise ValueError('Changed parent-sensitive needle profile')
    checked={}
    for at,size,digest,relocations in BLOCKS:
        raw,row=source.function(at)
        if (len(raw)!=size or sha256(raw)!=digest or
                sha256(json.dumps(sorted(row['relocations'].items()),separators=(',',':')).encode())!=relocations):
            raise ValueError('Changed complete needle dependency: '+row['symbol'])
        checked[row['symbol']]=row
    for role,name in (('create','fIJHOUI_ct'),('move','fIJHOUI_mv'),('draw','fIJHOUI_dw')):
        if any(adapter['functions'][role][k]!=checked[name][k] for k in ('offset','bytes','sha256','relocations')):
            raise ValueError('Changed needle callback binding')
    for role,name in (('before','fIJHOUI_DrawBefore'),('after','fIJHOUI_DrawAfter')):
        row=next(r for r in adapter['joint_callbacks'] if r['role']==role)
        if any(row[k]!=checked[name][k] for k in ('offset','bytes','sha256','relocations')):
            raise ValueError('Changed needle joint binding')
    base,size=source.sections[4]
    for at,value in CONSTANTS.items():
        raw=bytes.fromhex(value)
        if at+len(raw)>size or source.rel[base+at:base+at+len(raw)]!=raw:
            raise ValueError(f'Changed needle constant: {at:X}')
    from v3_furniture_rigs import checked_stop_initializer
    initializer=checked_stop_initializer(source)
    # The status helper uses a relocated jump table, not only code branches.
    expected=[0x2BFCD8]*8+[0x2BFC1C,0x2BFC28,0x2BFC1C,0x2BFC88]
    refs={p-0x88CC0:r for p,r in source.relocations.items() if 0x88CC0<=p<0x88CF0}
    if (source.data[0x88CC0:0x88CF0]!=bytes(48) or
            refs!={i*4:(1,True,1,target) for i,target in enumerate(expected)}):
        raise ValueError('Changed needle status dispatch')
    from v3_room_carry import source_contract as carrying_contract
    return dict(category='parent-sensitive-needle-motion',functions=checked,initializer=initializer,
        carrying=carrying_contract(source),
        constants={f'{at:X}':value for at,value in CONSTANTS.items()},
        status_dispatch=dict(offset=0x88CC0,bytes=48,targets=expected),
        source_wait_states=[8,10],source_rotation_states=[9,11],
        native_wait_states=[8,7],native_rotation_states=[3,4],
        source_steps_per_native_update=2,rotation_kick_tick=8,phase_step=800,
        initial_speed=.5,stopped_speed=0,state_bytes=16,
        debug_adjustments=dict(phase=80,decay=81),
        parent_required=True,callback_installed=False,
        pending=['native moving-parent registration, carry, draw, and release',
                 'joint dispatcher and complete constructor/move/draw binding'])


def native_contract(image,report=None):
    files=by_vrom(image);owner=bytearray(files[0x82D7F0].extract(image));rows=[];carrying=None
    if report is not None:
        from v3_room_carry_native import checked_binding,HOOKS,RAM
        carrying=checked_binding(image,report)
        # Check the actual installed hooks first, then compare every remaining
        # instruction in the original complete move/draw dependencies.
        for address,name,before in HOOKS:
            owner[address-RAM:address-RAM+8]=bytes.fromhex(before)
        from v3_furniture_motion import restore_embedded_dispatch
        owner=restore_embedded_dispatch(owner,report['equipment_resources']['room_rigs'])
    for name,at,n,digest in (
        ('rotation',0x80944358,400,'0b2ec06376e2deefa120ca4dc149b48caaf66869d2c699d856b271ca5fd829a2'),
        ('rotation_waits',0x80944D9C,96,'cdd06a67366b4b6ac64e735671345c797730b79575a69e1042f66f4923bf38d4'),
        ('state_dispatch',0x8094D0F4,64,'7a92b223bba1da2db031c25cf15cd144efb9dd44254a00d58498a5e6cceebb5f'),
        ('complete_owner_move',0x80944DFC,556,'9ea14e7299671297545682155532c799168acde6479406a9570a0cc717b32f83'),
        ('complete_owner_draw',0x80947024,684,'e49951f8efbe055fed3fbb252787e32bbf66ad7238690ecbda492e3baf2d1989')):
        raw=owner[at-0x80936710:at-0x80936710+n]
        if len(raw)!=n or sha256(raw)!=digest:raise ValueError('Changed needle native dependency: '+name)
        rows.append(dict(name=name,address=at,bytes=n,sha256=digest))
    code=files[CODE_VROM].extract(image);at=0x80099A94
    if sha256(code[at-CODE_RAM:at-CODE_RAM+64])!='ec2069784200594b9c741825ffd65c9449dba4d613b26fac7c3e8768d74f52de':
        raise ValueError('Changed needle native sine')
    debug=code[0x8007A0C0-CODE_RAM:0x8007A150-CODE_RAM]
    if sha256(debug)!='8ff8f035c40cae35db40b0f6e33422620870608e15a4356ca2ed08e512fb09ed':
        raise ValueError('Changed needle debug register initialization')
    return dict(blocks=rows,source_left_native=3,source_right_native=4,
        native_wait_left=8,native_wait_right=7,angle_float_offset=0x34,angle_short_offset=0x124,
        debug_owner_ram=0x80138E50,debug_register_offset=0x14,debug_group=11,debug_group_stride=96,
        parent_binding_installed=carrying is not None,**({'carrying':carrying} if carrying else {}))
