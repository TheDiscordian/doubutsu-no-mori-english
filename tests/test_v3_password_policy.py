"""Shared policy extraction, live-profile resolution, and Nook result decisions."""
import copy
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256
from v3_furniture_pipeline import Source
import v3_password_policy as policy

OUTPUT=ROOT/'build/v3-password-policy-prepared-03'
LOCK=ROOT/'build/v3-birth-scoring-runtime-02/build-lock.json'


def decision_reference(source):
    code,_=policy.evaluator(source)
    code=code.split('\nint main(void)',1)[0]
    header=(ROOT/'local/ac-decomp/include/ac_npc_shop_common.h').read_bytes()
    if sha256(header)!='69ad7b5e183c2ead62f7b8d13cbc19490f0e9a259c4dc7d5c54706f913aa6e50':
        raise ValueError('Changed reference shop result enum')
    result_enum=next(m.group() for m in re.finditer(r'enum\b[^;{}]*\{.*?\};',header.decode(),re.S)
                     if 'aNSC_PSW_RES_0' in m.group())
    texts=policy.reference_texts()
    code+='''
#include "overlays/v3/password.h"
typedef float f32;
static float reference_roll;
static int reference_names;
#define RANDOM_F(n) (assert((n)==100.0f),reference_roll)
static int mMpswd_check_name(mMpswd_password_c *p) {(void)p;return reference_names;}
'''+result_enum+'\n'
    code+=policy.function(texts['src/game/m_mail_password_check.c'],'mMpswd_check_npc_code')+'\n'
    code+=policy.function(texts['src/game/m_mail_password_check.c'],'mMpswd_password_zuru_check')+'\n'
    for name in ('famicom','npc','card_e','magazine','user','card_e_mini'):
        code+=policy.function(texts['src/actor/npc/ac_npc_shop_common.c'],
                              'aNSC_pc_check_password_'+name)+'\n'
    code+='''
int ref_decide(const af_v3_password *p,int names,float roll) {
    mMpswd_password_c v={0};
    v.item=p->item;v.npc_type=p->npc_type;v.npc_code=p->npc_code;v.type=p->type;
    v.hit_rate_index=p->hit_rate_index;v.checksum=p->checksum;
    memcpy(v.str0,p->str0,8);memcpy(v.str1,p->str1,8);
    reference_names=names;reference_roll=roll;
    if(mMpswd_password_zuru_check(&v)||!mMpswd_check_present(&v))return 0;
    switch(v.type) {
    case 0:return aNSC_pc_check_password_famicom(&v);
    case 1:return aNSC_pc_check_password_npc(&v);
    case 2:return aNSC_pc_check_password_card_e(&v);
    case 3:return aNSC_pc_check_password_magazine(&v);
    case 4:return aNSC_pc_check_password_user(&v);
    case 5:return aNSC_pc_check_password_card_e_mini(&v);
    }
    return 0;
}
'''
    return code


class PolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        cls.report=json.loads((OUTPUT/'password-policy.json').read_bytes())
        cls.masks=(OUTPUT/'donor-permissions.bin').read_bytes()

    def test_complete_donor_rules_compaction_and_kernel(self):
        code,source=policy.evaluator(self.source)
        self.assertEqual(sha256(code.encode()),self.report['generated_source_sha256'])
        self.assertEqual(json.loads(json.dumps(source['tables'])),self.report['tables'])
        data,rows=policy.compact(self.masks,source)
        self.assertEqual(data,(OUTPUT/'password-policy.bin').read_bytes())
        self.assertEqual(sha256(data),self.report['sha256'])
        expanded=bytearray(65536)
        for lo,hi,mask,_ in rows:expanded[lo:hi+1]=bytes([mask])*(hi-lo+1)
        self.assertEqual(expanded,self.masks)
        # HomePage furniture is Famicom-only; its surfaces use other codes.
        for name in ('ftr_listHomePage','ftr_listMario','carpet_listHomePage','wall_listHomePage'):
            for item, in struct.iter_unpack('>H',self.source.raw(name)[:-2]):
                self.assertEqual(self.masks[item],1 if name=='ftr_listHomePage' else 4,(name,f'{item:04X}'))
        self.assertEqual(self.masks[65535],7)  # Source sentinel; not a resolvable gift.
        self.assertEqual(self.masks[0],0)
        obj=(OUTPUT/'password_policy.o').read_bytes()
        self.assertEqual(obj[:6],b'\x7fELF\x01\x02')
        self.assertEqual(struct.unpack_from('>HH',obj,16),(1,8))
        self.assertEqual(sha256(obj),self.report['kernel']['sha256'])
        self.assertFalse(self.report['kernel']['linked'])
        self.assertFalse(any(self.report[k] for k in ('runtime_installed','acquisition_installed','destination_bindings_installed')))
        for name,digest in self.report['sources'].items():self.assertEqual(sha256((ROOT/name).read_bytes()),digest,name)

    def test_actual_import_mapping_and_changed_source_rejection(self):
        data,report=policy.destination_map(LOCK)
        self.assertEqual(data,(OUTPUT/'password-destinations.bin').read_bytes())
        self.assertEqual(report,self.report['destinations'])
        self.assertEqual(report['imports'],128)
        self.assertEqual(len(report['rows']),413)
        rows={r['source_item']:r for r in report['rows']}
        self.assertEqual(rows[0x1FA0]['item'],0x3C10)
        self.assertEqual(rows[0x1FA3]['item'],0x3C13)
        self.assertEqual(rows[0x2612]['item'],0x2649)
        self.assertEqual(rows[0x24BF]['item'],0x34BF)
        self.assertNotIn(65535,rows)
        for name in ('ftr_listHomePage','ftr_listMario','carpet_listHomePage','wall_listHomePage'):
            for item, in struct.iter_unpack('>H',self.source.raw(name)[:-2]):self.assertNotIn(item,rows)
        nintendo=[i for i,birth in enumerate(self.source.raw('mRmTp_birth_type')) if birth==34]
        self.assertEqual(len(nintendo),11)  # Nintendo bench plus ten Mario pieces.
        self.assertEqual(self.source.raw('ftr_listMario'),bytes(2))
        for index in nintendo:
            item=0x1000+index*4 if index<1024 else 0x3000+(index-1024)*4
            self.assertEqual(self.masks[item],4)
            if struct.unpack_from('>I',self.source.data,0x4FAFC+index*4)[0]>>26==59:
                self.assertNotIn(item,rows)
        bad=copy.copy(self.source);bad.rel=bytearray(self.source.rel);bad.rel[bad.sections[1][0]+0x4E1E8]^=1
        with self.assertRaises(ValueError):policy.evaluator(bad)
        bad=copy.copy(self.source);bad.data=bytearray(self.source.data)
        bad.data[self.source.symbol('mSP_goods_seg_inf')[0]]=1
        with self.assertRaises(ValueError):policy.evaluator(bad)
        with self.assertRaises(ValueError):policy.compact(self.masks[:-1],self.report)
        with self.assertRaises(ValueError):policy.compact(self.masks[:-1]+b'\x08',self.report)

    def test_nook_results_and_live_selection_under_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='v3-password-policy-test-',dir=ROOT/'build') as tmp:
            temporary=Path(tmp);reference=temporary/'reference.c';binary=temporary/'test'
            reference.write_text(decision_reference(self.source))
            compiled=subprocess.run(['cc','-std=c11','-O1','-g','-fsanitize=address,undefined',
                '-fno-omit-frame-pointer','-I',str(ROOT),str(reference),str(ROOT/'tests/v3_password_policy_test.c'),
                str(ROOT/'overlays/v3/password.c'),'-o',str(binary)],capture_output=True,text=True,timeout=30)
            self.assertEqual(compiled.returncode,0,compiled.stderr)
            result=subprocess.run([str(binary),str(OUTPUT/'password-policy.bin'),
                str(OUTPUT/'password-destinations.bin'),str(OUTPUT/'donor-permissions.bin'),
                str(ROOT/'build/v3-password-prepared-03/password-tables.bin')],
                capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('Source decisions, complete permissions, live selections, and no-gift outcomes pass',result.stdout)
            print(result.stdout.strip())
