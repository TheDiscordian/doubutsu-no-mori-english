"""QD donor comparisons, malformed bounds, and prepared shared dependencies."""
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256,yaz0_decode
from gamecube import rarc_files
from v3_console_games import read_donor
from v3_console_disk import donor_resources,BOOT_STATE_ADDRESS,BOOT_STATE_BYTES
from tests.test_v3_player_exercise import complete_function


class ConsoleDiskTests(unittest.TestCase):
    def test_native_cpu_and_graphics_adapter(self):
        prepared=ROOT/'build/v3-console-games-prepared-09/console_disk'
        dol,archive=read_donor(ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso')
        disks=[yaz0_decode(data) for path,data in rarc_files(archive) if '.qd.' in path]
        self.assertEqual(len(disks),1)
        with tempfile.TemporaryDirectory(prefix='v3-console-disk-native-') as temp:
            out=Path(temp);(out/'disk.bin').write_bytes(disks[0])
            run=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-fno-pie','-no-pie',
                str(ROOT/'tests/v3_console_disk_native_test.c'),
                str(ROOT/'overlays/v3/console_disk_native.c'),str(ROOT/'overlays/v3/console_disk.c'),
                '-o',str(out/'check')],capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            run=subprocess.run([str(out/'check'),str(out/'disk.bin'),str(prepared/'bios.bin'),
                str(prepared/'boot-state.bin')],capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            print(run.stdout.strip())

    def test_disk_boot_save_and_register_boundaries(self):
        dol,archive=read_donor(ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso')
        receipt,bios=donor_resources(dol,archive)
        self.assertEqual(len(receipt['functions']),6)
        disks=[yaz0_decode(data) for path,data in rarc_files(archive) if '.qd.' in path]
        self.assertEqual(len(disks),1)
        source=(ROOT/'local/ac-decomp/src/static/Famicom/ks_nes_core.cpp').read_text()
        donor='\n'.join(re.findall(r'^#define (?:ksNes_|QD_).*$',source,re.M))+'\n'
        donor+='\n'.join(complete_function(source,n) for n in ('ksNesQDFastLoad','ksNesQDFastSave'))
        with tempfile.TemporaryDirectory(prefix='v3-console-disk-') as temp:
            out=Path(temp)
            (out/'donor_disk.inc').write_text(donor)
            (out/'disk.bin').write_bytes(disks[0]);(out/'bios.bin').write_bytes(bios)
            (out/'boot-state.bin').write_bytes(dol.read(BOOT_STATE_ADDRESS,BOOT_STATE_BYTES))
            flags=['-O1','-g','-Wall','-Wextra','-Werror','-fno-pie','-no-pie',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer']
            run=subprocess.run(['cc','-std=c11',*flags,'-c',str(ROOT/'overlays/v3/console_disk.c'),
                '-o',str(out/'core.o')],capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            run=subprocess.run(['c++','-std=c++17',*flags,'-Wno-unused-parameter','-I'+str(out),
                str(ROOT/'tests/v3_console_disk_test.cpp'),str(out/'core.o'),'-o',str(out/'check')],
                capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            run=subprocess.run([str(out/'check'),str(out/'disk.bin'),str(out/'bios.bin'),str(out/'boot-state.bin')],
                capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            print(run.stdout.strip())

    def test_shared_preparation_preserves_games_and_supplies_complete_bios(self):
        out=ROOT/'build/v3-console-games-prepared-11'
        report=json.loads((out/'games.json').read_text());disk=report['disk_core']
        self.assertEqual(disk,json.loads((out/'console_disk/disk.json').read_text()))
        self.assertEqual(sha256((out/'console_disk/code.bin').read_bytes()),disk['sha256'])
        self.assertEqual(sha256((out/'console_disk/bios.bin').read_bytes()),disk['source']['bios']['sha256'])
        self.assertEqual(disk['source']['bios']['vectors'],[0xE18B,0xEE24,0xE1C7])
        self.assertEqual(sha256((out/'console_disk/boot-state.bin').read_bytes()),disk['source']['boot_state']['sha256'])
        self.assertEqual(disk['source']['boot_state']['bytes'],260)
        self.assertIn('af_v3_qd_wdm',disk['compiled']['symbols'])
        self.assertIn('af_v3_qd_native_characters',disk['compiled']['symbols'])
        self.assertEqual(disk['source']['native_character_converter']['address'],0x808328DC)
        for path,digest in disk['sources'].items():self.assertEqual(sha256((ROOT/path).read_bytes()),digest,path)
        for name in ('games.bin','games-metadata.bin','games-pool.bin'):
            self.assertEqual((out/name).read_bytes(),(ROOT/'build/v3-console-games-prepared-06'/name).read_bytes())
        self.assertFalse(disk['native_hooks_installed']);self.assertFalse(disk['choice_eligible'])
        self.assertTrue(disk['pending']);self.assertEqual(disk['linked_ram'],0)
        binding=disk['native_binding'];code=(out/'console_disk_native/code.bin').read_bytes()
        self.assertEqual(binding,json.loads((out/'console_disk_native/binding.json').read_bytes()))
        self.assertEqual(sha256(code),binding['sha256']);self.assertEqual(len(code),binding['bytes'])
        for path,digest in binding['sources'].items():self.assertEqual(sha256((ROOT/path).read_bytes()),digest,path)
        self.assertFalse(binding['installed']);self.assertFalse(binding['native_execution_tested'])
        self.assertLessEqual(len(code),binding['planned_memory']['code']['bytes'])
        # Verify the assembled bridges, including o32 argument space, all full
        # register stores/loads, HI/LO, and the nonstandard t6 return. This is
        # structural checking, not execution of MIPS instructions.
        import struct
        for name in ('af_v3_qd_wdm_bridge','af_v3_qd_ram_bridge'):
            at=binding['compiled']['symbols'][name]-binding['linked_ram']
            raw=code[at:at+308];words=struct.unpack('>77I',raw)
            self.assertEqual(words[0],0x27BDFEE0)
            regs=set(range(1,32))-{29}
            for reg in regs:
                self.assertIn(0xFC000000|(29<<21)|(reg<<16)|(16+reg*8),words)
                self.assertIn(0xDC000000|(29<<21)|(reg<<16)|(16+reg*8),words)
            self.assertEqual(words[32:38],(0x27A80120,0xFFA800F8,0x00004010,
                0xFFA80110,0x00004012,0xFFA80118))
            self.assertEqual(words[41:45],(0xDFA80110,0x01000011,0xDFA80118,0x01000013))
            self.assertEqual(words[-2:],(0x01C00008,0x27BD0120))


if __name__=='__main__':unittest.main()
