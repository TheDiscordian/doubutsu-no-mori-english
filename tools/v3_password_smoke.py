"""Focused execution of the installed password loader, codec, and engine reads."""
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256
from flash_mail import SAVE_RAM, SAVE_BYTES
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK
from v3_asset_loader import BLOB
from v3_npc_draw_smoke import boot_proofs
from v3_password_runtime import RAM, SIZE, BOOT, CACHE, TABLES, POLICY


def exercise(debug, rom_path, record):
    path = Path(rom_path); image = path.read_bytes()
    report = json.loads((path.parent/'build.json').read_bytes())
    if sha256(image) != report['output_sha256']:
        raise ValueError('Password fixture requires its current cartridge')
    equipment = report['equipment_resources']; p = equipment['passwords']
    blob = by_vrom(image)[BLOB].extract(image)
    packet = blob[p['blob_offset']:p['blob_offset']+SIZE]
    ep = blob[equipment['blob_offset']:equipment['blob_offset']+equipment['bytes']]
    if sha256(packet) != p['sha256'] or sha256(ep) != equipment['sha256']:
        raise ValueError('Changed password loader or packet')
    boot = boot_proofs(image); assertions = 0; cases = 0

    def check(label, address, want):
        nonlocal assertions
        actual = debug.read_memory(address, len(want))
        record(dict(password_check=label, address=f'{address:08X}', bytes=len(want),
                    assertion='passed' if actual == want else 'failed'))
        if actual != want:
            raise ValueError('Password mismatch: '+label)
        assertions += 1

    def call(address, args=(), proof=None, want=None):
        result = debug.call(f'{address:08X}', list(args), return_address=MODULE_RAM+0x6480,
                            verified_code=proof or boot.get(address))
        record(result)
        if want is not None and result['return_value'] != want:
            raise ValueError('Password call result differs from expectation')
        return result['return_value']

    def put(address, value):
        debug.write_memory(address, struct.pack('>I', value))

    # Other equipment modules contain live scenery/room cache words. Verify the
    # complete new loader reservation, not unrelated mutable runtime caches.
    check('complete startup password loader', BOOT, ep[BOOT-equipment['ram']:CACHE+4-equipment['ram']])
    check('equipment footer',equipment['ram']+equipment['bytes']-16,ep[-16:])
    check('cold loader cache', CACHE, bytes(4))
    check('native RNG including seed and float conversion', 0x8002C970,
          image[0x1060+0x6D10:0x1060+0x6DA0])
    allocation = call(0x8009BFC0, [0x400])
    if allocation & 15 or not MODULE_RAM+RESERVATION <= allocation <= 0x803FFC00:
        raise ValueError('Password fixture allocation failed')
    descriptor, text, names, result_at = (allocation+n for n in (0x20, 0x60, 0xA0, 0xC0))
    edge = b'V3PW'*4
    guards = (allocation, descriptor+32, text+32, names+16, result_at+16, allocation+0x3F0,
              TEST_STACK-0x800, TEST_STACK+0x40)
    for at in guards:
        debug.write_memory(at, edge)
    selected = p['source']['destinations']['rows']
    ranges = [struct.unpack_from('>HHBB', packet, POLICY+32+i*6)
              for i in range(struct.unpack_from('>H', packet, POLICY+6)[0])]
    def allowed(item):
        return next((mask for lo, hi, mask, _ in ranges if lo <= item <= hi), 0)
    candidates = []
    for match in (lambda r:r['kind']=='furniture', lambda r:r['kind']=='clothing',
                  lambda r:r['kind']=='floor'):
        candidates.append(next(r for r in selected if match(r) and allowed(r['source_item']) & 4))
    saved = {at:debug.read_memory(at,n) for at,n in
             ((SAVE_RAM,SAVE_BYTES), (0x8046C000,1232), (0x8003C590,4), (0x800419F0,4),
              *((r['enable_ram'],r['enable_bytes']) for r in candidates))}
    # The loader ends with diagnostic strings, not necessarily a whole word.
    # The debugger's instruction proof must include the checked zero alignment.
    proof = BOOT, ep[BOOT-equipment['ram']:BOOT-equipment['ram']+((p['bootstrap']['code']['bytes']+3)&~3)]
    symbols = p['code']['symbols']; body = (RAM, packet[:p['code']['bytes']])
    blank = bytes([0xA5])*12
    try:
        debug.write_memory(names, b'Code    Forest  ')
        debug.write_memory(text, b' '*28); debug.write_memory(result_at, blank)
        call(BOOT, [text,names,names+8,result_at], proof, 9)
        check('complete real DMA and checksum-loaded packet', RAM, packet)
        check('successful load cache', CACHE, struct.pack('>I',p['crc32']))
        check('cancel leaves offer untouched', result_at, blank)
        for row in candidates:
            for enabled, rate, result in ((1,4,3),(0,4,0),(2,4,0),(1,3,7)):
                debug.write_memory(row['enable_ram'], enabled.to_bytes(row['enable_bytes'],'big'))
                payload = struct.pack('>H6B8s8s',row['source_item'],3,rate,255,255,0,0,
                                      b'Code    ',b'Forest  ')
                debug.write_memory(descriptor,payload)
                call(symbols['af_v3_password_encode'],
                     [RAM+TABLES,p['parts'][1]['bytes'],descriptor,text,28],body,1)
                put(0x8003C590,0x12345678);put(0x800419F0,0)
                debug.write_memory(result_at,blank)
                call(BOOT,[text,names,names+8,result_at],proof,result)
                next_seed=(0x12345678*0x19660D+0x3C6EF35F)&0xFFFFFFFF if enabled==1 else 0x12345678
                check('exact native RNG consumption',0x8003C590,struct.pack('>I',next_seed))
                expected=struct.pack('>3I',row['source_item'],row['item'],result) if enabled==1 else blank
                check('selected mapped offer or untouched rejection',result_at,expected)
                cases+=1
            debug.write_memory(row['enable_ram'],saved[row['enable_ram']])
        debug.write_memory(text,b'!'*28);debug.write_memory(result_at,blank)
        before=debug.read_memory(0x8003C590,4)
        call(BOOT,[text,names,names+8,result_at],proof,0)
        check('malformed input does not use RNG',0x8003C590,before)
        check('malformed input does not expose an offer',result_at,blank)
        check('cached execution preserves entire packet',RAM,packet)
        check('native saved game untouched',SAVE_RAM,saved[SAVE_RAM])
        check('extended saved state untouched',0x8046C000,saved[0x8046C000])
        for at in guards:
            check('caller or scratch guard',at,edge)
        check('no CPU fault',0x8003CE34,bytes(4))
    finally:
        for at,data in saved.items():
            debug.write_memory(at,data)
        call(0x8009C040,[allocation])
    return dict(native_password_engine=True,assertions=assertions,selection_cases=cases,
        real_dma_crc_cache=True,real_rng=True,keyboard_tested=False,gift_delivery_tested=False,
        ordinary_gameplay_tested=False,hardware_tested=False,flash_written=False,
        requires_checkpoint_restore=True)
