"""Decode cartridge/disc texture bytes for local asset inspection, without editing art."""
import argparse
from pathlib import Path
import struct
import zlib

from aflib import by_vrom, sha256, verified_rom
from title_assets import DATA_BASE, REL_SHA256, rgb5a3, untile

ROOT = Path(__file__).resolve().parents[1]


def native_range(rom, address, size):
    entries = [e for e in by_vrom(rom).values()
               if e.vstart <= address and address+size <= e.vend and e.pstart != 0xFFFFFFFF]
    if len(entries) != 1 or size <= 0:
        raise ValueError('Texture range must belong to one file-backed DMA entry')
    entry = entries[0]
    return entry.extract(rom)[address-entry.vstart:address-entry.vstart+size]


def rgba5551(value):
    channels = [(value >> shift) & 31 for shift in (11, 6, 1)]
    return bytes((v << 3) | (v >> 2) for v in channels)+bytes([255*(value & 1)])


def decode(data, width, height, fmt, palette=None, *, gamecube=False):
    if fmt not in ('ci4', 'i4', 'ia8') or width <= 0 or height <= 0:
        raise ValueError('Unsupported preview texture')
    bits = 8 if fmt == 'ia8' else 4
    if len(data)*8 != width*height*bits:
        raise ValueError('Incorrect texture size')
    if gamecube:
        samples = untile(data, width, height, bits)
        if fmt == 'ia8':
            samples = bytes((v << 4 & 240) | v >> 4 for v in samples)
    else:
        samples = data if bits == 8 else bytes(v for b in data for v in (b >> 4, b & 15))
    if fmt == 'ci4':
        if palette is None or len(palette) != 32:
            raise ValueError('CI4 preview requires sixteen palette entries')
        colours = [(rgb5a3 if gamecube else rgba5551)(v) for v in struct.unpack('>16H', palette)]
        return b''.join(colours[v] for v in samples)
    if palette is not None:
        raise ValueError('Intensity preview must not have a palette')
    if fmt == 'i4':
        return b''.join(bytes([v*17, v*17, v*17, 255]) for v in samples)
    return b''.join(bytes([(v >> 4)*17]*3+[(v & 15)*17]) for v in samples)


def png_rgba(width, height, rgba, scale=1):
    if width <= 0 or height <= 0 or not 1 <= scale <= 16 or len(rgba) != width*height*4:
        raise ValueError('Invalid PNG dimensions or data')
    def chunk(kind, value):
        return struct.pack('>I', len(value))+kind+value+struct.pack('>I', zlib.crc32(kind+value))
    rows = []
    for y in range(height):
        row = rgba[y*width*4:(y+1)*width*4]
        expanded = b''.join(row[x:x+4]*scale for x in range(0, len(row), 4))
        rows.extend([b'\0'+expanded]*scale)
    return (b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR', struct.pack('>2I5B', width*scale, height*scale, 8, 6, 0, 0, 0))
            +chunk(b'IDAT', zlib.compress(b''.join(rows)))+chunk(b'IEND', b''))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gamecube', action='store_true')
    parser.add_argument('--address', type=lambda x: int(x, 16), required=True)
    parser.add_argument('--palette', type=lambda x: int(x, 16))
    parser.add_argument('--width', type=int, required=True)
    parser.add_argument('--height', type=int, required=True)
    parser.add_argument('--format', choices=('ci4', 'i4', 'ia8'), required=True)
    parser.add_argument('--scale', type=int, default=4)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.gamecube:
        data = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        if sha256(data) != REL_SHA256:
            raise ValueError('Unexpected supplied GameCube source')
        def read(address, size):
            if address < 0 or DATA_BASE+address+size > len(data):
                raise ValueError('GameCube range out of bounds')
            return data[DATA_BASE+address:DATA_BASE+address+size]
    else:
        data = verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
        def read(address, size):
            return native_range(data, address, size)
    size = args.width*args.height*(8 if args.format == 'ia8' else 4)//8
    rgba = decode(read(args.address, size), args.width, args.height, args.format,
                  None if args.palette is None else read(args.palette, 32), gamecube=args.gamecube)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('xb') as target:
        target.write(png_rgba(args.width, args.height, rgba, args.scale))
    print(args.output)


if __name__ == '__main__':
    main()
