"""Complete composite draw resources with explicit room-lifecycle dependencies.

Callback shapes select these formats. Neither preparation nor a model name
authorises omitting the required music, contact, animation, or scene behaviour.
"""
import struct
from aflib import u32,sha256
from v3_keyframes import skeleton,animation,model_descriptor

ROTATED_CATEGORY='rotated-fixed-material-assets'
DUAL_CATEGORY='dual-motion-scroll-rig-assets'
PENDING_CATEGORIES=(ROTATED_CATEGORY,DUAL_CATEGORY)


def discover(source,name,at,functions):
    sizes=tuple(functions.get(role,{}).get('bytes') for role in ('create','move','draw','destroy'))
    if sizes not in ((4,236,168,4),(436,508,492,36)):return None
    if set(functions)!={'create','move','draw','destroy'}:raise ValueError('Composite lifecycle has unexpected slots')
    module=u32(source.rel,0);ct,mv,dw,dt=(functions[role] for role in ('create','move','draw','destroy'))
    def pairs(receipt,rows):
        targets=[];refs={}
        for hi,lo,section,wanted in rows:
            ref=receipt['relocations'].get(hi)
            if ref is None or ref[:3]!=(6,module,section) or wanted is not None and ref[3]!=wanted:
                raise ValueError('Changed composite paired dependency')
            targets.append(ref[3]);refs.update({hi:ref,lo:(4,module,section,ref[3])})
        return targets,refs
    def constant(offset,hexadecimal):
        base,n=source.sections[4];raw=bytes.fromhex(hexadecimal)
        if not 0<=offset<=n-len(raw) or source.rel[base+offset:base+offset+len(raw)]!=raw:
            raise ValueError('Changed composite behaviour constant')
    helpers={}
    if sizes[0]==4:
        for receipt in (ct,dt):
            source.checked_callback_code(receipt,4,'f332ea5b5437103cbb6f1508679da89eec9288ad775c96c439a17fccabe3de8e',{}, {},'empty rotated-model callback')
        _,refs=pairs(mv,[(62,66,4,0xC258),(78,86,6,0xBC40)])
        constant(0xC258,'40400000')
        refs.update({16:(10,0,4,0x8009AED4),216:(10,0,4,0x8009AF20)})
        helpers.update(source.checked_callback_code(mv,236,
            '919e53dc85f869811298e2d59e68d411ed91e7076bddd590bc7aff788d9c82db',refs,
            {0x1C:(0x103ACC,'aMR_RadioCommonMove')},'rotated model music/emitter',internal_branches=True))
        music=helpers['aMR_RadioCommonMove']
        if music['sha256']!='9073271d688406e4223163121d74eed1e82d39f04635fc7101ce3257d976ef6a' or music['relocations']:
            raise ValueError('Changed complete room-music helper')
        (palette,model),refs=pairs(dw,[(82,98,5,None),(86,110,5,None)])
        refs.update({16:(10,0,4,0x8009AED4),148:(10,0,4,0x8009AF20)})
        helpers.update(source.checked_callback_code(dw,168,
            '0bda109e2456dde5dd7cdfadafd1ce9bc9e7000e22e4a806dac90a1fc18d692a',refs,
            {0x24:(0x9C49C,'Matrix_RotateY'),0x44:(0x9D214,'_Matrix_to_Mtx_new')},'rotated fixed material'))
        label,palette,n=source.containing(palette,exact=True)
        if n!=32 or source.pointers(palette,n):raise ValueError('Incomplete fixed palette')
        models={'opaque':source.containing(model,exact=True)}
        return models,{0x08000000:palette},dict(category=ROTATED_CATEGORY,
            vtable_symbol=name,vtable_offset=at,functions=functions,helpers=helpers,
            model_order=list(models),draw_arena='opaque',rotation_y=-0x7000,
            constant_palette=dict(symbol=label,donor_offset=palette,bytes=n,
                source_sha256=sha256(source.data[palette:palette+n]),segment_address=0x08000000),
            emitter=dict(source_period=36,height=-3.0,angle_offset=-0x1000,
                source_effect=32,source_item=0x1FCC,arg0=1,arg1=0,switch='equals-one'),
            pending_callbacks=['room-music-ownership','note-emitter','rotated-drawing','room-create-destroy'],
            runtime_installed=False)

    (bones,opening),refs=pairs(ct,[(102,110,5,None),(106,118,5,None)])
    (closing,),closing_refs=pairs(ct,[(262,274,5,None)])
    _,more=pairs(ct,[(10,22,6,0xBC40),(126,134,5,opening),(174,190,5,opening),
        (146,154,4,0xC104),(166,170,4,0xC100),(182,194,4,0xC110),
        (258,266,5,bones),(282,290,5,closing),(330,346,5,closing),
        (302,310,4,0xC104),(322,326,4,0xC100),(338,350,4,0xC110)])
    for offset,value in ((0xC100,'3f800000'),(0xC104,'00000000'),(0xC110,'4330000080000000'),
            (0xC118,'3f000000'),(0xC12C,'41c80000')):constant(offset,value)
    helpers.update(source.checked_callback_code(ct,436,
        '900b6d398d8a6779f5a919fbc15101659a50b795e45925fb403c9277f1b180c9',refs|closing_refs|more,
        {0x78:(0x8D4,'cKF_SkeletonInfo_R_ct'),0x8C:(0x934,'cKF_SkeletonInfo_R_init_standard_stop'),
         0x114:(0x8D4,'cKF_SkeletonInfo_R_ct'),0x128:(0x934,'cKF_SkeletonInfo_R_init_standard_stop'),
         0x19C:(0xE54,'cKF_SkeletonInfo_R_play')},'dual-motion constructor',internal_branches=True))
    _,refs=pairs(mv,[(58,66,4,0xC104),(106,114,5,opening),(126,134,4,0xC100),
        (130,146,5,opening),(142,154,4,0xC110),(162,170,4,0xC118),
        (222,230,5,closing),(242,250,4,0xC100),(246,262,5,closing),
        (258,270,4,0xC110),(278,286,4,0xC118),(382,390,4,0xC12C),
        (422,430,4,0xC12C),(474,478,4,0xC104)])
    helpers.update(source.checked_callback_code(mv,508,
        'a9f61825f1d6d5c631b6aee4440fe7763355f5b0e2fa5bc4c416730b0108ea2e',refs,
        {0x28:(0x103BC4,'aMR_GetContactInfoLayer1'),0x78:(0x934,'cKF_SkeletonInfo_R_init_standard_stop'),
         0xD4:(0x2BDDE8,'sAdo_OngenTrgStart'),0xEC:(0x934,'cKF_SkeletonInfo_R_init_standard_stop'),
         0x148:(0x2BDDE8,'sAdo_OngenTrgStart'),0x19C:(0x2BDD84,'sAdo_OngenPos'),
         0x1C4:(0x2BDD84,'sAdo_OngenPos'),0x1CC:(0xE54,'cKF_SkeletonInfo_R_play')},
        'dual-motion contact and sound',internal_branches=True))
    _,refs=pairs(dw,[(26,34,6,0xBC40)])
    helpers.update(source.checked_callback_code(dw,492,
        '561c37819d87f7da3703e150d8681fab44dd81912d348d32b0cb48769fb675f8',
        refs|{16:(10,0,4,0x8009AEC0),472:(10,0,4,0x8009AF0C)},
        {0x64:(0x49458,'mEnv_PointLightMin'),0xB4:(0x2BE944,'fFTR_GetTwoTileGfx'),
         0xEC:(0x2BE944,'fFTR_GetTwoTileGfx'),0x124:(0x2BE944,'fFTR_GetTwoTileGfx'),
         0x164:(0x9D214,'_Matrix_to_Mtx_new'),0x1D0:(0x1578,'cKF_Si3_draw_R_SV')},
        'dual-motion scrolling drawing',internal_branches=True))
    source.checked_callback_code(dt,36,'c50acb633e458da05b486ad2ee3523889f1a150e7554746d62a89f2e56e2d718',{}, {},'dual-motion persistence')
    for symbol,digest in (
        ('aMR_GetContactInfoLayer1','db0a6978f69d604ba28b26684d101066aebdeb796c8c1972909e1f1062de4006'),
        ('mEnv_PointLightMin','a117d59458101f6f013522626ae5640ab7b62b3519a56974bbbc8cc42bba89b0'),
        ('fFTR_GetTwoTileGfx','91996029d7c0bada911b5b37cd21ea93f8dc51c2ca5fc3ac3757878bd70a7da1'),
        ('sAdo_OngenPos','b982dbca7ed68e0565b554e142e64d69a1d2c47ec061169d114502a25e61f885'),
        ('sAdo_OngenTrgStart','4fdc889bb1697c19c8f386d72b80585ea07706d9f26b328389766bec96f0f989')):
        if helpers[symbol]['sha256']!=digest:raise ValueError('Changed complete composite helper '+symbol)
    from v3_furniture_rigs import checked_stop_initializer
    initializer=checked_stop_initializer(source)
    rig=skeleton(source,bones);motions=[animation(source,target,joints=rig['joints']) for target in (opening,closing)]
    if opening==closing or rig['joints']>8 or any(r['draw_stream'] for r in rig['rows']):
        raise ValueError('Unsupported complete dual-motion skeleton')
    desc=model_descriptor(rig,kind='animated-room-model');scrolls={}
    for label,(_,address,n) in desc['models'].items():
        for offset in range(address,address+n,8):
            first,last=struct.unpack_from('>II',source.data,offset)
            if first==0xDE000000:
                if label in scrolls or last not in (0x08000000,0x09000000,0x0A000000) or offset+4 in source.relocations:
                    raise ValueError('Unexpected dual-motion scrolling dependency')
                scrolls[label]=dict(segment=last,dimensions=[[32,8]])
    if sorted(r['segment'] for r in scrolls.values())!=[0x08000000,0x09000000,0x0A000000]:
        raise ValueError('Missing complete three-part scroll sequence')
    return desc['models'],{},dict(category=DUAL_CATEGORY,vtable_symbol=name,vtable_offset=at,
        functions=functions,helpers=helpers,initializer=initializer,skeleton=rig,
        animation=motions[0],animations=motions,joint_models=desc['joint_models'],joint_callbacks=[],
        model_scrolls=scrolls,scroll_phases=[0,5,15],scroll_dimensions=[[32,8],[32,8]],
        source_scroll_rate=[2,0,0,0],source_coordinate_shift=1,
        scrolling_condition='basement-and-point-light-minimum-nonzero-stops',
        constructor=dict(npc_rooms='force-closed',otherwise='saved-switch-equals-one',current='selected-end'),
        movement=dict(accept='nonzero-front-contact-idle',speed=.5,source_steps_per_native_update=2,
            sound_order='before-keyframe-play',sound_threshold=25.0,source_loop=0x52,source_clicks=[0x16A,0x16B],
            excluded_states=[13,14,15,12],destructor='state-to-saved-switch'),
        pending_callbacks=['scene-selection','contact-motion','full-source-audio','three-scroll-drawing','save-capture'],
        runtime_installed=False)
