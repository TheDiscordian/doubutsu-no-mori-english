"""Current shared Nook code and compact checked destination bindings."""
import ctypes
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,sha256
from v3_asset_loader import BLOB
from v3_furniture_install import inputs
import v3_password_runtime as runtime
import v3_password_policy as policy

OUT=ROOT/os.environ.get('V3_NOOK_PASSWORD_RUNTIME','build/v3-nook-password-runtime-02')


class NookPasswordRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image,cls.report=inputs(OUT/'build-lock.json')
        cls.base,cls.prior=inputs(OUT/'base-lock.json')

    def test_current_map_code_and_retained_keyboard_storage(self):
        r,p=self.report,self.report['equipment_resources']['passwords']
        files,before=by_vrom(self.image),by_vrom(self.base)
        self.assertEqual(r['save_codec'],self.prior['save_codec'])
        self.assertEqual(r['save_runtime'],self.prior['save_runtime'])
        self.assertEqual(r['password_editor'],self.prior['password_editor'])
        self.assertEqual(r['physical_resources'],self.prior['physical_resources'])
        for record in r['physical_resources']:
            at,n=record['physical'],record['bytes']
            self.assertEqual(self.image[at:at+n],self.base[at:at+n])
        for v in (0x4620000,0x4630000,0x7749C0):
            self.assertEqual(files[v].extract(self.image),before[v].extract(self.base))
        blob=files[BLOB].extract(self.image)
        packet=blob[p['blob_offset']:p['blob_offset']+p['bytes']]
        self.assertEqual(sha256(packet),p['sha256']);self.assertEqual(zlib.crc32(packet),p['crc32'])
        self.assertEqual(packet[:p['code']['bytes']],(OUT/'password_runtime/code.bin').read_bytes())
        self.assertLessEqual(p['code']['bytes'],runtime.TABLES)
        mapping,receipt=policy.connected_destination_map(OUT/'base-lock.json')
        self.assertEqual(packet[runtime.MAP:runtime.MAP+len(mapping)],mapping)
        self.assertEqual(p['source']['destinations'],receipt)
        self.assertFalse(any(packet[runtime.CONVERSATION:-16]))
        self.assertTrue(p['keyboard_installed']);self.assertFalse(p['acquisition_installed'])
        self.assertFalse(p['conversation']['native_bindings_installed'])
        for name in ('af_nook_password_begin','af_nook_password_step'):
            self.assertTrue(runtime.RAM<=p['code']['symbols'][name]<runtime.RAM+runtime.TABLES)
        self.assertIn('af_v3_password_boot_ready',p['bootstrap']['code']['symbols'])
        prior_p=self.prior['equipment_resources']['passwords']
        old=before[BLOB].extract(self.base)[prior_p['blob_offset']:prior_p['blob_offset']+prior_p['bytes']]
        for at,n in ((runtime.TABLES,p['parts'][1]['bytes']),(runtime.POLICY,p['parts'][2]['bytes'])):
            self.assertEqual(packet[at:at+n],old[at:at+n])

    def test_compact_map_ranges_bits_and_rejections(self):
        packet,report=policy.connected_destination_map(OUT/'base-lock.json')
        expanded={}
        for r in report['ranges']:
            for item in range(r['first'],r['last']+1):
                self.assertNotIn(item,expanded)
                expanded[item]=(r['item']+item-r['first'],r['enable_ram'],r['enable_bytes'],r['enable_mask'])
        self.assertEqual(expanded,{r['source_item']:(r['item'],r['enable_ram'],r['enable_bytes'],r.get('enable_mask',0)) for r in report['rows']})
        self.assertEqual(len(report['native_correspondences']),1425)
        self.assertEqual(report['imports'],197)
        with tempfile.TemporaryDirectory(prefix='v3-password-map-') as tmp:
            lib=Path(tmp)/'policy.so'
            build=subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-shared','-fPIC',
                str(ROOT/'overlays/v3/password_policy.c'),'-o',str(lib)],capture_output=True,text=True,timeout=30)
            self.assertEqual(build.returncode,0,build.stderr)
            code=ctypes.CDLL(str(lib));read_type=ctypes.CFUNCTYPE(ctypes.c_uint32,ctypes.c_void_p,ctypes.c_uint32,ctypes.c_uint32)
            valid=code.af_v3_password_map_valid;valid.argtypes=[ctypes.c_void_p,ctypes.c_uint32]
            resolve=code.af_v3_password_resolve
            resolve.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_uint32,read_type,ctypes.c_void_p]
            resolve.restype=ctypes.c_uint32
            data=ctypes.create_string_buffer(packet)
            self.assertEqual(valid(data,len(packet)),1)
            reads=[];value=[1]
            @read_type
            def read(_,ram,width):reads.append((ram,width));return value[0]
            for kind in ('native','furniture','clothing','carried','fish'):
                row=next(r for r in report['rows'] if r['kind']==kind)
                for enabled in (0,1,2,125):
                    value[0]=enabled;reads.clear()
                    mask=row.get('enable_mask',0);width=row['enable_bytes']
                    available=not width or bool(enabled&mask) if mask else not width or enabled==1
                    self.assertEqual(resolve(data,len(packet),row['source_item'],read,None),row['item'] if available else 0)
                    self.assertEqual(reads,[(row['enable_ram'],width)] if width else [])
            # Explicit shifted counterpart, not an equal-ID assumption.
            self.assertEqual(resolve(data,len(packet),0x1D28,read,None),0x1CC8)
            for item in (0,65535,65536):self.assertEqual(resolve(data,len(packet),item,read,None),0)
            for at in (0,4,6,8,10,12,16+7,16+13):
                bad=bytearray(packet);bad[at]=254;bad=ctypes.create_string_buffer(bytes(bad));reads.clear()
                self.assertEqual(valid(bad,len(packet)),0)
                self.assertEqual(resolve(bad,len(packet),0x1000,read,None),0)
                self.assertFalse(reads)
            # Retain the installed version-one wire decoder for old fixtures.
            v1=struct.pack('>4s6H',b'AFPM',1,1,12,28,0,0)+struct.pack('>HHIB3x',0x3000,0x3200,0x80460000,4)
            legacy=ctypes.create_string_buffer(v1);value[0]=1
            self.assertEqual(valid(legacy,len(v1)),1)
            self.assertEqual(resolve(legacy,len(v1),0x3000,read,None),0x3200)
            value[0]=2;self.assertEqual(resolve(legacy,len(v1),0x3000,read,None),0)


if __name__=='__main__':unittest.main()
