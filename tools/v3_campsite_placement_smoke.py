"""Native tent lookup, foreground placement/removal, and cleanup-list checks."""
import json
from pathlib import Path
import struct
from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from runtime_layout import MODULE_RAM
from v3_asset_loader import BLOB
from v3_furniture_room_smoke import extend
from v3_npc_draw_smoke import boot_proofs
import v3_campsite_placement as runtime


def exercise(debug, rom_path, record):
    path = Path(rom_path); rom = path.read_bytes()
    report = json.loads((path.parent/'build.json').read_bytes())
    if sha256(rom) != report['output_sha256'] or report['runtime_abi'] != 75:
        raise ValueError('Placement probe requires the current ABI 75 cartridge')
    files = by_vrom(rom); blob = files[BLOB].extract(rom)
    code,boot = files[CODE_VROM].extract(rom),boot_proofs(rom)
    def check(label, address, expected):
        actual = debug.read_memory(address,len(expected))
        record(dict(placement_check=label,address=f'{address:08X}',bytes=len(expected),
            assertion='passed' if actual==expected else 'failed',
            expected_sha256=sha256(expected),observed_sha256=sha256(actual),
            observed_hex=actual.hex() if len(actual)<=32 else None))
        if actual!=expected: raise ValueError('Native tent placement mismatch: '+label)
    def call(address, args, expected=None):
        result = debug.call(f'{address:08X}',args,return_address=MODULE_RAM+0x6480,
                            verified_code=boot.get(address))
        if expected is not None:
            result['assertion'] = 'passed' if result['return_value']==expected else 'failed'
        record(result)
        if expected is not None and result['return_value']!=expected:
            raise ValueError('Unexpected native tent placement return')
        return result['return_value']
    def put(address, value): debug.write_memory(address,struct.pack('>I',value))
    for address,size in ((runtime.CODE,report['campsite_placement']['code']['bytes']),
                         (runtime.CLEANUP,40)):
        at = runtime.PACKAGE+address-runtime.PACKAGE_RAM
        check('complete installed placement code/table',address,blob[at:at+size])
    for row in report['campsite_placement']['hooks']:
        check('installed native placement/cleanup hook',row['address'],bytes.fromhex(row['after']))
    original_save = debug.read_memory(0x80126EA0,65536)
    original_lists = debug.read_memory(0x80137000,15*56)
    original_runtime = debug.read_memory(0x8046C000,864)
    original_field = debug.read_memory(0x8013A248,4)
    original_lots = debug.read_memory(0x80106818,4)
    allocation = call(0x8009BFC0,[0x800])
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x803FF800:
        raise ValueError('Small placement fixture allocation failed')
    field,lots,stack = allocation+0x20,allocation+0x400,allocation+0x600
    edge = b'V3PL'*4
    debug.write_memory(allocation,edge); debug.write_memory(allocation+0x7F0,edge)
    debug.write_memory(field,bytes(0x380)); debug.write_memory(lots,bytes(0x100))
    stack_bytes = b'\xA5'*0x100
    debug.write_memory(stack,stack_bytes)
    before = debug.command('g')
    if len(before)!=71*16 or int(before[37*16:38*16],16)&0xFFFFFFFF!=0x800D334C:
        raise ValueError('Placement windows require a paused native game frame')
    original_registers = [int(before[i:i+16],16) for i in range(0,len(before),16)]
    windows = 0
    for start,end,source,dest,base in ((0x8008D4A8,0x8008D4B0,9,3,3),
                                     (0x8008D5BC,0x8008D5C4,6,4,4)):
        for item in (0x5804,0x5829,0x5843,0x5849):
            registers = original_registers.copy()
            for i in range(1,32):
                if i not in (26,27): registers[i]=(0x13579000+i)<<32 | (0x2468A000+i)
            registers[source],registers[base]=extend(item),extend(0x80100000+item)
            registers[29],registers[37]=extend(stack),extend(start)
            wanted = registers.copy(); wanted[1]=0x5849
            wanted[dest]=8 if item==0x5849 else code[0x8010119C+item-CODE_RAM]
            wanted[10 if dest==3 else 11]=extend(0xA5A5A5A5 if dest==3 else 0x80100000)
            breakpoint=f'0,{end:x},4'
            if debug.command('Z'+breakpoint)!='OK': raise ValueError('Placement breakpoint refused')
            try:
                if debug.command('G'+''.join(f'{n:016x}' for n in registers))!='OK':
                    raise ValueError('Placement register setup refused')
                stopped=debug.command('c'); after=debug.command('g')
                observed=[int(after[i:i+16],16) for i in range(0,len(after),16)]
                compared=(*range(26),28,29,30,31,33,34,*range(38,70))
                differences={str(i):[f'{wanted[i]:016X}',f'{observed[i]:016X}']
                             for i in compared if wanted[i]!=observed[i]}
                passed=stopped[:3] in ('T05','S05') and observed[37]&0xFFFFFFFF==end and not differences
                record(dict(placement_window=f'{start:08X}',item=f'{item:04X}',
                    register_differences=differences,assertion='passed' if passed else 'failed'))
                if not passed: raise ValueError('Placement native register/delay failure')
                windows+=1
            finally:
                debug.command('z'+breakpoint); debug.command('G'+before)
    check('classification leaves caller stack intact',stack,stack_bytes)
    # Complete native area function, retaining donor's origin-only event-lot
    # query semantics. The placement callback separately reserves nine cells.
    call(0x8008D574,[8,8,0x5849,8,8],1)
    call(0x8008D574,[7,8,0x5849,8,8],0)
    call(0x8008D574,[8,8,0x5829,8,8],1)
    # Use the native saved-town-foreground path while an indoor field is active.
    # This small data fixture is not a constructed scene or a rendered tent.
    debug.write_memory(field,bytes.fromhex('3000'))
    put(0x8013A248,field); put(0x80106818,lots)
    grid=0x80126EA0+0x62A8
    debug.write_memory(grid,bytes(512))
    call(0x8008D3A4,[0x5849,1,1,0,8,0],0)
    check('out-of-bounds 3x3 placement changes no cells',grid,bytes(512))
    call(0x8008D3A4,[0x5849,1,1,8,8,0],1)
    placed=bytearray(512)
    fill=struct.unpack_from('>H',code,0x80106A08-CODE_RAM)[0]
    for z in range(7,10):
        for x in range(7,10): struct.pack_into('>H',placed,2*(z*16+x),0x5849 if (x,z)==(8,8) else fill)
    check('native complete nine-cell tent foreground',grid,placed)
    check('native field update flag set',field+0x163,b'\x01')
    call(0x8008D3A4,[0x5849,1,1,8,8,1],1)
    restored=debug.read_memory(grid,512)
    reserve=struct.unpack_from('>H',restored,2*(8*16+8))[0]
    expected=bytearray(512); struct.pack_into('>H',expected,2*(8*16+8),reserve)
    if not 0x5810<=reserve<0x5825: raise ValueError('Native removal did not restore a housing-lot marker')
    check('native removal clears all eight reserved cells and restores the lot',grid,expected)
    check('all town NpcLists retained',0x80137000,original_lists)
    check('complete import save runtime retained',0x8046C000,original_runtime)
    # No FlashRAM or user save is written. The runner additionally restores
    # the entire checkpoint, including native update/burial/decal state.
    debug.write_memory(0x80126EA0,original_save)
    debug.write_memory(0x8013A248,original_field); debug.write_memory(0x80106818,original_lots)
    for at in (allocation,allocation+0x7F0): check('fixture guard',at,edge)
    for at,value in ((0x804A1F50,'AFCA11ED'),(0x804A2CF0,'AFC7CA1E'),
                     (0x804A2FF0,'AFACC0DE'),(0x8019C8D0,'AF32C0DE')):
        check('retained owner/package guard',at,bytes.fromhex(value)*4)
    check('no faulted thread',0x8003CE34,bytes(4))
    call(0x8009C040,[allocation])
    return dict(native_classification_windows=windows,native_tent_foreground_placement=True,
        native_tent_foreground_removal=True,native_area_reader=True,
        full_event_finish_executed=False,constructed_scene_or_gpu=False,flash_write_or_reload=False,
        event_manager_or_conversation=False,requires_checkpoint_restore=True)
