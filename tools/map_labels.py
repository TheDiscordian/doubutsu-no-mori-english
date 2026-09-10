"""Exact English landmark labels layered over the complete map-name image."""
import struct

from aflib import sha256
from gc_names import symbol_data
import map_names as m

ROOT, RAM = m.ROOT, m.RAM
BASE_SIZE = m.APPROVED['bytes']
DRAW, OLD_POST_DRAW, EMPTY = 0x8088F1E8, 0x8088F25C, 0x8088FE84
KINDS = ('shop', 'police', 'post', 'shrine', 'station', 'junk')
WORDS = ((b'Shop', b''), (b'Police', b'Station'), (b'Post', b'Office'),
         (b'Wishing', b'Well'), (b'Train', b'Station'), (b'Dump', b''))
NATIVE = ((0x8088FF00, '041f0d'), (0x8088FF04, '0902f6c3'),
          (0x8088FF08, '5e02f7c3'), (0x8088FF10, '045d0bc0'),
          (0x8088FF14, '0306'), (0x8088FF18, 'eb1f0c12f6'))
APPROVED = {
    'bytes': 27072,
    'symbols': {**m.APPROVED['symbols'], 'af_map_label_draw': 26544, 'af_map_labels': 26960},
    'suffix_sha256': '279b22d79c45f94e76ddcd97c169a419e7449a4e00fd17bfee4256f6fa075eca',
    'relocation_sha256': '72b43cb3b62b7eba86a1782913fddb7427188fe5fe44bb13530aa2e8c18ae134',
    'elf_relocations': [[26708, 4, 0x80090E98, 'af_map_native_draw'],
                        [26820, 5, RAM+BASE_SIZE, '.text'], [26824, 6, RAM+BASE_SIZE, '.text'],
                        [26940, 4, 0x80090E98, 'af_map_native_draw']],
}


def source_hashes():
    return {**m.source_hashes(), **{p: sha256((ROOT/p).read_bytes()) for p in
            ('overlays/map/labels.c', 'overlays/map/labels.ld')}}


def reference():
    rel = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
    symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_text()
    if (sha256(rel) != '29306a927eee861b073c571408393f99cb384048684eee4bff3d219725429837'
            or sha256(symbols.encode()) != 'e5267b989d235655c51885bd2a660b3e8c2cbd46d60b2b3c46166d337c7bca87'):
        raise ValueError('Changed supplied map-label reference')
    result = {}
    for kind, words in zip(KINDS, WORDS):
        for i, word in enumerate(words):
            if not word: continue
            suffix = kind+('2' if i else '')
            raw = symbol_data(rel, symbols, 'mMP_label_str_'+suffix)
            layout = symbol_data(rel, symbols, 'mMP_label_word_'+suffix)
            y = -25.0 if not words[1] else (-31.0 if i else -19.0)
            if (raw != word or len(layout) != 16 or struct.unpack_from('>2f', layout) != (-83.0, y)
                    or struct.unpack_from('>I', layout, 12)[0] != len(word)):
                raise ValueError('Changed GameCube map wording or line layout')
            result[suffix] = {'text_sha256': sha256(raw), 'layout_sha256': sha256(layout)}
    vacant = symbol_data(rel, symbols, 'akiya_str$483')
    if vacant != b'free    ': raise ValueError('Changed GameCube vacant-house label')
    result['vacant'] = {'text_sha256': sha256(vacant)}
    return result


def label_data():
    return b''.join(first.ljust(8, b'\0')+second.ljust(8, b'\0') for first, second in WORDS)


def patch_prefix(native, symbols):
    original = m.native_sources(native)[0]
    data = bytearray(m.patch_prefix(native, m.APPROVED['symbols']))
    slots = dict(m.original_relocations(m.native_sources(native)[1]))
    for at in (DRAW, OLD_POST_DRAW):
        if struct.unpack_from('>I', original, at-RAM)[0] != 0x0C0243A6 or at-RAM in slots:
            raise ValueError('Changed native map label call')
    struct.pack_into('>I', data, DRAW-RAM, 0x0C000000 | ((RAM+symbols['af_map_label_draw']) >> 2) & 0x3FFFFFF)
    struct.pack_into('>I', data, OLD_POST_DRAW-RAM, 0)
    for index, ((pointer, raw_hex), words) in enumerate(zip(NATIVE, WORDS), 2):
        raw = bytes.fromhex(raw_hex); at = 0x8088FF20+index*28-RAM
        if (original[pointer-RAM:pointer-RAM+len(raw)] != raw
                or struct.unpack_from('>2I', original, at+20) != (pointer, len(raw))
                or slots.get(at+20) != 2
                or struct.unpack_from('>2f', original, at+8) != (-83.0, -19.0 if index == 4 else -25.0)):
            raise ValueError('Changed map landmark descriptor or text')
        struct.pack_into('>f', data, at+12, -19.0 if words[1] else -25.0)
        struct.pack_into('>2I', data, at+20, RAM+symbols['af_map_labels']+(index-2)*16, len(words[0]))
    if original[EMPTY-RAM:EMPTY-RAM+6] != bytes.fromhex('00065d202020'):
        raise ValueError('Changed native vacant-house label')
    data[EMPTY-RAM:EMPTY-RAM+6] = b'free  '
    return bytes(data)


def relocation_data(native, inventory, size):
    old = m.relocation_data(native, m.APPROVED['elf_relocations'], BASE_SIZE)
    count = struct.unpack_from('>I', old, 16)[0]
    rows = list(struct.unpack_from('>'+str(count)+'I', old, 20))
    rows.append(0x44000000 | (DRAW-RAM))
    seen = set()
    for at, kind, target, name in inventory:
        if at in seen or at & 3 or not BASE_SIZE <= at <= size-4:
            raise ValueError('Unapproved landmark helper relocation')
        seen.add(at)
        if RAM+BASE_SIZE <= target < RAM+size and kind in (2, 4, 5, 6):
            rows.append(0x40000000 | kind << 24 | at)
        elif kind != 4 or target != 0x80090E98 or name != 'af_map_native_draw':
            raise ValueError('Unbound map landmark import')
    count = len(rows); length = (24+count*4+15) & ~15
    return (struct.pack('>5I', size, 0, 0, 0, count)+struct.pack('>'+str(count)+'I', *rows)
            +bytes(length-24-count*4)+struct.pack('>I', length))


def installed_report(data):
    if not APPROVED: raise ValueError('Map labels require independent image approval')
    from shrine_labels import LABEL_AT, transform, profile
    if data[LABEL_AT:LABEL_AT+16] == b'Shrine\0\0'+bytes(8):
        return profile(installed_report(transform(data, reverse=True)), data)
    return {**APPROVED, 'labels': True, 'sources': source_hashes(), 'imports': m.IMPORTS,
            'overlay_sha256': sha256(data), 'references': reference()}


def validate(native, data, reloc, report, module):
    if report.get('native_shrine'):
        from shrine_labels import validate as validate_shrine
        return validate_shrine(native, data, reloc, report, module)
    if not APPROVED: raise ValueError('Map labels require independent image approval')
    if (not report.get('labels') or report.get('bytes') != len(data) or len(data) != APPROVED['bytes']
            or report.get('symbols') != APPROVED['symbols'] or report.get('sources') != source_hashes()
            or report.get('imports') != m.IMPORTS or report.get('references') != reference()
            or report.get('overlay_sha256') != sha256(data) or report.get('relocation_sha256') != sha256(reloc)
            or report.get('elf_relocations') != APPROVED['elf_relocations']
            or data[:m.PREFIX] != patch_prefix(native, APPROVED['symbols'])
            or any(data[m.PREFIX:m.START])
            or sha256(data[m.START:BASE_SIZE]) != m.APPROVED['suffix_sha256']
            or sha256(data[BASE_SIZE:]) != APPROVED['suffix_sha256']
            or data[APPROVED['symbols']['af_map_labels']:APPROVED['symbols']['af_map_labels']+96] != label_data()
            or reloc != relocation_data(native, report.get('elf_relocations', []), len(data))
            or sha256(reloc) != APPROVED['relocation_sha256']
            or int(module['symbols']['af_load_display_name'], 16) != m.IMPORTS['af_load_display_name']):
        raise ValueError('Changed installed English map labels or retained name cache')
    return m.Image(RAM, len(data), struct.unpack_from('>5I', reloc))


def native_labels(native):
    data = m.native_sources(native)[0]
    rows = [(kind, data[at-RAM:at-RAM+len(bytes.fromhex(raw))]) for kind, (at, raw) in zip(KINDS, NATIVE)]
    rows += [('post_continuation', data[0x8088FF0C-RAM:0x8088FF0F-RAM]),
             ('vacant', data[EMPTY-RAM:EMPTY-RAM+6])]
    return rows


def measure_labels(ledger, native, built, report):
    applied = report.get('map_names', {}).get('overlay', {}).get('labels', False)
    if applied: m.verify_shared_parts(built, native, report['runtime_module'], report['map_names'])
    english = {kind: b' '.join(w for w in words if w) for kind, words in zip(KINDS, WORDS)}
    if report.get('map_names', {}).get('overlay', {}).get('native_shrine'):
        english['shrine'] = b'Shrine'
    english.update(post=b'Post', post_continuation=b'Office', vacant=b'free  ')
    for kind, raw in native_labels(native):
        identity = 'ui_map:'+kind
        ledger.add(identity, raw)
        if applied: ledger.credit(identity, english[kind], 'map_labels')
