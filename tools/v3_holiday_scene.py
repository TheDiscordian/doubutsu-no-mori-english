"""Shared event announcements and the checked native acre-transition lock."""
import json
import copy
import re
import struct
import zlib

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256
from apply_translation import write_new
from gc_text import decode_gc
from runtime_module import module_command_info
from textbanks import Bank
from textcodec import encode,tokenize,LATIN
from textvalidate import expanded_bound
from v3_asset_loader import ROOT,compile_part
from v3_camper_text import donor,extend_bank
from v3_event_text import MESSAGE,TABLE
from v3_holiday_dialogue import credit,check_provenance
from v3_password_policy import function

FIRST=12380
SOURCES=('tools/v3_holiday_scene.py','overlays/v3/holiday_demo.c','overlays/v3/holiday_demo.h',
    'overlays/v3/holiday_demo.ld','overlays/v3/holiday_groundhog.c','overlays/v3/holiday_groundhog.h',
    'overlays/v3/holiday_scene_native.c','overlays/v3/holiday_scene_native.h',
    'tools/v3_asset_loader.py','tools/v3_furniture_install.py')
REFERENCES={
    'src/game/m_demo.c':'71982f49f9380a7fe108595fe2ee18380a26c58c378006364f01c772650a1212',
    'src/game/m_player_lib.c':'76ef6299f5b1e1a1eef7ee783212e2c4db6d35db3c32db330723ece21ebca847',
    'src/game/m_player_common.c_inc':'0155a02590f38dcd12a71d2f276e923a98f11a3eaca0eae8219fc4b3bade4610',
    'src/game/m_event.c':'82a0d9ebdc4915357f5dd4217b49a978e6c680687dd4d7850e281a5a3a5741ef',
    'include/m_event.h':'7d479a212f933197a93b1abc80dc356940fd682beaf375503477728c4a2ef2f6'}
CORE_GUARDS=(
    (0x800B21D0,0x800B21F0,'3b7913d71676526dcce4d5dc37ba4a7c28043b0da4d01b8118e9bf708f1c657b'),
    (0x8007F950,0x8007F988,'571f1a81df18b4678bed592c74ca4c3240cf92d0d7dcd97b3d68963fc15d7d8c'),
    (0x8007C3D8,0x8007C484,'3f71b73c0d72652d716a92bb5ebf4245815c97ad3cb9548250cd897130be5112'),
    (0x8007C484,0x8007C570,'6947355553d383ecf49d5461466e78093babdccddc2c2554b1f0b436e6b239eb'))
PLAYER_GUARDS=(
    (0x808B400C,0x808B4428,'a69013938f78c5b79e2c947bed9e54b6e27429b5f0c081af64e7d4320e3ddecf'),
    (0x808B8114,0x808B81B4,'91661c0bbdb669c384ee8a9bdb18760de6201698ac6dc8073e0c58d7a2426d37'),
    (0x808B8204,0x808B828C,'2217da07b970e8557ee7edd7be15140ef6c680ad499300e45350d315ad96248a'),
    (0x808BB6B8,0x808BB724,'1294e3b5b569c0d4dd1f2f57a90dfa64bbd2dc197529444e7de5b5f0768ab908'))


def contract(base,source):
    texts={}
    for path,digest in REFERENCES.items():
        raw=(ROOT/'local/ac-decomp'/path).read_bytes()
        if sha256(raw)!=digest:raise ValueError('Changed complete event scene reference: '+path)
        texts[path]=re.sub(r'/\*.*?\*/|//[^\n]*','',raw.decode(),flags=re.S)
    enum=re.search(r'enum event_table\s*\{([^{}]+)\}',texts['include/m_event.h'])[1]
    names=[name.strip() for name in enum.split(',') if name.strip()]
    if any(not re.fullmatch(r'mEv_EVENT_\w+',n) for n in names):raise ValueError('Changed implicit event identities')
    lookup=dict(zip(names,range(len(names))))
    text=function(texts['src/game/m_demo.c'],'get_title_no_for_event')
    mapping={}
    for cases,title in re.findall(r'((?:\s*case \w+:)+)\s*return (\d+);',text):
        for name in re.findall(r'case (\w+):',cases):mapping[lookup[name]]=int(title)
    if len(mapping)!=18 or set(mapping.values())!=set(range(16)):
        raise ValueError('Incomplete donor event-title function')
    receipts=[]
    for name in ('get_title_no_for_event','set_emsg_default','mPlib_Set_unable_wade','mPlib_Get_unable_wade',
                 'Player_actor_CheckAbleMoveWadeBlock','Player_actor_Set_ScrollDemo_forWade',
                 'Player_actor_Reset_excute_cancel_wade','mEv_PlayerOK'):
        matches=[at for at,rows in source.functions.items() if any(n==name for n,_ in rows)]
        if len(matches)!=1:raise ValueError('Missing complete event scene source: '+name)
        _,row=source.function(matches[0]);receipts.append(row)
    core=by_vrom(base)[CODE_VROM].extract(base)
    for lo,hi,digest in CORE_GUARDS:
        if sha256(core[lo-CODE_RAM:hi-CODE_RAM])!=digest:
            raise ValueError(f'Changed complete event scene reader {lo:08X}')
    # Retain the actual initializer; only its one native init-proc table entry
    # is replaced when installed, avoiding recursive calls through an entry hook.
    matches=[i for i in range(0,len(core)-3,4) if core[i:i+4]==struct.pack('>I',0x8007C484)]
    if len(matches)!=1:raise ValueError('Changed event initializer directory references')
    player=by_vrom(base)[0x7AC420].extract(base)
    for lo,hi,digest in PLAYER_GUARDS:
        if sha256(player[lo-0x808B2D50:hi-0x808B2D50])!=digest:
            raise ValueError(f'Changed complete player acre-lock consumer {lo:08X}')
    calls=[0x808B4110,0x808B4204,0x808B42F8,0x808B43DC,0x808B815C,0x808B8218,0x808BB6D0]
    for at in calls:
        if player[at-0x808B2D50:at-0x808B2D50+4]!=bytes.fromhex('0c02c878'):
            raise ValueError('Changed actual player acre-lock consumer')
    return dict(references=REFERENCES,source_functions=receipts,title_indices=mapping,
        native_core_functions=CORE_GUARDS,init_pointer=CODE_RAM+matches[0],
        wade_setter=0x800B21D0,wade_getter=0x800B21E0,wade_state=0x801378DC,
        player_wade_consumers=calls,player_functions=PLAYER_GUARDS,native_event_gate=0x8007F950)


def convert(base,checked):
    source,_,decoder=donor();info=module_command_info(base);files=by_vrom(base)
    old=Bank('message',0,0,files[MESSAGE].extract(base),files[TABLE].extract(base)).entries()
    if len(old)!=FIRST:raise ValueError('Changed additive event-title message reservation')
    provenance=json.loads((ROOT/'translations/provenance.json').read_bytes())
    indexed={r['id']:r for r in provenance['entries']}
    extras=[];rows=[];credits=[];message_ids=[]
    # Retain the already reviewed shrine wording and its existing authorship.
    adaptations={0x1749:'42a731e35cfe7ee0f809052614b1a02f53306778f726cb47e80d76f71aca799e',
                 0x174D:'ff08b14b01f38d365b8c6e7fe6be17b04334172c6fa4ba0819136a4928ded849'}
    for first in (0x1743,0x1799):
        for source_id in range(first,first+16):
            data=encode(decode_gc(source[source_id],decoder),info)
            tokens=list(tokenize(data,info))
            if (not tokens or tokens[-1].data not in (bytes.fromhex('7f58'+n) for n in ('28','3c','50','64')) or expanded_bound(data,info)>1024 or
                any(t.kind=='cmd' and t.data[1] not in (3,5,80,88) for t in tokens) or
                sum(t.kind=='cmd' and t.data[1]==88 for t in tokens)!=1 or
                any(t.kind!='cmd' and (t.kind!='text' or t.data[0] not in LATIN|{0xCD}) for t in tokens)):
                raise ValueError(f'Unreviewed complete event title {source_id:04X}')
            if source_id in adaptations:
                data=old[source_id]
                if sha256(data)!=adaptations[source_id]:raise ValueError('Changed reviewed shrine adaptation')
            if source_id<0x1751 or 0x1799<=source_id<0x17A7:
                target=source_id
                if data!=old[target]:raise ValueError('Changed complete reusable event title')
                entry=indexed.get(f'message:{target:04X}',{}).get('locales',{}).get('en',{})
                if entry.get('encoded_sha256')!=sha256(data) or entry.get('credit')!='official':
                    raise ValueError('Uncredited reusable event announcement')
            else:
                target=FIRST+len(extras);extras.append(data)
                credits.append(credit(f'message:{target:04X}',f'message:{source_id:04X}',source[source_id],data,
                    ['Native encoding; unchanged official event announcement, colours, timing, and automatic close']))
                credits[-1]['locales']['en']['locator']=['tools/v3_holiday_scene.py:convert',f'N64/message/{target:04X}']
            message_ids.append(target)
            rows.append(dict(source_id=source_id,id=target,sha256=sha256(data),source_sha256=sha256(source[source_id]),
                bytes=len(data),reused=target<FIRST,shrine_adaptation=source_id in adaptations))
    if len(extras)!=4:raise ValueError('Incomplete additional event announcements')
    packet=bytearray(struct.pack('>4sHHII',b'AFHT',1,128,32,208)+bytes([255])*128)
    for source_id,title in checked['title_indices'].items():packet[16+source_id]=title
    packet.extend(struct.pack('>32H',*message_ids))
    payload,table=extend_bank(files[MESSAGE].extract(base),files[TABLE].extract(base),extras,FIRST)
    return bytes(packet),payload,table,dict(rows=rows,first_id=FIRST,added=4,reused=28,
        provenance_entries=credits,bytes=len(packet),sha256=sha256(packet))


def prepare(base,prior,source,output):
    checked=contract(base,source);packet,payload,table,converted=convert(base,checked)
    check_provenance(converted)
    output.mkdir(parents=True,exist_ok=False)
    for name,data in (('titles.bin',packet),('messages.bin',payload),('message-table.bin',table)):
        write_new(output/name,data)
    bindings=dict(af_holiday_scene_titles=0x806FB700,af_holiday_scene_event=0x80137682,
        af_holiday_scene_flags=0x80137684,af_holiday_scene_demo=0x80104A70,
        af_holiday_scene_original_init=0x8007C484,
        af_holiday_source_ids=prior['equipment_resources']['npc_extra']['events']['native_directory']['identity_ram']+128,
        af_holiday_native_type=prior['equipment_resources']['npc_extra']['events']['native_directory']['code']['symbols']['af_holiday_native_type'])
    code,compiled=compile_part('holiday_scene',output/'code',link_symbols=bindings)
    from v3_event_text import CHOICE_TABLE
    files=by_vrom(base);cv=prior['import_storage']['choice_vrom']
    write_new(output/'choices.bin',files[cv].extract(base))
    write_new(output/'choice-table.bin',files[CHOICE_TABLE].extract(base))
    converted.update(count=converted['added'],choice_vrom=cv,
        resources=[dict(vrom=v,file=str((output/f).relative_to(output.parent.parent)),
            bytes=len(d),sha256=sha256(d),original_sha256=sha256(files[v].extract(base))) for v,f,d in
            ((MESSAGE,'messages.bin',payload),(TABLE,'message-table.bin',table),
             (cv,'choices.bin',files[cv].extract(base)),(CHOICE_TABLE,'choice-table.bin',files[CHOICE_TABLE].extract(base)))])
    report=dict(contract=checked,text=converted,bindings=bindings,code=compiled,installed=False,
        native_init_pointer_hook=dict(address=checked['init_pointer'],before=0x8007C484,
            after=compiled['symbols']['af_holiday_scene_demo_init']))
    write_new(output/'scene.json',(json.dumps(report,indent=2)+'\n').encode())
    return report


DEMO_RAM,DEMO_STATE,DEMO_END=0x806FE000,0x806FFF80,0x806FFFC0
DEMO_HOOKS=(
    (0x8007B410,'talk_actor'),(0x8007B5C0,'message'),(0x8007B5F4,'actors'),
    (0x8007B724,'set_zoom'),(0x8007B760,'get_zoom'),
    (0x8007B79C,'set_name'),(0x8007B7DC,'get_name'),
    (0x8007B818,'set_change_player'),(0x8007B854,'get_change_player'),
    (0x8007B890,'set_return_wait'),(0x8007B8CC,'get_return_wait'),
    (0x8007B908,'set_turn'),(0x8007B944,'get_turn'),
    (0x8007B980,'colour'),(0x8007B9E0,'colour_pointer'),
    (0x8007C924,'choose'),(0x8007CB50,'init'),(0x8007CBEC,'run'),
    (0x8007CC9C,'main'),(0x8007CDD8,'request'),(0x8007D048,'busy'),
    (0x800641CC,'camera_reverse'),(0x8006447C,'camera_counter'))


def install_demo(base,prior,blob,core,output,*,scene_services=False):
    """Connect all additional announcement/speech consumers in one module."""
    from v3_import_storage import jump
    from v3_furniture_pipeline import Source
    del blob
    e=copy.deepcopy(prior['equipment_resources']);events=e['npc_extra']['events']
    previous_demo=events.get('demo');groundhog=bool(previous_demo and previous_demo.get('groundhog'))
    if ((previous_demo and (not scene_services or previous_demo.get('scene_services'))) or
            not e['holiday_fishing']['live'].get('measurement_choice')):
        raise ValueError('Unexpected shared announcement predecessor')
    if previous_demo:
        # Restore only this module's checked entry patches for the complete
        # original guards, then rebind all callers to the refreshed module.
        for hook in previous_demo['hooks']:
            at=hook['address']-CODE_RAM
            if core[at:at+8]!=bytes.fromhex(hook['after']):raise ValueError('Changed installed demo caller')
            core[at:at+8]=bytes.fromhex(hook['before'])
    references={
        'local/ac-decomp/src/game/m_demo.c':REFERENCES['src/game/m_demo.c'],
        'local/ac-decomp/src/game/m_camera2.c':'053942e40b0cc7b4212302a2c51b50fa421446441b3b69f8124e22dbdfb4e6fc',
        'local/ac-decomp/include/m_camera2.h':'ec7bc2f1efc05b14736ce3d169cf708b6d9e10d850ee37dee6f0625ad3f0b4a9',
        'upstream/af/src/code/m_demo.c':'0000cb13810b84141b670fcedde07c38c4a96ce981994dd2ae18c76ffe9651dd',
        'upstream/af/include/m_demo.h':'9332283a877036b8134c27004a688b61bbb61da47507298eeccfa895b60226a4'}
    if groundhog:
        references.update({
            'local/ac-decomp/src/actor/ac_groundhog_control.c':'e8ed5dba08279843b1842f0558f37cd66cf98eb5e5098a26e06b8c222a8492e8',
            'local/ac-decomp/include/ac_groundhog_control.h':'6b1b68a041c2673b9e1b0992ea942a8fbb06487bc0d63613ecc07721a69a2cdc',
            'local/ac-decomp/include/ac_groundhog_control_h.h':'8c04b892c4507ab13188ac2d634442593c14eeea918449ef64caf2d80f07311e'})
    if scene_services:
        references.update({
            'local/ac-decomp/src/actor/ac_my_room.c':'4543f92a35a19c393bba5479573a4535d4c9a7cf02d437de858f510739e43b5a',
            'local/ac-decomp/src/actor/ac_my_room_msg_ctrl.c_inc':'56b9e7965f1e225b5a99d6fefd261109a0ecbc438dd6bfa26fde438469bd3931',
            'local/ac-decomp/src/game/m_field_info.c':'6b89a2f8de448cf2beda42da58c17d696d46b2f73e6ccf0a365c64769af9b10f',
            'upstream/af/include/tables/actor_table.h':'7e8705925749254a11fa2f0d04934a7774ea24eadb02c065c516d6486e797c22',
            'overlays/v3/console_room.c':'37e9266f44d6175b4fb7c1256602a55a60ef45e48ee5a8d8fbb5db1221fddbe1'})
    for path,digest in references.items():
        if sha256((ROOT/path).read_bytes())!=digest:raise ValueError('Changed announcement reference: '+path)
    guards=(
        (0x8007B410,0x8007D128,'0d99af75437dc163779e8fbdd253190fd1f8c5433d0682015cbd5e752688256b'),
        (0x80064178,0x800645B0,'c33dedd8189351005fd020e1125ea4f05c54420dd9511450d8eff436704c4aca'),
        (0x800639A0,0x80063B1C,'17d11809f1f8a01506574f239f2c66430b09d0750f67498caef97c0730d405f1'),
        (0x80062690,0x800626E4,'9256ea6485d63c94f5b12e375219bd28da898ef468480f50ace331964629be08'),
        (0x8005EDD8,0x8005EDEC,'e9eeb7d88cacd79bbc33d22b594bad7a512a49e8998b78dc21a454a2edbe5bc4'),
        (0x800B21F0,0x800B2244,'cf740072194ece5b8cd55e506b58773ef6abfcd53e4614efc2ff046b8901d17b'),
        (0x80104A74,0x80104B58,'4206c14109b084495d46b0d6ae671a96c560e8ce13b6884dd49cca4855c24887'))
    for a,b,digest in guards:
        if sha256(core[a-CODE_RAM:b-CODE_RAM])!=digest:raise ValueError('Changed complete native demo/camera consumer')
    table=struct.unpack_from('>14I',core,0x80104AAC-CODE_RAM)
    if table[12]!=events['reserved']['native']['scene']['code']['symbols']['af_holiday_scene_demo_init']:
        raise ValueError('Missing installed official announcement reader')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    names=('set_emsg2_default','wait_emsg2_start','wait_emsg2_end','set_speech_default',
        'choice_demo_sub','choice_demo','init_demo','run_demo','main_proc','mDemo_Request',
        'change_camera','Camera2_Inter_CounterProc','Camera2_Inter_set_reverse_mode')
    if groundhog:
        control=(ROOT/'local/ac-decomp/src/actor/ac_groundhog_control.c').read_text()
        names+=tuple(re.findall(r'^static (?:int|void) (aGHC_\w+)\([^;{]*\)\s*\{',control,re.M))
        if len(names)!=28:raise ValueError('Incomplete Groundhog controller functions')
    donors=[]
    for name in names:
        offsets=[at for at,rows in source.functions.items() if any(n==name for n,_ in rows)]
        if len(offsets)!=1:raise ValueError('Ambiguous complete announcement source: '+name)
        _,row=source.function(offsets[0]);donors.append(row)
    bindings=dict(af_hd_native_demo=0x80104A70,af_hd_state=DEMO_STATE,af_hd_game=0x8010EF90,
        af_hd_common=0x80136EA0,af_hd_title_flags=0x80137684,
        af_hd_checks=0x80104A74,af_hd_defaults=0x80104AAC,af_hd_starts=0x80104AE8,af_hd_ends=0x80104B20,
        af_hd_title_demo=0x8007D90C,af_hd_trigger=0x80078DAC,af_hd_weight=0x8007C6C0,
        af_hd_force_speak=0x800B21F0,af_hd_player=0x800B1C84,af_hd_camera=0x8007BA84,
        af_hd_demo_type=0x8007BA4C,af_hd_emsg_colour=0x8007CB28,
        af_hd_camera_angle=0x80063AA0,af_hd_camera_simple=0x800639A0,
        af_hd_camera_inter=0x800641F8,af_hd_camera_normal=0x80062690,
        af_hd_landmark=0x80089440,af_hd_origin=0x80088B3C,af_hd_goto=0x800C6C10,
        af_hd_bgm_end=0x8005EDD8,memcpy=0x80034BF8,memset=0x8003B9B0)
    if groundhog:bindings['af_hg_live']=DEMO_STATE+24
    extra_sources=('overlays/v3/holiday_groundhog.c',) if groundhog else ()
    if scene_services:
        owner=by_vrom(base)[0x82D7F0].extract(base)
        room_guards=(
            (0x80936ADC,0x80936B68,'7c998a46bb3a7d3775ea516aa179def8223f664b55f239c9f8b68d926f5eadbb'),
            (0x80936E98,0x80937020,'a369c5c46de52034d043757142b86c07e4ecbb53b8b53be7376cca84c5caaff4'),
            (0x80939050,0x8093919C,'829a1b5c83b3284fe2e0174932f22be1ad56e184b4540017259fe6b229ed381a'),
            (0x8093A728,0x8093A7F4,'a8a41a9a91665059875ae31cfff0beb2950134d1d7566a3b47d25db682886cb8'),
            (0x8093BC30,0x8093BC94,'5b6cdeaefec7e22482d34e9c00c5bc1b10a7f1cb4e47755b547f41f592e1f7ab'),
            (0x8093BB04,0x8093BB5C,'3265c801e3dfdaacae731a6532d9c73eef2462f655b9f3c09554e00bf43f06cf'))
        for a,b,digest in room_guards:
            if sha256(owner[a-0x80936710:b-0x80936710])!=digest:
                raise ValueError('Changed live room transition service: '+hex(a))
        if struct.unpack_from('>8I',core,0x80100DF0-CODE_RAM)!=(
                0x82D7F0,0x844400,0x80936710,0x8094F610,0,0x8094756C,0,0):
            raise ValueError('Changed room owner descriptor for scene services')
        from v3_console_room import native_contract
        native_contract(base)
        bindings.update(af_holiday_scene_room_descriptor=0x80100DF0,
            af_holiday_scene_room_clip=0x80136F2C,af_holiday_scene_pool_variant=0x8008930C)
        extra_sources+=('overlays/v3/holiday_scene_native.c',)
    directory=output/'holiday-demo';code,compiled=compile_part('holiday_demo',directory/'code',link_symbols=bindings,
        extra_sources=extra_sources)
    p=e['holiday_state']['packet'];data=bytearray(base[p['physical']:p['physical']+p['bytes']])
    at=DEMO_RAM-p['ram'];end=DEMO_END-p['ram']
    transition=events['transition']['loaded_code']
    if previous_demo:
        old=previous_demo['code'];count=old['bytes']
        if old['symbols']['af_holiday_demo_main']!=DEMO_RAM or sha256(data[at:at+count])!=old['sha256']:
            raise ValueError('Changed complete demo module before refresh')
        data[at:at+count]=bytes(count)
    if (sha256(base[p['physical']:p['physical']+p['bytes']])!=p['sha256'] or p!=e['holiday_fishing']['packet'] or
            transition['ram']+transition['bytes']>DEMO_RAM or len(code)>DEMO_STATE-DEMO_RAM or
            any(data[at:end])):raise ValueError('Occupied or changed event-demo reservation')
    data[at:at+len(code)]=code
    hooks=[]
    for address,name in DEMO_HOOKS:
        symbol='af_holiday_demo_'+name;offset=address-CODE_RAM
        before=bytes(core[offset:offset+8]);after=struct.pack('>2I',jump(compiled['symbols'][symbol]),0)
        core[offset:offset+8]=after;hooks.append(dict(address=address,symbol=symbol,before=before.hex(),after=after.hex()))
        if previous_demo:hooks[-1]['previous']=next(h['after'] for h in previous_demo['hooks'] if h['address']==address)
    previous=p['sha256'];p.update(sha256=sha256(data),crc32=zlib.crc32(data))
    e['holiday_fishing']['packet']=copy.deepcopy(p)
    records=copy.deepcopy(prior['physical_resources']);matches=[r for r in records if r['id']==p['id']]
    if len(matches)!=1:raise ValueError('Ambiguous combined holiday physical packet')
    matches[0]['sha256']=p['sha256']
    stage=dict(installed=True,event_owners_enabled=False,native_execution_verified=False,
        code=compiled,bindings=bindings,hooks=hooks,references=references,native_guards=guards,
        source_functions=donors,types=dict(eventmsg2=14,speech=15),retained_native_types=list(range(14)),
        state=dict(ram=DEMO_STATE,bytes=64,saved=False),saved_format_changed=False,additional_resident_bytes=0,
        speech_camera=dict(native_interpolation_type=10,source_morph_ticks=14,native_morph_ticks=7,
            source_return_flag=4,original_return_flag=2),
        sources={p:sha256((ROOT/p).read_bytes()) for p in SOURCES},
        pending=['Live transition read/commit for scheduled owners, dedicated-owner dispatch, and event admission'])
    if groundhog:
        from v3_holiday_events import TYPES
        schedule=source.raw('event_schedule_data')
        scope_rows={event:[schedule[i:i+12].hex() for i in range(0,len(schedule),12)
            if int.from_bytes(schedule[i+10:i+12],'big')==event] for event in (7,81)}
        if (7 in TYPES or 81 not in TYPES or scope_rows!={
                7:['020200070202000800000007'],81:['020200090202001000000051']}):
            raise ValueError('Changed independent ceremony/diary-attendance scope')
        stage['groundhog']=dict(installed=True,actor_services_bound=False,native_execution_verified=False,
            source_functions=names[13:],states=9,source_updates_per_native_frame=2,
            clip_pointer_ram=DEMO_STATE+24,source_names={'speaker':0xD087,'groundhog':0xD081},
            source_music=252,common_area_bytes=4,
            required_for_diary_attendance=False,scope_schedule_rows=scope_rows,
            pending=['Inactive preparation; ceremony owner 7 is outside the diary owner set',
                'Native control actor lifecycle and required NPC/music services are not implemented'])
    if scene_services:
        stage['scene_services']=dict(installed=True,native_execution_verified=False,
            room_functions=room_guards,room_descriptor=0x80100DF0,room_clip=0x80136F2C,
            room_console_request_offset=0x47C,current_acre_offsets=[0xE4,0xE5],
            room_tempo=0x8093A7C4,room_gyroid_steps=0x80936E98,
            source_mainland_climate_states=[0,2,4],source_mainland_climate_results=[0,0,0],
            present_demo_imported=False,ceremony_owner_in_scope=False,
            pending=['Identity/status graph and live dedicated-owner dispatch'])
    events['demo']=stage;e['npc_extra']['sources'].update(stage['sources'])
    preserved=events['decorations']['controllers']['preserved']
    if previous_demo:
        entries=[row for row in preserved if row['ram']==DEMO_RAM]
        if len(entries)!=1 or entries[0]['sha256']!=previous_demo['code']['sha256']:
            raise ValueError('Changed preserved demo module')
        preserved.remove(entries[0])
    preserved.append(dict(ram=DEMO_RAM,bytes=len(code),sha256=sha256(code)))
    write_new(directory/'installed.json',(json.dumps(stage,indent=2)+'\n').encode())
    write_new(directory/'packet.bin',data)
    return e,{},dict(physical_resources=records),[(dict(matches[0],previous_sha256=previous),bytes(data))]
