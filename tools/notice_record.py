"""Lossless bulletin-board envelopes within the native 96-byte message field.

Profile one embeds a classic mail snapshot, not a 122-byte mail save record.
Storage validity is separate from approval of a notice's text and native owner.
No save hooks or text-coverage credit are enabled by this module.
"""

from mail_record import Record, pack as mail_pack, unpack as mail_unpack

RECORD_BYTES = 96
PREFIX = b"\x7fBN\x01"
PAYLOAD_BYTES = RECORD_BYTES - len(PREFIX)


def tagged(data):
    """Recognise the family, including unsupported versions, not valid content.

    Native integration must establish that ordinary editor output cannot carry
    this reserved command prefix. Malformed tagged records must not become text.
    """
    return type(data) is bytes and data.startswith(PREFIX[:3])


def pack(record):
    if not isinstance(record, Record) or record.kind != 0:
        raise ValueError("Notice snapshots require a classic body template")
    wire = mail_pack(record)
    if wire[2] > PAYLOAD_BYTES:
        raise ValueError("Notice snapshot exceeds native message storage")
    return PREFIX + wire[:PAYLOAD_BYTES]


def expand(data, *, expected_catalog):
    if type(data) is not bytes or len(data) != RECORD_BYTES or data[:4] != PREFIX:
        raise ValueError("Unsupported notice envelope format or size")
    wire = data[4:] + bytes(122-PAYLOAD_BYTES)
    record = mail_unpack(wire, expected_catalog=expected_catalog)
    if record.kind != 0 or wire[2] > PAYLOAD_BYTES:
        raise ValueError("Invalid notice body kind or payload size")
    return wire


def unpack(data, *, expected_catalog):
    return mail_unpack(expand(data, expected_catalog=expected_catalog),
                       expected_catalog=expected_catalog)
