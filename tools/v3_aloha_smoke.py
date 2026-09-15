"""Current native aloha artwork, item readers, and complete outfit initialization."""
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK
from v3_aloha_runtime import BLOB, PACKAGE_OFFSET, PACKAGE_BYTES
from v3_npc_draw_smoke import boot_proofs


def exercise(debug, rom_path, record):
    path=Path(rom_path)
    rom=path.read_bytes(); report=json.loads((path.parent/'build.json').read_text())
    if sha256(rom)!=report['output_sha256'] or report.get('runtime_abi')!=55:
        raise ValueError('Aloha check requires the exact current cartridge')
    files=by_vrom(rom); blob=files[BLOB].extract(rom)
    prefix=blob[:0xC000]; package=blob[PACKAGE_OFFSET:PACKAGE_OFFSET+PACKAGE_BYTES]
    proofs=boot_proofs(rom)
    bridges={}

    def check(label,address,expected):
        actual=debug.read_memory(address,len(expected))
        record({'aloha_check':label,'address':f'{address:08X}','bytes':len(expected),
                'assertion':'passed' if actual==expected else 'failed',
                'expected_sha256':sha256(expected),'observed_sha256':sha256(actual)})
        if actual!=expected:raise ValueError('Native aloha mismatch: '+label)

    def call(address,args,expected=None):
        target=bridges.get(address,address)
        result=debug.call(f'{target:08X}',args,return_address=MODULE_RAM+0x6480,
                          verified_code=proofs.get(target))
        record(result)
        if expected is not None and result['return_value']!=expected:
            raise ValueError('Unexpected native aloha return value at '+f'{address:08X}')
        return result['return_value']

    check('complete startup prefix',0x80460000,prefix)
    check('complete shared package and clothing helper',0x80473000,package)
    saved=debug.read_memory(0x8046C000,864)
    check('selected clothing profile loaded',0x8046C010,bytes.fromhex(report['save_runtime']['profile_hex']))
    size=0xA00; allocation=call(0x8009BFC0,[size])
    if allocation%16 or not MODULE_RAM+RESERVATION<=allocation<=0x80400000-size:
        raise ValueError('Aloha fixture allocation is invalid')
    texture,palette,name,item,animal=(allocation+n for n in (0x10,0x230,0x280,0x2D0,0x320))
    edge=b'V3AL'*4
    guards=(allocation,texture+512,palette-16,palette+32,name-16,name+32,
            item-16,item+16,animal-16,animal+0x540,allocation+size-16,
            TEST_STACK-0x800,TEST_STACK+0x40)
    for at in guards:debug.write_memory(at,edge)
    bridge=allocation+0x900
    wrappers=b''.join(struct.pack('>4I',0x08000000|(target>>2&0x3FFFFFF),0,0,0)
                       for target in (0x804608F0,0x80460B8C))
    debug.write_memory(bridge,wrappers)
    call(0x8002FE00,[bridge,len(wrappers)])
    call(0x80034CE0,[bridge,len(wrappers)])
    proofs[bridge]=proofs[bridge+16]=(bridge,wrappers)
    bridges={0x804608F0:bridge,0x80460B8C:bridge+16}
    land=debug.read_memory(0x80129E00,10)
    profile_address=0x80460020+163
    selected=debug.read_memory(profile_address,1)
    debug.write_memory(0x80129E00,b'Forest!!\x12\x34')
    try:
        # Retain the original N64 garment at the donor's numerical slot.
        call(0x800B1EDC,[texture,palette,0x1A])
        check('original 1A complete texture',texture,files[0xB68000].extract(rom)[0x3400:0x3600])
        check('original 1A complete palette',palette,files[0xB88000].extract(rom)[0x340:0x360])
        for row in report['clothing']['imports']:
            ident=int(row['item_id'],16); index=row['resource_index']; vrom=int(row['vrom'],16)
            data=blob[vrom-BLOB:vrom-BLOB+544]
            call(0x804608F0,[index,0],vrom)
            call(0x804608F0,[index,1],vrom+512)
            debug.write_memory(item,struct.pack('>H',ident)+b'\xA5\x5A')
            call(0x80460B8C,[item],index)
            check('full NPC clothing identity retained',item,struct.pack('>H',ident)+b'\xA5\x5A')
            call(0x800B1EDC,[texture,palette,index])
            check(row['name']+' complete texture',texture,data[:512])
            check(row['name']+' complete palette',palette,data[512:])
            debug.write_memory(name,b'!'*32)
            call(0x801969C8,[name,16,ident],1)
            check('complete clothing item name',name,row['name'].encode().ljust(16,b' ')+b'!'*16)
            call(0x800A5630,[ident],12)
            call(0x800C0194,[ident],row['price'])
        rows={int(r['actor_id'],16):r for r in report['villager_text']['imports']}
        for actor in (0xE0DA,0xE0DB,0xE0ED):
            row=rows[actor]; cloth=int(row['applied_clothing_id'],16)
            expected=bytearray(b'\xA5'*0x540)
            struct.pack_into('>HH',expected,0,actor,0x1234)
            expected[4:10]=b'Forest';expected[11]=row['personality']
            expected[0x4E5:0x4E9]=bytes.fromhex(row['saved_default_key'])
            struct.pack_into('>H',expected,0x520,cloth)
            for entry,args in ((0x800AA29C,[animal,actor,0]),(0x800AA218,[animal,actor,255,0]),
                               (0x800AD8C4,[animal,actor&255])):
                debug.write_memory(animal,b'\xA5'*0x540)
                call(entry,args)
                check(row['name']+' complete native initializer',animal,expected)
        # Changing one selected bit must not disable its neighbour or cherry shirt.
        debug.write_memory(profile_address,bytes((selected[0]&~4,)))
        call(0x804608F0,[0x101A,0],0)
        call(0x804608F0,[0x101B,0],0x022E2400)
        call(0x804608F0,[0x10BF,0],0x0220F000)
        call(0x800A5630,[0x341A],0)
        call(0x800A5630,[0x341B],12)
        debug.write_memory(name,b'!'*32)
        call(0x801969C8,[name,16,0x341A],0)
        check('disabled garment name is no-write',name,b'!'*32)
        debug.write_memory(animal,b'\xA5'*0x540)
        call(0x800AD8C4,[animal,218])
        check('missing exact outfit does not write partial defaults',animal,b'\xA5'*0x540)
        debug.write_memory(item,bytes.fromhex('341AA55A'))
        call(0x80460B8C,[item],0)
        check('disabled NPC index retains the native fallback',item,bytes.fromhex('2400A55A'))
        for index in (0x101A,0x101C,0xFFFFFFFF):call(0x800B1EDC,[texture,palette,index])
        check('invalid clothing calls retain texture',texture,data[:512])
        check('invalid clothing calls retain palette',palette,data[512:])
    finally:
        debug.write_memory(profile_address,selected)
        debug.write_memory(0x80129E00,land)
    for at in guards:check('fixture and stack guard',at,edge)
    check('complete prefix restored',0x80460000,prefix)
    check('complete shared package immutable',0x80473000,package)
    check('complete saved state retained',0x8046C000,saved)
    check('test-only dispatch bridges retained',bridge,wrappers)
    check('land restored',0x80129E00,land)
    check('translation guard',0x8019C8D0,bytes.fromhex('AF32C0DE')*4)
    check('no faulted thread',0x8003CE34,bytes(4))
    call(0x8009C040,[allocation])
    return {'native_complete_garments':4,'native_imported_item_records':3,
            'native_default_initializers':9,'subset_rejection_tested':True,
            'ordinary_gameplay_or_save_reload':False,'requires_checkpoint_restore':True}
