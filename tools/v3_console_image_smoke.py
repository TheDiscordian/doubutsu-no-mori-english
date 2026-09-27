"""Execute the installed streaming reader with real PI transfers, silently."""
import json
from pathlib import Path
import struct
from aflib import by_vrom,sha256,yaz0_decode
from runtime_layout import MODULE_RAM,RESERVATION,TEST_STACK
from v3_asset_loader import BLOB
from v3_npc_draw_smoke import boot_proofs


def exercise(debug,rom_path,record):
    path=Path(rom_path);rom=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(rom)!=report['output_sha256']:raise ValueError('Changed console image test cartridge')
    images=report['equipment_resources']['console_images'];storage=report['equipment_resources']['console_storage']
    blob=by_vrom(rom)[BLOB].extract(rom);packet=images['packet']
    expected=blob[packet['blob_offset']:packet['blob_offset']+packet['bytes']]
    count=0
    def check(label,address,wanted):
        nonlocal count
        actual=debug.read_memory(address,len(wanted));count+=1
        record(dict(console_image_check=label,address=f'{address:08X}',bytes=len(wanted),
            assertion='passed' if actual==wanted else 'failed',sha256=sha256(actual)))
        if actual!=wanted:raise ValueError('Native console image check failed: '+label)
    check('complete authenticated startup packet',packet['ram'],expected)
    check('idle console state',storage['state']['ram'],struct.pack('>4I',0x41464335,0,0,0))
    # Before any town load, with the game thread paused, borrow only the declared
    # transient save workspaces. Restore the emulator checkpoint after testing.
    output=storage['scratch']['ram']+16;work=storage['hash']['ram']+16;edge=b'NES!'*4
    saved=debug.read_memory(storage['state']['ram'],storage['state']['bytes'])
    for at in (output-16,work-16,work+1024,TEST_STACK-0x800,TEST_STACK+0x40):debug.write_memory(at,edge)
    symbol=images['compiled']['symbols']['af_v3_console_image_native_load'];calls=0
    proofs=boot_proofs(rom)
    def call(address,args,proof=None):
        nonlocal calls
        result=debug.call(f'{address:08X}',args,return_address=MODULE_RAM+0x6480,
                          verified_code=proofs.get(address) if proof is None else proof)
        record(result);calls+=1
        return result['return_value']
    # Use the existing checked low-memory jump stub convention; the debugger's
    # general native-proof range deliberately stops below Expansion Pak RAM.
    bridge=call(0x8009BFC0,[32])
    if bridge&15 or not MODULE_RAM+RESERVATION<=bridge<=0x80400000-32:
        raise ValueError('Console test bridge allocation failed')
    stub=struct.pack('>2I',0x08000000|(symbol>>2&0x3FFFFFF),0)
    debug.write_memory(bridge,stub);debug.write_memory(bridge+16,edge)
    call(0x8002FE00,[bridge,32]);call(0x80034CE0,[bridge,32])
    # One full iNES image and the full QD image cover distinct source formats;
    # this tests cartridge reading/decoding, not NES/FDS game execution.
    for game in (1,10):
        row=images['streaming']['rows'][game-1];size=row['image_bytes']
        if size+32>storage['scratch']['bytes']:raise ValueError('Fixture exceeds declared scratch')
        at=images['pool']['physical']+row['pool_offset']
        decoded=yaz0_decode(rom[at:at+row['packed_bytes']])
        if sha256(decoded)!=row['image_sha256']:raise ValueError('Changed complete donor image')
        debug.write_memory(output+size,edge)
        if call(bridge,[game,output,size,work],(bridge,stub))!=0:
            raise ValueError('Native console image load failed')
        check(f'complete decoded game {game}',output,decoded)
        check('game output end guard',output+size,edge)
    for at in (output-16,work-16,work+1024,TEST_STACK-0x800,TEST_STACK+0x40):check('scratch/stack guard',at,edge)
    for key in ('scratch','hash'):check('retained save workspace guard',storage[key]['guard'],bytes.fromhex('AF4355DE')*4)
    check('complete console save state untouched',storage['state']['ram'],saved)
    check('bridge guard',bridge+16,edge)
    call(0x8009C040,[bridge])
    return dict(console_image_native='passed',native_calls=calls,memory_assertions=count,
        game_ids=[1,10],real_physical_rom_reads=True,emulator_gameplay_tested=False)
