"""Current trade installation, donor behaviour, and bounded native ownership."""
import copy
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_VROM,by_vrom,sha256,n64_checksum
import v3_camper_trade as runtime
OUTPUT=ROOT/'build/v3-camper-trade-runtime-02'


class CamperTradeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=(runtime.BASE/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.rom=(OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report=json.loads((OUTPUT/'build.json').read_bytes());cls.t=cls.report['camper_trade']
        cls.files,cls.old=by_vrom(cls.rom),by_vrom(cls.base)
        cls.suffix=(OUTPUT/'trade/code.bin').read_bytes()

    def test_sanitized_actual_c_trade_and_optional_profile_rules(self):
        with tempfile.TemporaryDirectory(prefix='af-camper-trade-') as directory:
            binary=Path(directory)/'test'
            subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                str(ROOT/'tests/v3_camper_trade_test.c'),str(ROOT/'overlays/v3/camper_trade.c'),
                '-o',str(binary)],check=True,capture_output=True,text=True,timeout=30)
            result=subprocess.run([str(binary)],capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('pass:',result.stdout)

    def test_complete_current_native_owner_and_donor_binding(self):
        changes,report=runtime.install(self.base,self.suffix,self.t['code'])
        for v,data in changes.items():self.assertEqual(self.files[v].extract(self.rom),data)
        self.assertEqual(report['donor'][0]['offset'],0x1228F4)
        self.assertEqual(report['donor'][1]['offset'],0x122B8C)
        self.assertEqual(report['selected_reward_items'],list(runtime.TENT[:-1]))
        self.assertLessEqual(report['bytes']+report['relocation_bytes'],0x8800)

    def test_only_two_entry_hooks_loader_descriptor_and_startup_change(self):
        changed={runtime.VROM,runtime.RELOC,runtime.QUEST,runtime.BLOB,runtime.MODULE,0x19D40}
        for v,e in self.old.items():
            if v not in changed:self.assertEqual(self.files[v].extract(self.rom),e.extract(self.base))
        normal=bytearray(self.files[runtime.VROM].extract(self.rom))
        for h in self.t['hooks']:
            at=h['address']-runtime.RAM
            self.assertEqual(normal[at:at+8].hex(),h['after'])
            normal[at:at+8]=bytes.fromhex(h['before'])
        self.assertEqual(normal[:runtime.SIZE],self.old[runtime.VROM].extract(self.base))
        quest=bytearray(self.files[runtime.QUEST].extract(self.rom))
        for p in self.t['quest_patches']:struct.pack_into('>I',quest,p['offset'],p['before'])
        self.assertEqual(quest,self.old[runtime.QUEST].extract(self.base))
        self.assertEqual(self.files[CODE_VROM].extract(self.rom),self.old[CODE_VROM].extract(self.base))

    def test_no_new_resident_or_saved_fields_and_current_crc(self):
        for key in ('saved_format_changed','saved_profile_changed','additional_resident_bytes','additional_heap_bytes'):
            self.assertFalse(self.t[key])
        blob=bytearray(self.files[runtime.BLOB].extract(self.rom));old=self.old[runtime.BLOB].extract(self.base)
        struct.pack_into('>I',blob,4,80);self.assertEqual(blob[:len(old)],old)
        full=self.files[runtime.BLOB].extract(self.rom)
        module=self.files[runtime.MODULE].extract(self.rom)
        self.assertEqual(struct.unpack_from('>4I',module,runtime.CONFIG),
                         (runtime.BLOB,0xC000,zlib.crc32(full[:0xC000]),81))
        self.assertEqual(sha256(self.rom),self.report['output_sha256'])
        self.assertEqual(struct.unpack_from('>2I',self.rom,0x10),n64_checksum(self.rom))

    def test_changed_source_code_and_native_bindings_fail_closed(self):
        changed=copy.deepcopy(self.t['code']);changed['symbols']['native_rare_item']+=2
        with self.assertRaises(ValueError):runtime.install(self.base,self.suffix,changed)
        with self.assertRaises(ValueError):runtime.install(self.base,self.suffix[:-4],self.t['code'])
        base=bytearray(self.base);base[self.old[runtime.VROM].pstart]^=1
        with self.assertRaises(ValueError):runtime.source_owners(base)

    def test_old_physical_sources_and_dma_identity_retained(self):
        self.assertEqual(set(self.files),set(self.old))
        for row in self.t['moves']:
            v=row['vrom'];new,old=self.files[v],self.old[v]
            self.assertEqual(new.index,old.index);self.assertEqual(new.pstart,row['physical'])
            end=old.pend or old.pstart+old.size
            self.assertEqual(self.rom[old.pstart:end],self.base[old.pstart:end])
            self.assertEqual(sha256(new.extract(self.rom)),row['sha256'])
        self.assertEqual(self.files[runtime.RELOC].index,self.files[runtime.VROM].index+1)


if __name__=='__main__':unittest.main()
