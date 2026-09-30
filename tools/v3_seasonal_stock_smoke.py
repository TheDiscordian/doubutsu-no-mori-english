"""Shared native seasonal acquisition probe on a disposable paused checkpoint.

Exercises real installed profile selection, RTC reads, RNG, original seasonal
routine, and pair construction; not an ordinary purchase or hardware test.
"""
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from runtime_layout import TEST_RETURN, TEST_STACK
from v3_asset_loader import BLOB
from v3_seasonal_stock import END, FORMAT, GUARD, RAM


def exercise(debug, rom_path, record):
    path = Path(rom_path); image = path.read_bytes()
    report = json.loads((path.parent/'build.json').read_bytes())
    owner = report['equipment_resources']['seasonal_stock']; packet = owner['packet']
    if sha256(image) != report['output_sha256'] or owner['format'] != FORMAT or not owner['installed']:
        raise ValueError('Seasonal probe requires the exact installed cartridge')
    source = image[packet['physical']:packet['physical']+packet['bytes']]
    code = bytearray(source[RAM-packet['ram']:RAM-packet['ram']+owner['code']['bytes']])
    files = by_vrom(image); core = files[CODE_VROM].extract(image); blob = files[BLOB].extract(image)
    rtc, seed_at, mode_at = 0x80136FBC, 0x8003C590, owner['choice']['ram']
    rows = owner['source']['imports']
    enabled = [int(r['profile_ram'],16)-4 for r in rows]
    scratch = TEST_RETURN+0x200
    if scratch+64 >= TEST_STACK-0x800: raise ValueError('Seasonal fixture exceeds test scratch')

    def check(label, at, expected):
        actual = debug.read_memory(at,len(expected))
        record(dict(seasonal_stock_check=label,address=f'{at:08X}',bytes=len(expected),
                    expected_sha256=sha256(expected),observed_sha256=sha256(actual),
                    assertion='passed' if actual == expected else 'failed'))
        if actual != expected: raise ValueError('Native seasonal mismatch: '+label)

    check('complete installed seasonal code',RAM,bytes(code))
    check('seasonal reservation guard',END-16,struct.pack('>4I',*([GUARD]*4)))
    hook = owner['hook']; at = hook['address']
    check('actual Nook seasonal call and delay slot',at,core[at-CODE_RAM:at-CODE_RAM+8])
    furniture = report['furniture']['code']; at = furniture['symbols']['af_v3_furniture_import_profile']
    check('complete retained furniture selection code',at,blob[at-0x80460000:at-0x80460000+furniture['bytes']])
    for native in owner['native_consumers'][:2]:
        at = native['start']; check('complete native seasonal consumer',at,core[at-CODE_RAM:native['end']-CODE_RAM])
    saved = {at:debug.read_memory(at,n) for at,n in [(rtc,8),(seed_at,4),(mode_at,4),*((at,4) for at in enabled)]}
    edge = b'STOK'*4
    debug.write_memory(scratch,edge); debug.write_memory(scratch+32,edge)
    cases = 0

    def advance(seed): return (seed*0x19660D+0x3C6EF35F)&0xFFFFFFFF

    def run(mode,mask,count,month,day,seed):
        nonlocal cases
        date = bytearray(saved[rtc]); date[5] = month; date[3] = day
        debug.write_memory(rtc,bytes(date)); debug.write_memory(seed_at,struct.pack('>I',seed))
        for i,at in enumerate(enabled): debug.write_memory(at,struct.pack('>I',int(bool(mask&(1<<i)))))
        debug.write_memory(mode_at,struct.pack('>I',mode))
        struct.pack_into('>I',code,mode_at-RAM,mode)
        original = [0xF001,0xF002,0xF003,0xF004]; expected = original.copy()
        debug.write_memory(scratch+16,struct.pack('>4H',*original))
        seasonal = month == 12 and 26 <= day <= 31
        imported = seasonal and mask and mode < 2
        if imported and mode == 0:
            seed = advance(seed); imported = seed < 0x80000000
        pair = None
        if count > 0:
            if seasonal:
                pair = [int(r['item_id'],16) if imported and mask&(1<<i) else owner['source']['native_fallback'][i]
                        for i,r in enumerate(rows)]
            elif month == 12 and day <= 24: pair = [0x1E0C,0x1DD8]
            elif (month == 2 and day >= 20) or (month == 3 and day <= 3): expected[0] = 0x10E4
            elif (month == 4 and day >= 20) or (month == 5 and day <= 5): expected[0] = 0x1DCC
        if pair:
            if count > 1: expected[:2] = pair
            else:
                seed = advance(seed); expected[0] = pair[0 if seed < 0x80000000 else 1]
        record(dict(seasonal_stock_case=dict(mode=mode,selection=mask,count=count,month=month,day=day)))
        result = debug.call(f'{RAM:08X}',[scratch+16,count],return_address=TEST_RETURN,
                            verified_code=(RAM,bytes(code)))
        record(dict(seasonal_stock_call=True,**result))
        check('selected/native complete stock result',scratch+16,struct.pack('>4H',*expected))
        check('exact native RNG consumption',seed_at,struct.pack('>I',seed))
        for at in (scratch,scratch+32): check('stock fixture guard',at,edge)
        check('native fault pointer',0x8003CE34,bytes(4))
        cases += 1

    try:
        for mode in (0,1):
            for mask in range(4):
                for count in (1,2):
                    for seed in (0x10000000,0xE0000000): run(mode,mask,count,12,26,seed)
        for month,day in ((12,24),(12,25),(12,31),(2,20),(5,5),(1,26)):
            run(1,3,2,month,day,0x10000000)
    finally:
        for at,data in saved.items(): debug.write_memory(at,data)
    for at,data in saved.items(): check('original native state restored',at,data)
    check('seasonal reservation guard',END-16,struct.pack('>4I',*([GUARD]*4)))
    return dict(seasonal_stock_native='passed',cases=cases,
                ordinary_purchase_verified=False,save_restart_verified=False,hardware_verified=False,
                requires_checkpoint_restore=True)
