"""Connected design resources and editing services, without gameplay claims."""
import copy
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256
from v3_furniture_pipeline import Source,assemble_models
from v3_carried_items import design_field_art,design_defaults
from v3_furniture_art import native_texture_block

OUT=ROOT/os.environ.get('V3_CARRIED_DESIGNS','build/v3-carried-design-fields-01')

class DesignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        cls.report=json.loads((OUT/'designs.json').read_bytes())

    def test_complete_seasonal_art_and_dynamic_design_segments(self):
        prepared=design_field_art(self.source);r=self.report['art'];raw=(OUT/r['file']).read_bytes()
        self.assertEqual((len(raw),sha256(raw)),(r['bytes'],r['sha256']))
        self.assertEqual(r['resources'],prepared[2])
        self.assertEqual((OUT/'commands.c').read_text(),prepared[5])
        compiled={m['layer']:raw[m['native_offset']:m['native_offset']+m['bytes']] for m in r['models']}
        full,offsets,models,_=assemble_models(prepared,compiled)
        self.assertEqual(full,raw);self.assertEqual(offsets,r['offsets']);self.assertEqual(models,r['models'])
        self.assertEqual(set(compiled),{'pattern','ordinary','winter','shadow'})
        self.assertEqual(sum(m['triangles'] for m in models),8)
        palettes={x['symbol'] for x in r['resources'] if x['kind']=='palette'}
        self.assertEqual(palettes,{'hakushi_pal','obj_kanban_pal'}|{f'needlework{i}_pal' for i in range(16)})
        for resource in r['resources']:
            at,n=resource['native_offset'],resource['bytes'];data=raw[at:at+n]
            self.assertEqual(sha256(data),resource['output_sha256'])
            source=self.source.data[resource['donor_offset']:resource['donor_offset']+n]
            self.assertEqual(sha256(source),resource['source_sha256'])
            if resource['symbol']=='obj_kanban_shadow_tex':
                self.assertEqual(data,source);self.assertEqual(resource['source_layout'],'N64-row-major')
        addresses=[b for a,b in struct.iter_unpack('>II',compiled['pattern']) if a>>24==0xFD]
        self.assertIn(0x08000000,addresses);self.assertIn(0x09000000,addresses)
        self.assertIn((0x01004008,0x0A000000),list(struct.iter_unpack('>II',compiled['shadow'])))
        self.assertFalse(self.report['runtime_installed']);self.assertFalse(self.report['selectable'])

    def test_native_texture_block_rejects_incomplete_or_changed_dma(self):
        raw=self.source.raw('obj_kanban_shadowT_model');at=48
        shape,words=native_texture_block(raw,at);self.assertEqual(shape,(32,32,4,0))
        for offset,mask in ((0,0x40000),(8,1),(12,0x1000000),(24,1),(28,0x1000),
                            (28,1),(40,0x200),(44,0x04000000),(52,4)):
            bad=bytearray(raw);value=struct.unpack_from('>I',bad,at+offset)[0]
            struct.pack_into('>I',bad,at+offset,value^mask)
            with self.assertRaises(ValueError):native_texture_block(bad,at)
        with self.assertRaises(ValueError):native_texture_block(raw[:at+48],at)
        with self.assertRaises(ValueError):native_texture_block(raw,at+1)

    def test_complete_official_templates_and_source_credits(self):
        templates,receipt=design_defaults(self.source,ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso')
        self.assertEqual(templates,(OUT/'templates.bin').read_bytes());self.assertEqual(len(templates),8*544)
        for k,v in receipt.items():self.assertEqual(json.loads(json.dumps(v)),self.report['defaults'][k])
        entries={r['id']:r for r in json.loads((ROOT/'translations/provenance.json').read_bytes())['entries']}
        for entry in receipt['provenance_entries']:self.assertEqual(entries[entry['id']],entry)
        for i in range(8):
            row=templates[i*544:(i+1)*544]
            self.assertEqual(row[16],(0,8,7,7,0,0,0,0)[i]);self.assertEqual(row[17:32],bytes(15))
            if i>=4:self.assertEqual(row[:16],b'blank           ');self.assertEqual(row[32:],bytes([255])*512)
        source=copy.copy(self.source);source.data=bytearray(source.data)
        source.data[source.symbol('pal_table$400')[0]]=16
        with self.assertRaisesRegex(ValueError,'initialization'):
            design_defaults(source,ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso')

    def test_pattern_editing_and_atomic_commit(self):
        with tempfile.TemporaryDirectory(prefix='v3-designs-') as tmp:
            exe=Path(tmp)/'check'
            result=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fno-pie','-no-pie','-fsanitize=address,undefined','-fno-omit-frame-pointer',
                'tests/v3_carried_designs_test.c','overlays/v3/carried_designs.c','-o',str(exe)],
                cwd=ROOT,capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            result=subprocess.run([str(exe),str(OUT/'templates.bin')],capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr);print(result.stdout.strip())
        c=self.report['services'];data=(OUT/c['file']).read_bytes()
        self.assertEqual((len(data),sha256(data)),(c['bytes'],c['sha256']))
        self.assertEqual(c['symbols']['af_design_valid'],c['ram'])
        self.assertLessEqual(len(data),8192);self.assertEqual(c['saved_bytes'],17440)

    def test_complete_save_transaction_and_migration(self):
        templates=(OUT/'templates.bin').read_bytes()
        with tempfile.TemporaryDirectory(prefix='v3-design-save-') as temp:
            out=Path(temp)
            rows=[]
            for i in range(8):
                r=templates[i*544:(i+1)*544]
                rows.append('{.name={'+','.join(map(str,r[:16]))+'},.palette='+str(r[16])+
                    ',.flags='+str(r[17])+',.texture={'+','.join(map(str,r[32:]))+'}}')
            (out/'design_templates.h').write_text('const AFDesign af_design_templates[8]={'+','.join(rows)+'};\n')
            flags=['-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fno-pie','-no-pie',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-ffunction-sections','-fdata-sections',
                '-I'+str(out),*('-D'+name+'=1' for name in ('AF_V3_CLOTHING_PROFILE','AF_V3_REWARD_PROFILE',
                    'AF_V3_SURFACE_PROFILE','AF_V3_CREATURE_PROFILE','AF_V3_INSECT_SEASONS',
                    'AF_V3_DIARY_STORAGE','AF_V3_HOLIDAY_STORAGE','AF_V3_FISHING_STORAGE','AF_V3_CARD_STORAGE',
                    'AF_V3_EVENT_ITEM_PROFILE','AF_V3_CARRIED_PROFILE','AF_V3_CARRIED_QUEST',
                    'AF_V3_PAPER_PACKS','AF_V3_CARRIED_NPC','AF_V3_CONSOLE_STORAGE'))]
            commands=[['cc',*flags,'-Daf_v3_save_check=af_console_canonical_check',
                '-Daf_v3_save_pack=af_console_canonical_pack','-Daf_v3_save_collect=af_console_canonical_collect',
                '-c','overlays/v3/save_codec.c','-o',str(out/'codec.o')]]
            entries=('compress','expand','compress_diary','measure_diary','expand_diary',
                'compress_fishing','measure_fishing','expand_fishing','compress_cards','measure_cards','expand_cards')
            commands.append(['cc',*flags,*(f'-Daf_v3_save_{s}=af_v19_{s}' for s in entries),
                '-c','overlays/v3/save_compressed.c','-o',str(out/'v19.o')])
            for mode in (0,1):
                commands.extend([['cc',*flags,'-DAF_V3_DESIGN_STORAGE=1',f'-DTEST_PAPER_MODE={mode}',
                    '-Wl,--gc-sections','tests/v3_carried_design_storage_test.c',
                    *(f'overlays/v3/{s}.c' for s in ('save_runtime','console_storage','save_compressed',
                        'diary','diary_calendar','holiday_fishing','holiday_cards','carried_items',
                        'carried_collection','carried_paper','carried_designs')),
                    str(out/'codec.o'),str(out/'v19.o'),'-o',str(out/'check')],[str(out/'check')]])
            for command in commands:
                result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=30)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                if result.stdout:print(result.stdout.strip())

if __name__=='__main__':unittest.main()
