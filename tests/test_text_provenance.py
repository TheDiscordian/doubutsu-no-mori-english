"""One canonical catalogue with evidence-based credits and guarded human review."""
import copy
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import text_provenance as p

class ProvenanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalogue=json.loads(p.CATALOGUE.read_text())
        cls.rows={r['id']:r for r in cls.catalogue['entries']}

    def test_unique_credits_and_explicit_coverage_limits(self):
        self.assertEqual(sum(p.validate(self.catalogue).values()),len(self.rows))
        self.assertFalse(self.catalogue['coverage']['complete_whole_rom_provenance'])
        self.assertTrue(self.catalogue['coverage']['unresolved_work'])
        self.assertEqual(self.catalogue['inspection_rom_sha256'],p.ROM_SHA)

    def test_official_credit_title_and_native_contributors(self):
        for identity in ('string:04EA','string:0545','string:0546','string:0554'):
            self.assertEqual(self.rows[identity]['locales']['en']['credit'],'official')
        self.assertEqual(self.rows['string:04EA']['locales']['en']['source']['reference_id'],'string:077B')

    def test_recorded_drafts_are_not_mislabeled_human(self):
        for identity in ('string:009C','string:05DE','mail:00C0','ui/keyboard/page'):
            row=self.rows[identity]['locales']['en']
            self.assertEqual(row['credit'],'assistant'); self.assertTrue(row['text'])
            self.assertNotEqual(row['human_review'],'approved')
        self.assertEqual(p.classify({'provenance':'Unknown origin'}),'unresolved')
        self.assertEqual(p.classify({'status':'mechanically_validated_candidate_not_reviewed'}),'unresolved')

    def test_all_text_families_share_the_catalogue(self):
        for identity in ('message:09C7','npc_names:0000','item_24:00A8','catchphrases:0000',
                         'GAFE01-r0/mail:0000','message:2DEA','select:01CE',
                         'GAFE01-r0/villager/00D8/name','GAFE01-r0/item/335C/name',
                         'ui/editor-confirmation/0','ui/inventory_warning/0/0','ui/map/shrine'):
            self.assertIn(identity,self.rows)

    def test_missing_evidence_false_reviews_and_duplicate_ids_reject(self):
        sample=self.rows['string:04EA']
        for mutation in ('duplicate','source','hash','review','contributor'):
            data={**self.catalogue,'entries':[copy.deepcopy(sample)]}
            row=data['entries'][0]['locales']['en']
            if mutation=='duplicate':data['entries'].append(copy.deepcopy(sample))
            elif mutation=='source':row.pop('source')
            elif mutation=='hash':row['encoded_sha256']='not a hash'
            elif mutation=='review':row.update(credit='assistant',human_review='approved')
            else:row.update(credit='human')
            with self.assertRaises(ValueError):p.validate(data)

    def test_new_language_has_independent_authorship(self):
        data={**self.catalogue,'entries':[copy.deepcopy(self.rows['string:04EA'])]}
        data['entries'][0]['locales']['fr']=dict(credit='human',contributors=['Example translator'],
            locator=['translations/fr/credits.json'],encoded_sha256='a'*64,human_review='needed')
        p.validate(data)
        self.assertEqual(data['entries'][0]['locales']['en']['credit'],'official')

if __name__=='__main__':unittest.main()
