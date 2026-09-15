"""Execute the current tent's real floor and point-light entries in isolation."""
import json
from pathlib import Path
import struct
from aflib import by_vrom,sha256
from runtime_layout import MODULE_RAM,TEST_STACK
from v3_furniture_room_smoke import extend
import v3_campsite_environment as runtime


def exercise(debug,rom_path,record,*,remaining=False):
    path=Path(rom_path);rom=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(rom)!=report['output_sha256'] or report['runtime_abi']!=82:
        raise ValueError('Environment probe requires current ABI 82')
    files=by_vrom(rom);blob=files[runtime.BLOB].extract(rom)
    def check(label,at,expected):
        actual=debug.read_memory(at,len(expected));passed=actual==expected
        record(dict(campsite_environment_check=label,address=f'{at:08X}',bytes=len(expected),
            assertion='passed' if passed else 'failed',expected_sha256=sha256(expected),observed_sha256=sha256(actual)))
        if not passed:raise ValueError('Native environment mismatch: '+label)
    def call(address,args=(),want=None):
        result=debug.call(f'{address:08X}',list(args),return_address=MODULE_RAM+0x6480)
        if want is not None:result['assertion']='passed' if result['return_value']==want else 'failed'
        record(result)
        if result.get('assertion')=='failed':raise ValueError('Unexpected environment result')
        return result['return_value']
    saved={at:debug.read_memory(at,n) for at,n in (
        (0x80126EA0,65536),(0x80136EA2,1),(0x80137655,1),(0x80113844,1),(0x80113868,1))}
    check('complete installed environment and adjacent final guard',runtime.RAM,
        blob[runtime.PACKAGE+runtime.RAM-runtime.PACKAGE_RAM:runtime.PACKAGE+runtime.PACKAGE_SIZE])
    allocation=call(0x8009BFC0,[0x100]);edge=b'V3EN'*4
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x803FFF00:
        raise ValueError('Environment fixture allocation failed')
    out=allocation+0x20
    for at in (allocation,allocation+0xF0,TEST_STACK-0x400,TEST_STACK+0x40):debug.write_memory(at,edge)
    cases=((14,68),(31,72),(0,0xFFFFFFFF)) if remaining else ((35,68),(14,68),(31,72),(0,0xFFFFFFFF))
    for scene,floor in cases:
        debug.write_memory(0x80126EB4,runtime.words(scene));call(0x800BEEC4,want=floor)
    # Each call uses five genuine o32 arguments; guard padding checks store sizes.
    for scene,draw,pos,rgb,power,flame,want in (
        (35,1,(120,80,120),(235,190,185),6000,0,1),
        (21,1,(160,180,240),(160,160,160),1000,0xA5A5,1),
        (31,1,(160,80,38),(250,240,120),300,1,1),
        (35,0,None,None,None,None,0)):
        debug.write_memory(0x80126EB4,runtime.words(scene));debug.write_memory(0x80136EA2,bytes([draw]))
        debug.write_memory(out,b'\xA5'*32)
        call(0x80096D60,[0,out,out+8,out+16,out+24],want)
        expected=bytearray(b'\xA5'*32)
        if pos is not None:
            struct.pack_into('>3h',expected,0,*pos);expected[8:11]=bytes(rgb)
            struct.pack_into('>H',expected,16,power);struct.pack_into('>H',expected,24,flame)
        check('complete point-light fields and padding',out,expected)
    # Execute the real field caller through its store; do not just seed floorIdx.
    original=debug.command('g');registers=[int(original[i:i+16],16) for i in range(0,len(original),16)]
    def window(label,start,end,values):
        regs=registers.copy();regs[29]=extend(TEST_STACK);regs[37]=extend(start)
        for i,value in values.items():regs[i]=extend(value)
        bp=f'0,{end:x},4'
        if debug.command('Z'+bp)!='OK':raise ValueError('Environment breakpoint refused')
        try:
            if debug.command('G'+''.join(f'{n:016x}' for n in regs))!='OK':raise ValueError('Environment registers refused')
            stopped=debug.command('c');raw=debug.command('g');after=[int(raw[i:i+16],16)&0xFFFFFFFF for i in range(0,len(raw),16)]
            passed=stopped[:3] in ('T05','S05') and after[37]==end
            record(dict(campsite_environment_window=label,pc=f'{after[37]:08X}',assertion='passed' if passed else 'failed'))
            if not passed:raise ValueError('Environment caller window failed')
            return after
        finally:debug.command('z'+bp);debug.command('G'+original)
    debug.write_memory(0x80126EB4,runtime.words(35))
    window('actual field caller stores native audio-floor selector',0x80087128,0x80087140,{})
    check('actual field floorIdx',0x80137655,b'\x44')
    debug.write_memory(0x80113844,b'\x01');debug.write_memory(0x80113868,b'\x01')
    for address in (0x800F9064,0x800F9170):
        result=window('full footstep reader reaches native sound dispatcher',address,0x800F8E24,
            {4:68,5:0x1234,6:0,31:MODULE_RAM+0x6480})
        passed=result[4]==0x306 and result[5]==0x1234 and result[6]==0
        record(dict(campsite_environment_sound_id=result[4],assertion='passed' if passed else 'failed'))
        if not passed:raise ValueError('Floor reader selects the wrong actual sound')
    # These bounded windows stop before audio queuing, with no hardware playback.
    for at,value in saved.items():debug.write_memory(at,value)
    check('complete saved town restored',0x80126EA0,saved[0x80126EA0])
    for at in (allocation,allocation+0xF0,TEST_STACK-0x400,TEST_STACK+0x40):check('environment guard',at,edge)
    check('translation guard',0x8019C8D0,bytes.fromhex('AF32C0DE')*4)
    check('no faulted thread',0x8003CE34,bytes(4));call(0x8009C040,[allocation])
    return dict(native_floor_getter=True,native_field_store=True,player_and_npc_sound_dispatch=True,
        native_point_info=True,timed_lamp=False,ordinary_scene=False,saved_data_written=False,
        requires_checkpoint_restore=True)
