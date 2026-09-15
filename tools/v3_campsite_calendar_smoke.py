"""Current native calendar/index/save-area calls in a restored isolated machine."""
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256
from runtime_layout import MODULE_RAM
from v3_asset_loader import BLOB
from v3_npc_draw_smoke import boot_proofs
import v3_campsite_calendar as runtime


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    rom, report = path.read_bytes(), json.loads((path.parent / 'build.json').read_bytes())
    if sha256(rom) != report['output_sha256'] or report['runtime_abi'] != 73:
        raise ValueError('Calendar probe requires the current ABI 73 cartridge')
    blob, boot = by_vrom(rom)[BLOB].extract(rom), boot_proofs(rom)
    symbols = report['campsite_calendar']['code']['symbols']
    def check(label, address, expected):
        actual = debug.read_memory(address, len(expected))
        record(dict(calendar_check=label,address=f'{address:08X}',bytes=len(expected),
                    assertion='passed' if actual == expected else 'failed',
                    expected_sha256=sha256(expected),observed_sha256=sha256(actual),
                    observed_hex=actual.hex() if len(actual) <= 32 else None))
        if actual != expected: raise ValueError('Native calendar mismatch: ' + label)
    def call(address, args, expected=None, proof=None):
        result = debug.call(f'{address:08X}',args,return_address=MODULE_RAM+0x6480,
                            verified_code=proof or boot.get(address))
        if expected is not None:
            result['assertion'] = 'passed' if result['return_value'] == expected else 'failed'
        record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError('Unexpected native calendar return')
        return result['return_value']
    def word(address): return struct.unpack('>I',debug.read_memory(address,4))[0]
    def put(address,value): debug.write_memory(address,struct.pack('>I',value))
    for address, size in ((runtime.EVENT_CODE,report['campsite_calendar']['event_code']['bytes']),
                          (runtime.CALENDAR_CODE,report['campsite_calendar']['code']['bytes']), (runtime.PACKET,256)):
        at = runtime.PACKAGE + address-runtime.PACKAGE_RAM
        check('installed calendar code/packet',address,blob[at:at+size])
    save_runtime = debug.read_memory(0x8046C000,864)
    neighbouring_bss = debug.read_memory(0x8013A0DE,2)
    saved_clock = debug.read_memory(0x80136FBE,6)
    saved_scene, saved_last = word(0x80126EB4), word(0x80136EA4)
    game = word(0x8010EF90)
    if game & 3 or not 0x80000000 <= game <= 0x803FFF5C: raise ValueError('Invalid existing game pointer')
    saved_frame = word(game+0xA0)
    allocation = call(0x8009BFC0,[0x100])
    if allocation & 15 or not MODULE_RAM+0x8000 <= allocation <= 0x803FFF00:
        raise ValueError('Small calendar fixture allocation failed')
    bridge, schedule = allocation+16, allocation+0x80
    edge = b'V3CE'*4
    debug.write_memory(allocation,edge); debug.write_memory(allocation+0xF0,edge)
    def resident(name):
        stub = struct.pack('>II',0x08000000 | ((symbols[name]>>2)&0x3FFFFFF),0)
        debug.write_memory(bridge,stub)
        call(0x8002FE00,[bridge,8]); call(0x80034CE0,[bridge,8])
        return call(bridge,[],proof=(bridge,stub))
    def clock(year,month,day,weekday,hour,scene=0,last=1,frame=1):
        debug.write_memory(0x80136FBE,struct.pack('>BBBBH',hour,day,weekday,month,year))
        put(0x80126EB4,scene); put(0x80136EA4,last); put(game+0xA0,frame)
        call(0x8007DBB0,[])  # Actual weekday table construction for this isolated RTC.
    def reset():
        resident('af_v3_campsite_today_init')
        check('expanded index initialized',runtime.INDEX,b'\xFF'*128)
        check('neighbouring original BSS retained',0x8013A0DE,neighbouring_bss)
    def row(hours,begin,end):
        check('native complete camper today record',0x80139F98,struct.pack('>IIHHHH',70,hours,begin,end,0x80,0))
        check('camper additive index slot',runtime.INDEX+70,b'\x00')

    clock(2026,6,6,6,9); reset()
    expected = call(0x8007F2D8,[])
    observed = resident('af_v3_campsite_before_cleanup')
    if observed != expected: raise ValueError('Calendar hook changes native first-entry result')
    row(0xFFFE00,0x0606,0x0607)
    call(0x8007FCB8,[70],1)
    debug.write_memory(0x80136FBE,b'\x08'); call(0x8007FCB8,[70],0)
    debug.write_memory(0x80136FBE,b'\x09')
    call(0x8007E184,[70],9); call(0x8007E1D8,[70],23)
    call(0x8007FD40,[70],1)
    debug.write_memory(schedule,bytes.fromhex('060600000606001700000010'))
    call(0x8007E264,[0x0606,schedule])
    check('original event uses its own new-directory slot',runtime.INDEX+16,b'\x01')
    call(0x8007FCB8,[16],1)
    call(0x8007FE0C,[70],1); call(0x8007FF08,[70,1],1)
    call(0x8007FE74,[70,1]); call(0x8007FF08,[70,1],0)
    call(0x8007FDA8,[70,0x10]); call(0x8007FF08,[70,0x10],1)
    call(0x8007FE74,[70,0x10])
    # Disposable emulated RAM only: this is not a FlashRAM write or reload test.
    put(0x80135CF4,0)
    saved = call(0x80080080,[70,0])
    if saved not in [0x80135D00+i*48 for i in range(5)]: raise ValueError('Invalid native camper save area')
    check('native saved-event identity and date header',saved-8,struct.pack('>BBHHH',70,0,2026,0x0606,0x0607))
    check('native cleared forty-byte event payload',saved,bytes(40))
    debug.write_memory(saved,bytes.fromhex('e0da'))
    call(0x8008033C,[70,0],saved)
    check('camper identity readback in native event area',saved,bytes.fromhex('e0da')+bytes(38))
    call(0x800804AC,[70,0],40); check('native saved-event allocation released',0x80135CF4,bytes(4))

    clock(2025,6,1,0,14); reset(); resident('af_v3_campsite_before_cleanup')
    row(0x7FFF,0x051F,0x0601); call(0x8007FCB8,[70],1)
    debug.write_memory(0x80136FBE,b'\x0F'); call(0x8007FCB8,[70],0)
    clock(2025,6,29,0,14); reset(); resident('af_v3_campsite_before_cleanup')
    check('donor month-end clamp and preceding-Sunday adjustment',runtime.INDEX+70,b'\xFF')
    clock(2026,10,2,5,23,scene=35); reset(); resident('af_v3_campsite_before_cleanup')
    row(0xFFFFFF,0x0A02,0x0A02)
    clock(2026,10,2,5,23,last=35,frame=0); reset(); resident('af_v3_campsite_before_cleanup')
    row(0x10000000,0x0A02,0x0A02)
    # Event-start is bit 28, not an ordinary active hour. The assertion below
    # uses the complete native field rather than claiming current-hour activity.
    return_state = dict(native_calendar_and_index=True,native_event_save_area=True,
        flash_write_or_reload=False,event_manager_or_camper_actor=False,requires_checkpoint_restore=True)
    flags = []
    for item in (0x335C,0x3360,0x3364,0x336C,0x3370,0x339C,0x33A4,0x33A8,0x33AC,0x33B0):
        at = 0x80484000+(item-0x3000)//4*80+4
        flags.append((at,debug.read_memory(at,4))); put(at,0)
    reset(); resident('af_v3_campsite_before_cleanup')
    check('no camping selections means no summer event',runtime.INDEX+70,b'\xFF')
    for at,value in flags: debug.write_memory(at,value)
    for at in (allocation,allocation+0xF0): check('calendar fixture guard',at,edge)
    check('save runtime unchanged',0x8046C000,save_runtime)
    check('final package guard',0x804A2FF0,bytes.fromhex('AFACC0DE')*4)
    check('calendar packet guard',runtime.PACKET+0xF0,bytes.fromhex('AFC7CA1E')*4)
    check('translation guard',0x8019C8D0,bytes.fromhex('AF32C0DE')*4)
    check('no faulted thread',0x8003CE34,bytes(4))
    debug.write_memory(0x80136FBE,saved_clock)
    put(0x80126EB4,saved_scene); put(0x80136EA4,saved_last); put(game+0xA0,saved_frame)
    call(0x8009C040,[allocation])
    return return_state
