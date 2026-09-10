"""Immutable catalogue-five literal glyph semantics; old formatters remain unchanged."""
from mail_record import pack
from mail_format import (Templates,Letter,field_index,upper,ARTICLES,TEXT_BYTES,
                         format_letter as original_format)
from mail_glyph_codes import ADVANCES as PREVIOUS_ADVANCES, CAPITALS as PREVIOUS_CAPITALS

CATALOG=5
SEMANTICS=3
VROM=0x03100000
ADVANCES={**PREVIOUS_ADVANCES,0x87:6,0x12:6}
CAPITALS={**PREVIOUS_CAPITALS,0x87:0x12}


def glyph(data,pos):
    if pos+1>=len(data) or data[pos]!=0x80 or data[pos+1] not in ADVANCES:
        raise ValueError("Unknown or truncated literal/template glyph")
    return data[pos+1]


def format_letter(record, templates):
    """Assemble all wording; reject malformed input or overflow, never shorten.

    Substitutions retain their captured bytes in storage. As in GAFE01, only
    trailing space padding is omitted when displaying a free-string field.
    Template spaces/newlines are not trimmed or reflowed. Header newlines are
    name-placement markers, not body line breaks.
    """
    if record.catalog != CATALOG:
        return original_format(record,templates)
    pack(record)  # Same structural/storage contract as the persisted snapshot.
    if not isinstance(templates, Templates) or (templates.catalog, templates.kind) != (record.catalog, record.kind):
        raise ValueError("Mail template catalog/kind mismatch")
    expected_ids = record.templates if record.kind else record.templates*3
    if templates.ids != expected_ids or len(templates.parts) != len(expected_ids):
        raise ValueError("Mail template identity/count mismatch")
    if any(type(part) is not bytes or len(part) > TEXT_BYTES for part in templates.parts):
        raise ValueError("Invalid mail template bytes/size")
    # Pairs may not borrow their second byte from the next composite part.
    if record.catalog == CATALOG:
        for part in templates.parts:
            pos = 0
            while pos < len(part):
                byte = part[pos]
                if byte == 0x80:
                    glyph(part,pos)
                pos += 2 if byte in (0x7F,0x80) else 1
    fields = dict(record.fields)
    for field in fields.values():
        pos=0
        while pos<len(field.text):
            byte=field.text[pos]
            if byte==0x7F:raise ValueError("Mail literals cannot contain commands")
            if byte==0x80:glyph(field.text,pos)
            pos+=2 if byte==0x80 else 1
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
                if record.catalog != CATALOG:
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
                    if chunk[0]==0x80:
                        code=glyph(chunk,0)
                        chunk=bytes((0x80,CAPITALS.get(code,code)))+chunk[2:]
                    else:
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
