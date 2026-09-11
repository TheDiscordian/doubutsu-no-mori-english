"""Read-only source-bound review of 28 household images and one unresolved igloo detail."""
import argparse
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256, verified_rom
from apply_translation import write_new
from artwork_matches import data_pointers, native_material, objects
from texture_preview import decode, png_rgba
from title_assets import DATA_BASE, REL_SHA256, SYMBOLS_SHA256

ROOT = Path(__file__).resolve().parents[1]
CURRENT_SHA = '2a04f6e5c54dc2d5ed03009395af815b464bebdef51d67d899554deb54b3bcb4'
INVENTORY_SHA = '424fb279c90e7ac27a30ecbdf6c578b58cdfaeb3cd8549148a2d866816ad276f'
SELECTED = '''01430468 01432708 01432908 01432A08 01432D88 01432F88
0143B708 0143B908 0143BA08 0143BD88 0143BF88
0145AFD0 0145AE30 0145AEB0 0145AC30 0145AA30 0145A830
014CDAF8 014CD9F8 014CDBF8 014CDC78 014CDD78 014CDF78 014CE078 014CE178
0151E898 0151E598 0151EA18'''.split()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'build/household-artwork-review-01')
    args = parser.parse_args()
    output = args.output.resolve()
    if args.output.is_symlink() or output.exists() or not output.is_relative_to(ROOT/'build'):
        raise ValueError('Review output must be a fresh local build directory')
    original = verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    current = (ROOT/'build/v1rc8/Animal Forest English V1RC8.z64').read_bytes()
    if sha256(current) != CURRENT_SHA:
        raise ValueError('Review requires the current RC8 candidate')
    rel = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
    symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
    inventory_raw = (ROOT/'build/artwork-matches-01.json').read_bytes()
    if sha256(rel) != REL_SHA256 or sha256(symbols) != SYMBOLS_SHA256 or sha256(inventory_raw) != INVENTORY_SHA:
        raise ValueError('Review source identities changed')
    inventory = json.loads(inventory_raw)
    files, installed = by_vrom(original), by_vrom(current)
    pointers, models = data_pointers(rel), objects(symbols)
    rows, images = [], {}
    for address in SELECTED+['0138DA28']:
        matches = [r for r in inventory['native_candidates'] if r['texture'] == address]
        assert len(matches) == 1
        row = matches[0]
        owner = int(row['owner'], 16)
        obj = files[owner].extract(original)
        current_obj = installed[owner].extract(current)
        assert sha256(obj) == row['owner_sha256'] and current_obj == obj
        command = int(row['commands'][0], 16)-owner
        parsed, reason = native_material(obj, command)
        assert reason is None and all(parsed[key] == row[key] for key in parsed)
        palette_command = command-0x30
        a, pointer = struct.unpack_from('>II', obj, palette_command)
        assert a == 0xFD100000 and pointer >> 24 == 6
        colours = 256 if row['format'] == 'ci8' else 16
        assert obj[command-0x10:command-8] == struct.pack('>II', 0xF0000000, 0x07000000 | (colours-1) << 14)
        palette_at = pointer & 0xFFFFFF
        palette = obj[palette_at:palette_at+colours*2]
        data = obj[row['offset']:row['offset']+row['bytes']]
        assert sha256(data) == row['texel_sha256']
        rgba = decode(data, row['width'], row['height'], row['format'], palette)
        images[address+'.png'] = png_rgba(row['width'], row['height'], rgba, 4)
        record = {**row, 'palette': f'{owner+palette_at:08X}', 'palette_sha256': sha256(palette),
            'palette_entries': colours, 'rgba_sha256': sha256(rgba), 'current_owner_unchanged': True,
            'material_start': f'{owner+palette_command:08X}',
            'material_sha256': sha256(obj[palette_command:command+0x38])}
        if address in SELECTED:
            match = row['gc_matches'][0]
            donor = [g for g in inventory['gc_sources'] if g['texture'] == match['texture']
                     and g['format'] == row['format'] and g['width'] == row['width'] and g['height'] == row['height']]
            assert len(donor) == 1
            donor = donor[0]
            reader = donor['readers'][0]
            gc_command = int(reader['command'], 16)
            model = [m for m in models if m[0] <= gc_command < m[0]+m[1] and m[2] == reader['model']]
            assert len(model) == 1
            loads = [at for at in range(model[0][0], gc_command, 8)
                     if struct.unpack_from('>I', rel, DATA_BASE+at)[0] in (0xF08F4010, 0xF0804100)]
            assert loads
            gc_palette_command = loads[-1]
            assert struct.unpack_from('>I', rel, DATA_BASE+gc_palette_command)[0] == (
                0xF0804100 if colours == 256 else 0xF08F4010)
            assert not any(rel[DATA_BASE+at] in (0xDE, 0xDF) for at in range(gc_palette_command+8, gc_command, 8))
            gc_palette = pointers[gc_palette_command+4]
            gc_texture = int(donor['texture'], 16)
            assert pointers[gc_command+4] == gc_texture
            gc_data = rel[DATA_BASE+gc_texture:DATA_BASE+gc_texture+row['bytes']]
            gc_colours = rel[DATA_BASE+gc_palette:DATA_BASE+gc_palette+colours*2]
            gc_rgba = decode(gc_data, row['width'], row['height'], row['format'], gc_colours, gamecube=True)
            equal = all(rgba[i:i+4] == gc_rgba[i:i+4] or rgba[i+3] == gc_rgba[i+3] == 0
                        for i in range(0, len(rgba), 4))
            if not equal:
                images[address+'-gc.png'] = png_rgba(row['width'], row['height'], gc_rgba, 4)
            record.update(gc_texture=donor['texture'], gc_symbol=donor['symbol'], gc_reader=reader,
                gc_palette=f'{gc_palette:08X}', gc_palette_sha256=sha256(gc_colours),
                gc_visible_pixels_equal=equal, gc_rgba_sha256=sha256(gc_rgba))
        else:
            assert obj[0x1AC8:0x1AD0] == bytes.fromhex('0101402806000CC8')
            record['vertices'] = [struct.unpack_from('>3hH2h4B', obj, 0xCC8+i*16) for i in range(20)]
            record['vertex_sha256'] = sha256(obj[0xCC8:0xE08])
            record['triangles_hex'] = obj[0x1AD0:0x1B00].hex()
            record['gc_pot_is_not_a_matched_donor'] = True
        rows.append(record)
        print(address, record.get('gc_symbol', 'Native igloo detail'),
              record.get('gc_visible_pixels_equal', 'material/vertices bound'))
    report = {'source_rom_sha256': sha256(original), 'candidate_sha256': CURRENT_SHA,
        'source_rel_sha256': REL_SHA256, 'source_symbols_sha256': SYMBOLS_SHA256,
        'inventory_sha256': INVENTORY_SHA, 'script_sha256': sha256(Path(__file__).read_bytes()),
        'decoder_sha256': sha256((ROOT/'tools/texture_preview.py').read_bytes()),
        'rows': rows, 'cartridge_modified': False, 'old_builds_retested': False,
        'status': 'Source and current materials checked; visual findings belong in the review checkpoint',
        'png_sha256': {name: sha256(raw) for name, raw in images.items()}}
    output.mkdir(parents=True, exist_ok=False)
    for name, raw in images.items():
        write_new(output/name, raw)
    encoded = (json.dumps(report, indent=2)+'\n').encode()
    write_new(output/'inspection.json', encoded)
    print('Receipt:', sha256(encoded))


if __name__ == '__main__':
    main()
