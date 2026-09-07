"""Read-only live submenu observations and isolated native letter-open probes."""

import struct

from runtime_layout import TEST_RETURN, TEST_STACK

OPEN = 0x800C4DD8
OPEN_BYTES = bytes.fromhex('AC850004AC860010AC8700148FAE0010AC8E00188FAF0014AC8F001C03E0000800000000')


def pointer(debug, address, size):
    value = struct.unpack('>I',debug.read_memory(address,4))[0]
    if value & 3 or not 0x80000000 <= value <= 0x80400000-size:
        raise ValueError('Invalid live mail/menu pointer')
    return value


def snapshot(debug):
    game = pointer(debug,0x8010EF90,0x1DAC)
    submenu = game+0x1CBC
    data = debug.read_memory(submenu,0x38)
    values = struct.unpack('>14I',data)
    result = {'game':f'{game:08X}','submenu':f'{submenu:08X}',
              'phase':values[0],'program':values[1],'previous_program':values[2],
              'move_index':values[3],'open_mode':values[4],
              'overlay':f'{values[11]:08X}','read_only':True}
    if values[1] == 12 and values[3] == 3:
        overlay = pointer(debug,submenu+0x2C,0x10730)
        board = pointer(debug,overlay+0x106E4,192)
        menu = debug.read_memory(overlay+0x103E8,0x48)
        state = debug.read_memory(board,192)
        base = board-0x1D70
        if not 0x80000000 <= base <= 0x80400000-0x1E30:
            raise ValueError('Invalid loaded board code range')
        result.update(board=f'{board:08X}',board_state=struct.unpack_from('>I',menu,4)[0],
                      board_mode=struct.unpack_from('>I',menu,0x38)[0],
                      source=f'{struct.unpack_from(">I",state,0xAC)[0]:08X}',
                      header_length=state[5],body_length=state[6],footer_length=state[7],
                      mail=state[8:172].hex(),board_base=f'{base:08X}',
                      body_call=debug.read_memory(base+0x1210,4).hex(),
                      footer_call=debug.read_memory(base+0x1244,4).hex())
    return result


def open_test_mail(debug,address,*,snapshot_probe=False,open_mode=1):
    address = int(address,16) if isinstance(address,str) else address
    if type(address) is not int or address & 3 or not TEST_RETURN+16 <= address <= TEST_STACK-0x800-164:
        raise ValueError('Test mail must be inside isolated fixture RAM')
    if type(open_mode) is not int or (open_mode != 1 and not (snapshot_probe and open_mode == 2)):
        raise ValueError('Only an explicit snapshot probe may request edit-open mode two')
    state = snapshot(debug)
    if state['program'] != 0 or state['move_index'] != 0:
        raise ValueError('Native mail-open probe requires a closed submenu')
    mail = debug.read_memory(address,164)
    if mail[0x26] == 255 or (mail[0x27] > 10 and not (snapshot_probe and mail[0x27] == 128)) or mail[0x29] >= 64:
        raise ValueError('Mail-open probe requires an ordinary valid native letter')
    if debug.read_memory(OPEN,len(OPEN_BYTES)) != OPEN_BYTES:
        raise ValueError('Native submenu-open instruction guard failed')
    private = pointer(debug,0x80136FD8,0x40A)
    preference = private+0x3EE
    before = debug.read_memory(preference,28)
    called = debug.call(f'{OPEN:08X}',[int(state['submenu'],16),12,open_mode,0,address,0])
    return {'test_only_mail_open':True,'source':f'{address:08X}','mail':mail.hex(),
            'preference':f'{preference:08X}','preference_bytes':before.hex(),
            'before':state,'call':called,'requested_open_mode':open_mode,'requires_checkpoint_restore':True}


def verify_unchanged(debug,opened):
    if not opened:
        raise ValueError('No isolated mail-open probe is active')
    for address_key,data_key in (('source','mail'),('preference','preference_bytes')):
        expected = bytes.fromhex(opened[data_key])
        if debug.read_memory(int(opened[address_key],16),len(expected)) != expected:
            raise ValueError('Mail read changed its source or saved header/footer preferences')
    return {'test_mail_and_preferences_unchanged':True}
