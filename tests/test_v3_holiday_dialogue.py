"""Focused connected message/transport checks, not a native gameplay claim."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,u32
from gc_adapter import remove_redundant_article_suppression
from gc_text import decode_gc
from runtime_module import module_command_info
from textbanks import Bank
from textcodec import encode,tokenize
from v3_camper_text import donor
from v3_holiday_dialogue import convert,check_provenance,FIRST,CHOICE_FIRST,RANGES,MESSAGE,TABLE,CHOICE_TABLE
from v3_furniture_install import inputs

OUT=ROOT/os.environ.get('V3_HOLIDAY_DIALOGUE','build/v3-diary-category-work-01/tortimer-dialogue-02')


class DialogueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base,cls.report=inputs(OUT/'build-lock.json')
        cls.messages,cls.choices,cls.fields,cls.text=convert(cls.base)

    def test_installed_complete_group_and_provenance(self):
        image=self.base;p=self.report;files=by_vrom(image);info=module_command_info(image)
        text=self.text;check_provenance(text)
        messages=Bank('message',0,0,files[MESSAGE].extract(image),files[TABLE].extract(image)).entries()
        cv=p['import_storage']['choice_vrom']
        choices=Bank('choice',0,0,files[cv].extract(image),files[CHOICE_TABLE].extract(image)).entries()
        self.assertEqual(messages[FIRST:],self.messages);self.assertEqual(choices[CHOICE_FIRST:],self.choices)
        self.assertEqual((len(self.messages),len(self.choices),len(self.fields)),(347,4,640))
        core=files[CODE_VROM].extract(image)
        for a,op,value in ((0x8009E3A4,0x2A010000,len(messages)),(0x8009E668,0x28A10000,len(messages)),
                           (0x80065544,0x2A010000,len(choices)),(0x80065DAC,0x28810000,len(choices))):
            self.assertEqual(u32(core,a-CODE_RAM),op|value)
        # Reverse only the declared encoding/ID adaptations and compare every
        # token to the official donor. Pages, pauses, branches, and order values
        # cannot disappear merely because the output still fits its buffer.
        original,_,decoder=donor();reverse={r['id']:r['donor_id'] for r in text['rows']}
        reverse_choices={r['id']:r['donor_id'] for r in text['choices']}
        for row,data in zip(text['rows'],self.messages):
            expected,_=remove_redundant_article_suppression(decode_gc(original[row['donor_id']],decoder))
            expected=encode(expected.replace('ー','-'),info);out=bytearray(data)
            for t in tokenize(data,info):
                if t.kind=='cmd' and 14<=t.data[1]<=24:
                    mapping=reverse if t.data[1]<=21 else reverse_choices
                    for i in range(2,len(t.data),2):
                        n=mapping[int.from_bytes(t.data[i:i+2],'big')]
                        out[t.offset+i:t.offset+i+2]=n.to_bytes(2,'big')
            self.assertEqual(out,expected)
        npc=p['equipment_resources']['npc_extra'];packet=npc['packet']
        data=image[packet['physical']:packet['physical']+packet['bytes']]
        self.assertEqual(sha256(data),packet['sha256']);self.assertEqual(data[0x3800:0x3A80],self.fields)
        self.assertEqual(sha256(data[0x2800:0x2800+npc['dialogue']['code']['bytes']]),npc['dialogue']['code']['sha256'])
        self.assertFalse(npc['dialogue']['actor_active'])
        self.assertFalse(npc['record']['implemented']);self.assertFalse(npc['record']['selected'])
        self.assertEqual(data[npc['record']['flags_offset']:npc['record']['flags_offset']+4],bytes(4))
        for fixup in npc['record']['profile_fixups']:
            self.assertEqual(data[fixup['offset']:fixup['offset']+4],bytes(4))
        # Compare retained bytes, without replaying the predecessor's tests.
        before,previous=inputs(ROOT/'build/v3-diary-category-work-01/tortimer-services-03/build-lock.json')
        old=previous['equipment_resources']['npc_extra']['packet']
        original_packet=before[old['physical']:old['physical']+old['bytes']]
        self.assertEqual(data[:0x2800],original_packet[:0x2800])
        self.assertEqual(data[0x3A80:],original_packet[0x3A80:])
        self.assertEqual(text['max_expanded_bytes'],867)

    def test_connected_controller_and_transport(self):
        with tempfile.TemporaryDirectory(prefix='v3-holiday-dialogue-') as temp:
            directory=Path(temp);fields=directory/'fields.bin';fields.write_bytes(self.fields)
            command=['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fno-pie','-no-pie',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-I'+str(ROOT/'overlays/v3'),
                'tests/v3_holiday_dialogue_test.c','overlays/v3/holiday_dialogue.c',
                'overlays/v3/holiday_talk.c','overlays/v3/holiday_rewards.c','overlays/v3/diary.c',
                'overlays/v3/diary_calendar.c','-o',str(directory/'check')]
            for cmd in (command,[str(directory/'check'),str(fields),
                    str(ROOT/'build/v3-holiday-rewards-prepared-02/holiday-rewards.bin')]):
                result=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=30)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                if result.stdout:print(result.stdout.strip())


if __name__=='__main__':unittest.main()
