"""Retain corrected native C source validation after actual cartridge DMA."""

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256
from native_species_scenario import scenario

RUN = ROOT/'build/smoke-design-species-01'
PLAN = ROOT/'build/design-species-scenario.json'
BUILD = ROOT/'build/design-items-pilot'


@unittest.skipUnless((RUN/'results.json').is_file(), 'Completed corrected native word evidence required')
class NativeSpeciesResultsTests(unittest.TestCase):
    def test_actual_dma_relocation_init_rejection_recovery_and_all_restoration(self):
        rows = json.loads((RUN/'results.json').read_text())
        self.assertEqual(sha256((RUN/'results.json').read_bytes()),
                         '90b352c8d53848c09572cfedcb19389255190c6079829dadb38aaf37fce4ece5')
        self.assertEqual(len(rows), 58)
        self.assertFalse(any('error' in r or r.get('assertion') == 'failed' for r in rows))
        calls = [r for r in rows if 'test_only_function_call' in r]
        checks = [r for r in rows if r.get('assertion') == 'passed']
        self.assertEqual((len(calls), len(checks)), (13, 22))
        self.assertTrue(all(r['stack_restored'] for r in calls))
        self.assertEqual([r['test_only_function_call'] for r in calls[:6]],
                         ['8009C0C0', '8009BFC0', '80026B44', '8002B9C0', '8002FE00', '80034CE0'])
        self.assertEqual(calls[2]['return_value'], 0)
        self.assertEqual([r['return_value'] for r in calls[6:11]], [1, 1, 0, 0, 1])
        labels = {r.get('species_check') for r in checks}
        self.assertTrue({'complete cartridge image and relocations',
                         'complete native relocation agrees with independent model',
                         'corrected profile publishes complete descriptor',
                         'complete herabuna field with unaligned edge guards',
                         'wrong profile retains prior descriptor', 'damaged words retain prior descriptor',
                         'restored profile recovers', 'complete creator and resources restored',
                         'entire save unchanged', 'no leaked letter session'} <= labels)
        self.assertEqual(sum(r.get('species_check') == 'allocation or stack guard' for r in checks), 8)
        result = next(r for r in rows if 'native_species_cartridge_words' in r)
        self.assertTrue(result['cartridge_dma_and_relocation'])
        self.assertFalse(result['creator_code_uploaded']); self.assertFalse(result['complete_letter_delivery_tested'])
        self.assertTrue(any(r.get('species_heap_restored') for r in rows))
        self.assertTrue(any(r.get('loaded_state') == 'test.bs1' for r in rows))
        self.assertEqual(checks[-1]['read'], ['8019B200', 12])
        self.assertEqual(checks[-1]['data'], bytes(12).hex())
        self.assertTrue(rows[-1]['graceful_shutdown'])
        info = json.loads((RUN/'run.json').read_text())
        self.assertEqual(info['rom_sha256'], sha256((BUILD/'animal-forest-halfwidth.z64').read_bytes()))
        self.assertEqual(info['scenario_sha256'], sha256(PLAN.read_bytes()))
        self.assertEqual(info['audio'], 'disabled'); self.assertEqual(info['seed_files'], [])
        for key in ('initial_screenshot', 'expansion_pak', 'allow_test_flash_write', 'allow_test_pak_write'):
            self.assertFalse(info[key])
        for name, digest in (
                ('test.bs1', '8e58eabbe3f6b6c3c7d40e638274c2f80e05431ee0ddd84ef778d6c5990fc951'),
                ('test.flash', 'b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260'),
                ('test.pak', 'ab2a6e04fd3ceb36594f1216c888a1b8bd0a3ba0a94f715a7c7601e98c49ec51')):
            self.assertEqual(sha256((RUN/name).read_bytes()), digest)

    def test_plan_reconstructs_and_rejects_changed_rom_or_word_profile(self):
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        report = json.loads((BUILD/'build.json').read_text())
        self.assertEqual(scenario(native, built, report), json.loads(PLAN.read_text()))
        self.assertEqual(sha256(PLAN.read_bytes()), 'ebec9ded7f02e9695a60e71a012c1755b59789138148fe55a0dbb61fa5765fb2')
        changed = bytearray(built); changed[-1] ^= 1
        with self.assertRaises(ValueError): scenario(native, bytes(changed), report)
        wrong = deepcopy(report)
        wrong['runtime_module']['npc_mail_loader']['overlay']['word_sha256'] = '0'*64
        with self.assertRaises(ValueError): scenario(native, built, wrong)


if __name__ == '__main__': unittest.main()
