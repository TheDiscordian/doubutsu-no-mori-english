"""Independent expected-selection boundaries used by the native score batch."""

from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from academy_score_scenario import selected_template
from academy_score_smoke import mailbox_position


class AcademyScoreScenarioTests(unittest.TestCase):
    def test_all_twenty_one_templates_use_existing_players_and_slots(self):
        seen = set()
        for index in range(21):
            for capital in (0,1):
                player,slot = mailbox_position(index,capital)
                self.assertIn(player,range(4));self.assertIn(slot,range(10))
                if index<20:
                    self.assertEqual((player,slot),(index//10+capital*2,index%10))
                seen.add((player,slot))
        self.assertEqual(seen,{(p,s) for p in range(4) for s in range(10)})
        self.assertEqual(mailbox_position(20,0),(2,0))
        self.assertEqual(mailbox_position(20,1),(0,0))

    def test_fallback_points_and_original_room_defaults(self):
        request = {'selection_table':[-1]*64}
        for points,room,expected in ((0,0,0x42),(1,0,0x43),(19999,1,0x44),(5000,2,0x45),
                (5000,3,0x45),(5000,0xFFFFFFFF,0x45),(20000,0,0x46),(69999,0,0x46),
                (70000,0,0x47),(99999,0,0x47),(100000,0,0x48),(0x7FFFFFFF,0,0x48)):
            with self.subTest(points=points,room=room):
                self.assertEqual(selected_template(request,{'points':points,'room':room,'bits':'0'},0),expected)

    def test_original_descending_bit_priority_and_live_retry_seed(self):
        table = [-1]*64;table[0]=0x34;table[7]=0x3B
        request = {'selection_table':table};case = {'points':123456,'room':0,'bits':'81'}
        # Seeds zero and the next actual LCG state both choose native row zero.
        self.assertEqual(selected_template(request,case,0),0x3B)
        self.assertEqual(selected_template(request,case,0x3C6EF35F),0x3B)
        table[7] = -1
        self.assertEqual(selected_template(request,case,0),0x34)
        case['bits'] = '0'
        self.assertEqual(selected_template(request,case,0),0x48)


if __name__ == '__main__': unittest.main()
