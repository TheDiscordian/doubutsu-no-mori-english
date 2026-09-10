#!/usr/bin/env python3
"""Extract scoped English title assets and lossless N64 texture representations."""
import argparse
import json
from pathlib import Path
import re
import struct

from aflib import sha256

ROOT = Path(__file__).resolve().parents[1]
REL_SHA256 = '29306a927eee861b073c571408393f99cb384048684eee4bff3d219725429837'
SYMBOLS_SHA256 = 'e5267b989d235655c51885bd2a660b3e8c2cbd46d60b2b3c46166d337c7bca87'
DATA_BASE, START, END = 0x2DD340, 0x5E5020, 0x5F3CD8
REGION_SHA256 = '7c6ad2869ec1e3760b134c8fcc073518590beeeb2204dddf3e3232ea3d26303c'
# Offsets distinguish the repeated local palette and letter symbol names.
# Width/height come from the scoped model's Dolphin texture commands.
CI4 = (
    (0x5E6A40, 32, 96, 0x5E6A20), (0x5E7040, 64, 64, 0x5E6A20),
    (0x5E7840, 64, 64, 0x5E6A20), (0x5E8040, 32, 64, 0x5E6A20),
    (0x5E8440, 32, 96, 0x5E6A20), (0x5E8A40, 64, 64, 0x5E6A20),
    (0x5E9240, 64, 32, 0x5E6A20), (0x5E9640, 64, 64, 0x5E6A20),
    (0x5EEB60, 48, 64, 0x5EEB40), (0x5EF160, 64, 64, 0x5EEB40),
    (0x5EF960, 64, 64, 0x5EEB40), (0x5F0160, 64, 64, 0x5EEB40),
    (0x5F0960, 64, 32, 0x5EEB40),
    (0x5F1780, 64, 64, 0x5F1760), (0x5F1F80, 64, 32, 0x5F1760),
    (0x5F2380, 64, 64, 0x5F1760), (0x5F2B80, 32, 96, 0x5F1760),
    (0x5F3180, 48, 64, 0x5F1760),
)
I4 = ((0x5EA2E0, 64, 128), (0x5EB2E0, 64, 128),
      (0x5EC2E0, 64, 128), (0x5ED2E0, 64, 128), (0x5F3A60, 32, 32))
IA4 = tuple((offset, 64, 16) for offset in range(0x5E5020, 0x5E6420, 0x400))
MODEL_OFFSETS = (
    0x5EA040, 0x5EA070, 0x5EA0D0, 0x5EA0A0, 0x5EA100, 0x5EA130, 0x5EA160, 0x5EA190,
    0x5F0EA0, 0x5F0F00, 0x5F0ED0, 0x5F0F60, 0x5F0F30,
    0x5F3980, 0x5F3950, 0x5F38F0, 0x5F3920, 0x5F38C0,
    0x5EE3E0, 0x5EE408, 0x5EE458, 0x5EE430, 0x5F3CA0,
)


def model_texture_shape(data):
    if not data or len(data) % 8:
        raise ValueError('Invalid title display-list length')
    words = [a for a, _ in struct.iter_unpack('>2I', data) if a >> 24 == 0xFD]
    if len(words) != 1 or not words[0] & (1 << 18):
        raise ValueError('Title model must use one Dolphin texture command')
    word = words[0]
    return (word & 1023)+1, (((word >> 10) & 255)+1)*4, (word >> 21) & 7, (word >> 19) & 3


def untile(data, width, height, bits):
    """Return exact row-major samples from complete GX 32-byte blocks."""
    if bits not in (4, 8) or type(width) is not int or type(height) is not int:
        raise ValueError('Unsupported title texture dimensions/format')
    block_height = 8 if bits == 4 else 4
    if width <= 0 or height <= 0 or width % 8 or height % block_height or len(data)*8 != width*height*bits:
        raise ValueError('Title texture does not contain complete correctly-sized blocks')
    samples = bytes(value for byte in data for value in (byte >> 4, byte & 15)) if bits == 4 else data
    out = bytearray(width*height)
    for y in range(height):
        for x in range(width):
            tile = (y//block_height)*(width//8)+x//8
            index = tile*8*block_height+(y % block_height)*8+x % 8
            out[y*width+x] = samples[index]
    return bytes(out)


def pack4(samples):
    if len(samples) % 2 or any(value > 15 for value in samples):
        raise ValueError('Invalid four-bit title samples')
    return bytes((samples[i] << 4) | samples[i+1] for i in range(0, len(samples), 2))


def rgb5a3(value):
    if not 0 <= value <= 0xFFFF:
        raise ValueError('Invalid RGB5A3 colour')
    if value & 0x8000:
        channels = tuple((value >> shift) & 31 for shift in (10, 5, 0))
        return bytes(((v << 3) | (v >> 2)) for v in channels)+b'\xff'
    alpha = value >> 12
    return bytes(((value >> shift) & 15)*17 for shift in (8, 4, 0))+bytes([(alpha << 5) | (alpha << 2) | (alpha >> 1)])


def scoped_symbols(data):
    if sha256(data) != SYMBOLS_SHA256:
        raise ValueError('Changed title symbol reference')
    pattern = r'^(\w+) = \.data:0x([0-9A-Fa-f]+); // type:object size:0x([0-9A-Fa-f]+) '
    result = {}
    for name, offset, size in re.findall(pattern, data.decode(), re.M):
        offset, size = int(offset, 16), int(size, 16)
        if not START <= offset < END:
            continue
        if offset in result or size <= 0 or offset+size > END:
            raise ValueError('Ambiguous or out-of-bounds title asset')
        result[offset] = {'symbol': name, 'offset': f'{offset:08X}', 'bytes': size}
    previous = START
    for offset, entry in sorted(result.items()):
        if offset < previous:
            raise ValueError('Overlapping title symbols')
        previous = offset+entry['bytes']
    return result


def extract(rel, symbols):
    if sha256(rel) != REL_SHA256 or sha256(rel[DATA_BASE+START:DATA_BASE+END]) != REGION_SHA256:
        raise ValueError('Changed supplied English title asset region')
    entries = scoped_symbols(symbols)
    files = {}
    def raw(offset):
        entry = entries[offset]
        return rel[DATA_BASE+offset:DATA_BASE+offset+entry['bytes']]
    plans = [(row[0], row[1], row[2], 2) for row in CI4]+[(offset, w, h, 4) for offset, w, h in I4]
    if len(plans) != len(MODEL_OFFSETS):
        raise ValueError('Incomplete title model bindings')
    for (offset, width, height, fmt), model_offset in zip(plans, MODEL_OFFSETS):
        if model_texture_shape(raw(model_offset)) != (width, height, fmt, 0):
            raise ValueError(f'Title texture shape differs from its actual display list: {offset:08X}')
    for offset, entry in entries.items():
        name = f"{offset:08X}-{entry['symbol']}.gc.bin"
        files[name] = raw(offset)
        entry.update(source_file=name, source_sha256=sha256(files[name]))
    textures = []
    for offset, width, height, palette_offset in CI4:
        samples = untile(raw(offset), width, height, 4)
        palette_data = raw(palette_offset)
        if len(palette_data) != 32:
            raise ValueError('Title CI4 palette must have sixteen entries')
        palette = [rgb5a3(value) for value in struct.unpack('>16H', palette_data)]
        rgba = b''.join(palette[value] for value in samples)
        name = f'{offset:08X}.rgba32.bin'
        files[name] = rgba
        textures.append({'offset': f'{offset:08X}', 'width': width, 'height': height,
            'source_format': 'GX_C4', 'palette_offset': f'{palette_offset:08X}',
            'output_format': 'N64_RGBA32', 'file': name, 'bytes': len(rgba), 'sha256': sha256(rgba),
            'partial_alpha_pixels': sum(0 < palette[v][3] < 255 for v in samples)})
    for kind, plans, bits in (('I4', I4, 4), ('IA4', IA4, 8)):
        for offset, width, height in plans:
            samples = untile(raw(offset), width, height, bits)
            # GX IA4 stores A:I, whereas N64 IA8 stores I:A in each byte.
            converted = pack4(samples) if bits == 4 else bytes(((v & 15) << 4) | (v >> 4) for v in samples)
            fmt = 'I4' if bits == 4 else 'IA8'
            name = f'{offset:08X}.{fmt.lower()}.bin'
            files[name] = converted
            textures.append({'offset': f'{offset:08X}', 'width': width, 'height': height,
                'source_format': 'GX_'+kind, 'output_format': 'N64_'+fmt,
                'file': name, 'bytes': len(converted), 'sha256': sha256(converted)})
    report = {'version': 1, 'source_sha256': REL_SHA256, 'symbols_sha256': SYMBOLS_SHA256,
        'region_sha256': REGION_SHA256, 'assets': list(entries.values()), 'textures': textures,
        'output_texture_bytes': sum(row['bytes'] for row in textures),
        'installed': False, 'status': 'Local extracted assets; N64 drawing and animation integration pending'}
    return files, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rel', type=Path, default=ROOT/'build/gamecube/files/foresta.rel.szs.decoded')
    parser.add_argument('--symbols', type=Path, default=ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt')
    parser.add_argument('--output', type=Path, default=ROOT/'build/title-english-assets')
    args = parser.parse_args()
    files, report = extract(args.rel.read_bytes(), args.symbols.read_bytes())
    args.output.mkdir(parents=True, exist_ok=True)
    for name, value in files.items():
        path = args.output/name
        if path.exists() or path.is_symlink():
            if path.is_symlink() or path.read_bytes() != value:
                raise ValueError('Existing title output differs: '+str(path))
        else:
            with path.open('xb') as target:
                target.write(value)
    (args.output/'assets.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'output': str(args.output), 'scoped_assets': len(report['assets']),
        'textures': len(report['textures']), 'texture_bytes': report['output_texture_bytes'],
        'installed': False}, indent=2))


if __name__ == '__main__':
    main()
