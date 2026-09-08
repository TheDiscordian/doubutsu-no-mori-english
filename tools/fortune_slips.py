"""Source-bound complete fortune-slip phrases and immutable letter references."""

from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from fortune_strings import source_entries
from gc_names import symbol_data
from mail_catalog import parse, resource, verify_registered
from mail_reference import BANK_HASHES
from textbanks import Bank, banks as native_banks
from textcodec import encode

ROOT = Path(__file__).resolve().parents[1]
VROM, RAM, RELOCATION = 0x8C8F10, 0x809E5740, 0x8C9AC0
ACTOR_HASH = '29bb1d033017871b77d40d246c7fe892e4fe61ba4f2fb067a43757a782ac8a1b'
RELOCATION_HASH = '66afae771d50c718d584d4590aad187191f492d33d1eb735adfa7a1d7f7c2ee5'
METADATA = 0x80101D10
METADATA_BYTES = bytes.fromhex('008C8F10008C9AC0809E5740809E630000000000809E62600000000000000000')
BASES = (0x2B1, 0x2A1, 0x2DA, 0x2CA)
IDS = tuple(f'string:{base+i:04X}' for base in BASES for i in range(16)) + tuple(
    f'string:{i:04X}' for i in range(0x2C1, 0x2C5))
TEMPLATES = (0x72, 0x73, 0x74)
WORDS_HASH = '23163c7dacc3e3aef3924267447f02a58824e0a778352e6aa508ae17e0530231'
CATALOG = 3
CATALOG_VROM = 0x03050000
CATALOG_HASH = 'c75cc7d6c672e1f708a827cddb426895c3b15b7d3fc3c9337b6928174c71f254'
FOOTER_HASH = '85137eeab173aad6334b937568ac6c57a342325ef0c157c7827203b11d2c9ae6'
GC_FUNCTIONS = {
    'aEMK_get_omikuji': (336, '0bb777d02669bd81f5300833ee6896913c8b8722f0daf894f819c7928876d01c'),
    'aEMK_talk_omikuji': (184, '1887532a28f6dbeef2a3cb10c54f138c83ec4af9732149178b2d22d2257e6ae4'),
    'aEMK_talk_give': (268, '97ecca68dcb44dc3d773a3cb8b4b2a1990e79105e97384097b98e91a80103fe0'),
    'aEMK_talk_omikuji_init': (72, '214eb84a82966a9a4fb8f92ec05bc48f51df32c4996184bd46ebf9d9169dab32'),
}


def verify_native(rom):
    files = by_vrom(rom)
    actor, reloc = files[VROM].extract(rom), files[RELOCATION].extract(rom)
    code = files[CODE_VROM].extract(rom)
    if (sha256(actor) != ACTOR_HASH or sha256(reloc) != RELOCATION_HASH
            or struct.unpack_from('>5I', reloc) != (2848,144,0,16,51)
            or code[METADATA-CODE_RAM:METADATA-CODE_RAM+32] != METADATA_BYTES
            or struct.unpack_from('>4I',actor,0x809E62B8-RAM) != BASES
            or actor[0x809E62C8-RAM:0x809E62CC-RAM] != bytes((0,3,4,5))):
        raise ValueError('Changed native fortune-slip selection, effect, or ownership')


def verify_reference():
    rel = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
    symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_text()
    if sha256(rel) != '29306a927eee861b073c571408393f99cb384048684eee4bff3d219725429837':
        raise ValueError('Changed supplied English fortune-slip executable')
    for name, expected in GC_FUNCTIONS.items():
        data = symbol_data(rel,symbols,name)
        if (len(data),sha256(data)) != expected:
            raise ValueError('Changed English fortune-slip creator or outcome selection')


def words(rom, references, inventory, info):
    """All four complete sixteen-entry pools, then four native-order outcomes.

    The GC actor permutes its outcome indices. Native code does not; do not copy
    that permutation or change native luck effects when translating its labels.
    """
    verify_native(rom); verify_reference()
    native = source_entries(rom)
    values = []
    for id in IDS:
        row, ref = inventory.get(id), references.get(id)
        if not row or not ref or row['id'] != id or ref['id'] != id:
            raise ValueError('Missing fortune-slip native or English reference')
        value = encode(ref['text'],info)
        if (row['source_sha256'] != sha256(native[int(id[7:],16)])
                or ref['sha256'] != sha256(value) or encode(row['legacy'],info) != value
                or not 1 <= len(value) <= 16 or any(not 32 <= c < 127 for c in value)):
            raise ValueError('Changed complete fortune-slip phrase identity or capacity')
        values.append(value.ljust(16,b' '))
    result = b''.join(values)
    if sha256(result) != WORDS_HASH:
        raise ValueError('Changed complete native-order fortune-slip phrase group')
    return result


def catalog_three(rom, original, inventory, info, directory=None):
    """Add three complete signatures without changing frozen catalog two.

    GC code 2A is labelled ASCII tilde; the native decoder labels the same
    decoration fullwidth tilde. Use the existing native wave glyph explicitly,
    as the legacy translation does. No word, space, newline, or font pixel changes.
    The two glyphs are not claimed to have identical artwork or metrics.
    """
    verify_native(rom); verify_reference()
    if verify_registered(original)['catalog'] != 2:
        raise ValueError('Fortune-slip catalog requires unchanged catalog two')
    _, banks = parse(original)
    originals = {b.name: b.entries() for b in native_banks(rom) if b.name in ('super','mail','ps')}
    directory = directory or ROOT/'build/gamecube/files/forest_1st.arc.unpacked/data'
    for name in ('super','mail','ps'):
        data = (directory/(name+'_data.bin')).read_bytes()
        table = (directory/(name+'_data_table.bin')).read_bytes()
        if (sha256(data),sha256(table)) != BANK_HASHES[name]:
            raise ValueError('Changed complete supplied fortune-slip reference bank')
        entries = Bank(name,0,0,data,table).entries()
        for number in TEMPLATES:
            id = f'{name}:{number:04X}'
            row = inventory.get(id)
            native = originals[name][number]
            if not row or row['id'] != id or row['source_sha256'] != sha256(native):
                raise ValueError('Stale native fortune-slip template identity')
            value = encode(row['legacy'],info)
            if name == 'ps':
                if banks[name][number] is not None or sha256(entries[number]) != FOOTER_HASH or value != entries[number]:
                    raise ValueError('Changed complete Katrina signature or wave mapping')
                banks[name][number] = value
            elif value != banks[name][number] or value != entries[number]:
                raise ValueError('Fortune-slip English header/body differs from complete legacy reference')
    result = resource(banks,CATALOG)
    if sha256(result) != CATALOG_HASH:
        raise ValueError('Changed complete fortune-slip catalog identity')
    verify_registered(result)
    return result
