import json
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
from aflib import by_vrom,CODE_VROM,CODE_RAM,sha256
from v3_asset_loader import BLOB,MODULE,STARTUP
from v3_furniture_install import inputs
from v3_furniture_pipeline import Source
from v3_npc_registry import packet,patch_owners,checked_memory,TABLE,PROFILE,POOL,RAM
import v3_physical_resources as physical


class RegistryTests(unittest.TestCase):
    def test_current_bindings_and_complete_records(self):
        base,prior=inputs(ROOT/'build/v3-diary-category-work-01/catalogue-03/build-lock.json')
        self.assertEqual(checked_memory(prior)['ram'],RAM)
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        art=json.loads((ROOT/'build/v3-diary-category-work-01/tortimer-art-04/art.json').read_bytes())
        raw,r=packet(source,art)
        self.assertEqual((r['actor_bytes'],r['voice'],r['slot_stride']),(2612,281,2656))
        self.assertEqual(struct.unpack_from('>I',raw,TABLE+20)[0],0)
        self.assertEqual(raw[PROFILE+28:PROFILE+32],bytes(4))
        self.assertNotIn(PROFILE+28,[f['offset'] for f in r['profile_fixups']])
        self.assertEqual(struct.unpack_from('>4I',raw,POOL),(0x41464E53,0,0xD090,0xCC))
        _,patches,bindings=patch_owners(base,prior)
        self.assertEqual(len(patches),7)
        targets={p['helper']:RAM+i*16 for i,p in enumerate(patches)}
        changed,_,_=patch_owners(base,prior,targets)
        for vrom,out in changed.items():
            before=by_vrom(base)[vrom].extract(base)
            allowed={p['address']-p['ram']+i for p in patches if p['vrom']==vrom for i in range(4)}
            self.assertTrue(all(i in allowed for i,(a,b) in enumerate(zip(before,out)) if a!=b))
        self.assertEqual(bindings['af_npc_previous_allocate'],0x80057C48)
        bad=bytearray(base);entry=by_vrom(base)[CODE_VROM]
        bad[entry.pstart+0x800583B8-CODE_RAM]^=1
        with self.assertRaisesRegex(ValueError,'NPC hook'):patch_owners(bad,prior)

    def test_allocation_rendering_and_cleanup(self):
        with tempfile.TemporaryDirectory(prefix='v3-npc-registry-') as directory:
            out=Path(directory)/'check'
            cmd=['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fno-pie','-no-pie','-fsanitize=address,undefined','-fno-omit-frame-pointer',
                '-Ioverlays/v3','tests/v3_npc_registry_test.c','overlays/v3/npc_registry.c','-o',str(out)]
            r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=30)
            self.assertEqual(r.returncode,0,r.stdout+r.stderr)
            r=subprocess.run([str(out)],capture_output=True,text=True,timeout=30)
            self.assertEqual(r.returncode,0,r.stdout+r.stderr);print(r.stdout.strip())

    def test_installed_connections(self):
        base,old=inputs(ROOT/'build/v3-diary-category-work-01/catalogue-03/build-lock.json')
        directory=ROOT/os.environ.get('V3_NPC_REGISTRY','build/v3-diary-category-work-01/tortimer-installed-03')
        image,r=inputs(directory/'build-lock.json')
        e=r['equipment_resources'];n=e['npc_extra'];p=n['packet'];files=by_vrom(image)
        raw=image[p['physical']:p['physical']+p['bytes']];blob=files[BLOB].extract(image)
        self.assertEqual(sha256(raw),p['sha256']);self.assertEqual(zlib.crc32(raw),p['crc32'])
        self.assertEqual(raw[-16:],b'AFNX'*4)
        cane=n['record']['cane']
        self.assertEqual(sha256(raw[cane['offset']:cane['offset']+cane['bytes']]),cane['sha256'])
        self.assertFalse(cane['runtime_bound'])
        self.assertEqual(struct.unpack_from('>I',raw,TABLE+20)[0],0)
        self.assertFalse(n['actor_callbacks_bound']);self.assertFalse(n['selectable'])
        physical.verify(image,r['physical_resources'])
        self.assertEqual(r['object_capacity'],450);self.assertEqual(struct.unpack_from('>I',blob,12)[0],450)
        self.assertIn('-DAF_V3_OBJECT_CAPACITY=450',r['startup']['flags'])
        self.assertEqual(blob[0x1E10:0x1F80],by_vrom(base)[BLOB].extract(base)[0x1E10:0x1F80])
        for b in n['banks']:
            data=image[b['physical']:b['physical']+b['bytes']]
            self.assertEqual(data,(ROOT/'build/v3-diary-category-work-01/tortimer-art-04'/(b['kind']+'.bin')).read_bytes())
            self.assertEqual(struct.unpack_from('>2I',blob,0x1000+b['bank']*8),(b['vrom'],b['vrom']+b['bytes']))
        for h in n['hooks']:
            at=h['address']-h['ram'];owner=files[h['vrom']].extract(image)
            self.assertEqual(owner[at:at+4].hex(),h['after'])
            self.assertEqual(owner[at+4:at+8].hex(),h['before'][8:])
        boot=e['surface_bootstrap']['code'];self.assertLessEqual(boot['bytes'],688)
        at=e['blob_offset']+boot['symbols']['packets']-e['ram']
        descriptors=list(struct.iter_unpack('>5I',blob[at:at+17*20]))
        self.assertEqual(descriptors[-1][:3],(RAM,p['physical']|0x80000000,p['bytes']))
        for dest,source,size,crc,clear in descriptors:
            if source&0x80000000:data=image[source&0x7FFFFFFF:(source&0x7FFFFFFF)+size]
            else:
                owner=next(x for x in files.values() if x.vstart<=source<source+size<=x.vend)
                data=owner.extract(image)[source-owner.vstart:source-owner.vstart+size]
            self.assertEqual(struct.unpack_from('>I',blob,e['blob_offset']+crc-e['ram'])[0],zlib.crc32(data))
        self.assertEqual(files[0x1060].extract(image),by_vrom(base)[0x1060].extract(base))
        self.assertEqual(r['save_runtime']['profile_hex'],old['save_runtime']['profile_hex'])
        module=files[MODULE].extract(image);code=r['startup']
        self.assertEqual(sha256(module[STARTUP:STARTUP+code['bytes']]),code['sha256'])

    def test_transfer_and_complete_startup(self):
        with tempfile.TemporaryDirectory(prefix='v3-npc-dma-') as directory:
            for name,extra in (('v3_npc_dma_test', ['overlays/v3/npc_dma.c']),('v3_creature_startup_test', [])):
                out=Path(directory)/name
                cmd=['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fno-pie','-no-pie',
                    '-fsanitize=address,undefined','-fno-omit-frame-pointer','-Ioverlays/v3',
                    'tests/'+name+'.c',*extra,'-o',str(out)]
                r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=30)
                self.assertEqual(r.returncode,0,r.stdout+r.stderr)
                r=subprocess.run([str(out)],capture_output=True,text=True,timeout=30)
                self.assertEqual(r.returncode,0,r.stdout+r.stderr);print(r.stdout.strip())
