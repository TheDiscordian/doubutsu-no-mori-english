"""Convert Punchy's actual shirt and install the bounded shared resource reader."""
import struct

from aflib import CODE_RAM, by_vrom, sha256, verified_rom
from gamecube import rarc_files
from gc_names import symbol_data
from v3_import_catalog import REL_SHA, SYMBOLS_SHA
from v3_registry import CLOTHING_REGISTRY_VERSION, clothing_slot
from v3_villager_art import native_palette, pack4, untile
from v3_villager_defaults import PALETTES, TEXTURES, pixels
from v3_villager_text import FIRST_SHA

ABI, DATA, LIMIT = 28, 0x2820, 0x2900
ENTRY, END = 0x800B1EDC, 0x800B1F74
SOURCE_SHA = 'bc35c64e7d10f51813c50f8523f1aa31a2ac54f5a3481bc5ef59b21cfd38f736'
SOURCES = ('tools/v3_clothing.py', 'tools/v3_registry.py', 'overlays/v3/clothing.c', 'overlays/v3/clothing.h')


def convert(native, first, rel, symbols, *, donor_item=0x24BF):
    verified_rom(native)
    if (sha256(first), sha256(rel), sha256(symbols)) != (FIRST_SHA, REL_SHA, SYMBOLS_SHA):
        raise ValueError('Clothing conversion requires the verified English donor')
    members = dict(rarc_files(first))
    raw_textures, raw_palettes = (members['data/'+name+'.bin'] for name in ('tex_boy', 'pallet_boy'))
    names = symbol_data(rel, symbols.decode(), 'itemName_cloth')
    prices = symbol_data(rel, symbols.decode(), 'cloth_price_table')
    if tuple(map(len, (raw_textures, raw_palettes, names, prices))) != (0x20000, 0x2000, 255*16, 512):
        raise ValueError('Changed donor clothing dimensions')
    item, index, vrom = clothing_slot(donor_item)
    donor_index = donor_item-0x2400
    raw_tex = raw_textures[donor_index*512:(donor_index+1)*512]
    raw_pal = raw_palettes[donor_index*32:(donor_index+1)*32]
    texture, palette = pack4(untile(raw_tex, 32, 32, 4)), native_palette(raw_pal)
    expected_name, expected = {
        0x24BF: (b'cherry shirt    ',
            ('bc444e2665e530c51d7049facfd29db145410854c53c4927da286ba70354b9f0',
             '505f8de9046453227685d0ea19ea21576528b4f527404027d43e83f2d6e679a7')),
        0x241A: (b'red aloha shirt ',
            ('9be1b9563fbe3890a74e9c49eb59d6abb4c1e6631c1e63e031fdcb919f391768',
             'e0ed37453e0e32b4939acfc7ebde815d40277c73c17d36eeec019213560ed79d')),
        0x241B: (b'blue aloha shirt',
            ('9be1b9563fbe3890a74e9c49eb59d6abb4c1e6631c1e63e031fdcb919f391768',
             '70d36ccaccc6bb494d92586a43146bd41815807516f991c67902da0a9173eb5a')),
    }[donor_item]
    if (sha256(texture), sha256(palette)) != expected:
        raise ValueError('Changed complete imported-shirt artwork')
    files = by_vrom(native)
    native_tex, native_pal = (files[v].extract(native) for v in (TEXTURES, PALETTES))
    wanted = pixels(texture, palette)
    if any(wanted == pixels(native_tex[i*512:(i+1)*512], native_pal[i*32:(i+1)*32]) for i in range(256)):
        raise ValueError('Imported shirt unexpectedly aliases an existing native garment')
    name = names[donor_index*16:(donor_index+1)*16]
    price = struct.unpack_from('>H', prices, donor_index*2)[0]
    if name != expected_name or index != item-0x2400:
        raise ValueError('Changed clothing name or fixed index assignment')
    # Native item type 3 is unused, and reviewed donor furniture ends below
    # 3400. Never claim an extended clothing record is furniture.
    ftr2 = symbol_data(rel, symbols.decode(), 'ftrName2_table')
    if len(ftr2) != 242*16 or 0x3000+len(ftr2)//16*4 > 0x3400:
        raise ValueError('Clothing reservation collides with donor furniture')
    record = struct.pack('>HHIHBB16sI', item, index, vrom, price, 1, 0, name, 0)
    return texture+palette, record, {'donor_item_id': f'{donor_item:04X}', 'item_id': f'{item:04X}',
        'resource_index': index, 'name': name.decode('ascii').rstrip(), 'price': price,
        'vrom': f'{vrom:08X}', 'bytes': 544, 'registry_version': CLOTHING_REGISTRY_VERSION,
        'donor_texture_sha256': sha256(raw_tex), 'donor_palette_sha256': sha256(raw_pal),
        'texture_sha256': sha256(texture), 'palette_sha256': sha256(palette),
        'resource_sha256': sha256(texture+palette), 'metadata_sha256': sha256(record),
        'original_garments_retained': 256, 'playable': False, 'save_profile_installed': False}


def install(code, blob, symbols, resource, record):
    at = ENTRY-CODE_RAM
    target = symbols['af_v3_load_clothing']
    if (sha256(code[at:END-CODE_RAM]) != SOURCE_SHA or len(blob) != 0xC000
            or any(blob[DATA:LIMIT]) or len(record) != 32 or len(resource) != 544
            or not 0x80460100 <= target < 0x80461000 or target % 4):
        raise ValueError('Changed clothing reader or overlapping resident metadata')
    before = bytes(code[at:at+8])
    struct.pack_into('>II', code, at, 0x08000000 | ((target >> 2) & 0x3FFFFFF), 0)
    blob[DATA:DATA+len(record)] = record
    return {'entry': f'{ENTRY:08X}', 'native_function_sha256': SOURCE_SHA,
            'before': before.hex(), 'after': bytes(code[at:at+8]).hex(),
            'metadata_ram': f'{0x80460000+DATA:08X}', 'native_garments_unchanged': True,
            'npc_streaming_clothes_installed': False, 'wearing_and_item_readers_installed': False,
            'punchy_defaults_enabled': False}
