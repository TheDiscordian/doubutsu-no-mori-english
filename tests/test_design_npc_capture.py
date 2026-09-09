"""Execute the corrected resource through the actual C integrity/capture code."""

import ctypes as C
import os
import unittest

import test_npc_mail_capture as legacy


@unittest.skipUnless((legacy.ROOT/'build/design-items-words/words.bin').is_file(), 'Corrected complete word resource required')
class DesignNpcCaptureTests(legacy.NpcMailCaptureTests):
    word_path = legacy.ROOT/'build/design-items-words/words.bin'
    compiler_flags = ('-DAF_NPC_WORD_PROFILE=2',)+(
        ('-fsanitize=address,undefined', '-fno-sanitize-recover=all', '-fno-omit-frame-pointer', '-g')
        if os.environ.get('AF_DESIGN_CAPTURE_SANITIZE') == '1' else ())

    def test_old_valid_profile_is_rejected_and_corrected_species_reaches_capture(self):
        sources = self.sources(); before = bytes(sources)
        old = legacy.ROOT/'build/npc-mail-words/words.bin'
        words = C.create_string_buffer(old.read_bytes(), old.stat().st_size)
        self.assertEqual(self.lib.af_npc_mail_sources_init(C.byref(sources), words, len(words),
                                                         self.aliases, len(self.aliases)), 0)
        self.assertEqual(bytes(sources), before)
        for foreign in (0, 1):
            work = self.fixture(foreign)
            self.offsets[3] = 1  # Native fish family 0219 + 1 = herabuna.
            self.prepare(work)
            field = work.capture.fields[6]
            self.assertEqual((field.length, field.article, bytes(field.text)),
                             (16, 0, b'herabuna        '))


if __name__ == '__main__': unittest.main()
