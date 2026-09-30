"""Prepared complete source bank transactions; no native UI/save claim."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256
from v3_furniture_pipeline import Source
from v3_post_office import discover,generate,NUMERIC

PREPARED=ROOT/os.environ.get('V3_POST_OFFICE_PREPARED','build/v3-post-office-category-prepared-04')


class PostOfficeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())

    def test_whole_source_contract_and_generated_function_retention(self):
        generated,report=generate(self.source)
        prepared=json.loads((PREPARED/'prepared.json').read_bytes())
        self.assertEqual(len(report['functions']['src/game/m_bank_ovl.c']),16)
        self.assertEqual(report['rewards'],[
            dict(template=0x246,item='1FB0',paper='2000',received_mask=4,balance=1000000),
            dict(template=0x247,item='1FAC',paper='2000',received_mask=8,balance=10000000),
            dict(template=0x248,item='3294',paper='2000',received_mask=16,balance=100000000),
            dict(template=0x249,item='3020',paper='2000',received_mask=32,balance=999999999)])
        self.assertEqual(json.loads(json.dumps(report['functions'])),prepared['functions'])
        self.assertEqual(report['reward_sha256'],sha256((PREPARED/'post-office-rewards.bin').read_bytes()))
        for name,data in generated.items():
            self.assertEqual(data.encode(),(PREPARED/name).read_bytes())
            self.assertEqual(sha256(data.encode()),prepared['generated_sha256'][name])
        for name in NUMERIC:self.assertIn(name,generated['bank_source.c'])
        self.assertFalse(prepared['acquisition_installed']);self.assertFalse(prepared['compiled_frontend'])
        self.assertFalse(prepared['saved_record_installed']);self.assertEqual(prepared['base_abi'],386)
        self.assertEqual(sha256((PREPARED/'post-office.o').read_bytes()),prepared['object']['sha256'])
        source=object.__new__(Source);source.__dict__.update(self.source.__dict__)
        source.data=bytearray(source.data);at,_=source.symbol('l_mml_postoffice_info');source.data[at+15]^=1
        with self.assertRaisesRegex(ValueError,'complete source savings'):discover(source)

    def test_sanitized_donor_transactions_and_submission_receipts(self):
        with tempfile.TemporaryDirectory(prefix='v3-bank-account-') as temp:
            output=Path(temp)/'bank-account'
            compile=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-fno-pie','-no-pie',
                '-I',str(ROOT/'overlays/v3'),'-I',str(PREPARED),
                str(ROOT/'tests/v3_bank_account_test.c'),str(ROOT/'overlays/v3/bank_account.c'),
                str(PREPARED/'bank_source.c'),'-o',str(output)],
                capture_output=True,text=True,timeout=60)
            self.assertEqual(compile.returncode,0,compile.stdout+compile.stderr)
            run=subprocess.run([str(output),str(PREPARED/'post-office-rewards.bin')],
                capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr);print(run.stdout.strip())


if __name__=='__main__':unittest.main()
