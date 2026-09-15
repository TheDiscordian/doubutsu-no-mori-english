"""Complete summer owner preservation, native links, storage, and source guards."""
import copy
import json
from pathlib import Path
import struct
import sys
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_VROM,by_vrom,sha256,n64_checksum
import v3_camper_greeting as runtime
OUTPUT=ROOT/'build/v3-camper-greeting-runtime-02'


class CamperGreetingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=(runtime.BASE/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.rom=(OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report=json.loads((OUTPUT/'build.json').read_bytes());cls.g=cls.report['camper_greeting']
        cls.files,cls.old=by_vrom(cls.rom),by_vrom(cls.base)
        cls.suffix=(OUTPUT/'greeting/code.bin').read_bytes();cls.gift=(OUTPUT/'gift/code.bin').read_bytes()

    def test_real_donor_table_and_complete_relocated_owners(self):
        changes,report=runtime.install(self.base,self.suffix,self.g['code'],self.gift,self.g['gift_code'])
        self.assertEqual(report['repeat_messages'],[11826,11856,11887,11917,11947,11977])
        self.assertEqual((report['bytes'],report['relocation_bytes']),(4064,256))
        for v,data in changes.items():self.assertEqual(self.files[v].extract(self.rom),data)
        self.assertEqual(tuple(report['sections']),(4064,0,0,0,55))

    def test_only_dispatch_loader_gift_calls_and_startup_change(self):
        changed={runtime.OLD,runtime.OLD_RELOC,runtime.QUEST,runtime.NORMAL,runtime.BLOB,runtime.MODULE,0x19D40}
        for v,e in self.old.items():
            if v not in changed:self.assertEqual(self.files[v].extract(self.rom),e.extract(self.base))
        for v in (runtime.QUEST,runtime.NORMAL):
            data=bytearray(self.files[v].extract(self.rom))
            for h in self.g['hooks']:
                if h['vrom']==v:
                    self.assertEqual(struct.unpack_from('>I',data,h['address']-h['ram'])[0],h['after'])
                    struct.pack_into('>I',data,h['address']-h['ram'],h['before'])
            self.assertEqual(data,self.old[v].extract(self.base))
        self.assertEqual(self.files[CODE_VROM].extract(self.rom),self.old[CODE_VROM].extract(self.base))

    def test_no_new_allocations_saved_fields_or_unchecked_resident_writes(self):
        self.assertEqual(self.g['shared_buffer_bytes'],0x8800)
        for key in ('saved_format_changed','saved_profile_changed','additional_resident_bytes','additional_heap_bytes'):
            self.assertFalse(self.g[key])
        blob=bytearray(self.files[runtime.BLOB].extract(self.rom));old=self.old[runtime.BLOB].extract(self.base)
        at=runtime.PACKAGE+runtime.GIFT-runtime.PACKAGE_RAM
        self.assertEqual(blob[at:at+len(self.gift)],self.gift)
        self.assertEqual(blob[runtime.PACKAGE+runtime.LAST_GIFT-runtime.PACKAGE_RAM:][:2],bytes(2))
        blob[at:at+len(self.gift)]=old[at:at+len(self.gift)]
        for pos in (4,0xF8):blob[pos:pos+4]=old[pos:pos+4]
        self.assertEqual(blob[:len(old)],old)
        full=self.files[runtime.BLOB].extract(self.rom)
        self.assertEqual(struct.unpack_from('>I',full,0xF8)[0],
                         zlib.crc32(full[runtime.PACKAGE:runtime.PACKAGE+runtime.PACKAGE_SIZE]))
        self.assertEqual(self.gift,struct.pack('>9I',0x948801D8,0x3C09804A,0xA5281A12,
            0x03200008,0,0x3C08804A,0xA5001A12,0x0800BD30,0))

    def test_source_binding_and_compiled_import_corruption_rejected(self):
        compiled=copy.deepcopy(self.g['code']);compiled['symbols']['native_first']+=4
        with self.assertRaises(ValueError):runtime.install(self.base,self.suffix,compiled,self.gift,self.g['gift_code'])
        with self.assertRaises(ValueError):runtime.install(self.base,self.suffix[:-1],self.g['code'],self.gift,self.g['gift_code'])
        altered=bytearray(self.base);altered[self.old[runtime.QUEST].pstart]^=1
        with self.assertRaises(ValueError):runtime.source_owners(altered)

    def test_directory_aliases_preserve_compressed_sources_and_cartridge_bounds(self):
        self.assertEqual(len(self.files),len(self.old))
        for row in self.g['moves']:
            original=self.old[row['old_vrom']];new=self.files[row['vrom']]
            self.assertEqual(new.index,original.index)
            self.assertEqual(new.size,row['bytes']);self.assertEqual(new.pstart,row['physical'])
            self.assertEqual(sha256(new.extract(self.rom)),row['sha256'])
            self.assertEqual(self.rom[original.pstart:original.pend],self.base[original.pstart:original.pend])
            self.assertLessEqual(new.vend,0x4000000)
        self.assertEqual(self.files[runtime.RELOC].index,self.files[runtime.VROM].index+1)
        self.assertEqual(sha256(self.rom),self.report['output_sha256'])
        self.assertEqual(struct.unpack_from('>2I',self.rom,0x10),n64_checksum(self.rom))


if __name__=='__main__':unittest.main()
