"""Prepare the full source banking frontend and native-compatible UI resources.

All sixteen source bank functions remain compiled. Checked adapters retain the
native font ABI, transaction checks, motion callbacks, and complete source art.
Preparation does not attach the menu/account to a cartridge or change selections.
"""
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess

from aflib import by_vrom,CODE_RAM,CODE_VROM,sha256,u32
from apply_translation import write_new
from toolchain import IMAGE
from v3_asset_loader import ROOT
from v3_furniture_pipeline import Source,assemble_models,compile_models
from v3_holiday_participants import clean,constants,read
from v3_password_policy import function
from v3_post_office import discover,generate as numerical,pelly,HEADER_REFERENCES
from v3_ui_art import Packet

FONT_SOURCE='89f63d09c6c6b5c71b9ec2b51ffe3cba9ef89ea89714cec9ad8bef015c2316de'
FONT_HEADER='7a6354cc7d29d0d8fef7579d26fe40e58a19b0bbde40ca8c20f604f1b4134ded'
MESSAGE_SOURCE='bef7085161b41930f24d8649f26e49948c0ca673e425fdb7413e230e5fff5d0d'
SOURCES=('tools/v3_bank_frontend.py','tools/v3_post_office.py','tools/v3_ui_art.py',
    'tools/v3_furniture_art.py','overlays/v3/bank_account.c','overlays/v3/bank_account.h',
    'overlays/v3/bank_source_adapter.c','overlays/v3/bank_source_adapter.h',
    'overlays/v3/bank_frontend.h','overlays/v3/bank_frontend_source.h',
    'overlays/v3/bank_frontend_source.c','overlays/v3/bank_native.c','overlays/v3/bank_native.h',
    'translations/provenance.json','tools/v3_password_policy.py',
    'overlays/v3/bank_pelly.h','overlays/v3/bank_pelly_source.h',
    'overlays/v3/bank_pelly_source.c','overlays/v3/bank_pelly_native.c','overlays/v3/bank_admission.c')
SOURCES+=('tools/v3_bank_dialogue.py','overlays/v3/bank_dialogue.h',
    'tools/v3_post_office_install.py',
    'overlays/v3/bank_entries.c','overlays/v3/bank_entries.h',
    'tools/v3_bank_storage.py','overlays/v3/console_storage.c','overlays/v3/console_storage.h',
    'overlays/v3/save_compressed.c','overlays/v3/save_compressed.h','overlays/v3/save_runtime.c',
    'overlays/v3/holiday_cards.c','overlays/v3/holiday_cards.h',
    'overlays/v3/carried_collection.c')
ROOTS=('tyo_win_mode','tyo_win_model','tyo_win_moji2T_model','tyo_win_moji3T_model')
NATIVE_SERVICES={
    'af_bank_native_translate':(0x800E0314,264,'767212be165dde7a9be2467ffb03b98a80af114e9ad9d352e21998c6f9981ca2'),
    'af_bank_native_scale':(0x800E041C,228,'27f376ad3dc5687beaa39c0135d9bf172a320fed03d06bd42f973914ecf71a19'),
    'af_bank_native_matrix':(0x800E13C4,44,'a95d809ab70c8e9dfaa30cf0fed67d53588659763fc263399f056ff6f0a11059'),
    'af_bank_native_line':(0x80090E98,120,'052232c1c0aa7c78e1c39b74e3fce5f794f5b62bd9fdb7c1c739dd2b6443f130'),
    'af_bank_native_string_width':(0x800902CC,128,'9a28843e9e97310ebe6a2f16e9e9c4628458a8d83ca565727410ae9cf6313e16'),
    'af_bank_native_set_pocket':(0x800B8B08,132,'caea2a249bfff63d700b6ef34b0301ef01deed51c851aab13c4679e5d892dd24'),
    'af_bank_native_sound':(0x800D1A9C,40,'f474925e5fba40dfbbe8c72dcbdf15f05316a20526ee628a13bfde906513fc1f'),
    'af_bank_pelly_native_open_menu':(0x800C4D8C,36,'09c573631217451168f7e96d22287f1cd1695a421db4fa5bce50c3b25c387528'),
    'af_bank_open_queue':(0x800C4DD8,36,'f0827cdfe439f90459f5b7396d9b470b1ee8a1227db89176b0e3b7f099b259fd'),
}


def native_contract(owner,relocation,core):
    if (len(owner)!=3568 or sha256(owner)!='a180f68b34d8c5abb0609a99fa786e9d1396528240204ae11cf63d92c1ee19a9' or
        sha256(relocation)!='b0c5b4c56ce2844910a0d9a75428ce35912b00233fae22bd23144d04cb62d1ba' or
        struct.unpack_from('>5I',relocation)!=(3440,112,16,48,59)):
        raise ValueError('Changed complete translated repayment owner')
    # Whole functions above bind the source adapters. These actual retained
    # native instructions establish the distinct MenuInfo/control fields; the
    # GameCube view's layout is never used to locate any native field.
    instructions={0x80897B3C:0x8CC2068C,0x80897ED8:0x34210280,
        0x80897EE8:0x8CB9000C,0x80897F00:0x8CAE0004,
        0x80897F70:0x8C830298,0x80897FEC:0xC4400698,0x80897FF0:0xC442069C,
        0x808984E0:0x34210280,0x808984F0:0x8CD90010,
        0x80898580:0xAC2006A0,0x8089858C:0xAC400004,
        0x80898590:0xAC4E0030,0x80898594:0xAC4F0034}
    for address,word in instructions.items():
        if u32(owner,address-0x808979C0)!=word:raise ValueError('Changed native bank menu field reader')
    services={}
    for name,(address,size,digest) in NATIVE_SERVICES.items():
        raw=core[address-CODE_RAM:address-CODE_RAM+size]
        if len(raw)!=size or sha256(raw)!=digest:raise ValueError('Changed complete native bank service: '+name)
        services[name]=dict(address=address,bytes=size,sha256=digest)
    return dict(repayment_vrom=0x79B120,repayment_ram=0x808979C0,owner_sha256=sha256(owner),
        relocation_sha256=sha256(relocation),menu_slot=7,menu_info=0x10280,
        menu_control=0x10670,trigger=0x1068C,animation=0x106A0,
        texture_positions=[0x10698,0x1069C],native_services=services,
        field_instructions={f'{a:08X}':f'{w:08X}' for a,w in instructions.items()},
        private_fields=dict(pockets=0x14,conditions=0x34,wallet=0x38,loan=0x3C),
        installed=False,saved_provider_bound=False,pelly_admission_bound=False)


def admission_contract(owner,relocation,core):
    from v3_furniture_roofs import BLOCKS
    if (len(owner)!=7680 or sha256(owner)!='6c1df6be28bed6cc469f37a59ae317c6ba2ab86ba97c124f9d287da47be007ac' or
        sha256(relocation)!='ac371d4f4c5d0c87f2ffb3d56bbddfdd7f1384ecca4cca5d3e769e4306241d2f'):
        raise ValueError('Changed complete Pelly native owner')
    houses=[]
    for name,address,size,digest in BLOCKS:
        if name not in ('home_arrangement','home_upgrade_colour','current_player_home'):continue
        if sha256(core[address-CODE_RAM:address-CODE_RAM+size])!=digest:
            raise ValueError('Changed complete native banking admission field owner: '+name)
        houses.append(dict(name=name,address=address,bytes=size,sha256=digest))
    # Whole current owner guards include existing translated mail repairs. These
    # actual native reads/writes establish the distinct N64 actor/menu fields.
    fields={0x809C34A8:0xA2020724,0x809C34B0:0xAE180944,0x809C375C:0xA3100948,
        0x809C3C44:0x91040948,0x809C40D0:0x91CF1D98,
        0x809C4E84:0xAC860938,0x809C4E94:0xAC8F0940,0x809C4BB0:0x24841CBC}
    for address,word in fields.items():
        if u32(owner,address-0x809C3420)!=word:raise ValueError('Changed actual Pelly actor/menu field contract')
    return dict(owner_sha256=sha256(owner),relocation_sha256=sha256(relocation),
        houses=houses,fields={f'{a:08X}':f'{w:08X}' for a,w in fields.items()},
        native_actions=33,added_bank_actions=list(range(33,38)),
        source_bank_actions=list(range(24,29)),native_home_bytes=0xB48,
        size_offset=0x22,size_shift=6,renew_mask=8,native_completed_size=2,
        donor_minimum_size=3,homes=0x8012A428,arrangement=0x80135DFA,
        home_identity_bytes=16,loan=0x3C,submenu=0x1CBC,submenu_open=0x1D98,
        bank_flag_in_native_actor=False,compiled=True,installed=False)


def artwork(source):
    packet=Packet(source)
    packet.model('mode',[ROOTS[0]],state_only=True)
    packet.model('frame',[ROOTS[1]],texture=(32,32,2,0),palette=(14,),
        combiner=(0xFCFFFFFF,0xFFFCF438))
    packet.model('deposit',[ROOTS[2]])
    packet.model('withdraw',[ROOTS[3]],combiner=(0xFC30FFFF,0x5FFEF238))
    prepared=packet.prepared()
    entries={e['id']:e for e in json.loads((ROOT/'translations/provenance.json').read_bytes())['entries']}
    for name in ('fri_win_cash_tex','fri_win_bell_tex','tyo_win_balance_tex',
            'tyo_win_deposit_tex_rgb_ia8','tyo_win_withdraw_tex'):
        row=next(r for r in prepared[2] if r['symbol']==name)
        en=entries['v3/post-office/art/'+name]['locales']['en']
        if (en['credit']!='official' or en['resource_kind']!='bitmap' or
            en['source']['symbol']!=name or en['source']['data_offset']!=f'{row["donor_offset"]:08X}' or
            en['source']['reference_sha256']!=row['source_sha256'] or
            en['encoded_sha256']!=row['output_sha256']):raise ValueError('Missing official bank bitmap provenance: '+name)
    return prepared


def reuse_artwork(source,prepared,directory):
    directory=Path(directory).resolve();report=json.loads((directory/'prepared.json').read_bytes())
    art=report['artwork'];data=(directory/'bank-art.bin').read_bytes()
    if (report.get('format')!='AFV3-BANK-FRONTEND-PREPARED-1' or
        report['source_rel_sha256']!=sha256(source.rel) or
        report['source_symbols_sha256']!=sha256(source.symbols.encode()) or
        sha256(data)!=art['sha256'] or len(data)!=art['bytes'] or
        json.loads(json.dumps(prepared[2]))!=art['resources'] or
        json.loads(json.dumps(prepared[4]))!=art['models'] or
        (directory/'commands.c').read_text()!=prepared[5]):raise ValueError('Changed complete prepared bank artwork')
    compiled={row['layer']:data[row['native_offset']:row['native_offset']+row['bytes']]
        for row in art['compiled_models']}
    generated=assemble_models(prepared,compiled)
    if (generated[0]!=data or generated[1]!=art['model_offsets'] or
        json.loads(json.dumps(generated[2]))!=art['compiled_models'] or generated[3]):
        raise ValueError('Changed complete bank model packing/receipts')
    return generated


def generate(source):
    texts,report=discover(source)
    font=read('src/game/m_font.c',report['references'])
    if report['references']['src/game/m_font.c']['sha256']!=FONT_SOURCE:
        raise ValueError('Changed complete donor font formatter')
    names=[row['symbol'] for row in report['functions']['src/game/m_bank_ovl.c']]
    body='\n\n'.join(clean(function(texts['src/game/m_bank_ovl.c'],n)) for n in names)
    body=body.replace('Common_Get(now_private)','af_bank_source_view')
    for before,after in (
        ('mPr_GetPossessionItemSumWithCond','af_bank_source_sum'),
        ('mPr_GetPossessionItemIdxWithCond','af_bank_source_find'),
        ('mPr_SetPossessionItem','af_bank_source_set'),
        ('sAdo_SysTrgStart','af_bank_source_request_sound')):body=body.replace(before,after)
    # The complete donor Play body still backs af_bank_source_step. Only the
    # frontend's dispatch entry passes through snapshot/conservation/commit.
    if body.count('&mBN_move_Play')!=1:raise ValueError('Changed whole bank move dispatch')
    body=body.replace('&mBN_move_Play','&af_bank_frontend_play')
    body=body.replace('(mSM_MOVE_PROC)&none_proc1','&none_proc1')
    before='(*menu->pre_draw_func)(submenu, game);'
    if body.count(before)!=1:raise ValueError('Changed bank pre-draw contract')
    body=body.replace(before,before+'\n    if (!af_bank_frontend_ready()) return;')
    # Native scrolling is periodic. Float-to-u8 narrowing outside its range is
    # undefined in C; make the source's eight-bit wrap explicit after truncation.
    for axis,var in ((0,'s'),(1,'t')):
        before=f'{var} = -submenu->overlay->menu_control.texture_pos[{axis}] * 4.0f;'
        if body.count(before)!=1:raise ValueError('Changed source frame scrolling')
        body=body.replace(before,f'{var} = (u8)((int)(-submenu->overlay->menu_control.texture_pos[{axis}] * 4.0f) & 255);')
    # Original standalone declarations/static state are outside function bodies.
    prelude=numerical(source)[0]['bank_source.c'].split('static void mBN_now_bell_2_bell(',1)[0]
    prelude=prelude.replace('#include "bank_source_adapter.h"',
        '#define AF_BANK_FRONTEND 1\n#include "bank_source_adapter.h"\n#include "bank_frontend_source.h"')
    font_names=('mMsg_CutLeftSpace','mFont_suji_check','mFont_UnintToString')
    font_body='static u8 mFont_suji_data[10]={'+','.join(map(str,source.raw('mFont_suji_data')))+'};\n'+\
        '\n\n'.join(clean(function(font,n)) for n in font_names)
    if source.raw('mFont_suji_data')!=b'0123456789':raise ValueError('Changed donor numerical glyphs')
    font_rows=[]
    for name in font_names:
        offsets=[at for at,entries in source.functions.items() if any(n==name for n,_ in entries)]
        if len(offsets)!=1:raise ValueError('Ambiguous source font function')
        font_rows.append(source.function(offsets[0])[1])
    message=read('src/game/m_msg_main.c_inc',report['references'])
    if report['references']['src/game/m_msg_main.c_inc']['sha256']!=MESSAGE_SOURCE:
        raise ValueError('Changed complete donor message length helper')
    name='mMsg_Get_Length_String'
    offsets=[at for at,entries in source.functions.items() if any(n==name for n,_ in entries)]
    if len(offsets)!=1:raise ValueError('Ambiguous complete donor message length helper')
    message_row=source.function(offsets[0])[1]
    font_body+='\n'+clean(function(message,name))+'\n'
    macros=constants(body+font_body,report['references'],headers=('types.h','audio_defs.h',
        'm_name_table.h','m_private.h','m_bank_ovl.h','m_submenu.h','m_lib.h','m_font.h'))
    for path,digest in dict(HEADER_REFERENCES,**{'include/m_font.h':FONT_HEADER}).items():
        if report['references'][path]['sha256']!=digest:raise ValueError('Changed bank frontend constants: '+path)
    title=source.raw('kingaku_str$598');ok=source.raw('end_str$599')
    if title!=b'Your Account' or ok!=b'OK':raise ValueError('Changed complete official bank labels')
    entries={e['id']:e for e in json.loads((ROOT/'translations/provenance.json').read_bytes())['entries']}
    for key,symbol,data in (('account-title','kingaku_str$598',title),('account-ok','end_str$599',ok)):
        en=entries['v3/post-office/'+key]['locales']['en'];at,_=source.symbol(symbol)
        if (en['credit']!='official' or en['text'].encode()!=data or en['source']['symbol']!=symbol or
            en['source']['data_offset']!=f'{at:08X}' or en['source']['reference_sha256']!=sha256(data) or
            en['encoded_sha256']!=sha256(data)):raise ValueError('Missing official bank label provenance: '+key)
    declarations='static mBN_Ovl_c bn_ovl_data;\n'+''.join('extern Gfx '+n+'[];\n' for n in ROOTS)
    text=prelude+font_body+'\n'+declarations+body+'\n'+\
        (ROOT/'overlays/v3/bank_source_adapter.c').read_text()+'\n'+\
        (ROOT/'overlays/v3/bank_frontend_source.c').read_text()
    report.update(format='AFV3-BANK-FRONTEND-PREPARED-1',compiled_frontend=True,
        bank_functions=names,font_functions=font_rows,message_functions=[message_row],native_frontend_installed=False,
        frontend_transaction_adapter='full donor Play through guarded snapshot/conservation/commit',
        title=dict(symbol='kingaku_str$598',sha256=sha256(title),text=title.decode()),
        ok=dict(symbol='end_str$599',sha256=sha256(ok),text=ok.decode()))
    return {'bank_source.c':text,'bank_constants.h':macros},report


def prepare(output,lock,*,reuse_art=None,dialogue=None):
    from v3_furniture_install import inputs
    output=Path(output).resolve()
    if output.exists() or not output.is_relative_to(ROOT/'build'):raise ValueError('Use a fresh ignored bank frontend preparation')
    base,prior=inputs(lock)
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    files=by_vrom(base)
    native=native_contract(files[0x79B120].extract(base),files[0x79BF10].extract(base),files[CODE_VROM].extract(base))
    admission=admission_contract(files[0x8A6C10].extract(base),files[0x8A8A10].extract(base),files[CODE_VROM].extract(base))
    generated,report=generate(source);pg,pg_report=pelly(source);generated.update(pg)
    report['pelly']=pg_report;report['admission']=admission
    if dialogue is not None:
        from v3_holiday_dialogue import check_provenance
        from v3_bank_storage import layout
        dialogue=Path(dialogue).resolve()
        if not dialogue.is_relative_to(ROOT/'build'):raise ValueError('Bank dialogue must belong to ignored preparation')
        text=json.loads((dialogue/'dialogue.json').read_bytes());check_provenance(text)
        if sha256((dialogue/'bank-dialogue.c').read_bytes())!=text['generated_sha256']:
            raise ValueError('Changed generated bank dialogue mapping')
        for row in text['resources']:
            data=(dialogue/row['file']).read_bytes()
            if (len(data)!=row['bytes'] or sha256(data)!=row['sha256'] or
                sha256(files[row['vrom']].extract(base))!=row['previous_sha256']):
                raise ValueError('Changed complete bank dialogue resource or native predecessor')
        report['dialogue']=dict(text,prepared=str(dialogue.relative_to(ROOT)))
        report['saved_owner_memory']=layout(prior)
    prepared=artwork(source);output.mkdir(parents=True)
    for name,data in generated.items():write_new(output/name,data.encode())
    write_new(output/'post-office-rewards.bin',source.raw('l_mml_postoffice_info'))
    if reuse_art:
        art,offsets,models,sequence=reuse_artwork(source,prepared,reuse_art)
        write_new(output/'commands.c',prepared[5].encode())
    else:art,offsets,models,sequence=compile_models(output,prepared)
    if sequence:raise ValueError('Unexpected bank frontend drawing sequence')
    write_new(output/'bank-art.bin',art)
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
    run('gcc',*flags,'/source/overlays/v3/bank_native.c','-o','bank-native.o')
    run('gcc',*flags,'pelly_source.c','-o','pelly-source.o')
    run('gcc',*flags,'/source/overlays/v3/bank_pelly_native.c','-o','pelly-native.o')
    run('gcc',*flags,'/source/overlays/v3/bank_admission.c','-o','bank-admission.o')
    run('gcc',*flags,'/source/overlays/v3/bank_entries.c','-o','bank-entries.o')
    # Compile the full saved-town owner into this same object. Its bank calls
    # resolve to this object's one account/transaction implementation, not a
    # second busy flag or synthetic function addresses in a separate save owner.
    from v3_bank_storage import layout
    memory=layout(prior);retained=prior['save_codec']['active_storage_code']
    storage_flags=retained['flags']+['-DAF_V3_BANK_STORAGE=1',
        f'-DAF_BANK_STATE_RAM=0x{memory["account"]["ram"]:08X}u']
    saved_objects=[]
    for stem,path in (('bank-storage','console_storage'),('bank-codec','save_compressed'),
            ('bank-cards','holiday_cards'),('bank-collection','carried_collection')):
        obj=stem+'.o';run('gcc',*storage_flags,'/source/overlays/v3/'+path+'.c','-o',obj)
        saved_objects.append(obj)
    additional=[]
    if dialogue is not None:
        write_new(output/'bank-dialogue.c',(dialogue/'bank-dialogue.c').read_bytes())
        run('gcc',*flags,'bank-dialogue.c','-o','bank-dialogue.o');additional.append('bank-dialogue.o')
    objects=['bank-source.o','bank-account.o','bank-native.o','pelly-source.o',
        'pelly-native.o','bank-admission.o','bank-entries.o',*saved_objects,*additional]
    from v3_post_office_install import native_bindings
    candidates,binding_report=native_bindings(base,prior)
    undefined=set();defined=set()
    for obj in objects:
        undefined.update(line.split()[-1] for line in run('nm','--undefined-only',obj).splitlines())
        defined.update(line.split()[-1] for line in run('nm','--defined-only','--extern-only',obj).splitlines())
    # Resolve genuine external native APIs only; --defsym must never replace
    # a newly compiled implementation or saved-state provider.
    bound={name:candidates[name] for name in sorted(undefined-defined) if name in candidates}
    saved_bound={name:retained['link_symbols'][name] for name in sorted(undefined-defined-bound.keys())
        if name in retained['link_symbols']}
    if 'AF_HI_STORAGE_RAM' in saved_bound:raise ValueError('Partial saved owner unexpectedly depends on a code origin')
    all_bound=dict(bound,**saved_bound)
    run('ld','-EB','-r',*(f'--defsym={n}=0x{a:X}' for n,a in all_bound.items()),
        *objects,'-o','post-office.o')
    definitions={name:(int(address,16),kind) for address,kind,name in
        (line.split() for line in run('nm','--defined-only','--extern-only','post-office.o').splitlines())}
    if any(definitions.get(name)!=(address,'A') for name,address in all_bound.items()):
        raise ValueError('Checked native bank symbol was not bound to its real API')
    if definitions.get('af_bank_pelly_loan_balance',(0,''))[1]!='T':
        raise ValueError('Full source Pelly loan formatter is not compiled')
    for name in ('af_bank_native_account','af_v3_bank_data','af_v3_save_pack',
            'af_v3_save_check','af_v3_console_storage_commit','af_v3_console_player_clear',
            'af_v3_save_compress_bank','af_v3_save_expand_bank','af_v3_save_measure_bank'):
        if definitions.get(name,(0,''))[1]!='T':
            raise ValueError('Full saved-bank owner is not compiled: '+name)
    unbound=run('nm','--undefined-only','post-office.o').strip().splitlines()
    if {line.split()[-1] for line in unbound}-{'memcpy','memset',*ROOTS,
            'af_bank_native_translate','af_bank_native_scale','af_bank_native_matrix',
            'af_bank_native_string_width','af_bank_native_line','af_bank_native_account',
            'af_bank_now_private','af_bank_player','af_bank_native_set_pocket','af_bank_native_sound',
            'af_bank_account_mode','af_bank_home_arrangement','af_bank_native_homes',
            'af_bank_pelly_window','af_bank_pelly_continue','af_bank_pelly_disappeared','af_bank_pelly_appeared',
            'af_bank_pelly_unlock','af_bank_pelly_force','af_bank_pelly_free_string',
            'af_bank_pelly_appear','af_bank_pelly_disappear','af_bank_pelly_order','af_bank_pelly_set_order',
            'af_bank_pelly_choice_window','af_bank_pelly_choice','af_bank_pelly_mail_count',
            'af_bank_pelly_first_job','af_bank_pelly_foreigner',
            'af_bank_pelly_native_open_menu','af_bank_pelly_message_map','af_bank_pelly_message_unmap',
            'af_bank_pelly_native_number','af_bank_pelly_native_continue','af_bank_pelly_native_change',
            'af_bank_pelly_april_clip','af_bank_pelly_native_message'}:
        raise ValueError('Unexpected frontend dependencies: '+str(unbound))
    if {line.split()[-1] for line in unbound}&all_bound.keys():
        raise ValueError('Checked native bank API remains unresolved')
    report.update(base_sha256=sha256(base),base_abi=prior['runtime_abi'],native_adapter=native,
        native_bindings=binding_report,
        saved_owner=dict(compiled=True,installed=False,flags=storage_flags,memory=memory,
            retained_storage_sha256=retained['sha256'],bound_services=saved_bound,
            shared_account_implementation=True,save_format=21,card_wire=7),
        artwork_reused_from=str(Path(reuse_art).resolve().relative_to(ROOT)) if reuse_art else None,
        generated_sha256={n:sha256((output/n).read_bytes()) for n in generated},
        sources={n:sha256((ROOT/n).read_bytes()) for n in SOURCES},
        artwork=dict(bytes=len(art),sha256=sha256(art),model_offsets=offsets,
            resources=prepared[2],compiled_models=models,models=prepared[4],
            palette_slots=[14,15],shared_converter=True),
        object=dict(sha256=sha256((output/'post-office.o').read_bytes()),compiler=IMAGE,flags=flags,
            bound_native_services=bound,
            size=run('size','post-office.o'),linked=False,unbound_services=unbound))
    write_new(output/'prepared.json',(json.dumps(report,indent=2)+'\n').encode())
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-lock',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--reuse-art',type=Path)
    parser.add_argument('--dialogue',type=Path)
    args=parser.parse_args();report=prepare(args.output,args.base_lock,reuse_art=args.reuse_art,dialogue=args.dialogue)
    print(json.dumps({k:report[k] for k in ('base_abi','compiled_frontend','native_frontend_installed','object')}))


if __name__=='__main__':main()
