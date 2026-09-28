"""Link the shared diary UI and prepare native menu hooks, without publishing."""
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256
from apply_translation import write_new
from catalogue_names import Image
from editor_pixel_fix import flat_rows
from letter_ui_fix import compile_part
from npc_mail_show import relocate_verified_data
from toolchain import IMAGE
from v3_furniture_install import inputs
from v3_furniture_pipeline import ROOT
from v3_console_disk_install import reservations

RAM=0x806A0000
MEMORY={'code':(RAM,0x8000),'state':(0x806A8000,0x1000),'art':(0x806B0000,144240+16)}
KEYBOARD=(0x3E70000,0x3E80000,0x80885140,0x2B50)
HBOARD=(0x78A560,0x78ADC0,0x808828D0,0x2A50)
KEYBOARD_SHA='8927f2a00a2636816bfbb7f24b6f876f0ad080febf493c7f8cccbb6e5dbde944'
KEYBOARD_REL_SHA='4bf303b9cfd014e1cd9cf8187fb1735fad6bb950985081beeab9af9d2058981e'
SOURCES=('tools/v3_diary_ui.py','overlays/v3/diary_screen.c','overlays/v3/diary_screen.h',
    'overlays/v3/diary_draw.c','overlays/v3/diary_draw.h','overlays/v3/diary_editor.c',
    'overlays/v3/diary_editor.h','overlays/v3/diary_hboard.c')


def resident(out,prepared,screen):
    out.mkdir(parents=True,exist_ok=False)
    docker=['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
        '-v',f'{ROOT}:/source:ro','-v',f'{out}:/out','-w','/out','--entrypoint']
    def run(tool,*args):
        result=subprocess.run(docker+['/n64_toolchain/bin/mips64-elf-'+tool,IMAGE,*args],
            capture_output=True,text=True,timeout=60)
        if result.returncode:raise ValueError(result.stdout+result.stderr)
        return result.stdout
    core=prepared['compiled']['symbols']
    bindings={n:core[n] for n in ('af_diary_menu_open','af_diary_menu_input',
        'af_diary_menu_grid','af_diary_layout')}
    bindings.update(af_diary_submenu_open=0x800C4DD8,af_diary_screen_trigger=0x80078DF4,
        af_diary_screen_button=0x80078D78,af_diary_screen_y=0x80078E5C,
        af_diary_screen_sound=0x800D1A9C,af_hboard_font_line=0x80090E98)
    flags=['-c','-Os','-EB','-mabi=32','-march=vr4300','-mfix4300','-G0','-mno-abicalls',
        '-fno-pic','-ffreestanding','-fno-builtin','-fno-common','-fno-stack-protector',
        '-ffunction-sections','-fdata-sections','-fstack-usage','-Wall','-Wextra','-Werror',
        '-D_LANGUAGE_C','-DF3DEX_GBI_2','-I/source/upstream/af/lib/ultralib/include',
        '-I/source/'+str(screen.relative_to(ROOT))]
    objects=[]
    for name in ('diary_screen','diary_draw'):
        run('gcc',*flags,'/source/overlays/v3/'+name+'.c','-o',name+'.o');objects.append(name+'.o')
    script=f'''OUTPUT_ARCH(mips)
SECTIONS {{
 . = 0x{RAM:08X};
 .text : {{ *(.text .text.*) . = ALIGN(16); *(.rodata .rodata.*) . = ALIGN(16); }}
 .forbidden : {{ *(.data .data.* .bss .bss.* COMMON) }}
 /DISCARD/ : {{ *(.reginfo .MIPS.abiflags .pdr .comment .gnu.attributes .note.*) }}
 ASSERT(SIZEOF(.forbidden) == 0, "Diary UI must use caller-owned state")
 ASSERT(SIZEOF(.text) <= 0x7FF0, "Diary UI code exceeds reservation")
}}
'''
    write_new(out/'image.ld',script.encode())
    run('ld','-EB','-T','image.ld',*[f'--defsym={k}=0x{v:X}' for k,v in bindings.items()],
        '-Map=image.map','-o','image.elf',*objects)
    if run('nm','--undefined-only','image.elf').strip():raise ValueError('Unbound diary UI entry')
    symbols={f[2]:int(f[0],16) for line in run('nm','--defined-only','image.elf').splitlines()
        if len(f:=line.split())==3}
    run('objcopy','-O','binary','-j','.text','image.elf','code.bin')
    code=(out/'code.bin').read_bytes()
    state_bytes=struct.unpack_from('>I',code,symbols['af_diary_screen_bytes']-RAM)[0]
    if state_bytes>MEMORY['state'][1]-16:raise ValueError('Diary screen state exceeds reservation')
    write_new(out/'image.asm',run('objdump','-d','image.elf').encode())
    return dict(ram=RAM,bytes=len(code),sha256=sha256(code),symbols=symbols,bindings=bindings,
        state_bytes=state_bytes,flags=flags,toolchain=IMAGE,
        stack_usage=''.join((out/(n+'.su')).read_text() for n in ('diary_screen','diary_draw')))


def hooks(base,compiled,prepared,out):
    files=by_vrom(base);owner=files[0x7749C0].extract(base);reports={};growth=0
    core=prepared['compiled']['symbols'];exports=compiled['symbols']
    for name,(vrom,reloc,ram,owner_at) in (('hboard',HBOARD),('keyboard',KEYBOARD)):
        old=files[vrom].extract(base);rel=files[reloc].extract(base)
        if name=='keyboard':
            if sha256(old)!=KEYBOARD_SHA or sha256(rel)!=KEYBOARD_REL_SHA:
                raise ValueError('Changed complete accepted keyboard')
            bindings=dict(af_grid_context=ram+28608,af_grid_owned=ram+24620,
                af_grid_editor_prepare=0x8088B278,af_diary_keyboard_init=0x8088B2AC,
                af_diary_keyboard_update=0x80886724,af_diary_keyboard_input=0x8088C62C,
                af_diary_keyboard_feedback=0x8088596C,af_diary_keyboard_done=0x808860A0,
                af_diary_keyboard_exchange=0x8088A8FC,
                af_diary_keyboard_sound=0x800D1A9C,
                af_diary_layout=core['af_diary_layout'],af_diary_menu_edit=core['af_diary_menu_edit'])
            calls={0x80888484:('af_diary_editor_init',0x8088B2AC)}
            source='/source/overlays/v3/diary_editor.c'
        else:
            # Whole native owner, including constructor's automatic house editor,
            # must still match the retained native disassembly.
            mapped=(ROOT/'build/v3-diary-category-work-01/native-hboard-map/code.bin').read_bytes()
            if old!=mapped or len(old)!=2144:raise ValueError('Changed native HBOARD owner')
            bindings={n:exports[n] for n in ('af_diary_screen_init','af_diary_screen_set_proc','af_diary_screen_destruct')}
            bindings.update(af_diary_hboard_previous_init=0x80882FDC,
                af_diary_hboard_previous_proc=0x80882FAC,af_diary_hboard_previous_destruct=0x808830E8)
            calls={0x808830C8:('af_diary_hboard_init',0x80882FDC),
                0x808830D0:('af_diary_hboard_proc',0x80882FAC)}
            source='/source/overlays/v3/diary_hboard.c'
        spec=dict(vrom=vrom,reloc=reloc,ram=ram,sha=sha256(old),reloc_sha=sha256(rel),
            imports=bindings,calls=calls)
        data,new_rel,report=compile_part('diary_'+name,base,out/name,spec=spec,source=source)
        allowed=set(report['touched_offsets']);data=bytearray(data)
        if name=='keyboard':
            at=0x8088883C-ram
            if struct.unpack_from('>I',data,at)[0]!=0x80886724 or (0x42000000|at) not in flat_rows(new_rel,len(data)):
                raise ValueError('Changed native keyboard PLAY dispatch')
            struct.pack_into('>I',data,at,ram+report['symbols']['af_diary_editor_update']);allowed.update(range(at,at+4))
        for base_at in (0x80200010,0x80370010):
            a=relocate_verified_data(Image(ram,len(old),struct.unpack_from('>5I',rel)),old,rel,base_at)
            b=relocate_verified_data(Image(ram,len(data),struct.unpack_from('>5I',new_rel)),data,new_rel,base_at)
            if any(a[i]!=b[i] for i in range(len(a)) if i not in allowed):
                raise ValueError('Diary hooks change unrelated native menu bytes')
        native_end=ram+len(old)+struct.unpack_from('>I',rel,12)[0]
        before=struct.unpack_from('>7I',owner,owner_at)
        if before[:4]!=(vrom,vrom+len(old),ram,native_end):raise ValueError('Changed menu owner descriptor')
        after=list(before);after[1]=vrom+len(data);after[3]=ram+len(data)
        if name=='hboard':
            if before[4:7]!=(0x8088306C,0x808830E8,0x80882FAC):raise ValueError('Changed HBOARD lifecycle')
            after[5]=ram+report['symbols']['af_diary_hboard_destruct']
            after[6]=ram+report['symbols']['af_diary_hboard_proc']
        # Installation must relocate these DMA owners to free VROM slots, not
        # overwrite the following native relocation or accepted keyboard data.
        extra=((len(data)+63)&~63)-((native_end-ram+63)&~63);growth+=extra
        report.update(installed=False,vrom=vrom,reloc=reloc,ram=ram,
            owner_at=owner_at,owner_before=before,owner_after=after,
            additional_pool_bytes=extra,touched_offsets=sorted(allowed),
            overlay_sha256=sha256(data),complete_prefix_preserved=True)
        write_new(out/name/'prepared.bin',bytes(data))
        write_new(out/name/'prepared.json',(json.dumps(report,indent=2)+'\n').encode())
        reports[name]=report
    native=files[CODE_VROM].extract(base)
    high,low=(struct.unpack_from('>I',native,a-CODE_RAM)[0] for a in (0x800C4AFC,0x800C4B10))
    if (high,low)!=(0x3C0E808A,0x25CEA860):raise ValueError('Changed shared native submenu arena bound')
    if growth<0 or growth>0x8000:raise ValueError('Diary hooks exceed bounded shared menu growth')
    return dict(menus=reports,additional_pool_bytes=growth,previous_pool_bound=0x8089A860,
        pool_bound=0x8089A860+growth,installed=False)


def build(base_lock,prepared_path,screen_path,output):
    output=output.resolve();prepared_path=prepared_path.resolve();screen_path=screen_path.resolve()
    if not output.is_relative_to(ROOT/'build'):raise ValueError('Diary output must be local/ignored')
    base,prior=inputs(base_lock)
    prepared=json.loads((prepared_path/'diaries.json').read_bytes())
    screen=json.loads((screen_path/'screen.json').read_bytes())
    if prepared['base_rom_sha256']!=sha256(base):raise ValueError('Diary core belongs to a different cartridge')
    if sha256((prepared_path/prepared['code_file']).read_bytes())!=prepared['code_sha256']:
        raise ValueError('Changed prepared diary core')
    for path,digest in prepared['sources'].items():
        if path.startswith('overlays/') and sha256((ROOT/path).read_bytes())!=digest:
            raise ValueError('Changed compiled diary save/controller dependency: '+path)
    if sha256((screen_path/screen['file']).read_bytes())!=screen['sha256'] or screen['bytes']!=MEMORY['art'][1]-16:
        raise ValueError('Changed complete screen packet')
    if sha256((screen_path/'diary-art.inc').read_bytes())!=screen['draw_header_sha256']:
        raise ValueError('Changed screen resource bindings')
    ranges=list(reservations(prior))
    for row in prepared['planned_memory'].values():ranges.append((row['ram'],row['ram']+row['bytes']+16))
    for name,(start,size) in MEMORY.items():
        end=start+size
        if start&15 or end>0x807DA800 or any(a<end and start<b for a,b in ranges):
            raise ValueError('Diary UI memory overlaps another owner: '+name)
        ranges.append((start,end))
    compiled=resident(output/'resident',prepared,screen_path)
    overlay=hooks(base,compiled,prepared,output)
    report=dict(format='AFV3-DIARY-UI-1',base_rom_sha256=sha256(base),base_runtime_abi=prior['runtime_abi'],
        core_sha256=prepared['code_sha256'],art_sha256=screen['sha256'],compiled=compiled,hooks=overlay,
        planned_memory={n:dict(ram=a,bytes=b,guard=a+b-16) for n,(a,b) in MEMORY.items()},
        sources={p:sha256((ROOT/p).read_bytes()) for p in SOURCES},installed=False,native_execution_tested=False,
        remaining=['Real native date/event/room entry bindings','Resident/startup and save dispatch installation',
            'Carried item readers and selection','Connected native UI/save check'])
    write_new(output/'ui.json',(json.dumps(report,indent=2)+'\n').encode())
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base-lock',type=Path,required=True);p.add_argument('--core',type=Path,required=True)
    p.add_argument('--screen',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=build(a.base_lock,a.core,a.screen,a.output)
    print(json.dumps(dict(compiled_bytes=r['compiled']['bytes'],state_bytes=r['compiled']['state_bytes'],
        additional_menu_bytes=r['hooks']['additional_pool_bytes'],installed=r['installed'])))
