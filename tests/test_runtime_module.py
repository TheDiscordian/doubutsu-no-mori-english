"""DMA reservation and resident-module source/artifact contract checks."""

import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"tools"))
from aflib import CODE_RAM, CODE_VROM, DMA_START, by_vrom, dma_entries, replace_dma
from runtime_module import (BOOTSTRAP_RAM, MODULE_RAM, MODULE_VROM, RESERVATION,
                            WATCHDOG_COPY, WATCHDOG_START, add_runtime_module,
                            audit_watchdog_references, module_command_info,
                            verify_runtime_module, watchdog_bytes)
from textcodec import encode, tokenize
from textvalidate import validate_entry
from test_retail import ROM_PATH


@unittest.skipUnless(ROM_PATH.is_file(), "Retail ROM is a local-only optional test input")
class ModuleRetailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = ROM_PATH.read_bytes()

    def test_added_dma_file_and_preserved_terminator(self):
        payload = bytes(range(256))*64
        output = replace_dma(self.rom, {}, additions={MODULE_VROM: payload})
        self.assertEqual(len(dma_entries(output)), len(dma_entries(self.rom))+1)
        self.assertEqual(by_vrom(output)[MODULE_VROM].extract(output), payload)
        row = DMA_START+len(dma_entries(self.rom))*16
        self.assertEqual(output[row+16:row+32], bytes(16))
        allowed = set(range(16, 24)) | set(range(row, row+16))
        self.assertFalse(any(a != b and i not in allowed
                             for i, (a, b) in enumerate(zip(self.rom, output))))

    def test_bad_dma_additions_fail(self):
        for vrom, data in ((MODULE_VROM+1, bytes(16)), (MODULE_VROM, b"A"),
                           (MODULE_VROM, b""), (CODE_VROM, bytes(16)),
                           (0x04000000, bytes(16))):
            with self.assertRaisesRegex(ValueError, "Invalid new DMA"):
                replace_dma(self.rom, {}, additions={vrom: data})
        with self.assertRaisesRegex(ValueError, "overlap"):
            replace_dma(self.rom, {}, additions={CODE_VROM+16: bytes(16)})
        damaged = bytearray(self.rom)
        row = DMA_START+len(dma_entries(self.rom))*16
        damaged[row+16] = 1
        with self.assertRaisesRegex(ValueError, "unused DMA"):
            replace_dma(damaged, {}, additions={MODULE_VROM: bytes(16)})

    def test_watchdog_relocation_is_supported(self):
        self.assertEqual(len(watchdog_bytes(self.rom)), 496)
        self.assertEqual(audit_watchdog_references(self.rom)["external_interior_references"], [])

    def test_command_gaps_and_clock_field_policy(self):
        info = module_command_info(self.rom)
        self.assertEqual(encode("{cmd:7F76}", info), b"\x7f\x76")
        for command in (0x61, 0x63, 0x74, 0x77, 0xFF):
            with self.assertRaisesRegex(ValueError, "Unsupported"):
                list(tokenize(bytes([0x7F, command]), info))
            self.assertEqual(list(tokenize(bytes([0x7F, command]), info, strict=False))[0].kind, "raw")
        original = b"\x7f\x21"
        translated = b"\x7f\x21 \x7f\x76 \x7f\x1f"
        validate_entry(original, translated, info, "message", "reference_text", resident_runtime=True)
        with self.assertRaisesRegex(ValueError, "absent"):
            validate_entry(original, translated, info, "message", "reference_text")
        with self.assertRaisesRegex(ValueError, "preceding hour"):
            validate_entry(original, b"\x7f\x76", info, "message", "reference_text", resident_runtime=True)
        validate_entry(b"\x7f\x24", b"\x7f\x75\x7f\x24", info, "message", "presentation", resident_runtime=True)
        with self.assertRaisesRegex(ValueError, "signature"):
            validate_entry(b"\x7f\x24", b"\x7f\x75\x7f\x24", info, "message", "presentation")

    def test_cancel_policy_requires_matching_native_b_behaviour(self):
        info = module_command_info(self.rom)
        self.assertEqual(encode("{cmd:7F62}", info), b"\x7f\x62")
        validate_entry(b"\x7f\x5e", b"\x7f\x62", info, "message", "presentation", resident_runtime=True)
        for source, policy, runtime in ((b"\x7f\x5e", "exact", True),
                                        (b"\x7f\x5e", "presentation", False),
                                        (b"", "presentation", True)):
            with self.assertRaisesRegex(ValueError, "signature"):
                validate_entry(source, b"\x7f\x62", info, "message", policy, resident_runtime=runtime)

    @unittest.skipUnless((ROOT/"build/runtime-module/module.json").is_file(),
                         "Build resident-module artifacts to exercise guarded insertion")
    def test_module_artifacts_guards_and_insertion(self):
        directory = ROOT/"build/runtime-module"
        replacements = {}
        additions, report = add_runtime_module(self.rom, replacements, directory)
        self.assertEqual(len(additions[MODULE_VROM]), RESERVATION)
        code = replacements[CODE_VROM]
        word = lambda address: struct.unpack_from(">I", code, address-CODE_RAM)[0]
        self.assertEqual(word(WATCHDOG_START), 0x08000000 | ((WATCHDOG_COPY & 0x0FFFFFFF) >> 2))
        self.assertEqual(word(0x800D6720), 0x0C000000 | ((BOOTSTRAP_RAM & 0x0FFFFFFF) >> 2))
        self.assertEqual(report["ram"], f"{MODULE_RAM:08X}")
        verify_runtime_module(self.rom, replacements, additions, directory)
        with self.assertRaisesRegex(ValueError, "complete resident"):
            verify_runtime_module(self.rom, replacements, {}, directory)
        with self.assertRaisesRegex(ValueError, "instruction guard"):
            add_runtime_module(self.rom, replacements, directory)
        with tempfile.TemporaryDirectory() as temporary:
            copy = Path(temporary)
            for name in ("module.json", "module.bin", "bootstrap.bin"):
                (copy/name).write_bytes((directory/name).read_bytes())
            manifest = json.loads((copy/"module.json").read_text())
            manifest["runtime_sources"].pop("module.c")
            (copy/"module.json").write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "source inventory"):
                add_runtime_module(self.rom, {}, copy)
            (copy/"module.json").write_bytes((directory/"module.json").read_bytes())
            (copy/"bootstrap.bin").write_bytes(b"corrupt")
            with self.assertRaisesRegex(ValueError, "Stale or corrupt"):
                add_runtime_module(self.rom, {}, copy)


if __name__ == "__main__":
    unittest.main()
