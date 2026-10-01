"""Original HRA model presents through the existing transactional mail creator."""
import ctypes as C
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import unittest

import test_mail_glyph_creator as glyph_tests
from mail_catalog import templates
from mail_format import format_letter
from mail_record import Field, Record, pack
from test_mail_format import CText
from npc_mail_capture import (SCORE_SOURCE, LEGACY_SCORE_SOURCE_HASH,
                             REWARD_SCORE_SOURCE_HASH, source_report_matches)
from aflib import by_vrom, sha256
from v3_hra_mail import RAM as CREATOR_RAM, VROM as CREATOR_VROM

ROOT = Path(__file__).resolve().parents[1]


class HraRewardMailTests(glyph_tests.MailGlyphCreatorTests):
    @classmethod
    def generated_compile_flags(cls, directory):
        return [*super().generated_compile_flags(directory), '-DAF_V3_HRA_REWARDS=1']

    def reward_fixture(self, number, gift, points, capital=0):
        fixture = self.score_fixture(number, capital, points=points)
        C.memmove(C.addressof(fixture[5])+14, struct.pack('>H', gift), 2)
        return fixture

    def reward_invoke(self, fixture, success=True):
        memory, address, capture, player, series, request, destination, capital = fixture
        before = destination.raw, capital.value, player.raw, series.raw, request.raw
        result = self.lib.af_academy_score_mail_create(address, C.byref(destination,16),
                                                     C.byref(self.active), C.byref(capital))
        self.assertEqual(result, int(success))
        self.assertIsNone(self.active.value)
        self.assertEqual((player.raw, series.raw, request.raw), before[2:])
        self.assertEqual(destination.raw[:16]+destination.raw[180:], b'!'*32)
        lead = address-C.addressof(memory)
        self.assertEqual(memory.raw[:lead]+memory.raw[lead+self.size:], b'!'*64)
        self.assertEqual(bytes(self.series_memory), self.series_data)
        if not success:
            self.assertEqual((destination.raw, capital.value), before[:2])
            return
        points, _, _, _, _, _, number, gift, _, _ = struct.unpack('>IHHHBBHHBB', request.raw)
        record = Record(self.catalog_id, 0, (number,),
                        ((0, Field(f'{points:,}'.rjust(10).encode())),), bool(before[1]))
        expected = bytearray(164)
        expected[:16] = player.raw
        expected[18:30] = b' '*12
        expected[30:35] = b'\xff'*5
        expected[36:38] = struct.pack('>H', gift)
        expected[39:42] = bytes((128, 6, 51))
        expected[42:] = pack(record)
        self.assertEqual(destination.raw[16:180], bytes(expected))
        rendered = format_letter(record, templates(self.catalog, record))
        output = CText.from_address(address+self.text)
        self.assertEqual(tuple(bytes(output.text[o:o+n]) for o,n in zip(output.offsets,output.lengths)),
                         (rendered.header, rendered.body, rendered.footer))
        self.assertEqual(capital.value, int(rendered.final_capital))
        self.assertEqual(C.c_uint.in_dll(self.lib,'af_event_card_item_calls').value, 0)

    def test_original_templates_presents_and_score_thresholds(self):
        for number, gift, minimum in ((0x221, 0x3024, 70000), (0x222, 0x3028, 100000)):
            for capital in (0, 1):
                for points in (minimum, minimum+1, 0x7FFFFFFF):
                    self.reward_invoke(self.reward_fixture(number, gift, points, capital))
                for points in (minimum-1, 0x80000000, 0xFFFFFFFF):
                    self.reward_invoke(self.reward_fixture(number, gift, points, capital), False)

    def test_no_crossed_missing_or_unrelated_presents(self):
        for number in (0x34, 0x48, 0x220, 0x221, 0x222, 0x223):
            for gift in (0, 0x3024, 0x3028, 0x3224, 0xFFFF):
                if (number, gift) in ((0x34, 0), (0x48, 0), (0x221, 0x3024), (0x222, 0x3028)):
                    continue
                self.reward_invoke(self.reward_fixture(number, gift, 100000, 1), False)

    def test_failed_catalogue_reads_never_publish_a_present(self):
        reads = C.c_uint.in_dll(self.lib, 'af_mail_catalog_reads')
        failure = C.c_uint.in_dll(self.lib, 'af_mail_catalog_fail_read')
        for number, gift in ((0x221, 0x3024), (0x222, 0x3028)):
            reads.value = 0
            self.reward_invoke(self.reward_fixture(number, gift, 100000, 1))
            count = reads.value
            self.assertGreater(count, 0)
            for index in range(1, count+1):
                reads.value, failure.value = 0, index
                self.reward_invoke(self.reward_fixture(number, gift, 100000, 1), False)
            failure.value = 0


class HraRewardSourceTests(unittest.TestCase):
    def test_default_compilation_retains_the_exact_original_creator(self):
        original = subprocess.run(['git', 'show', 'd5c4660e6d32b551b055c195a8e525e717d89a2c:'+SCORE_SOURCE], cwd=ROOT,
                                  capture_output=True, check=True).stdout
        self.assertEqual(hashlib.sha256(original).hexdigest(), LEGACY_SCORE_SOURCE_HASH)
        current = (ROOT/SCORE_SOURCE).read_bytes()
        self.assertEqual(hashlib.sha256(current).hexdigest(), REWARD_SCORE_SOURCE_HASH)
        command = ['gcc', '-S', '-O2', '-x', 'c', '-', '-o', '-',
                   '-I'+str(ROOT/'overlays/mail_generation')]
        before = subprocess.run(command, input=original, capture_output=True, check=True).stdout
        after = subprocess.run(command, input=current, capture_output=True, check=True).stdout
        self.assertEqual(after, before)

    def test_predecessor_is_not_accepted_for_rewards_or_future_source_changes(self):
        current = {SCORE_SOURCE: REWARD_SCORE_SOURCE_HASH, 'other': 'same'}
        old = {SCORE_SOURCE: LEGACY_SCORE_SOURCE_HASH, 'other': 'same'}
        self.assertTrue(source_report_matches(old, current))
        self.assertFalse(source_report_matches(old, current, hra_rewards=True))
        self.assertFalse(source_report_matches(old, {**current, SCORE_SOURCE: 'different'}))
        self.assertFalse(source_report_matches({**old, 'other': 'different'}, current))


@unittest.skipUnless((ROOT/'build/v3-travel-native-dma-installed-02/build.json').is_file(),
                     'Verified local complete V3 score-letter table required')
class HraExpandedRewardMailTests(HraRewardMailTests):
    series_rows = 60

    @classmethod
    def generated_compile_flags(cls, directory):
        return [*super().generated_compile_flags(directory), '-DAF_V3_HRA_SERIES_COUNT=60']

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        directory = ROOT/'build/v3-travel-native-dma-installed-02'
        raw_report = (directory/'build.json').read_bytes()
        pin = json.loads((directory/'build-lock.json').read_bytes())
        report = json.loads(raw_report)['hra']['score_letters']
        image = (directory/'animal-forest-v3-asset-loader.z64').read_bytes()
        if sha256(image) != pin['rom_sha256'] or sha256(raw_report) != pin['report_sha256']:
            raise ValueError('Changed checked V3 score-letter fixture')
        creator = by_vrom(image)[CREATOR_VROM].extract(image)
        if report['name_rows'] != cls.series_rows or sha256(creator) != report['output_sha256']:
            raise ValueError('Changed complete V3 score-letter table fixture')
        at = report['name_table_address']-CREATOR_RAM
        table = creator[at:at+report['name_table_bytes']]
        if len(table) != cls.series_rows*26 or sha256(table) != report['name_table_sha256']:
            raise ValueError('Changed complete V3 theme names')
        if table[:55*26] != cls.series_data[:55*26]:
            raise ValueError('V3 theme fixture replaces original HRA names')
        cls.series_data = table.ljust((len(table)+15)&~15, b'\0')

    def test_all_added_theme_names_remain_usable_with_reward_creation(self):
        for row in range(55, self.series_rows):
            for number in (0x3A, 0x3B):
                for capital in (0, 1):
                    self.score_invoke(self.score_fixture(number, capital, series=row))


if __name__ == '__main__': unittest.main()
