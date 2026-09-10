"""The fresh seven-stage correction replay identifies every intermediate and final."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256, apply_ups
from rebuild_v1_fixes import FINAL_SHA, PATCH_SHA

OUT = ROOT/'build/v1-fixes-rebuild-01'


@unittest.skipUnless((OUT/'fixes.json').is_file(),'Complete correction replay required')
class CorrectionReplayTests(unittest.TestCase):
    def test_all_seven_stages_reproduce_the_retained_candidates(self):
        report=json.loads((OUT/'fixes.json').read_text())
        candidates=('v1-playtest-fixes-01','v1-editor-pixel-fix-03','v1-hud-label-fix-02',
                    'v1-notice-tune-fix-01','v1-inventory-money-fix-01','v1-letter-ui-fix-02',
                    'v1-keyboard-background-fix-01')
        self.assertEqual(len(report['stages']),len(candidates)); prior=report['baseline_sha256']
        for stage,candidate in zip(report['stages'],candidates):
            original=json.loads((ROOT/'build'/candidate/'fixes.json').read_text())
            self.assertEqual(stage['profile']['baseline_sha256'],prior)
            self.assertEqual(stage['profile']['output_sha256'],original['output_sha256'])
            self.assertEqual(stage['profile']['patch_sha256'],original['patch_sha256'])
            prior=stage['profile']['output_sha256']
        self.assertEqual(prior,FINAL_SHA)
        inputs={'tools/'+name+'.py' for name in ('aflib','rebuild_v1_fixes','title_start_fix',
            'editor_pixel_fix','hud_label_fix','notice_tune_fix','inventory_money_fix',
            'letter_ui_fix','keyboard_background_fix')}
        for stage in report['stages']:
            inputs.update(stage['profile'].get('sources',{}))
        for name in inputs:
            self.assertEqual(sha256((ROOT/name).read_bytes()),report['sources'][name],name)
        for stage in ('editor-pixels','letter-ui','keyboard-background'):
            self.assertTrue(list((OUT/stage).glob('*/image.elf')),stage)
        rom=(OUT/'animal-forest-title-preview.z64').read_bytes();patch=(OUT/'animal-forest-title-preview.ups').read_bytes()
        self.assertEqual(sha256(rom),FINAL_SHA);self.assertEqual(sha256(patch),PATCH_SHA)
        native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(native,patch),rom)
        self.assertTrue(report['complete_rebuild']);self.assertFalse(report['native_tests_run'])
        self.assertFalse(report['hardware_verified']);self.assertFalse(report['save_format_changed'])


if __name__=='__main__':unittest.main()
