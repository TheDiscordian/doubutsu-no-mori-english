"""Pinned native NPC letter-show overlays and independent relocation evidence."""

from dataclasses import dataclass
import struct

from aflib import by_vrom, sha256
from runtime_layout import MODULE_RAM, RESERVATION


@dataclass(frozen=True)
class ShowOverlay:
    vrom: int
    ram: int
    relocation: int
    file_bytes: int
    sections: tuple
    file_sha256: str
    relocation_sha256: str
    handler: int
    handler_end: int
    letter: int
    globals: int = 0

    @property
    def resident_bytes(self):
        return self.file_bytes+self.sections[3]


OVERLAYS = {
    'first_job': ShowOverlay(0x814FA0,0x8091CB30,0x815AD0,2864,(2784,80,0,176,33),
        '3da47017db9ccc53be92f9afdd71d48a364ba172832cdfadc1a60ca4f6f54a8c',
        '7589cd6d6e9138065042c2652b079624035e3c60f856ed4e44765515a8f01f23',
        0x8091D3E0,0x8091D484,0x8091D660),
    'ordinary': ShowOverlay(0x815B70,0x8091D7B0,0x81A1A0,17968,(16768,1200,0,352,552),
        '4d7822e44c34b224c6e6cb8374407ebe1c3b56279e19ab3eee0932d3b8ca9320',
        '88122500ea6e119be5ac7fc89f3091df1fdaac6b0496f983aa0abd4cc5f0688c',
        0x80921618,0x80921704,0x80921E90,0x80921DE8),
}


def source(rom,name):
    spec = OVERLAYS[name]
    files = by_vrom(rom)
    data,reloc = files[spec.vrom].extract(rom),files[spec.relocation].extract(rom)
    verify(spec,data,reloc)
    return data,reloc


def verify(spec,data,reloc):
    if (spec not in OVERLAYS.values() or len(data) != spec.file_bytes
            or sha256(data) != spec.file_sha256
            or sha256(reloc) != spec.relocation_sha256
            or struct.unpack_from('>5I',reloc) != spec.sections):
        raise ValueError('Unexpected NPC letter-show overlay or relocation input')


def relocated(spec,data,reloc,base):
    """Model only the two exact original overlays, including BSS address targets.

    Preserve the loader's HI register cache for reused low relocations. Actual
    native loading, cache maintenance, and BSS clearing require emulator tests.
    """
    verify(spec,data,reloc)
    return relocate_verified_data(spec, data, reloc, base)


def relocate_verified_data(spec, data, reloc, base, *, address_constants=(), base_alignment=16):
    """Relocate caller-verified native files; callers must first bind full hashes."""
    if (type(base_alignment) is not int or base_alignment not in (8,16) or
            type(base) is not int or base % base_alignment or
            not MODULE_RAM+RESERVATION <= base <= 0x80400000-spec.resident_bytes):
        raise ValueError('Invalid NPC show relocation base')
    text,writable,rodata,bss,count = spec.sections
    result,high = bytearray(data),{}
    starts,sizes = (0,0,text,text+writable),(0,text,writable,rodata)
    def store(at,value): struct.pack_into('>I',result,at,value&0xFFFFFFFF)
    def target(value):
        if not spec.ram <= value < spec.ram+spec.resident_bytes and value not in address_constants:
            raise ValueError('NPC show relocation points outside its file and BSS')
        return base+value-spec.ram
    for (entry,) in struct.iter_unpack('>I',reloc[20:20+count*4]):
        section,kind,offset = entry>>30,(entry>>24)&63,entry&0xFFFFFF
        if section == 0 or offset&3 or offset+4 > sizes[section]:
            raise ValueError('Invalid NPC show relocation location')
        at = starts[section]+offset
        word = struct.unpack_from('>I',result,at)[0]
        if kind == 2:
            if not word&0x0F000000: store(at,target(word))
        elif kind == 4:
            if word>>26 not in (2,3): raise ValueError('Invalid NPC show relocated jump')
            store(at,(word&0xFC000000)|((target(0x80000000|((word&0x3FFFFFF)<<2))&0xFFFFFFF)>>2))
        elif kind == 5:
            if word>>26 != 15: raise ValueError('Invalid NPC show high relocation')
            high[(word>>16)&31] = at,word
        elif kind == 6:
            register = (word>>21)&31
            if register not in high: raise ValueError('Unpaired NPC show low relocation')
            hi_at,hi_word = high[register]
            value = ((hi_word&0xFFFF)<<16)+(word&0xFFFF)-(0x10000 if word&0x8000 else 0)
            if not value&0x0F000000:
                value = target(value)
                store(hi_at,(hi_word&0xFFFF0000)|(((value+0x8000)>>16)&0xFFFF))
                store(at,(word&0xFFFF0000)|(value&0xFFFF))
        else:
            raise ValueError('Unsupported NPC show relocation kind')
    return bytes(result)+bytes(bss)
