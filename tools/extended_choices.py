"""Two complete reference labels, separate from the original 460-slot catalog."""

import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from textbanks import Bank
from textcodec import encode

COUNT = 460
DATA_VROM, TABLE_VROM = 0x00D05000, 0x00D06000
LIMITS = {0x80065544: 0x2A0101CC, 0x80065DAC: 0x288101CC}
LABELS = (
    ('select:01CC', 'select:025C', 'Less', 'ae5239ec63f28cd401ccd63e9f56e4ede8254a738a135ebcd33e844c18dd247f'),
    ('select:01CD', 'select:025B', 'More', 'd47d7cb0e4f8fd2be5ee07826694c18917d83ca77d0a01698582d05f432db996'),
)


def bindings():
    return {id: {'id': id, 'source_kind': 'appended_gamecube', 'reference_id': reference,
                 'source_sha256': digest, 'encoded_sha256': digest}
            for id, reference, text, digest in LABELS}


def payloads():
    result = {id: text.encode('ascii') for id, reference, text, digest in LABELS}
    if any(sha256(result[id]) != digest for id, reference, text, digest in LABELS):
        raise ValueError('Extended choice constants differ from the complete reference labels')
    return result


def verify_reference_labels(references, info):
    """Generation must establish the exact supplied reference, not infer a label."""
    result = payloads()
    for id, reference, text, digest in LABELS:
        row = references.get(reference)
        if (not row or row.get('id') != reference or row.get('sha256') != digest
                or encode(row['text'], info) != result[id]):
            raise ValueError('Missing or stale complete extended-choice reference')
    return result


def validate_binding(label):
    if (not isinstance(label, dict) or not isinstance(label.get('id'), str)
            or label != bindings().get(label['id'])):
        raise ValueError('Unknown or changed extended-choice reference binding')


def append_labels(data, table):
    entries = Bank('select', DATA_VROM, TABLE_VROM, data, table).entries()
    if len(entries) != COUNT or table[COUNT*4:COUNT*4+12] != bytes(12):
        raise ValueError('Extended choices require the native count and three unused table words')
    end = sum(map(len, entries))
    if any(data[end:]):
        raise ValueError('Unexpected nonzero choice-bank tail')
    extra = list(payloads().values())
    output = data[:end]+b''.join(extra)
    output += bytes(-len(output) % 16)
    new_table = bytearray(table)
    for index, raw in enumerate(extra, COUNT):
        end += len(raw)
        struct.pack_into('>I', new_table, index*4, end)
    if Bank('select', DATA_VROM, TABLE_VROM, output, bytes(new_table)).entries() != entries+extra:
        raise ValueError('Choice extension changed an existing label')
    return output, bytes(new_table)


def install(rom, replacements):
    """Called only after independent validation of a registered display menu."""
    files = by_vrom(rom)
    original = files[CODE_VROM].extract(rom)
    code = bytearray(replacements.get(CODE_VROM, original))
    for address, word in LIMITS.items():
        off = address-CODE_RAM
        if (struct.unpack_from('>I', original, off)[0] != word
                or struct.unpack_from('>I', code, off)[0] != word):
            raise ValueError('Unexpected or overlapping native choice-count limit')
        struct.pack_into('>I', code, off, (word & 0xFFFF0000) | (COUNT+len(LABELS)))
    append_labels(files[DATA_VROM].extract(rom), files[TABLE_VROM].extract(rom))
    data, table = append_labels(replacements.get(DATA_VROM, files[DATA_VROM].extract(rom)),
                                replacements.get(TABLE_VROM, files[TABLE_VROM].extract(rom)))
    replacements.update({CODE_VROM: bytes(code), DATA_VROM: data, TABLE_VROM: table})
