"""Bounded full-letter assembly from already transcoded, immutable templates.

This does not install a catalog, approve an identity, or render a native record.
GAFE01's sticky capitalization is explicit input/output, never decoder-global.
"""

from dataclasses import dataclass

from mail_record import pack
from mail_glyph_codes import CATALOG as GLYPH_CATALOG, CAPITALS, glyph

TEXT_BYTES = 1024
ARTICLES = (b"", b"a ", b"an ", b"the ", b"some ")


@dataclass(frozen=True)
class Templates:
    catalog: int
    kind: int
    ids: tuple[int, ...]
    parts: tuple[bytes, ...]  # header/body/footer, or header/A/B/C/footer


@dataclass(frozen=True)
class Letter:
    header: bytes
    body: bytes
    footer: bytes
    header_split: int
    final_capital: bool


def field_index(opcode):
    if 0x24 <= opcode <= 0x2D:
        return opcode-0x24
    if 0x36 <= opcode <= 0x3F:
        return opcode-0x36+10
    raise ValueError(f"Unsupported mail command 7F{opcode:02X}")


def upper(byte):
    return byte-32 if ord('a') <= byte <= ord('z') else byte


def format_letter(record, templates):
    """Assemble all wording; reject malformed input or overflow, never shorten.

    Substitutions retain their captured bytes in storage. As in GAFE01, only
    trailing space padding is omitted when displaying a free-string field.
    Template spaces/newlines are not trimmed or reflowed. Header newlines are
    name-placement markers, not body line breaks.
    """
    pack(record)  # Same structural/storage contract as the persisted snapshot.
    if not isinstance(templates, Templates) or (templates.catalog, templates.kind) != (record.catalog, record.kind):
        raise ValueError("Mail template catalog/kind mismatch")
    expected_ids = record.templates if record.kind else record.templates*3
    if templates.ids != expected_ids or len(templates.parts) != len(expected_ids):
        raise ValueError("Mail template identity/count mismatch")
    if any(type(part) is not bytes or len(part) > TEXT_BYTES for part in templates.parts):
        raise ValueError("Invalid mail template bytes/size")
    # Pairs may not borrow their second byte from the next composite part.
    if record.catalog == GLYPH_CATALOG:
        for part in templates.parts:
            pos = 0
            while pos < len(part):
                byte = part[pos]
                if byte == 0x80:
                    glyph(part,pos)
                pos += 2 if byte in (0x7F,0x80) else 1
    fields = dict(record.fields)
    if any(any(byte in (0x7F, 0x80) for byte in field.text) for field in fields.values()):
        raise ValueError("Mail fields must contain literal single-byte glyphs")
    capital, forced, total = record.initial_capital, False, 0

    def expand(data, header=False):
        nonlocal capital, forced, total
        if len(data) > TEXT_BYTES:
            raise ValueError("Mail template section exceeds input capacity")
        output, pos, split, pending = bytearray(), 0, 0, False
        markers = data.count(b"\xcd") if header else 0

        def append(chunk):
            nonlocal total
            if total+len(chunk) > TEXT_BYTES:
                raise ValueError("Complete mail exceeds output capacity")
            output.extend(chunk)
            total += len(chunk)

        while pos < len(data):
            byte = data[pos]
            pos += 1
            if header and byte == 0xCD:
                split = len(output)
                continue
            if byte == 0x80:
                if record.catalog != GLYPH_CATALOG:
                    raise ValueError("Mail templates require single-byte glyphs")
                code = glyph(data,pos-1)
                append(bytes((0x80,CAPITALS.get(code,code) if pending else code)))
                pos += 1
                pending = False
                continue
            if byte != 0x7F:
                append(bytes((upper(byte) if pending else byte,)))
                pending = False
                continue
            pending = False  # Native capitalization of the command prefix does nothing.
            if pos == len(data):
                raise ValueError("Truncated mail command")
            opcode = data[pos]
            pos += 1
            if opcode == 0x74:
                forced = True
            elif opcode == 0x75:
                capital = True
            else:
                index = field_index(opcode)
                if index not in fields:
                    raise ValueError(f"Missing captured mail field {index}")
                field = fields[index]
                chunk = ARTICLES[0 if forced else field.article] + field.text.rstrip(b" ")
                forced = False
                if capital and chunk:
                    chunk = bytes((upper(chunk[0]),)) + chunk[1:]
                append(chunk)
                # GAFE01 uppercases the following byte when an insertion is
                # empty, even when that byte is an ordinary template glyph.
                pending = capital and not chunk
        if header and markers != 1:
            # The reference uses the original size when the marker is absent
            # or duplicated, leaving one space for each removed newline.
            append(b" "*markers)
            split = len(output)
        return bytes(output), split

    header, split = expand(templates.parts[0], True)
    if record.kind:
        body, _ = expand(b"".join(templates.parts[1:4]))
        footer, _ = expand(templates.parts[4])
    else:
        footer, _ = expand(templates.parts[2])
        body, _ = expand(templates.parts[1])
    return Letter(header, body, footer, split, capital)
