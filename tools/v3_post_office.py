"""Prepare the complete source account/reward category without enabling it.

Numerical bank controls run the actual donor functions against a scoped view;
the native UI, Pelly, saved ownership, and real mail queue remain explicit owners.
"""
import argparse
import json
import os
from pathlib import Path
import re
import struct
import subprocess

from aflib import sha256
from apply_translation import write_new
from toolchain import IMAGE
from v3_asset_loader import ROOT
from v3_furniture_pipeline import Source
from v3_holiday_participants import clean,constants,read
from v3_password_policy import function

REFERENCES={
    'src/game/m_bank_ovl.c':'4a552f4229affbd3faeca2b522a26c166da199d2aeea6f1df5d07677bbde00a7',
    'src/game/m_mail.c':'80902dd956135c455466afae51e5450d2da37563fae83c0a394b1964db60f36d',
    'src/actor/npc/ac_npc_post_girl.c':'0e6692625359fa7d16ce7ed7877c6699f4b3bd50dbbfe7fa963ddf0e632f5d90',
    'src/actor/npc/ac_npc_post_girl.c_inc':'4a10254e56dcfcf9b7bfe196cb9e746048cbe7699c34626c70bbc6dfe886d523',
}
HEADER_REFERENCES={
    'include/types.h':'e05027e9cfee0101ba42f025d55f6b28c69f842b14a301f7f9ed67167f759528',
    'include/audio_defs.h':'c90b684aacc7489cc4a005b7ec810dde5f4f628f6f6eeeaad8ba61216d7f37cf',
    'include/m_name_table.h':'636228dda6f5a145a1c33f886d4d574e01cd460e0062dd7502d18db2a472e3cb',
    'include/m_private.h':'160ffd2557dfbb1442fd053f9b6ca12f8f192e4054a35ad726da2461a9dba8bd',
    'include/m_bank_ovl.h':'d6fa4648c25c8344f6aa84a3bcb4328e42abbfd80f8faa83a7eeebd1a382ab33',
    'include/m_submenu.h':'d8b64717f9a40599ecec16b06bb16f6783e00a7aa15750e5958ca93499706751',
    'include/m_lib.h':'2fff7707b699a6cf42f0891900ecceaf4effe2027b9d5fc8338368bdd9b75d05',
}
NUMERIC=('mBN_now_bell_2_bell','mBN_cursol_2_keta','mBN_total_item_bell',
    'mBN_bank_ok','mBN_move_Play','mBN_bank_ovl_init')
PELLY=('aPG_Set_continue_msg_num','aPG_ChangeMsgData','aPG_set_post_status',
    'aPG_ask_for_business','aPG_msg_win_open_wait','aPG_msg_win_close_wait',
    'aPG_deposit_before','aPG_deposit_menu_close_wait','aPG_deposit_after',
    'aPG_msg_win_open_wait_init','aPG_msg_win_close_wait_init','aPG_repay_after_init',
    'aPG_deposit_menu_close_wait_init','aPG_deposit_after_recover_init','aPG_set_talk_info')
PELLY_HEADERS={
    'ac_npc_post_girl.h':'08afd0aee17adf207fc273493e84119553f65df47f051ebb7a46af34515cb24a',
    'm_msg.h':'3c8970eaabbe27e4bddf0145929492260e56f42572898893b0fc6cda6f3a4094',
    'm_msg_enum.h':'217f44997a2f4113c6fcf2fd955fb1b2ad01f50394089621c92fe5cb0d2c5554',
    'm_choice.h':'bb8fc5347821769955e9f11d52ba8f6b464fa6e7056e8673cac14fcfe30c0a57',
    'm_demo.h':'ee115d213a0331b4fa588fa8fb6adfb4481105108ac2e39d42ef41ad7eb75786',
    'm_post_office.h':'5f51bcf1b629469982d3fd9949be3e2fe05438740c3554f1db1a9d0c5715ac42',
}
SOURCES=('tools/v3_post_office.py','overlays/v3/bank_account.h','overlays/v3/bank_account.c',
    'overlays/v3/bank_source_adapter.h','overlays/v3/bank_source_adapter.c')


def discover(source):
    receipts={};texts={};families={}
    for path,digest in REFERENCES.items():
        text=read(path,receipts)
        if receipts[path]['sha256']!=digest:raise ValueError('Changed complete postal source: '+path)
        texts[path]=text
        names=re.findall(r'^(?:(?:extern|static)\s+)?\w[\w *]*?\b((?:mBN_|aPG_)\w*)\([^;{}]*\)\s*\{',text,re.M)
        rows=[]
        for name in names:
            offsets=[at for at,entries in source.functions.items() if any(n==name for n,_ in entries)]
            if len(offsets)!=1:raise ValueError('Ambiguous complete account function: '+name)
            _,row=source.function(offsets[0]);rows.append(row)
        if names:families[path]=rows
    raw,mail=source.function(0x4CE5C)
    if len(raw)!=268 or sha256(raw)!='b6066e945f2c289ac475cfc5fbda66873432f42eb305419da3af1f40880e236f':
        raise ValueError('Changed complete postal milestone owner')
    data=source.raw('l_mml_postoffice_info')
    if len(data)!=64 or sha256(data)!='d243cdb56951f56246bdede24c0b50b568b633eae9edcea539e0388fafefa648':
        raise ValueError('Changed complete source savings milestones')
    rows=[dict(template=t,item=f'{i:04X}',paper=f'{p:04X}',received_mask=f,balance=b)
        for t,i,p,f,b in struct.iter_unpack('>IHHII',data)]
    amounts=source.raw('aNSM_sack_amount');items=source.raw('aNSM_itemNo')
    if amounts!=struct.pack('>4I',100,1000,10000,30000) or items!=struct.pack('>4H',0x2103,0x2100,0x2101,0x2102):
        raise ValueError('Changed source money bags or native correspondence')
    if len(families['src/game/m_bank_ovl.c'])!=16:
        raise ValueError('Incomplete bank source owner')
    return texts,dict(format='AFV3-POST-OFFICE-PREPARED-1',references=receipts,
        functions=families,mail_function=mail,rewards=rows,reward_sha256=sha256(data),
        source_rel_sha256=sha256(source.rel),source_symbols_sha256=sha256(source.symbols.encode()),
        numerical_functions=list(NUMERIC),compiled_frontend=False,native_money_bound=False,
        native_dialogue_bound=False,native_account_bound=False,saved_record_installed=False,
        ordinary_mail_bound=False,acquisition_installed=False,record_bytes=48)


def generate(source):
    texts,report=discover(source)
    body='\n\n'.join(clean(function(texts['src/game/m_bank_ovl.c'],name)) for name in NUMERIC)
    body=body.replace('Common_Get(now_private)','af_bank_source_view')
    for before,after in (
        ('mPr_GetPossessionItemSumWithCond','af_bank_source_sum'),
        ('mPr_GetPossessionItemIdxWithCond','af_bank_source_find'),
        ('mPr_SetPossessionItem','af_bank_source_set'),
        ('sAdo_SysTrgStart','af_bank_source_request_sound')):body=body.replace(before,after)
    macros=constants(body,report['references'],headers=('types.h','audio_defs.h','m_name_table.h',
        'm_private.h','m_bank_ovl.h','m_submenu.h','m_lib.h'))
    for name,digest in HEADER_REFERENCES.items():
        if report['references'][name]['sha256']!=digest:
            raise ValueError('Changed source banking constants: '+name)
    amounts=struct.unpack('>4I',source.raw('aNSM_sack_amount'))
    items=struct.unpack('>4H',source.raw('aNSM_itemNo'))
    prelude='''#include "bank_source_adapter.h"
#include "bank_constants.h"
static Private_c *af_bank_source_view;
static Private_c af_bank_source_storage;
static u32 af_bank_source_sound;
static void af_bank_source_request_sound(int n) {af_bank_source_sound=(u32)n;}
static void af_bank_source_close(mSM_MenuInfo_c *menu,int direction) {(void)direction;menu->closed=1;}
static int af_bank_source_sum(Private_c *p,mActor_name_t item,int condition) {
 int count=0;for(int i=0;i<15;i++)if(p->inventory.items[i]==item && p->inventory.conditions[i]==condition)count++;
 return count;
}
static int af_bank_source_find(Private_c *p,mActor_name_t item,int condition) {
 for(int i=0;i<15;i++)if(p->inventory.items[i]==item && p->inventory.conditions[i]==condition)return i;
 return -1;
}
static void af_bank_source_set(Private_c *p,int slot,mActor_name_t item,int condition) {
 if(slot>=0 && slot<15) {p->inventory.items[slot]=item;p->inventory.conditions[slot]=(u8)condition;}
}
'''
    prelude+='static int aNSM_sack_amount[4]={'+','.join(map(str,amounts))+'};\n'
    prelude+='static mActor_name_t aNSM_itemNo[4]={'+','.join(map(str,items))+'};\n'
    adapter=(ROOT/'overlays/v3/bank_source_adapter.c').read_text()
    return {'bank_source.c':prelude+body+'\n'+adapter,'bank_constants.h':macros},report


def pelly(source):
    texts,report=discover(source)
    pieces=[]
    for name in PELLY:
        part=clean(function(texts['src/actor/npc/ac_npc_post_girl.c_inc'],name))
        if name.endswith('_init'):
            part=part.replace('{','{\n    (void)actorx; (void)game;',1)
        pieces.append(part)
    body='\n\n'.join(pieces)
    # The matching decompilation names an eight-byte array, but the actual call
    # writes eleven characters (nine digits and two commas). Allocate the full
    # formatter result rather than reproducing that unsafe source declaration.
    if body.count('u8 str[8];')!=1:raise ValueError('Changed complete Pelly balance formatter contract')
    body=body.replace('u8 str[8];','u8 str[11];')
    if body.count('Now_Private')!=2:raise ValueError('Changed Pelly borrowed account/loan consumers')
    body=body.replace('Now_Private','af_pg_private')
    macros=constants(body,report['references'],headers=('types.h','ac_npc_post_girl.h',
        'm_msg.h','m_msg_enum.h','m_choice.h','m_demo.h','m_submenu.h','m_post_office.h'))
    for name,digest in PELLY_HEADERS.items():
        if report['references']['include/'+name]['sha256']!=digest:raise ValueError('Changed complete Pelly constants: '+name)
    rows=[row for row in report['functions']['src/actor/npc/ac_npc_post_girl.c_inc'] if row['symbol'] in PELLY]
    if len(rows)!=len(PELLY):raise ValueError('Missing complete Pelly conversation functions')
    prelude='#include "bank_pelly_source.h"\n#include "pelly_constants.h"\nstatic AFBankPellyPrivate *af_pg_private;\n'
    generated=prelude+body+'\n'+(ROOT/'overlays/v3/bank_pelly_source.c').read_text()
    return {'pelly_source.c':generated,'pelly_constants.h':macros},dict(
        functions=rows,references=report['references'],source_action_count=30,
        full_balance_field_bytes=11,native_actor_bytes=0x958,borrowed_fields=True,
        installed=False,native_menu_and_message_io_bound=False)


def prepare(output,lock):
    from v3_furniture_install import inputs
    output=Path(output).resolve()
    if output.exists() or not output.is_relative_to(ROOT/'build'):raise ValueError('Use a fresh ignored account preparation')
    base,prior=inputs(lock)
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    generated,report=generate(source);output.mkdir(parents=True)
    for name,text in generated.items():write_new(output/name,text.encode())
    write_new(output/'post-office-rewards.bin',source.raw('l_mml_postoffice_info'))
    docker=['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
        '-v',f'{ROOT}:/source:ro','-v',f'{output}:/out','-w','/out','--entrypoint']
    def run(tool,*args):
        result=subprocess.run(docker+['/n64_toolchain/bin/mips64-elf-'+tool,IMAGE,*args],
            capture_output=True,text=True,timeout=60)
        if result.returncode:raise ValueError(result.stdout+result.stderr)
        return result.stdout
    flags=['-c','-Os','-EB','-mabi=32','-march=vr4300','-mfix4300','-G0','-mno-abicalls','-fno-pic',
        '-ffreestanding','-fno-builtin','-fno-common','-fno-stack-protector','-ffunction-sections',
        '-fdata-sections','-fstack-usage','-Wall','-Wextra','-Werror','-I/source/overlays/v3','-I/out']
    run('gcc',*flags,'bank_source.c','-o','bank-source.o')
    run('gcc',*flags,'/source/overlays/v3/bank_account.c','-o','bank-account.o')
    run('ld','-EB','-r','bank-source.o','bank-account.o','-o','post-office.o')
    unbound=run('nm','--undefined-only','post-office.o').strip().splitlines()
    if {line.split()[-1] for line in unbound}-{'memcpy','memset'}:
        raise ValueError('Unexpected bank kernel dependencies: '+str(unbound))
    report.update(base_sha256=sha256(base),base_abi=prior['runtime_abi'],
        generated_sha256={n:sha256((output/n).read_bytes()) for n in generated},
        sources={n:sha256((ROOT/n).read_bytes()) for n in SOURCES},
        object=dict(sha256=sha256((output/'post-office.o').read_bytes()),compiler=IMAGE,flags=flags,
            size=run('size','post-office.o'),linked=False,unbound_services=unbound))
    write_new(output/'prepared.json',(json.dumps(report,indent=2)+'\n').encode())
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-lock',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();report=prepare(args.output,args.base_lock)
    print(json.dumps({k:report[k] for k in ('base_abi','record_bytes','acquisition_installed','object')}))


if __name__=='__main__':main()
