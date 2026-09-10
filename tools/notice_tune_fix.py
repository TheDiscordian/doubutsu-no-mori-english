"""Remove obsolete notice-date slashes and apply English tune notes/OK geometry."""
import argparse
import json
from pathlib import Path
import struct

from aflib import by_vrom, verified_rom, sha256, make_ups, apply_ups
from artwork_matches import converted, data_pointers, objects
from map_artwork import port_quad
from title_assets import DATA_BASE, REL_SHA256, SYMBOLS_SHA256, model_texture_shape
from title_start_fix import reconstruct

ROOT = Path(__file__).resolve().parents[1]
BASE_SHA = 'e8635188fc182cb9f7b735a96b2c71aa1e3e72792be49f4e5d2cda2b9cc9a844'
NOTICE, TUNE, OWNER = 0xABA000, 0xAD1000, 0x79C020
BANKS = {NOTICE: '8f391877c7de2ea7360a7af8a58dd29805540703f1d19c8fef4472e4645064ee',
         TUNE: 'f28322ed55ef9e3e93f473e643893305d348f1911b734458e3fdf2d4c855a1ba',
         OWNER: '458215a2da1132b4cd30d24d4fdaacc656986f2d730c5825ddb41e13994e0459'}
NOTE_DEST = (0x2A68, 0x2AE8, 0x2B68, 0x2868, 0x28E8, 0x2968, 0x29E8,
             0x2A68, 0x2AE8, 0x2B68, 0x2868, 0x28E8, 0x2968, 0x2C68, 0x2CE8, 0x2BE8)
NOTE_SOURCE = (0x49FC40, 0x49F940, 0x49F9C0, 0x49FA40, 0x49FAC0, 0x49FB40, 0x49FBC0,
               0x49FC40, 0x49F940, 0x49F9C0, 0x49FA40, 0x49FAC0, 0x49FB40, 0x49F8C0, 0x4A21C0, 0x4A2140)
LABELS = ('G', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'A', 'B', 'C', 'D', 'E', '?', 'rest', 'off')


def patch_assets(files, rel, symbols):
    if sha256(rel) != REL_SHA256 or sha256(symbols) != SYMBOLS_SHA256:
        raise ValueError('Changed supplied notice/tune source')
    if any(sha256(files[v]) != digest for v, digest in BANKS.items()):
        raise ValueError('Changed current notice/tune bank or native note selector')
    named = {at: (name, size) for at, size, name in objects(symbols)}
    pointers = data_pointers(rel)
    if (named.get(0x80B58) != ('note_moji', 0x240)
            or model_texture_shape(rel[DATA_BASE+0x4A2488:DATA_BASE+0x4A2490]) != (16, 16, 4, 0)
            or struct.unpack_from('>I', rel, DATA_BASE+0x4A248C)[0] != 0x09000000):
        raise ValueError('Changed GC note table or dynamic 16-by-16 I4 consumer')
    old = files[TUNE]; tune = bytearray(old); records = []; installed = {}
    if struct.unpack_from('>2I', old, 0x330) != (0xFD900000, 0x09000000):
        raise ValueError('Changed native dynamic note consumer')
    if struct.unpack_from('>2I', old, 0x360) != (0xF2000000, 0x0003C03C):
        raise ValueError('Changed native note sampling dimensions')
    for index, (destination, source, label) in enumerate(zip(NOTE_DEST, NOTE_SOURCE, LABELS)):
        n = files[OWNER][0x16A0+index*20:0x16A0+(index+1)*20]
        g = rel[DATA_BASE+0x80B58+index*36:DATA_BASE+0x80B58+(index+1)*36]
        if struct.unpack_from('>I', n, 4)[0] != 0x0C000000+destination or pointers.get(0x80B5C+index*36) != source:
            raise ValueError('Native/GC melody index no longer selects the bound label')
        # Pitch/index ordering, vertical offset, and both RGB colours agree. GC
        # stores colour channels as ints; native stores RGB plus alpha as bytes.
        if n[8:12] != g[8:12] or tuple(n[12:15]+n[16:19]) != struct.unpack_from('>6I', g, 12):
            raise ValueError('Native/English note semantics differ')
        if named.get(source, ('', 0))[1] != 128:
            raise ValueError('Note donor does not own a complete 16-by-16 I4 texture')
        texture = converted(rel[DATA_BASE+source:DATA_BASE+source+128], 16, 16, 'i4', 4)
        if destination in installed and installed[destination] != texture:
            raise ValueError('Repeated note label has conflicting donor pixels')
        installed[destination] = texture
        if index >= 14 and old[destination:destination+128] != texture:
            raise ValueError('Rest/off symbols unexpectedly differ; retain native semantics')
        if index < 14:
            tune[destination:destination+128] = texture
        records.append({'melody_index': index, 'label': label, 'native_offset': destination,
                        'gc_texture': f'{source:08X}', 'texture_sha256': sha256(texture),
                        'already_matching': index >= 14})
    if (pointers.get(0x4A9314), pointers.get(0x4A9324)) != (0x4A4980, 0x4A8DE0):
        raise ValueError('Changed English finish-label model')
    if struct.unpack_from('>2I', old, 0x4150) != (0x01004008, 0x0C003650):
        raise ValueError('Changed installed OK geometry consumer')
    tune[0x3650:0x3690] = port_quad(old[0x3650:0x3690],
                                   rel[DATA_BASE+0x4A8DE0:DATA_BASE+0x4A8E20], scale=1)
    notice = bytearray(files[NOTICE])
    if (struct.unpack_from('>2I', notice, 0x9F40) != (0xFD900000, 0x0C00CE18)
            or struct.unpack_from('>2I', notice, 0x9F28) != (0xFCFFFFFF, 0xFFFDF2F9)
            or struct.unpack_from('>2I', notice, 0x9F78) != (0x01008010, 0x0C009B90)):
        raise ValueError('Changed notice slash consumer or intensity-alpha combine mode')
    slash = bytes(notice[0xCE18:0xCE98])
    if sha256(slash) != 'c03dbe1dff58bf2a3af79e7ea8757b13bb3da2a4cd6daf7c66468ace5d9cd10c':
        raise ValueError('Changed date slash texture')
    # I4 supplies alpha under this native combine mode. Both date quads become
    # transparent; the separately drawn proportional English date stays intact.
    notice[0xCE18:0xCE98] = bytes(128)
    return {NOTICE: bytes(notice), TUNE: bytes(tune)}, records


def build(native, base, rel, symbols):
    verified_rom(native)
    if sha256(base) != BASE_SHA:
        raise ValueError('Notice/tune fix requires the combined HUD predecessor')
    files = by_vrom(base)
    changes, notes = patch_assets({v: files[v].extract(base) for v in BANKS}, rel, symbols)
    image = reconstruct(native, base, changes)
    patch = make_ups(native, image)
    if apply_ups(native, patch) != image:
        raise ValueError('Notice/tune patch reconstruction failed')
    report = {'version': 1, 'source_sha256': sha256(native), 'baseline_sha256': BASE_SHA,
              'source_rel_sha256': REL_SHA256, 'source_symbols_sha256': SYMBOLS_SHA256,
              'output_sha256': sha256(image), 'patch_sha256': sha256(patch),
              'changed_files': {f'{v:08X}': sha256(d) for v, d in changes.items()},
              'notes': notes, 'ok_gc_quad': '004A8DE0', 'ok_x': [74, 106], 'ok_y': [-63, -47],
              'notice_date_slash_texture': '00AC6E18', 'rom_bytes': len(image),
              'required_ram_bytes': 0x800000, 'code_changed': False, 'allocation_changed': False,
              'save_format_changed': False, 'melody_indices_and_sound_unchanged': True,
              'fixed_issues': ['V1-03', 'V1-06'], 'hardware_retest': 'pending'}
    return image, patch, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, default=ROOT/'build/v1-hud-label-fix-02')
    parser.add_argument('--output', type=Path, default=ROOT/'build/v1-notice-tune-fix-01')
    args = parser.parse_args()
    image, patch, report = build((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
        (args.base/'animal-forest-title-preview.z64').read_bytes(),
        (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    args.output.mkdir(parents=True, exist_ok=False)
    for name, data in {'animal-forest-title-preview.z64': image, 'animal-forest-title-preview.ups': patch,
                       'fixes.json': (json.dumps(report, indent=2)+'\n').encode()}.items():
        with (args.output/name).open('xb') as target:
            target.write(data)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
