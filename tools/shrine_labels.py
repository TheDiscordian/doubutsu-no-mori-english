"""Native shrine wording over the exact GC-derived map-label image."""
import copy
import struct

from aflib import sha256

LABEL_AT = 26960+3*16
DESCRIPTOR = 0x8088FF20+5*28-0x8088DBD0
EDITS = ((LABEL_AT, b'Wishing\0Well\0\0\0\0', b'Shrine\0\0'+bytes(8)),
         (DESCRIPTOR+12, struct.pack('>f', -19.0), struct.pack('>f', -25.0)),
         (DESCRIPTOR+24, struct.pack('>I', 7), struct.pack('>I', 6)))


def transform(data, *, reverse=False):
    if len(data) != 27072:
        raise ValueError('Native shrine requires the complete bounded map-label image')
    result = bytearray(data)
    for at, old, new in EDITS:
        before, after = (new, old) if reverse else (old, new)
        if len(before) != len(after) or result[at:at+len(before)] != before:
            raise ValueError('Changed shrine label, line placement, or descriptor length')
        result[at:at+len(after)] = after
    return bytes(result)


def profile(previous, data):
    if previous.get('native_shrine') or sha256(transform(data, reverse=True)) != previous.get('overlay_sha256'):
        raise ValueError('Native shrine requires its exact GC-label predecessor')
    result = copy.deepcopy(previous)
    result.update(native_shrine=True, previous_map_labels=copy.deepcopy(previous),
                  overlay_sha256=sha256(data),
                  native_label_correction={'location': 'shrine', 'text': 'Shrine', 'lines': 1,
                                           'reason': 'The N64 location is a shrine, not the GameCube wishing well'})
    return result


def validate(native, data, reloc, report, module):
    from map_labels import validate as validate_original
    if report.get('native_shrine') is not True:
        raise ValueError('Missing native shrine variant')
    previous = report.get('previous_map_labels', {})
    if previous.get('native_shrine'):
        raise ValueError('Nested shrine variants are not supported')
    original = transform(data, reverse=True)
    result = validate_original(native, original, reloc, previous, module)
    if report != profile(previous, data):
        raise ValueError('Changed native shrine output profile')
    return result


def patch(native, data, reloc, previous, module):
    from map_labels import validate as validate_original
    validate_original(native, data, reloc, previous, module)
    changed = transform(data)
    report = profile(previous, changed)
    validate(native, changed, reloc, report, module)
    return changed, report
