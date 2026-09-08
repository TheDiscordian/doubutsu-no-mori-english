"""Whole-letter native-adapter transactions with isolated mocked game helpers."""

import ctypes as C
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from fortune_slips import CATALOG_VROM
from mail_record import Field, Record, pack
from test_fortune_slips import Choice


class Pending(C.Structure):
    _pack_ = 4
    _fields_ = [('choice',Choice),('state',C.c_uint),('capital',C.c_uint),
                ('owner',C.c_void_p),('reserved',C.c_uint)]


def draw(seed, count):
    values = []
    for limit in (4,16,16,16,16,3)[:count]:
        seed = (seed*0x19660D+0x3C6EF35F)&0xFFFFFFFF
        value = struct.unpack('>f',struct.pack('>I',(seed>>9)|0x3F800000))[0]-1.0
        product = struct.unpack('>f',struct.pack('>f',value*limit))[0]
        values.append(int(product))
    return seed,values


@unittest.skipUnless(shutil.which('gcc') and (ROOT/'build/fortune-slip-resources/fortune-catalog.bin').is_file(),
                     'Host compiler and complete local fortune resources required')
class FortuneActorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='af-fortune-actor-')
        output = Path(cls.temporary.name)/'actor.so'
        sources = ['overlays/mail_generation/generate.c','overlays/mail_generation/fortune_slip.c',
                   'overlays/mail_generation/fortune_actor.c','runtime/mail/catalog.c',
                   'runtime/mail/format.c','runtime/mail/record.c','tests/mail_catalog_mock.c',
                   'tests/fortune_actor_mock.c']
        result = subprocess.run(['gcc','-std=c99','-Wall','-Wextra','-Werror','-O2','-shared','-fPIC',
                                 *(str(ROOT/p) for p in sources),'-o',str(output)],capture_output=True,text=True)
        if result.returncode: raise ValueError(result.stderr)
        cls.lib = C.CDLL(str(output))
        for name in ('af_miko_fortune_init','af_miko_fortune_give'):
            getattr(cls.lib,name).argtypes = [C.c_void_p,C.c_void_p]
            getattr(cls.lib,name).restype = None
        cls.words = (ROOT/'build/fortune-slip-resources/fortune-words.bin').read_bytes()
        cls.catalog = (ROOT/'build/fortune-slip-resources/fortune-catalog.bin').read_bytes()
        cls.original = (ROOT/'build/fortune-slip-resources/catalog.bin').read_bytes()

    @classmethod
    def tearDownClass(cls): cls.temporary.cleanup()

    def counter(self,name): return C.c_uint.in_dll(self.lib,'af_miko_test_'+name)
    def value(self,name): return self.counter(name).value

    def setUp(self):
        for name in ('rng','draws','allocations','frees','live','fail_malloc','bad_free','alignment',
                     'copies','slots','event_count','cancel','switch_owner','slot','second_slot','order'):
            self.counter(name).value = 0
        for name,value in (('enabled',1),('reads',0),('dma_error',0),('fail_read',0)):
            C.c_uint.in_dll(self.lib,'af_mail_catalog_'+name).value = value
        rom = (C.c_ubyte*0x100000).in_dll(self.lib,'af_mail_catalog_rom')
        C.memset(rom,0,len(rom));C.memmove(rom,self.original,len(self.original))
        C.memmove(C.addressof(rom)+CATALOG_VROM-0x03000000,self.catalog,len(self.catalog))
        C.memmove((C.c_ubyte*1088).in_dll(self.lib,'af_fortune_words'),self.words,1088)
        self.owner = C.c_void_p.in_dll(self.lib,'af_miko_private')
        self.capital = C.c_uint.in_dll(self.lib,'af_mail_generation_capital');self.capital.value = 0
        self.player = C.create_string_buffer(bytes((i%251 for i in range(4096))),4096)
        self.actor = C.create_string_buffer(b'!'*4096,4096)
        self.pending = Pending.from_address(C.addressof(self.actor)+0x948)
        self.owner.value = C.addressof(self.player)
        self.counter('rng').value = 0xF13579BD
        self.counter('order').value = 1
        self.counter('slot').value = self.counter('second_slot').value = 7
        self.before = self.player.raw
        self.set_action(2)
        self.lib.af_miko_fortune_init(self.actor,None)
        self.set_action(3)

    def set_action(self,value): C.c_int.from_address(C.addressof(self.actor)+0x938).value = value

    def give(self):
        self.lib.af_miko_fortune_give(self.actor,None)
        self.assertEqual((self.value('live'),self.value('bad_free')),(0,0))
        self.assertEqual(C.c_uint.in_dll(self.lib,'af_mail_catalog_dma_error').value,0)

    def expected_mail(self):
        choice = self.pending.choice
        rows = [slot*16+choice.phrases[slot] for slot in range(4)]+[64+choice.outcome]
        fields = tuple((slot,Field(self.words[row*16:(row+1)*16],0)) for slot,row in enumerate(rows))
        record = Record(3,0,(0x72+choice.template_index,),fields,bool(self.pending.capital))
        mail = bytearray(b' '*164);mail[:16] = self.before[:16]
        mail[36:42] = bytes((0x6A,0x2B,0,0x80,5,25));mail[42:] = pack(record)
        return bytes(mail)

    def test_full_delivery_retains_original_six_draws_and_announces_only_after_copy_and_free(self):
        self.assertEqual(self.lib.af_miko_test_pending_bytes(),C.sizeof(Pending))
        original_actor = self.actor.raw
        self.give()
        seed,values = draw(0xF13579BD,6)
        choice = self.pending.choice
        self.assertEqual((self.value('rng'),self.value('draws')),(seed,6))
        self.assertEqual((choice.outcome,*choice.phrases,choice.template_index),tuple(values))
        expected = bytearray(self.before);at = 0x40A+7*164;expected[at:at+164] = self.expected_mail()
        self.assertEqual(self.player.raw,bytes(expected))
        self.assertEqual((self.value('copies'),self.value('frees'),self.pending.state),(1,1,3))
        self.assertEqual(self.actor.raw[:0x938],original_actor[:0x938])
        self.assertEqual(self.actor.raw[0x93C:0x948],original_actor[0x93C:0x948])
        self.assertEqual(self.actor.raw[0x948+C.sizeof(Pending):],original_actor[0x948+C.sizeof(Pending):])
        events = (C.c_uint*64).in_dll(self.lib,'af_miko_test_events')
        self.assertEqual(list(events)[:self.value('event_count')],
                         [1,2,3,4,5,0x10490000,0x10410002,0x10502513,0x10510007,0x10520000,6])
        before = self.player.raw,self.value('draws'),self.value('copies'),self.value('allocations')
        for action in (0,3):
            self.set_action(action);self.counter('order').value = 1;self.give()
            self.assertEqual((self.player.raw,self.value('draws'),self.value('copies'),self.value('allocations')),before)

    def test_failed_resources_retry_the_same_complete_fortune_without_rewinding_shared_capital(self):
        C.c_uint.in_dll(self.lib,'af_mail_catalog_enabled').value = 0
        self.give();choice = bytes(self.pending.choice)
        self.assertEqual((self.player.raw,self.pending.state,self.value('draws'),self.value('order')),
                         (self.before,2,6,1))
        for _ in range(4): self.give()
        self.assertEqual((bytes(self.pending.choice),self.value('draws'),self.value('copies')),(choice,6,0))
        self.capital.value = 1
        C.c_uint.in_dll(self.lib,'af_mail_catalog_enabled').value = 1
        self.give()
        self.assertEqual((bytes(self.pending.choice),self.value('draws'),self.pending.state,self.capital.value),
                         (choice,6,3,1))
        self.assertEqual(self.player.raw[0x40A+7*164:0x40A+8*164],self.expected_mail())
        self.assertEqual(self.value('frees'),self.value('allocations'))

    def test_allocation_and_pocket_failures_do_not_select_or_announce(self):
        for slot in (-1,10,0x7FFFFFFF):
            self.counter('slots').value = 0;self.counter('slot').value = slot&0xFFFFFFFF
            self.give()
            self.assertEqual((self.value('allocations'),self.value('draws'),self.pending.state),(0,1,1))
        self.counter('slots').value = 0;self.counter('slot').value = 7
        self.counter('fail_malloc').value = 1
        self.give()
        self.assertEqual((self.value('allocations'),self.value('frees'),self.value('draws'),self.pending.state),(1,0,1,1))
        self.assertEqual((self.player.raw,self.value('order')),(self.before,1))
        self.counter('fail_malloc').value = 0;self.give()
        self.assertEqual((self.pending.state,self.value('draws'),self.value('copies')),(3,6,1))

    def test_recheck_rejects_full_pocket_cancelled_order_or_changed_player_without_publication(self):
        for mutation in ('pocket','cancel','switch_owner'):
            self.setUp()
            if mutation == 'pocket': self.counter('second_slot').value = 0xFFFFFFFF
            else: self.counter(mutation).value = 1
            self.give()
            self.assertEqual((self.player.raw,self.pending.state,self.value('copies'),self.value('frees')),
                             (self.before,2,0,1))
            self.assertEqual(self.value('event_count'),4)  # init, malloc, clear, free only

    def test_invalid_action_owner_outcome_pending_and_capital_do_not_allocate(self):
        for mutation in ('null_actor','action','order','owner','null_owner','outcome','state','reserved','capital'):
            self.setUp()
            if mutation == 'null_actor':
                self.lib.af_miko_fortune_give(None,None)
            else:
                if mutation == 'action': self.set_action(1)
                elif mutation == 'order': self.counter('order').value = 0
                elif mutation == 'owner': self.pending.owner = self.owner.value+16
                elif mutation == 'null_owner': self.owner.value = None
                elif mutation == 'outcome': C.c_int.from_address(C.addressof(self.actor)+0x940).value = 4
                elif mutation == 'state': self.pending.state = 0
                elif mutation == 'reserved': self.pending.reserved = 1
                elif mutation == 'capital': self.capital.value = 2
                self.give()
            self.assertEqual((self.value('allocations'),self.value('draws'),self.player.raw),(0,1,self.before))

    def test_each_heap_alignment_and_each_selected_read_failure_is_bounded_and_retryable(self):
        self.give();reads = C.c_uint.in_dll(self.lib,'af_mail_catalog_reads').value
        for alignment in range(16):
            self.setUp();self.counter('alignment').value = alignment;self.give()
            self.assertEqual(self.pending.state,3)
        for fail in range(1,reads+1):
            self.setUp();C.c_uint.in_dll(self.lib,'af_mail_catalog_fail_read').value = fail
            self.give();choice = bytes(self.pending.choice)
            self.assertEqual((self.pending.state,self.player.raw,self.value('copies')),(2,self.before,0))
            C.c_uint.in_dll(self.lib,'af_mail_catalog_fail_read').value = 0
            self.give()
            self.assertEqual((self.pending.state,bytes(self.pending.choice),self.value('draws')),(3,choice,6))

    def test_two_instances_do_not_share_pending_and_initializer_discards_old_instance_state(self):
        C.c_uint.in_dll(self.lib,'af_mail_catalog_enabled').value = 0;self.give()
        original = bytes(self.pending)
        other = C.create_string_buffer(b'?'*4096,4096)
        self.lib.af_miko_fortune_init(other,None)
        C.c_int.from_address(C.addressof(other)+0x938).value = 3
        self.lib.af_miko_fortune_give(other,None)
        self.assertEqual(bytes(self.pending),original)
        self.assertEqual(Pending.from_address(C.addressof(other)+0x948).state,2)
        self.lib.af_miko_fortune_init(self.actor,None)
        self.assertEqual((bytes(self.pending.choice),self.pending.state,self.pending.capital,
                          self.pending.owner,self.pending.reserved),(bytes(8),1,0,self.owner.value,0))
        self.assertEqual(self.value('live'),0)


if __name__ == '__main__': unittest.main()
