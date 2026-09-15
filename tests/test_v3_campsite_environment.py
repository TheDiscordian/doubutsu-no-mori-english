"""Current campsite sound/light installation and unchanged neighbouring owners."""
import copy
import json
import struct
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_VROM,CODE_RAM,DMA_START,DMA_END,by_vrom,sha256,n64_checksum
import v3_campsite_environment as runtime
OUTPUT=ROOT/'build/v3-campsite-environment-runtime-02'


class CampsiteEnvironmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base=(runtime.BASE/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.rom=(OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report=json.loads((OUTPUT/'build.json').read_bytes())
        cls.env=cls.report['campsite_environment']
        cls.files,cls.old=by_vrom(cls.rom),by_vrom(cls.base)
        cls.helper=(OUTPUT/'environment/code.bin').read_bytes()

    def test_actual_donor_program_instrument_and_sample_match(self):
        dol,audio=runtime.read_audio_donor(ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso')
        donor=runtime.verify_donor(self.native,dol,audio)
        self.assertEqual(donor,self.env['donor'])
        self.assertEqual(donor['sound_id'],0x306)
        self.assertEqual(donor['sounds'][0]['complete_instrument'],donor['sounds'][1]['complete_instrument'])
        with self.assertRaises(ValueError):runtime.verify_donor(self.native,dol,audio[:-1])

    def test_exact_installation_and_both_preserved_native_bodies(self):
        blob,code,hooks=runtime.install(self.native,self.base,self.helper,self.env['code'])
        actual_blob=bytearray(self.files[runtime.BLOB].extract(self.rom))
        struct.pack_into('>I',actual_blob,4,81)
        self.assertEqual(blob,actual_blob)
        self.assertEqual(code,self.files[CODE_VROM].extract(self.rom))
        self.assertEqual(hooks,self.env['hooks'])
        for hook in hooks:
            offset=hook['address']-CODE_RAM
            code[offset:offset+8]=bytes.fromhex(hook['before'])
        self.assertEqual(code,self.old[CODE_VROM].extract(self.base))

    def test_preserved_assets_audio_save_code_and_dma(self):
        for v,e in self.old.items():
            if v not in (runtime.BLOB,runtime.MODULE,CODE_VROM,0x19D40):
                self.assertEqual(self.files[v].extract(self.rom),e.extract(self.base))
        self.assertEqual(self.rom[DMA_START:DMA_END],self.base[DMA_START:DMA_END])
        blob=bytearray(self.files[runtime.BLOB].extract(self.rom))
        old=self.old[runtime.BLOB].extract(self.base)
        start=runtime.PACKAGE+runtime.RAM-runtime.PACKAGE_RAM
        blob[start:start+len(self.helper)]=bytes(len(self.helper))
        blob[4:8]=old[4:8];blob[0xF8:0xFC]=old[0xF8:0xFC]
        self.assertEqual(blob,old)
        for key in ('additional_resident_bytes','additional_heap_bytes','saved_format_changed',
                    'saved_profile_changed','timed_lamp_installed','web_patcher_enabled'):
            self.assertFalse(self.env[key])

    def test_exact_checked_resident_extent_and_trampolines(self):
        self.assertEqual(len(self.helper),156)
        self.assertEqual(runtime.RAM+len(self.helper),runtime.LIMIT)
        symbols=self.env['code']['symbols']
        self.assertEqual(symbols['af_v3_campsite_point_info'],runtime.RAM+40)
        self.assertEqual(self.helper[28:40],runtime.words(0x27BDFFE8,runtime.jump(0x800BEECC),0xAFBF0014))
        self.assertEqual(self.helper[-16:],runtime.words(0x27BDFFE0,0xAFA40020,runtime.jump(0x80096D68),0))

    def test_bad_bindings_helper_or_occupied_memory_fail_closed(self):
        compiled=copy.deepcopy(self.env['code']);compiled['symbols']['native_scene']+=4
        with self.assertRaises(ValueError):runtime.install(self.native,self.base,self.helper,compiled)
        with self.assertRaises(ValueError):runtime.install(self.native,self.base,self.helper[:-4],self.env['code'])
        for at in (self.old[runtime.BLOB].pstart+runtime.PACKAGE+runtime.RAM-runtime.PACKAGE_RAM,
                   self.old[CODE_VROM].pstart+0x800BEECC-CODE_RAM):
            base=bytearray(self.base);base[at]^=1
            with self.assertRaises(ValueError):runtime.install(self.native,base,self.helper,self.env['code'])

    def test_current_startup_resource_and_cartridge_checksums(self):
        import zlib
        blob=self.files[runtime.BLOB].extract(self.rom)
        module=self.files[runtime.MODULE].extract(self.rom)
        self.assertEqual(struct.unpack_from('>4I',module,runtime.CONFIG),
            (runtime.BLOB,0xC000,zlib.crc32(blob[:0xC000]),82))
        self.assertEqual(struct.unpack_from('>I',blob,0xF8)[0],
            zlib.crc32(blob[runtime.PACKAGE:runtime.PACKAGE+runtime.PACKAGE_SIZE]))
        self.assertEqual(sha256(self.rom),self.report['output_sha256'])
        self.assertEqual(struct.unpack_from('>2I',self.rom,0x10),n64_checksum(self.rom))


if __name__=='__main__':unittest.main()
