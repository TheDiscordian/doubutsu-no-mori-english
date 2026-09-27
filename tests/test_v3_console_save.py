"""One shared donor comparison for console persistence, not emulator execution."""
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256
from v3_console_games import read_donor, build_bundle, persistence_contract, streaming_bundle
from tests.test_v3_player_exercise import complete_function


class ConsoleSaveTests(unittest.TestCase):
    def test_all_donor_games_players_scores_battery_and_disk(self):
        dol,archive=read_donor(ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso')
        report,blob=build_bundle(dol,archive)
        streaming,metadata,pool=streaming_bundle(report,blob,archive)
        layout=persistence_contract(dol)
        self.assertEqual((layout['players'],layout['player_bytes'],layout['all_player_bytes'],
                          layout['donor_container_bytes']),(4,1632,6528,6592))
        self.assertEqual(len(layout['functions']),11)
        source=(ROOT/'local/ac-decomp/src/static/Famicom/famicom_nesinfo.cpp').read_text()
        header=(ROOT/'local/ac-decomp/include/Famicom/famicom.h').read_text()
        functions=('update_highscore_raw','nesinfo_get_u16','nesinfo_get_u8','nesinfo_set_u16',
            'nesinfo_next_tag_raw','nesinfo_next_tag','print_stringn_lf','print_hex_lf',
            'calcSum','special_zelda','nesinfo_tag_process1','nesinfo_tag_process3',
            'nesinfo_update_highscore','highscore_setup_flags')
        donor='\n'.join(re.findall(r'^#define NESTAG_.*$',header,re.M))+'\n'
        donor+='\n'.join(complete_function(source,name) for name in functions)
        with tempfile.TemporaryDirectory(prefix='v3-console-save-') as temp:
            out=Path(temp)
            (out/'donor_console_save.inc').write_text(donor)
            (out/'games.bin').write_bytes(blob)
            (out/'metadata.bin').write_bytes(metadata);(out/'pool.bin').write_bytes(pool)
            flags=['-O1','-g','-Wall','-Wextra','-Werror','-fno-pie','-no-pie',
                   '-fsanitize=address,undefined','-fno-omit-frame-pointer']
            run=subprocess.run(['cc','-std=c11',*flags,'-c',str(ROOT/'overlays/v3/console_save.c'),
                                '-o',str(out/'core.o')],capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            run=subprocess.run(['cc','-std=c11',*flags,'-c',str(ROOT/'overlays/v3/console_image.c'),
                                '-o',str(out/'image.o')],capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            run=subprocess.run(['c++','-std=c++17',*flags,'-Wno-unused-function','-Wno-unused-parameter',
                '-Wno-unused-variable','-Wno-unused-but-set-variable','-I'+str(out),
                str(ROOT/'tests/v3_console_save_test.cpp'),
                str(out/'core.o'),str(out/'image.o'),'-o',str(out/'check')],capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            run=subprocess.run([str(out/'check'),str(out/'games.bin'),str(out/'metadata.bin'),str(out/'pool.bin')],capture_output=True,text=True,timeout=45)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            print(run.stdout.strip())

    def test_prepared_mips_core_matches_current_sources_without_install_claim(self):
        out=ROOT/'build/v3-console-games-prepared-06'
        report=json.loads((out/'games.json').read_text())
        core=report['persistence_core']
        self.assertEqual(core['sha256'],sha256((out/'console_save/code.bin').read_bytes()))
        for path,digest in core['sources'].items():
            self.assertEqual(digest,sha256((ROOT/path).read_bytes()),path)
        self.assertFalse(core['native_hooks_installed'])
        self.assertFalse(core['flash_storage_installed'])
        self.assertFalse(report['choice_eligible'])
        self.assertEqual(core['linked_ram'],0)
        previous=(ROOT/'build/v3-console-games-prepared-02/games.bin').read_bytes()
        self.assertEqual((out/'games.bin').read_bytes(),previous)
        stream=report['streaming'];loader=stream['loader']
        self.assertEqual(sha256((out/'games-metadata.bin').read_bytes()),stream['metadata_sha256'])
        self.assertEqual(sha256((out/'games-pool.bin').read_bytes()),stream['pool_sha256'])
        self.assertEqual(sha256((out/'console_image/code.bin').read_bytes()),loader['sha256'])
        self.assertLess(stream['metadata_bytes'],16384)
        self.assertEqual(stream['maximum_image_bytes'],524304)
        for path,digest in loader['sources'].items():self.assertEqual(digest,sha256((ROOT/path).read_bytes()),path)
        self.assertFalse(loader['native_hooks_installed'])


if __name__=='__main__':unittest.main()
