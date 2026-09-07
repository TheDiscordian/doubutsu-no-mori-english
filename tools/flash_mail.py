"""Native FlashRAM layout and mail locations; all offsets are source guarded."""

import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256

SAVE_RAM, SAVE_BYTES, BANK_BYTES, FLASH_BYTES = 0x80126EA0,0xF980,0x10000,0x20000
SAVE_STATE, SAVE_DISPATCH = 0x8013A398,0x80090044
SAVE_STATES = (0x8008FAE0,0x8008FB64,0x8008FBEC,0x8008FCE8,0x8008FDD4,0x8008FE74,0x8008FF60)
CODE_GUARDS = (
    (0x8008ECA0,0x80090120,'6d95d3a3d34236f1447ead3e6a7512ce23917de7114974a602b59e8d8c6c956c'),
    (0x800CDB10,0x800CE120,'e4524a68fb1a56d8ff2f8441079316567c1e901d125c52cceb6b507165263759'),
)


def evidence(rom):
    code = by_vrom(rom)[CODE_VROM].extract(rom)
    guards = {}
    for start,end,digest in CODE_GUARDS:
        data = code[start-CODE_RAM:end-CODE_RAM]
        if sha256(data) != digest: raise ValueError('Unexpected native FlashRAM code')
        guards[f'{start:08X}'] = data.hex()
    table = code[0x80106ACC-CODE_RAM:0x80106AE8-CODE_RAM]
    if table != struct.pack('>7I',*SAVE_STATES): raise ValueError('Unexpected native save-state table')
    guards['80106ACC'] = table.hex()
    return {'save_ram':f'{SAVE_RAM:08X}','save_bytes':SAVE_BYTES,'bank_bytes':BANK_BYTES,
            'flash_bytes':FLASH_BYTES,'state_ram':f'{SAVE_STATE:08X}',
            'dispatch':f'{SAVE_DISPATCH:08X}','guards':guards}


def locations():
    """All slots of the verified player/home/post/NPC mail arrays in Save.

    This enumerates storage, not reachable delivered letters or generation IDs.
    Native Anmmem starts at Animal+10 and its letter at +2A. Some upstream
    structure offset comments still describe a different platform.
    """
    result = []
    def add(label,address,compact=False):
        size = 132 if compact else 164
        offset = address-SAVE_RAM
        if offset < 0x20 or offset+size > SAVE_BYTES:
            raise ValueError('Mail slot is outside the native save payload')
        result.append({'label':label,'offset':offset,'bytes':size,'compact':compact})
    for player in range(4):
        for slot in range(10):
            add(f'player:{player}:{slot}',SAVE_RAM+0x20+player*0xBD0+0x40A+slot*164)
    for home in range(4):
        for slot in range(10): add(f'home:{home}:{slot}',0x8012A8A0+home*0xB48+slot*164)
    for slot in range(5): add(f'post_queue:{slot}',0x80135E0C+slot*164)
    for slot in range(2): add(f'leaflet:{slot}',0x80136140+slot*164)
    for animal in range(15):
        for memory in range(7):
            add(f'npc:{animal}:{memory}',0x80130DB8+animal*0x528+0x10+memory*0xB0+0x2A,True)
    ordered = sorted(result,key=lambda row:row['offset'])
    if any(a['offset']+a['bytes'] > b['offset'] for a,b in zip(ordered,ordered[1:])):
        raise ValueError('Native saved mail slots overlap')
    return result


def checksum(data):
    if len(data)&1: raise ValueError('Native save checksum requires an even byte count')
    return sum(value for (value,) in struct.iter_unpack('>H',data))&0xFFFF


def validate_flash(data):
    if len(data) != FLASH_BYTES: raise ValueError('Native FlashRAM image must be 128 KiB')
    banks = [data[start:start+SAVE_BYTES] for start in (0,BANK_BYTES)]
    for bank in banks:
        if bank[4:8] != b'NAFJ': raise ValueError('Native save signature mismatch')
        town = int.from_bytes(bank[8:10],'big')
        if town&0xFF00 != 0x3000 or bank[8:10] != bank[0x2F68:0x2F6A]:
            raise ValueError('Native save town identity mismatch')
        if checksum(bank): raise ValueError('Native save checksum mismatch')
    if banks[0] != banks[1]: raise ValueError('Native save payload copies differ')
    return {'flash_sha256':sha256(data),'payload_sha256':sha256(banks[0]),
            'copies':2,'payload_bytes':SAVE_BYTES,'town_id':f'{town:04X}'}
