"""Shared event announcements and the checked native acre-transition lock."""
import json
import re
import struct

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
