"""Load complete NPC/quest owners and execute changed native instruction windows."""
import json
from pathlib import Path
import struct
from types import SimpleNamespace
from aflib import by_vrom,sha256
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM
from v3_asset_loader import BLOB
from v3_furniture_room_smoke import extend
from v3_npc_draw_smoke import boot_proofs
import v3_camper_quest as runtime


def exercise(debug,rom_path,record):
    path=Path(rom_path);rom=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(rom)!=report['output_sha256'] or report['runtime_abi']!=78:
        raise ValueError('Camper quest probe requires the current ABI 78 cartridge')
    files,boot=by_vrom(rom),boot_proofs(rom);quest=report['camper_quest']
    def check(label,address,value):
        actual=debug.read_memory(address,len(value))
        record(dict(camper_quest_check=label,address=f'{address:08X}',bytes=len(value),
            assertion='passed' if actual==value else 'failed',expected_sha256=sha256(value),
            observed_sha256=sha256(actual),observed_hex=actual.hex() if len(actual)<=8 else None))
        if actual!=value: raise ValueError('Native camper quest mismatch: '+label)
    def call(address,args):
        result=debug.call(f'{address:08X}',args,return_address=MODULE_RAM+0x6480,
                          verified_code=boot.get(address));record(result)
        return result['return_value']
    blob=files[BLOB].extract(rom);offset=runtime.PACKAGE+runtime.RAM-runtime.PACKAGE_RAM
    check('complete installed camper code',runtime.RAM,blob[offset:offset+quest['code']['bytes']])
    saved=debug.read_memory(0x80126EA0,65536);owner=debug.read_memory(0x804A1A00,560)
    size=0x800;allocation=call(0x8009BFC0,[size])
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x80400000-size:
        raise ValueError('Camper quest fixture allocation failed')
    # The title's normal heap cannot hold a second complete 136-KiB NPC owner.
    # While its game thread is paused, borrow part of the existing model pool,
    # snapshot it, and restore it before resuming. This tests the real loader
    # and instructions, not ordinary overlay allocation or NPC construction.
    scratch,scratch_size=0x80580000,0x24000
    pool=report['furniture']['bank_pool']
    if not pool['start']<=scratch<scratch+scratch_size<=pool['end']:
        raise ValueError('Quest probe scratch escapes the installed model pool')
    scratch_before=debug.read_memory(scratch,scratch_size)
    base,actor,stack=scratch+16,allocation+0x40,allocation+0x400
    edge=b'V3CQ'*4
    for at in (allocation,allocation+size-16,scratch,scratch+scratch_size-16):
        debug.write_memory(at,edge)
    before=debug.command('g')
    if len(before)!=71*16 or int(before[37*16:38*16],16)&0xFFFFFFFF!=0x800D334C:
        raise ValueError('Camper quest windows require a paused native frame')
    original=[int(before[i:i+16],16) for i in range(0,len(before),16)]
    def registers(start):
        regs=original.copy()
        for i in range(1,32):
            if i not in (26,27): regs[i]=(0x13579000+i)<<32 | (0x2468A000+i)
        regs[29],regs[37]=extend(stack),extend(start)
        return regs
    def window(label,regs,end,expected,compared):
        breakpoint=f'0,{end:x},4'
        if debug.command('Z'+breakpoint)!='OK': raise ValueError('Camper quest breakpoint refused')
        try:
            if debug.command('G'+''.join(f'{n:016x}' for n in regs))!='OK':
                raise ValueError('Camper quest register setup refused')
            stopped=debug.command('c');raw=debug.command('g')
            observed=[int(raw[i:i+16],16) for i in range(0,len(raw),16)]
            differences={str(i):[f'{expected[i]:016X}',f'{observed[i]:016X}']
                         for i in compared if expected[i]!=observed[i]}
            passed=stopped[:3] in ('T05','S05') and observed[37]&0xFFFFFFFF==end and not differences
            record(dict(camper_quest_window=label,register_differences=differences,
                        assertion='passed' if passed else 'failed'))
            if not passed: raise ValueError('Camper quest register/delay failure: '+label)
        finally:
            debug.command('z'+breakpoint);debug.command('G'+before)
    windows=0
    for row in quest['owners']:
        vrom,rvrom=int(row['vrom'],16),int(row['relocation_vrom'],16);ram=row['ram']
        data,reloc=files[vrom].extract(rom),files[rvrom].extract(rom)
        if (sha256(data),sha256(reloc))!=(row['patched_sha256'],row['relocation_sha256']):
            raise ValueError('Changed camper quest test owner')
        sections=struct.unpack_from('>5I',reloc)
        spec=SimpleNamespace(ram=ram,resident_bytes=len(data)+sections[3],sections=sections)
        if spec.resident_bytes+len(reloc)>=scratch_size-32: raise ValueError('Owner overlaps scratch guard')
        expected=relocate_verified_data(spec,data,reloc,base,address_constants=row['address_constants'],
                                       memory_end=0x80800000)
        call(0x800262D0,[vrom,vrom+len(data),ram,ram+spec.resident_bytes,
                        base,base+spec.resident_bytes,len(reloc)])
        check('complete actual relocated owner and BSS',base,expected)
        hook=base+row['hook']-ram
        if vrom!=0x849B50:
            for identity in (0xD000,0xD05E,0xD08F):
                debug.write_memory(stack,b'\xA5'*0x100)
                regs=registers(hook-12);regs[3]=extend(identity)
                wanted=regs.copy()
                profile=0x23 if identity==0xD08F else struct.unpack_from('>h',data,
                    row['address_constants'][0]+identity*2-ram)[0]
                wanted[1]=0xD08F;wanted[8]=identity*2;wanted[9]=extend(profile)
                wanted[4]=extend(stack+0x44);wanted[31]=extend(hook+12)
                compared=(*range(26),28,29,30,31,33,34,*range(38,70))
                window(f'{vrom:08X}/{identity:04X}',regs,hook+12,wanted,compared)
                expected_stack=bytearray(b'\xA5'*0x100);struct.pack_into('>h',expected_stack,0x56,profile)
                check('only original profile stack slot written',stack,expected_stack);windows+=1
        else:
            for identity,hello,greeted,want in ((0xD08F,1,0,4),(0xD08F,0,1,5),
                    (0xD08F,0,0,5),(0xD05E,1,0,4),(0xD05E,0,0,5),(0xE000,1,0,1)):
                debug.write_memory(actor,bytes(6)+struct.pack('>H',identity)+bytes(8))
                debug.write_memory(base+0x809571B0-ram,struct.pack('>I',hello))
                debug.write_memory(base+0x809571A4-ram,b'\xA5')
                debug.write_memory(0x804A1A10,bytes([greeted]));debug.write_memory(stack,b'\xA5'*0x100)
                regs=registers(hook);regs[16]=extend(actor);wanted=regs.copy()
                wanted[2],wanted[4],wanted[5],wanted[31]=want,identity,hello,extend(hook+20)
                compared=(0,2,3,4,5,6,7,*range(10,26),28,29,30,31,33,34,*range(38,70))
                window(f'quest/{identity:04X}/hello={hello}/flag={greeted}',regs,
                       hook+len(runtime.QUEST_BEFORE),wanted,compared)
                check('native quest mode',base+0x809571A4-ram,bytes([want]))
                check('summer-only first-talk session transition',0x804A1A10,
                      bytes([1 if identity==0xD08F and hello==1 else greeted]))
                check('quest leaves caller stack intact',stack,b'\xA5'*0x100);windows+=1
    debug.write_memory(0x804A1A00,owner)
    check('complete saved town untouched',0x80126EA0,saved)
    check('independent camper owner restored',0x804A1A00,owner)
    for at in (allocation,allocation+size-16,scratch,scratch+scratch_size-16):
        check('fixture guard',at,edge)
    debug.write_memory(scratch,scratch_before)
    check('complete borrowed model storage restored',scratch,scratch_before)
    for at,value in ((0x804A1F50,'AFCA11ED'),(0x804A2FF0,'AFACC0DE'),(0x8019C8D0,'AF32C0DE')):
        check('owner/package guard',at,bytes.fromhex(value)*4)
    check('no faulted thread',0x8003CE34,bytes(4));call(0x8009C040,[allocation])
    return dict(native_owners_loaded=3,native_profile_and_quest_windows=windows,
        npc_construction_or_complete_conversations=False,summer_english_messages=False,
        ordinary_gameplay_or_persistence=False,requires_checkpoint_restore=True)
