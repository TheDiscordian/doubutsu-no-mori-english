"""Encode the grid's two ASCII control-hint resources for the native font."""
from aflib import sha256

ORIGINAL_SHA = 'aa6807c5ebe327c295da87c62b23d4758adf56f6a4262f53d2477c7e31c1277f'
CORRECTED_SHA = '0844b5da4ce74e41045f9dcfb5d115314a86da8196e97036af41d64506ae42ac'
LABELS = ((0x6F00, b'L: Case   Z: Page   L+Z: ABC'),
          (0x6F4C, b'Move: Stick/D-pad   Cursor: C   L+A: Alter'))


def encode_label(value):
    # Native 2B is a heart and 2F is a music note. The actual plus glyph is 5C;
    # no native slash exists, so separate the two movement devices with a space.
    return value.replace(b'+', b'\\').replace(b'/', b' ')


def install(data):
    if sha256(data) != ORIGINAL_SHA:
        raise ValueError('Control labels require the exact compiled grid')
    result = bytearray(data)
    for at, label in LABELS:
        if data[at:at+len(label)+1] != label+b'\0':
            raise ValueError('Grid control label binding changed')
        result[at:at+len(label)] = encode_label(label)
    result = bytes(result)
    if sha256(result) != CORRECTED_SHA:
        raise ValueError('Unexpected encoded grid labels')
    return result


def compiled_form(data):
    """Retain strict compiled-code verification for the reviewed data-only fix."""
    if sha256(data) != CORRECTED_SHA:
        return data
    result = bytearray(data)
    for at, label in LABELS:
        if data[at:at+len(label)+1] != encode_label(label)+b'\0':
            raise ValueError('Changed native-encoded grid labels')
        result[at:at+len(label)] = label
    result = bytes(result)
    if sha256(result) != ORIGINAL_SHA:
        raise ValueError('Label correction changes compiled grid code')
    return result
