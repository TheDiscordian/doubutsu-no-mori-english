"""Execute actual current trade owners, selected rewards, and gift/return paths."""
import json
from pathlib import Path
import struct
from types import SimpleNamespace
from aflib import by_vrom,sha256
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM,TEST_STACK
from v3_npc_draw_smoke import boot_proofs
from v3_villager_rewards_smoke import ordinal
from v3_optional_composition import catalogue
from v3_furniture_room_smoke import extend
import v3_camper_trade as runtime


def exercise(debug,rom_path,record,*,remaining=False):
    path=Path(rom_path);rom=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(rom)!=report['output_sha256'] or report['runtime_abi']!=81:
        raise ValueError('Trade probe requires current ABI 81')
    files,boot=by_vrom(rom),boot_proofs(rom);trade=report['camper_trade'];options=catalogue(rom,report)
    def check(label,at,expected):
        actual=debug.read_memory(at,len(expected))
        record(dict(camper_trade_check=label,address=f'{at:08X}',bytes=len(expected),
            assertion='passed' if actual==expected else 'failed',
            expected_sha256=sha256(expected),observed_sha256=sha256(actual)))
        if actual!=expected:raise ValueError('Native camper trade mismatch: '+label)
    calls=0
    def call(address,args=(),proof=None,want=None):
        nonlocal calls
        result=debug.call(f'{address:08X}',list(args),return_address=MODULE_RAM+0x6480,
                          verified_code=proof or boot.get(address));calls+=1
        if want is not None:result['assertion']='passed' if result['return_value'] in want else 'failed'
        record(result)
        if result.get('assertion')=='failed':raise ValueError('Unexpected native trade return')
        return result['return_value']
    words=runtime.words;size=0xD000;allocation=call(0x8009BFC0,[size])
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x80400000-size:
        raise ValueError('Current trade fixture allocation failed')
    normal,quest,greeting,private,actor,animal,manager,categories,out=(allocation+o for o in
        (0x10,0x6010,0x9200,0xA800,0xB400,0xB600,0xBC00,0xC600,0xC620))
    edge=b'V3TR'*4
    guards=(allocation,allocation+0x6000,allocation+0x91E0,allocation+0xA300,
            private+0xA80,manager+0x8E0,allocation+size-16,TEST_STACK-0x800,TEST_STACK+0x40)
    for at in guards:debug.write_memory(at,edge)
    saved=debug.read_memory(0x80126EA0,65536)
    flags=[options[f'GAFE01-r0/item/{item:04X}']['enable_ram'] for item in runtime.TENT[:-1]]
    snapshots={at:debug.read_memory(at,n) for at,n in (
        (0x80136FD8,4),(0x8003C590,4),(0x80137000,15*56),
        (0x804A1A12,2),(0x80136FBE,1),*((at,4) for at in flags))}
    loaded={}
    for v,rv,ram,target in ((runtime.VROM,runtime.RELOC,runtime.RAM,normal),
            (runtime.QUEST,runtime.QUEST_RELOC,runtime.QUEST_RAM,quest),
            (0x03A10000,0x03A14000,0x8092CD00,greeting)):
        data,rel=files[v].extract(rom),files[rv].extract(rom);sec=struct.unpack_from('>5I',rel)
        total=len(data)+sec[3]
        call(0x800262D0,[v,v+len(data),ram,ram+total,target,target+total,len(rel)])
        expected=relocate_verified_data(SimpleNamespace(ram=ram,resident_bytes=total,sections=sec),data,rel,target)
        check('complete actual owner loading and relocation',target,expected);loaded[v]=expected
    proof=(normal,loaded[runtime.VROM][:16768])
    picker=normal+0x8091ED64-runtime.RAM;common=normal+0x8091EFDC-runtime.RAM
    state=normal+0x80921DE8-runtime.RAM
    debug.write_memory(0x80136FD8,words(private));debug.write_memory(0x80126EB4,words(35))
    debug.write_memory(categories,words(0,3,4));debug.write_memory(animal,bytes(0x528))
    debug.write_memory(animal,bytes.fromhex('E0EA'))
    def pockets(items=(),conditions=0,last=0):
        data=bytearray(0xA80);struct.pack_into('>15H',data,0x14,*(list(items)+[0]*(15-len(items))))
        struct.pack_into('>I',data,0x34,conditions);struct.pack_into('>H',data,0xA78,0x34BF)
        debug.write_memory(private,data);debug.write_memory(0x804A1A12,struct.pack('>H',last))
        debug.write_memory(out,bytes.fromhex('BEEF'))
    pocket_cases=(
        ('selected imported furniture',[0x3364],0,0,0,0x3364),
        ('last gift excluded; later carpet eligible',[0x3364,0x2600],0,0x3364,1,0x2600),
        ('wrapped and quest items excluded',[0x3364,0x2700],9,0,-1,0xBEEF),
        ('unsupported and clothing excluded',[0x3FFC,0x34BF],0,0,-1,0xBEEF))
    for label,items,cond,last,idx,item in (() if remaining else pocket_cases):
        pockets(items,cond,last);call(picker,[out],proof,(idx&0xFFFFFFFF,))
        check(label,out,struct.pack('>H',item))
    # Seed the real native RNG so the first pocket draw is followed by a tent
    # roll and a non-house roll. Never replace the RNG or award callbacks.
    def wanted(seed):
        _,s=ordinal(seed,1);r,s=ordinal(s,100);house,s=ordinal(s,10)
        return r>=80 and house>0
    seed=next(s for s in range(10000) if wanted(s))
    for item in (0x3364,0x33B0):
        for at,value in zip(flags,runtime.TENT[:-1]):debug.write_memory(at,words(value==item))
        pockets([0x3224]);debug.write_memory(state,bytes(0x30));debug.write_memory(0x8003C590,words(seed))
        call(common,[picker,animal,categories,3,1],proof)
        check('full installed common stores imported input slot',state+12,words(0))
        check('selected-only camping reward reaches real trade slots',state+0x14,struct.pack('>2H',0x3224,item))
        check('original pitfall mode retained',state+0x1C,bytes.fromhex('2512'))
        remaining=struct.unpack('>2H',debug.read_memory(state+0x18,4))
        if remaining[0]>>8!=0x26 or remaining[1]>>8!=0x27:
            raise ValueError('Summer trade lost carpet/wall categories')
        record(dict(native_camping_reward=f'{item:04X}',other_candidates=[f'{v:04X}' for v in remaining],seed=seed))
    for at in flags:debug.write_memory(at,snapshots[at])
    # Non-summer goes through the actual displaced prologue and retained body.
    debug.write_memory(0x80126EB4,words(0));pockets([0x3364],last=0x3364)
    debug.write_memory(state,bytes(0x30));call(common,[picker,animal,categories,3,1],proof)
    check('ordinary trade retains input and ignores summer-only last gift',state+0x14,bytes.fromhex('3364'))
    check('ordinary full body returns original pitfall result',state+0x1C,bytes.fromhex('2512'))
    # Previously unreached gift/reset windows, using a bounded native bzero
    # callback. The windows prove transport, not an animated conversation award.
    debug.write_memory(manager,bytes(0x8D8))
    before=debug.command('g');original=[int(before[i:i+16],16) for i in range(0,len(before),16)]
    def window(label,start,end,values):
        regs=original.copy();regs[29]=extend(TEST_STACK);regs[37]=extend(start)
        for i,value in values.items():regs[i]=extend(value)
        bp=f'0,{end:x},4'
        if debug.command('Z'+bp)!='OK':raise ValueError('Trade window breakpoint refused')
        try:
            if debug.command('G'+''.join(f'{n:016x}' for n in regs))!='OK':raise ValueError('Trade registers refused')
            stopped=debug.command('c');raw=debug.command('g');pc=int(raw[37*16:38*16],16)&0xFFFFFFFF
            passed=stopped[:3] in ('T05','S05') and pc==end
            record(dict(camper_trade_window=label,pc=f'{pc:08X}',assertion='passed' if passed else 'failed'))
            if not passed:raise ValueError('Trade caller window failed')
        finally:debug.command('z'+bp);debug.command('G'+before)
    for hook,item in ((0x8091F56C,0x3364),(0x80920AB8,0x2600)):
        debug.write_memory(manager,b'\xA5'*8)
        window('installed normal gift callback',normal+hook-runtime.RAM-8,normal+hook-runtime.RAM+8,
               {16:manager,24:item,25:0x8002F4C0})
        check('last gift full identity',0x804A1A12,struct.pack('>H',item))
        check('original callback manager and count',manager,bytes(6)+b'\xA5'*2)
    debug.write_memory(manager+0x8CC,b'\xA5'*8)
    window('installed constructor gift reset',quest+0x8095703C-runtime.QUEST_RAM,
           quest+0x80957048-runtime.QUEST_RAM,{16:manager})
    check('last gift reset',0x804A1A12,bytes(2))
    check('original constructor clear',manager+0x8CC,bytes(5)+b'\xA5'*3)
    # Execute the complete real greeting initializer and its return, instead of
    # relying on the previous mid-dispatch breakpoint in upper scratch memory.
    pockets();debug.write_memory(0x80126EB4,words(35));debug.write_memory(0x80136FBE,b'\x0C')
    debug.write_memory(actor,bytes(0x200));debug.write_memory(actor+2,b'\x03')
    debug.write_memory(actor+6,bytes.fromhex('D08F'));debug.write_memory(actor+0x174,words(animal))
    debug.write_memory(animal+11,b'\x04')
    timer=quest+0x809551C8-runtime.QUEST_RAM
    call(greeting+0xBF8,[actor,timer],(greeting,loaded[0x03A10000]),tuple(range(11754,12007)))
    for at,value in snapshots.items():debug.write_memory(at,value)
    debug.write_memory(0x80126EA0,saved);check('complete saved town restored',0x80126EA0,saved)
    for at in guards:check('fixture guard',at,edge)
    check('translation guard',0x8019C8D0,bytes.fromhex('AF32C0DE')*4)
    check('no faulted thread',0x8003CE34,bytes(4));call(0x8009C040,[allocation])
    return dict(native_calls=calls,complete_owner_loads=3,complete_common_trades=3,
        selected_camping_rewards=2,actual_gift_windows=2,actual_constructor_reset=True,
        complete_greeting_return=True,ordinary_conversation_or_save_reload=False,
        requires_checkpoint_restore=True)
