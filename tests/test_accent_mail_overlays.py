"""Accent hooks preserve complete prefixes, native ownership, and prior translations."""
from copy import deepcopy
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256
from accent_mail_overlays import dispatch,FONT_POINTER
from accent_mail_overlay_profile import validate,wrap
from accent_mail_font import PROFILE
from accent_items_install import verify_installation


class AccentOverlayTests(unittest.TestCase):
    def test_all_compiled_profiles_and_independent_relocations_retain_prefixes(self):
        for kind in ('creator','notice','event'):
            directory=ROOT/'build/accent-mail-overlays'/kind
            data=(directory/'overlay.bin').read_bytes();reloc=(directory/'relocation.bin').read_bytes()
            extension=json.loads((directory/'overlay.json').read_text());report=wrap(extension)
            old,oldrel,previous,spec=validate(kind,data,reloc,report)
            self.assertEqual(sha256(old),extension['previous_sha256'])
            self.assertEqual(sha256(oldrel),extension['previous_relocation_sha256'])
            self.assertEqual((len(data)-len(old),len(data)),(2256 if kind!='event' else 0,spec.resident_bytes))
            for file in ('overlay.bin','relocation.bin','overlay.json'):
                self.assertEqual((directory/file).read_bytes(),(ROOT/'build/accent-mail-overlays-rebuild'/kind/file).read_bytes())
            bad=bytearray(data);bad[extension['patches'][0]['at']]^=1
            with self.assertRaises(ValueError):validate(kind,bytes(bad),reloc,{**report,'overlay_sha256':sha256(bad)})
            forged=deepcopy(report);forged['accent_mail']['font_pointer']+=4
            with self.assertRaises(ValueError):validate(kind,data,reloc,forged)

    def test_argument_preserving_tail_bridges_use_the_actual_owned_font_pointer(self):
        for name in ('af_accent_capture_set','af_accent_mail_generate'):
            words=struct.unpack('>10I',dispatch(name))
            offset=words[1]&65535;offset-=65536 if offset&32768 else 0
            self.assertEqual(((words[0]&65535)<<16)+offset,FONT_POINTER)
            self.assertEqual(words[2:4],(0x13200004,0))
            self.assertEqual(words[4],0x27390000|PROFILE['symbols'][name])
            self.assertEqual(words[5:],(0x03200008,0,0x03E00008,0x1025,0))

    def test_actual_cartridge_retains_previous_files_and_all_new_consumers(self):
        directory=ROOT/'build/accent-items-pilot'
        built=(directory/'animal-forest-halfwidth.z64').read_bytes()
        report=json.loads((directory/'build.json').read_text())
        native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        names=verify_installation(built,native,report)
        self.assertEqual(len(names),8)
        self.assertEqual(report['accent_items']['submenu_pool_growth'],0)
        self.assertEqual(report['accent_items']['resident_module_growth'],0)
        bad=deepcopy(report);bad['accent_items']['source_ids'].pop()
        with self.assertRaises(ValueError):verify_installation(built,native,bad)


if __name__=='__main__':unittest.main()
