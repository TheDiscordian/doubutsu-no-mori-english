"""Prepare the connected player-record transport; native I/O installation follows.

This durability checkpoint is not a playable cartridge or a completion claim.
It retains lossless records and checks the new code against the N64 compiler.
"""
import argparse
import os
from pathlib import Path
import subprocess
import sys

from aflib import sha256
from apply_translation import write_new
from toolchain import IMAGE
from v3_furniture_install import ROOT,inputs
import json

DEFINES=('AF_V3_CLOTHING_PROFILE','AF_V3_REWARD_PROFILE','AF_V3_SURFACE_PROFILE',
    'AF_V3_CREATURE_PROFILE','AF_V3_INSECT_SEASONS','AF_V3_HOLIDAY_STORAGE',
    'AF_V3_EVENT_ITEM_PROFILE','AF_V3_CARRIED_PROFILE','AF_V3_CARRIED_QUEST','AF_V3_PAPER_PACKS',
    'AF_V3_CARRIED_NPC','AF_V3_GOLDEN_REWARD_STORAGE')
SOURCES=('tools/v3_player_travel.py','overlays/v3/pak_codec.c','overlays/v3/pak_codec.h',
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
    docker=['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
        '-v',f'{ROOT}:/source:ro','-v',f'{output.resolve()}:/out','-w','/out','--entrypoint']
    def run(tool,*args):
        p=subprocess.run(docker+['/n64_toolchain/bin/mips64-elf-'+tool,IMAGE,*args],
            check=True,capture_output=True,text=True,timeout=60)
        return p.stdout
    compiled={}
    providers=prior['save_codec']['active_storage_code']['symbols']
    expected={'pak_codec':set(),'travel_player':{
        'af_bank_valid','af_diary_days','af_diary_valid','af_holiday_cards_valid'}}
    for part in expected:
        run('gcc',*FLAGS,*['-D'+d+'=1' for d in DEFINES],
            f'/source/overlays/v3/{part}.c','-o',part+'.o')
        undefined={line.split()[-1] for line in run('nm','--undefined-only',part+'.o').splitlines()}
        if undefined!=expected[part] or any(name not in providers for name in undefined):
            raise ValueError(f'Unbound or unexpected native dependencies for {part}: {undefined}')
        stack=(output/(part+'.su')).read_text()
        write_new(output/(part+'.asm'),run('objdump','-dr',part+'.o').encode())
        compiled[part]=dict(object_sha256=sha256((output/(part+'.o')).read_bytes()),
            undefined=sorted(undefined),existing_providers={name:providers[name] for name in sorted(undefined)},
            stack_usage=stack,toolchain=IMAGE,flags=list(FLAGS)+['-D'+d+'=1' for d in DEFINES])
    receipt=dict(format='AFV3-PLAYER-TRAVEL-PREPARED-1',base_rom_sha256=sha256(image),
        runtime_abi=391,save_format=21,profile_bytes=272,player_record_bytes=14204,
        diary_player_bytes=12008,console_player_bytes=1632,note_header_bytes=96,
        max_note_bytes=0x7B00,compiled=compiled,
        sources={name:sha256((ROOT/name).read_bytes()) for name in SOURCES},
        tests=dict(host_passed=True,independent_decoder_passed=True,native_compilation_passed=True),
        installed=False,native_execution_tested=False,ordinary_visiting_tested=False,
        next_consumer='Bind bounded I/O and record lifecycle to all native passport callers, then visitor item/diary/console consumers; do not remove restrictions without that implementation.')
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
