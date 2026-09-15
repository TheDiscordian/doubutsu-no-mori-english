"""Current English event-owner extension, complete relocations, and retries."""
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
import v3_campsite_manager as runtime
OUTPUT=ROOT/'build/v3-campsite-manager-runtime-02'


class ManagerTests(unittest.TestCase):
    def test_sanitized_native_adapter_lifecycle_and_failure_retries(self):
        with tempfile.TemporaryDirectory(prefix='af-camper-manager-') as directory:
            binary=Path(directory)/'test'
            compile_result=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                str(ROOT/'tests/v3_campsite_manager_test.c'),str(ROOT/'overlays/v3/campsite_manager.c'),
                str(ROOT/'overlays/v3/campsite_event.c'),'-o',str(binary)],capture_output=True,text=True,timeout=30)
            self.assertEqual(compile_result.returncode,0,compile_result.stderr)
            result=subprocess.run([str(binary)],capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('pass:',result.stdout)

    def test_complete_current_english_owner_and_native_control_relocation(self):
        base=(runtime.BASE/'animal-forest-v3-asset-loader.z64').read_bytes()
        rom=(OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        report=json.loads((OUTPUT/'build.json').read_bytes());manager=report['campsite_manager']
        files,old=by_vrom(rom),by_vrom(base)
        data,reloc,rebuilt=runtime.install(base,(OUTPUT/'manager/code.bin').read_bytes(),manager['code'])
        self.assertEqual(data,files[runtime.VROM].extract(rom))
        self.assertEqual(reloc,files[runtime.RELOC].extract(rom))
        self.assertEqual((rebuilt['control_count'],rebuilt['retained_relocations']),(29,433))
        restored=bytearray(data[:runtime.SIZE])
        for row in manager['hooks']: struct.pack_into('>I',restored,row['address']-runtime.RAM,row['before'])
        self.assertEqual(restored,old[runtime.VROM].extract(base))
        changed={v for v in files if files[v].extract(rom)!=old[v].extract(base)}
        self.assertEqual(changed,{0x19D40,BLOB,MODULE,CODE_VROM,runtime.VROM,runtime.RELOC})
        directory=bytearray(rom[DMA_START:DMA_END])
        for vrom in (BLOB,runtime.VROM,runtime.RELOC):
            at=files[vrom].index*16
            directory[at:at+16]=base[DMA_START+at:DMA_START+at+16]
        self.assertEqual(directory,base[DMA_START:DMA_END])
        self.assertEqual(set(files),set(old));self.assertEqual(len(files),3389)
        code=bytearray(files[CODE_VROM].extract(rom)); at=runtime.METADATA-CODE_RAM
        self.assertEqual(code[at:at+32],bytes.fromhex(manager['metadata_after']))
        code[at:at+32]=bytes.fromhex(manager['metadata_before'])
        self.assertEqual(code,old[CODE_VROM].extract(base))
        for v in files:
            if v not in (BLOB,runtime.VROM,runtime.RELOC): self.assertEqual(files[v],old[v])
        self.assertEqual(files[runtime.RELOC].index,files[runtime.VROM].index+1)
        blob=files[BLOB].extract(rom); previous=old[BLOB].extract(base)
        self.assertEqual(blob[:4]+blob[8:len(previous)],previous[:4]+previous[8:])
        self.assertEqual(struct.unpack_from('>4I',files[MODULE].extract(rom),CONFIG),
            (BLOB,0xC000,zlib.crc32(blob[:0xC000]),76))
        self.assertEqual(struct.unpack_from('>II',rom,0x10),n64_checksum(rom))
        self.assertEqual(sha256(rom),report['output_sha256'])
        self.assertFalse(manager['web_patcher_enabled']);self.assertFalse(manager['acquisition_installed'])

    def test_changed_suffix_or_native_binding_is_rejected(self):
        base=(runtime.BASE/'animal-forest-v3-asset-loader.z64').read_bytes()
        report=json.loads((OUTPUT/'build.json').read_bytes())['campsite_manager']['code']
        suffix=(OUTPUT/'manager/code.bin').read_bytes()
        with self.assertRaises(ValueError): runtime.install(base,suffix[:-16],report)
        report['symbols']['native_get_save']+=4
        with self.assertRaises(ValueError): runtime.install(base,suffix,report)


if __name__=='__main__': unittest.main()
