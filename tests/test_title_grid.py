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
        native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        base=(ROOT/'build/keyboard-grid-01/animal-forest-halfwidth.z64').read_bytes()
        previous=json.loads((ROOT/'build/keyboard-grid-01/build.json').read_text())
        folder=ROOT/'build/title-grid-combined-01'
        image=(folder/'animal-forest-title-preview.z64').read_bytes()
        report=json.loads((folder/'preview.json').read_text());files=by_vrom(image)
        built,patch,evidence=build(native,base,previous,
            (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes(),
            files[NEW_ACTOR].extract(image),files[NEW_RELOC].extract(image),report['actor'])
        self.assertEqual(built,image);self.assertEqual(evidence,report)
        self.assertEqual(sha256(image),'f2c46b98e4d5748d39bcd17ce697f50c4f6dbeae6b560e2ba4851ad43b46ec8d')
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
