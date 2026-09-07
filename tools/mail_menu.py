"""Pinned native mail menu choices, static label sources, and test relocation."""

import struct

from aflib import by_vrom, sha256
from runtime_layout import MODULE_RAM, RESERVATION

VROM, RAM, RELOC = 0x777AE0,0x8086F310,0x781D60
SIZE, BSS = 41600,288
FILE_SHA = 'eee60f36d61212bd1719b752916be4825ba0952660fafe1c68054dbd1e9fa9d5'
RELOC_SHA = 'd5703988bd132d02415c4db7cbc2ac9a794dc1908cf9e6fb33f01f03def92af2'
SECTIONS = (38416,3024,160,BSS,792)
DEFINITIONS, DEFINITION_COUNT = 0x80878F08,44
READ, REWRITE, SELECT, MAX_LABEL = 0x80873498,0x80872684,0x80875888,0x8086FA88
FUNCTION_ENDS = {READ:0x80873510,REWRITE:0x808726B0,SELECT:0x808759C8,MAX_LABEL:0x8086FB04}


def verify(data,reloc):
    if (len(data) != SIZE or sha256(data) != FILE_SHA or sha256(reloc) != RELOC_SHA
            or struct.unpack_from('>5I',reloc) != SECTIONS):
        raise ValueError('Unexpected native tag overlay/relocation')


def source(rom):
    files = by_vrom(rom)
    data,reloc = files[VROM].extract(rom),files[RELOC].extract(rom)
    verify(data,reloc)
    return data,reloc


def definitions(data):
    if sha256(data) != FILE_SHA: raise ValueError('Unexpected native tag definitions')
    result = []
    for index in range(DEFINITION_COUNT):
        pointer,count = struct.unpack_from('>2I',data,DEFINITIONS-RAM+index*8)
        if count > 5 or count and not RAM+SECTIONS[0] <= pointer <= DEFINITIONS-count*4:
            raise ValueError('Tag option array is outside static data')
        rows = []
        for slot in range(count):
            word = struct.unpack_from('>I',data,pointer-RAM+slot*4)[0]
            if not RAM+SECTIONS[0] <= word <= DEFINITIONS-12:
                raise ValueError('Tag label is outside static data')
            callback = struct.unpack_from('>I',data,word-RAM+8)[0]
            if callback and not RAM <= callback < RAM+SECTIONS[0]:
                raise ValueError('Tag action points outside native code')
            rows.append({'pointer':word,'callback':callback,
                         'length':len(data[word-RAM:word-RAM+8].rstrip(b' '))})
        result.append({'type':index,'pointer':pointer,'count':count,'options':rows,
                       'max_length':max((row['length'] for row in rows),default=0)})
    for index in (19,20,21):
        if result[index]['options'][0]['callback'] != READ:
            raise ValueError('Received-letter menu does not begin with read')
    for index in (22,23,24):
        if result[index]['options'][0]['callback'] != REWRITE:
            raise ValueError('Player-letter menu does not begin with rewrite')
    if struct.unpack_from('>4I',data,0x8087939C-RAM) != (22,24,19,21):
        raise ValueError('Native mail menu decision table changed')
    return result


def select_type(font,present,menu,mode,field):
    """Native selector reference, not a policy change for generated letters."""
    if not 0 <= font <= 255 or menu not in (1,11,17) or mode not in (0,7) or field not in (0,1):
        raise ValueError('Invalid native mail menu case')
    if font == 255: return 0
    if menu in (11,17): return 20 if font in (0,3) else 19
    if mode == 7: return 30 if font == 1 else 0
    result = (22,24,19,21)[int(bool(present))+(0 if font == 1 else 2)]
    if field or font in (0,3): result = {22:23,19:20}.get(result,result)
    return result


def cases():
    return [{'font':font,'present':gift,'split':split,'menu':menu,'mode':mode,'field':field,
             'expected':select_type(font,gift,menu,mode,field)}
            for font in (0,1,2,3,4,255) for gift in (0,0x2001) for split in (0,128)
            for menu,mode,field in ((1,0,0),(1,0,1),(11,0,0),(17,0,0),(1,7,0))]


def relocated(data,reloc,base):
    """Independent loader model limited to the exact original tag overlay."""
    verify(data,reloc)
    if base&15 or not MODULE_RAM+RESERVATION <= base <= 0x80400000-SIZE-BSS:
        raise ValueError('Invalid native tag test base')
    text,writable,rodata,bss,count = SECTIONS
    result,high = bytearray(data),{}
    starts,sizes = (0,0,text,text+writable),(0,text,writable,rodata)
    def store(at,value): struct.pack_into('>I',result,at,value&0xFFFFFFFF)
    def target(value):
        if not RAM <= value < RAM+SIZE+BSS: raise ValueError('Tag relocation target exceeds its file/BSS')
        return base+value-RAM
    for (entry,) in struct.iter_unpack('>I',reloc[20:20+count*4]):
        section,kind,offset = entry>>30,(entry>>24)&63,entry&0xFFFFFF
        if not section or offset&3 or offset+4 > sizes[section]:
            raise ValueError('Invalid tag relocation location')
        at = starts[section]+offset
        word = struct.unpack_from('>I',result,at)[0]
        if kind == 2:
            if not word&0x0F000000: store(at,target(word))
        elif kind == 4:
            if word>>26 not in (2,3): raise ValueError('Invalid tag relocated jump')
            store(at,(word&0xFC000000)|((target(0x80000000|((word&0x3FFFFFF)<<2))&0xFFFFFFF)>>2))
        elif kind == 5:
            if word>>26 != 15: raise ValueError('Invalid tag high relocation')
            high[(word>>16)&31] = at,word
        elif kind == 6:
            register = (word>>21)&31
            if register not in high: raise ValueError('Unpaired tag low relocation')
            hi_at,hi_word = high[register]
            value = ((hi_word&0xFFFF)<<16)+(word&0xFFFF)-(0x10000 if word&0x8000 else 0)
            if not value&0x0F000000:
                value = target(value)
                store(hi_at,(hi_word&0xFFFF0000)|(((value+0x8000)>>16)&0xFFFF))
                store(at,(word&0xFFFF0000)|(value&0xFFFF))
        else: raise ValueError('Unsupported native tag relocation')
    return bytes(result)+bytes(bss)
