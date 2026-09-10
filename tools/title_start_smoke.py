"""Read-only proof of the preview's actual loaded title actor and texture bank."""
import struct

from aflib import by_vrom, sha256
from catalogue_names import Image
from npc_mail_show import relocate_verified_data
from title_press_start import ACTOR, RELOC, ASSETS, RAM, SOURCE_HASHES

PREVIEW_SHA256 = 'f8257e4d9a0625d51965c551541a3a560267f92ff758437b5c74542767a949db'


def verify(debug, rom):
    if sha256(rom) != PREVIEW_SHA256:
        raise ValueError('Title memory observation requires the exact Press Start preview')
    def read(address, size):
        if address % 4 or not 0x8019C8E0 <= address <= 0x80400000-size:
            raise ValueError('Title observation is outside allocated game memory')
        data = debug.read_memory(address, size)
        if len(data) != size:
            raise ValueError('Truncated title memory observation')
        return data
    pointer_bytes = debug.read_memory(0x8010EF90, 4)
    if len(pointer_bytes) != 4:
        raise ValueError('Truncated title game pointer')
    game = struct.unpack('>I', pointer_bytes)[0]
    count, actor = struct.unpack('>2I', read(game+0x1C9C, 8))
    if count > 64:
        raise ValueError('Invalid background actor count')
    found, seen = [], set()
    while actor:
        if actor in seen or len(seen) >= count:
            raise ValueError('Cyclic or excessive title actor list')
        seen.add(actor)
        data = read(actor, 0x174)
        if data[2] != 4:
            raise ValueError('Non-background actor in title list')
        if struct.unpack_from('>H', data)[0] == 0xAB:
            found.append((actor, data))
        actor = struct.unpack_from('>I', data, 0x158)[0]
    if len(seen) != count or len(found) != 1:
        raise ValueError('Expected exactly one active title actor')
    actor, data = found[0]
    update = struct.unpack_from('>I', data, 0x164)[0]
    base = update-(0x80AA1E58-RAM)
    bank = struct.unpack('>I', read(actor+0x2FC, 4))[0]
    files = by_vrom(rom)
    image, reloc, assets = [files[v].extract(rom) for v in (ACTOR, RELOC, ASSETS)]
    if sha256(reloc) != SOURCE_HASHES[RELOC] or struct.unpack_from('>5I', reloc) != (8912, 992, 48, 0, 145):
        raise ValueError('Changed native title relocation')
    expected = relocate_verified_data(Image(RAM, len(image), (8912, 992, 48, 0, 145)), image, reloc, base)
    if read(base, len(expected)) != expected:
        raise ValueError('Live title actor differs from its relocated preview')
    if read(bank, len(assets)) != assets:
        raise ValueError('Live title texture bank differs from the complete preview')
    return {'title_start_memory': 'passed', 'actor': f'{actor:08X}', 'overlay': f'{base:08X}',
            'asset_bank': f'{bank:08X}', 'asset_bytes': len(assets), 'read_only': True,
            'visual_validation': False, 'main_logo_replaced': False}
