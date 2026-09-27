"""Installed full-image disk sessions and retained cartridge paths."""
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,sha256,apply_ups
from npc_mail_show import relocate_verified_data
from v3_asset_loader import BLOB,MODULE
from v3_furniture_install import inputs
from v3_console_emulator import VROM,RELOC,RAM,patch


class ConsoleDiskSessionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out=ROOT/os.environ.get('V3_DISK_SESSION_BUILD','build/v3-console-disk-session-01')
        cls.image,cls.report=inputs(cls.out/'build-lock.json')
        cls.base,cls.prior=inputs(cls.out/'base-lock.json')
        cls.disk=cls.report['equipment_resources']['console_disk']

    def test_complete_native_hooks_and_retained_resources(self):
        files=by_vrom(self.image);old=by_vrom(self.base);e=self.report['equipment_resources'];d=self.disk
        images=e['console_images'];blob=files[BLOB].extract(self.image);prior_blob=old[BLOB].extract(self.base)
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes();original_files=by_vrom(original)
        owner,reloc,binding=patch(original_files[VROM].extract(original),original_files[RELOC].extract(original),
            images['compiled']['symbols'],disk_symbols=d['compiled']['symbols'])
        self.assertEqual(files[VROM].extract(self.image),owner);self.assertEqual(files[RELOC].extract(self.image),reloc)
        self.assertEqual(images['emulator']['native'],binding)
        self.assertEqual(len(binding['hooks']),10);self.assertEqual(len(binding['removed_relocations']),13)
        self.assertEqual({h['symbol'] for h in binding['hooks']},
            {'af_v3_console_'+n for n in ('graphics','setup','initialize','frame_native','reset_native','close_native',
             'arena_allocate','extent','cpu_frame')}|{'af_v3_qd_dpcm_bridge'})
        p=d['packet'];raw=blob[p['blob_offset']:p['blob_offset']+p['bytes']]
        q=self.prior['equipment_resources']['console_disk']['packet']
        self.assertEqual(raw[0x6000:],prior_blob[q['blob_offset']+0x6000:q['blob_offset']+q['bytes']])
        self.assertEqual(sha256(raw),p['sha256']);self.assertEqual(zlib.crc32(raw),p['crc32'])
        self.assertEqual(sha256(raw[:d['compiled']['bytes']]),d['compiled']['sha256'])
        self.assertLessEqual(d['compiled']['bytes'],0x6000)
        self.assertFalse(any(raw[d['compiled']['bytes']:0x6000]))
        for name,address in d['shared_calls'].items():self.assertEqual(address,images['compiled']['symbols'][name])
        for name in ('wdm','ram','read','write','irq','dpcm'):
            at=d['compiled']['symbols']['af_v3_qd_'+name+'_bridge']-p['ram']
            words=struct.unpack_from('>77I',raw,at)
            self.assertEqual(words[0],0x27BDFEE0)
            for reg in set(range(1,32))-{29}:
                self.assertIn(0xFC000000|(29<<21)|(reg<<16)|(16+reg*8),words)
                self.assertIn(0xDC000000|(29<<21)|(reg<<16)|(16+reg*8),words)
            self.assertEqual(words[38],0x00C02025 if name=='dpcm' else 0x03C02025)
        for path,digest in d['sources'].items():self.assertEqual(sha256((ROOT/path).read_bytes()),digest,path)
        self.assertTrue(d['session_hooks_installed']);self.assertFalse(d['choice_eligible'])
        self.assertEqual(set(files),set(old))
        for v in files:
            if v not in (BLOB,MODULE,0x19D40,VROM,RELOC):
                self.assertEqual(files[v].extract(self.image),old[v].extract(self.base),hex(v))
        for key in ('console_images','console_storage','room_goods','room_carry'):
            self.assertEqual(e[key]['packet'],self.prior['equipment_resources'][key]['packet'])
        self.assertEqual(self.report['save_runtime'],self.prior['save_runtime'])
        self.assertEqual(self.report['automatic_furniture']['imports'],self.prior['automatic_furniture']['imports'])
        for row in self.report['physical_resources']:
            self.assertEqual(self.image[row['physical']:row['physical']+row['bytes']],
                             self.base[row['physical']:row['physical']+row['bytes']])
        self.assertEqual(apply_ups(original,(self.out/'asset-loader.ups').read_bytes()),self.image)

    def test_actual_image_session_with_stubbed_native_cpu_and_audio(self):
        files=by_vrom(self.image);native=files[VROM].extract(self.image);reloc=files[RELOC].extract(self.image)
        sections=struct.unpack_from('>5I',reloc)
        spec=SimpleNamespace(ram=RAM,resident_bytes=len(native)+sections[3],sections=sections)
        prepared=ROOT/'build/v3-console-games-prepared-14';p=self.disk['packet']
        blob=files[BLOB].extract(self.image)
        with tempfile.TemporaryDirectory(prefix='v3-console-disk-session-') as temp:
            out=Path(temp)
            (out/'native.bin').write_bytes(relocate_verified_data(spec,native,reloc,0x80200000))
            (out/'disk.bin').write_bytes(blob[p['blob_offset']:p['blob_offset']+p['bytes']])
            run=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-fno-pie','-no-pie',
                '-DAF_CONSOLE_DISK=1','-DAF_CONSOLE_METADATA_BYTES=6336',
                '-DAF_CONSOLE_POOL_BYTES=770144','-DAF_CONSOLE_POOL_ROM=0x03F43FA0',
                str(ROOT/'tests/v3_console_emulator_test.c'),
                *[str(ROOT/'overlays/v3'/n) for n in ('console_image_native.c','console_image.c','console_save.c',
                    'console_disk_native.c','console_disk.c')],'-o',str(out/'check')],
                capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            run=subprocess.run([str(out/'check'),str(prepared/'games-metadata.bin'),
                str(prepared/'games-pool.bin'),str(prepared/'games.bin'),str(out/'native.bin'),str(out/'disk.bin')],
                capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr);print(run.stdout.strip())

    def test_private_composition_preserves_full_disk_engine(self):
        from tests.test_v3_room_rig_runtime import CurrentImportedRigTests
        self.rows=self.report['automatic_furniture']['imports']
        CurrentImportedRigTests.test_private_browser_selection_matches_offline_and_keeps_translation_only(self)


if __name__=='__main__':unittest.main()
