"""Source-bound world-label extension of the persistent cartridge font."""
from pathlib import Path
import struct
from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom

ROOT = Path(__file__).resolve().parents[1]
START, END = 0x800CBF80, 0x800CC9C4
NATIVE_SHA = '043752e0bcffd224e0a23ecde4d80a16c3587cbe7bc3fbd500f3cd2065d66d80'
IMAGE_SHA = '0e8d3860fea6f5d959e61dc0ce95b425f507fb42da16c3a6c2130bfcd2349db0'
RELOC_SHA = '247d442a7cd6c957ce097fe6845818582a98f411810c310be03223761e03353e'
SYMBOLS = {'af_world_reset':1884, 'af_world_load':1964, 'af_world_measure':2088,
           'af_world_draw':2256, 'af_world_font_install':2356,
           'world_hooks':4376, 'world_pixels':4536, 'world_name':4540}
ACCENT_PROFILE = {
    'bytes':4576,
    'image_sha256':'f6fc16ac0f62ad4f6be19bd372dc45fcac35b0810d6e9a23ac71a5a4c09addff',
    'relocation_sha256':'0f137f772732eeef360aecb807de2b1e0f5f1b720db040c96799d13ccaca8d61',
    'symbols':{'af_world_reset':1896,'af_world_load':1976,'af_world_measure':2100,
               'af_world_draw':2268,'af_world_font_install':2368,
               'world_hooks':4392,'world_pixels':4552,'world_name':4556},
}
HOOKS = {
    0x800CBF90: (0x0C00BD30, 'af_world_reset'),
    0x800CC324: (0x0C0259D0, 'af_world_load'),
    0x800CC32C: (0x3C048014, 'af_world_measure'),
    0x800CC330: (0x248446BD, 0),
    0x800CC334: (0x2405000A, 0x3C088014),
    0x800CC338: (0x0C027070, 0x250846A0),
    0x800CC33C: (0x24060020, 0x080330DB),
    0x800CC340: (0x44829000, 0),
    0x800CC9A8: (0x0C0243A6, 'af_world_draw'),
}


def validate_image(data, reloc, report):
    profile=ACCENT_PROFILE if report.get('accent_glyphs') else {
        'bytes':4560,'image_sha256':IMAGE_SHA,'relocation_sha256':RELOC_SHA,'symbols':SYMBOLS}
    if report.get('mail_literals'):
        from accent_mail_font import PROFILE,validate
        validate(data,reloc,report)
        profile=PROFILE
    if (len(data)!=profile['bytes'] or len(reloc)!=profile.get('relocation_bytes',464)
            or sha256(data)!=profile['image_sha256'] or sha256(reloc)!=profile['relocation_sha256']):
        raise ValueError('Changed approved complete world font image')
    text, writable, rodata = struct.unpack_from('>3I', reloc)
    symbols = report['symbols']
    if any(symbols.get(name)!=offset for name,offset in profile['symbols'].items()):
        raise ValueError('Changed approved world-label symbol layout')
    for name in ('af_world_font_install', 'af_world_reset', 'af_world_load',
                 'af_world_measure', 'af_world_draw'):
        if not 0 < symbols.get(name, len(data)) < text: raise ValueError('Missing world-label entry')
    for name, size in (('world_name', 16), ('world_pixels', 4)):
        if not text+writable+rodata <= symbols.get(name, 0) <= len(data)-size:
            raise ValueError('World-name state lacks owned BSS')
    rows = b''
    for address, (old, new) in HOOKS.items():
        rows += struct.pack('>4I', address, old, 0 if isinstance(new, str) else new,
                            0x80C00000+symbols[new] if isinstance(new, str) else 0)
    at = symbols.get('world_hooks', len(data))
    if data[at:at+len(rows)] != rows: raise ValueError('Changed complete world hook table')
    entry='af_accent_font_install' if report.get('mail_literals') else 'af_world_font_install'
    target = 0x08000000 | ((0x80C00000+symbols[entry]) >> 2) & 0x3FFFFFF
    if data[:8] != struct.pack('>2I', target, 0): raise ValueError('World startup entry not installed')


def references():
    from gc_names import symbol_data
    rel=(ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
    symbols=(ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_text()
    if (sha256(rel)!='29306a927eee861b073c571408393f99cb384048684eee4bff3d219725429837'
            or sha256(symbols.encode())!='e5267b989d235655c51885bd2a660b3e8c2cbd46d60b2b3c46166d337c7bca87'):
        raise ValueError('Changed GameCube world-label reference')
    expected={'watch_my_step_move':'148f80c444f266d87a80b7aab38b2412dde7f0933fa60c70260d8fa05f6d2183',
              'watch_my_step_draw':'6c21f1c9583d309a8ee9565caada6f4ca5c4b3fda9acbee2b3137a233967854e'}
    for name,digest in expected.items():
        if sha256(symbol_data(rel,symbols,name))!=digest: raise ValueError('Changed GameCube world consumer')
    return expected


def dependencies(native, current, module_data, additions, module):
    verified_rom(native)
    original = by_vrom(native)[CODE_VROM].extract(native)[START-CODE_RAM:END-CODE_RAM]
    if sha256(original) != NATIVE_SHA or current[START-CODE_RAM:END-CODE_RAM] != original:
        raise ValueError('Changed world-label native update/draw consumers')
    for address, (word, _) in HOOKS.items():
        if struct.unpack_from('>I', original, address-START)[0] != word:
            raise ValueError('Changed native world-label hook')
    if int(module['symbols'].get('af_load_item_name', '0'), 16) != 0x801969C8:
        raise ValueError('World labels require their bound full-name resident import')
    resource = additions.get(0x02A00000, b'')
    if (struct.unpack_from('>I', module_data, 56)[0] != 0x02A00000
            or len(resource) != 72736
            or resource[:32] != struct.pack('>8I', 0x4146494E, 1, 16, 4544, 0, 0, 0, 0)):
        raise ValueError('World labels require the installed complete item-name resource')
    return {'native_sha256': NATIVE_SHA, 'item_resource_sha256': sha256(resource),
            'full_name_entry': 0x801969C8, 'native_state_bytes': 40, 'complete_name_bytes': 16,
            'gamecube_references': references()}
