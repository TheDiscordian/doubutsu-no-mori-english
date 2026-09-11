"""Focused production checks; no emulator, audio device, or old build is run."""
import json
import os
from pathlib import Path
import signal
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from trailer_capture import Recording
from trailer_edit import CUTS,FOOTAGE,DURATION,TOTAL_FRAMES,artwork,inputs,probe


class TrailerTests(unittest.TestCase):
    def test_explicit_approved_name_take_and_musical_edit(self):
        self.assertEqual(FOOTAGE['keyboard'],'build/trailer-keyboard-03')
        self.assertNotIn('build/trailer-keyboard-01',FOOTAGE.values())
        self.assertEqual(sum(c['frames'] for c in CUTS),TOTAL_FRAMES)
        self.assertTrue(all(c['duration']>=2 for c in CUTS))
        keyboard_shots=[c for c in CUTS if c['source']=='keyboard' and c['start']<20]
        self.assertEqual(len(keyboard_shots),1)
        self.assertEqual(keyboard_shots[0]['start'],6.65)
        self.assertTrue({'map','nook_exterior','shop','catalogue','post_exterior','post','payment'}
                        <= {c['source'] for c in CUTS})
        self.assertEqual(set(inputs()),set(FOOTAGE))

    def test_soundtrack_comes_from_the_current_games_opening(self):
        directory=ROOT/os.environ.get('AF_TRAILER_BUILD','build/trailer-cut-05')
        report=json.loads((directory/'music.json').read_text())
        self.assertEqual(report['source'],FOOTAGE['opening']+'/footage.mkv')
        self.assertFalse(report['speaker_playback'])
        self.assertEqual(report['duration'],DURATION)
        self.assertIn('no replacement composition',report['arrangement'])

    def test_audio_capture_names_only_its_own_null_monitor(self):
        with tempfile.TemporaryDirectory(prefix='af-trailer-monitor-check-') as directory:
            recorder=Recording(directory,audio=True)
            process=Mock();process.poll.return_value=0;process.wait.return_value=0
            with patch('trailer_capture.subprocess.Popen',return_value=process) as spawn:
                recorder.start(':123',{'PULSE_SINK':recorder.sink},20)
                command=spawn.call_args.args[0]
                self.assertIn(recorder.sink+'.monitor',command)
                self.assertNotIn('default',command)
                self.assertEqual(command[command.index('-c:a')+1],'pcm_s16le')
                recorder.close()

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
        directory=ROOT/os.environ.get('AF_TRAILER_BUILD','build/trailer-cut-05')
        info=probe(directory/'Animal Forest English - Trailer.mp4')
        video=next(s for s in info['streams'] if s['codec_type']=='video')
        audio=next(s for s in info['streams'] if s['codec_type']=='audio')
        self.assertEqual((video['width'],video['height']),(1920,1080))
        self.assertEqual(video['r_frame_rate'],'30/1');self.assertEqual(video['pix_fmt'],'yuv420p')
        self.assertEqual(audio['codec_name'],'aac');self.assertEqual(audio['channels'],2)
        self.assertAlmostEqual(float(info['format']['duration']),DURATION,places=1)


if __name__=='__main__':unittest.main()
