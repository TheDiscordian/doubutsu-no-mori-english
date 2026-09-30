"""Whole donor bank frontend/resources with isolated transaction/draw callbacks."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,CODE_RAM,CODE_VROM,sha256
from v3_furniture_pipeline import Source
from v3_bank_frontend import generate,artwork,native_contract,admission_contract,reuse_artwork,ROOTS
from v3_post_office import pelly

PREPARED=ROOT/os.environ.get('V3_BANK_FRONTEND_PREPARED','build/v3-post-office-bank-frontend-prepared-20')


class BankFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())

    def test_whole_frontend_and_shared_resource_contract(self):
        generated,report=generate(self.source);prepared=json.loads((PREPARED/'prepared.json').read_bytes())
        pg,pg_report=pelly(self.source);generated.update(pg)
        from v3_bank_april import generate as april_generate,native_bindings as april_bindings
        april,april_report=april_generate(self.source);generated.update(april)
        self.assertEqual(json.loads(json.dumps(pg_report)),prepared['pelly'])
        self.assertEqual(len(pg_report['functions']),16)
        self.assertEqual(pg_report['full_loan_field_bytes'],7)
        self.assertIn('u8 str[aPG_LOAN_STR_LEN];',pg['pelly_source.c'])
        self.assertNotIn('u8 str[2];',pg['pelly_source.c'])
        self.assertIn('u8 str[11];',pg['pelly_source.c']);self.assertNotIn('u8 str[8];',pg['pelly_source.c'])
        self.assertEqual(len(report['bank_functions']),16)
        self.assertTrue(prepared['compiled_frontend']);self.assertFalse(prepared['native_frontend_installed'])
        self.assertFalse(prepared['saved_record_installed']);self.assertEqual(prepared['base_abi'],386)
        for name,text in generated.items():
            self.assertEqual(text.encode(),(PREPARED/name).read_bytes())
            self.assertEqual(sha256(text.encode()),prepared['generated_sha256'][name])
        self.assertEqual(sha256((PREPARED/'post-office.o').read_bytes()),prepared['object']['sha256'])
        from v3_post_office_install import native_bindings
        from v3_furniture_install import inputs
        image,prior=inputs(ROOT/'build/v3-holiday-card-prize-imports-01/password-destinations/build-lock.json')
        bound,receipt=native_bindings(image,prior)
        april_bound,april_receipt=april_bindings(image);bound.update(april_bound)
        april_report['native_bindings']=april_receipt
        self.assertEqual(json.loads(json.dumps(april_report)),prepared['april'])
        self.assertEqual(len(april_report['functions']),6)
        self.assertFalse(april_report['actor_installed']);self.assertFalse(april_report['calendar_installed'])
        self.assertEqual(receipt,prepared['native_bindings'])
        self.assertEqual(bound,prepared['object']['bound_native_services'])
        unresolved={line.split()[-1] for line in prepared['object']['unbound_services']}
        self.assertFalse(unresolved&bound.keys())
        self.assertNotIn('af_bank_pelly_loan_balance',unresolved)
        self.assertNotIn('af_bank_native_account',unresolved)
        self.assertNotIn('af_bank_pelly_april_clip',unresolved)
        self.assertTrue(prepared['saved_owner']['shared_account_implementation'])
        self.assertTrue(prepared['saved_owner']['compiled'])
        self.assertFalse(prepared['saved_owner']['installed'])
        self.assertEqual(prepared['saved_owner']['save_format'],21)
        self.assertEqual(prepared['saved_owner']['card_wire'],7)
        self.assertEqual(prepared['saved_owner']['flags'][:-2],prior['save_codec']['active_storage_code']['flags'])
        if 'dialogue' in prepared:
            from v3_bank_storage import layout
            from v3_holiday_dialogue import check_provenance
            check_provenance(prepared['dialogue'])
            self.assertEqual((prepared['dialogue']['count'],prepared['dialogue']['choice_count']),(12,4))
            self.assertEqual(sha256((PREPARED/'bank-dialogue.c').read_bytes()),prepared['dialogue']['generated_sha256'])
            self.assertFalse(any(line.split()[-1] in ('af_bank_pelly_message_map','af_bank_pelly_message_unmap')
                for line in prepared['object']['unbound_services']))
            from v3_furniture_install import inputs
            _,prior=inputs(ROOT/'build/v3-holiday-card-prize-imports-01/password-destinations/build-lock.json')
            self.assertEqual(prepared['saved_owner_memory'],layout(prior))
        p=artwork(self.source);actual=prepared['artwork'];data=(PREPARED/'bank-art.bin').read_bytes()
        self.assertEqual(reuse_artwork(self.source,p,PREPARED)[0],data)
        self.assertEqual(sha256(data),actual['sha256']);self.assertEqual(len(data),actual['bytes'])
        self.assertEqual(json.loads(json.dumps(p[2])),actual['resources'])
        self.assertEqual(json.loads(json.dumps(p[4])),actual['models'])
        self.assertEqual([n['symbol'] for n in actual['compiled_models']],list(ROOTS))
        self.assertEqual([r['symbol'] for r in p[2] if r.get('format')=='IA8'],
            ['tyo_win_deposit_tex_rgb_ia8','tyo_win_withdraw_tex'])
        # Both full 128x32 labels retain 4 KiB, not downscaled/cropped substitutes.
        labels=[r for r in p[2] if r.get('format')=='IA8']
        self.assertEqual([(r['width'],r['height'],r['bytes']) for r in labels],[(128,32,4096)]*2)
        mode=p[4]['mode']['rows'];frame=p[4]['frame']['rows']
        self.assertEqual([r.get('palette_slot',15) for r in mode if r['opcode']==0xF0],[14])
        loads=[r for r in frame if r['opcode']==0xFD and r['ui_tile']==1]
        self.assertEqual(len(loads),10);self.assertEqual({r['ui_tmem'] for r in loads},{64})
        for resource in p[2]:
            at,n=resource['native_offset'],resource['bytes']
            self.assertEqual(sha256(data[at:at+n]),resource['output_sha256'])
        from v3_ui_art import Packet
        bad=object.__new__(Source);bad.__dict__.update(self.source.__dict__);bad.data=bytearray(bad.data)
        at,_=bad.symbol(ROOTS[0]);bad.data[at+0x23]^=1
        with self.assertRaisesRegex(ValueError,'palette load'):Packet(bad).model('bad',[ROOTS[0]],state_only=True)

    def test_current_native_field_and_whole_service_guards(self):
        from v3_furniture_install import inputs
        base,_=inputs(ROOT/'build/v3-holiday-card-prize-imports-01/password-destinations/build-lock.json')
        files=by_vrom(base);owner=files[0x79B120].extract(base);rel=files[0x79BF10].extract(base)
        core=files[CODE_VROM].extract(base)
        report=native_contract(owner,rel,core)
        self.assertEqual(report,json.loads((PREPARED/'prepared.json').read_bytes())['native_adapter'])
        self.assertEqual(report['menu_slot'],7);self.assertFalse(report['saved_provider_bound'])
        admission=admission_contract(files[0x8A6C10].extract(base),files[0x8A8A10].extract(base),core)
        self.assertEqual(admission,json.loads((PREPARED/'prepared.json').read_bytes())['admission'])
        self.assertEqual(admission['added_bank_actions'],list(range(33,38)))
        changed=bytearray(core);changed[0x80094A90-CODE_RAM+20]^=1
        with self.assertRaisesRegex(ValueError,'admission field owner'):
            admission_contract(files[0x8A6C10].extract(base),files[0x8A8A10].extract(base),changed)
        changed=bytearray(core);changed[0x800B8B08-CODE_RAM+20]^=1
        with self.assertRaisesRegex(ValueError,'complete native bank service'):native_contract(owner,rel,changed)
        changed=bytearray(owner);changed[0x80897B3C-0x808979C0]^=1
        with self.assertRaisesRegex(ValueError,'complete translated repayment'):native_contract(changed,rel,core)

    def test_sanitized_complete_frontend_transactions_and_drawing(self):
        self.frontend_fixture(native=False)

    def test_sanitized_native_menu_and_money_adapters(self):
        self.frontend_fixture(native=True)

    def frontend_fixture(self,*,native,dialogue=None):
        with tempfile.TemporaryDirectory(prefix='v3-bank-frontend-') as temp:
            output=Path(temp)/'frontend'
            command=['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined,float-cast-overflow','-fno-omit-frame-pointer','-fno-pie','-no-pie',
                '-I',str(ROOT/'overlays/v3'),'-I',str(PREPARED),
                str(ROOT/'tests/v3_bank_frontend_test.c'),str(ROOT/'overlays/v3/bank_account.c'),
                str(PREPARED/'bank_source.c'),'-o',str(output)]
            if native:command+=['-DAF_BANK_TEST_NATIVE=1',str(ROOT/'overlays/v3/bank_native.c'),
                str(ROOT/'tests/v3_bank_native_test.c'),str(PREPARED/'pelly_source.c'),
                str(ROOT/'overlays/v3/bank_admission.c'),str(ROOT/'overlays/v3/bank_pelly_native.c'),
                str(ROOT/'overlays/v3/bank_entries.c'),
                str(ROOT/'tests/v3_bank_pelly_test.c')]
            if native:command+=['-DAF_BANK_TEST_APRIL=1',str(PREPARED/'april_source.c'),
                str(ROOT/'tests/v3_bank_april_test.c')]
            if dialogue is not None:
                self.assertTrue(native)
                command+=['-DAF_BANK_TEST_DIALOGUE=1',str(dialogue)]
            build=subprocess.run(command,capture_output=True,text=True,timeout=60)
            self.assertEqual(build.returncode,0,build.stdout+build.stderr)
            run=subprocess.run([str(output)],capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr);print(run.stdout.strip())


if __name__=='__main__':unittest.main()
