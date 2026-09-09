"""Full-letter assembly preserves reference ordering, fields, and line breaks."""

import ctypes as C
from dataclasses import replace
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"tools"))
from mail_record import Field, Record, pack, unpack
from mail_format import Templates, Letter, format_letter, TEXT_BYTES


class CField(C.Structure):
    _fields_ = [("length", C.c_ubyte), ("article", C.c_ubyte), ("text", C.c_ubyte*16)]


class CRecord(C.Structure):
    _fields_ = [("catalog", C.c_ushort), ("kind", C.c_ubyte), ("flags", C.c_ubyte),
               ("mask", C.c_uint), ("templates", C.c_ushort*5), ("fields", CField*20)]


class CPart(C.Structure):
    _fields_ = [("text", C.c_void_p), ("length", C.c_uint), ("id", C.c_ushort), ("reserved", C.c_ushort)]


class CTemplates(C.Structure):
    _fields_ = [("catalog", C.c_uint), ("kind", C.c_uint), ("parts", CPart*5)]


class CText(C.Structure):
    _fields_ = [("offsets", C.c_ushort*3), ("lengths", C.c_ushort*3),
               ("split", C.c_ushort), ("capital", C.c_ubyte), ("reserved", C.c_ubyte),
               ("text", C.c_ubyte*TEXT_BYTES)]


def fixture(parts, fields=(), capital=False):
    kind = int(len(parts) == 5)
    ids = (1, 2, 3, 4, 5) if kind else (7,)
    record = Record(1, kind, ids, tuple(fields), capital)
    templates = Templates(1, kind, ids if kind else ids*3, tuple(parts))
    return record, templates


def inplace_reference(record, templates):
    """Independent, unbounded in-place model of the guarded GAFE01 operations.

    Derived from the pinned CC0 ACReTeam m_handbill.c implementation. Uses
    replacement/movement and repeated scanning, not the streaming formatter.
    No native buffer truncation or artificial field padding becomes wording.
    Field safety and known templates are checked by callers before this model.
    """
    from mail_format import field_index
    articles = (b"", b"a ", b"an ", b"the ", b"some ")
    fields = dict(record.fields)
    capital, forced = record.initial_capital, False

    def convert(data, header=False):
        nonlocal capital, forced
        markers = data.count(b"\xcd") if header else 0
        split = data.index(b"\xcd") if markers == 1 else len(data)
        data = bytearray(data.replace(b"\xcd", b"") if header else data)
        pos = 0
        while pos < len(data):
            if data[pos] != 0x7F:
                pos += 1
                continue
            before = len(data)
            opcode = data[pos+1]
            if opcode in (0x74, 0x75):
                if opcode == 0x74:
                    forced = True
                else:
                    capital = True
                del data[pos:pos+2]
            else:
                field = fields[field_index(opcode)]
                data[pos:pos+2] = field.text.rstrip(b" ")
                data[pos:pos] = articles[0 if forced else field.article]
                if capital and pos < len(data) and ord('a') <= data[pos] <= ord('z'):
                    data[pos] -= 32
                elif capital and record.catalog == 4 and data[pos:pos+1] == b'\x80':
                    if data[pos+1] == 0x60:
                        data[pos+1] = 0x08
                    elif data[pos+1] == 0x7C:
                        data[pos+1] = 0x0A
                forced = False
            if header and pos < split:
                split += len(data)-before
        if header:
            data.extend(b" "*max(0, split-len(data)))
        return bytes(data), split

    header, split = convert(templates.parts[0], True)
    if record.kind:
        body, _ = convert(b"".join(templates.parts[1:4]))
        footer, _ = convert(templates.parts[4])
    else:
        footer, _ = convert(templates.parts[2])
        body, _ = convert(templates.parts[1])
    return Letter(header, body, footer, split, capital)


@unittest.skipUnless(shutil.which("gcc"), "Host GCC executes the standalone mail formatter")
class MailFormatTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        library = Path(cls.temporary.name)/"mail-format.so"
        subprocess.run(["gcc", "-std=c99", "-Wall", "-Wextra", "-Werror", "-O2", "-shared", "-fPIC",
                        str(ROOT/"runtime/mail/record.c"), str(ROOT/"runtime/mail/format.c"),
                        "-o", str(library)], check=True, capture_output=True)
        cls.lib = C.CDLL(str(library))
        cls.lib.af_mail_record_unpack.argtypes = [C.c_void_p, C.c_void_p, C.c_uint, C.c_uint]
        cls.lib.af_mail_format.argtypes = [C.c_void_p, C.c_void_p, C.c_void_p]

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def inputs(self, record, templates):
        native = CRecord()
        self.assertEqual(self.lib.af_mail_record_unpack(C.byref(native), pack(record), 122, record.catalog), 1)
        buffers = [C.create_string_buffer(part) for part in templates.parts]
        parts = (CPart*5)()
        for i, (data, identity) in enumerate(zip(buffers, templates.ids)):
            parts[i] = CPart(C.addressof(data), len(templates.parts[i]), identity, 0)
        return native, CTemplates(templates.catalog, templates.kind, parts), buffers

    def compare(self, record, templates, expected=None):
        record = unpack(pack(record), expected_catalog=record.catalog)
        result = format_letter(record, templates)
        self.assertEqual(result, inplace_reference(record, templates))
        if expected is not None:
            self.assertEqual(result, expected)
        native, parts, buffers = self.inputs(record, templates)
        before = bytes(native), bytes(parts), tuple(buffer.raw for buffer in buffers)
        output = C.create_string_buffer(b"!"*(C.sizeof(CText)+32), C.sizeof(CText)+32)
        self.assertEqual(self.lib.af_mail_format(C.byref(output, 16), C.byref(native), C.byref(parts)), 1)
        self.assertEqual(output.raw[:16]+output.raw[-16:], b"!"*32)
        value = CText.from_buffer_copy(output.raw[16:-16])
        chunks = [bytes(value.text[offset:offset+length]) for offset, length in zip(value.offsets, value.lengths)]
        self.assertEqual(Letter(*chunks, value.split, bool(value.capital)), result)
        self.assertEqual(value.reserved, 0)
        self.assertFalse(any(value.text[sum(value.lengths):]))
        self.assertEqual((bytes(native), bytes(parts), tuple(buffer.raw for buffer in buffers)), before)
        return output.raw[16:-16]

    def test_literal_layout_header_insertion_and_both_component_orders(self):
        parts = (b"To \xcd!", b"Line one.\xcd\xcdLine three.  \xcd", b"  Your friend  ")
        self.compare(*fixture(parts), Letter(b"To !", parts[1], parts[2], 3, False))
        self.compare(*fixture((b"So, \xcd...\xcd", b"", b"")), Letter(b"So, ...  ", b"", b"", 9, False))
        self.compare(*fixture((b"No marker", b"", b"")), Letter(b"No marker", b"", b"", 9, False))
        fields = ((0, Field(b"pear", 1)),)
        self.compare(*fixture((b"\xcd", b"\x7f\x24", b"\x7f\x75\x7f\x74"), fields),
                     Letter(b"", b"Pear", b"", 0, True))
        # Composite order is header -> all body parts -> footer, and state may
        # cross a part boundary. This includes a command split between A and B.
        self.compare(*fixture((b"\xcd", b"\x7f", b"\x75\x7f\x74", b"\x7f\x24", b"\x7f\x24"), fields),
                     Letter(b"", b"Pear", b"A pear", 0, True))

    def test_all_fields_articles_padding_and_sticky_capitalization(self):
        for index in range(20):
            opcode = 0x24+index if index < 10 else 0x36+index-10
            for width in range(17):
                for article in range(5):
                    for capital in (False, True):
                        field = Field((b"apple  "*3)[:width], article)
                        command = bytes((0x7F, opcode))
                        self.compare(*fixture((b"\xcd", command+b"-"+command+b"x", b""),
                                              ((index, field),), capital))
        self.compare(*fixture((b"\xcd", b"\x7f\x75\x7f\x24after \x7f\x24\x7f\x24end", b""),
                              ((0, Field(b" ")),)), Letter(b"", b"After End", b"", 0, True))
        self.compare(*fixture((b"\x7f\x75\x7f\x24\xcdx", b"", b""), ((0, Field(b"")),)),
                     Letter(b"X", b"", b"", 0, True))

    def test_random_streams_match_independent_inplace_reference(self):
        rng = random.Random(0xAF0301)
        tokens = [b"a", b" b ", b"\xcd", b"\x7f\x74", b"\x7f\x75"]
        tokens += [bytes((0x7F, 0x24+i)) for i in range(6)]
        for _ in range(600):
            fields = tuple((i, Field(rng.choice((b"", b"x", b"term  ", b"\0", b"\xcd")), rng.randrange(5))) for i in range(6))
            parts = [b"Hello \xcd! "] + [b"".join(rng.choices(tokens, k=rng.randrange(20))) for _ in range(rng.choice((2, 4)))]
            self.compare(*fixture(tuple(parts), fields, bool(rng.randrange(2))))

    def reject(self, record, templates):
        with self.assertRaises(ValueError):
            format_letter(record, templates)
        native, parts, buffers = self.inputs(record, templates)
        output = C.create_string_buffer(b"!"*C.sizeof(CText), C.sizeof(CText))
        self.assertEqual(self.lib.af_mail_format(output, C.byref(native), C.byref(parts)), 0)
        self.assertEqual(output.raw, b"!"*C.sizeof(CText))

    def test_unknown_codes_unsafe_fields_missing_data_and_exact_capacity(self):
        allowed = {*range(0x24, 0x2E), *range(0x36, 0x40), 0x74, 0x75}
        for opcode in set(range(256))-allowed:
            self.reject(*fixture((b"\xcd", bytes((0x7F, opcode)), b"")))
        for text in (b"ok\x7f", b"ok\x80", b"\x7f\x24"):
            self.reject(*fixture((b"\xcd", text, b"")))
        for text in (b"literal\x7f\x75", b"\x80", b"\x7f"):
            self.reject(*fixture((b"\xcd", b"\x7f\x24", b""), ((0, Field(text)),)))
        record, templates = fixture((b"H", b"x"*(TEXT_BYTES-2), b"F"))
        self.compare(record, templates)
        self.reject(record, replace(templates, parts=(b"H", b"x"*(TEXT_BYTES-1), b"F")))
        self.reject(record, replace(templates, catalog=2))
        self.reject(record, replace(templates, ids=(8, 8, 8)))
        self.reject(record, replace(templates, parts=(b"", b"x"*(TEXT_BYTES+1), b"")))
        self.reject(*fixture((b"\xcd", b"x"*400, b"x"*400, b"x"*400, b"")))

    def test_c_pointer_validation_structural_rejection_and_overlap(self):
        record, templates = fixture((b"Hi \xcd", b"\x7f\x75\x7f\x24!", b"End"), ((0, Field(b"there")),))
        expected = self.compare(record, templates)
        native, parts, buffers = self.inputs(record, templates)
        output = C.create_string_buffer(b"!"*C.sizeof(CText), C.sizeof(CText))
        for bad_record, bad_templates in ((None, C.byref(parts)), (C.byref(native), None)):
            self.assertEqual(self.lib.af_mail_format(output, bad_record, bad_templates), 0)
            self.assertEqual(output.raw, b"!"*C.sizeof(CText))
        self.assertEqual(self.lib.af_mail_format(None, C.byref(native), C.byref(parts)), 0)
        for part, attribute, bad in ((0, "reserved", 1), (1, "text", None), (1, "length", 0xFFFFFFFF)):
            old = getattr(parts.parts[part], attribute)
            setattr(parts.parts[part], attribute, bad)
            self.assertEqual(self.lib.af_mail_format(output, C.byref(native), C.byref(parts)), 0)
            self.assertEqual(output.raw, b"!"*C.sizeof(CText))
            setattr(parts.parts[part], attribute, old)
        for attr, bad in (("flags", 2), ("mask", 0x100000), ("kind", 2)):
            old = getattr(native, attr)
            setattr(native, attr, bad)
            self.assertEqual(self.lib.af_mail_format(output, C.byref(native), C.byref(parts)), 0)
            self.assertEqual(output.raw, b"!"*C.sizeof(CText))
            setattr(native, attr, old)
        # Output can overlap the snapshot structure, template descriptors, or
        # text. None is overwritten before the last input has been read.
        for which in ("record", "templates", "text"):
            C.memset(output, 0x21, C.sizeof(CText))
            if which == "record":
                C.memmove(output, C.byref(native), C.sizeof(native))
                args = output, C.byref(parts)
            elif which == "templates":
                C.memmove(output, C.byref(parts), C.sizeof(parts))
                args = C.byref(native), output
            else:
                C.memmove(output, buffers[0], len(templates.parts[0]))
                parts.parts[0].text = C.addressof(output)
                args = C.byref(native), C.byref(parts)
            self.assertEqual(self.lib.af_mail_format(output, *args), 1)
            self.assertEqual(output.raw, expected)

    @unittest.skipUnless((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').is_file()
                         and (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').is_file(),
                         'Local retail ROM and extracted English disc required')
    def test_source_verified_english_classic_and_composite_assembly(self):
        from aflib import verified_rom
        from mail_reference import load_reference, assembly_cases
        banks, report = load_reference(ROOT/'build/gamecube/files/forest_1st.arc.unpacked/data',
                                       ROOT/'local/ac-decomp', ROOT/'build/gamecube/files/foresta.rel.szs.decoded')
        self.assertEqual(sum(bank['total'] for bank in report['banks'].values()), 4866)
        self.assertEqual(sum(bank['converted'] for bank in report['banks'].values()), 4807)
        rom = verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
        assembled = rejected = bounded = 0
        for label, record, templates, limitation in assembly_cases(banks, rom):
            with self.subTest(case=label):
                if record is None:
                    self.assertEqual(limitation, 'unrepresentable_reference_glyph')
                    rejected += 1
                    continue
                self.compare(record, templates)
                assembled += 1
                bounded += limitation == 'requires_actual_field_bounds'
        self.assertEqual((assembled, rejected, bounded), (6398, 58, 2))
