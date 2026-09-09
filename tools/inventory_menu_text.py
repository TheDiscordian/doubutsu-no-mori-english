"""Complete category/present/question text appended to the validated tag image."""
import struct

from aflib import sha256
from gc_names import symbol_data
import inventory_english as inv

BASE_SIZE = inv.APPROVED['bytes']
SIZE = 42976
CODE_AT = BASE_SIZE
CATEGORY_AT = BASE_SIZE+32
PRESENT_AT, THROW_AT, SURE_AT, REALLY_AT = CATEGORY_AT+92, CATEGORY_AT+100, CATEGORY_AT+116, CATEGORY_AT+124
CONFIRM = (b'Are you', b'really sure?')
SOURCES = [(f'category:{i}', 0x80879148+i*6, 6, CATEGORY_AT+i*10, 10) for i in range(9)]+[
    ('present', 0x8087913C, 5, PRESENT_AT, 7),
    ('throw', 0x80879068, 5, THROW_AT, 13),
    ('sure', 0x80879070, 4, SURE_AT, 7),
    ('really', 0x80879074, 6, REALLY_AT, 12)]
POINTERS = [
    (0x808701D0, 0x808701D4, 0x8087913C, PRESENT_AT),
    (0x8087028C, 0x80870290, 0x80879148, CATEGORY_AT),
    (0x808780DC, 0x80878104, 0x80879070, SURE_AT),
    (0x80878130, 0x80878168, 0x80879074, REALLY_AT),
    (0x808781A8, 0x808781D0, 0x80879068, THROW_AT)]
WORDS = {0x808701E0: (0x24060005, 0x24060007),
         0x80870288: (0x01EE7823, 0x01EE7821),
         0x808702A0: (0x24060006, 0x2406000A),
         0x80878108: (0x24060004, 0x24060007),
         0x80878170: (0x24060006, 0x2406000C),
         0x808781D4: (0x24060005, 0x2406000D),
         0x8086FB78: (0x10000003, 0x08000000 | ((inv.RAM+CODE_AT) >> 2) & 0x3FFFFFF),
         0x808702AC: (0x0C027070, 0x0C000000 | ((inv.RAM+inv.APPROVED['symbols']['af_tag_cells']) >> 2) & 0x3FFFFFF)}
REFERENCE_HASHES = {
    'mTG_catalog_str': 'e2d3eade129993e6b7f5004b244f53fb9b29a091b35c1a623be500b4ce66680b',
    'present_str$820': '43f9b89c0b9d22d8110ead813ea3949f20592a8bfc3c777d2d49e64da3b0cc9b',
    'mTG_tag_str_suteruno': 'ad5d3a36a426a5fffd509f7395675c464831497977d89939c545376ccb8ce1d8',
    'mTG_tag_str_hontoni': '2c0b4ee2a03c434e1856404d03d57b82c8ef500237be8ae118b1147a1051d5b6',
    'mTG_tag_str_iidesuka': '2c0b4ee2a03c434e1856404d03d57b82c8ef500237be8ae118b1147a1051d5b6'}


def source_hashes():
    path = 'overlays/tag/menu_text.s'
    return {path: sha256((inv.ROOT/path).read_bytes())}


def reference_texts():
    inv.reference_labels()  # Pins the complete supplied executable and symbols.
    rel = (inv.ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
    symbols = (inv.ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_text()
    values = {name: symbol_data(rel, symbols, name) for name in REFERENCE_HASHES}
    if any(sha256(value) != REFERENCE_HASHES[name] for name, value in values.items()):
        raise ValueError('Changed complete embedded menu reference')
    if values['mTG_tag_str_hontoni'] != b'??????' or values['mTG_tag_str_iidesuka'] != b'??????':
        raise ValueError('Confirmation reference is no longer the reviewed placeholder')
    categories = values['mTG_catalog_str']
    result = [categories[i*10:i*10+10] for i in range(9)]+[
        values['present_str$820'], values['mTG_tag_str_suteruno'], *CONFIRM]
    if any(len(v) != entry[4] or any(c not in range(32, 127) for c in v) for entry, v in zip(SOURCES, result)):
        raise ValueError('Incomplete or non-Latin embedded menu text')
    return result


def cells(native, text):
    from font import make_halfwidth
    advances = make_halfwidth(native)[1]['advance_by_glyph']
    return (sum(advances[f'{c:02X}'] for c in text.rstrip(b' '))+11)//12


def helper(native):
    width = cells(native, reference_texts()[10])
    if width != 7 or any(cells(native, text) > 6 for text in CONFIRM):
        raise ValueError('Changed embedded question width contract')
    return struct.pack('>8I', 0x8C880000, 0x29010000 | width, 0x10200003, 0,
                       0x24080000 | width, 0xAC880000,
                       0x08000000 | (0x8086FB88 >> 2) & 0x3FFFFFF, 0)


def patched_words(native):
    original, reloc, _, _ = inv.native_sources(native)
    slots = dict(inv.original_relocations(reloc)); result = dict(WORDS)
    for hi, lo, before, target in POINTERS:
        h, l = (struct.unpack_from('>I', original, at-inv.RAM)[0] for at in (hi, lo))
        value = ((h & 65535) << 16)+(l & 65535)-(65536 if l & 32768 else 0)
        if (h >> 26 != 15 or l >> 26 != 9 or (h >> 16) & 31 != (l >> 21) & 31
                or value != before or slots.get(hi-inv.RAM) != 5 or slots.get(lo-inv.RAM) != 6):
            raise ValueError('Changed native menu text pointer pair')
        address = inv.RAM+target
        result[hi] = (h, (h & 0xFFFF0000) | ((address+32768) >> 16) & 65535)
        result[lo] = (l, (l & 0xFFFF0000) | address & 65535)
    if slots.get(0x8086FB78-inv.RAM) is not None or slots.get(0x808702AC-inv.RAM) is not None:
        raise ValueError('Unexpected original menu hook relocation')
    if set(result) & (set(inv.HOOKS) | set(inv.WORDS)):
        raise ValueError('Menu text overlaps a base inventory instruction')
    return result


def change_prefix(native, data, reverse=False):
    result = bytearray(data)
    for at, (before, after) in patched_words(native).items():
        if reverse: before, after = after, before
        if struct.unpack_from('>I', result, at-inv.RAM)[0] != before:
            raise ValueError('Changed installed menu text instruction')
        struct.pack_into('>I', result, at-inv.RAM, after)
    return bytes(result)


def relocation_data(native):
    old = inv.relocation_data(native, inv.APPROVED['symbols'], BASE_SIZE)
    count = struct.unpack_from('>I', old, 16)[0]
    rows = list(struct.unpack_from('>'+str(count)+'I', old, 20))
    rows += [0x44000000 | at for at in (0x8086FB78-inv.RAM, 0x808702AC-inv.RAM, CODE_AT+24)]
    if len({r & 0xFFFFFF for r in rows}) != len(rows): raise ValueError('Duplicate menu text relocation')
    length = (24+len(rows)*4+15) & ~15
    return (struct.pack('>5I', SIZE, 0, 0, 0, len(rows))+struct.pack('>'+str(len(rows))+'I', *rows)
            +bytes(length-24-len(rows)*4)+struct.pack('>I', length))


def base_report(native, base):
    return {**inv.APPROVED, 'sources': inv.source_hashes(), 'overlay_sha256': sha256(base),
            'relocation_sha256': sha256(inv.relocation_data(native, inv.APPROVED['symbols'], BASE_SIZE))}


def build_image(native, base):
    output = bytearray(change_prefix(native, base)+bytes(SIZE-BASE_SIZE))
    output[CODE_AT:CODE_AT+32] = helper(native)
    for entry, value in zip(SOURCES, reference_texts()):
        output[entry[3]:entry[3]+entry[4]] = value
    return bytes(output)


def make_report(native, data, reloc):
    base = change_prefix(native, data[:BASE_SIZE], reverse=True)
    return {**inv.APPROVED, 'bytes': SIZE, 'menu_text': True, 'sources': source_hashes(),
            'base_overlay': base_report(native, base), 'overlay_sha256': sha256(data),
            'relocation_sha256': sha256(reloc), 'reference_sha256': REFERENCE_HASHES,
            'menu_text_records': len(SOURCES), 'width_cells': {'throw': 7, 'confirmation': 6}}


def validate(native, data, reloc, report, module):
    if (len(data) != SIZE or report.get('menu_text') is not True or report.get('bytes') != SIZE
            or report.get('symbols') != inv.APPROVED['symbols'] or report.get('loader') != inv.APPROVED['loader']
            or report.get('sources') != source_hashes() or report.get('reference_sha256') != REFERENCE_HASHES
            or report.get('menu_text_records') != len(SOURCES)
            or report.get('width_cells') != {'throw': 7, 'confirmation': 6}
            or report.get('overlay_sha256') != sha256(data) or report.get('relocation_sha256') != sha256(reloc)
            or reloc != relocation_data(native)):
        raise ValueError('Changed complete embedded-menu profile')
    base = change_prefix(native, data[:BASE_SIZE], reverse=True)
    if report.get('base_overlay', {}).get('menu_text'):
        raise ValueError('Recursive embedded-menu base')
    inv.validate(native, base, inv.relocation_data(native, inv.APPROVED['symbols'], BASE_SIZE),
                 report['base_overlay'], module)
    if data != build_image(native, base): raise ValueError('Changed embedded menu text, clamp, or padding')
    return inv.Image(inv.RAM, SIZE, struct.unpack_from('>5I', reloc))
