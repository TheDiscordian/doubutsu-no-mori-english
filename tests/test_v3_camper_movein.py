"""Installed saved-camper exclusion without changing other candidate rules."""
import copy
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,DMA_START,DMA_END,by_vrom,sha256,n64_checksum
from v3_asset_loader import BLOB,MODULE,CONFIG
import v3_camper_movein as runtime
OUTPUT=ROOT/'build/v3-camper-movein-runtime-02'


class CamperMoveinTests(unittest.TestCase):
    def test_sanitized_candidate_and_transfer_guards(self):
        with tempfile.TemporaryDirectory(prefix='af-camper-movein-') as directory:
            binary=Path(directory)/'test'
            subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                str(ROOT/'tests/v3_camper_movein_test.c'),str(ROOT/'overlays/v3/camper_movein.c'),
                '-o',str(binary)],check=True,capture_output=True,text=True,timeout=30)
            result=subprocess.run([str(binary)],capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('pass:',result.stdout)

    def test_complete_current_native_and_resident_owner_retention(self):
        base=(runtime.BASE/'animal-forest-v3-asset-loader.z64').read_bytes()
        prior=json.loads((runtime.BASE/'build.json').read_bytes())
        rom=(OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        report=json.loads((OUTPUT/'build.json').read_bytes());guard=report['camper_movein']
        files,old=by_vrom(rom),by_vrom(base)
        helper=(OUTPUT/'camper_movein/code.bin').read_bytes()
        blob,code,rebuilt=runtime.install(base,helper,guard['code'],prior)
        self.assertEqual(code,files[CODE_VROM].extract(rom))
        actual=bytearray(files[BLOB].extract(rom));struct.pack_into('>I',actual,4,76)
        self.assertEqual(blob,actual);self.assertEqual(json.loads(json.dumps(rebuilt)),guard)
        self.assertEqual(len(helper),252);self.assertLessEqual(runtime.CODE+len(helper),runtime.LIMIT)
        self.assertEqual(rom[DMA_START:DMA_END],base[DMA_START:DMA_END])
        changed={v for v in files if files[v].extract(rom)!=old[v].extract(base)}
        self.assertEqual(changed,{BLOB,MODULE,CODE_VROM})
        for row in guard['hooks']:
            target=blob if row['address']>=0x80460000 else code
            at=row['address']-(0x80460000 if target is blob else CODE_RAM)
            target[at:at+4]=bytes.fromhex(row['before'])
        blob[runtime.CODE:runtime.CODE+len(helper)]=bytes(len(helper))
        self.assertEqual(blob,old[BLOB].extract(base));self.assertEqual(code,old[CODE_VROM].extract(base))
        self.assertEqual(struct.unpack_from('>4I',files[MODULE].extract(rom),CONFIG),
            (BLOB,0xC000,zlib.crc32(files[BLOB].extract(rom)[:0xC000]),77))
        self.assertEqual(struct.unpack_from('>2I',rom,0x10),n64_checksum(rom))
        self.assertEqual(sha256(rom),report['output_sha256'])
        self.assertFalse(guard['web_patcher_enabled']);self.assertFalse(guard['saved_format_changed'])

    def test_changed_source_helper_and_native_bindings_rejected(self):
        base=(runtime.BASE/'animal-forest-v3-asset-loader.z64').read_bytes()
        prior=json.loads((runtime.BASE/'build.json').read_bytes())
        compiled=json.loads((OUTPUT/'build.json').read_bytes())['camper_movein']['code']
        helper=(OUTPUT/'camper_movein/code.bin').read_bytes()
        with self.assertRaises(ValueError): runtime.install(base,helper[:-4],compiled,prior)
        changed=copy.deepcopy(compiled);changed['symbols']['native_event_save']+=4
        with self.assertRaises(ValueError): runtime.install(base,helper,changed,prior)


if __name__=='__main__': unittest.main()
