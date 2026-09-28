"""Complete streamed NPC artwork and native drawing adapter, without a game fixture."""
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256
from v3_furniture_pipeline import Source
from v3_npc_stream_art import prepare
from v3_npc_stream_runtime import native_records,patch_owners
from v3_furniture_install import inputs
from v3_villager_mesh import faces
from tests.test_v3_islander_bodies import gx_pixel

OUTPUT=ROOT/'build/v3-diary-category-work-01/tortimer-art-04'

class StreamedNpc(unittest.TestCase):
    def test_current_native_hook_retains_both_complete_renderers(self):
        from aflib import by_vrom
        base,_=inputs(ROOT/'build/v3-diary-category-work-01/catalogue-03/build-lock.json')
        changes,owners=patch_owners(base,0x80400100) # synthetic link target, no installation
        files=by_vrom(base)
        self.assertEqual(len(owners),2)
        for row in owners:
            old=files[row['vrom']].extract(base);new=changes[row['vrom']];at=row['call']-row['ram']
            self.assertEqual(old[:at],new[:at]);self.assertEqual(old[at+4:],new[at+4:])
            self.assertEqual(struct.unpack_from('>I',new,at)[0],0x0C100040)

    def test_native_adapter(self):
        with tempfile.TemporaryDirectory(prefix='af-npc-stream-') as tmp:
            exe=Path(tmp)/'check'
            subprocess.run(['gcc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                str(ROOT/'tests/v3_npc_stream_draw_test.c'),'-o',str(exe)],check=True,capture_output=True)
            r=subprocess.run([str(exe)],check=True,capture_output=True,text=True,timeout=10)
            self.assertIn('segment restoration pass',r.stdout)

    @unittest.skipUnless((OUTPUT/'art.json').exists(),'Prepared current donor artwork required')
    def test_complete_donor_mesh_expressions_and_texture_pixels(self):
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        p=prepare(source,348);r=json.loads((OUTPUT/'art.json').read_text())
        model=(OUTPUT/'model.bin').read_bytes();texture=(OUTPUT/'texture.bin').read_bytes()
        self.assertEqual((len(texture),r['triangles']),(4128,256))
        self.assertEqual(len(model),r['model_bytes']);self.assertLessEqual(len(model),0x2800)
        self.assertEqual(r['body_offset'],32)
        self.assertLessEqual(r['body_offset']+4096,len(texture))
        self.assertEqual(r['source_aliases'],[348,354,358,365,373])
        draw,stream,voice=native_records(source,r,0xDFFE,510,511) # synthetic, unreserved identities
        self.assertEqual((len(draw),len(stream),voice),(100,36,281))
        self.assertEqual(struct.unpack_from('>HHIII',draw),(510,511,r['skeleton'],0x06000020,0x06000000))
        self.assertEqual(draw[48:84],bytes(36))
        self.assertEqual(draw[0x54:0x5F],p['draw_row'][0x54:0x5F])
        self.assertEqual(draw[0x60:],p['draw_row'][0x64:0x68])
        self.assertEqual(struct.unpack_from('>4H',stream),(0xDFFE,4128,32,0))
        for eye in range(8):
            self.assertEqual(struct.unpack_from('>I',draw,16+eye*4)[0],0x06000000+r['eye_offsets'][eye])
        self.assertEqual(sha256(model),r['model_sha256']);self.assertEqual(texture,p['texture'])
        self.assertEqual((OUTPUT/'commands.c').read_text(),p['source'])
        for path,digest in r['sources'].items():self.assertEqual(sha256((ROOT/path).read_bytes()),digest)
        for resource in r['resources']:
            raw=source.data[resource['source_offset']:resource['source_offset']+resource['bytes']]
            at=resource['offset'];w=resource['width'];h=resource['height']
            for y in range(h):
                for x in range(w):
                    native=texture[at+y*w//2+x//2]>>(0 if x&1 else 4)&15
                    self.assertEqual(native,gx_pixel(raw,w,x,y))
        triangles=0
        for record in r['models']:
            raw=model[record['offset']:record['offset']+record['bytes']]
            triangles+=len(faces(raw,donor=False,streamed=True,vertex_bytes=len(p['vertices'])))
            for material in record['materials']:
                self.assertEqual(struct.unpack_from('>II',raw,material['command_offset']-8),(0xE7000000,0))
                corrupt=bytearray(raw);struct.pack_into('>I',corrupt,material['command_offset']+28,0)
                with self.assertRaisesRegex(ValueError,'load, tile, or transfer'):
                    faces(corrupt,donor=False,streamed=True,vertex_bytes=len(p['vertices']))
        self.assertEqual(triangles,256)
        joints=model[r['joint_offset']:r['joint_offset']+26*12]
        for i in range(26):self.assertEqual(joints[i*12+4:i*12+12],p['joints'][i*12+4:i*12+12])

if __name__=='__main__':unittest.main()
