"""Complete official bank text, native destinations, and real Pelly mapping."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,sha256
from v3_furniture_install import inputs
from v3_bank_dialogue import prepare,ROOTS,CHOICES,NATIVE_DESTINATIONS,MESSAGE,TABLE,CHOICE_TABLE
from v3_holiday_dialogue import check_provenance
from textbanks import Bank
from textcodec import tokenize
from runtime_module import module_command_info
from tests import test_v3_bank_frontend as frontend


class BankDialogueTests(unittest.TestCase):
    def test_complete_official_text_and_preserved_native_banks(self):
        image,prior=inputs(ROOT/'build/v3-holiday-card-prize-imports-01/password-destinations/build-lock.json')
        files=by_vrom(image);info=module_command_info(image)
        with tempfile.TemporaryDirectory(prefix='v3-bank-dialogue-',dir=ROOT/'build') as temp:
            out=Path(temp)/'dialogue';r=prepare(image,prior,out);check_provenance(r)
            self.assertEqual((r['count'],r['choice_count']),(14,4))
            self.assertEqual(set(r['mapping']),set(ROOTS));self.assertEqual(set(r['choice_mapping']),set(CHOICES))
            self.assertFalse(r['installed']);self.assertEqual(r['max_expanded_bytes'],297)
            messages=Bank('messages',0,0,(out/'messages.bin').read_bytes(),(out/'message-table.bin').read_bytes()).entries()
            choices=Bank('choices',0,0,(out/'choices.bin').read_bytes(),(out/'choice-table.bin').read_bytes()).entries()
            old=Bank('messages',0,0,files[MESSAGE].extract(image),files[TABLE].extract(image)).entries()
            cv=prior['import_storage']['choice_vrom']
            old_c=Bank('choices',0,0,files[cv].extract(image),files[CHOICE_TABLE].extract(image)).entries()
            self.assertEqual(messages[:r['first_id']],old)
            self.assertEqual(choices[:r['first_choice']],old_c)
            branches=set();captions=set()
            for row in r['messages']:
                data=messages[row['id']];self.assertEqual(sha256(data),row['sha256'])
                for t in tokenize(data,info):
                    if t.kind=='cmd' and (15<=t.data[1]<=18 or t.data[1]==24):
                        refs={int.from_bytes(t.data[a:a+2],'big') for a in range(2,len(t.data),2)}
                        if t.data[1]==24:captions|=refs
                        else:branches|=refs
            self.assertEqual(branches,set(NATIVE_DESTINATIONS)|{r['mapping'][0x2DE0],r['mapping'][0x2DE1]})
            self.assertEqual(captions,set(r['choice_mapping'].values()))
            # Full source and native controller use the generated map, not an
            # arithmetic message-number double. Native I/O remains doubled.
            frontend.BankFrontendTests.frontend_fixture(self,native=True,dialogue=out/'bank-dialogue.c')
            for resource in r['resources']:
                self.assertEqual(sha256((out/resource['file']).read_bytes()),resource['sha256'])
            retained=json.loads((ROOT/'build/v3-post-office-bank-dialogue-02/dialogue.json').read_text())
            self.assertEqual(json.loads(json.dumps(r)),retained)


if __name__=='__main__':unittest.main()
