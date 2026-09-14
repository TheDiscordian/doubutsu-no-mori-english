"""Current native stock, ownership, and complete English score-letter paths."""
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256, u32
from flash_mail import SAVE_RAM, SAVE_BYTES
from mail_catalog import templates
from mail_record import Field, Record, pack
from mail_runtime_test_scenario import output_bytes
from runtime_layout import MODULE_RAM, MODULE_VROM, RESERVATION, TEST_STACK
from v3_asset_loader import BLOB, BLOB_RAM
from v3_npc_draw_smoke import boot_proofs


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    rom = path.read_bytes(); report = json.loads((path.parent/'build.json').read_text())
    if sha256(rom) != report['output_sha256'] or not report['speed_bag']['saved_profile_included']:
        raise ValueError('Speed-bag gameplay check requires the exact integrated cartridge')
    files, proofs = by_vrom(rom), boot_proofs(rom)
    prefix = files[BLOB].extract(rom)[:0xC000]
    module = files[MODULE_VROM].extract(rom)
    creator = files[0x03200000].extract(rom)
    catalog = files[0x030A0000].extract(rom)
    calls = 0

    def check(label, address, expected):
        actual = debug.read_memory(address, len(expected))
        record({'speed_bag_gameplay_check': label, 'address': f'{address:08X}', 'bytes': len(expected),
                'expected_sha256': sha256(expected), 'observed_sha256': sha256(actual),
                'assertion': 'passed' if actual == expected else 'failed'})
        if actual != expected: raise ValueError('Native speed-bag integration mismatch: '+label)

    def call(address, args=(), expected=None):
        nonlocal calls
        result = debug.call(f'{address:08X}', list(args), return_address=MODULE_RAM+0x6480,
                            verified_code=proofs.get(address))
        record(result); calls += 1
        if expected is not None and result['return_value'] != expected & 0xFFFFFFFF:
            raise ValueError(f'Speed-bag native call {address:08X} returned {result["return_value"]}, expected {expected}')
        return result['return_value']

    def put(address, value): debug.write_memory(address, struct.pack('>I', value))

    check('complete current resident prefix', BLOB_RAM, prefix)
    check('complete changed creator loader configuration', MODULE_RAM+0x48, module[0x48:0x68])
    loader = 0x80197BB4
    # Resident-module entries use the debugger's normal checked module route;
    # external-code proofs intentionally cannot overlap that reservation.
    check('installed score-letter loader entry',loader,module[loader-MODULE_RAM:loader-MODULE_RAM+32])
    allocation = call(0x8009BFC0, [0x2000])
    if allocation & 15 or not MODULE_RAM+RESERVATION <= allocation <= 0x803FE000:
        raise ValueError('Speed-bag integration allocation failed')
    result_at, mail, player_id, request, name, text, work = (allocation+n for n in
        (0x20, 0x100, 0x200, 0x220, 0x240, 0x400, 0x900))
    edge = b'V3SG'*4
    guards = (allocation, mail+164, player_id-16, request-16, name+16,
              text-16, text+1040, work-16, work+3552, allocation+0x1FF0,
              TEST_STACK-0x1800, TEST_STACK+0x40)
    for address in guards: debug.write_memory(address, edge)
    saved = debug.read_memory(SAVE_RAM, SAVE_BYTES)
    runtime = debug.read_memory(0x8046C000, 864)
    globals_before = {at: debug.read_memory(at, size) for at, size in
        ((0x80199F64,4), (0x80199F5C,4), (0x8003C590,4), (0x80136FD8,4),
         (0x801458B8,4), (0x80140680,200), (0x80467134,4))}
    player = 0x80126EC0
    try:
        put(0x80467134, 1)
        # Native group A maps to this town's common category for this fixture.
        debug.write_memory(0x80135B1C, bytes([0x18]))
        for rarity in range(3): call(0x800C0490, [0x3350,0,rarity,0], int(rarity==0))
        next_random = 0xFF800000
        seed = ((next_random-0x3C6EF35F)*pow(0x19660D,-1,1<<32)) & 0xFFFFFFFF
        debug.write_memory(0x80135C00, bytes(2)); put(0x8003C590, seed)
        call(0x800BFCF0, [0,result_at,1,0,0,0,0])
        check('native group-A stock selector returns the speed bag', result_at, bytes.fromhex('3350'))
        check('stock selection consumes its single native RNG draw', 0x8003C590, struct.pack('>I',next_random))
        call(0x800C05E0, [0x3350], 0)
        put(0x80467134,0); call(0x800C05E0,[0x3350],-1); put(0x80467134,1)
        put(0x80136FD8, player)
        debug.write_memory(player+0x14, bytes(0x24))
        debug.write_memory(0x8046C000+16+192, bytes(640))
        call(0x800B8B8C, [player,0x3350,0], 1)
        check('native pocket acquisition retains the full imported ID', player+0x14, bytes.fromhex('3350'))
        ownership = bytearray(640); ownership[26] = 16
        check('speed-bag ownership uses its independent saved furniture bit', 0x8046C000+16+192, ownership)
        pid = b'PLAYER'+b'TOWN  '+bytes.fromhex('12343001')
        debug.write_memory(player_id,pid)
        original_key = creator[0x9860:0x986A]
        cases = ((0x3A,b'boxing    ',b'boxing          '),
                 (0x3B,b'boxing    ',b'boxing          '),
                 (0x3A,original_key,b'exotic          '),
                 (0x37,b'boxing    ',None))
        for number,key,english in cases:
            debug.write_memory(name,key+b'!!')
            descriptor = struct.pack('>IHHHBBHHBB',123456,0x3350,0,2000,9,17,number,0,250,51)
            debug.write_memory(request,descriptor); debug.write_memory(mail,b'!'*164)
            put(0x80199F64,0)
            call(loader,[mail,player_id,name,request,0,1],mail)
            fields = {0:Field(b'   123,456'),3:Field(b'2000'),4:Field(b'September'),5:Field(b'17th')}
            if english is not None: fields[2] = Field(english)
            if number==0x37: fields[1] = Field(b'speed bag       ')
            snapshot = Record(4,0,(number,),tuple(sorted(fields.items())),False)
            expected = bytearray(164); expected[:16]=pid; expected[18:30]=b' '*12
            expected[30:35]=b'\xFF'*5; expected[39:42]=bytes((128,6,51)); expected[42:]=pack(snapshot)
            check('complete native English score letter with exact captured fields',mail,expected)
            call(0x80196C28,[text,mail+42,122,work],1)
            check('complete restored English score-letter text',text,output_bytes(snapshot,templates(catalog,snapshot)))
            check('borrowed series key remains unchanged',name,key+b'!!')
            check('score descriptor remains unchanged',request,descriptor)
            check('creator detaches after complete generation',0x80199F5C,bytes(4))
        debug.write_memory(name,b'?'*12); debug.write_memory(mail,b'!'*164)
        debug.write_memory(request,struct.pack('>IHHHBBHHBB',123456,0,0,2000,9,17,0x3A,0,250,51))
        put(0x80199F64,0)
        call(loader,[mail,player_id,name,request,0,1],0)
        check('unknown series cannot partially overwrite a letter',mail,b'!'*164)
        check('failed creator leaves its session detached',0x80199F5C,bytes(4))
        debug.write_memory(0x80467134,globals_before[0x80467134])
        check('complete resident prefix retained',BLOB_RAM,prefix)
        for address in guards: check('fixture guard',address,edge)
        check('translation guard',0x8019C8D0,bytes.fromhex('AF32C0DE')*4)
        check('save-state guard',0x8046C350,bytes.fromhex('AF53C0DE')*4)
        check('no faulted thread',0x8003CE34,bytes(4))
    finally:
        debug.write_memory(SAVE_RAM,saved); debug.write_memory(0x8046C000,runtime)
        for address,value in globals_before.items(): debug.write_memory(address,value)
    call(0x8009C040,[allocation])
    return {'native_speed_bag_calls':calls,'native_stock_selection':True,
            'native_pocket_acquisition':True,'native_english_score_letters':4,
            'unknown_series_rejected':True,'saved_data_written':False,
            'ordinary_shop_payment_tested':False,'requires_checkpoint_restore':True}
