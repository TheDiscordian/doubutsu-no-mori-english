"""Focused complete world-label consumer and shared font checks."""
import copy
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom, sha256, apply_ups, CODE_VROM
from extended_font_cartridge import validate, relocate, mail_capability
import world_names as w
OUT=ROOT/'build/world-names-font'
BUILD=ROOT/'build/world-names-pilot'
OLD=ROOT/'build/tag-descriptions-pilot'


class WorldCoreTests(unittest.TestCase):
    def test_storage_failure_reset_geometry_and_installation_under_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='af-world-host-') as tmp:
            target=str(Path(tmp)/'check')
            subprocess.run(['gcc','-std=c99','-Wall','-Wextra','-Werror','-O1','-g',
                            '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                            '-DAF_GLYPH_HOST_TEST','-I'+str(ROOT/'overlays/extended_font'),
                            str(ROOT/'overlays/extended_font/font.c'),
                            str(ROOT/'overlays/world_names/names.c'),
                            str(ROOT/'overlays/world_names/install.c'),
                            str(ROOT/'tests/world_names_check.c'),'-o',target],
                           check=True,capture_output=True,timeout=30)
            subprocess.run([target,str(ROOT/'build/mail-glyphs/glyphs.bin')],
                           check=True,capture_output=True,timeout=10)


@unittest.skipUnless((OUT/'font.json').is_file(),'Compiled world font required')
class WorldArtifactTests(unittest.TestCase):
    def test_rehashed_code_and_altered_state_metadata_are_rejected(self):
        data=(OUT/'font.bin').read_bytes();reloc=(OUT/'relocation.bin').read_bytes()
        report=json.loads((OUT/'font.json').read_text())
        for at in (0,w.SYMBOLS['af_world_load'],w.SYMBOLS['af_world_draw']):
            altered=bytearray(data);altered[at]^=1
            with self.assertRaises(ValueError): validate(altered,reloc,{**report,'sha256':sha256(altered)})
        altered=copy.deepcopy(report);altered['symbols']['world_name']-=4
        with self.assertRaises(ValueError): validate(data,reloc,altered)

    def test_complete_resources_old_profiles_and_relocated_hooks(self):
        data=(OUT/'font.bin').read_bytes();reloc=(OUT/'relocation.bin').read_bytes()
        report=json.loads((OUT/'font.json').read_text());validate(data,reloc,report)
        self.assertEqual(mail_capability(OUT),sha256(data+reloc))
        old=ROOT/'build/mail-font-cartridge'
        old_report=json.loads((old/'font.json').read_text())
        old_data=(old/'font.bin').read_bytes()
        validate(old_data,(old/'relocation.bin').read_bytes(),old_report)
        self.assertEqual(data[report['symbols']['af_font_resource']:][:1600],
                         old_data[old_report['symbols']['af_font_resource']:][:1600])
        for base in (0x801A0010,0x802F8010,0x803F0000):
            relocated=relocate(data,reloc,base)
            at=report['symbols']['world_hooks']
            for i,(address,(old,target)) in enumerate(w.HOOKS.items()):
                row=struct.unpack_from('>4I',relocated,at+i*16)
                self.assertEqual(row,(address,old,0 if isinstance(target,str) else target,
                    base+report['symbols'][target] if isinstance(target,str) else 0))

    def test_native_region_and_full_name_dependencies_reject_changes(self):
        native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        built=(OLD/'animal-forest-halfwidth.z64').read_bytes();files=by_vrom(built)
        report=json.loads((OLD/'build.json').read_text())['runtime_module']
        from runtime_layout import MODULE_VROM
        module=files[MODULE_VROM].extract(built)
        code=files[CODE_VROM].extract(built)
        additions={0x02A00000:files[0x02A00000].extract(built)}
        w.dependencies(native,code,module,additions,report)
        for address in w.HOOKS:
            altered=bytearray(code);altered[address-w.CODE_RAM]^=1
            with self.assertRaises(ValueError): w.dependencies(native,altered,module,additions,report)
        with self.assertRaises(ValueError): w.dependencies(native,code,module,{},report)


@unittest.skipUnless((BUILD/'build.json').is_file(),'Complete world-name cartridge required')
class WorldCartridgeTests(unittest.TestCase):
    def test_full_patch_previous_resources_and_name_consumers_retained(self):
        native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        built=(BUILD/'animal-forest-halfwidth.z64').read_bytes()
        old=(OLD/'animal-forest-halfwidth.z64').read_bytes()
        report=json.loads((BUILD/'build.json').read_text())
        from runtime_layout import MODULE_VROM
        from extended_font_cartridge import verify_configuration
        from catalogue_names import verify_shared_parts
        files,previous=by_vrom(built),by_vrom(old)
        self.assertEqual(set(files),set(previous))
        for v in files:
            if v not in (0x19D40,MODULE_VROM,0x03400000):
                self.assertEqual(files[v].extract(built),previous[v].extract(old),hex(v))
        module=files[MODULE_VROM].extract(built);before=previous[MODULE_VROM].extract(old)
        self.assertEqual(module[:0x68],before[:0x68]);self.assertEqual(module[0x88:],before[0x88:])
        verify_configuration(module,files[0x03400000].extract(built),report['runtime_module'])
        verify_shared_parts(built,native,report['runtime_module'],report['catalogue_names'])
        self.assertEqual(apply_ups(native,(BUILD/'animal-forest-halfwidth.ups').read_bytes()),built)

    def test_existing_complete_names_receive_no_duplicate_translation_credit(self):
        from translation_progress import measure
        native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        rows=[]
        for path in (OLD,BUILD):
            report=json.loads((path/'build.json').read_text())
            rows.append(measure(native,(path/'animal-forest-halfwidth.z64').read_bytes(),report).rows)
        self.assertEqual(rows[0],rows[1])


if __name__=='__main__': unittest.main()
