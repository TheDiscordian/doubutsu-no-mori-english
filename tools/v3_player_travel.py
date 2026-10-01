"""Prepare the connected player-record transport; native I/O installation follows.

This durability checkpoint is not a playable cartridge or a completion claim.
It retains lossless records and checks the new code against the N64 compiler.
"""
import argparse
import os
from pathlib import Path
import subprocess
import sys

from aflib import sha256,by_vrom,CODE_RAM,CODE_VROM
from apply_translation import write_new
from toolchain import IMAGE
from v3_furniture_install import ROOT,inputs
import json

DEFINES=('AF_V3_CLOTHING_PROFILE','AF_V3_REWARD_PROFILE','AF_V3_SURFACE_PROFILE',
    'AF_V3_CREATURE_PROFILE','AF_V3_INSECT_SEASONS','AF_V3_HOLIDAY_STORAGE',
    'AF_V3_EVENT_ITEM_PROFILE','AF_V3_CARRIED_PROFILE','AF_V3_CARRIED_QUEST','AF_V3_PAPER_PACKS',
    'AF_V3_CARRIED_NPC','AF_V3_GOLDEN_REWARD_STORAGE')
SOURCES=('tools/v3_player_travel.py','overlays/v3/pak_codec.c','overlays/v3/pak_codec.h',
    'overlays/v3/pak_native.c','overlays/v3/pak_native.h','overlays/v3/pak_workspace.c',
    'overlays/v3/console_storage.c','overlays/v3/console_storage.h','tests/v3_pak_native_test.c',
    'overlays/v3/save_runtime.c','overlays/v3/save_runtime.h',
    'tests/test_v3_carried_storage.py','tests/test_v3_bank_storage.py',
    'tests/v3_bank_storage_test.c','tests/v3_carried_storage_test.c','tests/v3_console_storage_test.c',
    'overlays/v3/travel_player.c','overlays/v3/travel_player.h','tests/test_v3_pak_codec.py',
    'tests/v3_pak_codec_test.c','tests/v3_travel_player_test.c',
    'overlays/v3/save_codec.h','overlays/v3/diary.c','overlays/v3/diary.h',
    'overlays/v3/diary_calendar.c','overlays/v3/holiday_cards.c','overlays/v3/holiday_cards.h',
    'overlays/v3/bank_account.c','overlays/v3/bank_account.h')
FLAGS=('-c','-Os','-EB','-mabi=32','-march=vr4300','-mfix4300','-G0','-mno-abicalls',
    '-fno-pic','-ffreestanding','-fno-builtin','-fno-common','-fno-stack-protector',
    '-ffunction-sections','-fdata-sections','-fstack-usage','-Wall','-Wextra','-Werror')


def prepare(lock,output):
    image,prior=inputs(lock)
    if(prior['runtime_abi']!=391 or prior['save_codec']['format_version']!=21 or
       prior['save_codec']['registry_version']!=5):
        raise ValueError('Player transport requires the checked current format-21 build')
    output.mkdir(parents=True,exist_ok=False)
    result=subprocess.run([sys.executable,'-m','unittest','tests.test_v3_pak_codec','-v'],
        cwd=ROOT,capture_output=True,text=True,timeout=60)
    log=result.stdout+result.stderr;print(log.strip(),flush=True)
    write_new(output/'host-tests.txt',log.encode());result.check_returncode()
    result=subprocess.run([sys.executable,'-m','unittest',
        'tests.test_v3_bank_storage.BankStorageTests.test_account_owner_migration_and_profile_rejection','-v'],
        cwd=ROOT,capture_output=True,text=True,timeout=60)
    log=result.stdout+result.stderr;print(log.strip(),flush=True)
    write_new(output/'workspace-tests.txt',log.encode());result.check_returncode()
    docker=['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
        '-v',f'{ROOT}:/source:ro','-v',f'{output.resolve()}:/out','-w','/out','--entrypoint']
    def run(tool,*args):
        p=subprocess.run(docker+['/n64_toolchain/bin/mips64-elf-'+tool,IMAGE,*args],
            check=True,capture_output=True,text=True,timeout=60)
        return p.stdout
    compiled={}
    providers=dict(prior['save_codec']['active_storage_code']['symbols'])
    native_providers=dict(af_pi_lock=0x800D6A10,af_pi_unlock=0x800D6A44,
        af_pi_open=0x80078EE0,af_pi_make=0x80078EB4,af_pi_num=0x80078F08,
        af_pi_free=0x80078FE8,af_pi_file_state=0x800CDA4C,af_pi_load=0x800CD82C,
        af_pi_save=0x800CD760,af_pi_delete=0x800CD9F0,af_pi_null_identity=0x800B7914)
    # Bind addresses to the pinned native symbol inventory, not recalled values.
    import re
    symbols=dict((name,int(value,16)) for name,value in re.findall(
        r'^(\w+) = (0x[0-9A-Fa-f]+);',
        (ROOT/'upstream/af/linker_scripts/jp/symbol_addrs_code.txt').read_text(),re.MULTILINE))
    native_names=('padmgr_LockSerialMesgQ','padmgr_UnlockSerialMesgQ',
        'mCPk_NoteOpen','mCPk_NoteMake','mCPk_NoteNum','mCPk_FreeBlockNum',
        'sCPk_FileState','sCPk_Load','sCPk_Save','sCPk_DeleteFile','mPr_NullCheckPersonalID')
    if list(native_providers.values())!=[symbols[name] for name in native_names]:
        raise ValueError('Native Pak provider addresses differ from pinned source')
    providers.update(native_providers)
    core=by_vrom(image)[CODE_VROM].extract(image)
    entries=[dict(address=a,symbol=name,before=core[a-CODE_RAM:a-CODE_RAM+8].hex())
        for a,name in ((0x8007920C,'af_v3_pak_native_write'),
            (0x800792FC,'af_v3_pak_native_read'),(0x800794E4,'af_v3_pak_native_status'))]
    storage_flags=prior['save_codec']['active_storage_code']['flags']
    run('gcc',*storage_flags,'/source/overlays/v3/console_storage.c','-o','console_storage.o')
    undefined={line.split()[-1] for line in run('nm','--undefined-only','console_storage.o').splitlines()}
    if any(name not in providers for name in undefined):
        raise ValueError('Loan-enabled storage has an unbound existing service')
    compiled['console_storage']=dict(object_sha256=sha256((output/'console_storage.o').read_bytes()),
        undefined=sorted(undefined),existing_providers={name:providers[name] for name in sorted(undefined)},
        stack_usage=(output/'console_storage.su').read_text(),flags=storage_flags,
        installed=False,new_entries=['af_v3_save_workspace_acquire','af_v3_save_workspace_release'])
    pending={'af_pi_record_export','af_pi_record_validate','af_pi_record_publish',
        'af_pi_legacy_validate','af_pi_legacy_publish','af_v3_save_workspace_acquire',
        'af_v3_save_workspace_release','af_v3_console_storage_valid','af_v3_travel_prepare'}
    expected={'pak_codec':set(),'travel_player':{
        'af_bank_valid','af_diary_days','af_diary_valid','af_holiday_cards_valid'},
        'pak_native':set(native_providers)|{name for name in pending if name.startswith('af_pi_')}|
            {'af_v3_pak_decode','af_v3_pak_encode','af_v3_pak_measure',
             'af_pi_workspace_acquire','af_pi_workspace_release'},
        'pak_workspace':{name for name in pending if name.startswith('af_v3_')}}
    for part in expected:
        run('gcc',*FLAGS,*['-D'+d+'=1' for d in DEFINES],
            f'/source/overlays/v3/{part}.c','-o',part+'.o')
        undefined={line.split()[-1] for line in run('nm','--undefined-only',part+'.o').splitlines()}
        local={'af_v3_pak_decode','af_v3_pak_encode','af_v3_pak_measure',
            'af_pi_workspace_acquire','af_pi_workspace_release'}
        if undefined!=expected[part] or any(name not in providers|dict.fromkeys(pending|local) for name in undefined):
            raise ValueError(f'Unbound or unexpected native dependencies for {part}: {undefined}')
        stack=(output/(part+'.su')).read_text()
        write_new(output/(part+'.asm'),run('objdump','-dr',part+'.o').encode())
        compiled[part]=dict(object_sha256=sha256((output/(part+'.o')).read_bytes()),
            undefined=sorted(undefined),existing_providers={name:providers[name] for name in sorted(undefined) if name in providers},
            local_dependencies=sorted(undefined&local),pending_integration=sorted(undefined&pending),
            stack_usage=stack,toolchain=IMAGE,flags=list(FLAGS)+['-D'+d+'=1' for d in DEFINES])
    receipt=dict(format='AFV3-PLAYER-TRAVEL-PREPARED-1',base_rom_sha256=sha256(image),
        runtime_abi=391,save_format=21,profile_bytes=272,player_record_bytes=14204,
        diary_player_bytes=12008,console_player_bytes=1632,note_header_bytes=96,
        max_note_bytes=0x7B00,compiled=compiled,
        sources={name:sha256((ROOT/name).read_bytes()) for name in SOURCES},
        tests=dict(host_passed=True,independent_decoder_passed=True,native_compilation_passed=True,
            guarded_current_storage_workspace_passed=True),
        installed=False,native_execution_tested=False,ordinary_visiting_tested=False,
        pak_io=dict(shared_read_write_status_implemented=True,journal_commit_last=True,
            original_notes_retained=True,device_failures_tested_with_doubles=True,
            scratch_bytes=119932,shared_save_workspace_loan_implemented=True,
            native_hooks=entries,native_hooks_installed=False,player_lifecycle_provider_installed=False),
        next_consumer='Connect record export/admission/publication and checked visitor reservation; rebuild and bind the loan-enabled storage and all three native Pak entries, then visitor item/diary/console consumers. Keep restrictions until connected.')
    write_new(output/'prepared.json',(json.dumps(receipt,indent=2,sort_keys=True)+'\n').encode())
    print(json.dumps({'output':str(output),'installed':False,'player_record_bytes':14204,
        'host_tests':'passed','native_compilation':'passed'}),flush=True)
    return receipt


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-lock',type=Path,default=ROOT/'build/v3-nook-font-repaired-02/build-lock.json')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();prepare(args.build_lock,args.output)


if __name__=='__main__':main()
