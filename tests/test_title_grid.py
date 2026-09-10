"""Combine the reviewed grid with the unchanged English title and warning."""
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,sha256,apply_ups,CODE_VROM
from title_overlay import build,ACTOR,RELOC,ASSETS,NEW_ACTOR,NEW_RELOC
from title_memory import BOOT,HELPER,HELPER_END
from aflib import CODE_RAM
from keyboard_grid_overlay import verify_owned_parts


@unittest.skipUnless((ROOT/'build/title-grid-combined-01/preview.json').is_file(),'Local title/grid candidate required')
class TitleGridTests(unittest.TestCase):
    def test_combined_patch_retains_complete_grid_and_identical_title_implementation(self):
        self.check_combination('keyboard-grid-01', 'title-grid-combined-01',
            'f2c46b98e4d5748d39bcd17ce697f50c4f6dbeae6b560e2ba4851ad43b46ec8d')

    @unittest.skipUnless((ROOT/'build/title-nookington-combined-01/preview.json').is_file(),
                         'Local Nookington/title candidate required')
    def test_nookington_combination_retains_building_loader_and_unchanged_title(self):
        self.check_combination('nookington-sign-02', 'title-nookington-combined-01',
            '76757a029aca2d0564daff08e3f2a790bf572b66efb6a2a84fee8f26a8acf4c4')

    @unittest.skipUnless((ROOT/'build/title-police-combined-01/preview.json').is_file(),
                         'Local police/title candidate required')
    def test_police_combination_retains_english_signs_and_corrected_grid_labels(self):
        self.check_combination('police-artwork-01', 'title-police-combined-01',
            'aa0978ff0efd992face36276e02e867f64c618b1469326ad4904013793e71f95')

    @unittest.skipUnless((ROOT/'build/title-redd-combined-01/preview.json').is_file(),
                         'Local Redd/title candidate required')
    def test_redd_combination_retains_summer_colours_and_all_earlier_artwork(self):
        self.check_combination('redd-artwork-01', 'title-redd-combined-01',
            'b37f9ecf3ccde2344df6c6cad8e39baea73a7c2eaa6ea3f7cad865eeb8aebc9b')

    @unittest.skipUnless((ROOT/'build/title-cursor-combined-01/preview.json').is_file(),
                         'Local corrected cursor/title candidate required')
    def test_cursor_combination_retains_corrected_commands_and_complete_artwork(self):
        self.check_combination('keyboard-grid-cursor-01', 'title-cursor-combined-01',
            'b42b63b0c59b9e947338dc3ac477f7c8562dd6cbd9dddbdc3831ca49622b63c6')

    @unittest.skipUnless((ROOT/'build/title-tune-combined-01/preview.json').is_file(),
                         'Local notice/tune/title candidate required')
    def test_tune_combination_retains_notice_controls_and_all_earlier_artwork(self):
        self.check_combination('tune-artwork-01', 'title-tune-combined-01',
            '41282aa2c64a946a7588cc0434a8ddf1f3b51727b52205ae708b71f16c0b4cca')

    @unittest.skipUnless((ROOT/'build/title-service-combined-01/preview.json').is_file(),
                         'Local catalogue/service/title candidate required')
    def test_service_combination_retains_mail_repayment_and_catalogue_artwork(self):
        self.check_combination('service-artwork-01', 'title-service-combined-01',
            '5353187111c528ecb88e2efa5606e23dfd3a05adc10bb4d1ae16691c31132258')

    @unittest.skipUnless((ROOT/'build/title-birthday-combined-01/preview.json').is_file(),
                         'Local English birthday/title candidate required')
    def test_birthday_combination_retains_renderer_and_complete_prior_artwork(self):
        self.check_combination('birthday-screen-01', 'title-birthday-combined-01',
            '4849a83ebcff09fa188cfbe4f54a66f2691769c98f4a1dc787b48417e07fc9f7')

    @unittest.skipUnless((ROOT/'build/title-pak-combined-01/preview.json').is_file(),
                         'Local English Controller Pak/title candidate required')
    def test_pak_combination_retains_labels_birthday_and_complete_prior_artwork(self):
        self.check_combination('controller-pak-artwork-01', 'title-pak-combined-01',
            'd74b8999ed97206f9358597d66de105677af41ee4d4dbd9fcdbff467e38e23d4')

    @unittest.skipUnless((ROOT/'build/title-submenu-combined-01/preview.json').is_file(),
                         'Local embedded menu English/title candidate required')
    def test_submenu_combination_retains_warning_storage_pool_and_all_prior_work(self):
        self.check_combination('submenu-text-01', 'title-submenu-combined-01',
            'be9b51bada53c9fc8a3abd6cc53ae054689100e9bee8a595334d5da183febe35')

    @unittest.skipUnless((ROOT/'build/title-gyroid-service-combined-01/preview.json').is_file(),
                         'Local gyroid service English/title candidate required')
    def test_gyroid_service_combination_retains_safe_buffer_and_all_prior_work(self):
        self.check_combination('gyroid-service-01', 'title-gyroid-service-combined-01',
            'da66a789341307c625da130ae11e20609b9a023fca82712f303fc59fe95deb94')

    @unittest.skipUnless((ROOT/'build/title-nookington-details-combined-01/preview.json').is_file(),
                         'Local complete Nookington/title candidate required')
    def test_nookington_details_combination_retains_complete_menu_and_title_work(self):
        self.check_combination('nookington-details-01', 'title-nookington-details-combined-01',
            '172069ba24d2f6a907006222b5a0743d34dffaa7c319b740dbba21ba8edbb9b7')

    @unittest.skipUnless((ROOT/'build/title-dump-combined-01/preview.json').is_file(),
                         'Local English dump/title candidate required')
    def test_dump_combination_retains_complete_nookington_and_menu_work(self):
        self.check_combination('dump-artwork-01', 'title-dump-combined-01',
            '9f734ba89b2456e5dce7b79c6cafe33b3017dd22e8d9cec02e5eb70c1533b560')

    def check_combination(self, baseline, output, expected_sha):
        native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        base=(ROOT/'build'/baseline/'animal-forest-halfwidth.z64').read_bytes()
        previous=json.loads((ROOT/'build'/baseline/'build.json').read_text())
        folder=ROOT/'build'/output
        image=(folder/'animal-forest-title-preview.z64').read_bytes()
        report=json.loads((folder/'preview.json').read_text());files=by_vrom(image)
        built,patch,evidence=build(native,base,previous,
            (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes(),
            files[NEW_ACTOR].extract(image),files[NEW_RELOC].extract(image),report['actor'])
        self.assertEqual(built,image);self.assertEqual(evidence,report)
        self.assertEqual(sha256(image),expected_sha)
        self.assertEqual(apply_ups(native,patch),image)
        self.assertEqual(report['baseline_sha256'],previous['output_sha256'])
        verify_owned_parts(image,native,previous['keyboard_grid'],previous['apology_input'])
        prior=by_vrom(base)
        for address,entry in prior.items():
            if address not in (ACTOR,RELOC,ASSETS,CODE_VROM,BOOT,0x19D40):
                self.assertEqual(files[address].extract(image),entry.extract(base),f'{address:08X}')
        title=(ROOT/'build/title-combined-01/animal-forest-title-preview.z64').read_bytes()
        known=by_vrom(title)
        for address in (NEW_ACTOR,NEW_RELOC,ASSETS,BOOT):
            self.assertEqual(files[address].extract(image),known[address].extract(title))
        self.assertEqual(files[CODE_VROM].extract(image)[HELPER-CODE_RAM:HELPER_END-CODE_RAM],
                         known[CODE_VROM].extract(title)[HELPER-CODE_RAM:HELPER_END-CODE_RAM])
        self.assertEqual(report['memory']['required_ram_bytes'],0x800000)
        self.assertEqual(report['memory']['ordinary_heap_end'],0x80400000)


if __name__=='__main__':unittest.main()
