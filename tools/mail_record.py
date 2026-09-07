"""Lossless generated-letter snapshot prototype; not installed in native saves.

The 122-byte envelope is exactly the contiguous native header/body/footer space.
Template identity and literal substitutions are persistent; no random choices or
current world names are consulted when decoding an existing snapshot.
"""

from dataclasses import dataclass
import binascii

RECORD_BYTES = 122
VERSION = 1
MAGIC = 0xAF
FIELD_COUNT = 20
FIELD_BYTES = 16
PARTS = {0: 1, 1: 5}


@dataclass(frozen=True)
class Field:
    text: bytes
    article: int = 0


@dataclass(frozen=True)
class Record:
    catalog: int
    kind: int
    templates: tuple[int, ...]
    fields: tuple[tuple[int, Field], ...]


def integer(value, lo, hi, description):
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"Invalid mail {description}")


def snapshot_size(kind, widths):
    """Exact encoded bytes for a set of snapshot lengths, not rendered text."""
    integer(kind, 0, 1, "template kind")
    widths = tuple(widths)
    if len(widths) > FIELD_COUNT:
        raise ValueError("Too many mail snapshot fields")
    for width in widths:
        integer(width, 0, FIELD_BYTES, "field length")
    return 10 + 2*PARTS[kind] + sum(1+width for width in widths)


def pack(record):
    """Return a canonical fixed-size envelope, or reject without truncating."""
    if not isinstance(record, Record):
        raise ValueError("Expected a mail snapshot record")
    integer(record.catalog, 1, 0xFFFF, "catalog identity")
    integer(record.kind, 0, 1, "template kind")
    if len(record.templates) != PARTS[record.kind]:
        raise ValueError("Wrong mail template count")
    for template in record.templates:
        integer(template, 0, 0xFFFF, "template identity")
    mask, last, payload = 0, -1, bytearray()
    for index, field in record.fields:
        integer(index, 0, FIELD_COUNT-1, "field index")
        if index <= last:
            raise ValueError("Mail fields must be unique and sorted")
        if not isinstance(field, Field) or type(field.text) is not bytes:
            raise ValueError("Mail snapshots require literal bytes")
        integer(len(field.text), 0, FIELD_BYTES, "field length")
        integer(field.article, 0, 4, "article")
        mask |= 1 << index
        last = index
        payload.append((field.article << 5) | len(field.text))
        payload.extend(field.text)
    size = snapshot_size(record.kind, (len(field.text) for _, field in record.fields))
    if size > RECORD_BYTES:
        raise ValueError("Mail snapshot exceeds native text storage")
    data = bytearray((MAGIC, (VERSION << 4) | record.kind, size))
    data.extend(record.catalog.to_bytes(2, "big"))
    data.extend(mask.to_bytes(3, "big"))
    for template in record.templates:
        data.extend(template.to_bytes(2, "big"))
    data.extend(payload)
    data.extend(binascii.crc_hqx(data, 0xFFFF).to_bytes(2, "big"))
    assert len(data) == size
    return bytes(data).ljust(RECORD_BYTES, b"\0")


def unpack(data, *, expected_catalog):
    """Decode only an explicitly tagged envelope for the requested catalog.

    This is not an auto-detector for native mail. A future native record flag
    must distinguish encoded snapshots before any text reader is invoked.
    """
    integer(expected_catalog, 1, 0xFFFF, "expected catalog identity")
    if type(data) is not bytes or len(data) != RECORD_BYTES:
        raise ValueError("Wrong mail envelope size")
    if data[0] != MAGIC or data[1] >> 4 != VERSION or data[1] & 15 not in PARTS:
        raise ValueError("Unsupported mail envelope format")
    kind, size = data[1] & 15, data[2]
    if not snapshot_size(kind, ()) <= size <= RECORD_BYTES:
        raise ValueError("Invalid mail envelope payload size")
    if any(data[size:]):
        raise ValueError("Non-canonical mail envelope padding")
    if binascii.crc_hqx(data[:size-2], 0xFFFF) != int.from_bytes(data[size-2:size], "big"):
        raise ValueError("Mail snapshot checksum mismatch")
    catalog = int.from_bytes(data[3:5], "big")
    if catalog != expected_catalog:
        raise ValueError("Mail snapshot requires a different immutable catalog")
    mask = int.from_bytes(data[5:8], "big")
    if mask >> FIELD_COUNT:
        raise ValueError("Reserved mail field bits are set")
    pos = 8
    templates = tuple(int.from_bytes(data[pos+2*i:pos+2*i+2], "big") for i in range(PARTS[kind]))
    pos += 2*PARTS[kind]
    fields = []
    for index in range(FIELD_COUNT):
        if mask & (1 << index):
            if pos >= size-2:
                raise ValueError("Truncated mail field metadata")
            width, article = data[pos] & 31, data[pos] >> 5
            pos += 1
            if width > FIELD_BYTES or article > 4 or pos+width > size-2:
                raise ValueError("Invalid mail field payload")
            fields.append((index, Field(data[pos:pos+width], article)))
            pos += width
    if pos != size-2:
        raise ValueError("Extra mail snapshot payload")
    return Record(catalog, kind, templates, tuple(fields))
