"""Complete leaflet time, installed actor changes, and atomic dependency guards."""

from copy import deepcopy
import ctypes as C
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,by_vrom,replace_dma,sha256
from leaflet_dates import (ACTORS,CALLS,HOUR,HOUR_END,SCRATCH_CHANGES,changes,install,
                           native_evidence,patched,relocated,source,validate_hour,verify_installation)
from npc_mail_show import relocate_verified_data


@unittest.skipUnless(shutil.which('gcc'),'Host GCC required')
class LeafletHourTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        library = Path(cls.temporary.name)/'hour.so'
        subprocess.run(['gcc','-std=c99','-Wall','-Wextra','-Werror','-O2','-shared','-fPIC',
                        str(ROOT/'overlays/leaflet_dates/hour.c'),'-o',str(library)],check=True,capture_output=True)
        cls.lib = C.CDLL(str(library));cls.hour = cls.lib.af_leaflet_hour
        cls.hour.argtypes = [C.c_void_p,C.c_uint];cls.hour.restype = C.c_int

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_all_byte_hours_and_unaligned_buffers_preserve_complete_suffix_and_guards(self):
        for value in range(256):
            hour = value if value < 24 else 0
            expected = f'{hour%12 or 12} {"a.m." if hour<12 else "p.m."}'.encode()
            for offset in range(16,32):
                data = C.create_string_buffer(b'!'*64,64)
                self.assertEqual(self.hour(C.byref(data,offset),value),len(expected))
                self.assertEqual(data.raw,b'!'*offset+expected+b'!'*(64-offset-len(expected)))

    def test_null_and_out_of_byte_range_inputs(self):
        self.assertEqual(self.hour(None,12),-1)
        for value in (256,65535,65536,0x80000000,0xFFFFFFFF):
            data = C.create_string_buffer(b'!'*16,16)
            self.assertEqual(self.hour(data,value),7)
            self.assertEqual(data.raw,b'12 a.m.'+b'!'*9)

    @unittest.skipUnless((ROOT/'build/gamecube/text/string.jsonl').is_file(),'Supplied English references required')
    def test_suffixes_match_complete_supplied_english_strings(self):
        rows = {r['id']:r for r in map(json.loads,(ROOT/'build/gamecube/text/string.jsonl').read_text().splitlines())}
        for hour,id in ((0,'string:0001'),(12,'string:0002')):
            expected = rows[id]['text'].encode()
            self.assertEqual(sha256(expected),rows[id]['sha256'])
            data = C.create_string_buffer(16);length = self.hour(data,hour)
            self.assertEqual(data.raw[:length],b'12 '+expected)


@unittest.skipUnless((ROOT/'build/leaflet-dates-pilot/build.json').is_file(),'Installed leaflet-date fixture required')
class LeafletDateInstallationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.rom = (ROOT/'build/leaflet-dates-pilot/animal-forest-halfwidth.z64').read_bytes()
        cls.build = json.loads((ROOT/'build/leaflet-dates-pilot/build.json').read_text())
        cls.module = cls.build['runtime_module'];cls.directory = ROOT/'build/leaflet-dates'
        cls.hour = (cls.directory/'hour.bin').read_bytes()
        cls.report = json.loads((cls.directory/'hour.json').read_text())
        previous = ROOT/'build/fortune-recovery-pilot'
        cls.previous = (previous/'animal-forest-halfwidth.z64').read_bytes()
        build = json.loads((previous/'build.json').read_text());files = by_vrom(cls.previous)
        cls.moved = {int(k,16):int(v,16) for k,v in build['vrom_relocations'].items()}
        cls.replacements = {int(v,16):files[cls.moved.get(int(v,16),int(v,16))].extract(cls.previous)
                            for v in build['replacement_files']}
        cls.additions = {int(v,16):files[int(v,16)].extract(cls.previous) for v in build['added_files']}

    def test_complete_patch_and_relocations_preserve_native_layout_and_scratch_lifetimes(self):
        verify_installation(self.rom,self.native,self.module,self.directory)
        self.assertEqual(len(validate_hour(self.hour,self.report)),192)
        evidence = native_evidence(self.native)
        self.assertEqual(evidence['external_interior_or_literal_references'],0)
        self.assertEqual(len(evidence['hour_callers']),3)
        for name,spec in ACTORS.items():
            old,reloc = source(self.native,name);data,unchanged = patched(self.native,name,self.module)
            self.assertEqual(reloc,unchanged);self.assertEqual(len(old),len(data))
            changed = {i for i in range(0,len(data),4) if data[i:i+4] != old[i:i+4]}
            self.assertEqual(changed,{a-spec.ram for a,_,_ in changes(name,self.module)})
            for base in (0x801A0010,0x802F8010):
                self.assertEqual(relocate_verified_data(spec,data,reloc,base),
                                 relocated(self.native,name,self.module,base))
        # Redd's nine-byte month no longer overlaps the saved input pointer.
        self.assertEqual([new&0xFFFF for _,_,new in SCRATCH_CHANGES],[0x18,0x18])

    def test_code_and_manifest_mutations_are_rejected(self):
        for key,value in (('ram',HOUR+4),('bytes',192),('sources',{}),('imports',['unknown']),
                          ('relocations',[0]),('destination_bytes',6)):
            with self.assertRaises(ValueError): validate_hour(self.hour,{**self.report,key:value})
        for offset in range(0,len(self.hour),4):
            data = bytearray(self.hour);data[offset] ^= 1
            with self.assertRaises(ValueError):
                validate_hour(bytes(data),{**self.report,'sha256':sha256(data)})
        module = deepcopy(self.module);module['symbols']['af_format_month'] = '00000000'
        with self.assertRaises(ValueError): patched(self.native,'event',module)
        for name,spec in ACTORS.items():
            for vrom in (spec.vrom,spec.relocation):
                data = bytearray(by_vrom(self.native)[vrom].extract(self.native));data[0] ^= 1
                with self.assertRaises(ValueError): source(replace_dma(self.native,{vrom:bytes(data)}),name)

    def test_install_matches_cartridge_and_rejection_retains_all_maps(self):
        replacements,additions,moved = dict(self.replacements),dict(self.additions),dict(self.moved)
        report = install(self.native,replacements,additions,moved,self.module,self.directory)
        self.assertEqual(report,self.build['leaflet_dates'])
        self.assertEqual(additions,self.additions);self.assertEqual(moved,self.moved)
        files = by_vrom(self.rom)
        for vrom in (CODE_VROM,0x84D180,0x850680):
            self.assertEqual(replacements[vrom],files[vrom].extract(self.rom))
        for mutation in ('module','hour','actor','relocations','main_hour_caller'):
            replacements,additions,moved = dict(self.replacements),dict(self.additions),dict(self.moved)
            if mutation == 'module': additions.pop(0x2800000)
            elif mutation == 'hour':
                data = bytearray(replacements[CODE_VROM]);data[HOUR-CODE_RAM] ^= 1
                replacements[CODE_VROM] = bytes(data)
            elif mutation == 'actor': replacements[0x84D180] = b'overlap'
            elif mutation == 'relocations': moved[0x850680] = 0x3800000
            else:
                data = bytearray(replacements[CODE_VROM]);data[0x8009F0C4-CODE_RAM] ^= 1
                replacements[CODE_VROM] = bytes(data)
            before = dict(replacements),dict(additions),dict(moved)
            with self.assertRaises(ValueError):
                install(self.native,replacements,additions,moved,self.module,self.directory)
            self.assertEqual((replacements,additions,moved),before)


if __name__ == '__main__':
    unittest.main()
