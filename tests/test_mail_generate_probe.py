"""Original synthetic code checks for the isolated generation probe loader."""

from copy import deepcopy
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256
from build_mail_generation import IMPORTS,SOURCES
from mail_generate_probe import validate,relocate
from runtime_layout import MODULE_RAM,RESERVATION


class MailGenerateProbeTests(unittest.TestCase):
    def setUp(self):
        self.module = {'module_sha256':'a'*64,
                       'symbols':{name:f'{MODULE_RAM+0x300+i*16:08X}'
                                  for i,name in enumerate(IMPORTS)}}
        self.imports = {name:int(value,16) for name,value in self.module['symbols'].items()}
        # The internal J and imported JAL are intentionally synthetic, not
        # executable game instructions or an assumed production link layout.
        self.code = struct.pack('>8I',0,0,0,0x08000000|((0x8020001C&0xFFFFFFF)>>2),
                                0x0C000000|((self.imports[IMPORTS[0]]&0xFFFFFFF)>>2),
                                0x03E00008,0,0)
        self.report = {'version':1,'base':0x80200000,'bytes':len(self.code),
                       'sha256':sha256(self.code),
                       'sources':{name:sha256((ROOT/name).read_bytes()) for name in SOURCES},
                       'module_sha256':self.module['module_sha256'],'imports':self.imports,
                       'symbols':{'af_mail_capture_reset':0,'af_mail_capture_set':4,
                                  'af_mail_generate':8},'jump_relocations':[12]}

    def test_internal_jump_relocation_and_other_instructions_retained(self):
        validate(self.code,self.report,self.module)
        before_code,before_report = self.code,deepcopy(self.report)
        for base in (MODULE_RAM+RESERVATION,0x80200000,0x80300000,0x80400000-len(self.code)):
            result = relocate(self.code,self.report,self.module,base)
            self.assertEqual(result[:12]+result[16:],self.code[:12]+self.code[16:])
            word = struct.unpack_from('>I',result,12)[0]
            self.assertEqual(word>>26,2)
            self.assertEqual(0x80000000|((word&0x3FFFFFF)<<2),base+28)
        self.assertEqual(self.code,before_code)
        self.assertEqual(self.report,before_report)

    def test_stale_code_sources_module_and_imports_are_rejected(self):
        for key,value in (('version',2),('base',0x80200004),('bytes',36),
                          ('sha256','0'*64),('sources',{}),('module_sha256','0'*64),
                          ('imports',{})):
            report = deepcopy(self.report);report[key] = value
            with self.subTest(key=key),self.assertRaises(ValueError):
                validate(self.code,report,self.module)
        for code in (b'',self.code[:4],self.code+b'\0',bytes([1])+self.code[1:]):
            with self.assertRaises(ValueError): validate(code,self.report,self.module)
        report = deepcopy(self.report)
        report['imports'][IMPORTS[0]] += 4
        with self.assertRaises(ValueError): validate(self.code,report,self.module)

    def test_entry_points_and_relocation_inventory_are_bounded(self):
        for value in (-4,2,len(self.code),True,'0'):
            report = deepcopy(self.report);report['symbols']['af_mail_generate'] = value
            with self.subTest(entry=value),self.assertRaises(ValueError):
                validate(self.code,report,self.module)
        for names in ({},{'af_mail_generate':0},{**self.report['symbols'],'extra':0}):
            report = deepcopy(self.report);report['symbols'] = names
            with self.assertRaises(ValueError): validate(self.code,report,self.module)
        for entries in ([],[12,12],[12,16],[12,0],[-4],[2],[32],[True],['12'],(12,)):
            report = deepcopy(self.report);report['jump_relocations'] = entries
            with self.subTest(relocations=entries),self.assertRaises(ValueError):
                validate(self.code,report,self.module)

    def test_unknown_jump_destinations_are_rejected_even_with_new_code_hash(self):
        for target in (0x80200000-4,0x80200000+len(self.code),MODULE_RAM,0x80000000):
            code = bytearray(self.code)
            struct.pack_into('>I',code,12,0x08000000|((target&0xFFFFFFF)>>2))
            report = deepcopy(self.report);report['sha256'] = sha256(code)
            report['jump_relocations'] = []
            with self.subTest(target=target),self.assertRaises(ValueError):
                validate(code,report,self.module)
        # Imports must not be labelled as relocatable internal calls.
        code = bytearray(self.code)
        struct.pack_into('>I',code,12,0x08000000|((self.imports[IMPORTS[1]]&0xFFFFFFF)>>2))
        report = deepcopy(self.report);report['sha256'] = sha256(code)
        with self.assertRaises(ValueError): validate(code,report,self.module)
        report['jump_relocations'] = []
        validate(code,report,self.module)

    def test_allocation_rejects_reserved_memory_alignment_and_four_mib_overflow(self):
        for base in (None,True,0,MODULE_RAM,MODULE_RAM+RESERVATION-16,
                     MODULE_RAM+RESERVATION+1,0x80400000-len(self.code)+16,
                     0x80400000,0xA0200000):
            with self.subTest(base=base),self.assertRaises(ValueError):
                relocate(self.code,self.report,self.module,base)

    @unittest.skipUnless((ROOT/'build/mail-generation-runtime-followup-01/generate.json').is_file(),
                         'Local native generation build required')
    def test_current_native_artifact_has_verified_imports_and_exported_entries(self):
        directory = ROOT/'build/mail-generation-runtime-followup-01'
        code = (directory/'generate.bin').read_bytes()
        report = json.loads((directory/'generate.json').read_text())
        module = json.loads((ROOT/'build/notice-seasonal-runtime/module.json').read_text())
        validate(code,report,module)
        for base in (MODULE_RAM+RESERVATION,0x80200000,0x80300000):
            output = relocate(code,report,module,base)
            self.assertEqual(len(output),len(code))
            self.assertEqual({offset for offset in range(0,len(code),4)
                              if output[offset:offset+4] != code[offset:offset+4]},
                             set(report['jump_relocations']) if base != report['base'] else set())


if __name__ == '__main__': unittest.main()
