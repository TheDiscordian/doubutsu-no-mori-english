"""Shared source topology, complete motion traversal, and native-object packing."""
import copy
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256
from v3_furniture_pipeline import Source
import v3_handheld_items as held
import v3_keyframes as keyframes


class MotionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        cls.motion = held.motion(cls.source)
        cls.animations = [{k:v for k,v in row.items() if k!='resource_type'}
            for row in cls.motion['equipment_animations'].values()]
        cls.animations += list(cls.motion['player_animations'].values())

    def mutable_data(self):
        source = copy.copy(self.source)
        source.data = bytearray(self.source.data)
        return source

    def test_complete_motion_sources_and_parent_bindings(self):
        self.assertEqual(len(self.motion['parents']), 79)
        self.assertEqual(len(self.motion['skeletons']), 20)
        self.assertEqual(len(self.motion['equipment_animations']), 16)
        self.assertEqual(len(self.motion['player_animations']), 8)
        self.assertEqual(self.motion['fan_swing_animation'], 140)
        self.assertEqual(self.motion['player_animations'][139]['duration'], 17)
        self.assertEqual(self.motion['player_animations'][140]['duration'], 9)
        for row in self.motion['parents']:
            if 'shape_index' in row:
                self.assertIn(row['default_animation'], row['animation_resources'])
                rig = self.motion['skeletons'][row['shape_index']]
                for index in row['animation_resources']:
                    self.assertEqual(self.motion['equipment_animations'][index]['joints'],rig['joints'])
        self.assertFalse(self.motion['selectable'])
        self.assertFalse(self.motion['runtime_installed'])

    def test_complete_native_object_matches_all_source_arrays_and_pointers(self):
        asset, report = keyframes.compile_animations(self.source, self.animations)
        self.assertEqual(len(asset), 7760)
        self.assertEqual(len(report['headers']), 24)
        self.assertEqual(len(report['arrays']), 84)
        offsets = {r['donor_offset']:r['native_offset'] for r in report['arrays']}
        occupied = bytearray(len(asset))
        for row in report['arrays']:
            at,n,start = row['native_offset'],row['bytes'],row['donor_offset']
            self.assertEqual(asset[at:at+n],self.source.data[start:start+n])
            self.assertEqual(sha256(asset[at:at+n]),row['output_sha256'])
            self.assertFalse(any(occupied[at:at+n]));occupied[at:at+n]=b'\1'*n
        by_root = {row['header']['donor_offset']:row for row in self.animations}
        for row in report['headers']:
            at,start = row['native_offset'],row['donor_offset']
            self.assertFalse(any(occupied[at:at+20]));occupied[at:at+20]=b'\1'*20
            self.assertEqual(asset[at+16:at+20],self.source.data[start+16:start+20])
            self.assertEqual(sha256(asset[at:at+20]),row['output_sha256'])
            pointers = self.source.pointers(start,20)
            for index in range(4):
                target = pointers.get(start+index*4)
                actual = struct.unpack_from('>I',asset,at+index*4)[0]
                self.assertEqual(actual,0 if target is None else 0x06000000+offsets[target])
            # Independent consumer traversal: every root translation and joint
            # rotation uses exactly one constant or one complete keyed track.
            desc = by_root[start]
            flags,keys,counts,constants = [
                b'' if desc['arrays'][name] is None else self.source.data[
                    desc['arrays'][name]['donor_offset']:
                    desc['arrays'][name]['donor_offset']+desc['arrays'][name]['bytes']]
                for name in ('flags','keys','counts','constants')]
            channels = [(0,bit) for bit in (32,16,8)]
            channels += [(i,bit) for i in range(row['joints']) for bit in (4,2,1)]
            count_pos = constant_pos = key_pos = 0
            for joint,bit in channels:
                if flags[joint]&bit:
                    length = struct.unpack_from('>h',counts,count_pos)[0];count_pos+=2
                    frames = [struct.unpack_from('>hhh',keys,key_pos+i*6)[0] for i in range(length)]
                    key_pos += length*6
                    self.assertEqual(frames,sorted(set(frames)))
                    self.assertGreaterEqual(frames[0],1);self.assertLessEqual(frames[-1],row['duration'])
                else:
                    struct.unpack_from('>h',constants,constant_pos);constant_pos+=2
            self.assertEqual((count_pos,constant_pos,key_pos),(len(counts),len(constants),len(keys)))
        self.assertTrue(all(used or value==0 for used,value in zip(occupied,asset)))

    def test_constant_only_poses_preserve_null_key_pointers(self):
        rows = [r for r in self.animations if r['keyed_channels']==0]
        self.assertEqual(len(rows),6)
        asset,report = keyframes.compile_animations(self.source,rows)
        for row in report['headers']:
            at = row['native_offset']
            self.assertEqual(asset[at+4:at+12],bytes(8))
            self.assertEqual(row['joints'],26)

    def test_every_skeleton_preserves_hierarchy_and_model_roots(self):
        for rig in self.motion['skeletons'].values():
            at = rig['joint_table']['donor_offset'];remaining = [1]
            shown = 0
            for i,row in enumerate(rig['rows']):
                while remaining and remaining[-1]==0:remaining.pop()
                self.assertTrue(remaining);remaining[-1]-=1
                if row['children']:remaining.append(row['children'])
                raw = self.source.data[at+i*12:at+(i+1)*12]
                self.assertEqual(list(struct.unpack_from('>hhh',raw,6)),row['translation'])
                if 'model' in row:
                    shown += 1
                    self.assertEqual(self.source.pointers(at+i*12,12)[at+i*12],row['model']['donor_offset'])
            self.assertFalse(any(remaining));self.assertEqual(shown,rig['shown_joints'])

    def test_malformed_channels_and_tracks_reject(self):
        row = self.motion['player_animations'][140];root = row['header']['donor_offset']
        for label,offset,value in (('flags',0,b'\x80'),('flags',1,b'\x08'),
                ('counts',0,b'\0\0'),('counts',0,b'\xff\xff'),
                ('keys',0,b'\0\0'),('keys',6,b'\0\1'),('keys',0,b'\x7f\xff')):
            source = self.mutable_data();at=row['arrays'][label]['donor_offset']+offset
            source.data[at:at+len(value)]=value
            with self.assertRaises(ValueError):keyframes.animation(source,root)
        with self.assertRaisesRegex(ValueError,'skeleton'):keyframes.animation(self.source,root,joints=25)
        source = copy.copy(self.source);source.relocations=dict(self.source.relocations)
        del source.relocations[root+4]
        source.relocation_addresses=[at for at in self.source.relocation_addresses if at!=root+4]
        with self.assertRaisesRegex(ValueError,'complete key data'):keyframes.animation(source,root)

    def test_malformed_skeleton_and_stale_descriptions_reject(self):
        rig = self.motion['skeletons'][33];root=rig['header']['donor_offset']
        for at,value in ((root+1,3),(rig['joint_table']['donor_offset']+4,0),
                         (rig['joint_table']['donor_offset']+5,2)):
            source=self.mutable_data();source.data[at]=value
            with self.assertRaises(ValueError):keyframes.skeleton(source,root)
        bad=copy.deepcopy(self.animations);bad[0]['duration']+=1
        with self.assertRaisesRegex(ValueError,'changed animation'):
            keyframes.compile_animations(self.source,bad)
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            keyframes.compile_animations(self.source,self.animations*2)

    def test_changed_player_selectors_and_fan_setup_reject(self):
        for address in (0x68A44,0x68A74,0x1962B0):
            source=copy.copy(self.source);source.rel=bytearray(self.source.rel)
            source.rel[source.sections[1][0]+address]^=1
            with self.assertRaises(ValueError):held.motion(source)
            source=copy.copy(self.source);source.code_relocations=dict(self.source.code_relocations)
            source.code_relocations[address+0x12]=(6,0,5,0)
            with self.assertRaises(ValueError):held.motion(source)

    def test_shared_cli_category_produces_reproducible_prepared_only_data(self):
        path=ROOT/'build/v3-held-motion-prepared-01'
        saved=json.loads((path/'art.json').read_bytes())
        self.assertEqual(saved['source'],json.loads(json.dumps(self.motion)))
        asset,compiled=keyframes.compile_animations(self.source,self.animations)
        self.assertEqual((path/saved['object_file']).read_bytes(),asset)
        self.assertEqual(saved['object_sha256'],sha256(asset))
        self.assertFalse(saved['selectable']);self.assertFalse(saved['runtime_installed'])
        self.assertEqual(saved['relocations'],compiled['relocations'])
        with tempfile.TemporaryDirectory(prefix='v3-motion-') as temporary:
            target=Path(temporary)/'not-created'
            with self.assertRaisesRegex(ValueError,'complete source dependency bundle'):
                held.convert(self.source,target,['2254'],category='held-motion')
            self.assertFalse(target.exists())


if __name__=='__main__':unittest.main()
