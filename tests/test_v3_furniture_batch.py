"""Bulk compilation and strict reuse without replaying runtime verification."""
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import map_artwork
import v3_furniture_pipeline as pipeline


class BatchCompilerTests(unittest.TestCase):
    def test_one_container_for_multiple_objects_and_all_sections(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'build',prefix='batch compiler ') as temp:
            base=Path(temp);source=base/'commands.c';source.write_text('/* fixture */')
            output=base/'compiled'
            jobs=[('one',source,(('opaque',8),('translucent',16))),('two',source,(('part0',24),))]
            def compile_fixture(command,**kwargs):
                self.assertEqual(command[:5],['docker','run','--rm','--network','none'])
                self.assertTrue(kwargs['check']);self.assertIn('set -eu',command[-1])
                self.assertEqual(command[-1].count('mips64-elf-gcc'),2)
                self.assertEqual(command[-1].count('mips64-elf-objcopy'),3)
                for key,_,sections in jobs:
                    for name,size in sections:(output/key/(name+'.bin')).write_bytes(bytes(size))
            with patch.object(map_artwork.subprocess,'run',side_effect=compile_fixture) as run:
                result=map_artwork.compile_commands_batch(output,jobs)
            self.assertEqual(run.call_count,1)
            self.assertEqual(result,{'one':{'opaque':bytes(8),'translucent':bytes(16)},'two':{'part0':bytes(24)}})

    def test_empty_or_invalid_batch_never_starts_compiler(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'build') as temp:
            base=Path(temp);source=base/'commands.c';source.write_text('/* fixture */')
            with patch.object(map_artwork.subprocess,'run') as run:
                self.assertEqual(map_artwork.compile_commands_batch(base/'empty',[]),{})
                for jobs in ([('../bad',source,(('opaque',8),))],
                             [('one',source,(('opaque',8),))]*2,
                             [('one',source,(('opaque',7),))],
                             [('one',source,(('opaque',8),('opaque',8)))],
                             [('one',source,(('bad;command',8),))]):
                    with self.subTest(jobs=jobs),self.assertRaises(ValueError):
                        map_artwork.compile_commands_batch(base/'invalid',jobs)
                run.assert_not_called()
            self.assertFalse((base/'empty').exists());self.assertFalse((base/'invalid').exists())

    def test_incomplete_compiler_output_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'build') as temp:
            base=Path(temp);source=base/'commands.c';source.write_text('/* fixture */')
            output=base/'compiled'
            def short_section(*args,**kwargs):(output/'one'/'opaque.bin').write_bytes(bytes(8))
            with patch.object(map_artwork.subprocess,'run',side_effect=short_section):
                with self.assertRaisesRegex(ValueError,'section differs'):
                    map_artwork.compile_commands_batch(output,[('one',source,(('opaque',16),))])


class PreparedReuseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=pipeline.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        cls.directory=Path(os.environ.get('V3_FURNITURE_PREPARED_ART',ROOT/'build/v3-bulk-prepared-02')).resolve()
        cls.cache=pipeline.PreparedAssets(cls.source,[cls.directory])

    def test_reuse_retains_complete_objects_without_compilation(self):
        with patch.object(map_artwork.subprocess,'run',side_effect=AssertionError('Unexpected compiler')):
            for item in self.cache.rows:
                prepared=pipeline.prepare(self.source,int(item,16))
                compiled,receipt=self.cache.reuse(self.source,item,prepared)
                self.assertEqual(set(compiled),set(prepared[4]))
                self.assertEqual(receipt['object_sha256'],self.cache.rows[item][0][1]['object_sha256'])
        self.assertIsNone(self.cache.reuse(self.source,'FFFF',None))

    def test_changed_hash_bounds_layout_and_source_are_rejected(self):
        item=next(iter(self.cache.rows));prepared=pipeline.prepare(self.source,int(item,16))
        for kind in ('hash','offset-type','offset-range','model','path'):
            cache=copy.copy(self.cache);cache.rows=copy.deepcopy(self.cache.rows)
            row=cache.rows[item][0][1]
            if kind=='hash':row['object_sha256']='0'*64
            elif kind=='offset-type':row['models'][0]['native_offset']='0'
            elif kind=='offset-range':row['models'][0]['native_offset']=row['object_bytes']
            elif kind=='model':row['models'][0]['source_sha256']='0'*64
            else:row['object_file']='../escaped.bin'
            with self.subTest(kind=kind),self.assertRaises(ValueError):cache.reuse(self.source,item,prepared)
        with tempfile.TemporaryDirectory(dir=ROOT/'build') as temp:
            art=json.loads((self.directory/'art.json').read_bytes());art['source_rel_sha256']='0'*64
            path=Path(temp);(path/'art.json').write_text(json.dumps(art))
            with self.assertRaisesRegex(ValueError,'source/format'):pipeline.PreparedAssets(self.source,[path])

    def test_constant_palette_sequence_keeps_both_models_and_source_palette(self):
        records=[]
        for item in (0x3210,0x3374):
            profile,body,resources,offsets,models,_,sections=pipeline.prepare(self.source,item)
            adapter=profile['callback_adapter'];palette=adapter['constant_palette']
            self.assertEqual(adapter['model_order'],['part0','part1'])
            self.assertEqual(adapter['null_callbacks'],['create','move','destroy'])
            self.assertEqual(profile['palette_bindings'],{0x08000000:palette['donor_offset']})
            converted=[r for r in resources if r['kind']=='palette']
            self.assertEqual(len(converted),1)
            self.assertEqual(converted[0]['source_sha256'],palette['source_sha256'])
            self.assertEqual(len(models),2)
            record,linked=pipeline.draw_sequence(profile,len(body),sections)
            self.assertEqual(record['bytes'],24);self.assertEqual(len(linked),24)
            records.append((profile,models,palette))
        self.assertEqual({k:v['source_sha256'] for k,v in records[0][1].items()},
                         {k:v['source_sha256'] for k,v in records[1][1].items()})
        self.assertNotEqual(records[0][2]['source_sha256'],records[1][2]['source_sha256'])
        adapter=records[0][0]['callback_adapter'];draw=adapter['functions']['draw']
        changed=copy.copy(self.source);changed.code_relocations=dict(self.source.code_relocations)
        kind,module,section,target=draw['relocations'][0x56]
        changed.code_relocations[draw['offset']+0x56]=(kind,module,section,target+32)
        with self.assertRaisesRegex(ValueError,'fixed draw'):changed.profile(0x3210)


if __name__=='__main__':unittest.main()
