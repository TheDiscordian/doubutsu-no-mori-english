"""Current V3 translation integration, preserved imports, and corrected empty output."""
import copy
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_VROM,apply_ups,by_vrom,sha256
import letter_names as names
from v3_asset_loader import BLOB,MODULE,STARTUP,CONFIG
from v3_furniture_install import inputs,reuse_resource_tail
import v3_optional_composition as composer
import v3_translation_updates as updates
from tests import test_v3_browser_composition as browser_tests

OUTPUT=ROOT/os.environ.get('V3_TRANSLATION_BUILD','build/v3-translation-headers-02')


class TranslationHeaderHostTests(unittest.TestCase):
    def test_complete_original_and_extended_editor_names(self):
        with tempfile.TemporaryDirectory(prefix='v3-translation-headers-') as directory:
            for count in (216,238):
                target=str(Path(directory)/f'check-{count}')
                subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O1','-g',
                    '-DAF_MUSEUM_HEADER',f'-DAF_LETTER_NPC_COUNT={count}u',
                    '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                    str(ROOT/'overlays/letter_names/names.c'),str(ROOT/'tests/letter_names_check.c'),
                    '-o',target],check=True,capture_output=True,timeout=30)
                subprocess.run([target],check=True,capture_output=True,timeout=10)


@unittest.skipUnless((OUTPUT/'build-lock.json').is_file(),'Current corrected V3 cartridge required')
class TranslationIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pin=(composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI)
        composer.use_build_lock(OUTPUT/'build-lock.json')
        cls.base,cls.report=composer.inputs()
        cls.old,cls.prior=inputs(OUTPUT/'base-lock.json')
        cls.catalog=composer.catalogue(cls.base,cls.report)

    @classmethod
    def tearDownClass(cls):
        composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=cls.pin

    def test_complete_resource_retention_bounds_and_reconstructible_patch(self):
        before,after=by_vrom(self.old),by_vrom(self.base)
        changed={names.NEW_VROM,names.NEW_RELOC,names.OWNER,MODULE,BLOB,0x19D40}
        self.assertEqual(set(before),set(after))
        for v in set(after)-changed:
            self.assertEqual(before[v].extract(self.old),after[v].extract(self.base),hex(v))
        self.assertEqual(before[CODE_VROM].extract(self.old),after[CODE_VROM].extract(self.base))
        old_board,new_board=(f[names.NEW_VROM].extract(r) for f,r in ((before,self.old),(after,self.base)))
        at=names.HEADER-names.RAM
        self.assertEqual(old_board[:at],new_board[:at])
        self.assertEqual(old_board[at+4:],new_board[at+4:len(old_board)])
        self.assertEqual(new_board[0x1FF8:0x1FFC],bytes.fromhex('2CC200EE'))
        fixed=(ROOT/updates.BASELINE['path']).read_bytes()
        equivalent=bytearray(by_vrom(fixed)[names.NEW_VROM].extract(fixed))
        # The compiler emits Museum as immediate stores, not a string literal.
        for bound in (0x1FF8,0x2CF0):
            self.assertEqual(struct.unpack_from('>I',equivalent,bound)[0],0x2CC200D8)
            struct.pack_into('>I',equivalent,bound,0x2CC200EE)
        self.assertEqual(new_board,equivalent)
        update=self.report['translation_updates']
        self.assertEqual(len(new_board)-len(old_board),1536)
        self.assertEqual(update['additional_pool_bytes'],0)
        self.assertFalse(update['delivery_code_changed'])
        self.assertFalse(update['saved_format_changed'])
        self.assertEqual(self.report['save_runtime'],self.prior['save_runtime'])
        self.assertEqual(self.report['equipment_resources'],self.prior['equipment_resources'])
        old_owner,new_owner=(f[names.OWNER].extract(r) for f,r in ((before,self.old),(after,self.base)))
        at=names.OWNER_AT
        self.assertEqual(old_owner[:at],new_owner[:at])
        self.assertEqual(old_owner[at+16:],new_owner[at+16:])
        self.assertEqual(struct.unpack_from('>4I',new_owner,at),
            (names.NEW_VROM,names.NEW_VROM+len(new_board),names.RAM,names.RAM+len(new_board)))
        old_module,new_module=(f[MODULE].extract(r) for f,r in ((before,self.old),(after,self.base)))
        restored=bytearray(new_module)
        for at,end in ((0x90,0x100),(updates.museum.NAME_ENTRY-updates.MODULE_RAM,updates.museum.NAME_ENTRY-updates.MODULE_RAM+8),
                       (updates.READER_BOUND,updates.READER_BOUND+4),(STARTUP,CONFIG+16)):
            restored[at:end]=old_module[at:end]
        self.assertEqual(restored,old_module)
        self.assertEqual(struct.unpack_from('>I',new_module,updates.READER_BOUND)[0],0x2CC200EE)
        blob=after[BLOB].extract(self.base)
        self.assertEqual(sha256(blob),self.report['blob_sha256'])
        retained,tail=reuse_resource_tail(self.base,self.report,blob)
        self.assertGreater(tail['reused_bytes'],0)
        for row in self.report['shared_runtime_refresh']['changed_owner_moves']:
            self.assertLessEqual(row['blob_offset']+row['bytes'],len(retained))
            self.assertEqual(after[row['vrom']].extract(self.base),blob[row['blob_offset']:row['blob_offset']+row['bytes']])
        native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(native,(OUTPUT/'asset-loader.ups').read_bytes()),self.base)
        for path,digest in update['sources'].items():
            self.assertEqual(sha256((ROOT/path).read_bytes()),digest,path)

    def test_reader_and_baseline_reject_changed_inputs(self):
        native=(ROOT/'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
        fixed=(ROOT/updates.BASELINE['path']).read_bytes()
        old_module=by_vrom(native)[MODULE].extract(native)
        fixed_module=by_vrom(fixed)[MODULE].extract(fixed)
        gate=(OUTPUT/'translation-reader/gate.bin').read_bytes()
        current=by_vrom(self.old)[MODULE].extract(self.old)
        valid=updates.patch_reader(current,gate,old_module,fixed_module)
        self.assertEqual(struct.unpack_from('>I',valid,updates.READER_BOUND)[0],0x2CC200EE)
        for at in (0x90,updates.READER_BOUND,updates.museum.NAME_ENTRY-updates.MODULE_RAM+12):
            damaged=bytearray(current);damaged[at]^=1
            with self.assertRaises(ValueError):updates.patch_reader(damaged,gate,old_module,fixed_module)
        with self.assertRaises(ValueError):updates.patch_reader(current,bytes([gate[0]^1])+gate[1:],old_module,fixed_module)
        for key,value in (('path','build/other.z64'),('sha256','0'*64),('build','V2-11')):
            damaged=copy.deepcopy(self.report);damaged['translation_baseline'][key]=value
            with self.assertRaises(ValueError):composer.stable_reference(damaged)

    def test_selected_and_empty_outputs_keep_the_fix(self):
        selection=composer.resolve(self.catalog,[])
        empty,_,blob=composer.compose(self.base,self.report,self.catalog,selection)
        self.assertIsNone(blob)
        self.assertEqual(sha256(empty),updates.BASELINE['sha256'])
        self.assertEqual(composer.compose(self.base,self.report,self.catalog,
            composer.resolve(self.catalog,list(self.catalog)))[0],self.base)
        keys=['GAFE01-r0/villager/00EB','GAFE01-r0/item/2255']
        result,_,_=composer.compose(self.base,self.report,self.catalog,composer.resolve(self.catalog,keys))
        files,base_files=by_vrom(result),by_vrom(self.base)
        for v in (names.NEW_VROM,names.NEW_RELOC,names.OWNER):
            self.assertEqual(files[v].extract(result),base_files[v].extract(self.base))
        module=files[MODULE].extract(result)
        self.assertEqual(struct.unpack_from('>I',module,updates.READER_BOUND)[0],0x2CC200EE)

    def test_browser_matches_current_corrected_profiles(self):
        from v3_browser_composition import rules
        self.plan=rules(self.base,self.report)
        self.assertEqual(self.plan['stable_sha256'],updates.BASELINE['sha256'])
        browser_tests.BrowserCompositionTests.test_browser_output_matches_authoritative_composition_for_representative_profiles(self)


if __name__=='__main__':unittest.main()
