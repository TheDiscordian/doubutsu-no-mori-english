"""Focused production checks; no emulator, audio device, or old build is run."""
import json
import os
from pathlib import Path
import signal
import struct
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from trailer_capture import Recording
from trailer_edit import CUTS,FOOTAGE,artwork,inputs,probe
from trailer_music import midi


class TrailerTests(unittest.TestCase):
    def test_explicit_approved_name_take_and_fifty_second_edit(self):
        self.assertEqual(FOOTAGE['keyboard'],'build/trailer-keyboard-02')
        self.assertNotIn('build/trailer-keyboard-01',FOOTAGE.values())
        self.assertEqual(sum(c['duration'] for c in CUTS),50)
        self.assertTrue(all(c['duration']>=4 for c in CUTS))
        self.assertEqual(set(inputs()),set(FOOTAGE))

    def test_original_midi_has_bounded_notes_and_a_resolving_end(self):
        raw=midi();self.assertEqual(raw[:4],b'MThd')
        self.assertEqual(struct.unpack_from('>IHHH',raw,4),(6,0,1,480))
        self.assertEqual(raw[14:18],b'MTrk')
        self.assertEqual(int.from_bytes(raw[18:22],'big'),len(raw)-22)
        at=22;tick=0;active={};ended=False
        while at<len(raw):
            delta=0
            while True:
                value=raw[at];at+=1;delta=(delta<<7)|(value&127)
                if not value&128:break
            tick+=delta;status=raw[at];at+=1
            if status==255:
                kind,length=raw[at:at+2];at+=2
                self.assertIn(kind,(0x51,0x2F))
                if kind==0x51:self.assertEqual(int.from_bytes(raw[at:at+length],'big'),500000)
                if kind==0x2F:ended=True
                at+=length;continue
            count=1 if status&0xF0==0xC0 else 2
            args=raw[at:at+count];at+=count
            self.assertTrue(all(v<128 for v in args))
            if status&0xF0 in (0x80,0x90):
                key=(status&15,args[0]);active[key]=active.get(key,0)+(1 if status&0xF0==0x90 else -1)
                self.assertGreaterEqual(active[key],0)
        self.assertTrue(ended);self.assertEqual(tick,100*480)
        self.assertTrue(all(v==0 for v in active.values()))

    def test_recording_uses_and_removes_only_its_private_null_sink(self):
        with tempfile.TemporaryDirectory(prefix='af-trailer-check-') as directory:
            recorder=Recording(directory);env={'PULSE_SERVER':'unix:/nonexistent-af-audio'}
            outputs=['77\n',json.dumps([{'name':recorder.sink}])]
            with patch.dict(os.environ,{},clear=True),patch('trailer_capture.subprocess.check_output',side_effect=outputs) as command:
                recorder.configure(env)
            self.assertEqual(env['PULSE_SINK'],recorder.sink)
            self.assertNotIn('PULSE_SERVER',env)
            self.assertEqual(command.call_args_list[0].args[0][:3],['pactl','load-module','module-null-sink'])
            with patch('trailer_capture.subprocess.run') as command:
                recorder.close()
            self.assertEqual(command.call_args.args[0],['pactl','unload-module','77'])

    def test_recording_stops_encoder_cleanly(self):
        recorder=Recording(ROOT/'build/unused-trailer-test')
        process=Mock();process.poll.return_value=None;process.wait.return_value=255;recorder.process=process
        recorder.stop();process.send_signal.assert_called_once_with(signal.SIGINT)
        self.assertIsNone(recorder.process)

    def test_cards_identify_unofficial_project_without_a_public_release_claim(self):
        end=artwork(CUTS[-1])
        self.assertIn('UNOFFICIAL FAN TRANSLATION',end)
        self.assertIn('V2 PREVIEW',end)
        self.assertIn('EXPANSION PAK REQUIRED',end)
        self.assertNotIn('Download now',end)

    def test_current_video_format(self):
        directory=ROOT/os.environ.get('AF_TRAILER_BUILD','build/trailer-cut-02')
        info=probe(directory/'Animal Forest English - Trailer.mp4')
        video=next(s for s in info['streams'] if s['codec_type']=='video')
        audio=next(s for s in info['streams'] if s['codec_type']=='audio')
        self.assertEqual((video['width'],video['height']),(1920,1080))
        self.assertEqual(video['r_frame_rate'],'30/1');self.assertEqual(video['pix_fmt'],'yuv420p')
        self.assertEqual(audio['codec_name'],'aac');self.assertEqual(audio['channels'],2)
        self.assertAlmostEqual(float(info['format']['duration']),50,places=1)


if __name__=='__main__':unittest.main()
