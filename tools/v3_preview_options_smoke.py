"""Bounded native checks for changed starting-house and ocean-movement paths.

Diagnostic calls use a disposable checkpoint and restore the complete machine.
This is not an ordinary new-town, travel, or save/reload playthrough.
"""
import json
from pathlib import Path
import struct

from aflib import by_vrom, CODE_RAM, CODE_VROM, sha256
from runtime_layout import MODULE_RAM
from v3_asset_loader import BLOB
from v3_starting_diary import HOOK, WRAPPER, SETTING, wrapper


def exercise(debug, rom_path, record):
    image = Path(rom_path).read_bytes()
    report = json.loads((Path(rom_path).parent/'build.json').read_bytes())
    if sha256(image) != report['output_sha256']:
        raise ValueError('Native options check requires its exact composed ROM')
    values = report['composition']['behaviours']
    if any(values.get(key) != 'GameCube' for key in ('starting-diary','coastal-fish-movement')):
        raise ValueError('Check the real house/ocean GameCube profile')
    files = by_vrom(image); core = files[CODE_VROM].extract(image)
    world = report['equipment_resources']['creature_fish']['world']
    packet = files[BLOB].extract(image)[world['packet']['blob_offset']:
        world['packet']['blob_offset']+world['packet']['bytes']]
    ram = world['packet']['ram']; tail = ram+WRAPPER
    house_base, stride = 0x8012A428, 0xB48
    actor = MODULE_RAM+0x6500
    checks = 0

    def check(label, address, expected):
        nonlocal checks
        actual = debug.read_memory(address,len(expected))
        record({'preview_options_check':label,'address':f'{address:08X}',
            'bytes':len(expected),'assertion':'passed' if actual==expected else 'failed',
            **({'differences':[{'offset':i,'expected':wanted,'observed':seen}
                for i,(wanted,seen) in enumerate(zip(expected,actual)) if wanted!=seen][:16]}
                if actual!=expected else {})})
        if actual != expected:
            raise ValueError('Native preview options mismatch: '+label)
        checks += 1

    def call(address, arguments, verified_code=None):
        result = debug.call(f'{address:08X}', arguments, return_address=MODULE_RAM+0x6480,
            verified_code=verified_code)
        record(result); return result['return_value']

    def flush_instructions(address, size):
        # The diagnostic changes this return between source alternatives. Use
        # the native loader's real cache sequence before executing either one.
        for helper_address, digest in (
            (0x8002FE00,'5306341d7122fdbbae63d48917c76f7f6c2ee0321e490862302581561bf0474c'),
            (0x80034CE0,'713e7b78373df6fbf3d030b5237e9c1e2148c9443cbfdf938f2e8ffdf8e2d326')):
            code = debug.read_memory(helper_address,116)
            if sha256(code)!=digest:
                raise ValueError('Changed native cache helper')
            call(helper_address,[address,size],(helper_address,code))

    check('startup ready before new-house initialization',0x8019ACD0,struct.pack('>I',1))
    check('house tail loaded by ordinary startup',tail,wrapper(0x2B10))
    check('real new-house branch',HOOK,core[HOOK-CODE_RAM:HOOK-CODE_RAM+8])
    check('selected house mode',ram+SETTING,struct.pack('>I',1))
    houses = debug.read_memory(house_base,4*stride)
    pockets = debug.read_memory(0x80126EC0,4*0xBD0)
    saved_actor = debug.read_memory(actor,0x280)
    mode = world['patrol_mode']['ram']
    helper = world['compiled']['symbols']['donor']
    helper_code = packet[helper-ram:helper-ram+36]
    check('shared ocean helper with origin branch removed',helper,helper_code)
    original_return = bytes.fromhex('03e0000800000000')
    installed_return = core[HOOK-CODE_RAM:HOOK-CODE_RAM+8]
    try:
        for gc in (True,False):
            debug.write_memory(HOOK,installed_return if gc else original_return)
            flush_instructions(HOOK,8)
            # Filled rooms catch writes outside the two source cells, room
            # surfaces, and existing cassette placement. Never touch a real save.
            fill = bytes([0xA5])*(4*stride); debug.write_memory(house_base,fill)
            expected = bytearray(fill)
            for index in (0,1,2,3,7):
                slot = index&3
                call(0x80094744,[index])
                default = core[0x801075E0-CODE_RAM+slot*16:0x801075E0-CODE_RAM+(slot+1)*16]
                ut_x,ut_z = struct.unpack_from('>2I',default,4)
                tape = struct.unpack_from('>H',default,12)[0]
                at = slot*stride
                expected[at+0x14:at+0x16] = bytes((default[1],default[0]))
                struct.pack_into('>H',expected,at+0x38+ut_z*32+ut_x*2,tape)
                if gc:
                    struct.pack_into('>H',expected,at+0x38+34,0x30F8)
                    struct.pack_into('>H',expected,at+0x238+34,0x2B10)
                check(('GameCube' if gc else 'N64')+f' complete house data after index {index}',
                    house_base,bytes(expected))
        for gc in (0,1):
            debug.write_memory(mode,struct.pack('>I',gc))
            for origin in (0,1):
                data = bytearray(0x280); data[0x1DA] = origin
                debug.write_memory(actor,bytes(data))
                result = call(helper,[actor],(helper,helper_code))
                if result != gc:
                    raise ValueError('Ocean movement does not apply equally to both origins')
                record({'preview_options_check':'ocean mode for '+('original' if not origin else 'imported')+' fish',
                    'mode':gc,'return':result,'assertion':'passed'})
                checks += 1
        check('all player inventories unchanged',0x80126EC0,pockets)
        check('no native fault',0x8003CE34,bytes(4))
    finally:
        debug.write_memory(HOOK,installed_return)
        flush_instructions(HOOK,8)
        debug.write_memory(mode,struct.pack('>I',1))
        debug.write_memory(house_base,houses)
        debug.write_memory(actor,saved_actor)
    check('house data restored',house_base,houses)
    check('installed house branch restored',HOOK,installed_return)
    check('fish packet guard',ram+world['packet']['bytes']-16,packet[-16:])
    return dict(preview_options_native_checks=checks,checkpoint_restore_required=True,
        ordinary_new_town_or_save_tested=False,original_hardware_tested=False)
