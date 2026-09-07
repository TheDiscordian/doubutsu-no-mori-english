"""Pinned native Controller Pak transport and isolated raw-reader fixture."""

import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256

PAK_BYTES, PASSPORT_BYTES, LETTER_FILE_BYTES = 0x8000,0x1200,0x6700
PRIVATE_BYTES, ANIMAL_BYTES = 0xBD0,0x528
PAK_INFO, PASSPORT = 0x80137960,0x80137C40
PROBE_CODE = bytes.fromhex(
    '27bdffd0afbf002cafb00028afb10024afb20020afb3001c0080802500008825'
    '0c035a8400009825004090250240202500002825022030250c00e46c02003825'
    '144000060040982526310001261000202e2804001500fff5000000000c035a91'
    '02402025026010258fb3001c8fb200208fb100248fb000288fbf002c03e0000827bd0030'
    '000000000000000000000000')

CODE_GUARDS = (
    (CODE_VROM,CODE_RAM,0x80078E90,0x8007A0C0,'0a24e76d1c4ce5ded79bae3e7d18e27ee21313d62fdf1abbd25b1d99f3cc21ce'),
    (CODE_VROM,CODE_RAM,0x800CD640,0x800CDB10,'05799c3f893336e2588260671a16aeb73917cb2e1753e51f06560521b766a7df'),
    (CODE_VROM,CODE_RAM,0x800D6A10,0x800D6A78,'346cb40453a16a14714e4d394f6905610ee09cdb94d8ddcce9bbef2b2f0cb145'),
    (0x1060,0x80025C60,0x800391B0,0x800393D4,'49f4d8fd189dd16f0071b7c8580ab532786fd2dbc3739e31a92a6bd3bb0eee91'),
)


def evidence(rom):
    files = by_vrom(rom)
    guards = {}
    for vrom,base,start,end,digest in CODE_GUARDS:
        data = files[vrom].extract(rom)[start-base:end-base]
        if sha256(data) != digest: raise ValueError('Unexpected native Controller Pak code')
        guards[f'{start:08X}'] = data.hex()
    code = files[CODE_VROM].extract(rom)
    sizes = code[0x80116808-CODE_RAM:0x80116810-CODE_RAM]
    if sizes != struct.pack('>2I',PASSPORT_BYTES,LETTER_FILE_BYTES):
        raise ValueError('Unexpected native Controller Pak file sizes')
    guards['80116808'] = sizes.hex()
    storage = files[0x79E430].extract(rom)
    if sha256(storage) != 'afc2fe5337796bc9e2d50daacfb2ab23a56e241077273c7ec7cec7aa797f9235':
        raise ValueError('Unexpected native Controller Pak letter-storage layout')
    return {'guards':guards,'passport_bytes':PASSPORT_BYTES,'letter_file_bytes':LETTER_FILE_BYTES,
            'pak_bytes':PAK_BYTES,'passport_slots':passport_slots(),'letter_slots':letter_slots()}


def passport_slots():
    rows = [{'label':f'player:{i}','offset':8+0x40A+i*164,'bytes':164,'compact':False}
            for i in range(10)]
    rows += [{'label':f'npc:{i}','offset':0xBD8+0x10+i*0xB0+0x2A,'bytes':132,'compact':True}
             for i in range(7)]
    if any(row['offset']+row['bytes'] > 0x1100 for row in rows):
        raise ValueError('Passport letter exceeds the copied private/animal data')
    return rows


def letter_slots():
    # Native initialization clears 160 records at +52, after the checksum and
    # eight ten-byte page labels. It is not a 128-byte header.
    return [{'label':f'page:{page}:slot:{slot}','offset':0x52+(page*20+slot)*164,
             'bytes':164,'compact':False} for page in range(8) for slot in range(20)]


def fixture_records(data,slots,cases):
    """Install synthetic envelopes without discarding surrounding identities."""
    modified,records = bytearray(data),[]
    for index,slot in enumerate(slots):
        offset,size = slot['offset'],slot['bytes']
        wire = bytes.fromhex(cases[index%2]['wire'])
        if len(wire) != 122 or offset+size > len(data):
            raise ValueError('Invalid Pak letter fixture size')
        value = bytearray(data[offset:offset+size])
        if slot['compact']:
            value[0],value[4] = 1,128
            value[5:127] = wire
        else:
            value[38:42] = bytes((1,128,4,0))
            value[42:] = wire
        modified[offset:offset+size] = value
        records.append({'label':slot['label'],'data':value.hex(),'case':index%2})
    return bytes(modified),records
