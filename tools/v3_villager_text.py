"""Bind imported names/default references to their actual verified donor data."""
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom
from gamecube import Disc, rarc_files
from gc_names import symbol_data
from gc_text import decoder_tables, decode_gc
from textbanks import Bank
from textcodec import LATIN, command_info, encode
from v3_import_catalog import ROOT, SYMBOLS_SHA, DECODER_SHA, REL_SHA, DONOR_FILES
from v3_registry import villager_actor

ABI, BLOB_SIZE, DATA, STRIDE, CODE = 4, 0x8000, 0x2C00, 32, 0x4000
FIRST_SHA = '461d3d0e0293dac2d93ade9cf317487c92dc15a199da8f698b8f99cba1d812c0'
SOURCES = ('tools/v3_villager_text.py', 'tools/v3_registry.py',
           'overlays/v3/villager.c', 'overlays/v3/villager.ld', 'tools/gc_text.py',
           'tools/gc_names.py', 'tools/gamecube.py', 'tools/textcodec.py', 'tools/textbanks.py')
# No PC-relative instructions are copied into these four return bridges.
BRIDGES = (
    (0x80196044, 0x2F00, 'af_v3_load_name', (0x27BDFFA0, 0xAFB30054)),
    (0x80194FDC, 0x2F10, 'af_v3_load_phrase', (0x27BDFF78, 0xAFBF0084)),
    (0x800ACC38, 0x2F20, 'af_v3_short_name', (0x27BDFFD0, 0xAFA50034)),
    (0x800A9EC8, 0x2F30, 'af_v3_reset_phrase', (0x27BDFFC8, 0xAFBF001C)),
)


def read_text_donor(path):
    with Disc(path) as disc:
        if disc.header[:8] != b'GAFE01\0\0':
            raise ValueError('Villager text requires the GAFE01 revision 0 donor')
        entries = [e for e in disc.files() if e['path'] == 'forest_1st.arc']
        if len(entries) != 1 or entries[0]['size'] != 852896:
            raise ValueError('Changed donor default-text archive')
        data = disc.read(entries[0]['offset'], entries[0]['size'])
    if sha256(data) != FIRST_SHA:
        raise ValueError('Changed donor default-text archive hash')
    return data


def metadata(native, donor, first, symbols):
    verified_rom(native)
    if (sha256(donor['rel']) != REL_SHA or sha256(first) != FIRST_SHA
            or sha256(donor['forest_2nd.arc']) != DONOR_FILES['forest_2nd.arc'][1]
            or sha256(symbols) != SYMBOLS_SHA):
        raise ValueError('Unverified donor villager metadata')
    decoder = ROOT / 'local/ac-decomp/tools/msg_tool.py'
    if sha256(decoder.read_bytes()) != DECODER_SHA:
        raise ValueError('Changed donor text decoder')
    tables = decoder_tables(decoder)
    members = dict(rarc_files(first))
    names = dict(rarc_files(donor['forest_2nd.arc']))['data/npc_name_str_table.bin']
    if len(names) != 236 * 8:
        raise ValueError('Changed donor name count')
    strings = Bank('string', 0, 0, members['data/string_data.bin'], members['data/string_data_table.bin']).entries()
    symbols = symbols.decode()
    defaults = symbol_data(donor['rel'], symbols, 'npc_def_list')
    looks = symbol_data(donor['rel'], symbols, 'npc_looks_table')
    growth = symbol_data(donor['rel'], symbols, 'npc_grow_list')
    if (len(defaults), len(looks), len(growth)) != (238 * 6, 238, 238):
        raise ValueError('Changed donor metadata table sizes')
    files = by_vrom(native)
    info = command_info(files[CODE_VROM].extract(native))
    result, rows = bytearray(20 * STRIDE), []
    # Pilot content only; other registry slots stay unavailable.
    for index in (232, 235):
        actor = villager_actor(index)
        raw_name = names[index * 8:(index + 1) * 8]
        default = defaults[index * 6:(index + 1) * 6]
        cloth, phrase_index, umbrella, padding = struct.unpack('>HHBB', default)
        raw_phrase = strings[phrase_index]
        name, phrase = (encode(decode_gc(data, tables).rstrip(' '), info) for data in (raw_name, raw_phrase))
        if (not 1 <= len(name) <= 8 or not 1 <= len(phrase) <= 10
                or any(c not in LATIN for c in name + phrase) or padding
                or looks[index] >= 6 or growth[index] != 0 or umbrella >= 32):
            raise ValueError('Pilot text or ordinary-villager defaults need adaptation')
        key = bytes((0xFE, 0xF3, actor & 255, 0x20))
        record = (struct.pack('>HH4B', actor, cloth, looks[index], umbrella, growth[index], 1)
                  + name.ljust(8, b' ') + phrase.ljust(10, b' ') + key + bytes(2))
        slot = actor - 0xE0DA
        result[slot * STRIDE:(slot + 1) * STRIDE] = record
        rows.append({'id': f'GAFE01-r0/villager/{index:04X}', 'actor_id': f'{actor:04X}',
            'name': decode_gc(raw_name, tables).rstrip(' '), 'catchphrase': decode_gc(raw_phrase, tables),
            'saved_default_key': key.hex(), 'donor_name_sha256': sha256(raw_name),
            'donor_phrase_sha256': sha256(raw_phrase), 'donor_default_sha256': sha256(default),
            'donor_clothing_id': f'{cloth:04X}', 'donor_umbrella': umbrella, 'personality': looks[index],
            'record_sha256': sha256(record), 'clothing_applied': False, 'move_in_enabled': False})
    return bytes(result), rows


def jump(address): return 0x08000000 | (address >> 2 & 0x3FFFFFF)


def install(native, code, module, blob, symbols, donor, first, donor_symbols):
    from v3_asset_loader import MODULE_RAM
    records, rows = metadata(native, donor, first, donor_symbols)
    if len(blob) != BLOB_SIZE or any(blob[DATA:0x2F40]):
        raise ValueError('Villager metadata/return-bridge reservation is occupied')
    # Keys must not collide with any original/default translated lookup key.
    # FE cannot be entered through the English keyboard, and no key contains a
    # control prefix (7F) or two-byte glyph prefix (80).
    original_phrases = by_vrom(native)
    from textbanks import banks
    strings = next(b for b in banks(native) if b.name == 'string').entries()
    defaults = original_phrases[0xE03000].extract(native)
    existing = {strings[struct.unpack_from('>H', defaults, i * 6 + 2)[0]].ljust(4, b' ') for i in range(216)}
    for row in rows:
        if bytes.fromhex(row['saved_default_key']) in existing:
            raise ValueError('V3 default key collides with an original saved key')
    blob[DATA:DATA + len(records)] = records
    patches = []
    for address, bridge, helper, expected in BRIDGES:
        owner, base = (module, MODULE_RAM) if address >= MODULE_RAM else (code, CODE_RAM)
        at = address - base
        if struct.unpack_from('>II', owner, at) != expected:
            raise ValueError(f'Changed native text entry {address:08X}')
        struct.pack_into('>4I', blob, bridge, *expected, jump(address + 8), 0)
        struct.pack_into('>II', owner, at, jump(symbols[helper]), 0)
        patches.append({'entry': f'{address:08X}', 'helper': helper, 'bridge_ram': f'{0x80460000 + bridge:08X}'})
    at = 0x80195D20 - MODULE_RAM
    if struct.unpack_from('>II', module, at) != (0x10800040, 0):
        raise ValueError('Changed original actor-name null guard')
    struct.pack_into('>II', module, at, jump(symbols['af_v3_actor_name']), 0)
    patches.append({'entry': '80195D20', 'helper': 'af_v3_actor_name', 'original_nonnull_entry': '80195D28'})
    return {'imports': rows, 'hooks': patches, 'metadata_ram': f'{0x80460000 + DATA:08X}',
            'record_stride': STRIDE, 'donor_first_archive_sha256': FIRST_SHA,
            'default_reference_format': 'FEF3ii20; ii is registry-version-1 N64 identity',
            'requires_v3_for_imported_saved_references': True, 'native_test': 'pending',
            'remaining': ['initial defaults/clothes/umbrella', 'house data', 'all ID-bounded readers',
                          'roster and move-ins', 'saved identity and profile handling']}
