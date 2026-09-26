"""Complete source particles, typed multi-frame models, and bounded callbacks."""
import copy
import json
import os
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,sha256
from v3_furniture_pipeline import Source,prepare_models
from v3_furniture_art import FRAME_BLEND_COMBINERS
from v3_room_particles import source_contract,models,append_object
import tests.test_v3_equipment_runtime as shared


class ParticleTests(unittest.TestCase):
    sanitized=shared.HostTests.sanitized

    @classmethod
    def setUpClass(cls):
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        cls.prepared=models(cls.source)

    def test_complete_source_and_unsupported_mutation(self):
        contract=source_contract(self.source)
        self.assertEqual(len(contract['functions']),8)
        self.assertEqual(contract['source_effect_ids'],[113,122])
        self.assertEqual(contract['source_ticks_per_native_update'],2)
        source=copy.copy(self.source);raw=bytearray(source.rel)
        raw[source.sections[1][0]+0x2A4250+20]^=1;source.rel=bytes(raw)
        with self.assertRaisesRegex(ValueError,'complete source'):source_contract(source)

    def test_shared_converter_retains_all_frames_models_and_materials(self):
        steam=self.prepared['steam']
        self.assertEqual(len(steam[1]),576)
        self.assertEqual([r['format'] for r in steam[2] if r['kind']=='texture'],['I4']*4)
        self.assertEqual([r['native_offset'] for r in steam[2]],[0,128,256,384,512])
        self.assertEqual(len(steam[4]),2)
        for label,model in steam[4].items():
            textures=[r for r in model['rows'] if r['opcode']==0xFD]
            self.assertEqual([(r['dynamic_texture'],r['scroll_tile'],r['scroll_tmem']) for r in textures],
                [(0x08000000,0,0),(0x09000000,1,16)])
            combine=next(r for r in model['rows'] if r['opcode']==0xFC)
            self.assertEqual(tuple(combine['frame_combine_lerp']),FRAME_BLEND_COMBINERS[combine['words']])
            self.assertEqual(sum(len(r.get('triangles',[])) for r in model['rows']),2)
        projectile=self.prepared['projectile']
        self.assertEqual([(r['kind'],r['bytes']) for r in projectile[2]],
            [('palette',32),('texture',512),('vertices',400)])
        self.assertEqual(sum(len(r.get('triangles',[])) for r in projectile[4]['opaque']['rows']),34)
        broken=copy.deepcopy(steam[0]);broken['callback_adapter']['material_frames'].pop()
        with self.assertRaises(ValueError):prepare_models(self.source,broken)
        source=copy.copy(self.source);data=bytearray(source.data)
        at=source.symbol('ef_dust01_modelT')[0]
        struct.pack_into('>I',data,at+48,0xD2F0FA00);source.data=bytes(data)
        with self.assertRaisesRegex(ValueError,'reordered'):prepare_models(source,steam[0])

    def test_actual_callbacks_under_sanitizers(self):
        self.sanitized('v3_room_particles_test.c')

    def test_current_owner_can_expand_without_losing_native_hooks(self):
        from v3_furniture_install import inputs
        from v3_room_effects import restore_controller,extend_controller,profile_overlay
        image,report=inputs(ROOT/'build/v3-static-interaction-imports-02/profile-runtime/build-lock.json')
        current=report['equipment_resources']['room_rigs']['effects']['controller'];files=by_vrom(image)
        owner,reloc=(files[current[k]].extract(image) for k in ('vrom','reloc'))
        native,original_reloc=restore_controller(owner,reloc,current)
        self.assertEqual(sha256(native),current['original']['sha256'])
        self.assertTrue(current['original']['timed_lamp_retained'])
        additions=copy.deepcopy(current['additions'])
        for i in range(2):
            ram=0x80700200+i*0x100;vrom=0x2500080+i*64
            additions.append(dict(id=113+i,overlay=[vrom,vrom+32,ram,ram+32,ram],
                graphics=[0x06018000+i*0x1000,0x06018400+i*0x1000],unique=0))
        changed,_,receipt=extend_controller(native,original_reloc,additions)
        self.assertEqual(receipt['count'],115)
        self.assertEqual(changed[0x36B0:0x36C0],owner[0x36B0:0x36C0])
        for table in receipt['tables']:
            at,n=table['offset'],113*table['stride']
            old_table=next(t for t in current['tables'] if t['stride']==table['stride'])
            self.assertEqual(changed[at:at+n],owner[old_table['offset']:old_table['offset']+n])
        symbols={}
        for i,kind in enumerate(('flash','flash_controller','steam','projectile')):
            for j,role in enumerate(('init','ct','mv','dw')):
                symbols[f'af_v3_{kind}_{role}']=0x804C8000+i*128+j*32
        for kind in ('steam','projectile'):
            packet=profile_overlay(symbols,kind=kind)
            self.assertEqual(len(packet),64)
            self.assertEqual(struct.unpack_from('>hhI',packet,16),(-2,255,0xC47A0CFF))
        damaged=bytearray(owner);damaged[16]^=1
        with self.assertRaisesRegex(ValueError,'installed'):restore_controller(damaged,reloc,current)

    def test_prepared_native_bank_and_code(self):
        directory=ROOT/os.environ.get('V3_PARTICLE_PREPARED','build/v3-room-particles-prepared-01')
        receipt=json.loads((directory/'particles.json').read_bytes())
        self.assertFalse(receipt['installed']);self.assertTrue(receipt['unresolved_sound_binding'])
        self.assertEqual(receipt['source'],json.loads(json.dumps(source_contract(self.source))))
        bank=(directory/'effect-art-bank.bin').read_bytes()
        self.assertEqual(sha256(bank),receipt['bank']['sha256'])
        original=bank[:receipt['objects']['steam']['graphics'][0]-0x06000000]
        self.assertEqual(sha256(original),receipt['bank']['previous_sha256'])
        restored=original
        # Sorted JSON keys differ from installation order.
        for kind in ('steam','projectile'):
            row=receipt['objects'][kind];asset=(directory/row['file']).read_bytes()
            restored,appended=append_object(restored,asset,row['model_records'])
            self.assertEqual(appended,{k:row[k] for k in appended})
            self.assertLessEqual(row['bytes'],3584)
            for model in row['model_records']:
                words=list(struct.iter_unpack('>II',asset[model['native_offset']:model['native_offset']+model['bytes']]))
                self.assertFalse(any(a>>24 in (0xD2,0x0A) for a,b in words))
                if kind=='steam':
                    self.assertIn(next(w for w in words if w[0]>>24==0xFC),FRAME_BLEND_COMBINERS)
                    self.assertEqual([b for a,b in words if a>>24==0xFD],[0x08000000,0x09000000])
        self.assertEqual(restored,bank)
        code=(directory/'callbacks/code.bin').read_bytes()
        self.assertEqual(sha256(code),receipt['code']['sha256'])
        for kind in ('steam','projectile'):
            for role in ('init','ct','mv','dw'):
                address=receipt['code']['symbols'][f'af_v3_{kind}_{role}']
                self.assertTrue(0x804C8000<=address<0x804C8000+len(code))


if __name__=='__main__':unittest.main()
