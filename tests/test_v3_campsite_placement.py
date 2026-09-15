"""Checked tent placement hooks, donor semantics, and complete owner retention."""
import json
from pathlib import Path
import struct
import sys
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,DMA_START,DMA_END,by_vrom,sha256,n64_checksum
from v3_asset_loader import BLOB,MODULE,CONFIG
import v3_campsite_placement as runtime

OUTPUT = ROOT/'build/v3-campsite-placement-runtime-01'


class PlacementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=(runtime.BASE/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.rom=(OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report=json.loads((OUTPUT/'build.json').read_bytes())
        cls.files,cls.old=by_vrom(cls.rom),by_vrom(cls.base)

    def test_complete_resource_and_native_owner_retention(self):
        self.assertEqual(self.files,self.old)
        self.assertEqual(self.rom[DMA_START:DMA_END],self.base[DMA_START:DMA_END])
        changed={v for v in self.files if self.files[v].extract(self.rom)!=self.old[v].extract(self.base)}
        self.assertEqual(changed,{BLOB,MODULE,CODE_VROM})
        code=bytearray(self.files[CODE_VROM].extract(self.rom))
        for row in self.report['campsite_placement']['hooks']:
            at=row['address']-CODE_RAM; new=bytes.fromhex(row['after']); old=bytes.fromhex(row['before'])
            self.assertEqual(code[at:at+len(new)],new)
            code[at:at+len(old)]=old
        self.assertEqual(code,self.old[CODE_VROM].extract(self.base))
        # In particular, keep the CURRENT English letter-manager suffix,
        # callbacks, relocations, and descriptor; do not restore Japanese code.
        for vrom in (0x03800000,0x03810000):
            self.assertEqual(self.files[vrom].extract(self.rom),self.old[vrom].extract(self.base))

    def test_exact_reservations_packet_crc_and_complete_previous_package(self):
        blob=self.files[BLOB].extract(self.rom); restored=bytearray(blob)
        previous=self.old[BLOB].extract(self.base)
        helper=(OUTPUT/'placement/code.bin').read_bytes()
        self.assertEqual(len(helper),80)
        self.assertEqual(sha256(helper),self.report['campsite_placement']['code']['sha256'])
        cleanup=struct.pack('>20H',*range(0x5826,0x5839),0x5849)
        for address,data in ((runtime.CODE,helper),(runtime.CLEANUP,cleanup)):
            at=runtime.PACKAGE+address-runtime.PACKAGE_RAM
            self.assertEqual(previous[at:at+len(data)],bytes(len(data)))
            self.assertEqual(blob[at:at+len(data)],data)
            restored[at:at+len(data)]=bytes(len(data))
        restored[4:8]=previous[4:8]; restored[0xF8:0xFC]=previous[0xF8:0xFC]
        self.assertEqual(restored,previous)
        package=blob[runtime.PACKAGE:runtime.PACKAGE+runtime.PACKAGE_SIZE]
        self.assertEqual(sha256(package),self.report['campsite_placement']['package_sha256'])
        self.assertEqual(struct.unpack_from('>4I',blob,0xF0),
            (BLOB+runtime.PACKAGE,runtime.PACKAGE_SIZE,zlib.crc32(package),runtime.PACKAGE_RAM))
        self.assertEqual(struct.unpack_from('>4I',self.files[MODULE].extract(self.rom),CONFIG),
            (BLOB,0xC000,zlib.crc32(blob[:0xC000]),75))
        at=runtime.PACKAGE+0x804A2C00-runtime.PACKAGE_RAM
        self.assertEqual(sha256(blob[at:at+256]),self.report['campsite_calendar']['packet_sha256'])
        self.assertEqual(struct.unpack_from('>II',self.rom,0x10),n64_checksum(self.rom))
        self.assertEqual(sha256(self.rom),self.report['output_sha256'])

    def test_actual_donor_lot_restoration_contract(self):
        self.assertEqual(runtime.donor_contract(),self.report['campsite_placement']['donor'])
        code=self.files[CODE_VROM].extract(self.rom)
        self.assertEqual(struct.unpack_from('>I',code,0x801069E0+8*4-CODE_RAM)[0],0x8008D12C)
        self.assertEqual(code[0x80106A14+32-CODE_RAM:0x80106A14+36-CODE_RAM],bytes(4))
        self.assertEqual(code[runtime.CLASS_TABLE+0x29-CODE_RAM],8)
        self.assertFalse(self.report['campsite_placement']['manager_installed'])
        self.assertFalse(self.report['campsite_placement']['web_patcher_enabled'])

    def test_changed_class_consumer_or_cleanup_contract_rejected(self):
        original=self.old[CODE_VROM].extract(self.base)
        symbols=self.report['campsite_placement']['code']['symbols']
        for address in (0x8008D4A8,0x8008D5BC,0x8007FBCC,0x8007FBD0,0x80105008):
            code=bytearray(original); code[address-CODE_RAM]^=1
            with self.assertRaises(ValueError): runtime.patch_native(code,original,symbols)
        altered=bytearray(original)
        struct.pack_into('>I',altered,0x80090000-CODE_RAM,0x9063119C)
        with self.assertRaises(ValueError): runtime.patch_native(bytearray(original),altered,symbols)


if __name__=='__main__': unittest.main()
