"""Silent current-cartridge checks of native dresser input and cancellation."""
import json
from pathlib import Path
import struct
from types import SimpleNamespace

from aflib import by_vrom, sha256
from dresser_menu_fix import ROOM, ROOM_RAM, HANDLER
from english_runtime import ChoiceLayout
from flash_mail import SAVE_RAM, SAVE_BYTES
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_VROM, GUARD_ADDRESS, GUARD_WORD


def exercise(debug, rom_path, record):
    path = Path(rom_path); image = path.read_bytes()
    report = json.loads((path.parent/'build.json').read_bytes())
    if report['build'] != 'V2-14' or sha256(image) != report['output_sha256']:
        raise ValueError('Dresser test requires the corrected current V2 cartridge')
    files = by_vrom(image); read, write = debug.read_memory, debug.write_memory
    count = 0
    def check(label, actual, expected):
        nonlocal count
        count += 1
        record(dict(dresser_check=label, passed=actual == expected))
        if actual != expected: raise ValueError('Dresser mismatch: '+label)
    def call(at, args=(), proof=None):
        value = debug.call(f'{at:08X}', list(args), verified_code=proof)
        record(value); return value['return_value']
    def words(*values): return struct.pack('>'+str(len(values))+'I', *values)
    layout = ChoiceLayout(*struct.unpack_from('>4I', files[MODULE_VROM].extract(image), 40))
    choice, staging, controller, actor = 0x801425C0, 0x8019B800, 0x8019BC00, 0x8019B000
    saved = read(SAVE_RAM, SAVE_BYTES)
    write(0x80104F94, words(0)); write(0x8010EF90, words(controller))
    write(controller, bytes(0x100)); write(choice, bytes(0xBC))
    labels = (b'Remove', b'Swap', b'Never mind...')
    for index, (number, label) in enumerate(zip((0x7E,0xE9,0xD), labels)):
        call(0x80065D90, [choice, staging+index*32, number, 0])
        check('cartridge choice label', read(staging+index*32,20), label.ljust(20,b' '))
    call(0x80065278, [choice, staging,20, staging+32,20, staging+64,20, 0,0])
    call(0x80065EE8, [choice])
    for button in (0x4000, 0x8000):
        for cursor in range(3):
            write(choice+0x84, words(cursor)); write(controller+0x20, struct.pack('>H',button))
            check('native input accepted', call(0x80066194,[choice,0]), 1)
            selected = 2 if button == 0x4000 else cursor
            check('native selected action', read(choice+0x80,8),words(selected,selected))
            check('native selected label', read(layout.selected,len(labels[selected])),labels[selected])
    # Execute the actual relocated dresser handler's cancel arm after real B input.
    data = files[ROOM].extract(image); rel = files[ROOM+len(data)].extract(image)
    sections = struct.unpack_from('>5I',rel); size = len(data)+sections[3]+32
    allocation = call(0x8009BFC0, [size])
    if allocation & 15 or not 0x8019C8E0 <= allocation <= 0x80400000-size:
        raise ValueError('Dresser fixture allocation failed')
    owner = allocation+16
    resident = len(data)+sections[3]
    expected = relocate_verified_data(SimpleNamespace(ram=ROOM_RAM,resident_bytes=resident,sections=sections),data,rel,owner)
    boot_at = 0x1060+0x800262D0-0x80025C60
    call(0x800262D0,[ROOM,ROOM+len(data),ROOM_RAM,ROOM_RAM+resident,owner,owner+len(data),len(rel)],
         (0x800262D0,image[boot_at:boot_at+0xF0]))
    check('complete room relocation and BSS',read(owner,resident),expected)
    edge = b'DRSG'*4
    write(allocation,edge); write(allocation+size-16,edge)
    write(actor,bytes(0x500)); write(choice+0x84,words(0)); write(controller+0x20,b'\x40\x00')
    check('B selects cancel before room handler',call(0x80066194,[choice,0]),1)
    call(owner+HANDLER-ROOM_RAM,[actor,0],(owner,expected[:sections[0]]))
    check('dresser requests close, not swap submenu',read(actor+0x3E8,2),b'\0\x0A')
    check('selection consumed',read(choice+0x80,4),b'\xFF'*4)
    check('complete saved inventory and town unchanged',read(SAVE_RAM,SAVE_BYTES),saved)
    check('allocation start guard',read(allocation,16),edge)
    check('allocation end guard',read(allocation+size-16,16),edge)
    check('resident scratch guard',read(GUARD_ADDRESS,16),words(*([GUARD_WORD]*4)))
    return dict(dresser_menu='passed', assertions=count, ordinary_playthrough=False)
