"""Bind the complete donor holiday actor to its shared movement/talk controller."""
import argparse
import json
from pathlib import Path
import re
import struct

from aflib import by_vrom,sha256
from apply_translation import write_new
from v3_asset_loader import ROOT
from v3_furniture_pipeline import Source
from v3_holiday_rewards import compile_kernel
from v3_furniture_install import inputs

REFERENCES={
    'src/actor/npc/event/ac_ev_soncho2.c':'14a19402e14897ef67b2e47a883b14dbc69c6c8d430fb312d363e946af3ee540',
    'src/actor/npc/event/ac_ev_soncho2_think.c_inc':'3777c7ee2306059d231856c99c48472b0e5faac115c92cc0b6f32eff481ddcb5',
    'include/ac_ev_soncho2.h':'032a789150c076724149c92c1804bf6f07e7669c0fd98d46b198c5983d7f693b',
    'include/ac_npc.h':'0b6cc1bf100ba37d105ebb8d439d68c254e6fd0b92f92c256a9c18ce667a7a65',
    'src/game/m_calendar.c':'f6683884803ee1373b84ea55d9a4deca268dde4d4eb494a4138f6a1599f5e467',
}
NATIVE=(
    ('request',0x8097BF90,0x8097C00C,'b1f8cc3149e05c4978351677583995fc6c437db7f28500c441af9d967f9db7c5'),
    ('destination',0x809774A0,0x809774DC,'352cf23adef9bf48e58bbf8a7479e64bca65e38daa3c36ed56cbe40928b4cd93'),
    ('think',0x8097E74C,0x8097E860,'85963ab2da4a6d4e2fc9cdd0761b3d2f999558f1cf8b00561d161b5325564bd6'),
    ('schedule',0x8097F060,0x8097F148,'24c511a346ee4caf0fed0d40215008fb08e76ce91a1a1fcfdfd809efe8f5daa1'),
    ('ctor_prefix',0x8097F520,0x8097F93C,'7104414a71354b4e27346b032a19aacb450c068c4f2c5606009d19ad879cf39e'),
    ('ctor_mode',0x8097F47C,0x8097F520,'2161e124553a2f4c3ad100f661e2c1e4abe7e7c7b166cd11b1312bc0563ef02d'),
)


def native_contract(base):
    owner=by_vrom(base)[0x8681F0].extract(base);ram=0x809735B0;functions=[]
    for name,start,end,digest in NATIVE:
        if sha256(owner[start-ram:end-ram])!=digest:
            raise ValueError('Changed native holiday actor dependency: '+name)
        functions.append(dict(name=name,start=start,end=end,sha256=digest))
    # The two dispatch arrays establish SPECIAL as native think 8 / schedule 5,
    # rather than the donor's think 9 / schedule 6.
    if (struct.unpack_from('>9I',owner,0x809835F8-ram)!=
            (0x8097D438,0x8097DBA0,0x8097DEDC,0x8097DF78,0x8097E080,
             0x8097E434,0x8097E5C4,0x8097E71C,0x8097E74C) or
            struct.unpack_from('>6I',owner,0x80983678-ram)!=
            (0x8097EAF4,0x8097ECC8,0x8097EE90,0x8097EF7C,0x8097F030,0x8097F060)):
        raise ValueError('Changed native NPC schedule/think dispatch')
    return dict(functions=functions,npc_prefix=0x93C,clip_pointer=0x80136EEC,
        think_callback=0x7A4,schedule_callback=0x7C0,interrupt_flags=0x7A8,
        action=0x7C5,step=0x7C6,hide_request=0x7FD,demo_flags=0x80C,
        pal_ignore_timer=0x8AC,destination_x=0x8BC,destination_z=0x8C0,
        talk_request=0x91C,ctor_schedule=4,special_think=8,special_schedule=5,
        motion_indices_bound=False,walking_only_schedule_bound=False,
        callback_cadence_verified=False)


def discover(source):
    for path,digest in REFERENCES.items():
        if sha256((ROOT/'local/ac-decomp'/path).read_bytes())!=digest:
            raise ValueError('Changed complete holiday actor reference: '+path)
    code=bytearray();relocations=bytearray();functions=[];next_address=0x1B44B4
    for match in re.finditer(r'^(aES2_\w+) = \.text:0x([0-9A-Fa-f]+);',source.symbols,re.M):
        at=int(match[2],16);raw,row=source.function(at)
        if at!=next_address or row['symbol']!=match[1]:
            raise ValueError('Incomplete holiday actor function extent')
        next_address+=len(raw);code.extend(raw);functions.append(row)
        relocations.extend(b''.join(struct.pack('>5I',p,*v) for p,v in sorted(row['relocations'].items())))
    if (len(functions)!=37 or next_address!=0x1B55FC or
        sha256(code)!='01b120b35905c78d70c4c2784ca36577f7b0fcad0c6252a7cf2a3f988c6a2e60' or
        sha256(relocations)!='cd4a3c77f6343e3d60f376252c62a8bf9e5b511ad5a1b7ae1d52f4a4b9052e94'):
        raise ValueError('Changed complete holiday actor code or relocations')
    at=0x538E4;raw=source.data[at:at+75]
    expected=bytes.fromhex('01010000000001000001030100000200030100030003010104'
        '02020102050404010306050501040604040105080602010608040401070a'
        '050501080a040401090c0602010a0c0706010b0e')
    if source.containing(at,exact=True)!=('dt_tbl',at,75) or raw!=expected or source.pointers(at,75):
        raise ValueError('Changed complete holiday actor state table')
    start,end=0x53888,0x53978
    data=source.data[start:end]
    pointers={p:r for p,r in source.relocations.items() if start<=p<end}
    packed=b''.join(struct.pack('>5I',p,*r) for p,r in sorted(pointers.items()))
    if (sha256(data)!='865394740375c36165be193cb681cf3e9289233a702e7c96541677a1c58976b2' or
            sha256(packed)!='7b76f7c6376629c5f7932381c18884014270e54657aff14df77ea2b15407fc26'):
        raise ValueError('Changed complete holiday actor data or relocations')
    return dict(format='AFV3-HOLIDAY-ACTOR-1',functions=functions,references=REFERENCES,
        data=dict(offset=start,bytes=end-start,sha256=sha256(data),relocations=pointers),
        states=[list(raw[i:i+5]) for i in range(0,75,5)],runtime_installed=False,
        native_services_bound=False,native_gameplay_verified=False,
        sources={p:sha256((ROOT/p).read_bytes()) for p in (
            'overlays/v3/holiday_actor.c','overlays/v3/holiday_actor.h',
            'overlays/v3/holiday_npc.c','overlays/v3/holiday_npc.h',
            'overlays/v3/holiday_talk.c','overlays/v3/holiday_talk.h',
            'tools/v3_holiday_actor.py','tools/v3_holiday_rewards.py')})


def prepare(source,output,lock):
    output=output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'build'):raise ValueError('Use a fresh ignored actor output')
    report=discover(source);base,prior=inputs(lock)
    report['native']=native_contract(base)
    motion=prior.get('equipment_resources',{}).get('npc_extra',{}).get('motion')
    if motion:
        owner=by_vrom(base)[0x8681F0].extract(base)
        if sha256(owner)!=motion['owner_sha256']:raise ValueError('Changed installed holiday motion owner')
        report['native'].update(motion_services=motion,
            motion_indices_bound=True,walking_only_schedule_bound=True,
            callback_cadence_verified=True,native_callback_cadence_executed=False)
    dialogue=prior.get('equipment_resources',{}).get('npc_extra',{}).get('dialogue')
    if dialogue:
        npc=prior['equipment_resources']['npc_extra'];packet=npc['packet'];code=dialogue['code']
        at=packet['physical']+0x2800
        if sha256(base[at:at+code['bytes']])!=code['sha256']:
            raise ValueError('Changed installed holiday dialogue transport')
        report['native'].update(dialogue_transport=dialogue,
            message_transport_bound=True,continuation_bound=True,native_conversation_executed=False)
    report['base_sha256']=sha256(base);report['base_abi']=prior['runtime_abi']
    output.mkdir(parents=True)
    report['kernel']=compile_kernel(output,name='holiday_actor')
    report['kernel']['stack_usage']=(output/'holiday_actor.su').read_text()
    report['native']['kernel']=compile_kernel(output,name='holiday_npc')
    report['native']['kernel']['stack_usage']=(output/'holiday_npc.su').read_text()
    write_new(output/'actor.json',(json.dumps(report,indent=2)+'\n').encode());return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--lock',type=Path,required=True)
    args=p.parse_args()
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    r=prepare(source,args.output,args.lock)
    print(json.dumps(dict(kernel=r['kernel'],native=r['native']['kernel']),indent=2))
